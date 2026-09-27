"""
Base Repository implementing common MongoDB CRUD operations.
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from pymongo.collection import Collection
from app.services.common import to_object_id, serialize_document, serialize_documents, now_utc


class BaseRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def find_by_id(self, item_id: str | ObjectId) -> Optional[Dict[str, Any]]:
        oid = to_object_id(item_id)
        doc = self.collection.find_one({"_id": oid})
        return serialize_document(doc) if doc else None

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one(query)
        return serialize_document(doc) if doc else None

    def find_all(
        self, query: Optional[Dict[str, Any]] = None, sort_field: str = "_id", sort_dir: int = -1
    ) -> List[Dict[str, Any]]:
        query = query or {}
        cursor = self.collection.find(query).sort(sort_field, sort_dir)
        return serialize_documents(cursor)

    def insert(self, document: Dict[str, Any]) -> Dict[str, Any]:
        if "created_at" not in document:
            document["created_at"] = now_utc()
        result = self.collection.insert_one(document)
        document["_id"] = result.inserted_id
        return serialize_document(document)

    def update(self, item_id: str | ObjectId, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        oid = to_object_id(item_id)
        if "updated_at" not in update_data:
            update_data["updated_at"] = now_utc()
        self.collection.update_one({"_id": oid}, {"$set": update_data})
        return self.find_by_id(oid)

    def delete(self, item_id: str | ObjectId) -> bool:
        oid = to_object_id(item_id)
        result = self.collection.delete_one({"_id": oid})
        return result.deleted_count > 0

    def count(self, query: Optional[Dict[str, Any]] = None) -> int:
        return self.collection.count_documents(query or {})
