from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict


class StockMovementModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )

    id: Optional[ObjectId] = None

    ingredient_id: ObjectId
    movement_type: str = Field(...)
    quantity: float = Field(...)
    previous_stock: Optional[float] = None
    new_stock: Optional[float] = None
    reference_type: Optional[str] = None
    reference_id: Optional[ObjectId] = None
    reason: Optional[str] = None
    performed_by: Optional[ObjectId] = None
    created_at: Optional[datetime] = None