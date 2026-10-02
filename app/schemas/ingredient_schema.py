from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class IngredientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    sku: Optional[str] = None
    category: Optional[str] = "Other"
    category_id: Optional[str] = None
    unit: str = Field(min_length=1, max_length=20)
    available_quantity: Optional[Decimal] = Field(default=Decimal("0"), ge=0)
    current_stock: Optional[Decimal] = Field(default=None, ge=0)
    minimum_stock_level: Optional[Decimal] = Field(default=Decimal("0"), ge=0)
    minimum_stock: Optional[Decimal] = Field(default=None, ge=0)
    maximum_stock: Optional[Decimal] = Field(default=None, ge=0)
    reorder_level: Optional[Decimal] = Field(default=None, ge=0)
    cost_per_unit: Decimal = Field(default=Decimal("0"), ge=0)
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    storage_location_id: Optional[str] = None
    storage_location_name: Optional[str] = None
    is_active: bool = True


class IngredientUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    sku: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[str] = None
    unit: Optional[str] = None
    available_quantity: Optional[Decimal] = Field(default=None, ge=0)
    current_stock: Optional[Decimal] = Field(default=None, ge=0)
    minimum_stock_level: Optional[Decimal] = Field(default=None, ge=0)
    minimum_stock: Optional[Decimal] = Field(default=None, ge=0)
    maximum_stock: Optional[Decimal] = Field(default=None, ge=0)
    reorder_level: Optional[Decimal] = Field(default=None, ge=0)
    cost_per_unit: Optional[Decimal] = Field(default=None, ge=0)
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    storage_location_id: Optional[str] = None
    storage_location_name: Optional[str] = None
    is_active: Optional[bool] = None


class StockUpdate(BaseModel):
    quantity: Decimal


class StockReceiveSchema(BaseModel):
    quantity: Decimal = Field(gt=0)
    unit_cost: Optional[Decimal] = Field(default=None, ge=0)
    supplier_id: Optional[str] = None
    purchase_order_id: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    storage_location_id: Optional[str] = None
    reason: Optional[str] = "Stock Received"


class WastageCreateSchema(BaseModel):
    ingredient_id: Optional[str] = None
    quantity: Decimal = Field(gt=0)
    reason: str = Field(description="EXPIRED, SPOILED, BURNT, OVER_PRODUCTION, DAMAGED, SPILLAGE, PREPARATION_ERROR, OTHER")
    batch_id: Optional[str] = None
    notes: Optional[str] = None


class StockAdjustmentSchema(BaseModel):
    physical_stock: Decimal = Field(ge=0)
    reason: str = Field(description="PHYSICAL_COUNT, DAMAGED, SYSTEM_ERROR, OPENING_BALANCE, OTHER")
    notes: Optional[str] = None


class StockTransferSchema(BaseModel):
    ingredient_id: Optional[str] = None
    from_location_id: str
    to_location_id: str
    quantity: Decimal = Field(gt=0)
    batch_id: Optional[str] = None
    notes: Optional[str] = None


class CategoryCreateSchema(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    description: Optional[str] = None


class StorageLocationCreateSchema(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    description: Optional[str] = None
    temperature_type: Optional[str] = "AMBIENT"  # AMBIENT | CHILLED | FROZEN


class IngredientResponse(BaseModel):
    id: str
    name: str
    sku: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[str] = None
    unit: str
    available_quantity: Decimal
    current_stock: Optional[Decimal] = None
    minimum_stock_level: Decimal
    maximum_stock: Optional[Decimal] = None
    reorder_level: Optional[Decimal] = None
    cost_per_unit: Decimal
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    storage_location_id: Optional[str] = None
    storage_location_name: Optional[str] = None
    is_active: bool
    status: Optional[str] = "NORMAL"
    created_at: datetime
    updated_at: Optional[datetime] = None