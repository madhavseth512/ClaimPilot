"""
GuardrailRunner — dual-rail input/output filtering for the FastAPI chat route.

Input rail  : LLM-based topic classification via Groq (no annoy dependency).
Output rail : Custom action checks (hallucination, jurisdiction, insurer recommendation).

NeMo's Colang flows.co defines the canonical patterns and block messages as
the source-of-truth specification; the LLM prompt in check_input() implements
the same logic without needing NeMo's AnnoyIndex for embedding-based matching.
"""
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client = None

INPUT_CLASSIFICATION_PROMPT = """You are a content moderation assistant for ClaimPilot, \
an Indian insurance claim assistant.

Classify the user message into exactly one category:

ALLOWED        — insurance claims, policy queries, IRDAI regulations, document questions,
                 claim status, greetings (hi/hello/namaste), short replies (ok/yes/no/sure),
                 or any message where the insurance intent is unclear (when in doubt → ALLOWED)
BLOCK_OFFTOPIC — explicitly and clearly unrelated to insurance (weather forecast, jokes, movies,
                 cooking recipes, sports scores, coding help, travel recommendations, etc.)
BLOCK_MEDICAL  — explicitly requesting medical diagnosis, treatment advice, or medication
                 recommendations (e.g. "what medicine should I take?", "is my condition serious?").
                 Do NOT block descriptions of medical events shared as insurance context
                 (e.g. "my mother was sick", "I was hospitalised", "she had a disease") —
                 these are ALLOWED because they describe an insurance claim situation.
BLOCK_INVEST   — asking to compare, recommend, or rank specific insurance companies or products
BLOCK_LEGAL    — requesting legal advice unrelated to insurance grievance/ombudsman processes

When in doubt, always choose ALLOWED. Only block when the message is unmistakably off-topic.
Respond with ONLY the category name. Nothing else.

User message: {message}
Category:"""

BLOCK_MESSAGES = {
    "BLOCK_OFFTOPIC": (
        "I'm sorry, I can only assist with insurance-related queries. "
        "For other concerns, please reach out to the appropriate service. "
        "Is there anything related to your insurance claim I can help you with?"
    ),
    "BLOCK_MEDICAL": (
        "I'm not able to provide medical advice. "
        "For medical guidance, please consult a qualified doctor. "
        "I can help you with the documentation required for your health insurance claim — "
        "would you like to continue?"
    ),
    "BLOCK_INVEST": (
        "I'm not able to recommend specific insurance products or companies. "
        "For policy comparisons, please visit your insurer's official website or "
        "consult an IRDAI-registered insurance advisor. "
        "Is there anything related to your existing claim I can help you with?"
    ),
    "BLOCK_LEGAL": (
        "I'm not able to provide legal advice unrelated to insurance claims. "
        "For legal matters, please consult a qualified lawyer. "
        "For insurance-related grievances, I can guide you through the IRDAI "
        "Grievance Redressal process — would that help?"
    ),
}


_PASSTHROUGH_WORDS = {
    "hello", "hi", "hey", "namaste", "ok", "okay", "yes", "no", "sure",
    "thanks", "thank", "thank you", "please", "help", "start", "begin",
    "continue", "next", "done", "ready", "1", "2", "3",
}


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


async def check_input(message: str) -> tuple[bool, str]:
    """
    Run input rail on the user message.
    Returns (True, "")               if the message is insurance-related.
    Returns (False, block_message)   if a rail blocks the message.
    Fails open (returns True) on any exception — never silently block a user.
    """
    # Short messages and greetings always pass — LLM cannot reliably classify
    # them and false positives would break the onboarding flow.
    words = message.strip().lower().split()
    if len(words) <= 3 or all(w.strip(".,!?") in _PASSTHROUGH_WORDS for w in words):
        return True, ""

    try:
        response = _get_client().chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            messages=[{
                "role": "user",
                "content": INPUT_CLASSIFICATION_PROMPT.format(message=message),
            }],
            temperature=0.0,
            max_tokens=10,
        )
        category = response.choices[0].message.content.strip().upper()

        # Normalise — LLM sometimes returns partial matches
        for key in BLOCK_MESSAGES:
            if key in category:
                return False, BLOCK_MESSAGES[key]

        return True, ""

    except Exception:
        return True, ""


async def check_output(response: str) -> tuple[bool, str]:
    """
    Run output rails on the generated response.
    Returns (True, response)         if the response passes all checks.
    Returns (False, safe_fallback)   if a violation is detected.
    Fails open on any exception — always return the original response.
    """
    try:
        from guardrails.actions import (
            check_hallucination,
            check_jurisdiction,
            check_insurer_recommendation,
        )

        hallucination = await check_hallucination(response=response)
        if hallucination.get("flagged"):
            return False, (
                "I want to make sure I give you accurate information. "
                "Based on the documents provided, I cannot confirm that specific detail. "
                "Please verify this directly with your insurer."
            )

        jurisdiction = await check_jurisdiction(response=response)
        if jurisdiction.get("flagged"):
            return False, (
                "I can only provide guidance based on Indian insurance regulations "
                "and IRDAI guidelines."
            )

        recommendation = await check_insurer_recommendation(response=response)
        if recommendation.get("flagged"):
            return False, (
                "I'm not able to recommend specific insurance companies or products. "
                "For guidance on choosing a policy, please consult an IRDAI-registered "
                "insurance advisor."
            )

        return True, response

    except Exception:
        return True, response
