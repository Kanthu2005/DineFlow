from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class KitchenTicketCreate(BaseModel):
    order_id: str
    priority: str = "NORMAL"

class KitchenStaffAssignment(BaseModel):
    staff_id: str

class KitchenTicket(BaseModel):
    id: str
    order_id: str
    status: str
    priority: str
    assigned_staff_id: Optional[str] = None
    started_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
