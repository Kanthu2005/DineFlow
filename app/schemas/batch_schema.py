from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class BatchCreate(BaseModel):
    ingredient_id: str
    batch_number: Optional[str] = None
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)
    received_date: Optional[datetime] = None
    expiry_date: datetime
    supplier_id: Optional[str] = None
    purchase_order_id: Optional[str] = None
    storage_location_id: Optional[str] = None


class BatchResponse(BaseModel):
    id: str
    ingredient_id: str
    ingredient_name: Optional[str] = None
    batch_number: str
    quantity: Decimal
    remaining_quantity: Decimal
    unit: Optional[str] = None
    unit_cost: Decimal
    received_date: datetime
    expiry_date: datetime
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    storage_location_id: Optional[str] = None
    status: str  # ACTIVE | EXPIRING_SOON | EXPIRED | CONSUMED
    days_until_expiry: Optional[int] = None
