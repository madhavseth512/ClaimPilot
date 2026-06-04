"""
Custom NeMo Guardrails actions for output rail checks.
Each action is called from flows.co via the `execute` keyword.
All checks use Groq (same model as the main app) with strict yes/no prompts.
"""
import os
from groq import Groq
from nemoguardrails.actions import action
from dotenv import load_dotenv

load_dotenv()

_groq_client = None


def _get_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _groq_client


def _yes_no_check(prompt: str) -> bool:
    """Runs a yes/no classification prompt. Returns True if answer is YES."""
    response = _get_client().chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=5,
    )
    answer = response.choices[0].message.content.strip().upper()
    return answer.startswith("YES")


@action(name="check_hallucination")
async def check_hallucination(response: str, **kwargs) -> dict:
    """
    Detects if the response asserts specific facts (claim amounts, dates,
    policy terms, coverage limits) that are not verifiable from IRDAI
    regulatory documents or context provided to the model.
    """
    prompt = (
        "You are a fact-checking assistant. Read the insurance assistant response below "
        "and answer YES or NO to this question:\n\n"
        "Does this response state specific numerical values such as claim amounts, "
        "rupee figures, coverage limits, policy durations, or specific dates that "
        "appear to be invented or assumed rather than cited from a source?\n\n"
        f"Response:\n{response}\n\n"
        "Answer YES if specific unverified numbers or dates are present. "
        "Answer NO if the response is general, cites IRDAI sources, or asks for documents.\n"
        "Answer (YES or NO only):"
    )
    return {"flagged": _yes_no_check(prompt)}


@action(name="check_jurisdiction")
async def check_jurisdiction(response: str, **kwargs) -> dict:
    """
    Detects if the response references insurance regulations, laws, or
    regulatory bodies from countries other than India.
    """
    prompt = (
        "You are a compliance checker for an Indian insurance assistant. "
        "Read the response below and answer YES or NO:\n\n"
        "Does this response reference insurance laws, regulations, or regulatory bodies "
        "from any country OTHER than India? "
        "(e.g., UK FCA, US SEC, EU regulations, Australian APRA, etc.)\n\n"
        f"Response:\n{response}\n\n"
        "Answer YES if non-Indian regulations are referenced. "
        "Answer NO if the response only references IRDAI, Indian laws, or is general.\n"
        "Answer (YES or NO only):"
    )
    return {"flagged": _yes_no_check(prompt)}


@action(name="check_insurer_recommendation")
async def check_insurer_recommendation(response: str, **kwargs) -> dict:
    """
    Detects if the response recommends or negatively compares specific
    insurance companies or products by name.
    """
    prompt = (
        "You are a compliance checker. Read the insurance assistant response below "
        "and answer YES or NO:\n\n"
        "Does this response recommend a specific insurance company by name, "
        "suggest one insurer is better than another, or compare specific insurance "
        "products from named companies?\n\n"
        f"Response:\n{response}\n\n"
        "Answer YES if specific insurer names are recommended or compared. "
        "Answer NO if the response is general or only mentions IRDAI/regulators.\n"
        "Answer (YES or NO only):"
    )
    return {"flagged": _yes_no_check(prompt)}
