import os
import uuid
from typing import List
import chromadb
from dotenv import load_dotenv

load_dotenv()

CHROMA_PERSIST_PATH = os.getenv("CHROMA_PERSIST_PATH", "./chroma_store")
IRDAI_COLLECTION_NAME = "irdai_knowledge_base"

# Module-level singleton client
_client = None


def get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
    return _client


def get_user_collection(user_id: str):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=f"user_{user_id}",
        metadata={"hnsw:space": "cosine"},
    )


def get_irdai_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=IRDAI_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def store_vectors(
    user_id: str,
    document_id: str,
    case_id: str,
    document_type: str,
    filename: str,
    chunks: List[dict],
    embeddings: List[List[float]],
) -> int:
    """
    Store document chunks and their embeddings in the user's ChromaDB collection.
    Returns the number of chunks stored.
    """
    collection = get_user_collection(user_id)

    ids = [f"{document_id}_chunk_{c['chunk_index']}" for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [
        {
            "user_id": user_id,
            "case_id": case_id,
            "document_id": document_id,
            "document_type": document_type,
            "filename": filename,
            "chunk_index": c["chunk_index"],
        }
        for c in chunks
    ]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)


def store_irdai_vectors(
    source_doc_name: str,
    chunks: List[dict],
    embeddings: List[List[float]],
    source_display_name: str = None,
) -> int:
    """Store IRDAI knowledge base chunks. Used by ingest_irdai.py in Phase 4."""
    collection = get_irdai_collection()

    ids = [f"{source_doc_name}_chunk_{c['chunk_index']}" for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [
        {
            "source": source_doc_name,
            "source_name": source_display_name or source_doc_name,
            "chunk_index": c["chunk_index"],
        }
        for c in chunks
    ]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)


def query_user_collection(
    user_id: str,
    query_embedding: List[float],
    case_id: str = None,
    n_results: int = 5,
) -> dict:
    """Semantic search over a user's documents. Optionally filtered by case_id."""
    collection = get_user_collection(user_id)
    where = {"case_id": case_id} if case_id else None

    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )


def query_irdai_collection(
    query_embedding: List[float],
    n_results: int = 5,
) -> dict:
    """Semantic search over the IRDAI knowledge base."""
    collection = get_irdai_collection()
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )


def delete_document_vectors(user_id: str, document_id: str):
    """Remove all vectors for a specific document from the user's collection."""
    collection = get_user_collection(user_id)
    collection.delete(where={"document_id": document_id})
