from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class IngredientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    unit: str = Field(min_length=1, max_length=20)
    available_quantity: Decimal = Field(ge=0)
    minimum_stock_level: Decimal = Field(ge=0)
    cost_per_unit: Decimal = Field(ge=0)
    supplier_name: str | None = None
    is_active: bool = True


class IngredientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    unit: str | None = None
    minimum_stock_level: Decimal | None = Field(default=None, ge=0)
    cost_per_unit: Decimal | None = Field(default=None, ge=0)
    supplier_name: str | None = None
    is_active: bool | None = None


class StockUpdate(BaseModel):
    quantity: Decimal


class IngredientResponse(BaseModel):
    id: str
    name: str
    unit: str
    available_quantity: Decimal
    minimum_stock_level: Decimal
    cost_per_unit: Decimal
    supplier_name: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime