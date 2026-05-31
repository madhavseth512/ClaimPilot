from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from typing import Optional

router = APIRouter()


@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    case_id: str = None,
    document_type: str = None,
    authorization: Optional[str] = Header(None),
):
    """
    Receive a PDF upload, validate it, and trigger the DocProcessor pipeline.
    Returns upload status and updated checklist.
    Implemented in Phase 8.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="I currently only accept PDF files. Please upload your document in PDF format.",
        )
    raise HTTPException(status_code=501, detail="Not implemented yet")
