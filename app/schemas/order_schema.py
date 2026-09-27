from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field



#orderitem...


class OrderItemCreate(BaseModel):
    menu_item_id: str
    quantity: int = Field(gt=0)
    special_instructions: str | None = None


class OrderItemUpdate(BaseModel):
    quantity: int = Field(gt=0)
    special_instructions: str | None = None


class OrderItemResponse(BaseModel):
    id: str
    order_id: str
    menu_item_id: str
    item_name_snapshot: str
    unit_price_snapshot: Decimal
    quantity: int
    special_instructions: str | None = None
    item_total: Decimal



#order...


class OrderCreate(BaseModel):
    customer_id: str | None = None
    table_id: str | None = None
    order_type: str
    created_by: str


class OrderResponse(BaseModel):
    id: str
    order_number: str
    customer_id: str | None = None
    table_id: str | None = None
    order_type: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    created_by: str
    created_at: datetime


class OrderStatusUpdate(BaseModel):
    status: str


class OrderDiscountUpdate(BaseModel):
    discount_amount: Decimal = Field(ge=0)