from pydantic import BaseModel, field_validator


# ── Request ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str
    role: str  # "faculty" | "student"


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str  # "faculty" | "student"
    # Optional student-specific fields
    roll_no: str | None = None
    year: str | None = None
    section: str | None = None
    department: str | None = None
    # Optional faculty-specific fields
    title: str | None = None

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, v: str) -> str:
        if v not in ("faculty", "student"):
            raise ValueError("role must be 'faculty' or 'student'")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("password must be at least 6 characters")
        return v


# ── Responses ─────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    avatar_initials: str


class RegisterResponse(BaseModel):
    """Returned after successful registration — includes a ready-to-use token."""
    id: str
    name: str
    email: str
    role: str
    avatar_initials: str
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    """Lightweight payload returned by GET /auth/me."""
    id: str
    name: str
    email: str
    role: str
    avatar_initials: str
