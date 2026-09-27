from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

#menucategory...
class MenuCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None

class MenuCategoryUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None

class MenuCategoryResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

#menuitem...


class MenuItemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    category_id: str
    price: Decimal = Field(gt=0)
    preparation_time: int = Field(gt=0)
    is_available: bool = True
    is_vegetarian: bool = False
    image_url: str | None = None


class MenuItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    category_id: str | None = None
    price: Decimal | None = Field(default=None, gt=0)
    preparation_time: int | None = Field(default=None, gt=0)
    is_available: bool | None = None
    is_vegetarian: bool | None = None
    image_url: str | None = None


class MenuItemResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    category_id: str
    price: Decimal
    preparation_time: int
    is_available: bool
    is_vegetarian: bool
    image_url: str | None = None
    created_at: datetime