"""
Kitchen Repository for Kitchen Tickets, Ticket Items, and Staff Assignments.
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.database.mongodb import (
    kitchen_tickets_collection,
    kitchen_ticket_items_collection,
    staff_assignments_collection,
    users_collection,
)
from app.repositories.base_repository import BaseRepository
from app.utils.mongo_utils import to_object_id, serialize_document, serialize_documents, now_utc


class KitchenRepository(BaseRepository):
    def __init__(self):
        super().__init__(kitchen_tickets_collection)
        self.ticket_items_col = kitchen_ticket_items_collection
        self.assignments_col = staff_assignments_collection
        self.users_col = users_collection

    def find_by_order_id(self, order_id: str | ObjectId) -> Optional[Dict[str, Any]]:
        oid = to_object_id(order_id)
        doc = self.collection.find_one({"order_id": oid})
        return serialize_document(doc) if doc else None

    def find_tickets(self, status: Optional[str] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
        query = {}
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        docs = self.collection.find(query).sort("_id", -1)
        return serialize_documents(docs)

    def count_active_orders_by_staff(self, staff_id: str | ObjectId) -> int:
        return self.collection.count_documents(
            {
                "assigned_staff_id": staff_id,
                "status": {"$in": ["ACCEPTED", "PREPARING"]},
            }
        )

    def record_staff_assignment(self, ticket_id: str | ObjectId, staff_id: str, station: Optional[str] = None) -> Dict[str, Any]:
        t_oid = to_object_id(ticket_id)
        # Unassign previous
        self.assignments_col.update_many(
            {"kitchen_ticket_id": t_oid, "unassigned_at": None},
            {"$set": {"unassigned_at": now_utc()}},
        )
        record = {
            "kitchen_ticket_id": t_oid,
            "staff_id": staff_id,
            "station": station,
            "assigned_at": now_utc(),
            "unassigned_at": None,
        }
        res = self.assignments_col.insert_one(record)
        record["_id"] = res.inserted_id
        return serialize_document(record)

    def find_assignment_history(self, ticket_id: str | ObjectId) -> List[Dict[str, Any]]:
        t_oid = to_object_id(ticket_id)
        docs = self.assignments_col.find({"kitchen_ticket_id": t_oid}).sort("assigned_at", -1)
        return serialize_documents(docs)
