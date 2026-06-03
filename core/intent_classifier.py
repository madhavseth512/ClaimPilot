import json
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

INTENT_CLASSIFICATION_PROMPT = """You are an insurance intent classifier.
Given the user's description of their situation, classify it into
exactly one of these insurance intents:

- motor_claim: vehicle accident, theft, damage
- health_claim: hospitalisation, surgery, medical diagnosis
- life_insurance: death claim, policy surrender, nominee filing
- travel_insurance: baggage loss, trip cancellation, medical abroad
- home_property: fire, flood, burglary, property damage
- personal_accident: injury, workplace accident, disability, accidental death

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
