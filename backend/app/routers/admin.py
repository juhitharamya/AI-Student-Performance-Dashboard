from fastapi import APIRouter, Depends, status

from app.core.dependencies import require_admin
from app.schemas.auth import AdminUserCreateRequest, AdminUserItem, AdminUserUpdateRequest
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


@router.put("/users/{user_id}", response_model=AdminUserItem, summary="Update faculty or student login account")
def update_user(user_id: str, body: AdminUserUpdateRequest, _: dict = Depends(require_admin)) -> AdminUserItem:
    return admin_service.update_managed_user(user_id, body.model_dump())


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete faculty or student login account")
def delete_user(user_id: str, role: str, _: dict = Depends(require_admin)) -> None:
    admin_service.delete_managed_user(user_id, role)
    return None
