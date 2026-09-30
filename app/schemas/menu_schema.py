from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

# ==========================================
# Generic Message Schema
# ==========================================
class MessageResponse(BaseModel):
    message: str

# ==========================================
# Menu Category Schemas
# ==========================================
class MenuCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = None

class MenuCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = None

class MenuCategoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# ==========================================
# Menu Item Schemas
# ==========================================
class MenuItemCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: Optional[str] = None
    category_id: str
    price: Decimal = Field(gt=0)
    preparation_time: int = Field(default=15, gt=0)
    is_available: bool = True
    is_vegetarian: bool = False
    image_url: Optional[str] = None

class MenuItemUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = None
    category_id: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, gt=0)
    preparation_time: Optional[int] = Field(default=None, gt=0)
    is_available: Optional[bool] = None
    is_vegetarian: Optional[bool] = None
    image_url: Optional[str] = None

class MenuItemResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    price: Decimal | float
    preparation_time: int = 15
    is_available: bool = True
    is_vegetarian: bool = False
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None