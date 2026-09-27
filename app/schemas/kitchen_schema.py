from datetime import datetime

from pydantic import BaseModel


class KitchenTicketCreate(BaseModel):
    order_id: str
    priority: str = "NORMAL"


class KitchenTicketResponse(BaseModel):
    id: str
    order_id: str
    status: str
    priority: str
    assigned_staff_id: str | None = None
    started_at: datetime | None = None
    ready_at: datetime | None = None
    completed_at: datetime | None = None


class KitchenTicketItemCreate(BaseModel):
    order_item_id: str
    station: str


class KitchenTicketItemResponse(BaseModel):
    id: str
    kitchen_ticket_id: str
    order_item_id: str
    station: str
    status: str


class KitchenStaffAssignment(BaseModel):
    staff_id: str


class StaffAssignmentResponse(BaseModel):
    id: str
    kitchen_ticket_id: str
    staff_id: str
    assigned_at: datetime
    unassigned_at: datetime | None = None


class PreparationEstimateResponse(BaseModel):
    order_id: str
    estimated_minutes: int
    estimated_ready_time: datetime
    calculation_basis: str