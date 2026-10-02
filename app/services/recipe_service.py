"""
Recipe Service for mapping Menu Items to Ingredients, calculating live availability,
validating stock requirements, and calculating food cost percentage.
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
from app.utils.units import convert_quantity, are_units_compatible, normalize_unit


class RecipeService:

    @staticmethod
    def create_recipe(menu_item_id_or_data: Any, data: Optional[Any] = None) -> Dict[str, Any]:
        """
        Accepts either (menu_item_id, data) or (data) with data.menu_item_id.
        Validates unit compatibility between recipe and raw ingredient stock unit.
        """
        if data is None:
            data = menu_item_id_or_data
            menu_item_id = get_field(data, "menu_item_id")
        else:
            menu_item_id = menu_item_id_or_data

        # If batch creation of ingredients passed as a list
        ingredients_list = get_field(data, "ingredients")
        if ingredients_list and isinstance(ingredients_list, list):
            results = []
            for item_data in ingredients_list:
                rec = RecipeService.create_recipe(menu_item_id, item_data)
                results.append(rec)
            return {
                "menu_item_id": str(menu_item_id),
                "ingredients": results,
                "count": len(results),
            }

        ingredient_id = get_field(data, "ingredient_id")
        quantity_required = get_field(data, "quantity_required")
        unit = get_field(data, "unit")
        is_optional = get_field(data, "is_optional", False)

        if not menu_item_id or not ingredient_id:
            raise ValueError("menu_item_id and ingredient_id are required")

        menu_item = menu_items_collection.find_one({"_id": to_object_id(menu_item_id)})
        if not menu_item:
            raise ValueError("Menu item not found")

        ingredient = ingredients_collection.find_one({"_id": to_object_id(ingredient_id)})
        if not ingredient:
            raise ValueError("Ingredient not found")

        norm_recipe_unit = normalize_unit(unit) if unit else ingredient.get("unit")
        norm_ing_unit = normalize_unit(ingredient.get("unit"))

        # Unit compatibility check
        if not are_units_compatible(norm_recipe_unit, norm_ing_unit):
            raise ValueError(
                f"Incompatible units: Recipe unit '{unit}' cannot be converted to ingredient stock unit '{ingredient.get('unit')}'"
            )

        # Validate with Domain Entity
        entity = RecipeEntity(
            menu_item_id=str(menu_item_id),
            ingredient_id=str(ingredient_id),
            quantity_required=quantity_required,
            unit=norm_recipe_unit,
            is_optional=is_optional,
        )

        existing = recipes_collection.find_one({
            "menu_item_id": to_object_id(entity.menu_item_id),
            "ingredient_id": to_object_id(entity.ingredient_id),
        })

        if existing:
            update_fields: Dict[str, Any] = {
                "quantity_required": decimal128(entity.quantity_required),
                "is_optional": entity.is_optional,
            }
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
            "unit": norm_recipe_unit,
            "is_optional": entity.is_optional,
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
                avail = ing.get("available_quantity") or ing.get("current_stock")
                item["available_stock"] = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail or 0))
                cost = ing.get("cost_per_unit") or Decimal("0")
                item["cost_per_unit"] = cost.to_decimal() if hasattr(cost, "to_decimal") else Decimal(str(cost))
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
            avail = ing.get("available_quantity") or ing.get("current_stock")
            item["available_stock"] = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail or 0))
            cost = ing.get("cost_per_unit") or Decimal("0")
            item["cost_per_unit"] = cost.to_decimal() if hasattr(cost, "to_decimal") else Decimal(str(cost))
        return item

    @staticmethod
    def update_recipe(recipe_id: str, data: Any) -> Dict[str, Any]:
        qty = get_field(data, "quantity_required")
        unit = get_field(data, "unit")
        is_optional = get_field(data, "is_optional")

        update_dict: Dict[str, Any] = {}
        if qty is not None:
            dec_qty = Decimal(str(qty))
            if dec_qty <= 0:
                raise ValueError("Recipe quantity required must be greater than zero")
            update_dict["quantity_required"] = decimal128(dec_qty)
        if unit:
            recipe = recipes_collection.find_one({"_id": to_object_id(recipe_id)})
            if recipe:
                ing = ingredients_collection.find_one({"_id": recipe["ingredient_id"]})
                if ing and not are_units_compatible(unit, ing.get("unit")):
                    raise ValueError(f"Unit '{unit}' is incompatible with ingredient stock unit '{ing.get('unit')}'")
            update_dict["unit"] = normalize_unit(unit)
        if is_optional is not None:
            update_dict["is_optional"] = bool(is_optional)

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
    def update_menu_recipe(menu_item_id: str, data: Any) -> Any:
        """
        Updates or sets the recipe for a menu item.
        Accepts list of ingredients or dict with ingredients list, or single ingredient spec.
        """
        menu_item = menu_items_collection.find_one({"_id": to_object_id(menu_item_id)})
        if not menu_item:
            raise ValueError("Menu item not found")

        ingredients_list = None
        if isinstance(data, list):
            ingredients_list = data
        elif isinstance(data, dict):
            ingredients_list = data.get("ingredients")
        elif hasattr(data, "ingredients"):
            ingredients_list = getattr(data, "ingredients")

        if ingredients_list is not None:
            # Replace all recipe mappings
            recipes_collection.delete_many({"menu_item_id": to_object_id(menu_item_id)})
            for ing in ingredients_list:
                RecipeService.create_recipe(menu_item_id, ing)
            return RecipeService.get_by_menu_item(menu_item_id)

        # Single ingredient update / upsert
        RecipeService.create_recipe(menu_item_id, data)
        return RecipeService.get_by_menu_item(menu_item_id)

    @staticmethod
    def delete_all_by_menu_item(menu_item_id: str) -> Dict[str, Any]:
        """Deletes all recipe ingredient mappings for the given menu item."""
        recipes_collection.delete_many({"menu_item_id": to_object_id(menu_item_id)})
        return {"message": "Recipe deleted successfully"}

    # =========================================================================
    # Food Costing & Recipe Analytics (Section 19)
    # =========================================================================

    @staticmethod
    def calculate_recipe_cost(menu_item_id: str) -> Dict[str, Any]:
        """
        Calculates the estimated cost of a recipe and the Food Cost Percentage.
        Formula:
          Total Recipe Cost = Sum(quantity_required * cost_per_unit)
          Food Cost Percentage = (Total Recipe Cost / Selling Price) * 100
        """
        menu_item = menu_items_collection.find_one({"_id": to_object_id(menu_item_id)})
        if not menu_item:
            raise ValueError("Menu item not found")

        recipes = list(recipes_collection.find({"menu_item_id": menu_item["_id"]}))
        selling_price = menu_item["price"].to_decimal() if hasattr(menu_item["price"], "to_decimal") else Decimal(str(menu_item["price"]))

        if not recipes:
            return {
                "menu_item_id": str(menu_item["_id"]),
                "menu_item_name": menu_item["name"],
                "selling_price": float(selling_price),
                "total_recipe_cost": 0.0,
                "food_cost_percentage": 0.0,
                "profit_margin": float(selling_price),
                "breakdown": [],
                "has_recipe": False,
            }

        total_cost = Decimal("0")
        breakdown = []

        for r in recipes:
            ing = ingredients_collection.find_one({"_id": r["ingredient_id"]})
            if not ing:
                continue

            req_qty = r["quantity_required"].to_decimal() if hasattr(r["quantity_required"], "to_decimal") else Decimal(str(r["quantity_required"]))
            rec_unit = r.get("unit") or ing["unit"]
            converted_qty = convert_quantity(req_qty, rec_unit, ing["unit"])

            cost_per_unit = ing["cost_per_unit"].to_decimal() if hasattr(ing["cost_per_unit"], "to_decimal") else Decimal(str(ing["cost_per_unit"]))
            item_cost = converted_qty * cost_per_unit
            total_cost += item_cost

            breakdown.append({
                "ingredient_id": str(ing["_id"]),
                "ingredient_name": ing["name"],
                "quantity_required": float(req_qty),
                "unit": rec_unit,
                "converted_quantity": float(converted_qty),
                "stock_unit": ing["unit"],
                "cost_per_unit": float(cost_per_unit),
                "total_cost": float(item_cost),
            })

        food_cost_pct = (total_cost / selling_price * Decimal("100")) if selling_price > 0 else Decimal("0")
        profit_margin = selling_price - total_cost

        return {
            "menu_item_id": str(menu_item["_id"]),
            "menu_item_name": menu_item["name"],
            "selling_price": float(selling_price),
            "total_recipe_cost": float(total_cost),
            "food_cost_percentage": round(float(food_cost_pct), 2),
            "profit_margin": float(profit_margin),
            "breakdown": breakdown,
            "has_recipe": True,
        }

    @staticmethod
    def get_all_recipes_cost_analytics() -> List[Dict[str, Any]]:
        items = list(menu_items_collection.find({"is_available": True}))
        results = []
        for it in items:
            cost_info = RecipeService.calculate_recipe_cost(str(it["_id"]))
            results.append(cost_info)
        return results

    # =========================================================================
    # Live Stock Availability & Cart Validation
    # =========================================================================

    @staticmethod
    def calculate_item_availability(menu_item_id: str, requested_quantity: int = 1) -> Dict[str, Any]:
        """
        Determines the real-time stock availability state of a menu item.
        Handles inventory_tracking_enabled flag for Starters/Special items.
        """
        menu_item = menu_items_collection.find_one({"_id": to_object_id(menu_item_id)})
        if not menu_item:
            raise ValueError("Menu item not found")

        # Starter / Special Item rule: if tracking is disabled, item is always available
        tracking_enabled = menu_item.get("inventory_tracking_enabled", True)
        if not tracking_enabled:
            return {
                "menu_item_id": str(menu_item["_id"]),
                "menu_item_name": menu_item["name"],
                "has_recipe": False,
                "inventory_tracking_enabled": False,
                "status": "AVAILABLE",
                "is_available": True,
                "max_possible_servings": 9999,
                "max_portions": 9999,
                "limiting_ingredient": None,
                "message": "Available (Inventory tracking not enabled)",
                "shortages": [],
                "details": [],
            }

        recipes = list(recipes_collection.find({"menu_item_id": menu_item["_id"]}))

        # If no recipe mapped
        if not recipes:
            return {
                "menu_item_id": str(menu_item["_id"]),
                "menu_item_name": menu_item["name"],
                "has_recipe": False,
                "inventory_tracking_enabled": True,
                "status": "AVAILABLE",
                "is_available": True,
                "max_possible_servings": 9999,
                "max_portions": 9999,
                "limiting_ingredient": None,
                "message": "Available (Recipe not configured)",
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

            avail = ing.get("available_quantity") or ing.get("current_stock") or Decimal("0")
            avail_dec = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail))

            req_per_unit = r["quantity_required"].to_decimal() if hasattr(r["quantity_required"], "to_decimal") else Decimal(str(r["quantity_required"]))
            rec_unit = r.get("unit") or ing["unit"]
            converted_req_single = convert_quantity(req_per_unit, rec_unit, ing["unit"])

            if converted_req_single <= 0:
                servings = 0
            else:
                servings = int(avail_dec // converted_req_single)

            servings_list.append((servings, ing["name"]))

            # Check requested quantity sufficiency
            converted_req_total = converted_req_single * Decimal(str(requested_quantity))
            if avail_dec < converted_req_total:
                shortages.append({
                    "ingredient_id": str(ing["_id"]),
                    "ingredient_name": ing["name"],
                    "required": float(converted_req_total),
                    "available": float(avail_dec),
                    "shortage": float(converted_req_total - avail_dec),
                    "unit": ing["unit"],
                })

            details.append({
                "ingredient_id": str(ing["_id"]),
                "ingredient_name": ing["name"],
                "available": float(avail_dec),
                "required_per_serving": float(converted_req_single),
                "unit": ing["unit"],
                "possible_servings": servings,
            })

        if not servings_list:
            min_servings, limiting_ing = 0, None
        else:
            min_servings, limiting_ing = min(servings_list, key=lambda x: x[0])

        if min_servings == 0 or len(shortages) > 0:
            status = "OUT_OF_STOCK"
            if len(shortages) == 1:
                s = shortages[0]
                message = f"{menu_item['name']} cannot be prepared. {s['ingredient_name']} stock is insufficient. Required: {s['required']} {s['unit']}, Available: {s['available']} {s['unit']}."
            else:
                shortage_names = [f"{s['ingredient_name']} (Req: {s['required']} {s['unit']}, Avail: {s['available']} {s['unit']})" for s in shortages]
                message = f"{menu_item['name']} cannot be prepared. Insufficient stock for: {', '.join(shortage_names)}."
        elif min_servings <= 5:
            status = "LOW_STOCK"
            message = f"Only {min_servings} portions available"
        else:
            status = "AVAILABLE"
            message = "Available"

        return {
            "menu_item_id": str(menu_item["_id"]),
            "menu_item_name": menu_item["name"],
            "has_recipe": True,
            "inventory_tracking_enabled": True,
            "status": status,
            "is_available": (status == "AVAILABLE" or (status == "LOW_STOCK" and len(shortages) == 0)),
            "max_possible_servings": min_servings,
            "max_portions": min_servings,
            "limiting_ingredient": limiting_ing,
            "message": message,
            "shortages": shortages,
            "details": details,
        }

    @staticmethod
    def get_all_availability() -> Dict[str, Any]:
        items = list(menu_items_collection.find({"is_available": True}))
        availability_map: Dict[str, Any] = {}
        for itm in items:
            item_id = str(itm["_id"])
            availability_map[item_id] = RecipeService.calculate_item_availability(item_id, requested_quantity=1)
        return availability_map

    @staticmethod
    def check_availability(menu_item_id: str, order_quantity: int = 1) -> Tuple[bool, Optional[str]]:
        res = RecipeService.calculate_item_availability(menu_item_id, requested_quantity=order_quantity)
        if res.get("shortages"):
            return False, res["message"]
        return True, None

    @staticmethod
    def validate_cart(items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregates all recipe ingredient requirements across an entire cart/order
        and detects if any ingredient has insufficient inventory.
        """
        if not items:
            return {"is_valid": True, "message": "Cart is empty", "shortages": []}

        total_required: Dict[str, Dict[str, Any]] = {}

        for itm in items:
            menu_item_id = str(itm.get("menu_item_id") or itm.get("item_id"))
            qty = int(itm.get("quantity", 1))
            if qty <= 0:
                continue

            menu_item = menu_items_collection.find_one({"_id": to_object_id(menu_item_id)})
            if not menu_item:
                continue

            # Skip items where inventory tracking is disabled
            if not menu_item.get("inventory_tracking_enabled", True):
                continue

            recipes = list(recipes_collection.find({"menu_item_id": menu_item["_id"]}))
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
                    avail = ing.get("available_quantity") or ing.get("current_stock") or Decimal("0")
                    avail_dec = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail))
                    total_required[ing_id] = {
                        "ingredient_id": ing_id,
                        "ingredient_name": ing["name"],
                        "unit": ing["unit"],
                        "available": avail_dec,
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
                f"{s['ingredient_name']} stock is insufficient. Required: {s['required']} {s['unit']}, Available: {s['available']} {s['unit']}"
                for s in shortages
            ]
            return {
                "is_valid": False,
                "message": f"Order cannot be prepared. {'; '.join(shortage_lines)}",
                "shortages": shortages,
            }

        return {
            "is_valid": True,
            "message": "All required ingredients are available in stock",
            "shortages": [],
        }
