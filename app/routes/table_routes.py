from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.table_schema import (
    RestaurantTableCreate,
    RestaurantTableUpdate,
    TableStatusUpdate,
)
from app.services.table_service import RestaurantTableService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Tables"])


@router.post(
    "/tables",
    status_code=status.HTTP_201_CREATED,
)
def create_table(
    data: RestaurantTableCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return RestaurantTableService.create_table(data)
    except Exception as e:
        handle_error(e)


@router.get("/tables/available")
def get_available_tables(current_user: dict = Depends(get_current_user)):
    try:
        return RestaurantTableService.get_available_tables()
    except Exception as e:
        handle_error(e)


@router.get("/tables")
def get_tables(current_user: dict = Depends(get_current_user)):
    try:
        return RestaurantTableService.get_tables()
    except Exception as e:
        handle_error(e)


@router.get("/tables/{table_id}")
def get_table(
    table_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        return RestaurantTableService.get_table(table_id)
    except Exception as e:
        handle_error(e)


@router.put("/tables/{table_id}")
def update_table(
    table_id: str,
    data: RestaurantTableUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return RestaurantTableService.update_table(
            table_id,
            data,
        )
    except Exception as e:
        handle_error(e)


@router.patch("/tables/{table_id}/status")
def update_table_status(
    table_id: str,
    data: TableStatusUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER")),
):
    try:
        return RestaurantTableService.update_status(
            table_id,
            data.status,
        )
    except Exception as e:
        handle_error(e)
