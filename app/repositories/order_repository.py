"""
Order Repository for Orders and Order Items.
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.database.mongodb import orders_collection, order_items_collection
from app.repositories.base_repository import BaseRepository
from app.utils.mongo_utils import to_object_id, serialize_document, serialize_documents, now_utc


class OrderRepository(BaseRepository):
    def __init__(self):
        super().__init__(orders_collection)
        self.items_col = order_items_collection

    def find_by_number(self, order_number: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"order_number": order_number})
        return serialize_document(doc) if doc else None

    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        docs = self.collection.find({"status": status}).sort("created_at", -1)
        return serialize_documents(docs)

    def find_active_by_table(self, table_id: str | ObjectId) -> List[Dict[str, Any]]:
        oid = to_object_id(table_id)
        # Active orders occupy the table until COMPLETED or CANCELLED
        docs = self.collection.find(
            {
                "table_id": oid,
                "status": {"$in": ["DRAFT", "PLACED", "CONFIRMED", "SENT_TO_KITCHEN", "PREPARING", "READY", "SERVED", "DELIVERED", "PARTIALLY_DELIVERED"]},
            }
        )
        return serialize_documents(docs)

    # Order Item methods
    def add_order_item(self, item_doc: Dict[str, Any]) -> Dict[str, Any]:
        res = self.items_col.insert_one(item_doc)
        item_doc["_id"] = res.inserted_id
        return serialize_document(item_doc)

    def find_order_items(self, order_id: str | ObjectId) -> List[Dict[str, Any]]:
        oid = to_object_id(order_id)
        docs = list(self.items_col.find({"order_id": oid}).sort("created_at", 1))
        serialized = serialize_documents(docs)
        for item in serialized:
            if "name" not in item and "item_name_snapshot" in item:
                item["name"] = item["item_name_snapshot"]
            if "price" not in item and "unit_price_snapshot" in item:
                item["price"] = item["unit_price_snapshot"]
            if "price_at_addition" not in item:
                item["price_at_addition"] = item.get("unit_price_snapshot", item.get("price"))
            if "status" not in item:
                item["status"] = "PENDING"
            if "batch_number" not in item:
                item["batch_number"] = 1
            if "is_additional" not in item:
                item["is_additional"] = False
        return serialized

    def find_order_item(self, item_id: str | ObjectId) -> Optional[Dict[str, Any]]:
        oid = to_object_id(item_id)
        doc = self.items_col.find_one({"_id": oid})
        return serialize_document(doc) if doc else None

    def update_order_item(self, item_id: str | ObjectId, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        oid = to_object_id(item_id)
        self.items_col.update_one({"_id": oid}, {"$set": update_data})
        doc = self.items_col.find_one({"_id": oid})
        return serialize_document(doc) if doc else None

    def delete_order_item(self, item_id: str | ObjectId) -> bool:
        oid = to_object_id(item_id)
        res = self.items_col.delete_one({"_id": oid})
        return res.deleted_count > 0

    def delete_items_by_order(self, order_id: str | ObjectId) -> int:
        oid = to_object_id(order_id)
        res = self.items_col.delete_many({"order_id": oid})
        return res.deleted_count
