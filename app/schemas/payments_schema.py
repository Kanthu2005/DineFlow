from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

#invoice...

class InvoiceCreate(BaseModel):
    order_id: str

class InvoiceResponse(BaseModel):
    id: str
    order_id: str
    invoice_number: str
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    status: str
    generated_at: datetime

#payment...
class PaymentCreate(BaseModel):
    invoice_id: str
    amount: Decimal = Field(gt=0)
    payment_method: str
    transaction_reference: str | None = None
    recorded_by: str | None = None


class PaymentResponse(BaseModel):
    id: str
    invoice_id: str
    amount: Decimal
    payment_method: str
    payment_status: str
    transaction_reference: str | None = None
    paid_at: datetime | None = None
    recorded_by: str | None = None

#refund...
class RefundCreate(BaseModel):
    payment_id: str
    order_id: str
    requested_amount: Decimal = Field(gt=0)
    reason: str = Field(min_length=3, max_length=500)


class RefundApproval(BaseModel):
    approved_amount: Decimal = Field(ge=0)
    approved_by: str | None = None


class RefundResponse(BaseModel):
    id: str
    payment_id: str
    order_id: str
    requested_amount: Decimal
    approved_amount: Decimal
    reason: str
    status: str
    approved_by: str | None = None
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime