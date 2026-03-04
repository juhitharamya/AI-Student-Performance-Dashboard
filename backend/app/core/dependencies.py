"""
FastAPI dependency helpers — reusable across all routers.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core import data_store as db
from app.core.security import decode_access_token

# ── Bearer-token extractor ────────────────────────────────────────────────────

_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=True)


def get_current_user(
    token: str = Depends(_oauth2),
) -> dict:
    """
    Validate the JWT from the Authorization header and return the user dict.

    Raises 401 if the token is missing, expired, or invalid.
    Raises 404 if the user encoded in the token no longer exists.
    """
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload malformed — missing 'sub'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = next((u for u in db.USERS if u["id"] == user_id), None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User belonging to this token no longer exists.",
        )

    return user


def require_faculty(current_user: dict = Depends(get_current_user)) -> dict:
    """Guard decorator — only allows users with role == 'faculty'."""
    if current_user["role"] != "faculty":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to faculty accounts.",
        )
    return current_user


def require_student(current_user: dict = Depends(get_current_user)) -> dict:
    """Guard decorator — only allows users with role == 'student'."""
    if current_user["role"] != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to student accounts.",
        )
    return current_user
