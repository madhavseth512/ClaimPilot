from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Form
from pydantic import BaseModel
from typing import Optional

from core.security import validate_token
from core.state_manager import get_graph
from agents.doc_processor import DocProcessor

router = APIRouter()


class UploadResponse(BaseModel):
    success: bool
    document_id: Optional[str]
    message: str
    pending_docs: list
    collected_docs: list
    case_status: str


@router.post("/", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    case_id: str = Form(...),
    document_type: str = Form(...),
    authorization: Optional[str] = Header(None),
):
    user_id = validate_token(authorization)

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="I currently only accept PDF files. Please upload your document in PDF format.",
        )

    graph = get_graph()
    config = {"configurable": {"thread_id": case_id}}

    # Verify the case exists
    existing = graph.get_state(config)
    if not existing.values:
        raise HTTPException(status_code=404, detail="Case not found.")

    # ── Run DocProcessor ──────────────────────────────────────────────────────
    file_bytes = await file.read()
    result = DocProcessor().process(
        file_bytes=file_bytes,
        filename=file.filename,
        user_id=user_id,
        case_id=case_id,
        document_type=document_type,
    )

    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["message"])

    # ── Update checklist state ────────────────────────────────────────────────
    current = existing.values
    pending = list(current.get("pending_docs", []))
    collected = list(current.get("collected_docs", []))

    # Move the uploaded document type from pending to collected
    if document_type in pending:
        pending.remove(document_type)
    if document_type not in collected:
        collected.append(document_type)

    # ── Invoke graph to generate acknowledgement message ──────────────────────
    graph_result = graph.invoke(
        {
            "input_type": "file",
            "collected_docs": collected,
            "pending_docs": pending,
            "last_uploaded_doc": document_type,
            "current_query": None,
        },
        config=config,
    )

    return UploadResponse(
        success=True,
        document_id=result["document_id"],
        message=graph_result.get("last_response", result["message"]),
        pending_docs=graph_result.get("pending_docs", pending),
        collected_docs=graph_result.get("collected_docs", collected),
        case_status=graph_result.get("case_status", "active"),
    )
