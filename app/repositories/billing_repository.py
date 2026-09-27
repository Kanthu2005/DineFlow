"""
Billing and Payment Repository for Invoices, Payments, and Refunds.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.database.mongodb import invoices_collection, payments_collection, refunds_collection
from app.repositories.base_repository import BaseRepository
from app.services.common import to_object_id, serialize_document, serialize_documents


class BillingRepository(BaseRepository):
    def __init__(self):
        super().__init__(invoices_collection)
        self.payments_col = payments_collection
        self.refunds_col = refunds_collection

    def find_invoice_by_order(self, order_id: str | ObjectId) -> Optional[Dict[str, Any]]:
        oid = to_object_id(order_id)
        doc = self.collection.find_one({"order_id": oid})
        return serialize_document(doc) if doc else None

    def find_invoice_by_number(self, invoice_number: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"invoice_number": invoice_number})
        return serialize_document(doc) if doc else None

    # Payments
    def record_payment(self, payment_doc: Dict[str, Any]) -> Dict[str, Any]:
        res = self.payments_col.insert_one(payment_doc)
        payment_doc["_id"] = res.inserted_id
        return serialize_document(payment_doc)

    def find_payments_by_invoice(self, invoice_id: str | ObjectId) -> List[Dict[str, Any]]:
        oid = to_object_id(invoice_id)
        docs = self.payments_col.find({"invoice_id": oid}).sort("paid_at", -1)
        return serialize_documents(docs)

    def find_payment_by_id(self, payment_id: str | ObjectId) -> Optional[Dict[str, Any]]:
        oid = to_object_id(payment_id)
        doc = self.payments_col.find_one({"_id": oid})
        return serialize_document(doc) if doc else None

    def find_payment_by_reference(self, reference: str) -> Optional[Dict[str, Any]]:
        if not reference:
            return None
        doc = self.payments_col.find_one({"transaction_reference": reference})
        return serialize_document(doc) if doc else None

    # Refunds
    def record_refund(self, refund_doc: Dict[str, Any]) -> Dict[str, Any]:
        res = self.refunds_col.insert_one(refund_doc)
        refund_doc["_id"] = res.inserted_id
        return serialize_document(refund_doc)

    def find_refund_by_id(self, refund_id: str | ObjectId) -> Optional[Dict[str, Any]]:
        oid = to_object_id(refund_id)
        doc = self.refunds_col.find_one({"_id": oid})
        return serialize_document(doc) if doc else None

    def find_refunds_by_order(self, order_id: str | ObjectId) -> List[Dict[str, Any]]:
        oid = to_object_id(order_id)
        docs = self.refunds_col.find({"order_id": oid}).sort("created_at", -1)
        return serialize_documents(docs)
