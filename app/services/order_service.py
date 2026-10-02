"""
Order Management Service.
Handles Order creation, line items, snapshots, stock verification & deduction,
confirmation, cancellation policies, and audit logging.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId
from bson.decimal128 import Decimal128

from app.database.mongodb import (
    orders_collection,
    order_items_collection,
    menu_items_collection,
    restaurant_tables_collection,
    customers_collection,
    recipes_collection,
    ingredients_collection,
    kitchen_tickets_collection,
    invoices_collection,
)
from app.repositories.order_repository import OrderRepository
from app.repositories.inventory_repository import IngredientRepository, BatchRepository
from app.repositories.table_repository import TableRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.models.entities import Order as OrderEntity, OrderItem as OrderItemEntity
from app.services.common import (
    now_utc,
    to_object_id,
    decimal128,
    generate_number,
    get_field,
    serialize_document,
    serialize_documents,
)
from app.utils.units import convert_quantity

order_repo = OrderRepository()
ing_repo = IngredientRepository()
batch_repo = BatchRepository()
table_repo = TableRepository()
audit_repo = AuditLogRepository()


class OrderService:

    @staticmethod
    def create_order(data: Any) -> Dict[str, Any]:
        customer_id = get_field(data, "customer_id")
        table_id = get_field(data, "table_id")
        order_type = str(get_field(data, "order_type", "DINE_IN")).upper()
        created_by = str(get_field(data, "created_by", "WAITER"))

        if customer_id:
            customer = customers_collection.find_one({"_id": to_object_id(customer_id)})
            if not customer:
                raise ValueError("Customer not found")

        table_number = None
        if table_id:
            table = restaurant_tables_collection.find_one({"_id": to_object_id(table_id)})
            if not table:
                raise ValueError("Table not found")
            if not table["is_active"]:
                raise ValueError("Table is out of service")
            if table["status"] == "OCCUPIED":
                raise ValueError(f"Table {table['table_number']} is already occupied")
            table_number = table.get("table_number")

        order_number = generate_number("ORD")

        doc = {
            "order_number": order_number,
            "customer_id": to_object_id(customer_id) if customer_id else None,
            "table_id": to_object_id(table_id) if table_id else None,
            "table_number": table_number,
            "order_type": order_type,
            "status": "DRAFT",
            "subtotal": Decimal128("0"),
            "tax_amount": Decimal128("0"),
            "discount_amount": decimal128(Decimal(str(get_field(data, "discount_amount", 0) or 0))),
            "total_amount": Decimal128("0"),
            "inventory_deducted": False,
            "created_by": created_by,
            "created_at": now_utc(),
        }

        created = order_repo.insert(doc)

        audit_repo.record_order_activity(
            order_id=created["id"],
            action="ORDER_CREATED",
            performed_by=created_by,
            performed_by_role=created_by,
            metadata={"order_number": order_number, "order_type": order_type},
        )

        items_list = get_field(data, "items")
        if items_list:
            for itm in items_list:
                OrderItemService.add_item(created["id"], itm)
            created = OrderService.get_order(created["id"])

        return created

    @staticmethod
    def _enrich_order(order: Dict[str, Any], items: List[Dict[str, Any]]) -> Dict[str, Any]:
        order["items"] = items
        prev_tot = Decimal("0")
        new_tot = Decimal("0")
        for it in items:
            it_tot = it.get("item_total")
            it_tot_dec = it_tot.to_decimal() if isinstance(it_tot, Decimal128) else Decimal(str(it_tot or 0))
            if it.get("is_additional") or it.get("batch_number", 1) > 1:
                new_tot += it_tot_dec
            else:
                prev_tot += it_tot_dec

        if "previous_item_total" not in order or order.get("previous_item_total") is None:
            order["previous_item_total"] = prev_tot
        if "new_item_total" not in order or order.get("new_item_total") is None:
            order["new_item_total"] = new_tot
        return order

    @staticmethod
    def get_orders(status: Optional[str] = None, order_type: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {}
        if status:
            query["status"] = status.upper()
        if order_type:
            query["order_type"] = order_type.upper()
        orders = order_repo.find_all(query=query, sort_field="created_at", sort_dir=-1)
        for o in orders:
            if o.get("table_id") and not o.get("table_number"):
                tbl = restaurant_tables_collection.find_one({"_id": to_object_id(o["table_id"])})
                if tbl:
                    o["table_number"] = tbl.get("table_number")
            items = order_repo.find_order_items(o["id"])
            OrderService._enrich_order(o, items)
        return orders

    @staticmethod
    def get_order(order_id: str) -> Dict[str, Any]:
        order = order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        if order.get("table_id") and not order.get("table_number"):
            tbl = restaurant_tables_collection.find_one({"_id": to_object_id(order["table_id"])})
            if tbl:
                order["table_number"] = tbl.get("table_number")
        # Attach order items & calculate breakdowns
        items = order_repo.find_order_items(order_id)
        return OrderService._enrich_order(order, items)

    @staticmethod
    def get_order_by_number(order_number: str) -> Dict[str, Any]:
        order = order_repo.find_by_number(order_number)
        if not order:
            raise ValueError("Order not found")
        items = order_repo.find_order_items(order["id"])
        return OrderService._enrich_order(order, items)

    @staticmethod
    def calculate_order_status(order_id: str) -> str:
        """
        Calculates overall order status based on its individual line items.
        - If all active items DELIVERED / SERVED -> DELIVERED
        - If all active items READY -> READY
        - If any active item PREPARING -> PREPARING
        - If any item PENDING and some DELIVERED -> PREPARING (kitchen in progress)
        - If all items PENDING -> PENDING
        """
        items = order_repo.find_order_items(order_id)
        if not items:
            order = order_repo.find_by_id(order_id)
            return order.get("status", "DRAFT") if order else "DRAFT"

        active_items = [i for i in items if i.get("status") != "CANCELLED"]
        if not active_items:
            return "CANCELLED"

        statuses = [i.get("status", "PENDING").upper() for i in active_items]
        delivered_count = sum(1 for s in statuses if s in ["DELIVERED", "SERVED"])

        if delivered_count == len(active_items):
            return "DELIVERED"
        if any(s == "PREPARING" for s in statuses):
            return "PREPARING"
        if all(s == "READY" for s in statuses):
            return "READY"
        if any(s == "PENDING" for s in statuses):
            if delivered_count > 0:
                # Prior items delivered, newly added items are queued/cooking
                return "PREPARING"
            return "PENDING"
        return "PREPARING"

    @staticmethod
    def update_status(order_id: str, new_status: str, performed_by: str = "SYSTEM", role: str = "SYSTEM") -> Dict[str, Any]:
        status_upper = new_status.upper()
        if status_upper not in OrderEntity.VALID_STATUSES:
            raise ValueError(f"Invalid order status: {status_upper}")

        order = OrderService.get_order(order_id)
        old_status = order["status"]

        # Invariant checks
        if old_status in ["CANCELLED", "REFUNDED"] and status_upper != old_status:
            raise ValueError(f"Cannot transition order from finalized status {old_status}")

        order_repo.update(order_id, {"status": status_upper})

        # Update item statuses accordingly
        items = order_repo.find_order_items(order_id)
        if status_upper in ["SERVED", "DELIVERED"]:
            for it in items:
                if it.get("status") not in ["DELIVERED", "SERVED", "CANCELLED"]:
                    order_repo.update_order_item(it["id"], {"status": "DELIVERED"})
            OrderService.deduct_order_inventory(order_id, performed_by=performed_by)
        elif status_upper == "COMPLETED":
            for it in items:
                if it.get("status") not in ["DELIVERED", "SERVED", "CANCELLED"]:
                    order_repo.update_order_item(it["id"], {"status": "DELIVERED"})
            OrderService.deduct_order_inventory(order_id, performed_by=performed_by)
        elif status_upper == "PREPARING":
            for it in items:
                if it.get("status") == "PENDING":
                    order_repo.update_order_item(it["id"], {"status": "PREPARING"})
        elif status_upper == "READY":
            for it in items:
                if it.get("status") in ["PENDING", "PREPARING"]:
                    order_repo.update_order_item(it["id"], {"status": "READY"})

        audit_repo.record_order_activity(
            order_id=order_id,
            action=f"STATUS_CHANGED_TO_{status_upper}",
            performed_by=performed_by,
            performed_by_role=role,
            metadata={"old_status": old_status, "new_status": status_upper},
        )

        return OrderService.get_order(order_id)

    @staticmethod
    def update_item_status(
        order_id: str,
        item_id: str,
        new_status: str,
        performed_by: str = "SYSTEM",
        role: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """
        Updates the status of an individual item in an order.
        When reaching DELIVERED/SERVED, triggers inventory deduction for that item.
        Recalculates the overall order status.
        """
        item = order_repo.find_order_item(item_id)
        if not item or str(item.get("order_id")) != str(order_id):
            raise ValueError("Order item not found")

        status_upper = new_status.upper()
        if status_upper not in OrderItemEntity.VALID_STATUSES:
            raise ValueError(f"Invalid order item status: {status_upper}")

        old_status = item.get("status", "PENDING")
        order_repo.update_order_item(item_id, {"status": status_upper})

        # Deduct inventory if marked DELIVERED/SERVED and not already deducted
        if status_upper in ["DELIVERED", "SERVED"] and not item.get("inventory_deducted", False):
            OrderService._deduct_single_item_inventory(order_id, item, performed_by=performed_by)

        # Recalculate overall status
        new_overall_status = OrderService.calculate_order_status(order_id)
        order_repo.update(order_id, {"status": new_overall_status})

        audit_repo.record_order_activity(
            order_id=order_id,
            action=f"ITEM_STATUS_CHANGED_TO_{status_upper}",
            performed_by=performed_by,
            performed_by_role=role,
            metadata={
                "item_id": str(item_id),
                "item_name": item.get("item_name_snapshot"),
                "old_status": old_status,
                "new_status": status_upper,
                "overall_status": new_overall_status,
            },
        )

        return OrderService.get_order(order_id)

    @staticmethod
    def _deduct_single_item_inventory(order_id: str, item: Dict[str, Any], performed_by: str = "SYSTEM") -> None:
        """Deducts recipe ingredients for a single item when delivered using FEFO."""
        order = order_repo.find_by_id(order_id)
        menu_item = menu_items_collection.find_one({"_id": to_object_id(item["menu_item_id"])})
        if menu_item and not menu_item.get("inventory_tracking_enabled", True):
            order_repo.update_order_item(item["id"], {"inventory_deducted": True})
            return

        recipes = list(recipes_collection.find({"menu_item_id": to_object_id(item["menu_item_id"])}))
        if not recipes:
            order_repo.update_order_item(item["id"], {"inventory_deducted": True})
            return

        for r in recipes:
            ing = ing_repo.find_by_id(r["ingredient_id"])
            if not ing:
                continue
            req_qty = Decimal(str(r["quantity_required"])) * Decimal(str(item["quantity"]))
            rec_unit = r.get("unit") or ing["unit"]
            converted_req = convert_quantity(req_qty, rec_unit, ing["unit"])

            avail = ing.get("available_quantity") or ing.get("current_stock") or Decimal("0")
            avail_dec = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail))
            if avail_dec < converted_req:
                raise ValueError(
                    f"{item.get('item_name_snapshot')} cannot be prepared. {ing['name']} stock is insufficient. Required: {converted_req} {ing['unit']}, Available: {avail_dec} {ing['unit']}."
                )

            # FEFO Batch deduction
            batches = batch_repo.find_active_batches_fefo(ing["id"])
            rem_to_deduct = converted_req
            allocated_batch_id = None
            for b in batches:
                b_rem = b["remaining_quantity"].to_decimal() if hasattr(b["remaining_quantity"], "to_decimal") else Decimal(str(b["remaining_quantity"]))
                if b_rem <= 0:
                    continue
                alloc = min(b_rem, rem_to_deduct)
                batch_repo.decrement_batch(b["id"], alloc)
                allocated_batch_id = to_object_id(b["id"])
                rem_to_deduct -= alloc
                if rem_to_deduct <= 0:
                    break

            ing_repo.increment_stock(ing["id"], -converted_req)
            cost_per_unit = Decimal(str(ing.get("cost_per_unit") or 0))
            ing_repo.record_movement({
                "ingredient_id": to_object_id(ing["id"]),
                "batch_id": allocated_batch_id,
                "movement_type": "ORDER_DEDUCTION",
                "quantity": decimal128(converted_req),
                "unit": ing["unit"],
                "previous_stock": decimal128(avail_dec),
                "new_stock": decimal128(avail_dec - converted_req),
                "unit_cost": decimal128(cost_per_unit),
                "total_cost": decimal128(converted_req * cost_per_unit),
                "reference_type": "ORDER_ITEM",
                "reference_id": order.get("order_number") if order else str(order_id),
                "reason": f"Prepared for {item.get('item_name_snapshot')}",
                "performed_by": performed_by,
                "created_at": now_utc(),
            })

        order_repo.update_order_item(item["id"], {"inventory_deducted": True})

        # Check if all items in order are now deducted
        all_items = order_repo.find_order_items(order_id)
        if all(it.get("inventory_deducted", False) for it in all_items):
            order_repo.update(order_id, {"inventory_deducted": True})

    @staticmethod
    def add_additional_items(
        order_id: str,
        items_data: List[Any],
        performed_by: str = "WAITER",
        role: str = "WAITER",
    ) -> Dict[str, Any]:
        """
        Adds new menu items to an existing order (even after already delivered).
        Business rules:
        - Keeps same order ID and order number.
        - Existing delivered items are preserved unchanged without modification or duplication.
        - New items are appended with status='PENDING', is_additional=True, and incremented batch_number.
        - Recalculates order subtotal (previous + additional), taxes, and total payable amount.
        - Dispatches the new items to the kitchen workflow (creates or updates kitchen ticket).
        - Recalculates billing / existing invoice.
        - Validates inventory/recipe ingredients before adding.
        - Logs audit activity with items, quantities, prices, and timestamp.
        """
        order = order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        if order["status"] in ["CANCELLED", "REFUNDED"]:
            raise ValueError(f"Cannot add items to {order['status']} order")

        if not items_data:
            raise ValueError("No items provided to add to order")

        # 1. Existing items inspection: determine current round/batch
        existing_items = order_repo.find_order_items(order_id)
        current_max_batch = max([it.get("batch_number", 1) for it in existing_items], default=1)
        next_batch = current_max_batch + 1

        # If order was DELIVERED / SERVED / COMPLETED, make sure existing items are marked DELIVERED
        if order["status"] in ["DELIVERED", "SERVED", "COMPLETED"]:
            for prev_it in existing_items:
                if prev_it.get("status") not in ["DELIVERED", "SERVED", "CANCELLED"]:
                    order_repo.update_order_item(prev_it["id"], {"status": "DELIVERED"})

        # 2. Validate inventory sufficiency for ALL newly added items with recipes
        deductions_needed: Dict[str, Dict[str, Any]] = {}
        for itm in items_data:
            m_id = get_field(itm, "menu_item_id")
            qty = int(get_field(itm, "quantity", 1))
            if qty <= 0:
                raise ValueError("Item quantity must be greater than zero")

            menu_item = menu_items_collection.find_one({"_id": to_object_id(m_id)})
            if not menu_item:
                raise ValueError(f"Menu item '{m_id}' not found")
            if not menu_item.get("is_available", True):
                raise ValueError(f"Menu item '{menu_item['name']}' is not available")

            recipes = list(recipes_collection.find({"menu_item_id": menu_item["_id"]}))
            for r in recipes:
                ing = ing_repo.find_by_id(r["ingredient_id"])
                if not ing:
                    continue
                ing_id = str(ing["id"])
                req_qty = Decimal(str(r["quantity_required"])) * Decimal(str(qty))
                rec_unit = r.get("unit") or ing["unit"]
                converted_req = convert_quantity(req_qty, rec_unit, ing["unit"])

                if ing_id not in deductions_needed:
                    avail = ing["available_quantity"].to_decimal() if hasattr(ing["available_quantity"], "to_decimal") else Decimal(str(ing["available_quantity"]))
                    deductions_needed[ing_id] = {
                        "ingredient": ing,
                        "available_qty": avail,
                        "required_qty": Decimal("0"),
                    }
                deductions_needed[ing_id]["required_qty"] += converted_req

        shortages = []
        for ing_id, info in deductions_needed.items():
            ing = info["ingredient"]
            avail = info["available_qty"]
            req = info["required_qty"]
            if avail < req:
                shortage_qty = req - avail
                shortages.append(
                    f"{ing['name']}: Required {req} {ing['unit']}, Available {avail} {ing['unit']}, Shortage {shortage_qty} {ing['unit']}"
                )

        if shortages:
            raise ValueError(f"Insufficient stock to add items: {'; '.join(shortages)}")

        # 3. Append newly added items to the order
        added_items_summary = []
        added_at = now_utc()
        for itm in items_data:
            m_id = get_field(itm, "menu_item_id")
            qty = int(get_field(itm, "quantity", 1))
            specs = get_field(itm, "special_instructions") or ""

            menu_item = menu_items_collection.find_one({"_id": to_object_id(m_id)})
            unit_price = menu_item["price"]
            unit_price_dec = unit_price.to_decimal() if isinstance(unit_price, Decimal128) else Decimal(str(unit_price))
            item_tot = unit_price_dec * Decimal(qty)

            new_item_doc = {
                "order_id": to_object_id(order_id),
                "menu_item_id": menu_item["_id"],
                "item_name_snapshot": menu_item["name"],
                "unit_price_snapshot": decimal128(unit_price_dec),
                "price_at_addition": decimal128(unit_price_dec),
                "quantity": qty,
                "special_instructions": specs,
                "item_total": decimal128(item_tot),
                "status": "PENDING",
                "batch_number": next_batch,
                "is_additional": True,
                "inventory_deducted": False,
                "added_at": added_at,
                "created_at": added_at,
            }
            order_repo.add_order_item(new_item_doc)
            added_items_summary.append({
                "menu_item_id": str(menu_item["_id"]),
                "name": menu_item["name"],
                "quantity": qty,
                "price": float(unit_price_dec),
                "item_total": float(item_tot),
                "batch_number": next_batch,
            })

        # 4. Mark order inventory_deducted: False so the new items can be deducted when prepared/delivered
        order_repo.update(order_id, {"inventory_deducted": False})

        # 5. Recalculate financial breakdown (previous items total, new items total, subtotal, taxes, total)
        updated_order = OrderItemService.recalculate_order(order_id)

        # 6. Overall order status reflects active additions (items in progress)
        new_overall_status = OrderService.calculate_order_status(order_id)
        order_repo.update(order_id, {"status": new_overall_status})

        # 7. Auto-dispatch to Kitchen Workflow
        existing_ticket = kitchen_tickets_collection.find_one({"order_id": to_object_id(order_id)})
        if existing_ticket:
            kitchen_tickets_collection.update_one(
                {"_id": existing_ticket["_id"]},
                {
                    "$set": {
                        "status": "QUEUED",
                        "priority": "NORMAL",
                        "has_additional_items": True,
                        "batch_number": next_batch,
                        "updated_at": now_utc(),
                    }
                }
            )
            audit_repo.record_kitchen_event(
                order_id=order_id,
                kitchen_ticket_id=str(existing_ticket["_id"]),
                event="ADDITIONAL_ITEMS_DISPATCHED",
                old_status=existing_ticket.get("status"),
                new_status="QUEUED",
                metadata={"batch_number": next_batch, "items": added_items_summary},
            )
        else:
            ticket = {
                "order_id": to_object_id(order_id),
                "status": "QUEUED",
                "priority": "NORMAL",
                "assigned_staff_id": None,
                "batch_number": next_batch,
                "started_at": None,
                "ready_at": None,
                "completed_at": None,
                "created_at": now_utc(),
            }
            res = kitchen_tickets_collection.insert_one(ticket)
            audit_repo.record_kitchen_event(
                order_id=order_id,
                kitchen_ticket_id=str(res.inserted_id),
                event="TICKET_CREATED_FOR_ADDITIONAL_ITEMS",
                old_status=None,
                new_status="QUEUED",
                metadata={"batch_number": next_batch, "items": added_items_summary},
            )

        # 8. Update existing invoice if already generated
        invoices_collection.update_many(
            {"order_id": to_object_id(order_id)},
            {
                "$set": {
                    "subtotal": decimal128(updated_order["subtotal"]),
                    "previous_item_total": decimal128(updated_order.get("previous_item_total", 0)),
                    "new_item_total": decimal128(updated_order.get("new_item_total", 0)),
                    "discount_amount": decimal128(updated_order.get("discount_amount", 0)),
                    "tax_amount": decimal128(updated_order.get("tax_amount", 0)),
                    "total_amount": decimal128(updated_order["total_amount"]),
                    "status": "UNPAID",  # Requires settlement for additional items
                    "updated_at": now_utc(),
                }
            }
        )

        prev_sub = updated_order.get("previous_item_total", 0)
        new_sub = updated_order.get("new_item_total", 0)
        tot_amt = updated_order.get("total_amount", 0)
        prev_sub_flt = float(prev_sub.to_decimal()) if hasattr(prev_sub, "to_decimal") else float(prev_sub or 0)
        new_sub_flt = float(new_sub.to_decimal()) if hasattr(new_sub, "to_decimal") else float(new_sub or 0)
        tot_flt = float(tot_amt.to_decimal()) if hasattr(tot_amt, "to_decimal") else float(tot_amt or 0)

        # 9. Record audit activity
        audit_repo.record_order_activity(
            order_id=order_id,
            action="ORDER_ADDITIONAL_ITEMS_ADDED",
            performed_by=performed_by,
            performed_by_role=role,
            metadata={
                "batch_number": next_batch,
                "items_added": added_items_summary,
                "previous_subtotal": prev_sub_flt,
                "additional_subtotal": new_sub_flt,
                "new_total": tot_flt,
                "added_at": added_at.isoformat(),
            },
        )

        return OrderService.get_order(order_id)

    @staticmethod
    def update_discount(order_id: str, data: Any) -> Dict[str, Any]:
        order = OrderService.get_order(order_id)
        discount_val = get_field(data, "discount_amount", data)
        discount = Decimal(str(discount_val))
        if discount < 0:
            raise ValueError("Discount amount cannot be negative")

        order_repo.update(order_id, {"discount_amount": decimal128(discount)})
        return OrderItemService.recalculate_order(order_id)

    @staticmethod
    def confirm_order(order_id: str, performed_by: str = "WAITER", role: str = "WAITER") -> Dict[str, Any]:
        """
        Confirms order:
        1. Verifies order is in DRAFT, PLACED, or PENDING status.
        2. Verifies order is not empty.
        3. Verifies sufficient stock for all recipe ingredients of ordered items (fails with all shortages if any).
        4. Does NOT deduct stock yet (deduction happens at SERVED / DELIVERED / COMPLETED).
        5. Marks table as OCCUPIED (if dine-in).
        6. Updates order status to CONFIRMED.
        7. Creates kitchen ticket and updates order to SENT_TO_KITCHEN.
        8. Logs activity in MongoDB.
        """
        order = OrderService.get_order(order_id)
        if order["status"] not in ["DRAFT", "PLACED", "PENDING"]:
            raise ValueError(f"Cannot confirm order in status {order['status']}. Only DRAFT/PLACED/PENDING orders can be confirmed.")

        items = order_repo.find_order_items(order_id)
        if not items:
            raise ValueError("Cannot confirm an empty order. Please add at least one item.")

        # Compute total required ingredients across all items with recipes
        deductions_needed: Dict[str, Dict[str, Any]] = {}

        for item in items:
            menu_item = menu_items_collection.find_one({"_id": to_object_id(item["menu_item_id"])})
            if menu_item and not menu_item.get("inventory_tracking_enabled", True):
                continue

            recipes = list(recipes_collection.find({"menu_item_id": to_object_id(item["menu_item_id"])}))
            for r in recipes:
                ing = ing_repo.find_by_id(r["ingredient_id"])
                if not ing:
                    continue

                ing_id = str(ing["id"])
                req_qty = Decimal(str(r["quantity_required"])) * Decimal(str(item["quantity"]))
                rec_unit = r.get("unit") or ing["unit"]
                converted_req = convert_quantity(req_qty, rec_unit, ing["unit"])

                if ing_id not in deductions_needed:
                    deductions_needed[ing_id] = {
                        "ingredient": ing,
                        "required_qty": Decimal("0"),
                    }
                deductions_needed[ing_id]["required_qty"] += converted_req

        # Check sufficiency for all required ingredients (report ALL shortages)
        shortages = []
        for ing_id, info in deductions_needed.items():
            ing = info["ingredient"]
            req = info["required_qty"]
            avail = Decimal(str(ing["available_quantity"]))
            if avail < req:
                shortages.append(
                    f"{ing['name']}: Required {req} {ing['unit']}, Available {avail} {ing['unit']}, Shortage {req - avail} {ing['unit']}"
                )

        if shortages:
            raise ValueError(f"Insufficient stock for: {'; '.join(shortages)}")

        # Table occupation for Dine-In
        if order.get("table_id"):
            table_repo.set_status(order["table_id"], "OCCUPIED")

        # Update status to CONFIRMED (stock deduction deferred to SERVED/DELIVERED/COMPLETED)
        order_repo.update(order_id, {"status": "CONFIRMED", "inventory_deducted": False})

        audit_repo.record_order_activity(
            order_id=order_id,
            action="ORDER_CONFIRMED",
            performed_by=performed_by,
            performed_by_role=role,
            metadata={"table_id": str(order.get("table_id")) if order.get("table_id") else None},
        )

        # Auto-create Kitchen Ticket
        existing_ticket = kitchen_tickets_collection.find_one({"order_id": to_object_id(order_id)})
        if not existing_ticket:
            ticket = {
                "order_id": to_object_id(order_id),
                "status": "QUEUED",
                "priority": "NORMAL",
                "assigned_staff_id": None,
                "started_at": None,
                "ready_at": None,
                "completed_at": None,
                "created_at": now_utc(),
            }
            res = kitchen_tickets_collection.insert_one(ticket)
            ticket["_id"] = res.inserted_id

            order_repo.update(order_id, {"status": "SENT_TO_KITCHEN"})

            audit_repo.record_order_activity(
                order_id=order_id,
                action="ORDER_SENT_TO_KITCHEN",
                performed_by=performed_by,
                performed_by_role=role,
                metadata={"kitchen_ticket_id": str(ticket["_id"])},
            )

        return OrderService.get_order(order_id)

    @staticmethod
    def deduct_order_inventory(order_id: str, performed_by: str = "SYSTEM", order_items: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Deducts raw material stock for all recipe-configured menu items in an order
        that have NOT yet had their inventory deducted.
        Guaranteed idempotency: Checks each item's 'inventory_deducted' flag.
        Starters and items without recipes do not consume inventory stock.
        Never allows negative inventory: validates all ingredients before deduction.
        If any ingredient is insufficient, raises ValueError listing ALL shortages.
        Atomically records StockMovement for each ingredient and sets inventory_deducted: True.
        """
        order = OrderService.get_order(order_id)
        if order.get("inventory_deducted", False):
            return {
                "status": "SKIPPED",
                "order_id": order_id,
                "message": "Inventory already deducted for this order",
            }

        items = order_items or order_repo.find_order_items(order_id)
        if not items:
            order_repo.update(order_id, {"inventory_deducted": True})
            return {"status": "SKIPPED", "order_id": order_id, "message": "No items in order"}

        # Filter only items that have not yet had their inventory deducted
        items_to_deduct = [it for it in items if not it.get("inventory_deducted", False)]
        if not items_to_deduct:
            order_repo.update(order_id, {"inventory_deducted": True})
            return {
                "status": "SKIPPED",
                "order_id": order_id,
                "message": "Inventory already deducted for this order",
            }

        deductions_needed: Dict[str, Dict[str, Any]] = {}
        items_with_recipes = []

        for item in items_to_deduct:
            menu_item = menu_items_collection.find_one({"_id": to_object_id(item["menu_item_id"])})
            if menu_item and not menu_item.get("inventory_tracking_enabled", True):
                if "id" in item:
                    order_repo.update_order_item(item["id"], {"inventory_deducted": True})
                continue

            recipes = list(recipes_collection.find({"menu_item_id": to_object_id(item["menu_item_id"])}))
            # Items without recipes (like Starters) do NOT deduct main inventory
            if not recipes:
                if "id" in item:
                    order_repo.update_order_item(item["id"], {"inventory_deducted": True})
                continue

            items_with_recipes.append(item)
            for r in recipes:
                ing = ing_repo.find_by_id(r["ingredient_id"])
                if not ing:
                    continue

                ing_id = str(ing["id"])
                req_qty = Decimal(str(r["quantity_required"])) * Decimal(str(item["quantity"]))
                rec_unit = r.get("unit") or ing["unit"]
                converted_req = convert_quantity(req_qty, rec_unit, ing["unit"])

                if ing_id not in deductions_needed:
                    avail = ing.get("available_quantity") or ing.get("current_stock") or Decimal("0")
                    avail_dec = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail))
                    deductions_needed[ing_id] = {
                        "ingredient": ing,
                        "available_qty": avail_dec,
                        "required_qty": Decimal("0"),
                    }
                deductions_needed[ing_id]["required_qty"] += converted_req

        if not deductions_needed:
            # Order contains only items without inventory recipes (e.g. only Starters)
            for it in items_to_deduct:
                if "id" in it:
                    order_repo.update_order_item(it["id"], {"inventory_deducted": True})
            order_repo.update(order_id, {"inventory_deducted": True})
            return {
                "status": "SKIPPED",
                "sub_status": "NO_INVENTORY_ITEMS",
                "order_id": order_id,
                "message": "Order contains only items without tracked recipes",
            }

        # Step 1: Validate stock for all required ingredients
        shortages = []
        for ing_id, info in deductions_needed.items():
            ing = info["ingredient"]
            avail = info["available_qty"]
            req = info["required_qty"]
            if avail < req:
                shortage_qty = req - avail
                shortages.append(
                    f"{ing['name']}: Required {req} {ing['unit']}, Available {avail} {ing['unit']}, Shortage {shortage_qty} {ing['unit']}"
                )

        if shortages:
            raise ValueError(f"Insufficient stock for: {'; '.join(shortages)}")

        # Step 2: Atomic stock deduction and stock movement logging via FEFO
        deduction_summary = []
        for ing_id, info in deductions_needed.items():
            ing = info["ingredient"]
            req = info["required_qty"]
            avail_before = info["available_qty"]

            # FEFO Batch deduction
            batches = batch_repo.find_active_batches_fefo(ing_id)
            rem_to_deduct = req
            allocated_batch_id = None
            for b in batches:
                b_rem = b["remaining_quantity"].to_decimal() if hasattr(b["remaining_quantity"], "to_decimal") else Decimal(str(b["remaining_quantity"]))
                if b_rem <= 0:
                    continue
                alloc = min(b_rem, rem_to_deduct)
                batch_repo.decrement_batch(b["id"], alloc)
                allocated_batch_id = to_object_id(b["id"])
                rem_to_deduct -= alloc
                if rem_to_deduct <= 0:
                    break

            ing_repo.increment_stock(ing_id, -req)

            cost_per_unit = Decimal(str(ing.get("cost_per_unit") or 0))
            ing_repo.record_movement({
                "ingredient_id": to_object_id(ing_id),
                "batch_id": allocated_batch_id,
                "movement_type": "ORDER_DEDUCTION",
                "quantity": decimal128(req),
                "unit": ing["unit"],
                "previous_stock": decimal128(avail_before),
                "new_stock": decimal128(avail_before - req),
                "unit_cost": decimal128(cost_per_unit),
                "total_cost": decimal128(req * cost_per_unit),
                "reference_type": "ORDER",
                "reference_id": order["order_number"],
                "reason": f"Order {order.get('order_number', order_id)} preparation consumption",
                "created_by": performed_by,
                "created_at": now_utc(),
            })
            deduction_summary.append({
                "ingredient_id": ing_id,
                "ingredient_name": ing["name"],
                "deducted_quantity": float(req),
                "unit": ing["unit"],
            })

        for it in items_with_recipes:
            if "id" in it:
                order_repo.update_order_item(it["id"], {"inventory_deducted": True})

        order_repo.update(order_id, {"inventory_deducted": True})

        audit_repo.record_order_activity(
            order_id=order_id,
            action="INVENTORY_DEDUCTED",
            performed_by=performed_by,
            performed_by_role="SYSTEM",
            metadata={"deductions": deduction_summary},
        )

        return {
            "status": "DEDUCTED",
            "order_id": order_id,
            "deductions": deduction_summary,
        }

    @staticmethod
    def complete_order(order_id: str, performed_by: str = "SYSTEM", role: str = "SYSTEM") -> Dict[str, Any]:
        """
        Marks an order as COMPLETED, deducting inventory if not already done,
        and releasing the dining table if assigned.
        """
        order = OrderService.get_order(order_id)
        if order["status"] == "COMPLETED":
            return order

        # Transition status to COMPLETED (triggers deduct_order_inventory via update_status)
        OrderService.update_status(order_id, "COMPLETED", performed_by=performed_by, role=role)

        # Release table if assigned
        if order.get("table_id"):
            table_repo.set_status(order["table_id"], "AVAILABLE")

        return OrderService.get_order(order_id)

    @staticmethod
    def cancel_order(order_id: str, reason: Optional[str] = None, role: str = "CUSTOMER", performed_by: str = "SYSTEM") -> Dict[str, Any]:
        """
        Cancels order following role & status policy:
        - If inventory was deducted (served/completed), returns ingredients with ORDER_RETURN movement.
        - If inventory was not deducted, no stock return needed.
        """
        order = OrderService.get_order(order_id)
        current_status = order["status"]

        order_entity = OrderEntity(
            order_type=order["order_type"],
            customer_id=str(order.get("customer_id")) if order.get("customer_id") else None,
            table_id=str(order.get("table_id")) if order.get("table_id") else None,
            order_number=order["order_number"],
            order_id=str(order["id"]),
        )
        order_entity.status = current_status

        can_cancel, policy_msg = order_entity.can_cancel(role=role)
        if not can_cancel:
            raise ValueError(policy_msg)

        # Inventory return logic
        if order.get("inventory_deducted") is True:
            items = order_repo.find_order_items(order_id)
            for item in items:
                recipes = list(recipes_collection.find({"menu_item_id": to_object_id(item["menu_item_id"])}))
                for r in recipes:
                    ing = ing_repo.find_by_id(r["ingredient_id"])
                    if not ing:
                        continue
                    req_qty = Decimal(str(r["quantity_required"])) * Decimal(str(item["quantity"]))
                    rec_unit = r.get("unit") or ing["unit"]
                    converted_req = convert_quantity(req_qty, rec_unit, ing["unit"])

                    ing_repo.increment_stock(ing["id"], converted_req)
                    ing_repo.record_movement({
                        "ingredient_id": to_object_id(ing["id"]),
                        "movement_type": "ORDER_RETURN",
                        "quantity": decimal128(converted_req),
                        "unit": ing["unit"],
                        "reference_type": "ORDER_CANCELLATION",
                        "reference_id": order["order_number"],
                        "created_by": performed_by,
                        "created_at": now_utc(),
                    })
            order_repo.update(order_id, {"inventory_deducted": False})

        # Cancel kitchen ticket if active
        kitchen_tickets_collection.update_one(
            {"order_id": to_object_id(order_id), "status": {"$in": ["QUEUED", "ACCEPTED", "PREPARING"]}},
            {"$set": {"status": "CANCELLED"}},
        )

        # Release table if assigned and no other active orders on table
        if order.get("table_id"):
            active = order_repo.find_active_by_table(order["table_id"])
            if not active or all(str(a["id"]) == str(order_id) for a in active):
                table_repo.set_status(order["table_id"], "AVAILABLE")

        order_repo.update(order_id, {"status": "CANCELLED", "cancellation_reason": reason})

        audit_repo.record_order_activity(
            order_id=order_id,
            action="ORDER_CANCELLED",
            performed_by=performed_by,
            performed_by_role=role,
            metadata={"reason": reason, "previous_status": current_status},
        )

        return OrderService.get_order(order_id)


