"""
Order Management Routes.
Supports full lifecycle: creation, item management, discount, confirmation, and cancellation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel
from app.schemas.order_schema import (
    OrderCreate,
    OrderItemCreate,
    OrderItemUpdate,
    OrderStatusUpdate,
    OrderDiscountUpdate,
)
from app.services.order_service import OrderService, OrderItemService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Orders"])


class OrderCancelRequest(BaseModel):
    reason: Optional[str] = "Customer requested cancellation"


@router.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        if not data.created_by:
            data.created_by = current_user.get("name") or current_user.get("email") or "Staff"
        return OrderService.create_order(data)
    except Exception as e:
        handle_error(e)


@router.get("/orders/number/{order_number}")
def get_order_by_number(
    order_number: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER", "CHEF")),
):
    try:
        return OrderService.get_order_by_number(order_number)
    except Exception as e:
        handle_error(e)


@router.get("/orders")
def get_orders(
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER", "CHEF")),
):
    try:
        return OrderService.get_orders(status=status, order_type=order_type)
    except Exception as e:
        handle_error(e)


@router.get("/orders/{order_id}")
def get_order(
    order_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER", "CHEF")),
):
    try:
        return OrderService.get_order(order_id)
    except Exception as e:
        handle_error(e)


@router.post("/orders/{order_id}/confirm")
def confirm_order(
    order_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    """
    Confirms an order, verifies ingredient availability, deducts stock,
    and forwards the ticket to the kitchen.
    """
    try:
        return OrderService.confirm_order(
            order_id=order_id,
            performed_by=current_user.get("name", "WAITER"),
            role=current_user.get("role", "WAITER"),
        )
    except Exception as e:
        handle_error(e)


@router.post("/orders/{order_id}/cancel")
def cancel_order(
    order_id: str,
    cancel_req: Optional[OrderCancelRequest] = Body(None),
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    """
    Cancels an order according to status and role policy.
    Restores stock if order had not begun preparation.
    """
    try:
        reason = cancel_req.reason if cancel_req else "Cancellation requested"
        return OrderService.cancel_order(
            order_id=order_id,
            reason=reason,
            role=current_user.get("role", "CUSTOMER"),
            performed_by=current_user.get("name", "SYSTEM"),
        )
    except Exception as e:
        handle_error(e)


@router.patch("/orders/{order_id}/status")
def update_order_status(
    order_id: str,
    data: OrderStatusUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return OrderService.update_status(
            order_id=order_id,
            new_status=data.status,
            performed_by=current_user.get("name", "SYSTEM"),
            role=current_user.get("role", "SYSTEM"),
        )
    except Exception as e:
        handle_error(e)


@router.patch("/orders/{order_id}/discount")
def update_order_discount(
    order_id: str,
    data: OrderDiscountUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return OrderService.update_discount(order_id, data)
    except Exception as e:
        handle_error(e)


# ==========================================
# Order Items
# ==========================================

@router.post("/orders/{order_id}/items", status_code=status.HTTP_201_CREATED)
def add_order_item(
    order_id: str,
    data: OrderItemCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return OrderItemService.add_item(order_id, data)
    except Exception as e:
        handle_error(e)


@router.get("/orders/{order_id}/items")
def get_order_items(
    order_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER", "CHEF")),
):
    try:
        return OrderItemService.get_order_items(order_id)
    except Exception as e:
        handle_error(e)


@router.put("/orders/{order_id}/items/{item_id}")
def update_order_item(
    order_id: str,
    item_id: str,
    data: OrderItemUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return OrderItemService.update_item(order_id, item_id, data)
    except Exception as e:
        handle_error(e)


@router.delete("/orders/{order_id}/items/{item_id}")
def delete_order_item(
    order_id: str,
    item_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return OrderItemService.delete_item(order_id, item_id)
    except Exception as e:
        handle_error(e)


@router.post("/orders/{order_id}/recalculate")
def recalculate_order(
    order_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return OrderItemService.recalculate_order(order_id)
    except Exception as e:
        handle_error(e)
