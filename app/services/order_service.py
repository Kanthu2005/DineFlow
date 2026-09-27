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
)
from app.repositories.order_repository import OrderRepository
from app.repositories.inventory_repository import IngredientRepository
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

        if table_id:
            table = restaurant_tables_collection.find_one({"_id": to_object_id(table_id)})
            if not table:
                raise ValueError("Table not found")
            if not table["is_active"]:
                raise ValueError("Table is out of service")
            if table["status"] == "OCCUPIED":
                raise ValueError(f"Table {table['table_number']} is already occupied")

        order_number = generate_number("ORD")

        doc = {
            "order_number": order_number,
            "customer_id": to_object_id(customer_id) if customer_id else None,
            "table_id": to_object_id(table_id) if table_id else None,
            "order_type": order_type,
            "status": "DRAFT",
            "subtotal": Decimal128("0"),
            "tax_amount": Decimal128("0"),
            "discount_amount": Decimal128("0"),
            "total_amount": Decimal128("0"),
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

        return created

    @staticmethod
    def get_orders(status: Optional[str] = None, order_type: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {}
        if status:
            query["status"] = status.upper()
        if order_type:
            query["order_type"] = order_type.upper()
        return order_repo.find_all(query=query, sort_field="created_at", sort_dir=-1)

    @staticmethod
    def get_order(order_id: str) -> Dict[str, Any]:
        order = order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        # Attach order items
        items = order_repo.find_order_items(order_id)
        order["items"] = items
        return order

    @staticmethod
    def get_order_by_number(order_number: str) -> Dict[str, Any]:
        order = order_repo.find_by_number(order_number)
        if not order:
            raise ValueError("Order not found")
        items = order_repo.find_order_items(order["id"])
        order["items"] = items
        return order

    @staticmethod
    def update_status(order_id: str, new_status: str, performed_by: str = "SYSTEM", role: str = "SYSTEM") -> Dict[str, Any]:
        status_upper = new_status.upper()
        if status_upper not in OrderEntity.VALID_STATUSES:
            raise ValueError(f"Invalid order status: {status_upper}")

        order = OrderService.get_order(order_id)
        old_status = order["status"]

        # Invariant checks
        if old_status in ["COMPLETED", "CANCELLED", "REFUNDED"]:
            raise ValueError(f"Cannot transition order from finalized status {old_status}")

        order_repo.update(order_id, {"status": status_upper})

        audit_repo.record_order_activity(
            order_id=order_id,
            action=f"STATUS_CHANGED_TO_{status_upper}",
            performed_by=performed_by,
            performed_by_role=role,
            metadata={"old_status": old_status, "new_status": status_upper},
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
        1. Verifies order is in DRAFT or PLACED status.
        2. Verifies order is not empty.
        3. Verifies sufficient stock for all recipe ingredients of ordered items.
        4. Atomically deducts ingredients from stock and logs ORDER_DEDUCTION movements.
        5. Marks table as OCCUPIED (if dine-in).
        6. Updates order status to CONFIRMED.
        7. Creates kitchen ticket and updates order to SENT_TO_KITCHEN.
        8. Logs activity in MongoDB.
        """
        order = OrderService.get_order(order_id)
        if order["status"] not in ["DRAFT", "PLACED"]:
            raise ValueError(f"Cannot confirm order in status {order['status']}. Only DRAFT/PLACED orders can be confirmed.")

        items = order_repo.find_order_items(order_id)
        if not items:
            raise ValueError("Cannot confirm an empty order. Please add at least one item.")

        # Step 3: Compute total required ingredients across all items
        deductions_needed: Dict[str, Dict[str, Any]] = {}

        for item in items:
            recipes = list(recipes_collection.find({"menu_item_id": to_object_id(item["menu_item_id"])}))
            for r in recipes:
                ing = ing_repo.find_by_id(r["ingredient_id"])
                if not ing:
                    continue

                ing_id = str(ing["id"])
                req_qty = Decimal(str(r["quantity_required"])) * Decimal(item["quantity"])
                rec_unit = r.get("unit") or ing["unit"]
                converted_req = convert_quantity(req_qty, rec_unit, ing["unit"])

                if ing_id not in deductions_needed:
                    deductions_needed[ing_id] = {
                        "ingredient": ing,
                        "required_qty": Decimal("0"),
                    }
                deductions_needed[ing_id]["required_qty"] += converted_req

        # Check sufficiency for all required ingredients
        for ing_id, info in deductions_needed.items():
            ing = info["ingredient"]
            req = info["required_qty"]
            avail = Decimal(str(ing["available_quantity"]))
            if avail < req:
                raise ValueError(
                    f"Insufficient stock for ingredient '{ing['name']}'. Available: {avail} {ing['unit']}, Required: {req} {ing['unit']}"
                )

        # Step 4: Deduct stock atomically and record movements
        for ing_id, info in deductions_needed.items():
            ing = info["ingredient"]
            req = info["required_qty"]
            ing_repo.increment_stock(ing_id, -req)

            ing_repo.record_movement({
                "ingredient_id": to_object_id(ing_id),
                "movement_type": "ORDER_DEDUCTION",
                "quantity": decimal128(req),
                "reference_type": "ORDER",
                "reference_id": order["order_number"],
                "created_by": performed_by,
                "created_at": now_utc(),
            })

        # Step 5: Table occupation for Dine-In
        if order.get("table_id"):
            table_repo.set_status(order["table_id"], "OCCUPIED")

        # Step 6: Update status to CONFIRMED
        order_repo.update(order_id, {"status": "CONFIRMED"})

        audit_repo.record_order_activity(
            order_id=order_id,
            action="ORDER_CONFIRMED",
            performed_by=performed_by,
            performed_by_role=role,
            metadata={"table_id": str(order.get("table_id")) if order.get("table_id") else None},
        )

        # Step 7: Auto-create Kitchen Ticket
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
    def cancel_order(order_id: str, reason: Optional[str] = None, role: str = "CUSTOMER", performed_by: str = "SYSTEM") -> Dict[str, Any]:
        """
        Cancels order following role & status policy:
        - DRAFT / PLACED: Allowed, no inventory used yet.
        - CONFIRMED / SENT_TO_KITCHEN: Allowed, return ingredients to stock (RETURN).
        - PREPARING: Allowed ONLY with manager/admin approval. Ingredients NOT returned (already cooked/used).
        - READY: Restricted without manager override.
        - SERVED / COMPLETED: Disallowed directly (must request refund).
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

        # Inventory reversal logic
        # Return ingredients ONLY if order was confirmed/sent to kitchen, BUT NOT yet preparing
        if current_status in ["CONFIRMED", "SENT_TO_KITCHEN"]:
            items = order_repo.find_order_items(order_id)
            for item in items:
                recipes = list(recipes_collection.find({"menu_item_id": to_object_id(item["menu_item_id"])}))
                for r in recipes:
                    ing = ing_repo.find_by_id(r["ingredient_id"])
                    if not ing:
                        continue
                    req_qty = Decimal(str(r["quantity_required"])) * Decimal(item["quantity"])
                    rec_unit = r.get("unit") or ing["unit"]
                    converted_req = convert_quantity(req_qty, rec_unit, ing["unit"])

                    ing_repo.increment_stock(ing["id"], converted_req)
                    ing_repo.record_movement({
                        "ingredient_id": to_object_id(ing["id"]),
                        "movement_type": "RETURN",
                        "quantity": decimal128(converted_req),
                        "reference_type": "ORDER_CANCELLATION",
                        "reference_id": order["order_number"],
                        "created_by": performed_by,
                        "created_at": now_utc(),
                    })

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

        if order["status"] != "DRAFT":
            raise ValueError("Items can only be added to DRAFT orders")

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
            "quantity": entity.quantity,
            "special_instructions": entity.special_instructions,
            "item_total": decimal128(entity.item_total),
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

        subtotal = Decimal("0")
        for it in items:
            p = it["unit_price_snapshot"]
            p_dec = p.to_decimal() if isinstance(p, Decimal128) else Decimal(str(p))
            subtotal += p_dec * Decimal(it["quantity"])

        # Documented 5% tax policy
        tax = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))

        discount_raw = order.get("discount_amount", 0)
        discount = discount_raw.to_decimal() if isinstance(discount_raw, Decimal128) else Decimal(str(discount_raw))

        total = max(Decimal("0"), (subtotal - discount + tax).quantize(Decimal("0.01")))

        order_repo.update(order_id, {
            "subtotal": decimal128(subtotal),
            "tax_amount": decimal128(tax),
            "total_amount": decimal128(total),
        })

        return order_repo.find_by_id(order_id)
