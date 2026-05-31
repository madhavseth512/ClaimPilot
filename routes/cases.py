from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from typing import Optional
from db.postgres import get_db

router = APIRouter()


@router.get("/")
async def get_cases(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Return all active cases for the authenticated user. Implemented in Phase 8."""
    raise HTTPException(status_code=501, detail="Not implemented yet")
