import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from ingestion.pdf_extractor import PDFExtractor
from core.semantic_chunker import SemanticChunker
from core.embedding_generator import EmbeddingGenerator
from db.chroma import store_vectors
from db.postgres import SessionLocal, Document


class DocProcessor:

    def __init__(self):
        self.extractor = PDFExtractor()
        self.chunker = SemanticChunker()
        self.embedder = EmbeddingGenerator()

    def process(
        self,
        file_bytes: bytes,
        filename: str,
        user_id: str,
        case_id: str,
        document_type: str,
    ) -> dict:
        """
        Full ingestion pipeline:
        1. Validate PDF
        2. Extract text (digital or OCR)
        3. Chunk text
        4. Generate embeddings
        5. Store vectors in ChromaDB
        6. Write metadata to PostgreSQL
        Returns: {"success": bool, "document_id": str, "chunks_stored": int, "message": str}
        """
        # Step 1 — Validate
        is_valid, error_msg = self.extractor.validate_pdf(file_bytes)
        if not is_valid:
            return {"success": False, "document_id": None, "chunks_stored": 0, "message": error_msg}

        # Step 2 — Extract text
        try:
            text = self.extractor.extract(file_bytes)
        except Exception as e:
            return {
                "success": False,
                "document_id": None,
                "chunks_stored": 0,
                "message": "I was unable to read this document. Please ensure the file is not password-protected and try again.",
            }

        if not text.strip():
            return {
                "success": False,
                "document_id": None,
                "chunks_stored": 0,
                "message": "No readable text was found in this document. Please try a different file.",
            }

        # Step 3 — Chunk
        document_id = str(uuid.uuid4())
        chunks = self.chunker.chunk(
            text,
            metadata={
                "user_id": user_id,
                "case_id": case_id,
                "document_id": document_id,
                "document_type": document_type,
                "filename": filename,
            },
        )

        if not chunks:
            return {
                "success": False,
                "document_id": None,
                "chunks_stored": 0,
                "message": "The document could not be split into readable sections. Please try again.",
            }

        # Step 4 — Embed
        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.embed(texts)

        # Step 5 — Store in ChromaDB
        chunks_stored = store_vectors(
            user_id=user_id,
            document_id=document_id,
            case_id=case_id,
            document_type=document_type,
            filename=filename,
            chunks=chunks,
            embeddings=embeddings,
        )

        # Step 6 — Write metadata to PostgreSQL
        db: Session = SessionLocal()
        try:
            doc_row = Document(
                document_id=document_id,
                case_id=case_id,
                user_id=user_id,
                filename=filename,
                document_type=document_type,
                upload_timestamp=datetime.utcnow(),
                chroma_collection_ref=f"user_{user_id}",
            )
            db.add(doc_row)
            db.commit()
        finally:
            db.close()

        return {
            "success": True,
            "document_id": document_id,
            "chunks_stored": chunks_stored,
            "message": f"Thank you, I've received your {document_type}.",
        }
