"""
Inventory, Recipe, Batch, Supplier, and Purchase Order Repositories.
Provides high-integrity data access for ingredients, stock ledger, batches, locations, and vendors.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId
from bson.decimal128 import Decimal128
from app.database.mongodb import (
    ingredients_collection,
    recipes_collection,
    stock_movements_collection,
    batches_collection,
    suppliers_collection,
    purchase_orders_collection,
    storage_locations_collection,
    ingredient_categories_collection,
    wastage_records_collection,
    stock_adjustments_collection,
    stock_transfers_collection,
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

    def find_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        if not sku:
            return None
        doc = self.collection.find_one({"sku": {"$regex": f"^{sku}$", "$options": "i"}})
        return serialize_document(doc) if doc else None

    def find_active(self) -> List[Dict[str, Any]]:
        docs = self.collection.find({"is_active": True}).sort("name", 1)
        return serialize_documents(docs)

    def find_low_stock(self) -> List[Dict[str, Any]]:
        # All ingredients where available_quantity <= reorder_level or minimum_stock_level
        pipeline = [
            {"$match": {"is_active": True}},
            {
                "$match": {
                    "$expr": {
                        "$lte": [
                            "$available_quantity",
                            {"$ifNull": ["$reorder_level", "$minimum_stock_level"]}
                        ]
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
                },
                "$set": {
                    "updated_at": now_utc()
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
                movement_data["ingredient_name"] = ing.get("name")
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

    def find_filtered_movements(
        self,
        ingredient_id: Optional[str] = None,
        movement_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        supplier_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if ingredient_id:
            query["ingredient_id"] = to_object_id(ingredient_id)
        if movement_type and movement_type != "ALL":
            query["movement_type"] = movement_type.upper()
        if supplier_id:
            query["supplier_id"] = to_object_id(supplier_id)
        if start_date or end_date:
            date_filter: Dict[str, Any] = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["created_at"] = date_filter

        docs = list(self.movements_col.find(query).sort("created_at", -1).limit(limit))
        serialized = serialize_documents(docs)
        ing_cache = {}
        for doc in serialized:
            i_id = str(doc.get("ingredient_id"))
            if i_id not in ing_cache:
                ing = self.collection.find_one({"_id": to_object_id(i_id)})
                ing_cache[i_id] = (ing.get("name"), ing.get("unit")) if ing else (None, None)
            name, unit = ing_cache[i_id]
            doc["ingredient_name"] = name
            if not doc.get("unit"):
                doc["unit"] = unit
        return serialized


class BatchRepository(BaseRepository):
    def __init__(self):
        super().__init__(batches_collection)

    def create_batch(self, batch_data: Dict[str, Any]) -> Dict[str, Any]:
        if "created_at" not in batch_data:
            batch_data["created_at"] = now_utc()
        if "status" not in batch_data:
            batch_data["status"] = "ACTIVE"
        res = self.collection.insert_one(batch_data)
        batch_data["_id"] = res.inserted_id
        return serialize_document(batch_data)

    def find_by_ingredient(self, ingredient_id: str | ObjectId, only_active: bool = False) -> List[Dict[str, Any]]:
        oid = to_object_id(ingredient_id)
        query: Dict[str, Any] = {"ingredient_id": oid}
        if only_active:
            query["remaining_quantity"] = {"$gt": decimal128(Decimal("0"))}
            query["status"] = {"$in": ["ACTIVE", "EXPIRING_SOON"]}
        docs = list(self.collection.find(query).sort("expiry_date", 1))
        return serialize_documents(docs)

    def find_active_batches_fefo(self, ingredient_id: str | ObjectId) -> List[Dict[str, Any]]:
        """
        Returns active, non-expired batches with remaining quantity > 0 sorted by earliest expiry date.
        """
        oid = to_object_id(ingredient_id)
        now = now_utc()
        query = {
            "ingredient_id": oid,
            "remaining_quantity": {"$gt": decimal128(Decimal("0"))},
            "expiry_date": {"$gt": now},
            "status": {"$in": ["ACTIVE", "EXPIRING_SOON"]},
        }
        docs = list(self.collection.find(query).sort("expiry_date", 1))
        return serialize_documents(docs)

    def decrement_batch(self, batch_id: str | ObjectId, delta: Decimal) -> Optional[Dict[str, Any]]:
        oid = to_object_id(batch_id)
        batch = self.collection.find_one({"_id": oid})
        if not batch:
            return None
        current_rem = batch["remaining_quantity"].to_decimal() if hasattr(batch["remaining_quantity"], "to_decimal") else Decimal(str(batch["remaining_quantity"]))
        new_rem = max(Decimal("0"), current_rem - delta)
        new_status = "CONSUMED" if new_rem == 0 else batch.get("status", "ACTIVE")
        self.collection.update_one(
            {"_id": oid},
            {
                "$set": {
                    "remaining_quantity": decimal128(new_rem),
                    "status": new_status,
                    "updated_at": now_utc(),
                }
            }
        )
        return self.find_by_id(oid)

    def find_expiring_batches(self, warning_days: int = 3) -> List[Dict[str, Any]]:
        now = now_utc()
        threshold_date = now.replace(day=now.day + warning_days) if hasattr(now, "replace") else now
        try:
            from datetime import timedelta
            threshold_date = now + timedelta(days=warning_days)
        except Exception:
            pass

        query = {
            "remaining_quantity": {"$gt": decimal128(Decimal("0"))},
            "expiry_date": {"$gte": now, "$lte": threshold_date},
        }
        docs = list(self.collection.find(query).sort("expiry_date", 1))
        serialized = serialize_documents(docs)
        for b in serialized:
            ing = ingredients_collection.find_one({"_id": to_object_id(b.get("ingredient_id"))})
            if ing:
                b["ingredient_name"] = ing.get("name")
        return serialized

    def find_expired_batches(self) -> List[Dict[str, Any]]:
        now = now_utc()
        query = {
            "remaining_quantity": {"$gt": decimal128(Decimal("0"))},
            "expiry_date": {"$lt": now},
        }
        docs = list(self.collection.find(query).sort("expiry_date", 1))
        serialized = serialize_documents(docs)
        for b in serialized:
            ing = ingredients_collection.find_one({"_id": to_object_id(b.get("ingredient_id"))})
            if ing:
                b["ingredient_name"] = ing.get("name")
        return serialized


class SupplierRepository(BaseRepository):
    def __init__(self):
        super().__init__(suppliers_collection)

    def find_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
        return serialize_document(doc) if doc else None

    def find_active(self) -> List[Dict[str, Any]]:
        docs = self.collection.find({"is_active": True}).sort("name", 1)
        return serialize_documents(docs)


class PurchaseOrderRepository(BaseRepository):
    def __init__(self):
        super().__init__(purchase_orders_collection)

    def find_by_po_number(self, po_number: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.find_one({"po_number": po_number})
        return serialize_document(doc) if doc else None

    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        docs = self.collection.find({"status": status.upper()}).sort("order_date", -1)
        return serialize_documents(docs)


class CategoryRepository(BaseRepository):
    def __init__(self):
        super().__init__(ingredient_categories_collection)


class StorageLocationRepository(BaseRepository):
    def __init__(self):
        super().__init__(storage_locations_collection)


class WastageRepository(BaseRepository):
    def __init__(self):
        super().__init__(wastage_records_collection)


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
