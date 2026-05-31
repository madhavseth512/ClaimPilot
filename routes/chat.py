from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    case_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    case_id: str
    pending_docs: list


@router.post("/", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Main conversation endpoint. Runs the full agent pipeline:
    Guardrails → Intent Classifier → LangGraph → Response.
    Implemented in Phase 8.
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")
