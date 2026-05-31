from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from db.postgres import get_db

router = APIRouter()


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register")
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new user. Returns user_id and session token. Implemented in Phase 8."""
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/login")
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user. Returns session token. Implemented in Phase 8."""
    raise HTTPException(status_code=501, detail="Not implemented yet")
