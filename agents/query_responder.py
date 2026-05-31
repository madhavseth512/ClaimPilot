import os
from groq import Groq
from db.chroma import get_chroma_client, get_user_collection, get_irdai_collection, query_collection
from core.embedding_generator import EmbeddingGenerator
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are ClaimPilot, a professional insurance assistant for Indian customers.
You help users understand their insurance policies, file claims,
and navigate the insurance process.

All your answers must be:
- Grounded in the provided context (user documents or IRDAI regulations)
- Specific to Indian insurance regulations and IRDAI guidelines
- Clear, empathetic, and professional in tone
- Free of technical jargon unless the user demonstrates familiarity

You must NEVER:
- Provide medical advice beyond what is relevant to claim documentation
- Make up policy terms or claim amounts not present in the provided context
- Reference regulations from countries other than India
- Recommend specific insurance products or companies
- Discuss topics unrelated to insurance

If you do not have sufficient context to answer a query accurately,
say so clearly and suggest the user contact their insurer directly.

When answering from IRDAI documents, always cite the source:
Example: "According to the IRDAI Master Circular on Health Insurance..." """


class QueryResponder:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.embedder = EmbeddingGenerator()

    def respond_from_user_docs(
        self, query: str, user_id: str, case_id: str, conversation_history: list
    ) -> str:
        """RAG over user's ChromaDB collection. Implemented in Phase 5."""
        raise NotImplementedError("Implemented in Phase 5")

    def respond_from_irdai(
        self, query: str, conversation_history: list
    ) -> str:
        """RAG over IRDAI knowledge base. Implemented in Phase 5."""
        raise NotImplementedError("Implemented in Phase 5")
