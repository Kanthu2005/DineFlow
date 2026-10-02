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
    price_at_addition: Decimal | None = None
    quantity: int
    special_instructions: str | None = None
    status: str = "PENDING"
    batch_number: int = 1
    is_additional: bool = False
    added_at: datetime | None = None
    inventory_deducted: bool = False
    item_total: Decimal


class AdditionalItemsRequest(BaseModel):
    items: list[OrderItemCreate]


class OrderItemStatusUpdate(BaseModel):
    status: str


#order...


class OrderCreate(BaseModel):
    customer_id: str | None = None
    customer_name: str | None = None
    customer_phone: str | None = None
    table_id: str | None = None
    order_type: str = "DINE_IN"
    discount_amount: Decimal | None = None
    created_by: str | None = None
    items: list[OrderItemCreate] | None = None


class OrderResponse(BaseModel):
    id: str
    order_number: str
    customer_id: str | None = None
    customer_name: str | None = None
    customer_phone: str | None = None
    table_id: str | None = None
    table_number: str | None = None
    order_type: str
    status: str
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    previous_item_total: Decimal | None = None
    new_item_total: Decimal | None = None
    created_by: str
    created_at: datetime
    items: list[OrderItemResponse] | None = None


class OrderStatusUpdate(BaseModel):
    status: str


class OrderDiscountUpdate(BaseModel):
    discount_amount: Decimal = Field(ge=0)