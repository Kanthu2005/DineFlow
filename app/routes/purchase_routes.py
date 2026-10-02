"""
Supplier and Purchase Order Procurement Routes.
Manages vendors, purchase orders, status transitions, and shipment goods receipt.
"""

from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel
from app.schemas.supplier_schema import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)
from app.schemas.purchase_order_schema import (
    PurchaseOrderCreate,
    PurchaseOrderReceiveSchema,
    PurchaseOrderResponse,
)
from app.services.supplier_service import SupplierService
from app.services.purchase_service import PurchaseService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Suppliers & Purchase Orders"])


class PurchaseOrderStatusUpdate(BaseModel):
    status: str


# ==========================================
# Supplier Endpoints
# ==========================================

@router.get("/suppliers", response_model=None)
@router.get("/purchases/suppliers", response_model=None)
def get_suppliers(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return SupplierService.get_suppliers()
    except Exception as e:
        handle_error(e)


@router.post("/suppliers", status_code=status.HTTP_201_CREATED)
@router.post("/purchases/suppliers", status_code=status.HTTP_201_CREATED)
def create_supplier(
    data: SupplierCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return SupplierService.create_supplier(data)
    except Exception as e:
        handle_error(e)


@router.get("/suppliers/{supplier_id}")
@router.get("/purchases/suppliers/{supplier_id}")
def get_supplier(
    supplier_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return SupplierService.get_supplier(supplier_id)
    except Exception as e:
        handle_error(e)


@router.put("/suppliers/{supplier_id}")
@router.put("/purchases/suppliers/{supplier_id}")
def update_supplier(
    supplier_id: str,
    data: SupplierUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return SupplierService.update_supplier(supplier_id, data)
    except Exception as e:
        handle_error(e)


@router.delete("/suppliers/{supplier_id}")
@router.delete("/purchases/suppliers/{supplier_id}")
def delete_supplier(
    supplier_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return SupplierService.delete_supplier(supplier_id)
    except Exception as e:
        handle_error(e)


# ==========================================
# Purchase Order Endpoints
# ==========================================

@router.get("/purchases/orders")
@router.get("/purchase-orders")
@router.get("/purchases")
def get_purchase_orders(
    status: Optional[str] = None,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return PurchaseService.get_purchase_orders(status=status)
    except Exception as e:
        handle_error(e)


@router.post("/purchases/orders", status_code=status.HTTP_201_CREATED)
@router.post("/purchase-orders", status_code=status.HTTP_201_CREATED)
@router.post("/purchases", status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    data: PurchaseOrderCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    """
    Creates a new Purchase Order in DRAFT status.
    NOTE: Does NOT update inventory until goods are received.
    """
    try:
        return PurchaseService.create_purchase_order(data, created_by=current_user.get("name", "SYSTEM"))
    except Exception as e:
        handle_error(e)


@router.get("/purchases/orders/{po_id}")
@router.get("/purchase-orders/{po_id}")
def get_purchase_order(
    po_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return PurchaseService.get_purchase_order(po_id)
    except Exception as e:
        handle_error(e)


@router.patch("/purchases/orders/{po_id}/status")
@router.post("/purchases/orders/{po_id}/status")
@router.patch("/purchase-orders/{po_id}/status")
@router.post("/purchase-orders/{po_id}/status")
def update_purchase_order_status(
    po_id: str,
    data: Optional[PurchaseOrderStatusUpdate] = None,
    status_value: Optional[str] = Query(None, description="DRAFT, ORDERED, CANCELLED"),
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    target_status = (data.status if data else None) or status_value
    if not target_status:
        raise HTTPException(status_code=400, detail="status is required")
    try:
        return PurchaseService.update_status(po_id, target_status)
    except Exception as e:
        handle_error(e)


@router.post("/purchases/orders/{po_id}/receive")
@router.post("/purchase-orders/{po_id}/receive")
def receive_purchase_order_goods(
    po_id: str,
    data: Optional[PurchaseOrderReceiveSchema] = None,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    """
    Receives goods from a Purchase Order.
    Updates raw ingredient inventory, creates batches, and logs RECEIVE movements.
    """
    try:
        return PurchaseService.receive_purchase_order(
            po_id=po_id,
            receive_data=data,
            performed_by=current_user.get("name", "SYSTEM"),
        )
    except Exception as e:
        handle_error(e)
