from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SupplierCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    contact_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_id_gst: Optional[str] = None
    payment_terms: Optional[str] = "Net 30"
    is_active: bool = True


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    contact_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_id_gst: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(BaseModel):
    id: str
    name: str
    contact_number: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    tax_id_gst: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
