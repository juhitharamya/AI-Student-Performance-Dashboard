"""
Auth service — now backed by SQLite via SQLAlchemy.
"""
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import app.core.database as _db
from app.core.security import verify_password, create_access_token, hash_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


def _get_db() -> Session:
    """Always use the current module-level SessionLocal so tests can patch it."""
    return _db.SessionLocal()


def authenticate_user(email: str, password: str, role: str) -> dict:
    """
    Look up the user in the database.
    - If found: verify password.
    - If NOT found: auto-register and return new user.
    """
    db = _get_db()
    try:
        user = db.query(User).filter(
            User.email == email.lower(),
            User.role == role,
        ).first()

        if user is None:
            # Auto-create a new account
            email_local = email.split("@")[0]
            parts = email_local.replace(".", " ").replace("_", " ").split()
            name = " ".join(p.capitalize() for p in parts) if parts else email_local.capitalize()
            initials = (name[0] + name[-1]).upper() if len(name) >= 2 else name[:2].upper()

            new_user = User(
                id=f"u{uuid.uuid4().hex[:8]}",
                name=name,
                email=email.lower(),
                password=hash_password(password),
                role=role,
                avatar_initials=initials,
            )
            if role == "student":
                new_user.roll_no   = f"STU{uuid.uuid4().hex[:6].upper()}"
                new_user.cgpa      = 0.0
                new_user.year      = "1st Year"
                new_user.section   = "Section A"
                new_user.department = "General"
            else:
                new_user.title      = "Lecturer"
                new_user.department = "General"

            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user.to_dict()

        # Existing user — verify password
        if not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user.to_dict()
    finally:
        db.close()


def register_user(body: RegisterRequest) -> dict:
    """
    Create a new user account and return a ready-to-use JWT.
    Raises 409 if email+role already exists.
    """
    db = _get_db()
    try:
        existing = db.query(User).filter(
            User.email == body.email.lower(),
            User.role == body.role,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An account with this email already exists for role '{body.role}'.",
            )

        parts = body.name.strip().split()
        initials = (
            (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else body.name[:2].upper()
        )

        new_user = User(
            id=f"u{uuid.uuid4().hex[:8]}",
            name=body.name.strip(),
            email=body.email.lower(),
            password=hash_password(body.password),
            role=body.role,
            avatar_initials=initials,
        )
        if body.role == "student":
            new_user.roll_no    = getattr(body, "roll_no", None) or f"STU{uuid.uuid4().hex[:6].upper()}"
            new_user.cgpa       = 0.0
            new_user.year       = getattr(body, "year", None) or "1st Year"
            new_user.section    = getattr(body, "section", None) or "Section A"
            new_user.department = getattr(body, "department", None) or "General"
        else:
            new_user.title      = getattr(body, "title", None) or "Lecturer"
            new_user.department = getattr(body, "department", None) or "General"

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token({"sub": new_user.id, "role": new_user.role})
        return {
            "id":             new_user.id,
            "name":           new_user.name,
            "email":          new_user.email,
            "role":           new_user.role,
            "avatar_initials": new_user.avatar_initials,
            "access_token":   token,
            "token_type":     "bearer",
        }
    finally:
        db.close()


def create_token_for_user(user: dict) -> dict:
    token = create_access_token({"sub": user["id"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "name": user["name"],
        "avatar_initials": user.get("avatar_initials", "??"),
    }


def get_user_by_id(user_id: str) -> dict | None:
    db = _get_db()
    try:
        u = db.query(User).filter(User.id == user_id).first()
        return u.to_dict() if u else None
    finally:
        db.close()


def get_me(current_user: dict) -> dict:
    """Return the response payload for GET /auth/me."""
    return {
        "id": current_user.get("id"),
        "name": current_user.get("name"),
        "email": current_user.get("email"),
        "role": current_user.get("role"),
        "avatar_initials": current_user.get("avatar_initials", "??"),
    }
