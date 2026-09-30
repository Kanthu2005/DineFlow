"""
Menu Repository for Menu Items and Categories.
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.database.mongodb import menu_items_collection, menu_categories_collection
from app.repositories.base_repository import BaseRepository
from app.utils.mongo_utils import to_object_id, serialize_document, serialize_documents


class MenuRepository(BaseRepository):
    def __init__(self):
        super().__init__(menu_items_collection)
        self.categories_col = menu_categories_collection

    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
        return serialize_document(doc) if doc else None

    def find_by_category(self, category_id: str) -> List[Dict[str, Any]]:
        if not category_id:
            return []
        match_keys = []
        if isinstance(category_id, ObjectId):
            match_keys.extend([category_id, str(category_id)])
        elif ObjectId.is_valid(str(category_id)):
            match_keys.extend([ObjectId(str(category_id)), str(category_id)])
        else:
            match_keys.append(str(category_id))
            cat = self.find_category_by_name(str(category_id))
            if cat:
                raw_id = cat.get("id") or cat.get("_id")
                if raw_id:
                    match_keys.append(raw_id)
                    if ObjectId.is_valid(str(raw_id)):
                        match_keys.append(ObjectId(str(raw_id)))
        docs = self.collection.find({"category_id": {"$in": match_keys}})
        return serialize_documents(docs)

    def find_available(self) -> List[Dict[str, Any]]:
        docs = self.collection.find({"is_available": True})
        return serialize_documents(docs)

    def search(self, query_str: str) -> List[Dict[str, Any]]:
        query = {
            "$or": [
                {"name": {"$regex": query_str, "$options": "i"}},
                {"description": {"$regex": query_str, "$options": "i"}},
            ]
        }
        docs = self.collection.find(query)
        return serialize_documents(docs)

    # Category methods
    def create_category(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        res = self.categories_col.insert_one(doc)
        doc["_id"] = res.inserted_id
        return serialize_document(doc)

    def find_category_by_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        if not category_id:
            return None
        # Try valid ObjectId
        if ObjectId.is_valid(str(category_id)):
            doc = self.categories_col.find_one({"_id": ObjectId(str(category_id))})
            if doc:
                return serialize_document(doc)
        # Try string _id or exact name match
        doc = self.categories_col.find_one({
            "$or": [
                {"_id": str(category_id)},
                {"name": {"$regex": f"^{str(category_id).strip()}$", "$options": "i"}}
            ]
        })
        return serialize_document(doc) if doc else None

    def find_category_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        if not name:
            return None
        doc = self.categories_col.find_one({"name": {"$regex": f"^{name.strip()}$", "$options": "i"}})
        return serialize_document(doc) if doc else None

    def find_all_categories(self) -> List[Dict[str, Any]]:
        docs = self.categories_col.find().sort("name", 1)
        return serialize_documents(docs)

    def update_category(self, category_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        cat = self.find_category_by_id(category_id)
        if not cat:
            return None
        raw_id = cat.get("id") or cat.get("_id")
        oid = ObjectId(str(raw_id)) if ObjectId.is_valid(str(raw_id)) else raw_id
        self.categories_col.update_one({"_id": oid}, {"$set": update_data})
        return self.find_category_by_id(raw_id)

    def delete_category(self, category_id: str) -> bool:
        if not category_id:
            return False
        cat = self.find_category_by_id(category_id)
        raw_id = (cat.get("id") or cat.get("_id")) if cat else category_id
        if not raw_id:
            return False
        raw_str = str(raw_id).strip()
        queries = [{"_id": raw_str}]
        if ObjectId.is_valid(raw_str):
            queries.insert(0, {"_id": ObjectId(raw_str)})
        res = self.categories_col.delete_one({"$or": queries})
        return res.deleted_count > 0
