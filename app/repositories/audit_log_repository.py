"""
Audit Log Repository for MongoDB collections:
- order_activity_logs
- kitchen_events
- customer_feedback
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.database.mongodb import (
    order_activity_logs_collection,
    kitchen_events_collection,
    customer_feedback_collection,
)
from app.utils.mongo_utils import to_object_id, serialize_document, serialize_documents, now_utc


class AuditLogRepository:
    def __init__(self):
        self.logs_col = order_activity_logs_collection
        self.events_col = kitchen_events_collection
        self.feedback_col = customer_feedback_collection

    # Order Activity Logs
    def record_order_activity(
        self,
        order_id: str | ObjectId,
        action: str,
        performed_by: Optional[str] = None,
        performed_by_role: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        doc = {
            "order_id": to_object_id(order_id),
            "action": action,
            "performed_by": performed_by,
            "performed_by_role": performed_by_role,
            "timestamp": now_utc(),
            "metadata": metadata or {},
        }
        res = self.logs_col.insert_one(doc)
        doc["_id"] = res.inserted_id
        return serialize_document(doc)

    def find_order_activities(self, order_id: str | ObjectId) -> List[Dict[str, Any]]:
        oid = to_object_id(order_id)
        docs = self.logs_col.find({"order_id": oid}).sort("timestamp", -1)
        return serialize_documents(docs)

    # Kitchen Events
    def record_kitchen_event(
        self,
        order_id: str | ObjectId,
        event: str,
        kitchen_ticket_id: Optional[str | ObjectId] = None,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        staff_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        doc = {
            "order_id": to_object_id(order_id),
            "kitchen_ticket_id": to_object_id(kitchen_ticket_id) if kitchen_ticket_id else None,
            "event": event,
            "old_status": old_status,
            "new_status": new_status,
            "staff_id": staff_id,
            "timestamp": now_utc(),
            "metadata": metadata or {},
        }
        res = self.events_col.insert_one(doc)
        doc["_id"] = res.inserted_id
        return serialize_document(doc)

    def find_kitchen_events(self, order_id: Optional[str | ObjectId] = None) -> List[Dict[str, Any]]:
        query = {}
        if order_id:
            query["order_id"] = to_object_id(order_id)
        docs = self.events_col.find(query).sort("timestamp", -1)
        return serialize_documents(docs)

    # Customer Feedback
    def record_feedback(self, feedback_doc: Dict[str, Any]) -> Dict[str, Any]:
        if "created_at" not in feedback_doc:
            feedback_doc["created_at"] = now_utc()
        res = self.feedback_col.insert_one(feedback_doc)
        feedback_doc["_id"] = res.inserted_id
        return serialize_document(feedback_doc)

    def find_feedback_by_order(self, order_id: str | ObjectId) -> Optional[Dict[str, Any]]:
        oid = to_object_id(order_id)
        doc = self.feedback_col.find_one({"order_id": oid})
        return serialize_document(doc) if doc else None

    def find_all_feedback(self) -> List[Dict[str, Any]]:
        docs = self.feedback_col.find().sort("created_at", -1)
        return serialize_documents(docs)
