from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.stock_movement_schema import StockMovementCreate
from app.services.stock_movement_service import StockMovementService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Stock Movements"])


@router.post(
    "/stock-movements",
    status_code=status.HTTP_201_CREATED,
)
def create_stock_movement(
    data: StockMovementCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return StockMovementService.create_movement(data)
    except Exception as e:
        handle_error(e)


@router.get("/stock-movements")
def get_stock_movements(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return StockMovementService.get_movements()
    except Exception as e:
        handle_error(e)


@router.get("/stock-movements/ingredient/{ingredient_id}")
def get_ingredient_stock_movements(
    ingredient_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return StockMovementService.get_by_ingredient(
            ingredient_id
        )
    except Exception as e:
        handle_error(e)
