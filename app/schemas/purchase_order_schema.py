from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class PurchaseOrderItemCreate(BaseModel):
    ingredient_id: str
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    unit: Optional[str] = None


class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    items: List[PurchaseOrderItemCreate] = Field(min_length=1)
    expected_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None


class PurchaseOrderReceiveItem(BaseModel):
    ingredient_id: str
    received_quantity: Decimal = Field(ge=0)
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    unit_cost: Optional[Decimal] = None
    storage_location_id: Optional[str] = None


class PurchaseOrderReceiveSchema(BaseModel):
    items: Optional[List[PurchaseOrderReceiveItem]] = None
    notes: Optional[str] = "Received from Purchase Order"


class PurchaseOrderItemResponse(BaseModel):
    ingredient_id: str
    ingredient_name: Optional[str] = None
    quantity: Decimal
    received_quantity: Decimal = Decimal("0")
    unit: Optional[str] = None
    unit_cost: Decimal
    total_cost: Decimal


class PurchaseOrderResponse(BaseModel):
    id: str
    po_number: str
    supplier_id: str
    supplier_name: Optional[str] = None
    items: List[PurchaseOrderItemResponse]
    total_expected_cost: Decimal
    status: str  # DRAFT | ORDERED | PARTIALLY_RECEIVED | RECEIVED | CANCELLED
    order_date: datetime
    expected_delivery_date: Optional[datetime] = None
    received_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
