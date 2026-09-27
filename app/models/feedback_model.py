from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict


class FeedbackModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )

    id: Optional[ObjectId] = None

    order_id: ObjectId
    customer_id: ObjectId

    rating: int = Field(..., ge=1, le=5)
    food_rating: int = Field(..., ge=1, le=5)
    service_rating: int = Field(..., ge=1, le=5)

    comments: Optional[str] = None
    created_at: Optional[datetime] = None