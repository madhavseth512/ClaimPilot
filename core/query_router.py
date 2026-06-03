import json
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


def _strip_code_fences(text: str) -> str:
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:] if lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(lines)
    return text.strip()


class QueryRouter:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    def route(self, query: str) -> dict:
        """
        Returns {"category": str, "confidence": float, "reasoning": str}.
        Categories: personal_doc | general_insurance | ambiguous | off_topic.
        On failure returns category="ambiguous" with confidence=0.0.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": QUERY_ROUTER_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0.1,
                max_tokens=150,
            )
            content = response.choices[0].message.content.strip()
            content = _strip_code_fences(content)
            return json.loads(content)
        except json.JSONDecodeError:
            return {"category": "ambiguous", "confidence": 0.0, "reasoning": "Could not parse routing response."}
        except Exception as e:
            return {"category": "ambiguous", "confidence": 0.0, "reasoning": str(e)}

    def is_confident(self, result: dict) -> bool:
        return result.get("confidence", 0) >= CONFIDENCE_THRESHOLD
