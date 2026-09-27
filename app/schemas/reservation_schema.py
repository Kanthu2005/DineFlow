from datetime import date, datetime, time

from pydantic import BaseModel, Field


class ReservationCreate(BaseModel):
    table_id: str
    reservation_date: date | str
    start_time: time | str
    end_time: time | str
    guest_count: int = Field(gt=0)
    customer_id: str | None = None
    contact_number: str | None = None


class ReservationUpdate(BaseModel):
    reservation_date: date | str | None = None
    start_time: time | str | None = None
    end_time: time | str | None = None
    guest_count: int | None = Field(default=None, gt=0)
    contact_number: str | None = None


class ReservationResponse(BaseModel):
    id: str
    customer_id: str
    table_id: str
    reservation_date: date
    start_time: time
    end_time: time
    guest_count: int
    status: str
    contact_number: str
    created_at: datetime
    updated_at: datetime