class OrderItemService:

    @staticmethod
    def add_item(order_id: str, data: Any) -> Dict[str, Any]:
        order = order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        # If order is already past DRAFT (e.g. DELIVERED, SERVED, CONFIRMED, PREPARING, READY),
        # add the item via the additional items workflow to maintain round tracking, billing, & KDS
        if order["status"] != "DRAFT":
            if order["status"] in ["CANCELLED", "REFUNDED"]:
                raise ValueError(f"Cannot add items to {order['status']} order")
            res = OrderService.add_additional_items(order_id, [data])
            # Return the newly created item
            items = order_repo.find_order_items(order_id)
            return items[-1] if items else res

        menu_item_id = get_field(data, "menu_item_id")
        quantity = int(get_field(data, "quantity", 0))
        special_instructions = get_field(data, "special_instructions")

        if quantity <= 0:
            raise ValueError("Order item quantity must be greater than zero")

        menu_item = menu_items_collection.find_one({"_id": to_object_id(menu_item_id)})
        if not menu_item:
            raise ValueError("Menu item not found")

        if not menu_item["is_available"]:
            raise ValueError("Menu item is not available")

        unit_price = menu_item["price"]
        unit_price_dec = unit_price.to_decimal() if isinstance(unit_price, Decimal128) else Decimal(str(unit_price))

        # Use Domain Entity for item total calculation
        entity = OrderItemEntity(
            menu_item_id=str(menu_item["_id"]),
            item_name_snapshot=menu_item["name"],
            unit_price_snapshot=unit_price_dec,
            quantity=quantity,
            special_instructions=special_instructions,
        )

        item_doc = {
            "order_id": to_object_id(order_id),
            "menu_item_id": menu_item["_id"],
            "item_name_snapshot": entity.item_name_snapshot,
            "unit_price_snapshot": decimal128(entity.unit_price_snapshot),
            "price_at_addition": decimal128(entity.unit_price_snapshot),
            "quantity": entity.quantity,
            "special_instructions": entity.special_instructions,
            "item_total": decimal128(entity.item_total),
            "status": "PENDING",
            "batch_number": 1,
            "is_additional": False,
            "inventory_deducted": False,
            "added_at": now_utc(),
            "created_at": now_utc(),
        }

        created = order_repo.add_order_item(item_doc)
        OrderItemService.recalculate_order(order_id)

        return created

    @staticmethod
    def update_item(order_id: str, item_id: str, data: Any) -> Dict[str, Any]:
        order = order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        if order["status"] != "DRAFT":
            raise ValueError("Items can only be updated in DRAFT orders")

        item = order_repo.find_order_item(item_id)
        if not item or str(item["order_id"]) != str(order_id):
            raise ValueError("Order item not found")

        update_dict: Dict[str, Any] = {}
        qty = get_field(data, "quantity")
        if qty is not None:
            new_qty = int(qty)
            if new_qty <= 0:
                raise ValueError("Order item quantity must be greater than zero")
            unit_price = item["unit_price_snapshot"]
            unit_price_dec = unit_price.to_decimal() if isinstance(unit_price, Decimal128) else Decimal(str(unit_price))
            update_dict["quantity"] = new_qty
            update_dict["item_total"] = decimal128(unit_price_dec * Decimal(new_qty))

        specs = get_field(data, "special_instructions")
        if specs is not None:
            update_dict["special_instructions"] = specs

        updated = order_repo.update_order_item(item_id, update_dict)
        OrderItemService.recalculate_order(order_id)
        return updated

    @staticmethod
    def delete_item(order_id: str, item_id: str) -> Dict[str, Any]:
        order = order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        if order["status"] != "DRAFT":
            raise ValueError("Items can only be deleted from DRAFT orders")

        item = order_repo.find_order_item(item_id)
        if not item or str(item["order_id"]) != str(order_id):
            raise ValueError("Order item not found")

        order_repo.delete_order_item(item_id)
        OrderItemService.recalculate_order(order_id)
        return {"message": "Order item deleted successfully"}

    @staticmethod
    def get_order_items(order_id: str) -> List[Dict[str, Any]]:
        return order_repo.find_order_items(order_id)

    @staticmethod
    def recalculate_order(order_id: str) -> Dict[str, Any]:
        items = order_repo.find_order_items(order_id)
        order = order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        previous_subtotal = Decimal("0")
        new_subtotal = Decimal("0")
        subtotal = Decimal("0")

        for it in items:
            p = it.get("unit_price_snapshot") or it.get("price") or 0
            p_dec = p.to_decimal() if isinstance(p, Decimal128) else Decimal(str(p))
            it_qty = Decimal(str(it.get("quantity", 1)))
            line_tot = p_dec * it_qty
            subtotal += line_tot

            if it.get("is_additional") or it.get("batch_number", 1) > 1:
                new_subtotal += line_tot
            else:
                previous_subtotal += line_tot

        discount_raw = order.get("discount_amount", 0)
        discount = discount_raw.to_decimal() if isinstance(discount_raw, Decimal128) else Decimal(str(discount_raw))
        discount = min(subtotal, max(Decimal("0"), discount))

        taxable = max(Decimal("0"), subtotal - discount)
        tax = (taxable * Decimal("0.05")).quantize(Decimal("0.01"))
        total = (taxable + tax).quantize(Decimal("0.01"))

        order_repo.update(order_id, {
            "subtotal": decimal128(subtotal),
            "previous_item_total": decimal128(previous_subtotal),
            "new_item_total": decimal128(new_subtotal),
            "discount_amount": decimal128(discount),
            "tax_amount": decimal128(tax),
            "total_amount": decimal128(total),
        })

        # Keep any existing invoice in sync
        invoices_collection.update_many(
            {"order_id": to_object_id(order_id)},
            {
                "$set": {
                    "subtotal": decimal128(subtotal),
                    "previous_item_total": decimal128(previous_subtotal),
                    "new_item_total": decimal128(new_subtotal),
                    "discount_amount": decimal128(discount),
                    "tax_amount": decimal128(tax),
                    "total_amount": decimal128(total),
                }
            }
        )

        return order_repo.find_by_id(order_id)
