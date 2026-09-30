"""
Billing Service.
Handles Invoice generation, calculation sequences, and outstanding balance tracking.
Calculation Order: Item Total -> Subtotal -> Discount -> Tax -> Final Total.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId
from bson.decimal128 import Decimal128

from app.database.mongodb import invoices_collection, orders_collection
from app.repositories.billing_repository import BillingRepository
from app.repositories.order_repository import OrderRepository
from app.models.entities import Invoice as InvoiceEntity
from app.services.common import (
    now_utc,
    to_object_id,
    decimal128,
    generate_number,
    serialize_document,
    serialize_documents,
)

billing_repo = BillingRepository()
order_repo = OrderRepository()


class BillingService:

    @staticmethod
    def create_invoice(order_id: str) -> Dict[str, Any]:
        order = order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        existing = billing_repo.find_invoice_by_order(order_id)
        if existing:
            return existing

        subtotal_dec = order["subtotal"].to_decimal() if isinstance(order["subtotal"], Decimal128) else Decimal(str(order["subtotal"]))
        discount_dec = order["discount_amount"].to_decimal() if isinstance(order["discount_amount"], Decimal128) else Decimal(str(order["discount_amount"]))
        tax_dec = order["tax_amount"].to_decimal() if isinstance(order["tax_amount"], Decimal128) else Decimal(str(order["tax_amount"]))
        total_dec = order["total_amount"].to_decimal() if isinstance(order["total_amount"], Decimal128) else Decimal(str(order["total_amount"]))

        invoice_number = generate_number("INV")

        entity = InvoiceEntity(
            order_id=order_id,
            invoice_number=invoice_number,
            subtotal=subtotal_dec,
            discount_amount=discount_dec,
            tax_amount=tax_dec,
            total_amount=total_dec,
            status="UNPAID",
        )

        table_number = order.get("table_number")
        if not table_number and order.get("table_id"):
            from app.database.mongodb import restaurant_tables_collection
            tbl = restaurant_tables_collection.find_one({"_id": to_object_id(order["table_id"])})
            if tbl:
                table_number = tbl.get("table_number")

        doc = {
            "order_id": to_object_id(order_id),
            "order_number": order.get("order_number"),
            "table_number": table_number,
            "customer_name": order.get("customer_name"),
            "invoice_number": entity.invoice_number,
            "subtotal": decimal128(entity.subtotal),
            "discount_amount": decimal128(entity.discount_amount),
            "tax_amount": decimal128(entity.tax_amount),
            "total_amount": decimal128(entity.total_amount),
            "status": entity.status,
            "generated_at": now_utc(),
        }

        return billing_repo.insert(doc)

    @staticmethod
    def get_invoice(invoice_id: str) -> Dict[str, Any]:
        invoice = billing_repo.find_by_id(invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        if invoice.get("order_id"):
            ord_doc = order_repo.find_by_id(invoice["order_id"])
            if ord_doc:
                invoice["order_number"] = ord_doc.get("order_number")
                invoice["table_number"] = ord_doc.get("table_number")
                invoice["customer_name"] = ord_doc.get("customer_name")
                invoice["items"] = order_repo.find_order_items(ord_doc["id"])
        return invoice

    @staticmethod
    def get_invoice_by_order(order_id: str) -> Dict[str, Any]:
        invoice = billing_repo.find_invoice_by_order(order_id)
        if not invoice:
            raise ValueError("Invoice not found for this order")
        if invoice.get("order_id"):
            ord_doc = order_repo.find_by_id(invoice["order_id"])
            if ord_doc:
                invoice["order_number"] = ord_doc.get("order_number")
                invoice["table_number"] = ord_doc.get("table_number")
                invoice["customer_name"] = ord_doc.get("customer_name")
                invoice["items"] = order_repo.find_order_items(ord_doc["id"])
        return invoice

    @staticmethod
    def get_by_order(order_id: str) -> Dict[str, Any]:
        return BillingService.get_invoice_by_order(order_id)

    @staticmethod
    def get_invoices(status: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {}
        if status:
            query["status"] = status.upper()

        invoices = billing_repo.find_all(query=query, sort_field="generated_at", sort_dir=-1)
        for inv in invoices:
            if inv.get("order_id"):
                ord_doc = order_repo.find_by_id(inv["order_id"])
                if ord_doc:
                    inv["order_number"] = ord_doc.get("order_number")
                    inv["order_type"] = ord_doc.get("order_type")
                    inv["table_number"] = ord_doc.get("table_number")
                    inv["customer_name"] = ord_doc.get("customer_name")
                    inv["items"] = order_repo.find_order_items(ord_doc["id"])
        return invoices
