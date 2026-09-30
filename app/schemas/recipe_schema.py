from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class RecipeCreate(BaseModel):
    menu_item_id: Optional[str] = None
    ingredient_id: str
    quantity_required: Decimal = Field(gt=0)
    unit: Optional[str] = None


class RecipeUpdate(BaseModel):
    quantity_required: Optional[Decimal] = Field(default=None, gt=0)
    unit: Optional[str] = None


class RecipeResponse(BaseModel):
    id: str
    menu_item_id: str
    ingredient_id: str
    quantity_required: Decimal
    unit: Optional[str] = None
    ingredient_name: Optional[str] = None
    ingredient_unit: Optional[str] = None
    available_stock: Optional[Decimal] = None