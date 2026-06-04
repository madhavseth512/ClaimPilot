import uuid
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from core.security import validate_token
from core.state_manager import get_graph, make_initial_state
from guardrails.runner import check_input, check_output

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    case_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    case_id: str
    pending_docs: list
    case_status: str


@router.post("/", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    authorization: Optional[str] = Header(None),
):
    user_id = validate_token(authorization)

    # ── Input guardrail ───────────────────────────────────────────────────────
    passes, block_msg = await check_input(payload.message)
    if not passes:
        case_id = payload.case_id or str(uuid.uuid4())
        return ChatResponse(
            response=block_msg,
            case_id=case_id,
            pending_docs=[],
            case_status="active",
        )

    # ── Resolve case ──────────────────────────────────────────────────────────
    graph = get_graph()
    case_id = payload.case_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": case_id}}

    # Check if this case already has state in the checkpointer
    existing = graph.get_state(config)
    if existing.values:
        # Existing case — partial update only
        state_input = {
            "current_query": payload.message,
            "input_type": "text",
        }
    else:
        # New case — provide full initial state
        state_input = make_initial_state(user_id, case_id, payload.message)

    # ── Invoke LangGraph ──────────────────────────────────────────────────────
    try:
        result = graph.invoke(state_input, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    raw_response = result.get("last_response", "I'm sorry, something went wrong. Please try again.")

    # ── Output guardrail ──────────────────────────────────────────────────────
    _, final_response = await check_output(raw_response)

    return ChatResponse(
        response=final_response,
        case_id=case_id,
        pending_docs=result.get("pending_docs", []),
        case_status=result.get("case_status", "active"),
    )


@router.post("/resume", response_model=ChatResponse)
async def resume_session(
    case_id: str,
    authorization: Optional[str] = Header(None),
):
    """Signal a session resumption — shows the user their case status."""
    validate_token(authorization)

    graph = get_graph()
    config = {"configurable": {"thread_id": case_id}}

    existing = graph.get_state(config)
    if not existing.values:
        raise HTTPException(status_code=404, detail="Case not found.")

    result = graph.invoke(
        {"input_type": "resume", "current_query": ""},
        config=config,
    )

    return ChatResponse(
        response=result.get("last_response", ""),
        case_id=case_id,
        pending_docs=result.get("pending_docs", []),
        case_status=result.get("case_status", "active"),
    )
