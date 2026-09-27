"""
Refund Management Service.
Handles customer refund requests, validation against paid amount, and manager approvals.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId
from bson.decimal128 import Decimal128

from app.database.mongodb import (
    refunds_collection,
    payments_collection,
    orders_collection,
)
from app.repositories.billing_repository import BillingRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.common import (
    now_utc,
    to_object_id,
    decimal128,
    get_field,
    serialize_document,
    serialize_documents,
)

billing_repo = BillingRepository()
order_repo = OrderRepository()
audit_repo = AuditLogRepository()


class RefundService:

    @staticmethod
    def create_refund(data: Any) -> Dict[str, Any]:
        payment_id = get_field(data, "payment_id")
        order_id = get_field(data, "order_id")
        requested_amt_raw = get_field(data, "requested_amount")
        reason = get_field(data, "reason", "Customer requested cancellation/refund")

        payment = billing_repo.find_payment_by_id(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        requested_amount = Decimal(str(requested_amt_raw))
        if requested_amount <= 0:
            raise ValueError("Requested refund amount must be greater than zero")

        payment_amount = payment["amount"].to_decimal() if isinstance(payment["amount"], Decimal128) else Decimal(str(payment["amount"]))

        # Business Rule / Test 28: Reject refund exceeding paid amount
        if requested_amount > payment_amount:
            raise ValueError(
                f"Requested refund amount ({requested_amount}) exceeds original paid payment amount ({payment_amount})"
            )

        doc = {
            "payment_id": to_object_id(payment_id),
            "order_id": to_object_id(order_id) if order_id else payment.get("order_id"),
            "requested_amount": decimal128(requested_amount),
            "approved_amount": decimal128("0"),
            "reason": reason,
            "status": "REQUESTED",
            "approved_by": None,
            "processed_at": None,
            "created_at": now_utc(),
        }

        created = billing_repo.record_refund(doc)

        if doc.get("order_id"):
            audit_repo.record_order_activity(
                order_id=doc["order_id"],
                action="REFUND_REQUESTED",
                performed_by="CASHIER",
                performed_by_role="CASHIER",
                metadata={"refund_id": created["id"], "requested_amount": str(requested_amount)},
            )

        return created

    @staticmethod
    def approve_refund(refund_id: str, data: Any) -> Dict[str, Any]:
        refund = billing_repo.find_refund_by_id(refund_id)
        if not refund:
            raise ValueError("Refund not found")

        requested = refund["requested_amount"].to_decimal() if isinstance(refund["requested_amount"], Decimal128) else Decimal(str(refund["requested_amount"]))

        app_amt_raw = get_field(data, "approved_amount")
        approved_by = str(get_field(data, "approved_by", "MANAGER"))

        approved_amount = Decimal(str(app_amt_raw))
        if approved_amount <= 0:
            raise ValueError("Approved refund amount must be greater than zero")

        if approved_amount > requested:
            raise ValueError(
                f"Approved amount ({approved_amount}) cannot exceed requested amount ({requested})"
            )

        now = now_utc()
        refunds_collection.update_one(
            {"_id": to_object_id(refund_id)},
            {
                "$set": {
                    "approved_amount": decimal128(approved_amount),
                    "approved_by": approved_by,
                    "status": "APPROVED",
                    "processed_at": now,
                }
            },
        )

        # Update order status to REFUNDED or REFUND_PENDING
        if refund.get("order_id"):
            order_repo.update(refund["order_id"], {"status": "REFUNDED"})
            audit_repo.record_order_activity(
                order_id=refund["order_id"],
                action="REFUND_APPROVED",
                performed_by=approved_by,
                performed_by_role="MANAGER",
                metadata={"refund_id": refund_id, "approved_amount": str(approved_amount)},
            )

        return RefundService.get_refund(refund_id)

    @staticmethod
    def get_refund(refund_id: str) -> Dict[str, Any]:
        refund = billing_repo.find_refund_by_id(refund_id)
        if not refund:
            raise ValueError("Refund not found")
        return refund

    @staticmethod
    def get_by_order(order_id: str) -> List[Dict[str, Any]]:
        return billing_repo.find_refunds_by_order(order_id)
