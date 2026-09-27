from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime

class IngredientBase(BaseModel):
    name: str
    unit: str
    available_quantity: Decimal
    minimum_stock_level: Decimal
    cost_per_unit: Decimal
    supplier_name: Optional[str] = None
    is_active: bool = True

class IngredientCreate(IngredientBase):
    pass

class IngredientUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    available_quantity: Optional[Decimal] = None
    minimum_stock_level: Optional[Decimal] = None
    cost_per_unit: Optional[Decimal] = None
    supplier_name: Optional[str] = None
    is_active: Optional[bool] = None

class Ingredient(IngredientBase):
    id: str
    created_at: datetime
