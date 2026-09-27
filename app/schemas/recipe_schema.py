from decimal import Decimal

from pydantic import BaseModel, Field


class RecipeCreate(BaseModel):
    ingredient_id: str
    quantity_required: Decimal = Field(gt=0)


class RecipeUpdate(BaseModel):
    quantity_required: Decimal = Field(gt=0)


class RecipeResponse(BaseModel):
    id: str
    menu_item_id: str
    ingredient_id: str
    quantity_required: Decimal