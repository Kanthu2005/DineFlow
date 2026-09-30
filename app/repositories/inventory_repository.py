"""
Inventory and Recipe Repositories for managing ingredients, stock movements, and recipes.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId
from bson.decimal128 import Decimal128
from app.database.mongodb import (
    ingredients_collection,
    recipes_collection,
    stock_movements_collection,
)
from app.repositories.base_repository import BaseRepository
from app.utils.mongo_utils import to_object_id, serialize_document, serialize_documents, decimal128, now_utc


class IngredientRepository(BaseRepository):
    def __init__(self):
        super().__init__(ingredients_collection)
        self.movements_col = stock_movements_collection

    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
        return serialize_document(doc) if doc else None

    def find_active(self) -> List[Dict[str, Any]]:
        docs = self.collection.find({"is_active": True}).sort("name", 1)
        return serialize_documents(docs)

    def find_low_stock(self) -> List[Dict[str, Any]]:
        # All ingredients where available_quantity <= minimum_stock_level
        pipeline = [
            {"$match": {"is_active": True}},
            {
                "$match": {
                    "$expr": {
                        "$lte": ["$available_quantity", "$minimum_stock_level"]
                    }
                }
            },
            {"$sort": {"name": 1}},
        ]
        docs = list(self.collection.aggregate(pipeline))
        return serialize_documents(docs)

    def increment_stock(self, ingredient_id: str | ObjectId, delta: Decimal) -> Optional[Dict[str, Any]]:
        oid = to_object_id(ingredient_id)
        self.collection.update_one(
            {"_id": oid},
            {
                "$inc": {
                    "available_quantity": decimal128(delta),
                    "current_stock": decimal128(delta),
                }
            }
        )
        return self.find_by_id(oid)

    # Movements
    def record_movement(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        if "created_at" not in movement_data:
            movement_data["created_at"] = now_utc()
        if "unit" not in movement_data and "ingredient_id" in movement_data:
            ing = self.collection.find_one({"_id": to_object_id(movement_data["ingredient_id"])})
            if ing:
                movement_data["unit"] = ing.get("unit")
        res = self.movements_col.insert_one(movement_data)
        movement_data["_id"] = res.inserted_id
        return serialize_document(movement_data)

    def find_movements_by_ingredient(self, ingredient_id: str | ObjectId) -> List[Dict[str, Any]]:
        oid = to_object_id(ingredient_id)
        docs = list(self.movements_col.find({"ingredient_id": oid}).sort("created_at", -1))
        ing = self.collection.find_one({"_id": oid})
        ing_name = ing.get("name") if ing else None
        serialized = serialize_documents(docs)
        for doc in serialized:
            if ing_name:
                doc["ingredient_name"] = ing_name
        return serialized

    def find_all_movements(self, limit: int = 100) -> List[Dict[str, Any]]:
        docs = list(self.movements_col.find().sort("created_at", -1).limit(limit))
        serialized = serialize_documents(docs)
        # Cache ingredient names
        ing_cache = {}
        for doc in serialized:
            ing_id = str(doc.get("ingredient_id"))
            if ing_id not in ing_cache:
                ing = self.collection.find_one({"_id": to_object_id(ing_id)})
                ing_cache[ing_id] = (ing.get("name"), ing.get("unit")) if ing else (None, None)
            name, unit = ing_cache[ing_id]
            doc["ingredient_name"] = name
            if not doc.get("unit"):
                doc["unit"] = unit
        return serialized


class RecipeRepository(BaseRepository):
    def __init__(self):
        super().__init__(recipes_collection)

    def find_by_menu_item(self, menu_item_id: str | ObjectId) -> List[Dict[str, Any]]:
        oid = to_object_id(menu_item_id)
        docs = self.collection.find({"menu_item_id": oid})
        return serialize_documents(docs)

    def find_by_item_and_ingredient(
        self, menu_item_id: str | ObjectId, ingredient_id: str | ObjectId
    ) -> Optional[Dict[str, Any]]:
        m_oid = to_object_id(menu_item_id)
        i_oid = to_object_id(ingredient_id)
        doc = self.collection.find_one({"menu_item_id": m_oid, "ingredient_id": i_oid})
        return serialize_document(doc) if doc else None
