"""
Token management and password hashing for ClaimPilot auth.
Tokens are stored in-memory (lost on server restart — acceptable for demo).
"""
import secrets
import bcrypt
from fastapi import HTTPException

# token → user_id
_tokens: dict[str, str] = {}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), stored_hash.encode())


def create_token(user_id: str) -> str:
    token = secrets.token_hex(32)
    _tokens[token] = user_id
    return token


def validate_token(authorization: str | None) -> str:
    """Extract and validate Bearer token. Returns user_id or raises 401."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header.")
    token = authorization[7:]
    user_id = _tokens.get(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return user_id
