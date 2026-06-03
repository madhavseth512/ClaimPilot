"""
Script to populate the IRDAI knowledge base ChromaDB collection.

Run once after downloading IRDAI PDFs to knowledge_base/irdai_docs/.
Each document is tagged with its source name for citation in responses.

Usage:
    python knowledge_base/ingest_irdai.py
"""
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path when script is run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.chroma import get_irdai_collection, store_irdai_vectors
from ingestion.pdf_extractor import PDFExtractor
from core.semantic_chunker import SemanticChunker
from core.embedding_generator import EmbeddingGenerator

IRDAI_DOCS_DIR = Path(__file__).parent / "irdai_docs"

DOCUMENT_REGISTRY = {
    # --- Regulatory Master Circulars (authoritative source) ---
    "irdai_health_master_circular.pdf": "IRDAI Master Circular on Health Insurance Business",
    "irdai_life_master_circular.pdf": "IRDAI Master Circular on Life Insurance Products",
    # Covers Motor, Travel, Home/Property, and Personal Accident in one document
    "irdai_general_insurance_master_circular.pdf": "IRDAI Master Circular on General Insurance Business",
    "irdai_policyholder_protection.pdf": "IRDAI Master Circular on Protection of Policyholders Interests",
    "irdai_ombudsman_guidelines.pdf": "IRDAI Grievance Redressal System Handbook",

    # --- Consumer Handbooks (plain-language guides for policyholders) ---
    "irdai_health_handbook.pdf": "IRDAI Health Insurance Consumer Handbook",
    "irdai_motor_handbook.pdf": "IRDAI Motor Insurance Consumer Handbook",
    "irdai_life_handbook.pdf": "IRDAI Life Insurance Consumer Handbook",
}


def ingest_all():
    """
    Populate the ChromaDB irdai_knowledge_base collection from all PDFs in DOCUMENT_REGISTRY.
    Idempotent — skips documents already ingested (detected by chunk_0 ID presence).
    Run once: python knowledge_base/ingest_irdai.py
    """
    extractor = PDFExtractor()
    chunker = SemanticChunker()
    embedder = EmbeddingGenerator()
    collection = get_irdai_collection()

    processed = 0
    skipped = 0

    print("Starting IRDAI knowledge base ingestion...")
    print(f"Documents directory: {IRDAI_DOCS_DIR}\n")

    for filename, source_name in DOCUMENT_REGISTRY.items():
        pdf_path = IRDAI_DOCS_DIR / filename

        if not pdf_path.exists():
            print(f"[MISSING] {filename} — not found in irdai_docs/, skipping")
            continue

        # Idempotency: skip if already ingested
        existing = collection.get(ids=[f"{filename}_chunk_0"])
        if existing["ids"]:
            print(f"[SKIP]    {filename} already ingested")
            skipped += 1
            continue

        size_mb = pdf_path.stat().st_size / 1024 / 1024
        print(f"[START]   {source_name}")
        print(f"          File: {filename} ({size_mb:.1f} MB)")

        file_bytes = pdf_path.read_bytes()

        # Extract
        text = extractor.extract(file_bytes)
        if not text.strip():
            print(f"[WARN]    No text extracted from {filename} — skipping\n")
            continue

        print(f"          Extracted {len(text):,} characters")

        # Chunk
        chunks = chunker.chunk(text, metadata={"source": filename})
        if not chunks:
            print(f"[WARN]    No chunks produced for {filename} — skipping\n")
            continue

        print(f"          Split into {len(chunks)} chunks — embedding...")

        # Embed
        texts = [c["text"] for c in chunks]
        embeddings = embedder.embed(texts)

        # Store
        stored = store_irdai_vectors(filename, chunks, embeddings, source_display_name=source_name)
        processed += 1
        print(f"[DONE]    {stored} chunks stored\n")

    print("Ingestion complete.")
    print(f"  Documents processed : {processed}")
    print(f"  Documents skipped   : {skipped}")
    print(f"  Total chunks in knowledge base: {collection.count()}")


if __name__ == "__main__":
    ingest_all()
