"""
Recipe Service for mapping Menu Items to Ingredients and validating stock requirements.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.database.mongodb import (
    recipes_collection,
    menu_items_collection,
    ingredients_collection,
)
from app.models.entities import Recipe as RecipeEntity
from app.services.common import (
    now_utc,
    to_object_id,
    decimal128,
    serialize_document,
    serialize_documents,
    get_field,
)
from app.utils.units import convert_quantity


class RecipeService:

    @staticmethod
    def create_recipe(menu_item_id_or_data: Any, data: Optional[Any] = None) -> Dict[str, Any]:
        """
        Accepts either (menu_item_id, data) or (data) with data.menu_item_id.
        """
        if data is None:
            data = menu_item_id_or_data
            menu_item_id = get_field(data, "menu_item_id")
        else:
            menu_item_id = menu_item_id_or_data

        ingredient_id = get_field(data, "ingredient_id")
        quantity_required = get_field(data, "quantity_required")
        unit = get_field(data, "unit")

        if not menu_item_id or not ingredient_id:
            raise ValueError("menu_item_id and ingredient_id are required")

        # Validate with Domain Entity
        entity = RecipeEntity(
            menu_item_id=str(menu_item_id),
            ingredient_id=str(ingredient_id),
            quantity_required=quantity_required,
        )

        menu_item = menu_items_collection.find_one({"_id": to_object_id(entity.menu_item_id)})
        if not menu_item:
            raise ValueError("Menu item not found")

        ingredient = ingredients_collection.find_one({"_id": to_object_id(entity.ingredient_id)})
        if not ingredient:
            raise ValueError("Ingredient not found")

        existing = recipes_collection.find_one({
            "menu_item_id": to_object_id(entity.menu_item_id),
            "ingredient_id": to_object_id(entity.ingredient_id),
        })

        if existing:
            # Update existing recipe quantity
            recipes_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": {"quantity_required": decimal128(entity.quantity_required)}}
            )
            return RecipeService.get_recipe(str(existing["_id"]))

        recipe = {
            "menu_item_id": to_object_id(entity.menu_item_id),
            "ingredient_id": to_object_id(entity.ingredient_id),
            "quantity_required": decimal128(entity.quantity_required),
            "unit": unit or ingredient.get("unit"),
            "created_at": now_utc(),
        }

        result = recipes_collection.insert_one(recipe)
        recipe["_id"] = result.inserted_id
        return serialize_document(recipe)

    @staticmethod
    def get_by_menu_item(menu_item_id: str) -> List[Dict[str, Any]]:
        recipes = list(recipes_collection.find({"menu_item_id": to_object_id(menu_item_id)}))
        # Enrich with ingredient name and unit
        enriched = []
        for r in recipes:
            item = serialize_document(r)
            ing = ingredients_collection.find_one({"_id": r["ingredient_id"]})
            if ing:
                item["ingredient_name"] = ing.get("name")
                item["ingredient_unit"] = ing.get("unit")
                item["available_stock"] = ing.get("available_quantity")
            enriched.append(item)
        return enriched

    @staticmethod
    def get_recipe(recipe_id: str) -> Dict[str, Any]:
        recipe = recipes_collection.find_one({"_id": to_object_id(recipe_id)})
        if not recipe:
            raise ValueError("Recipe not found")
        return serialize_document(recipe)

    @staticmethod
    def update_recipe(recipe_id: str, data: Any) -> Dict[str, Any]:
        qty = get_field(data, "quantity_required")
        dec_qty = Decimal(str(qty))
        if dec_qty <= 0:
            raise ValueError("Recipe quantity required must be greater than zero")

        result = recipes_collection.update_one(
            {"_id": to_object_id(recipe_id)},
            {"$set": {"quantity_required": decimal128(dec_qty)}}
        )
        if result.matched_count == 0:
            raise ValueError("Recipe not found")
        return RecipeService.get_recipe(recipe_id)

    @staticmethod
    def delete_recipe(recipe_id: str) -> Dict[str, Any]:
        result = recipes_collection.delete_one({"_id": to_object_id(recipe_id)})
        if result.deleted_count == 0:
            raise ValueError("Recipe not found")
        return {"message": "Recipe deleted successfully"}

    @staticmethod
    def check_availability(menu_item_id: str, order_quantity: int = 1) -> tuple[bool, Optional[str]]:
        """
        Multiplies recipe requirement by order_quantity and verifies against stock.
        """
        recipes = list(recipes_collection.find({"menu_item_id": to_object_id(menu_item_id)}))
        for r in recipes:
            ing = ingredients_collection.find_one({"_id": r["ingredient_id"]})
            if not ing:
                continue
            avail = ing["available_quantity"].to_decimal() if hasattr(ing["available_quantity"], "to_decimal") else Decimal(str(ing["available_quantity"]))
            req_per_unit = r["quantity_required"].to_decimal() if hasattr(r["quantity_required"], "to_decimal") else Decimal(str(r["quantity_required"]))
            rec_unit = r.get("unit") or ing["unit"]
            converted_req = convert_quantity(req_per_unit * Decimal(order_quantity), rec_unit, ing["unit"])

            if avail < converted_req:
                return False, f"Insufficient stock for {ing['name']}. Available: {avail} {ing['unit']}, Required: {converted_req} {ing['unit']}"

        return True, None
