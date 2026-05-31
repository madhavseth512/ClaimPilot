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


class IntentClassifier:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    def classify(self, user_message: str) -> dict:
        raise NotImplementedError("Implemented in Phase 5")

    def is_confident(self, result: dict) -> bool:
        return result.get("confidence", 0) >= CONFIDENCE_THRESHOLD
