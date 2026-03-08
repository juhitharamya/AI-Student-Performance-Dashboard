from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_admin
from app.schemas.auth import AdminUserCreateRequest, AdminUserItem
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=list[AdminUserItem], summary="List faculty and student accounts")
def list_users(_: dict = Depends(require_admin)) -> list[AdminUserItem]:
    return admin_service.list_managed_users()


@router.post(
    "/users",
    response_model=AdminUserItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create faculty or student login account",
)
def create_user(body: AdminUserCreateRequest, _: dict = Depends(require_admin)) -> AdminUserItem:
    return admin_service.create_managed_user(body.model_dump())
