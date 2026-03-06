"""
Auth service — now backed by SQLite via SQLAlchemy.
"""
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

import app.core.database as _db
from app.core.security import verify_password, create_access_token, hash_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


def _get_db() -> Session:
    """Always use the current module-level SessionLocal so tests can patch it."""
    return _db.SessionLocal()


def _normalize_roll_no_str(s: str) -> str:
    value = (s or "").strip()
    if value.endswith(".0") and value[:-2].isdigit():
        return value[:-2]
    return value


def _looks_like_roll_no(value: str) -> bool:
    """
    Heuristic: roll numbers usually include digits and are short-ish.
    Examples: 23Q91A6601, CS2023045, 23q91a6601
    """
    s = (value or "").strip()
    if not (5 <= len(s) <= 32):
        return False
    return any(ch.isdigit() for ch in s)


def _make_initials(name: str) -> str:
    parts = (name or "").strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return (name or "")[:2].upper() if name else "??"


def _sync_student_profile_from_marks(db: Session, user: User) -> None:
    """
    Hydrate missing/placeholder student profile fields from uploaded marks.

    This makes the student dashboard show correct name/year/section/department
    without manual changes in Supabase.
    """
    if user.role != "student":
        return

    email_local = (user.email or "").split("@")[0]
    roll_candidates: list[str] = []

    if user.roll_no and user.roll_no.strip():
        roll_candidates.append(user.roll_no.strip())
    if _looks_like_roll_no(user.name or ""):
        roll_candidates.append((user.name or "").strip())
    if _looks_like_roll_no(email_local):
        roll_candidates.append(email_local.strip())

    roll_candidates = [_normalize_roll_no_str(r) for r in roll_candidates if r]
    if not roll_candidates:
        return

    from app.models.student_mark import StudentMark
    from app.models.uploaded_file import UploadedFile

    q = (
        db.query(StudentMark, UploadedFile)
        .join(UploadedFile, UploadedFile.id == StudentMark.uploaded_file_id)
        .filter(func.lower(StudentMark.roll_no).in_([r.lower() for r in roll_candidates]))
        .order_by(UploadedFile.created_at.desc(), StudentMark.created_at.desc())
    )
    row = q.first()
    if not row:
        return

    sm, uf = row

    # If roll_no is missing or clearly auto-generated, set it from the matched record.
    if not (user.roll_no and user.roll_no.strip()) or user.roll_no.upper().startswith("STU") or not _looks_like_roll_no(user.roll_no):
        user.roll_no = (sm.roll_no or roll_candidates[0]).strip()

    # Update "name" only if it's clearly a placeholder (e.g. equals roll/email local).
    name_norm = (user.name or "").strip().lower()
    placeholder_names = {r.lower() for r in roll_candidates}
    if _looks_like_roll_no(email_local):
        placeholder_names.add(email_local.lower())
    if name_norm in placeholder_names and (sm.student_name or "").strip():
        user.name = sm.student_name.strip()
        user.avatar_initials = _make_initials(user.name)

    # Update class metadata only if still defaults/placeholders.
    if (user.department or "") in {"", "General", "N/A"} and (uf.department or "").strip():
        user.department = uf.department.strip()
    if (user.year or "") in {"", "1st Year", "N/A"} and (uf.year or "").strip():
        user.year = uf.year.strip()
    if (user.section or "") in {"", "Section A", "A", "N/A"} and (uf.section or "").strip():
        user.section = uf.section.strip()


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
                new_user.roll_no   = (
                    email_local.strip()
                    if _looks_like_roll_no(email_local)
                    else f"STU{uuid.uuid4().hex[:6].upper()}"
                )
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
            _sync_student_profile_from_marks(db, new_user)
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
        _sync_student_profile_from_marks(db, user)
        db.commit()
        db.refresh(user)
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
