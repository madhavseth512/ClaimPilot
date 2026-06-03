import os
from groq import Groq
from db.chroma import query_user_collection, query_irdai_collection
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
        """RAG over the user's ChromaDB collection for the given case."""
        query_embedding = self.embedder.embed_single(query)
        results = query_user_collection(user_id, query_embedding, case_id=case_id, n_results=5)

        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if docs:
            context_parts = [
                f"[Document: {meta.get('filename', 'uploaded document')}]\n{doc}"
                for doc, meta in zip(docs, metadatas)
            ]
            context = "\n\n".join(context_parts)
        else:
            context = "No documents have been uploaded for this case yet."

        system = f"{SYSTEM_PROMPT}\n\nThe following is extracted from the user's uploaded documents:\n\n{context}"

        messages = [{"role": "system", "content": system}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": query})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()

    def respond_from_irdai(
        self, query: str, conversation_history: list
    ) -> str:
        """RAG over the IRDAI knowledge base with source citation."""
        query_embedding = self.embedder.embed_single(query)
        results = query_irdai_collection(query_embedding, n_results=5)

        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if docs:
            context_parts = [
                f"[Source: {meta.get('source_name', meta.get('source', 'IRDAI document'))}]\n{doc}"
                for doc, meta in zip(docs, metadatas)
            ]
            context = "\n\n".join(context_parts)
        else:
            context = "No relevant IRDAI regulatory information found."

        system = f"{SYSTEM_PROMPT}\n\nThe following is from official IRDAI regulatory documents:\n\n{context}"

        messages = [{"role": "system", "content": system}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": query})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()
