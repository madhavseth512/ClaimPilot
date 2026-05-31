from agents.doc_processor import DocProcessor

processor = DocProcessor()


def ingest_document(
    file_bytes: bytes,
    filename: str,
    user_id: str,
    case_id: str,
    document_type: str,
) -> dict:
    """
    Entry point for all PDF uploads. Validates format then triggers DocProcessor.
    Returns dict with keys: success, document_id, message.
    Implemented in Phase 3.
    """
    raise NotImplementedError("Implemented in Phase 3")
