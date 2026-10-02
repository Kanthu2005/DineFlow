from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


# ==========================================
# Menu Category Models
# ==========================================

class MenuCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    food_type: Optional[str] = None  # "Veg", "Non-Veg", "Both"
    image_url: Optional[str] = None
    is_active: bool = True
    display_order: int = 0


class MenuCategoryCreate(MenuCategoryBase):
    pass


class MenuCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    food_type: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class MenuCategory(MenuCategoryBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# ==========================================
# Menu Subcategory Models
# ==========================================

class MenuSubcategoryBase(BaseModel):
    name: str
    category_id: str
    description: Optional[str] = None
    is_active: bool = True
    display_order: int = 0


class MenuSubcategoryCreate(MenuSubcategoryBase):
    pass


class MenuSubcategoryUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class MenuSubcategory(MenuSubcategoryBase):
    id: str
    category_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


# ==========================================
# Menu Item Models
# ==========================================

class MenuItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: str
    subcategory_id: Optional[str] = None
    price: Decimal
    base_price: Optional[Decimal] = None
    discount: Optional[Decimal] = Decimal("0")
    tax: Optional[Decimal] = Decimal("0")
    final_price: Optional[Decimal] = None
    preparation_time: int = 15
    is_available: bool = True
    is_vegetarian: bool = False
    food_type: Optional[str] = None  # "Veg", "Non-Veg"
    type: Optional[str] = None
    image_url: Optional[str] = None
    is_featured: bool = False
    is_active: bool = True
    display_order: int = 0
    spicy_level: Optional[str] = None
    serving_size: Optional[str] = None
    tags: Optional[List[str]] = None


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    price: Optional[Decimal] = None
    base_price: Optional[Decimal] = None
    discount: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    final_price: Optional[Decimal] = None
    preparation_time: Optional[int] = None
    is_available: Optional[bool] = None
    is_vegetarian: Optional[bool] = None
    food_type: Optional[str] = None
    type: Optional[str] = None
    image_url: Optional[str] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    spicy_level: Optional[str] = None
    serving_size: Optional[str] = None
    tags: Optional[List[str]] = None


class MenuItem(MenuItemBase):
    id: str
    category_name: Optional[str] = None
    subcategory_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
