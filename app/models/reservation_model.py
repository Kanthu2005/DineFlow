from datetime import date, time, datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict


class ReservationModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )

    id: Optional[ObjectId] = None

    customer_id: ObjectId
    table_id: ObjectId

    reservation_date: date
    reservation_time: time

    guest_count: int = Field(..., gt=0)

    status: str = Field(default="PENDING")

    contact_number: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None