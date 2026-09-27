"""
Table and Reservation Repositories.
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.database.mongodb import restaurant_tables_collection, reservations_collection
from app.repositories.base_repository import BaseRepository
from app.services.common import to_object_id, serialize_document, serialize_documents, now_utc


class TableRepository(BaseRepository):
    def __init__(self):
        super().__init__(restaurant_tables_collection)

    def find_by_number(self, table_number: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"table_number": table_number.strip()})
        return serialize_document(doc) if doc else None

    def find_available(self) -> List[Dict[str, Any]]:
        docs = self.collection.find({"status": "AVAILABLE", "is_active": True}).sort("table_number", 1)
        return serialize_documents(docs)

    def set_status(self, table_id: str | ObjectId, status: str) -> Optional[Dict[str, Any]]:
        oid = to_object_id(table_id)
        self.collection.update_one({"_id": oid}, {"$set": {"status": status, "updated_at": now_utc()}})
        return self.find_by_id(oid)


class ReservationRepository(BaseRepository):
    def __init__(self):
        super().__init__(reservations_collection)

    def find_overlapping(
        self,
        table_id: str | ObjectId,
        reservation_date: str,
        start_time: str,
        end_time: str,
        exclude_id: Optional[str | ObjectId] = None,
    ) -> List[Dict[str, Any]]:
        oid = to_object_id(table_id)
        query = {
            "table_id": oid,
            "reservation_date": str(reservation_date),
            "status": {"$in": ["REQUESTED", "CONFIRMED", "SEATED"]},
            "$expr": {
                "$and": [
                    {"$lt": ["$start_time", str(end_time)]},
                    {"$gt": ["$end_time", str(start_time)]},
                ]
            },
        }
        if exclude_id:
            query["_id"] = {"$ne": to_object_id(exclude_id)}

        docs = self.collection.find(query)
        return serialize_documents(docs)

    def find_by_customer(self, customer_id: str | ObjectId) -> List[Dict[str, Any]]:
        oid = to_object_id(customer_id)
        docs = self.collection.find({"customer_id": oid}).sort("created_at", -1)
        return serialize_documents(docs)

    def find_by_table(self, table_id: str | ObjectId) -> List[Dict[str, Any]]:
        oid = to_object_id(table_id)
        docs = self.collection.find({"table_id": oid}).sort("created_at", -1)
        return serialize_documents(docs)
