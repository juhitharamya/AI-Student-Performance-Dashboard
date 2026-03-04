import uuid

from fastapi import HTTPException, status

from app.core.data_store import USERS
from app.core.security import verify_password, create_access_token, hash_password
from app.schemas.auth import RegisterRequest


def authenticate_user(email: str, password: str, role: str) -> dict:
    """
    Validate credentials against the data store.
    - If the user exists: verify the password.
    - If the user does NOT exist: auto-register them so any email/password works.
    Returns the user dict on success, raises 401 on failure.
    """
    user = next(
        (u for u in USERS if u["email"].lower() == email.lower() and u["role"] == role),
        None,
    )

    if user is None:
        # Auto-create a new account on first login with any email
        email_local = email.split("@")[0]
        parts = email_local.replace(".", " ").replace("_", " ").split()
        name = " ".join(p.capitalize() for p in parts) if parts else email_local.capitalize()
        initials = (name[0] + name[-1]).upper() if len(name) >= 2 else name[:2].upper()

        new_user: dict = {
            "id": f"u{uuid.uuid4().hex[:8]}",
            "name": name,
            "email": email,
            "password": hash_password(password),
            "role": role,
            "avatar_initials": initials,
        }
        if role == "student":
            new_user.update({
                "roll_no": f"STU{uuid.uuid4().hex[:6].upper()}",
                "cgpa": 0.0,
                "year": "1st Year",
                "section": "Section A",
                "department": "General",
            })
        else:
            new_user.update({
                "title": "Lecturer",
                "department": "General",
            })

        USERS.append(new_user)
        return new_user

    # Existing user — verify password
    if not verify_password(password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def register_user(body: RegisterRequest) -> dict:
    """
    Create a new user account and return a ready-to-use JWT.
    Raises 409 if the email+role combination is already registered.
    """
    # Check for duplicate email within the same role
    existing = next(
        (u for u in USERS if u["email"].lower() == body.email.lower() and u["role"] == body.role),
        None,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with this email already exists for role '{body.role}'.",
        )

    # Derive avatar initials from name (e.g. "John Doe" → "JD")
    parts = body.name.strip().split()
    initials = (parts[0][0] + parts[-1][0]).upper() if len(parts) >= 2 else parts[0][:2].upper()

    new_user: dict = {
        "id": f"u{uuid.uuid4().hex[:8]}",
        "name": body.name,
        "email": body.email,
        "password": hash_password(body.password),
        "role": body.role,
        "avatar_initials": initials,
    }

    # Role-specific defaults
    if body.role == "student":
        new_user.update({
            "roll_no": body.roll_no or f"STU{uuid.uuid4().hex[:6].upper()}",
            "cgpa": 0.0,
            "year": body.year or "1st Year",
            "section": body.section or "Section A",
            "department": body.department or "General",
        })
    else:  # faculty
        new_user.update({
            "title": body.title or "Lecturer",
            "department": body.department or "General",
        })

    USERS.append(new_user)

    # Issue a JWT immediately so the client is logged in right away
    token = create_access_token({"sub": new_user["id"], "role": new_user["role"]})
    return {
        "id": new_user["id"],
        "name": new_user["name"],
        "email": new_user["email"],
        "role": new_user["role"],
        "avatar_initials": new_user["avatar_initials"],
        "access_token": token,
        "token_type": "bearer",
    }


def create_token_for_user(user: dict) -> dict:
    """Build the JWT payload and return the token response dict."""
    token = create_access_token({"sub": user["id"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "name": user["name"],
        "avatar_initials": user["avatar_initials"],
    }


def get_me(user: dict) -> dict:
    """
    Return a lightweight profile for the /auth/me endpoint.
    The `user` dict is already validated by the get_current_user dependency.
    """
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "avatar_initials": user["avatar_initials"],
    }
