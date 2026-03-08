from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.schemas.auth import AdminExistsResponse, LoginRequest, MeResponse, RegisterRequest, RegisterResponse, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get(
    "/admin-exists",
    response_model=AdminExistsResponse,
    summary="Check whether an admin account already exists",
)
def admin_exists() -> AdminExistsResponse:
    return {"exists": auth_service.admin_exists()}


# ── Register ──────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
    summary="Create the first admin account",
)
def register(body: RegisterRequest) -> RegisterResponse:
    """
    Register the initial **admin** account.
    Allowed only once. After that, use `/auth/login` for admin sign-in.
    """
    return auth_service.register_user(body)


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT",
)
def login(body: LoginRequest) -> TokenResponse:
    """
    Authenticate with **email**, **password**, and **role** (`faculty` | `student`).

    Returns a Bearer token and basic profile info for the frontend to store.
    """
    user = auth_service.authenticate_user(body.email, body.password, body.role)
    return auth_service.create_token_for_user(user)


# ── Me (validate stored token) ────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=MeResponse,
    summary="Return the current authenticated user's profile",
)
def me(current_user: dict = Depends(get_current_user)) -> MeResponse:
    """
    Validates the Bearer token sent by the client and returns a lightweight
    profile payload.  The frontend should call this on app startup to confirm
    a persisted token is still valid before showing the dashboard.
    """
    return auth_service.get_me(current_user)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post(
    "/logout",
    summary="Logout (client-side token invalidation)",
    status_code=200,
)
def logout(_: dict = Depends(get_current_user)) -> dict:
    """
    Stateless logout — the server confirms the token is valid and instructs
    the client to delete it.  For a stateful blacklist, add a token-revocation
    store (e.g. Redis) in production.
    """
    return {"message": "Logged out successfully. Please delete your token client-side."}
