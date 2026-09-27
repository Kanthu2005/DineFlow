"""
Kitchen Operations Service.
Manages Kitchen Tickets, preparation workflow, staff assignments, workload limits,
delayed order detection, and preparation time estimation.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId

from app.database.mongodb import (
    kitchen_tickets_collection,
    kitchen_ticket_items_collection,
    staff_assignments_collection,
    orders_collection,
    order_items_collection,
    menu_items_collection,
    users_collection,
)
from app.repositories.kitchen_repository import KitchenRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.models.entities import KitchenTicket as TicketEntity
from app.services.common import (
    now_utc,
    to_object_id,
    serialize_document,
    serialize_documents,
)

kitchen_repo = KitchenRepository()
order_repo = OrderRepository()
audit_repo = AuditLogRepository()

VALID_STATIONS = ["GRILL", "MAIN_COURSE", "STARTERS", "BEVERAGES", "DESSERTS", "PACKING"]


class KitchenService:

    @staticmethod
    def create_ticket(order_id: str, priority: str = "NORMAL") -> Dict[str, Any]:
        order = order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        if order["status"] not in ["CONFIRMED", "SENT_TO_KITCHEN"]:
            raise ValueError(f"Only confirmed orders can go to kitchen. Current status: {order['status']}")

        existing = kitchen_repo.find_by_order_id(order_id)
        if existing:
            raise ValueError("Kitchen ticket already exists for this order")

        priority_upper = priority.upper()
        if priority_upper not in ["NORMAL", "HIGH", "URGENT"]:
            priority_upper = "NORMAL"

        ticket_doc = {
            "order_id": to_object_id(order_id),
            "status": "QUEUED",
            "priority": priority_upper,
            "assigned_staff_id": None,
            "started_at": None,
            "ready_at": None,
            "completed_at": None,
            "created_at": now_utc(),
        }

        created = kitchen_repo.insert(ticket_doc)

        order_repo.update(order_id, {"status": "SENT_TO_KITCHEN"})

        audit_repo.record_kitchen_event(
            order_id=order_id,
            kitchen_ticket_id=created["id"],
            event="TICKET_CREATED",
            old_status=None,
            new_status="QUEUED",
            metadata={"priority": priority_upper},
        )

        return created

    @staticmethod
    def get_ticket(ticket_id: str) -> Dict[str, Any]:
        ticket = kitchen_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError("Kitchen ticket not found")

        # Enrich with order and order items
        if ticket.get("order_id"):
            order = order_repo.find_by_id(ticket["order_id"])
            if order:
                ticket["order_number"] = order.get("order_number")
                ticket["order_type"] = order.get("order_type")
                ticket["table_id"] = str(order.get("table_id")) if order.get("table_id") else None
                items = order_repo.find_order_items(order["id"])
                ticket["items"] = items

        return ticket

    @staticmethod
    def get_tickets(status: Optional[str] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        tickets = kitchen_repo.find_tickets(status=status, priority=priority)
        enriched = []
        for t in tickets:
            if t.get("order_id"):
                order = orders_collection.find_one({"_id": to_object_id(t["order_id"])})
                if order:
                    t["order_number"] = order.get("order_number")
                    t["order_type"] = order.get("order_type")
                    t["table_id"] = str(order.get("table_id")) if order.get("table_id") else None
                    items = list(order_items_collection.find({"order_id": order["_id"]}))
                    t["order_items"] = serialize_documents(items)
            enriched.append(t)
        return enriched

    @staticmethod
    def accept_ticket(ticket_id: str, staff_id: Optional[str] = None) -> Dict[str, Any]:
        ticket = kitchen_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError("Kitchen ticket not found")

        if ticket["status"] == "CANCELLED":
            raise ValueError("A cancelled order cannot begin preparation")

        old_status = ticket["status"]
        update_data: Dict[str, Any] = {"status": "ACCEPTED"}
        if staff_id:
            update_data["assigned_staff_id"] = staff_id

        kitchen_repo.update(ticket_id, update_data)

        audit_repo.record_kitchen_event(
            order_id=ticket["order_id"],
            kitchen_ticket_id=ticket_id,
            event="STATUS_CHANGED",
            old_status=old_status,
            new_status="ACCEPTED",
            staff_id=staff_id,
        )

        return KitchenService.get_ticket(ticket_id)

    @staticmethod
    def start_preparation(ticket_id: str, staff_id: Optional[str] = None) -> Dict[str, Any]:
        ticket = kitchen_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError("Kitchen ticket not found")

        if ticket["status"] == "CANCELLED":
            raise ValueError("A cancelled order cannot begin preparation")

        old_status = ticket["status"]
        now = now_utc()
        update_data: Dict[str, Any] = {
            "status": "PREPARING",
            "started_at": now,
        }
        if staff_id:
            update_data["assigned_staff_id"] = staff_id

        kitchen_repo.update(ticket_id, update_data)

        # Update parent order
        order_repo.update(ticket["order_id"], {"status": "PREPARING"})

        audit_repo.record_kitchen_event(
            order_id=ticket["order_id"],
            kitchen_ticket_id=ticket_id,
            event="STATUS_CHANGED",
            old_status=old_status,
            new_status="PREPARING",
            staff_id=staff_id,
        )

        return KitchenService.get_ticket(ticket_id)

    @staticmethod
    def mark_ready(ticket_id: str) -> Dict[str, Any]:
        ticket = kitchen_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError("Kitchen ticket not found")

        if ticket["status"] == "CANCELLED":
            raise ValueError("Cannot mark cancelled ticket as ready")

        old_status = ticket["status"]
        now = now_utc()
        kitchen_repo.update(ticket_id, {
            "status": "READY",
            "ready_at": now,
        })

        order_repo.update(ticket["order_id"], {"status": "READY"})

        audit_repo.record_kitchen_event(
            order_id=ticket["order_id"],
            kitchen_ticket_id=ticket_id,
            event="STATUS_CHANGED",
            old_status=old_status,
            new_status="READY",
            staff_id=ticket.get("assigned_staff_id"),
        )

        return KitchenService.get_ticket(ticket_id)

    @staticmethod
    def handover(ticket_id: str) -> Dict[str, Any]:
        ticket = kitchen_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError("Kitchen ticket not found")

        old_status = ticket["status"]
        now = now_utc()
        kitchen_repo.update(ticket_id, {
            "status": "HANDED_OVER",
            "completed_at": now,
        })

        order_repo.update(ticket["order_id"], {"status": "SERVED"})

        audit_repo.record_kitchen_event(
            order_id=ticket["order_id"],
            kitchen_ticket_id=ticket_id,
            event="STATUS_CHANGED",
            old_status=old_status,
            new_status="HANDED_OVER",
            staff_id=ticket.get("assigned_staff_id"),
        )

        return KitchenService.get_ticket(ticket_id)

    @staticmethod
    def update_ticket_status(ticket_id: str, new_status: str, staff_id: Optional[str] = None, user_role: str = "CHEF") -> Dict[str, Any]:
        status_upper = new_status.upper()
        if status_upper not in TicketEntity.VALID_STATUSES:
            raise ValueError(f"Invalid kitchen ticket status: {status_upper}")

        ticket = kitchen_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError("Kitchen ticket not found")

        # Business Rule: A completed ticket cannot return to preparing without manager permission
        if ticket["status"] in ["READY", "HANDED_OVER"] and status_upper in ["PREPARING", "QUEUED"]:
            if user_role.upper() not in ["ADMIN", "MANAGER"]:
                raise ValueError("A completed kitchen ticket cannot return to preparing without manager permission")

        if status_upper == "ACCEPTED":
            return KitchenService.accept_ticket(ticket_id, staff_id)
        elif status_upper == "PREPARING":
            return KitchenService.start_preparation(ticket_id, staff_id)
        elif status_upper == "READY":
            return KitchenService.mark_ready(ticket_id)
        elif status_upper == "HANDED_OVER":
            return KitchenService.handover(ticket_id)
        else:
            old_status = ticket["status"]
            kitchen_repo.update(ticket_id, {"status": status_upper})
            audit_repo.record_kitchen_event(
                order_id=ticket["order_id"],
                kitchen_ticket_id=ticket_id,
                event="STATUS_CHANGED",
                old_status=old_status,
                new_status=status_upper,
                staff_id=staff_id,
            )
            return KitchenService.get_ticket(ticket_id)

    @staticmethod
    def assign_staff(ticket_id: str, staff_id: str, station: Optional[str] = None) -> Dict[str, Any]:
        ticket = kitchen_repo.find_by_id(ticket_id)
        if not ticket:
            raise ValueError("Kitchen ticket not found")

        # Verify staff exists and is active
        staff = users_collection.find_one({"_id": to_object_id(staff_id)})
        if not staff:
            raise ValueError("Staff member not found")
        if not staff.get("is_active", True):
            raise ValueError("Cannot assign order to inactive staff member")

        # Workload limit check: Maximum active orders (default 5)
        max_orders = staff.get("maximum_active_orders", 5)
        current_active = kitchen_repo.count_active_orders_by_staff(staff_id)
        if current_active >= max_orders:
            raise ValueError(
                f"Staff member '{staff['name']}' has reached the maximum workload limit ({max_orders} active orders)"
            )

        # Update ticket
        kitchen_repo.update(ticket_id, {
            "assigned_staff_id": staff_id,
            "station": station,
        })

        # Record assignment history
        kitchen_repo.record_staff_assignment(ticket_id, staff_id, station)

        audit_repo.record_kitchen_event(
            order_id=ticket["order_id"],
            kitchen_ticket_id=ticket_id,
            event="STAFF_ASSIGNED",
            staff_id=staff_id,
            metadata={"station": station},
        )

        return KitchenService.get_ticket(ticket_id)

    @staticmethod
    def estimate_preparation_time(order_id: str) -> Dict[str, Any]:
        """
        Calculates estimated preparation duration:
        Estimated preparation time = Maximum item preparation time + Current kitchen queue delay
        """
        order = order_repo.find_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        items = order_repo.find_order_items(order_id)
        max_item_prep = 0
        for it in items:
            menu_item = menu_items_collection.find_one({"_id": to_object_id(it["menu_item_id"])})
            if menu_item and menu_item.get("preparation_time"):
                if menu_item["preparation_time"] > max_item_prep:
                    max_item_prep = menu_item["preparation_time"]

        if max_item_prep == 0:
            max_item_prep = 15  # Default baseline prep time in minutes

        # Kitchen queue delay: count of orders in QUEUED or PREPARING
        queued_count = kitchen_tickets_collection.count_documents({"status": "QUEUED"})
        preparing_count = kitchen_tickets_collection.count_documents({"status": "PREPARING"})
        queue_delay = (queued_count * 5) + (preparing_count * 2)

        total_estimated_minutes = max_item_prep + queue_delay

        ready_time = datetime.now(timezone.utc) + timedelta(minutes=total_estimated_minutes)
        ready_time_str = ready_time.strftime("%H:%M")

        return {
            "order_id": order_id,
            "order_number": order.get("order_number"),
            "max_item_prep_minutes": max_item_prep,
            "queue_delay_minutes": queue_delay,
            "estimated_minutes": total_estimated_minutes,
            "estimated_ready_time": ready_time_str,
            "calculation_basis": f"Queue delay ({queue_delay} mins) + max item prep time ({max_item_prep} mins)",
        }

    @staticmethod
    def get_delayed_orders(threshold_minutes: int = 30) -> List[Dict[str, Any]]:
        """
        Returns kitchen tickets in QUEUED or PREPARING waiting longer than threshold_minutes.
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=threshold_minutes)

        tickets = list(kitchen_tickets_collection.find({
            "status": {"$in": ["QUEUED", "PREPARING"]},
            "created_at": {"$lt": cutoff},
        }).sort("created_at", 1))

        results = []
        for t in tickets:
            item = serialize_document(t)
            created_at = t.get("created_at")
            if created_at:
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                waiting_mins = int((now - created_at).total_seconds() // 60)
                item["waiting_minutes"] = waiting_mins
            results.append(item)
        return results

    @staticmethod
    def get_workload() -> Dict[str, Any]:
        """
        Returns active workload summary for kitchen manager dashboard.
        """
        queued = kitchen_tickets_collection.count_documents({"status": "QUEUED"})
        accepted = kitchen_tickets_collection.count_documents({"status": "ACCEPTED"})
        preparing = kitchen_tickets_collection.count_documents({"status": "PREPARING"})
        ready = kitchen_tickets_collection.count_documents({"status": "READY"})

        # Active staff workload
        pipeline = [
            {"$match": {"status": {"$in": ["ACCEPTED", "PREPARING"]}, "assigned_staff_id": {"$ne": None}}},
            {"$group": {"_id": "$assigned_staff_id", "active_orders": {"$sum": 1}}},
        ]
        staff_counts = list(kitchen_tickets_collection.aggregate(pipeline))

        staff_summary = []
        for sc in staff_counts:
            staff_user = users_collection.find_one({"_id": to_object_id(sc["_id"])})
            staff_summary.append({
                "staff_id": str(sc["_id"]),
                "staff_name": staff_user["name"] if staff_user else "Unknown",
                "active_orders": sc["active_orders"],
                "maximum_orders": staff_user.get("maximum_active_orders", 5) if staff_user else 5,
            })

        return {
            "total_active_orders": queued + accepted + preparing,
            "queued_orders": queued,
            "accepted_orders": accepted,
            "preparing_orders": preparing,
            "ready_orders": ready,
            "staff_workload": staff_summary,
        }
