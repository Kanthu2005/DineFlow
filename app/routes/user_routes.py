from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user_schema import UserCreate, UserUpdate
from app.services.user_service import UserService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Users"])


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return UserService.create_user(data)
    except Exception as e:
        handle_error(e)


@router.get("/users")
def get_users(current_user: dict = Depends(require_roles("ADMIN", "MANAGER"))):
    try:
        return UserService.get_users()
    except Exception as e:
        handle_error(e)


@router.get("/users/{user_id}")
def get_user(
    user_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return UserService.get_user(user_id)
    except Exception as e:
        handle_error(e)


@router.put("/users/{user_id}")
def update_user(
    user_id: str,
    data: UserUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return UserService.update_user(
            user_id,
            data,
        )
    except Exception as e:
        handle_error(e)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    current_user: dict = Depends(require_roles("ADMIN")),
):
    try:
        return UserService.delete_user(user_id)
    except Exception as e:
        handle_error(e)
