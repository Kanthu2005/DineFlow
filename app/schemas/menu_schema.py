from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any
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
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    food_type: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True
    display_order: int = 0


class MenuCategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    food_type: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class MenuCategoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    food_type: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True
    display_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ==========================================
# Menu Subcategory Schemas
# ==========================================
class MenuSubcategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category_id: str
    description: Optional[str] = None
    is_active: bool = True
    display_order: int = 0


class MenuSubcategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category_id: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class MenuSubcategoryResponse(BaseModel):
    id: str
    name: str
    category_id: str
    category_name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    display_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ==========================================
# Menu Item Schemas
# ==========================================
class MenuItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: Optional[str] = None
    category_id: str
    subcategory_id: Optional[str] = None
    price: Decimal = Field(ge=0)
    base_price: Optional[Decimal] = None
    discount: Optional[Decimal] = Field(default=Decimal("0"), ge=0)
    tax: Optional[Decimal] = Field(default=Decimal("0"), ge=0)
    final_price: Optional[Decimal] = None
    preparation_time: int = Field(default=15, gt=0)
    is_available: bool = True
    is_vegetarian: bool = False
    food_type: Optional[str] = None  # "Veg", "Non-Veg"
    image_url: Optional[str] = None
    type: Optional[str] = None
    is_featured: bool = False
    is_active: bool = True
    display_order: int = 0
    spicy_level: Optional[str] = None
    serving_size: Optional[str] = None
    tags: Optional[List[str]] = None
    inventory_tracking_enabled: bool = True


class MenuItemUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    description: Optional[str] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, ge=0)
    base_price: Optional[Decimal] = Field(default=None, ge=0)
    discount: Optional[Decimal] = Field(default=None, ge=0)
    tax: Optional[Decimal] = Field(default=None, ge=0)
    final_price: Optional[Decimal] = None
    preparation_time: Optional[int] = Field(default=None, ge=0)
    is_available: Optional[bool] = None
    is_vegetarian: Optional[bool] = None
    food_type: Optional[str] = None
    image_url: Optional[str] = None
    type: Optional[str] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    spicy_level: Optional[str] = None
    serving_size: Optional[str] = None
    tags: Optional[List[str]] = None
    inventory_tracking_enabled: Optional[bool] = None


class MenuItemResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    subcategory_id: Optional[str] = None
    subcategory_name: Optional[str] = None
    price: Decimal | float
    base_price: Optional[Decimal | float] = None
    discount: Optional[Decimal | float] = 0.0
    tax: Optional[Decimal | float] = 0.0
    final_price: Optional[Decimal | float] = None
    preparation_time: int = 15
    is_available: bool = True
    is_vegetarian: bool = False
    food_type: Optional[str] = None
    image_url: Optional[str] = None
    type: Optional[str] = None
    is_featured: bool = False
    is_active: bool = True
    display_order: int = 0
    spicy_level: Optional[str] = None
    serving_size: Optional[str] = None
    tags: Optional[List[str]] = None
    inventory_tracking_enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ==========================================
# Menu Dashboard Statistics Schema
# ==========================================
class MenuStatsResponse(BaseModel):
    total_items: int = 0
    available_items: int = 0
    unavailable_items: int = 0
    veg_items: int = 0
    non_veg_items: int = 0
    starters: int = 0
    desserts: int = 0
    featured_items: int = 0
    categories_count: int = 0
    subcategories_count: int = 0