import os
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

load_dotenv()

CHROMA_PERSIST_PATH = os.getenv("CHROMA_PERSIST_PATH", "./chroma_db")
IRDAI_COLLECTION_NAME = "irdai_knowledge_base"


def get_chroma_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)


def get_user_collection(client: chromadb.PersistentClient, user_id: str):
    return client.get_or_create_collection(
        name=f"user_{user_id}",
        metadata={"hnsw:space": "cosine"},
    )


def get_irdai_collection(client: chromadb.PersistentClient):
    return client.get_or_create_collection(
        name=IRDAI_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def delete_document_vectors(client: chromadb.PersistentClient, user_id: str, document_id: str):
    collection = get_user_collection(client, user_id)
    collection.delete(where={"document_id": document_id})


def query_collection(collection, query_embeddings: list, n_results: int = 5) -> dict:
    return collection.query(
        query_embeddings=query_embeddings,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
