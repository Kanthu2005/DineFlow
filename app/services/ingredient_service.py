"""
Ingredient and Inventory Service.
Manages raw materials, stock movement tracking, and low-stock alerts.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.repositories.inventory_repository import IngredientRepository
from app.repositories.menu_repository import MenuRepository
from app.models.entities import Ingredient as IngredientEntity
from app.services.common import to_object_id, decimal128, now_utc, serialize_document, serialize_documents, get_field
from app.database.mongodb import recipes_collection, menu_items_collection
from app.utils.units import convert_quantity

repo = IngredientRepository()


class IngredientService:

    @staticmethod
    def create_ingredient(data: Any) -> Dict[str, Any]:
        name = get_field(data, "name")
        unit = get_field(data, "unit")
        available_qty = get_field(data, "available_quantity", 0)
        min_stock = get_field(data, "minimum_stock_level", 0)
        cost = get_field(data, "cost_per_unit", 0)
        supplier = get_field(data, "supplier_name")
        is_active = get_field(data, "is_active", True)

        # Validate with Domain Entity
        entity = IngredientEntity(
            name=name,
            unit=unit,
            available_quantity=available_qty,
            minimum_stock_level=min_stock,
            cost_per_unit=cost,
            supplier_name=supplier,
            is_active=is_active,
        )

        existing = repo.find_by_name(entity.name)
        if existing:
            raise ValueError(f"Ingredient '{entity.name}' already exists")

        doc = {
            "name": entity.name,
            "unit": entity.unit,
            "available_quantity": decimal128(entity.available_quantity),
            "minimum_stock_level": decimal128(entity.minimum_stock_level),
            "cost_per_unit": decimal128(entity.cost_per_unit),
            "supplier_name": entity.supplier_name,
            "is_active": entity.is_active,
            "created_at": now_utc(),
        }

        created = repo.insert(doc)

        # Record initial stock purchase/opening stock movement if available > 0
        if entity.available_quantity > 0:
            repo.record_movement({
                "ingredient_id": to_object_id(created["id"]),
                "movement_type": "PURCHASE",
                "quantity": decimal128(entity.available_quantity),
                "reference_type": "INITIAL_STOCK",
                "reference_id": None,
                "created_by": "SYSTEM",
                "created_at": now_utc(),
            })

        return created

    @staticmethod
    def get_ingredients() -> List[Dict[str, Any]]:
        return repo.find_all(sort_field="name", sort_dir=1)

    @staticmethod
    def get_active_ingredients() -> List[Dict[str, Any]]:
        return repo.find_active()

    @staticmethod
    def get_ingredient(ingredient_id: str) -> Dict[str, Any]:
        item = repo.find_by_id(ingredient_id)
        if not item:
            raise ValueError("Ingredient not found")
        return item

    @staticmethod
    def update_ingredient(ingredient_id: str, data: Any) -> Dict[str, Any]:
        update_dict = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.copy()

        # Reject negative values
        for field in ["available_quantity", "minimum_stock_level", "cost_per_unit"]:
            if field in update_dict and update_dict[field] is not None:
                dec = Decimal(str(update_dict[field]))
                if dec < 0:
                    raise ValueError(f"{field} cannot be negative")
                update_dict[field] = decimal128(dec)

        updated = repo.update(ingredient_id, update_dict)
        if not updated:
            raise ValueError("Ingredient not found")
        return updated

    @staticmethod
    def update_stock(ingredient_id: str, quantity: Decimal | float | int | str, movement_type: str = "MANUAL_ADJUSTMENT", reference_type: Optional[str] = None, reference_id: Optional[str] = None, created_by: str = "SYSTEM") -> Dict[str, Any]:
        dec_qty = Decimal(str(quantity))
        item = IngredientService.get_ingredient(ingredient_id)
        current_stock = item["available_quantity"].to_decimal() if hasattr(item["available_quantity"], "to_decimal") else Decimal(str(item["available_quantity"]))

        new_stock = current_stock + dec_qty
        if new_stock < 0:
            raise ValueError(f"Insufficient stock for {item['name']}. Current: {current_stock}, Requested deduction: {abs(dec_qty)}")

        updated = repo.increment_stock(ingredient_id, dec_qty)

        # Record movement
        repo.record_movement({
            "ingredient_id": to_object_id(ingredient_id),
            "movement_type": movement_type,
            "quantity": decimal128(abs(dec_qty)),
            "reference_type": reference_type,
            "reference_id": reference_id,
            "created_by": created_by,
            "created_at": now_utc(),
        })

        return updated

    @staticmethod
    def get_stock_status(ingredient_id: str) -> Dict[str, Any]:
        ingredient = IngredientService.get_ingredient(ingredient_id)
        avail = Decimal(str(ingredient["available_quantity"]))
        min_lvl = Decimal(str(ingredient["minimum_stock_level"]))

        entity = IngredientEntity(
            name=ingredient["name"],
            unit=ingredient["unit"],
            available_quantity=avail,
            minimum_stock_level=min_lvl,
            cost_per_unit=Decimal(str(ingredient["cost_per_unit"])),
        )

        return {
            "ingredient_id": ingredient_id,
            "ingredient_name": ingredient["name"],
            "unit": ingredient["unit"],
            "available_quantity": avail,
            "minimum_stock_level": min_lvl,
            "status": entity.get_alert_level(),
        }

    @staticmethod
    def get_low_stock_ingredients() -> List[Dict[str, Any]]:
        raw_items = repo.find_low_stock()
        results = []
        for item in raw_items:
            avail = Decimal(str(item["available_quantity"]))
            min_lvl = Decimal(str(item["minimum_stock_level"]))
            entity = IngredientEntity(
                name=item["name"],
                unit=item["unit"],
                available_quantity=avail,
                minimum_stock_level=min_lvl,
                cost_per_unit=Decimal(str(item["cost_per_unit"])),
            )
            item["alert_level"] = entity.get_alert_level()
            results.append(item)
        return results

    @staticmethod
    def estimate_serving_capacity(menu_item_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Calculates how many servings of each menu item can be prepared based on current stock.
        Formula: min(floor(available_quantity / required_quantity)) across all recipe ingredients.
        """
        query = {"_id": to_object_id(menu_item_id)} if menu_item_id else {"is_available": True}
        menu_items = list(menu_items_collection.find(query))

        capacity_reports = []
        for item in menu_items:
            recipes = list(recipes_collection.find({"menu_item_id": item["_id"]}))
            if not recipes:
                capacity_reports.append({
                    "menu_item_id": str(item["_id"]),
                    "menu_item_name": item["name"],
                    "possible_servings": 9999,  # No raw ingredients tracked
                    "limiting_ingredient": None,
                    "details": [],
                })
                continue

            possible_servings_list = []
            details = []
            for r in recipes:
                ing = repo.find_by_id(r["ingredient_id"])
                if not ing:
                    continue
                avail_qty = Decimal(str(ing["available_quantity"]))
                recipe_qty = Decimal(str(r["quantity_required"]))
                # Normalize units if recipe specifies unit
                rec_unit = r.get("unit") or ing["unit"]
                converted_req = convert_quantity(recipe_qty, rec_unit, ing["unit"])

                if converted_req <= 0:
                    servings = 0
                else:
                    servings = int(avail_qty // converted_req)

                possible_servings_list.append((servings, ing["name"]))
                details.append({
                    "ingredient_id": str(ing["id"]),
                    "ingredient_name": ing["name"],
                    "available": avail_qty,
                    "required_per_serving": converted_req,
                    "unit": ing["unit"],
                    "possible_servings": servings,
                })

            if possible_servings_list:
                min_servings, limiting_ing = min(possible_servings_list, key=lambda x: x[0])
            else:
                min_servings, limiting_ing = 0, None

            capacity_reports.append({
                "menu_item_id": str(item["_id"]),
                "menu_item_name": item["name"],
                "possible_servings": min_servings,
                "limiting_ingredient": limiting_ing,
                "details": details,
            })

        return capacity_reports
