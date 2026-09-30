"""
Payment Management Service.
Handles Payment processing, outstanding balance enforcement, duplicate reference checks,
and table release upon full payment.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId
from bson.decimal128 import Decimal128

from app.database.mongodb import (
    payments_collection,
    invoices_collection,
    orders_collection,
    restaurant_tables_collection,
)
from app.repositories.billing_repository import BillingRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.table_repository import TableRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.common import (
    now_utc,
    to_object_id,
    decimal128,
    generate_number,
    get_field,
    serialize_document,
    serialize_documents,
)

billing_repo = BillingRepository()
order_repo = OrderRepository()
table_repo = TableRepository()
audit_repo = AuditLogRepository()

VALID_PAYMENT_METHODS = ["CASH", "CARD", "UPI", "WALLET", "ONLINE"]


class PaymentService:

    @staticmethod
    def create_payment(data: Any) -> Dict[str, Any]:
        invoice_id = get_field(data, "invoice_id")
        amount_raw = get_field(data, "amount")
        method = str(get_field(data, "payment_method", "CASH")).upper()
        ref = get_field(data, "transaction_reference")
        recorded_by = str(get_field(data, "recorded_by", "CASHIER"))

        if not invoice_id:
            raise ValueError("invoice_id is required")

        invoice = billing_repo.find_by_id(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")

        # Business Rule: Prevent payments on already paid invoice
        if invoice["status"] == "PAID":
            raise ValueError("Invoice is already fully paid. Duplicate payment rejected.")

        # Business Rule: Amount cannot be negative or zero
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero")

        # Check existing successful payments
        existing_payments = billing_repo.find_payments_by_invoice(invoice_id)
        paid_amount = Decimal("0")
        for p in existing_payments:
            if p.get("payment_status") == "SUCCESS":
                p_amt = p["amount"].to_decimal() if isinstance(p["amount"], Decimal128) else Decimal(str(p["amount"]))
                paid_amount += p_amt

        inv_total = invoice["total_amount"].to_decimal() if isinstance(invoice["total_amount"], Decimal128) else Decimal(str(invoice["total_amount"]))
        outstanding = inv_total - paid_amount

        # Business Rule: Payment cannot exceed outstanding amount
        if amount > outstanding:
            raise ValueError(
                f"Payment amount ({amount}) exceeds outstanding amount ({outstanding})"
            )

        # Business Rule: Duplicate transaction references should be rejected
        if ref:
            duplicate = billing_repo.find_payment_by_reference(ref)
            if duplicate:
                raise ValueError(f"Duplicate transaction reference '{ref}' already exists")

        payment_doc = {
            "invoice_id": to_object_id(invoice_id),
            "amount": decimal128(amount),
            "payment_method": method,
            "payment_status": "SUCCESS",
            "recorded_by": recorded_by,
            "paid_at": now_utc(),
        }
        if ref:
            payment_doc["transaction_reference"] = ref

        created = billing_repo.record_payment(payment_doc)

        new_paid_amount = paid_amount + amount

        # Check if full or partial
        if new_paid_amount >= inv_total:
            # Mark invoice as PAID
            billing_repo.update(invoice_id, {"status": "PAID"})

            # Mark order as COMPLETED
            order_id = str(invoice["order_id"])
            from app.services.order_service import OrderService
            OrderService.update_status(order_id, "COMPLETED", performed_by=recorded_by, role="CASHIER")

            # Business Rule: Release table after payment for dine-in orders
            order = order_repo.find_by_id(order_id)
            if order and order.get("table_id"):
                table_repo.set_status(order["table_id"], "AVAILABLE")

            audit_repo.record_order_activity(
                order_id=order_id,
                action="PAYMENT_COMPLETED",
                performed_by=recorded_by,
                performed_by_role="CASHIER",
                metadata={"invoice_id": invoice_id, "amount": str(amount), "method": method},
            )
        else:
            billing_repo.update(invoice_id, {"status": "PARTIALLY_PAID"})

        return created

    @staticmethod
    def get_payment(payment_id: str) -> Dict[str, Any]:
        p = billing_repo.find_payment_by_id(payment_id)
        if not p:
            raise ValueError("Payment not found")
        return p

    @staticmethod
    def get_payments() -> List[Dict[str, Any]]:
        docs = payments_collection.find().sort("paid_at", -1)
        return serialize_documents(docs)

    @staticmethod
    def get_by_invoice(invoice_id: str) -> List[Dict[str, Any]]:
        return billing_repo.find_payments_by_invoice(invoice_id)
