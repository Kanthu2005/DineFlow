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
    def _format_items(items_raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        formatted = []
        for it in (items_raw or []):
            p = it.get("unit_price_snapshot") or it.get("price") or 0
            p_val = float(p.to_decimal() if isinstance(p, Decimal128) else Decimal(str(p or 0)))
            t = it.get("item_total")
            t_val = float(t.to_decimal() if isinstance(t, Decimal128) else Decimal(str(t or 0)))
            p_add = it.get("price_at_addition")
            p_add_val = float(p_add.to_decimal() if isinstance(p_add, Decimal128) else Decimal(str(p_add or p_val))) if p_add else p_val
            formatted.append({
                "id": str(it.get("id") or it.get("_id", "")),
                "name": it.get("item_name_snapshot") or it.get("name") or "Dish Item",
                "price": p_val,
                "price_at_addition": p_add_val,
                "quantity": int(it.get("quantity", 1)),
                "item_total": t_val,
                "special_instructions": it.get("special_instructions") or "",
                "status": it.get("status", "DELIVERED"),
                "batch_number": it.get("batch_number", 1),
                "is_additional": bool(it.get("is_additional", False)),
                "added_at": it.get("added_at") or it.get("created_at"),
            })
        return formatted

    @staticmethod
    def create_invoice(order_id: str, discount_amount: Optional[Decimal] = None) -> Dict[str, Any]:
        order = order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        # If discount_amount is explicitly provided, update the order discount first
        if discount_amount is not None:
            from app.services.order_service import OrderService
            OrderService.update_discount(order_id, discount_amount)
            order = order_repo.find_by_id(order_id)
        else:
            from app.services.order_service import OrderItemService
            OrderItemService.recalculate_order(order_id)
            order = order_repo.find_by_id(order_id)

        subtotal_dec = order["subtotal"].to_decimal() if isinstance(order["subtotal"], Decimal128) else Decimal(str(order["subtotal"]))
        discount_dec = order["discount_amount"].to_decimal() if isinstance(order["discount_amount"], Decimal128) else Decimal(str(order["discount_amount"]))
        tax_dec = order["tax_amount"].to_decimal() if isinstance(order["tax_amount"], Decimal128) else Decimal(str(order["tax_amount"]))
        total_dec = order["total_amount"].to_decimal() if isinstance(order["total_amount"], Decimal128) else Decimal(str(order["total_amount"]))

        prev_sub = order.get("previous_item_total", Decimal("0"))
        prev_sub_dec = prev_sub.to_decimal() if isinstance(prev_sub, Decimal128) else Decimal(str(prev_sub or 0))
        new_sub = order.get("new_item_total", Decimal("0"))
        new_sub_dec = new_sub.to_decimal() if isinstance(new_sub, Decimal128) else Decimal(str(new_sub or 0))

        table_number = order.get("table_number")
        if not table_number and order.get("table_id"):
            from app.database.mongodb import restaurant_tables_collection
            tbl = restaurant_tables_collection.find_one({"_id": to_object_id(order["table_id"])})
            if tbl:
                table_number = tbl.get("table_number")

        items_raw = order_repo.find_order_items(order_id)
        formatted_items = BillingService._format_items(items_raw)

        existing = billing_repo.find_invoice_by_order(order_id)
        if existing:
            billing_repo.update(existing["id"], {
                "subtotal": decimal128(subtotal_dec),
                "previous_item_total": decimal128(prev_sub_dec),
                "new_item_total": decimal128(new_sub_dec),
                "discount_amount": decimal128(discount_dec),
                "tax_amount": decimal128(tax_dec),
                "total_amount": decimal128(total_dec),
                "table_number": table_number,
                "order_number": order.get("order_number"),
                "customer_name": order.get("customer_name"),
            })
            existing["subtotal"] = subtotal_dec
            existing["previous_item_total"] = prev_sub_dec
            existing["new_item_total"] = new_sub_dec
            existing["discount_amount"] = discount_dec
            existing["tax_amount"] = tax_dec
            existing["total_amount"] = total_dec
            existing["items"] = formatted_items
            existing["order_number"] = order.get("order_number")
            existing["table_number"] = table_number
            existing["customer_name"] = order.get("customer_name")
            return existing

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

        doc = {
            "order_id": to_object_id(order_id),
            "order_number": order.get("order_number"),
            "table_number": table_number,
            "customer_name": order.get("customer_name"),
            "invoice_number": entity.invoice_number,
            "subtotal": decimal128(entity.subtotal),
            "previous_item_total": decimal128(prev_sub_dec),
            "new_item_total": decimal128(new_sub_dec),
            "discount_amount": decimal128(entity.discount_amount),
            "tax_amount": decimal128(entity.tax_amount),
            "total_amount": decimal128(entity.total_amount),
            "status": entity.status,
            "generated_at": now_utc(),
        }

        created = billing_repo.insert(doc)
        created["items"] = formatted_items
        created["previous_item_total"] = prev_sub_dec
        created["new_item_total"] = new_sub_dec
        return created

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
                raw_items = order_repo.find_order_items(ord_doc["id"])
                invoice["items"] = BillingService._format_items(raw_items)
                prev_tot = ord_doc.get("previous_item_total")
                new_tot = ord_doc.get("new_item_total")
                invoice["previous_item_total"] = prev_tot.to_decimal() if isinstance(prev_tot, Decimal128) else prev_tot
                invoice["new_item_total"] = new_tot.to_decimal() if isinstance(new_tot, Decimal128) else new_tot
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
                raw_items = order_repo.find_order_items(ord_doc["id"])
                invoice["items"] = BillingService._format_items(raw_items)
                prev_tot = ord_doc.get("previous_item_total")
                new_tot = ord_doc.get("new_item_total")
                invoice["previous_item_total"] = prev_tot.to_decimal() if isinstance(prev_tot, Decimal128) else prev_tot
                invoice["new_item_total"] = new_tot.to_decimal() if isinstance(new_tot, Decimal128) else new_tot
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
                    raw_items = order_repo.find_order_items(ord_doc["id"])
                    inv["items"] = BillingService._format_items(raw_items)
                    prev_tot = ord_doc.get("previous_item_total")
                    new_tot = ord_doc.get("new_item_total")
                    inv["previous_item_total"] = prev_tot.to_decimal() if isinstance(prev_tot, Decimal128) else prev_tot
                    inv["new_item_total"] = new_tot.to_decimal() if isinstance(new_tot, Decimal128) else new_tot
        return invoices
