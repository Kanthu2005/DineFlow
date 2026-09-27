from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class StockMovementCreate(BaseModel):
    ingredient_id: str
    movement_type: str
    quantity: Decimal = Field(gt=0)
    reference_type: str | None = None
    reference_id: str | None = None
    created_by: str


class StockMovementResponse(BaseModel):
    id: str
    ingredient_id: str
    movement_type: str
    quantity: Decimal
    reference_type: str | None = None
    reference_id: str | None = None
    created_by: str
    created_at: datetime
