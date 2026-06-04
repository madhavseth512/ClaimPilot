from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from db.postgres import get_db, Case
from core.security import validate_token
from core.state_manager import get_graph

router = APIRouter()


class CaseSummary(BaseModel):
    case_id: str
    intent: str
    case_status: str
    created_at: str
    pending_docs: list
    collected_docs: list
    total_docs: int


@router.get("/", response_model=list[CaseSummary])
async def get_cases(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user_id = validate_token(authorization)

    cases = db.query(Case).filter(Case.user_id == user_id).all()
    if not cases:
        return []

    graph = get_graph()
    summaries = []

    for case in cases:
        config = {"configurable": {"thread_id": case.case_id}}
        state_snapshot = graph.get_state(config)
        state = state_snapshot.values if state_snapshot.values else {}

        summaries.append(CaseSummary(
            case_id=case.case_id,
            intent=case.intent,
            case_status=case.case_status,
            created_at=case.created_at.isoformat(),
            pending_docs=state.get("pending_docs", []),
            collected_docs=state.get("collected_docs", []),
            total_docs=len(state.get("required_docs", [])),
        ))

    return summaries


@router.get("/{case_id}", response_model=CaseSummary)
async def get_case(
    case_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    user_id = validate_token(authorization)

    case = db.query(Case).filter(
        Case.case_id == case_id,
        Case.user_id == user_id,
    ).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    graph = get_graph()
    config = {"configurable": {"thread_id": case_id}}
    state_snapshot = graph.get_state(config)
    state = state_snapshot.values if state_snapshot.values else {}

    return CaseSummary(
        case_id=case.case_id,
        intent=case.intent,
        case_status=case.case_status,
        created_at=case.created_at.isoformat(),
        pending_docs=state.get("pending_docs", []),
        collected_docs=state.get("collected_docs", []),
        total_docs=len(state.get("required_docs", [])),
    )
