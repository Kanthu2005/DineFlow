from decimal import Decimal
from bson import ObjectId
from bson.decimal128 import Decimal128
from app.database.mongodb import (
    stock_movements_collection,
    ingredients_collection,
)
from app.services.common import (
    now_utc,
    to_object_id,
    decimal128,
    serialize_document,
    serialize_documents,
)


class StockMovementService:

    @staticmethod
    def create_movement(data):

        ingredient_id = getattr(data, "ingredient_id", None) or (data.get("ingredient_id") if isinstance(data, dict) else None)
        movement_type = getattr(data, "movement_type", None) or (data.get("movement_type") if isinstance(data, dict) else None)
        quantity_raw = getattr(data, "quantity", None) or (data.get("quantity") if isinstance(data, dict) else None)
        reference_type = getattr(data, "reference_type", None) or (data.get("reference_type") if isinstance(data, dict) else None)
        reference_id = getattr(data, "reference_id", None) or (data.get("reference_id") if isinstance(data, dict) else None)
        created_by = getattr(data, "created_by", None) or (data.get("created_by") if isinstance(data, dict) else "SYSTEM")

        if not ingredient_id:
            raise ValueError("ingredient_id is required")
        if not movement_type:
            raise ValueError("movement_type is required")
        if quantity_raw is None:
            raise ValueError("quantity is required")

        ingredient = ingredients_collection.find_one(
            {"_id": to_object_id(ingredient_id)}
        )

        if not ingredient:
            raise ValueError("Ingredient not found")

        quantity = Decimal(str(quantity_raw))

        if movement_type in [
            "OUT",
            "USAGE",
            "WASTE",
        ]:

            available = ingredient[
                "available_quantity"
            ].to_decimal()

            if quantity > available:
                raise ValueError(
                    "Insufficient stock"
                )

            quantity_change = -quantity

        else:
            quantity_change = quantity

        ingredients_collection.update_one(
            {"_id": ingredient["_id"]},
            {
                "$inc": {
                    "available_quantity": decimal128(
                        quantity_change
                    )
                }
            }
        )

        movement = {
            "ingredient_id": ingredient["_id"],
            "movement_type": movement_type,
            "quantity": decimal128(quantity),
            "reference_type": reference_type,
            "reference_id": reference_id,
            "created_by": created_by,
            "created_at": now_utc(),
        }

        result = stock_movements_collection.insert_one(
            movement
        )

        movement["_id"] = result.inserted_id

        return serialize_document(movement)

    @staticmethod
    def get_movements():

        movements = stock_movements_collection.find().sort(
            "created_at",
            -1
        )

        return serialize_documents(movements)

    @staticmethod
    def get_by_ingredient(ingredient_id):

        movements = stock_movements_collection.find(
            {
                "ingredient_id": to_object_id(
                    ingredient_id
                )
            }
        ).sort(
            "created_at",
            -1
        )

        return serialize_documents(movements)


#billingservice...
