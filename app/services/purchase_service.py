"""
Purchase Order Procurement Service.
Manages Purchase Orders lifecycle: DRAFT -> ORDERED -> RECEIVED / PARTIALLY_RECEIVED / CANCELLED.
Integrates stock receiving when goods are verified and physically received.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.repositories.inventory_repository import (
    PurchaseOrderRepository,
    SupplierRepository,
    IngredientRepository,
)
from app.services.ingredient_service import IngredientService
from app.services.common import (
    to_object_id,
    decimal128,
    now_utc,
    serialize_document,
    serialize_documents,
    get_field,
)
from app.database.mongodb import purchase_orders_collection

po_repo = PurchaseOrderRepository()
supplier_repo = SupplierRepository()
ing_repo = IngredientRepository()


class PurchaseService:

    @staticmethod
    def create_purchase_order(data: Any, created_by: str = "SYSTEM") -> Dict[str, Any]:
        """
        Creates a new Purchase Order in DRAFT status.
        IMPORTANT: Does NOT update inventory at creation time.
        """
        supplier_id = get_field(data, "supplier_id")
        items_data = get_field(data, "items", [])
        expected_delivery = get_field(data, "expected_delivery_date")
        notes = get_field(data, "notes")

        if not supplier_id:
            raise ValueError("supplier_id is required")
        if not items_data:
            raise ValueError("Purchase order must contain at least one item")

        supplier = supplier_repo.find_by_id(supplier_id)
        if not supplier:
            raise ValueError("Supplier not found")

        total_expected_cost = Decimal("0")
        processed_items = []

        for item in items_data:
            ing_id = get_field(item, "ingredient_id")
            qty = Decimal(str(get_field(item, "quantity", 0)))
            cost = Decimal(str(get_field(item, "unit_cost", 0)))
            unit = get_field(item, "unit")

            if qty <= 0:
                raise ValueError("Item quantity must be greater than zero")
            if cost < 0:
                raise ValueError("Item cost cannot be negative")

            ing = ing_repo.find_by_id(ing_id)
            if not ing:
                raise ValueError(f"Ingredient ID {ing_id} not found")

            item_total = qty * cost
            total_expected_cost += item_total

            processed_items.append({
                "ingredient_id": to_object_id(ing_id),
                "ingredient_name": ing.get("name"),
                "quantity": decimal128(qty),
                "received_quantity": decimal128(Decimal("0")),
                "unit": unit or ing.get("unit"),
                "unit_cost": decimal128(cost),
                "total_cost": decimal128(item_total),
            })

        timestamp_num = int(now_utc().timestamp()) % 100000
        po_number = f"PO-{now_utc().strftime('%Y%m%d')}-{timestamp_num:05d}"

        doc = {
            "po_number": po_number,
            "supplier_id": to_object_id(supplier_id),
            "supplier_name": supplier.get("name"),
            "items": processed_items,
            "total_expected_cost": decimal128(total_expected_cost),
            "total_amount": decimal128(total_expected_cost),
            "total_cost": decimal128(total_expected_cost),
            "status": "DRAFT",  # DRAFT | ORDERED | PARTIALLY_RECEIVED | RECEIVED | CANCELLED
            "order_date": now_utc(),
            "expected_delivery_date": expected_delivery,
            "received_date": None,
            "notes": notes,
            "created_by": created_by,
            "created_at": now_utc(),
            "updated_at": now_utc(),
        }

        res = purchase_orders_collection.insert_one(doc)
        doc["_id"] = res.inserted_id
        return serialize_document(doc)

    @staticmethod
    def get_purchase_orders(status: Optional[str] = None) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if status and status != "ALL":
            query["status"] = status.upper()
        docs = list(purchase_orders_collection.find(query).sort("order_date", -1))
        return serialize_documents(docs)

    @staticmethod
    def get_purchase_order(po_id: str) -> Dict[str, Any]:
        po = po_repo.find_by_id(po_id)
        if not po:
            raise ValueError("Purchase order not found")
        return po

    @staticmethod
    def update_status(po_id: str, new_status: str) -> Dict[str, Any]:
        valid_statuses = ["DRAFT", "ORDERED", "PARTIALLY_RECEIVED", "RECEIVED", "CANCELLED"]
        st = new_status.upper()
        if st not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}. Valid: {valid_statuses}")

        po = PurchaseService.get_purchase_order(po_id)
        if po["status"] in ["RECEIVED", "CANCELLED"] and st != po["status"]:
            raise ValueError(f"Cannot change status of a {po['status']} purchase order")

        po_repo.update(po_id, {"status": st, "updated_at": now_utc()})
        return PurchaseService.get_purchase_order(po_id)

    @staticmethod
    def receive_purchase_order(
        po_id: str,
        receive_data: Optional[Any] = None,
        performed_by: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """
        Receives goods from a Purchase Order.
        Updates stock by calling IngredientService.receive_stock,
        creating corresponding batches and movements for each item received.
        """
        po = PurchaseService.get_purchase_order(po_id)
        if po["status"] in ["RECEIVED", "CANCELLED"]:
            raise ValueError(f"Purchase order is already {po['status']}")

        received_items = get_field(receive_data, "items") if receive_data else None
        receipt_results = []
        all_fully_received = True

        updated_items = []
        for itm in po["items"]:
            ing_id = str(itm["ingredient_id"])
            expected_qty = Decimal(str(itm["quantity"]))
            already_recv = Decimal(str(itm.get("received_quantity") or 0))
            cost = Decimal(str(itm["unit_cost"]))

            # Look up specific receipt data if provided
            recv_item_info = None
            if received_items:
                recv_item_info = next((r for r in received_items if str(get_field(r, "ingredient_id")) == ing_id), None)

            if recv_item_info:
                recv_qty = Decimal(str(get_field(recv_item_info, "received_quantity", expected_qty - already_recv)))
                batch_no = get_field(recv_item_info, "batch_number")
                exp_date = get_field(recv_item_info, "expiry_date")
                loc_id = get_field(recv_item_info, "storage_location_id")
            else:
                recv_qty = expected_qty - already_recv
                batch_no = f"{po['po_number']}-{itm.get('ingredient_name', 'ITEM')[:3].upper()}"
                exp_date = None
                loc_id = None

            if recv_qty > 0:
                result = IngredientService.receive_stock(
                    ingredient_id=ing_id,
                    quantity=recv_qty,
                    unit_cost=cost,
                    supplier_id=str(po["supplier_id"]),
                    purchase_order_id=po_id,
                    batch_number=batch_no,
                    expiry_date=exp_date,
                    storage_location_id=loc_id,
                    reason=f"Received via PO {po['po_number']}",
                    performed_by=performed_by,
                )
                receipt_results.append(result)

            total_now_recv = already_recv + recv_qty
            if total_now_recv < expected_qty:
                all_fully_received = False
            
            encoded_item = {
                "ingredient_id": to_object_id(itm["ingredient_id"]),
                "ingredient_name": itm.get("ingredient_name"),
                "quantity": decimal128(itm["quantity"]),
                "received_quantity": decimal128(total_now_recv),
                "unit": itm.get("unit"),
                "unit_cost": decimal128(itm["unit_cost"]),
                "total_cost": decimal128(itm.get("total_cost", Decimal(str(itm["quantity"])) * Decimal(str(itm["unit_cost"])))),
            }
            updated_items.append(encoded_item)

        final_status = "RECEIVED" if all_fully_received else "PARTIALLY_RECEIVED"
        po_repo.update(po_id, {
            "status": final_status,
            "items": updated_items,
            "received_date": now_utc(),
            "updated_at": now_utc(),
        })

        return {
            "message": f"Purchase order goods received successfully ({final_status})",
            "po_number": po["po_number"],
            "status": final_status,
            "receipt_summary": receipt_results,
        }
