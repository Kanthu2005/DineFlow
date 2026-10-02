from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime

class OrderBase(BaseModel):
    customer_id: Optional[str] = None
    table_id: Optional[str] = None
    order_type: str
    created_by: str

class OrderCreate(OrderBase):
    pass

class OrderStatusUpdate(BaseModel):
    status: str

class OrderDiscountUpdate(BaseModel):
    discount: Decimal

class Order(OrderBase):
    id: str
    order_number: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    previous_item_total: Optional[Decimal] = None
    new_item_total: Optional[Decimal] = None
    created_at: datetime
