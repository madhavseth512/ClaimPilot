import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

INTENT_CLASSIFICATION_PROMPT = """You are an insurance intent classifier.
Given the user's description of their situation, classify it into
exactly one of these insurance intents:

- motor_claim: vehicle accident, theft, damage to vehicle
- health_claim: hospitalisation, surgery, illness, disease, medical treatment,
                health insurance policy claim (even if the user says "health insurance")
- life_insurance: death claim, policy surrender, nominee filing — ONLY when someone has died
- travel_insurance: baggage loss, trip cancellation, medical expenses abroad
- home_property: fire, flood, burglary, property damage
- personal_accident: injury, workplace accident, disability, accidental death

IMPORTANT RULES:
- If the user explicitly mentions "health insurance", classify as health_claim.
- Only use life_insurance if the person has actually died or the claim is about a death.
- "My mother was sick / hospitalised / had a disease" → health_claim, not life_insurance.
- "I was injured but my car is fine" → personal_accident, not motor_claim.
- "Fell sick / got ill while travelling abroad / overseas / in another country" → travel_insurance. Medical expenses during international travel are a travel insurance claim, not health_claim.
- "Met with an accident and was hospitalised" → personal_accident. Hospitalisation caused by an accident is personal_accident. Only use health_claim when illness/condition is NOT caused by an accident.
- When both accident AND hospitalisation are mentioned → personal_accident takes priority over health_claim.

Respond ONLY in this JSON format:
{
  "intent": "<intent_name>",
  "confidence": float between 0 and 1,
  "description": "one sentence summary of the user's situation"
}

If the situation does not clearly match any intent, set confidence below 0.75."""

CONFIDENCE_THRESHOLD = float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", 0.75))


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences the LLM sometimes wraps JSON in."""
    if text.startswith("```"):
        lines = text.split("\n")
        # Drop first line (```json or ```) and last line (```)
        lines = lines[1:] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(lines)
    return text.strip()


class IntentClassifier:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    def classify(self, user_message: str) -> dict:
        """
        Returns {"intent": str, "confidence": float, "description": str}.
        On failure returns intent="unknown" with confidence=0.0.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": INTENT_CLASSIFICATION_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
                max_tokens=150,
            )
            content = response.choices[0].message.content.strip()
            content = _strip_code_fences(content)
            return json.loads(content)
        except json.JSONDecodeError:
            return {"intent": "unknown", "confidence": 0.0, "description": "Could not parse intent from response."}
        except Exception as e:
            return {"intent": "unknown", "confidence": 0.0, "description": str(e)}

    def is_confident(self, result: dict) -> bool:
        return result.get("confidence", 0) >= CONFIDENCE_THRESHOLD
