"""
Seed script for Restaurant Recipe-Based Inventory Stock Management.
Initializes:
1. Standard Menu Categories: Veg, Non-Veg, Starters
2. Centralized Main Inventory Raw Materials (Rice, Chicken, Mutton, Paneer, Vegetables, Oil, Onion, Tomato)
3. Dishes with BOM recipes for Veg and Non-Veg items
4. Starters dishes with NO recipes (0 inventory deduction rule)
"""

import sys
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database.mongodb import (
    db,
    menu_categories_collection,
    menu_items_collection,
    ingredients_collection,
    recipes_collection,
    stock_movements_collection,
)
from app.services.common import now_utc, decimal128, to_object_id

RAW_MATERIALS = [
    {"name": "Rice", "unit": "KG", "available_quantity": Decimal("50.00"), "minimum_stock_level": Decimal("10.00"), "cost_per_unit": Decimal("60.00")},
    {"name": "Chicken", "unit": "KG", "available_quantity": Decimal("30.00"), "minimum_stock_level": Decimal("5.00"), "cost_per_unit": Decimal("180.00")},
    {"name": "Mutton", "unit": "KG", "available_quantity": Decimal("20.00"), "minimum_stock_level": Decimal("5.00"), "cost_per_unit": Decimal("600.00")},
    {"name": "Paneer", "unit": "KG", "available_quantity": Decimal("15.00"), "minimum_stock_level": Decimal("3.00"), "cost_per_unit": Decimal("320.00")},
    {"name": "Vegetables", "unit": "KG", "available_quantity": Decimal("40.00"), "minimum_stock_level": Decimal("8.00"), "cost_per_unit": Decimal("40.00")},
    {"name": "Oil", "unit": "LITRE", "available_quantity": Decimal("20.00"), "minimum_stock_level": Decimal("5.00"), "cost_per_unit": Decimal("130.00")},
    {"name": "Onion", "unit": "KG", "available_quantity": Decimal("30.00"), "minimum_stock_level": Decimal("5.00"), "cost_per_unit": Decimal("30.00")},
    {"name": "Tomato", "unit": "KG", "available_quantity": Decimal("25.00"), "minimum_stock_level": Decimal("5.00"), "cost_per_unit": Decimal("25.00")},
]

CATEGORIES_DATA = [
    {
        "name": "Biryani",
        "description": "Rich authentic biryanis and royal rice specialties",
        "items": [
            {
                "name": "Chicken Biryani",
                "price": Decimal("250.00"),
                "preparation_time": 25,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
                "description": "Dum cooked basmati rice with marinated chicken pieces and fragrant Indian herbs.",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("250"), "unit": "G"},
                    {"ingredient": "Chicken", "qty": Decimal("150"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "G"},
                ]
            },
            {
                "name": "Mutton Biryani",
                "price": Decimal("320.00"),
                "preparation_time": 30,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600&auto=format&fit=crop&q=80",
                "description": "Slow-cooked tender mutton layered with saffron basmati rice and royal spices.",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("250"), "unit": "G"},
                    {"ingredient": "Mutton", "qty": Decimal("180"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("60"), "unit": "G"},
                ]
            },
            {
                "name": "Veg Biryani",
                "price": Decimal("180.00"),
                "preparation_time": 20,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1645177628172-a94c1f96e6db?w=600&auto=format&fit=crop&q=80",
                "description": "Fragrant basmati rice layered with garden fresh vegetables, mint, and fried onions.",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("250"), "unit": "G"},
                    {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "G"},
                ]
            },
            {
                "name": "Paneer Biryani",
                "price": Decimal("210.00"),
                "preparation_time": 18,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
                "description": "Golden marinated paneer cubes simmered with saffron basmati rice and caramelized onions.",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("250"), "unit": "G"},
                    {"ingredient": "Paneer", "qty": Decimal("120"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "G"},
                ]
            },
        ]
    },
    {
        "name": "Starters",
        "description": "Crispy appetizers and tandoori skewers (Non-inventory tracked by default)",
        "items": [
            {
                "name": "Chicken Starter",
                "price": Decimal("240.00"),
                "preparation_time": 12,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
                "description": "Crispy spiced chicken starter tossed with southern curry leaves and cracked pepper.",
                "recipe": []  # No inventory deduction
            },
            {
                "name": "Paneer Tikka Starter",
                "price": Decimal("220.00"),
                "preparation_time": 12,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=600&auto=format&fit=crop&q=80",
                "description": "Clay oven grilled paneer tikka with bell peppers and tangy mint chutney.",
                "recipe": []  # No inventory deduction
            },
            {
                "name": "Crispy Corn Starter",
                "price": Decimal("190.00"),
                "preparation_time": 10,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=600&auto=format&fit=crop&q=80",
                "description": "Golden battered sweet corn kernels wok-tossed with crushed black pepper and lime.",
                "recipe": []  # No inventory deduction
            },
        ]
    },
]


