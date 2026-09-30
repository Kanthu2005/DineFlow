"""
Recipe Service for mapping Menu Items to Ingredients, calculating live availability,
and validating stock requirements.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
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
            unit=unit,
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
            # Update existing recipe quantity and unit
            update_fields: Dict[str, Any] = {"quantity_required": decimal128(entity.quantity_required)}
            if entity.unit:
                update_fields["unit"] = entity.unit
            recipes_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": update_fields}
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
        enriched = []
        for r in recipes:
            item = serialize_document(r)
            ing = ingredients_collection.find_one({"_id": r["ingredient_id"]})
            if ing:
                item["ingredient_name"] = ing.get("name")
                item["ingredient_unit"] = ing.get("unit")
                avail = ing.get("available_quantity")
                item["available_stock"] = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail or 0))
            enriched.append(item)
        return enriched

    @staticmethod
    def get_recipe(recipe_id: str) -> Dict[str, Any]:
        recipe = recipes_collection.find_one({"_id": to_object_id(recipe_id)})
        if not recipe:
            raise ValueError("Recipe not found")
        item = serialize_document(recipe)
        ing = ingredients_collection.find_one({"_id": recipe["ingredient_id"]})
        if ing:
            item["ingredient_name"] = ing.get("name")
            item["ingredient_unit"] = ing.get("unit")
            avail = ing.get("available_quantity")
            item["available_stock"] = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail or 0))
        return item

    @staticmethod
    def update_recipe(recipe_id: str, data: Any) -> Dict[str, Any]:
        qty = get_field(data, "quantity_required")
        unit = get_field(data, "unit")

        update_dict: Dict[str, Any] = {}
        if qty is not None:
            dec_qty = Decimal(str(qty))
            if dec_qty <= 0:
                raise ValueError("Recipe quantity required must be greater than zero")
            update_dict["quantity_required"] = decimal128(dec_qty)
        if unit:
            update_dict["unit"] = unit.strip()

        if not update_dict:
            return RecipeService.get_recipe(recipe_id)

        result = recipes_collection.update_one(
            {"_id": to_object_id(recipe_id)},
            {"$set": update_dict}
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
    def delete_by_menu_item_and_ingredient(menu_item_id: str, ingredient_id: str) -> Dict[str, Any]:
        result = recipes_collection.delete_one({
            "menu_item_id": to_object_id(menu_item_id),
            "ingredient_id": to_object_id(ingredient_id),
        })
        if result.deleted_count == 0:
            raise ValueError("Recipe mapping not found")
        return {"message": "Ingredient removed from recipe"}

    @staticmethod
    def calculate_item_availability(menu_item_id: str, requested_quantity: int = 1) -> Dict[str, Any]:
        """
        Determines the real-time stock availability state of a menu item.
        Returns:
          status: 'AVAILABLE' | 'LOW_STOCK' | 'OUT_OF_STOCK'
          max_portions: int
          limiting_ingredient: str | None
          message: str
          shortages: List of deficient ingredients if requested_quantity cannot be satisfied
        """
        menu_item = menu_items_collection.find_one({"_id": to_object_id(menu_item_id)})
        if not menu_item:
            raise ValueError("Menu item not found")

        recipes = list(recipes_collection.find({"menu_item_id": menu_item["_id"]}))

        # If no recipe BOM is mapped (e.g. Starters or untracked items)
        if not recipes:
            return {
                "menu_item_id": str(menu_item["_id"]),
                "menu_item_name": menu_item["name"],
                "has_recipe": False,
                "status": "AVAILABLE",
                "max_portions": 9999,
                "limiting_ingredient": None,
                "message": "Available",
                "shortages": [],
                "details": [],
            }

        servings_list: List[Tuple[int, str]] = []
        details = []
        shortages = []

        for r in recipes:
            ing = ingredients_collection.find_one({"_id": r["ingredient_id"]})
            if not ing:
                continue

            avail = ing["available_quantity"].to_decimal() if hasattr(ing["available_quantity"], "to_decimal") else Decimal(str(ing["available_quantity"]))
            req_per_unit = r["quantity_required"].to_decimal() if hasattr(r["quantity_required"], "to_decimal") else Decimal(str(r["quantity_required"]))
            rec_unit = r.get("unit") or ing["unit"]
            converted_req_single = convert_quantity(req_per_unit, rec_unit, ing["unit"])

            if converted_req_single <= 0:
                servings = 0
            else:
                servings = int(avail // converted_req_single)

            servings_list.append((servings, ing["name"]))

            # Check requested quantity sufficiency
            converted_req_total = converted_req_single * Decimal(str(requested_quantity))
            if avail < converted_req_total:
                shortages.append({
                    "ingredient_id": str(ing["_id"]),
                    "ingredient_name": ing["name"],
                    "required": float(converted_req_total),
                    "available": float(avail),
                    "shortage": float(converted_req_total - avail),
                    "unit": ing["unit"],
                })

            details.append({
                "ingredient_id": str(ing["_id"]),
                "ingredient_name": ing["name"],
                "available": float(avail),
                "required_per_serving": float(converted_req_single),
                "unit": ing["unit"],
                "possible_servings": servings,
            })

        if not servings_list:
            min_servings, limiting_ing = 0, None
        else:
            min_servings, limiting_ing = min(servings_list, key=lambda x: x[0])

        if min_servings == 0:
            status = "OUT_OF_STOCK"
            if len(shortages) == 1:
                message = f"{shortages[0]['ingredient_name']} stock is unavailable. (Required: {shortages[0]['required']} {shortages[0]['unit']}, Available: {shortages[0]['available']} {shortages[0]['unit']})"
            else:
                message = f"{limiting_ing} stock is unavailable."
        elif min_portions_val := min_servings:
            if min_portions_val <= 5:
                status = "LOW_STOCK"
                message = f"Only {min_portions_val} plates available"
            else:
                status = "AVAILABLE"
                message = "Available"
        else:
            status = "AVAILABLE"
            message = "Available"

        return {
            "menu_item_id": str(menu_item["_id"]),
            "menu_item_name": menu_item["name"],
            "has_recipe": True,
            "status": status,
            "max_portions": min_servings,
            "limiting_ingredient": limiting_ing,
            "message": message,
            "shortages": shortages,
            "details": details,
        }

    @staticmethod
    def get_all_availability() -> Dict[str, Any]:
        """
        Returns a mapping of menu_item_id -> availability data for all active menu items.
        """
        items = list(menu_items_collection.find({"is_available": True}))
        availability_map: Dict[str, Any] = {}
        for itm in items:
            item_id = str(itm["_id"])
            availability_map[item_id] = RecipeService.calculate_item_availability(item_id, requested_quantity=1)
        return availability_map

    @staticmethod
    def check_availability(menu_item_id: str, order_quantity: int = 1) -> Tuple[bool, Optional[str]]:
        """
        Multiplies recipe requirement by order_quantity and verifies against stock.
        """
        res = RecipeService.calculate_item_availability(menu_item_id, requested_quantity=order_quantity)
        if res["shortages"]:
            shortage_strs = [
                f"{s['ingredient_name']} (Required: {s['required']} {s['unit']}, Available: {s['available']} {s['unit']})"
                for s in res["shortages"]
            ]
            return False, f"Insufficient stock for {', '.join(shortage_strs)}"
        return True, None

    @staticmethod
    def validate_cart(items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates all recipe ingredient requirements across an entire cart/order
        and detects if any ingredient has insufficient inventory.
        Items format: [{'menu_item_id': str, 'quantity': int}]
        """
        if not items:
            return {"is_valid": True, "message": "Cart is empty", "shortages": []}

        # Aggregate total required stock per ingredient
        total_required: Dict[str, Dict[str, Any]] = {}

        for itm in items:
            menu_item_id = str(itm.get("menu_item_id") or itm.get("item_id"))
            qty = int(itm.get("quantity", 1))
            if qty <= 0:
                continue

            recipes = list(recipes_collection.find({"menu_item_id": to_object_id(menu_item_id)}))
            for r in recipes:
                ing = ingredients_collection.find_one({"_id": r["ingredient_id"]})
                if not ing:
                    continue

                ing_id = str(ing["_id"])
                req_per_unit = r["quantity_required"].to_decimal() if hasattr(r["quantity_required"], "to_decimal") else Decimal(str(r["quantity_required"]))
                rec_unit = r.get("unit") or ing["unit"]
                converted_single = convert_quantity(req_per_unit, rec_unit, ing["unit"])
                total_for_item = converted_single * Decimal(str(qty))

                if ing_id not in total_required:
                    avail = ing["available_quantity"].to_decimal() if hasattr(ing["available_quantity"], "to_decimal") else Decimal(str(ing["available_quantity"]))
                    total_required[ing_id] = {
                        "ingredient_id": ing_id,
                        "ingredient_name": ing["name"],
                        "unit": ing["unit"],
                        "available": avail,
                        "required": Decimal("0"),
                    }
                total_required[ing_id]["required"] += total_for_item

        shortages = []
        for ing_id, info in total_required.items():
            if info["available"] < info["required"]:
                shortages.append({
                    "ingredient_id": ing_id,
                    "ingredient_name": info["ingredient_name"],
                    "required": float(info["required"]),
                    "available": float(info["available"]),
                    "shortage": float(info["required"] - info["available"]),
                    "unit": info["unit"],
                })

        if shortages:
            shortage_lines = [
                f"{s['ingredient_name']}: Required {s['required']} {s['unit']}, Available {s['available']} {s['unit']}, Shortage {s['shortage']} {s['unit']}"
                for s in shortages
            ]
            return {
                "is_valid": False,
                "message": f"Insufficient inventory for: {'; '.join(shortage_lines)}",
                "shortages": shortages,
            }

        return {
            "is_valid": True,
            "message": "All required ingredients are available in stock",
            "shortages": [],
        }
