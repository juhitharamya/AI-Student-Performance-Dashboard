"""
Auth service — now backed by SQLite via SQLAlchemy.
"""
import uuid
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

import app.core.database as _db
from app.core.security import verify_password, create_access_token, hash_password
from app.models.admin_user import AdminUser
from app.models.faculty_user import FacultyUser
from app.models.student_user import StudentUser
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


def _sync_student_profile_from_marks(db: Session, user: StudentUser) -> None:
    """
    Hydrate missing/placeholder student profile fields from uploaded marks.

    This makes the student dashboard show correct name/year/section/department
    without manual changes in Supabase.
    """
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
        if role == "admin":
            user = db.query(AdminUser).filter(AdminUser.email == email.lower()).first()
        elif role == "faculty":
            user = db.query(FacultyUser).filter(FacultyUser.email == email.lower()).first()
        elif role == "student":
            user = db.query(StudentUser).filter(StudentUser.email == email.lower()).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Role must be one of 'admin', 'faculty', or 'student'.",
            )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account not found. Contact admin for access.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Existing user — verify password
        if not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if role == "student":
            _sync_student_profile_from_marks(db, user)
            db.commit()
            db.refresh(user)
        return user.to_dict()
    finally:
        db.close()


def register_user(body: RegisterRequest) -> dict:
    """
    Create the initial admin account and return a ready-to-use JWT.
    """
    db = _get_db()
    try:
        if body.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin signup is allowed here.",
            )
        if db.query(AdminUser).count() > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Admin already exists. Please sign in.",
            )

        existing = db.query(AdminUser).filter(AdminUser.email == body.email.lower()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An account with this email already exists for role '{body.role}'.",
            )

        parts = body.name.strip().split()
        initials = (
            (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else body.name[:2].upper()
        )

        new_user = AdminUser(
            id=f"a{uuid.uuid4().hex[:8]}",
            name=body.name.strip(),
            email=body.email.lower(),
            password=hash_password(body.password),
            avatar_initials=initials,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = create_access_token({"sub": new_user.id, "role": body.role})
        return {
            "id":             new_user.id,
            "name":           new_user.name,
            "email":          new_user.email,
            "role":           body.role,
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


def get_user_by_id(user_id: str, role: str | None = None) -> dict | None:
    db = _get_db()
    try:
        if role == "admin":
            u = db.query(AdminUser).filter(AdminUser.id == user_id).first()
            return u.to_dict() if u else None
        if role == "faculty":
            u = db.query(FacultyUser).filter(FacultyUser.id == user_id).first()
            return u.to_dict() if u else None
        if role == "student":
            u = db.query(StudentUser).filter(StudentUser.id == user_id).first()
            return u.to_dict() if u else None
        u_admin = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if u_admin:
            return u_admin.to_dict()
        u_fac = db.query(FacultyUser).filter(FacultyUser.id == user_id).first()
        if u_fac:
            return u_fac.to_dict()
        u_stu = db.query(StudentUser).filter(StudentUser.id == user_id).first()
        return u_stu.to_dict() if u_stu else None
    finally:
        db.close()


def admin_exists() -> bool:
    db = _get_db()
    try:
        return db.query(AdminUser).count() > 0
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
