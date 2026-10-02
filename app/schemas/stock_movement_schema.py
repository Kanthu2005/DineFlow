from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class StockMovementCreate(BaseModel):
    ingredient_id: str
    movement_type: str
    quantity: Decimal = Field(gt=0)
    unit: Optional[str] = None
    previous_stock: Optional[Decimal] = None
    new_stock: Optional[Decimal] = None
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    batch_id: Optional[str] = None
    supplier_id: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    reason: Optional[str] = None
    performed_by: Optional[str] = "SYSTEM"


class StockMovementResponse(BaseModel):
    id: str
    ingredient_id: str
    movement_type: str
    quantity: Decimal
    unit: Optional[str] = None
    previous_stock: Optional[Decimal] = None
    new_stock: Optional[Decimal] = None
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    batch_id: Optional[str] = None
    supplier_id: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    reason: Optional[str] = None
    performed_by: Optional[str] = "SYSTEM"
    created_at: datetime
    ingredient_name: Optional[str] = None
