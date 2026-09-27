"""
Billing, Payment, and Refund Routes.
Supports both /orders/{id}/invoice and /invoices conventions.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.payments_schema import (
    InvoiceCreate,
    PaymentCreate,
    RefundCreate,
    RefundApproval,
)
from app.services.billing_service import BillingService
from app.services.payment_service import PaymentService
from app.services.refund_service import RefundService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Billing & Payments"])


# ==========================================
# Invoices
# ==========================================

@router.post("/orders/{order_id}/invoice", status_code=status.HTTP_201_CREATED, summary="Generate Order Invoice")
@router.post("/invoices", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_invoice(
    order_id: Optional[str] = None,
    data: Optional[InvoiceCreate] = None,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CASHIER")),
):
    try:
        oid = order_id or (data.order_id if data else None)
        if not oid:
            raise ValueError("order_id is required to create invoice")
        return BillingService.create_invoice(oid)
    except Exception as e:
        handle_error(e)


@router.get("/orders/{order_id}/invoice", summary="Get Order Invoice")
@router.get("/invoices/order/{order_id}", include_in_schema=False)
def get_order_invoice(
    order_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CASHIER")),
):
    try:
        return BillingService.get_by_order(order_id)
    except Exception as e:
        handle_error(e)


@router.get("/invoices")
def get_invoices(
    status: Optional[str] = None,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CASHIER")),
):
    try:
        return BillingService.get_invoices(status)
    except Exception as e:
        handle_error(e)


@router.get("/invoices/{invoice_id}")
def get_invoice(
    invoice_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CASHIER")),
):
    try:
        return BillingService.get_invoice(invoice_id)
    except Exception as e:
        handle_error(e)


# ==========================================
# Payments
# ==========================================

@router.post("/payments", status_code=status.HTTP_201_CREATED)
def create_payment(
    data: PaymentCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CASHIER")),
):
    try:
        return PaymentService.create_payment(data)
    except Exception as e:
        handle_error(e)


@router.get("/payments")
def get_payments(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CASHIER")),
):
    try:
        return PaymentService.get_payments()
    except Exception as e:
        handle_error(e)


@router.get("/payments/{payment_id}")
def get_payment(
    payment_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CASHIER")),
):
    try:
        return PaymentService.get_payment(payment_id)
    except Exception as e:
        handle_error(e)


@router.get("/payments/invoice/{invoice_id}")
def get_invoice_payments(
    invoice_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CASHIER")),
):
    try:
        return PaymentService.get_by_invoice(invoice_id)
    except Exception as e:
        handle_error(e)


# ==========================================
# Refunds
# ==========================================

@router.post("/refunds", status_code=status.HTTP_201_CREATED)
def create_refund(
    data: RefundCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CASHIER")),
):
    try:
        return RefundService.create_refund(data)
    except Exception as e:
        handle_error(e)


@router.patch("/refunds/{refund_id}/approve")
def approve_refund(
    refund_id: str,
    data: RefundApproval,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return RefundService.approve_refund(refund_id, data)
    except Exception as e:
        handle_error(e)


@router.get("/refunds/order/{order_id}")
def get_order_refunds(
    order_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CASHIER")),
):
    try:
        return RefundService.get_by_order(order_id)
    except Exception as e:
        handle_error(e)


@router.get("/refunds/{refund_id}")
def get_refund(
    refund_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CASHIER")),
):
    try:
        return RefundService.get_refund(refund_id)
    except Exception as e:
        handle_error(e)
