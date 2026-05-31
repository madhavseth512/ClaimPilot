import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

QUERY_ROUTER_PROMPT = """You are a query classification assistant.
Given the user query below, classify it into exactly one of these categories:

1. personal_doc — the answer requires looking at this user's uploaded documents
   Example: "What is my claim amount?", "What did my policy cover?"

2. general_insurance — the answer is a general insurance knowledge question
   Example: "How long does a motor claim take?", "What is a deductible?"

3. ambiguous — the query could fit multiple categories or is unclear
   Example: "What documents do I need?" (need to know for which intent)

4. off_topic — the query is unrelated to insurance
   Example: "What is the weather today?", "Help me write an email"

Respond ONLY in this JSON format:
{
  "category": "personal_doc" | "general_insurance" | "ambiguous" | "off_topic",
  "confidence": float between 0 and 1,
  "reasoning": "one sentence explanation"
}"""

CONFIDENCE_THRESHOLD = float(os.getenv("QUERY_ROUTER_CONFIDENCE_THRESHOLD", 0.75))


class QueryRouter:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    def route(self, query: str) -> dict:
        raise NotImplementedError("Implemented in Phase 5")

    def is_confident(self, result: dict) -> bool:
        return result.get("confidence", 0) >= CONFIDENCE_THRESHOLD
