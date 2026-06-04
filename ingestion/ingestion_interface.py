from agents.doc_processor import DocProcessor

_processor = DocProcessor()


def ingest_document(
    file_bytes: bytes,
    filename: str,
    user_id: str,
    case_id: str,
    document_type: str,
) -> dict:
    """
    Entry point for all PDF uploads.
    Delegates to DocProcessor which validates, extracts, chunks, embeds, and stores.
    Returns: {"success": bool, "document_id": str, "chunks_stored": int, "message": str}
    """
    return _processor.process(file_bytes, filename, user_id, case_id, document_type)
