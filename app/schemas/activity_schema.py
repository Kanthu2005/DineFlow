from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ActivityLogCreate(BaseModel):
    action: str = Field(description="Action name, e.g. ORDER_CREATED, ORDER_CONFIRMED, ORDER_CANCELLED")
    performed_by: Optional[str] = Field(default=None, description="Performer user ID or name")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata dictionary")


class KitchenEventCreate(BaseModel):
    order_id: str = Field(description="Order ID associated with the kitchen event")
    event_type: str = Field(description="Event type, e.g. STATUS_CHANGED, PREP_DELAY, STAFF_ASSIGNED")
    kitchen_ticket_id: Optional[str] = Field(default=None, description="Optional kitchen ticket ID")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Event metadata such as old_status and new_status")
