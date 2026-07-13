"""Admin-only user management service."""

import uuid

import app.core.database as _db
from app.core.security import hash_password
from app.models.faculty_user import FacultyUser
from app.models.student_user import StudentUser
from fastapi import HTTPException, status


def list_managed_users() -> list[dict]:
    with _db.SessionLocal() as db:
        faculty_rows = db.query(FacultyUser).all()
        student_rows = db.query(StudentUser).all()
        out: list[dict] = []
        out.extend(
            [
                {
                    "id": r.id,
                    "name": r.name,
                    "email": r.email,
                    "role": "faculty",
                    "title": r.title,
                    "department": r.department or "",
                    "year": "",
                    "section": "",
                    "roll_no": "",
                }
                for r in faculty_rows
            ]
        )
        out.extend(
            [
                {
                    "id": r.id,
                    "name": r.name,
                    "email": r.email,
                    "role": "student",
                    "title": None,
                    "department": r.department or "",
                    "year": r.year or "",
                    "section": r.section or "",
                    "roll_no": r.roll_no or "",
                }
                for r in student_rows
            ]
        )
        return sorted(out, key=lambda x: (x["role"], x["name"].lower()))


def create_managed_user(payload: dict) -> dict:
    role = (payload.get("role") or "").strip().lower()
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    roll_no = (payload.get("roll_no") or "").strip()

    if role not in {"faculty", "student"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Role must be faculty or student.")
    if len(password) < 6:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password must be at least 6 characters.")
    if not email:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email is required.")
    
    # Email domain constraints
    allowed_student_domains = {"universityname.com", "university.edu", "mrce.in"}
    email_domain = email.split("@")[-1] if "@" in email else ""
    if role == "student" and email_domain not in allowed_student_domains:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Student email must end with a university domain (e.g., @universityname.com, @mrce.in)."
        )
    if role == "faculty" and not email.endswith(".com"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Faculty email must end with .com."
        )

    if role == "faculty" and not name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Name is required for faculty.")
    
    if role == "student":
        # roll_no is not required during creation; default to email prefix
        if not roll_no:
            roll_no = email.split("@")[0]
        if not name:
            name = roll_no

    with _db.SessionLocal() as db:
        email_exists = (
            db.query(FacultyUser).filter(FacultyUser.email == email).first()
            or db.query(StudentUser).filter(StudentUser.email == email).first()
        )
        if email_exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")

        initials = "".join([p[0] for p in name.split()[:2]]).upper() or name[:2].upper()
        if role == "faculty":
            user = FacultyUser(
                id=f"f{uuid.uuid4().hex[:8]}",
                name=name,
                email=email,
                password=hash_password(password),
                title=(payload.get("title") or "Lecturer").strip(),
                department=(payload.get("department") or "General").strip(),
                avatar_initials=initials,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": "faculty",
                "title": user.title,
                "department": user.department or "",
                "year": "",
                "section": "",
                "roll_no": "",
            }

        user = StudentUser(
            id=f"s{uuid.uuid4().hex[:8]}",
            name=name,
            email=email,
            password=hash_password(password),
            department=(payload.get("department") or "General").strip(),
            year="",
            section="",
            roll_no=roll_no,
            cgpa=0.0,
            avatar_initials=initials,
            attendance="—",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": "student",
            "title": None,
            "department": user.department or "",
            "year": user.year or "",
            "section": user.section or "",
            "roll_no": user.roll_no or "",
        }


def update_managed_user(user_id: str, payload: dict) -> dict:
    role = (payload.get("role") or "").strip().lower()
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    department = (payload.get("department") or "").strip()
    roll_no = (payload.get("roll_no") or "").strip()

    if role not in {"faculty", "student"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Role must be faculty or student.")
    if password and len(password) < 6:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password must be at least 6 characters.")
    
    # Email domain constraints if updated
    if email:
        allowed_student_domains = {"universityname.com", "university.edu", "mrce.in"}
        email_domain = email.split("@")[-1] if "@" in email else ""
        if role == "student" and email_domain not in allowed_student_domains:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Student email must end with a university domain (e.g., @universityname.com, @mrce.in)."
            )
        if role == "faculty" and not email.endswith(".com"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Faculty email must end with .com."
            )

    with _db.SessionLocal() as db:
        if role == "faculty":
            user = db.query(FacultyUser).filter(FacultyUser.id == user_id).first()
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty user not found.")
            
            # Check unique email
            if email and email != user.email:
                exists = db.query(FacultyUser).filter(FacultyUser.email == email).first() or db.query(StudentUser).filter(StudentUser.email == email).first()
                if exists:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")
                user.email = email
            
            if name:
                user.name = name
                user.avatar_initials = "".join([p[0] for p in name.split()[:2]]).upper() or name[:2].upper()
            if password:
                user.password = hash_password(password)
            if department:
                user.department = department
            if payload.get("title"):
                user.title = payload.get("title")
            db.commit()
            db.refresh(user)
            return {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": "faculty",
                "title": user.title,
                "department": user.department or "",
                "year": "",
                "section": "",
                "roll_no": "",
            }

        else:
            user = db.query(StudentUser).filter(StudentUser.id == user_id).first()
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student user not found.")
            
            # Check unique email
            if email and email != user.email:
                exists = db.query(FacultyUser).filter(FacultyUser.email == email).first() or db.query(StudentUser).filter(StudentUser.email == email).first()
                if exists:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")
                user.email = email
            
            if name:
                user.name = name
                user.avatar_initials = "".join([p[0] for p in name.split()[:2]]).upper() or name[:2].upper()
            if password:
                user.password = hash_password(password)
            if department:
                user.department = department
            if roll_no:
                user.roll_no = roll_no
            db.commit()
            db.refresh(user)
            return {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": "student",
                "title": None,
                "department": user.department or "",
                "year": user.year or "",
                "section": user.section or "",
                "roll_no": user.roll_no or "",
            }


def delete_managed_user(user_id: str, role: str) -> None:
    role = (role or "").strip().lower()
    if role not in {"faculty", "student"}:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Role must be faculty or student.")
        
    with _db.SessionLocal() as db:
        if role == "faculty":
            user = db.query(FacultyUser).filter(FacultyUser.id == user_id).first()
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty user not found.")
            db.delete(user)
        else:
            user = db.query(StudentUser).filter(StudentUser.id == user_id).first()
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student user not found.")
            db.delete(user)
        db.commit()
