"""
Menu Repository for Menu Items, Categories, and Subcategories.
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.database.mongodb import (
    menu_items_collection,
    menu_categories_collection,
    menu_subcategories_collection,
    order_items_collection,
    orders_collection,
    kitchen_tickets_collection,
    recipes_collection,
)
from app.repositories.base_repository import BaseRepository
from app.utils.mongo_utils import to_object_id, serialize_document, serialize_documents


class MenuRepository(BaseRepository):
    def __init__(self):
        super().__init__(menu_items_collection)
        self.categories_col = menu_categories_collection
        self.subcategories_col = menu_subcategories_collection

    # ==========================================
    # Menu Items
    # ==========================================

    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"name": {"$regex": f"^{name.strip()}$", "$options": "i"}})
        return serialize_document(doc) if doc else None

    def find_by_category(self, category_id: str, include_inactive: bool = False) -> List[Dict[str, Any]]:
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

        query: Dict[str, Any] = {"category_id": {"$in": match_keys}}
        if not include_inactive:
            query["is_active"] = {"$ne": False}

        docs = self.collection.find(query).sort([("display_order", 1), ("name", 1)])
        return serialize_documents(docs)

    def find_by_subcategory(self, subcategory_id: str, include_inactive: bool = False) -> List[Dict[str, Any]]:
        if not subcategory_id:
            return []
        match_keys = []
        if isinstance(subcategory_id, ObjectId):
            match_keys.extend([subcategory_id, str(subcategory_id)])
        elif ObjectId.is_valid(str(subcategory_id)):
            match_keys.extend([ObjectId(str(subcategory_id)), str(subcategory_id)])
        else:
            match_keys.append(str(subcategory_id))

        query: Dict[str, Any] = {"subcategory_id": {"$in": match_keys}}
        if not include_inactive:
            query["is_active"] = {"$ne": False}

        docs = self.collection.find(query).sort([("display_order", 1), ("name", 1)])
        return serialize_documents(docs)

    def find_available(self) -> List[Dict[str, Any]]:
        docs = self.collection.find({"is_available": True, "is_active": {"$ne": False}}).sort([("display_order", 1), ("name", 1)])
        return serialize_documents(docs)

    def search(self, query_str: str, include_inactive: bool = False) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {
            "$or": [
                {"name": {"$regex": query_str, "$options": "i"}},
                {"description": {"$regex": query_str, "$options": "i"}},
                {"tags": {"$in": [query_str]}},
            ]
        }
        if not include_inactive:
            query["is_active"] = {"$ne": False}
        docs = self.collection.find(query).sort([("display_order", 1), ("name", 1)])
        return serialize_documents(docs)

    def has_item_associations(self, item_id: str) -> bool:
        """Check if an item has historical records in orders, kitchen, or recipes."""
        raw_keys = [item_id]
        if ObjectId.is_valid(str(item_id)):
            raw_keys.append(ObjectId(str(item_id)))

        in_order_items = order_items_collection.find_one({"menu_item_id": {"$in": raw_keys}}) is not None
        in_orders = orders_collection.find_one({"items.menu_item_id": {"$in": raw_keys}}) is not None
        in_kitchen = kitchen_tickets_collection.find_one({"items.menu_item_id": {"$in": raw_keys}}) is not None
        in_recipes = recipes_collection.find_one({"menu_item_id": {"$in": raw_keys}}) is not None
        return in_order_items or in_orders or in_kitchen or in_recipes

    def soft_delete_item(self, item_id: str) -> bool:
        raw_id = ObjectId(str(item_id)) if ObjectId.is_valid(str(item_id)) else item_id
        res = self.collection.update_one(
            {"$or": [{"_id": raw_id}, {"_id": str(item_id)}]},
            {"$set": {"is_active": False, "is_available": False}}
        )
        return res.modified_count > 0

    # ==========================================
    # Category Methods
    # ==========================================

    def create_category(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        res = self.categories_col.insert_one(doc)
        doc["_id"] = res.inserted_id
        return serialize_document(doc)

    def find_category_by_id(self, category_id: str) -> Optional[Dict[str, Any]]:
        if not category_id:
            return None
        if ObjectId.is_valid(str(category_id)):
            doc = self.categories_col.find_one({"_id": ObjectId(str(category_id))})
            if doc:
                return serialize_document(doc)
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

    def find_all_categories(self, active_only: bool = False) -> List[Dict[str, Any]]:
        query = {"is_active": True} if active_only else {}
        docs = self.categories_col.find(query).sort([("display_order", 1), ("name", 1)])
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

    # ==========================================
    # Subcategory Methods
    # ==========================================

    def create_subcategory(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        res = self.subcategories_col.insert_one(doc)
        doc["_id"] = res.inserted_id
        return serialize_document(doc)

    def find_subcategory_by_id(self, subcategory_id: str) -> Optional[Dict[str, Any]]:
        if not subcategory_id:
            return None
        if ObjectId.is_valid(str(subcategory_id)):
            doc = self.subcategories_col.find_one({"_id": ObjectId(str(subcategory_id))})
            if doc:
                return serialize_document(doc)
        doc = self.subcategories_col.find_one({
            "$or": [
                {"_id": str(subcategory_id)},
                {"name": {"$regex": f"^{str(subcategory_id).strip()}$", "$options": "i"}}
            ]
        })
        return serialize_document(doc) if doc else None

    def find_subcategory_by_name(self, category_id: str, name: str) -> Optional[Dict[str, Any]]:
        if not name or not category_id:
            return None
        cat_keys = [str(category_id)]
        if ObjectId.is_valid(str(category_id)):
            cat_keys.append(ObjectId(str(category_id)))

        doc = self.subcategories_col.find_one({
            "category_id": {"$in": cat_keys},
            "name": {"$regex": f"^{name.strip()}$", "$options": "i"},
        })
        return serialize_document(doc) if doc else None

    def find_subcategories_by_category(self, category_id: str, active_only: bool = False) -> List[Dict[str, Any]]:
        if not category_id:
            return []
        cat_keys = [str(category_id)]
        if ObjectId.is_valid(str(category_id)):
            cat_keys.append(ObjectId(str(category_id)))

        query: Dict[str, Any] = {"category_id": {"$in": cat_keys}}
        if active_only:
            query["is_active"] = True

        docs = self.subcategories_col.find(query).sort([("display_order", 1), ("name", 1)])
        return serialize_documents(docs)

    def find_all_subcategories(self, active_only: bool = False) -> List[Dict[str, Any]]:
        query = {"is_active": True} if active_only else {}
        docs = self.subcategories_col.find(query).sort([("display_order", 1), ("name", 1)])
        return serialize_documents(docs)

    def update_subcategory(self, subcategory_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        subcat = self.find_subcategory_by_id(subcategory_id)
        if not subcat:
            return None
        raw_id = subcat.get("id") or subcat.get("_id")
        oid = ObjectId(str(raw_id)) if ObjectId.is_valid(str(raw_id)) else raw_id
        self.subcategories_col.update_one({"_id": oid}, {"$set": update_data})
        return self.find_subcategory_by_id(raw_id)

    def delete_subcategory(self, subcategory_id: str) -> bool:
        if not subcategory_id:
            return False
        subcat = self.find_subcategory_by_id(subcategory_id)
        raw_id = (subcat.get("id") or subcat.get("_id")) if subcat else subcategory_id
        if not raw_id:
            return False
        raw_str = str(raw_id).strip()
        queries = [{"_id": raw_str}]
        if ObjectId.is_valid(raw_str):
            queries.insert(0, {"_id": ObjectId(raw_str)})
        res = self.subcategories_col.delete_one({"$or": queries})
        return res.deleted_count > 0
