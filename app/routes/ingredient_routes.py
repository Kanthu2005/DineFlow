"""
Ingredient and Inventory Routes.
Supports /inventory and /ingredients endpoints for full RESTful compatibility,
including Stock In / Receiving, Wastage, Adjustments, Transfers, Categories,
Storage Locations, Batches, and Comprehensive Inventory Reports.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.ingredient_schema import (
    IngredientCreate,
    IngredientUpdate,
    StockUpdate,
    StockReceiveSchema,
    WastageCreateSchema,
    StockAdjustmentSchema,
    StockTransferSchema,
    CategoryCreateSchema,
    StorageLocationCreateSchema,
)
from app.services.ingredient_service import IngredientService
from app.repositories.inventory_repository import IngredientRepository
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Inventory & Ingredients"])
ing_repo = IngredientRepository()


# ==========================================
# Dashboard & Core Analytics
# ==========================================

@router.get("/inventory/dashboard")
@router.get("/ingredients/dashboard")
def get_inventory_dashboard(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "CASHIER")),
):
    """
    Returns inventory summary: total ingredients, total stock value, low stock items,
    out of stock items, expiring batches, expired stock, today's consumption,
    today's wastage, and pending purchase orders.
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
# Categories & Storage Locations
# ==========================================

@router.get("/inventory/categories")
@router.get("/ingredients/categories")
def get_categories(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return IngredientService.get_categories()
    except Exception as e:
        handle_error(e)


@router.post("/inventory/categories", status_code=status.HTTP_201_CREATED)
@router.post("/ingredients/categories", status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreateSchema,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return IngredientService.create_category(name=data.name, description=data.description)
    except Exception as e:
        handle_error(e)


@router.get("/inventory/locations")
@router.get("/ingredients/locations")
def get_storage_locations(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return IngredientService.get_storage_locations()
    except Exception as e:
        handle_error(e)


@router.post("/inventory/locations", status_code=status.HTTP_201_CREATED)
@router.post("/ingredients/locations", status_code=status.HTTP_201_CREATED)
def create_storage_location(
    data: StorageLocationCreateSchema,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return IngredientService.create_storage_location(
            name=data.name,
            description=data.description,
            temperature_type=data.temperature_type or "AMBIENT",
        )
    except Exception as e:
        handle_error(e)


# ==========================================
# Batches & Expiry Management
# ==========================================

@router.get("/inventory/{ingredient_id}/batches")
@router.get("/ingredients/{ingredient_id}/batches")
@router.get("/inventory/batches")
@router.get("/ingredients/batches")
def get_batches(
    ingredient_id: Optional[str] = None,
    only_active: bool = False,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.get_batches(ingredient_id=ingredient_id, only_active=only_active)
    except Exception as e:
        handle_error(e)


@router.get("/inventory/batches/expiring")
@router.get("/ingredients/batches/expiring")
def get_expiring_batches(
    warning_days: int = Query(default=3, ge=1, le=90),
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.get_expiring_batches(warning_days=warning_days)
    except Exception as e:
        handle_error(e)


@router.get("/inventory/batches/expired")
@router.get("/ingredients/batches/expired")
def get_expired_batches(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.get_expired_batches()
    except Exception as e:
        handle_error(e)


# ==========================================
# Stock Operations (Receive, Wastage, Adjust, Transfer)
# ==========================================

@router.post("/inventory/{ingredient_id}/receive", status_code=status.HTTP_200_OK)
@router.post("/ingredients/{ingredient_id}/receive", status_code=status.HTTP_200_OK)
def receive_stock_for_ingredient(
    ingredient_id: str,
    data: StockReceiveSchema,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    """
    Adds received stock to inventory, creates a batch record, and logs movement.
    Previous Stock + Received Quantity = New Stock.
    """
    try:
        return IngredientService.receive_stock(
            ingredient_id=ingredient_id,
            quantity=data.quantity,
            unit_cost=data.unit_cost,
            supplier_id=data.supplier_id,
            purchase_order_id=data.purchase_order_id,
            batch_number=data.batch_number,
            expiry_date=data.expiry_date,
            storage_location_id=data.storage_location_id,
            reason=data.reason,
            performed_by=current_user.get("name", "SYSTEM"),
        )
    except Exception as e:
        handle_error(e)


@router.post("/inventory/{ingredient_id}/wastage", status_code=status.HTTP_200_OK)
@router.post("/ingredients/{ingredient_id}/wastage", status_code=status.HTTP_200_OK)
@router.post("/inventory/wastage", status_code=status.HTTP_201_CREATED)
@router.post("/ingredients/wastage", status_code=status.HTTP_201_CREATED)
def record_wastage(
    data: WastageCreateSchema,
    ingredient_id: Optional[str] = None,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    """
    Records kitchen / storage wastage (EXPIRED, SPOILED, BURNT, etc.),
    deducts batch remaining quantity and overall stock balance, and logs a WASTAGE movement.
    """
    target_id = ingredient_id or data.ingredient_id
    if not target_id:
        raise HTTPException(status_code=400, detail="ingredient_id is required")
    try:
        return IngredientService.record_wastage(
            ingredient_id=target_id,
            quantity=data.quantity,
            reason=data.reason,
            batch_id=data.batch_id,
            notes=data.notes,
            performed_by=current_user.get("name", "SYSTEM"),
        )
    except Exception as e:
        handle_error(e)


@router.post("/inventory/{ingredient_id}/adjust")
@router.post("/ingredients/{ingredient_id}/adjust")
def adjust_stock(
    ingredient_id: str,
    data: StockAdjustmentSchema,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    """
    Manual physical stock count reconciliation.
    Records discrepancy and generates an ADJUSTMENT movement.
    """
    try:
        return IngredientService.adjust_stock(
            ingredient_id=ingredient_id,
            physical_stock=data.physical_stock,
            reason=data.reason,
            notes=data.notes,
            performed_by=current_user.get("name", "SYSTEM"),
        )
    except Exception as e:
        handle_error(e)


@router.post("/inventory/{ingredient_id}/transfer", status_code=status.HTTP_200_OK)
@router.post("/ingredients/{ingredient_id}/transfer", status_code=status.HTTP_200_OK)
@router.post("/inventory/transfer", status_code=status.HTTP_200_OK)
@router.post("/ingredients/transfer", status_code=status.HTTP_200_OK)
def transfer_stock(
    data: StockTransferSchema,
    ingredient_id: Optional[str] = None,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    """
    Transfers inventory between storage locations (e.g. Main Store -> Kitchen Store).
    Atomically logs TRANSFER_OUT and TRANSFER_IN movements.
    """
    target_id = ingredient_id or data.ingredient_id
    if not target_id:
        raise HTTPException(status_code=400, detail="ingredient_id is required")
    try:
        return IngredientService.transfer_stock(
            ingredient_id=target_id,
            from_location_id=data.from_location_id,
            to_location_id=data.to_location_id,
            quantity=data.quantity,
            batch_id=data.batch_id,
            notes=data.notes,
            performed_by=current_user.get("name", "SYSTEM"),
        )
    except Exception as e:
        handle_error(e)


# ==========================================
# Reports
# ==========================================

@router.get("/inventory/reports/stock")
def get_stock_report(
    category: Optional[str] = None,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.get_stock_report(category=category)
    except Exception as e:
        handle_error(e)


@router.get("/inventory/reports/consumption")
def get_consumption_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    ingredient_id: Optional[str] = None,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.get_consumption_report(start_date=start_date, end_date=end_date, ingredient_id=ingredient_id)
    except Exception as e:
        handle_error(e)


@router.get("/inventory/reports/wastage")
def get_wastage_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    reason: Optional[str] = None,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.get_wastage_report(start_date=start_date, end_date=end_date, reason=reason)
    except Exception as e:
        handle_error(e)


@router.get("/inventory/reports/expiry")
def get_expiry_report(
    warning_days: int = Query(default=30, ge=1, le=180),
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.get_expiry_report(warning_days=warning_days)
    except Exception as e:
        handle_error(e)


@router.get("/inventory/reports/movements")
def get_movements_report(
    ingredient_id: Optional[str] = None,
    movement_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    supplier_id: Optional[str] = None,
    limit: int = 200,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return IngredientService.get_movement_report(
            ingredient_id=ingredient_id,
            movement_type=movement_type,
            start_date=start_date,
            end_date=end_date,
            supplier_id=supplier_id,
            limit=limit,
        )
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
    category: Optional[str] = None,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return IngredientService.get_ingredients(category=category)
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