def seed_inventory_and_recipes():
    print("Seeding Main Inventory Raw Materials...")
    ingredient_id_map = {}

    for mat in RAW_MATERIALS:
        existing = ingredients_collection.find_one({"name": mat["name"]})
        if existing:
            # Update to ensure specified starting stock
            ingredients_collection.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "unit": mat["unit"],
                        "available_quantity": decimal128(mat["available_quantity"]),
                        "minimum_stock_level": decimal128(mat["minimum_stock_level"]),
                        "cost_per_unit": decimal128(mat["cost_per_unit"]),
                        "is_active": True,
                    }
                }
            )
            ingredient_id_map[mat["name"]] = existing["_id"]
            print(f"  [OK] Ingredient updated: {mat['name']} -> {mat['available_quantity']} {mat['unit']}")
        else:
            doc = {
                "name": mat["name"],
                "unit": mat["unit"],
                "available_quantity": decimal128(mat["available_quantity"]),
                "minimum_stock_level": decimal128(mat["minimum_stock_level"]),
                "cost_per_unit": decimal128(mat["cost_per_unit"]),
                "is_active": True,
                "created_at": now_utc(),
            }
            res = ingredients_collection.insert_one(doc)
            ingredient_id_map[mat["name"]] = res.inserted_id
            # Opening stock movement
            stock_movements_collection.insert_one({
                "ingredient_id": res.inserted_id,
                "movement_type": "PURCHASE",
                "quantity": decimal128(mat["available_quantity"]),
                "unit": mat["unit"],
                "reference_type": "INITIAL_STOCK",
                "reference_id": "INIT",
                "created_by": "SYSTEM",
                "created_at": now_utc(),
            })
            print(f"  [+] Ingredient inserted: {mat['name']} -> {mat['available_quantity']} {mat['unit']}")

    print("\nSeeding Core Categories & BOM Recipes...")
    for cat_data in CATEGORIES_DATA:
        cat_name = cat_data["name"]
        cat_doc = menu_categories_collection.find_one({"name": cat_name})
        if not cat_doc:
            cat_res = menu_categories_collection.insert_one({
                "name": cat_name,
                "description": cat_data["description"],
                "created_at": now_utc(),
            })
            cat_id = cat_res.inserted_id
            print(f"  [+] Category created: {cat_name}")
        else:
            cat_id = cat_doc["_id"]
            print(f"  [OK] Category exists: {cat_name}")

        for dish in cat_data["items"]:
            dish_name = dish["name"]
            existing_dish = menu_items_collection.find_one({"name": dish_name})
            dish_fields = {
                "name": dish_name,
                "category_id": cat_id,
                "price": decimal128(dish["price"]),
                "preparation_time": dish["preparation_time"],
                "is_vegetarian": dish["is_vegetarian"],
                "is_available": True,
                "image_url": dish["image_url"],
                "description": dish["description"],
                "created_at": now_utc(),
            }

            if existing_dish:
                menu_items_collection.update_one(
                    {"_id": existing_dish["_id"]},
                    {"$set": dish_fields}
                )
                item_id = existing_dish["_id"]
                print(f"    [OK] Dish updated: {dish_name}")
            else:
                res_dish = menu_items_collection.insert_one(dish_fields)
                item_id = res_dish.inserted_id
                print(f"    [+] Dish inserted: {dish_name}")

            # Map BOM recipes
            recipe_items = dish.get("recipe", [])
            if recipe_items:
                # Remove existing recipes to re-seed cleanly
                recipes_collection.delete_many({"menu_item_id": item_id})
                for r in recipe_items:
                    ing_id = ingredient_id_map.get(r["ingredient"])
                    if ing_id:
                        recipes_collection.insert_one({
                            "menu_item_id": item_id,
                            "ingredient_id": ing_id,
                            "quantity_required": decimal128(r["qty"]),
                            "unit": r["unit"],
                            "created_at": now_utc(),
                        })
                        print(f"      -> BOM: {r['qty']} {r['unit']} of {r['ingredient']}")
            else:
                # Dish has NO recipe (e.g. Starter item -> 0 inventory deduction)
                recipes_collection.delete_many({"menu_item_id": item_id})
                print(f"      -> Non-inventory item (No recipe mapped, 0 stock deduction)")

    print("\n[SUCCESS] Recipe-based inventory seed completed successfully!")


if __name__ == "__main__":
    seed_inventory_and_recipes()
