"""
Ingredient and Inventory Routes.
Supports both /inventory and /ingredients endpoints for full RESTful compatibility.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.ingredient_schema import (
    IngredientCreate,
    IngredientUpdate,
    StockUpdate,
)
from app.services.ingredient_service import IngredientService
from app.repositories.inventory_repository import IngredientRepository
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Inventory & Ingredients"])
ing_repo = IngredientRepository()


# ==========================================
# Dashboard & Reports
# ==========================================

@router.get("/inventory/dashboard")
@router.get("/ingredients/dashboard")
def get_inventory_dashboard(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "CASHIER")),
):
    """
    Returns inventory summary: total ingredients, low stock items,
    out of stock items, recent stock movements, and today's consumption.
    """
    try:
        return IngredientService.get_inventory_dashboard()
    except Exception as e:
        handle_error(e)


@router.get("/inventory/low-stock")
@router.get("/ingredients/low-stock")
def get_low_stock_ingredients(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.get_low_stock_ingredients()
    except Exception as e:
        handle_error(e)


@router.get("/inventory/movements")
@router.get("/ingredients/movements")
def get_all_stock_movements(
    limit: int = 100,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return ing_repo.find_all_movements(limit=limit)
    except Exception as e:
        handle_error(e)


@router.get("/inventory/active")
@router.get("/ingredients/active")
def get_active_ingredients(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return IngredientService.get_active_ingredients()
    except Exception as e:
        handle_error(e)


# ==========================================
# Core CRUD Operations
# ==========================================

@router.post("/inventory", status_code=status.HTTP_201_CREATED)
@router.post("/ingredients", status_code=status.HTTP_201_CREATED)
def create_ingredient(
    data: IngredientCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.create_ingredient(data)
    except Exception as e:
        handle_error(e)


@router.get("/inventory")
@router.get("/ingredients")
def get_ingredients(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return IngredientService.get_ingredients()
    except Exception as e:
        handle_error(e)


@router.get("/inventory/{ingredient_id}")
@router.get("/ingredients/{ingredient_id}")
def get_ingredient(
    ingredient_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return IngredientService.get_ingredient(ingredient_id)
    except Exception as e:
        handle_error(e)


@router.put("/inventory/{ingredient_id}")
@router.put("/ingredients/{ingredient_id}")
def update_ingredient(
    ingredient_id: str,
    data: IngredientUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.update_ingredient(ingredient_id, data)
    except Exception as e:
        handle_error(e)


@router.delete("/inventory/{ingredient_id}")
@router.delete("/ingredients/{ingredient_id}")
def delete_ingredient(
    ingredient_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.delete_ingredient(ingredient_id)
    except Exception as e:
        handle_error(e)


@router.post("/inventory/{ingredient_id}/stock")
@router.post("/ingredients/{ingredient_id}/stock")
def update_ingredient_stock(
    ingredient_id: str,
    data: StockUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.update_stock(
            ingredient_id=ingredient_id,
            quantity=data.quantity,
            movement_type="PURCHASE" if data.quantity > 0 else "MANUAL_ADJUSTMENT",
            created_by=current_user.get("name", "SYSTEM"),
        )
    except Exception as e:
        handle_error(e)


@router.get("/inventory/{ingredient_id}/stock-status")
@router.get("/ingredients/{ingredient_id}/stock-status")
def get_ingredient_stock_status(
    ingredient_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.get_stock_status(ingredient_id)
    except Exception as e:
        handle_error(e)


@router.get("/inventory/{ingredient_id}/movements")
@router.get("/ingredients/{ingredient_id}/movements")
def get_ingredient_movements(
    ingredient_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return ing_repo.find_movements_by_ingredient(ingredient_id)
    except Exception as e:
        handle_error(e)
