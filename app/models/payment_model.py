from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime

class InvoiceCreate(BaseModel):
    order_id: str

class PaymentCreate(BaseModel):
    invoice_id: str
    amount: Decimal
    method: str

class RefundCreate(BaseModel):
    payment_id: str
    reason: str

class RefundApproval(BaseModel):
    approved_by: str
    approved_at: datetime
