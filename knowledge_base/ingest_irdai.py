"""
Script to populate the IRDAI knowledge base ChromaDB collection.

Run once after downloading IRDAI PDFs to knowledge_base/irdai_docs/.
Each document is tagged with its source name for citation in responses.

Usage:
    python knowledge_base/ingest_irdai.py
"""
import os
from pathlib import Path
from db.chroma import get_chroma_client, get_irdai_collection
from ingestion.pdf_extractor import PDFExtractor
from core.semantic_chunker import SemanticChunker
from core.embedding_generator import EmbeddingGenerator

IRDAI_DOCS_DIR = Path(__file__).parent / "irdai_docs"

DOCUMENT_REGISTRY = {
    "irdai_health_master_circular.pdf": "IRDAI Master Circular on Health Insurance",
    "irdai_motor_master_circular.pdf": "IRDAI Master Circular on Motor Insurance",
    "irdai_life_master_circular.pdf": "IRDAI Master Circular on Life Insurance",
    "irdai_travel_guidelines.pdf": "IRDAI Guidelines on Travel Insurance",
    "irdai_home_property_guidelines.pdf": "IRDAI Guidelines on Home and Property Insurance",
    "irdai_personal_accident_guidelines.pdf": "IRDAI Guidelines on Personal Accident Insurance",
    "irdai_policyholder_protection.pdf": "IRDAI Policyholder Protection Guidelines",
    "irdai_ombudsman_guidelines.pdf": "IRDAI Insurance Ombudsman Guidelines",
}


def ingest_all():
    """Implemented in Phase 4."""
    raise NotImplementedError("Implemented in Phase 4")


if __name__ == "__main__":
    ingest_all()
