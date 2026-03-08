"""
FastAPI dependency helpers — reusable across all routers.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token

# ── Bearer-token extractor ────────────────────────────────────────────────────

_bearer = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """
    Validate the JWT from the Authorization header and return the user dict.

    Raises 401 if the token is missing, expired, or invalid.
    Raises 404 if the user encoded in the token no longer exists in the DB.
    """
    payload = decode_access_token(credentials.credentials)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub")
    role: str | None = payload.get("role")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload malformed — missing 'sub'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Query the database (not the old in-memory list)
    from app.services.auth_service import get_user_by_id
    user = get_user_by_id(user_id, role=role)
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


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Guard decorator — only allows users with role == 'admin'."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to admin accounts.",
        )
    return current_user
