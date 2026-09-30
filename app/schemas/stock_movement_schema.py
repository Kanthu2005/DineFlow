from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class StockMovementCreate(BaseModel):
    ingredient_id: str
    movement_type: str
    quantity: Decimal = Field(gt=0)
    unit: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    created_by: str = "SYSTEM"


class StockMovementResponse(BaseModel):
    id: str
    ingredient_id: str
    movement_type: str
    quantity: Decimal
    unit: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    created_by: str
    created_at: datetime
    ingredient_name: Optional[str] = None
