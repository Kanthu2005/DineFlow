"""
Reset and seed script for DineFlow Restaurant:
1. Resets tables to clean names: T1, T2, T3, T4, T5, T6, T7, T8, T9, T10, T11, T12
2. Clears old test orders, tickets, invoices, and payments for a spotless billing section
3. Seeds the centralized raw materials inventory (Rice, Chicken, Mutton, Paneer, Vegetables, Oil, Onion, Tomato)
4. Configures Veg & Non-Veg dishes with exact BOM recipes, and Starters with 0 recipe deduction
5. Initializes stock movement audit history
"""

import sys
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database.mongodb import (
    db,
    restaurant_tables_collection,
    orders_collection,
    order_items_collection,
    kitchen_tickets_collection,
    invoices_collection,
    payments_collection,
    menu_categories_collection,
    menu_items_collection,
    ingredients_collection,
    recipes_collection,
    stock_movements_collection,
    reservations_collection,
    order_activity_logs_collection,
)
from app.services.common import now_utc, decimal128, to_object_id

# 1. Clean Simple Tables: T1 through T12
STANDARD_TABLES = [
    {"table_number": "T1", "capacity": 2, "location": "MAIN_DINING", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T2", "capacity": 2, "location": "MAIN_DINING", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T3", "capacity": 4, "location": "MAIN_DINING", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T4", "capacity": 4, "location": "MAIN_DINING", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T5", "capacity": 4, "location": "MAIN_DINING", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T6", "capacity": 4, "location": "MAIN_DINING", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T7", "capacity": 6, "location": "FAMILY_SECTION", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T8", "capacity": 6, "location": "FAMILY_SECTION", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T9", "capacity": 8, "location": "FAMILY_SECTION", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T10", "capacity": 2, "location": "WINDOW_BAY", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T11", "capacity": 4, "location": "OUTDOOR_PATIO", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T12", "capacity": 6, "location": "OUTDOOR_PATIO", "status": "AVAILABLE", "is_active": True},
]

# 2. Centralized Main Inventory Raw Materials
RAW_MATERIALS = [
    {"name": "Rice", "unit": "KG", "current_stock": Decimal("50.00"), "low_stock_threshold": Decimal("10.00"), "cost_per_unit": Decimal("60.00")},
    {"name": "Chicken", "unit": "KG", "current_stock": Decimal("30.00"), "low_stock_threshold": Decimal("5.00"), "cost_per_unit": Decimal("180.00")},
    {"name": "Mutton", "unit": "KG", "current_stock": Decimal("20.00"), "low_stock_threshold": Decimal("5.00"), "cost_per_unit": Decimal("600.00")},
    {"name": "Paneer", "unit": "KG", "current_stock": Decimal("15.00"), "low_stock_threshold": Decimal("3.00"), "cost_per_unit": Decimal("320.00")},
    {"name": "Vegetables", "unit": "KG", "current_stock": Decimal("40.00"), "low_stock_threshold": Decimal("8.00"), "cost_per_unit": Decimal("40.00")},
    {"name": "Oil", "unit": "LITRE", "current_stock": Decimal("20.00"), "low_stock_threshold": Decimal("5.00"), "cost_per_unit": Decimal("130.00")},
    {"name": "Onion", "unit": "KG", "current_stock": Decimal("30.00"), "low_stock_threshold": Decimal("5.00"), "cost_per_unit": Decimal("30.00")},
    {"name": "Tomato", "unit": "KG", "current_stock": Decimal("25.00"), "low_stock_threshold": Decimal("5.00"), "cost_per_unit": Decimal("25.00")},
]

# 3. Categories and Dishes with Recipes
MENU_DATA = [
    {
        "category": "Non-Veg",
        "description": "Authentic chicken and mutton biryanis using tracked warehouse ingredients",
        "items": [
            {
                "name": "Chicken Biryani",
                "price": Decimal("220.00"),
                "preparation_time": 20,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
                "description": "Dum cooked basmati rice with marinated chicken pieces and fragrant Indian spices.",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
                    {"ingredient": "Chicken", "qty": Decimal("150"), "unit": "GRAM"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
                ]
            },
            {
                "name": "Mutton Biryani",
                "price": Decimal("340.00"),
                "preparation_time": 25,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600&auto=format&fit=crop&q=80",
                "description": "Slow-cooked tender mutton layered with saffron basmati rice and royal aroma.",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
                    {"ingredient": "Mutton", "qty": Decimal("180"), "unit": "GRAM"},
                    {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("60"), "unit": "GRAM"},
                ]
            },
            {
                "name": "Butter Chicken",
                "price": Decimal("260.00"),
                "preparation_time": 20,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop&q=80",
                "description": "Tender chicken cooked in a rich, buttery tomato gravy with aromatic spices.",
                "recipe": [
                    {"ingredient": "Chicken", "qty": Decimal("180"), "unit": "GRAM"},
                    {"ingredient": "Tomato", "qty": Decimal("100"), "unit": "GRAM"},
                    {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
                ]
            },
            {
                "name": "Kashmiri Mutton Rogan Josh",
                "price": Decimal("360.00"),
                "preparation_time": 25,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1545247181-516773cae754?w=600&auto=format&fit=crop&q=80",
                "description": "Slow cooked succulent mutton in traditional Kashmiri spices and rich gravy.",
                "recipe": [
                    {"ingredient": "Mutton", "qty": Decimal("180"), "unit": "GRAM"},
                    {"ingredient": "Tomato", "qty": Decimal("80"), "unit": "GRAM"},
                    {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("60"), "unit": "GRAM"},
                ]
            }
        ]
    },
    {
        "category": "Veg",
        "description": "Flavorful vegetarian and paneer specialties using tracked main warehouse stock",
        "items": [
            {
                "name": "Veg Biryani",
                "price": Decimal("180.00"),
                "preparation_time": 15,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1645177628172-a94c1f96e6db?w=600&auto=format&fit=crop&q=80",
                "description": "Fragrant basmati rice layered with garden fresh vegetables, mint, and fried onions.",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
                    {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "GRAM"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
                ]
            },
            {
                "name": "Paneer Biryani",
                "price": Decimal("210.00"),
                "preparation_time": 18,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
                "description": "Golden marinated paneer cubes layered with saffron basmati rice and caramelized onions.",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
                    {"ingredient": "Paneer", "qty": Decimal("120"), "unit": "GRAM"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
                ]
            },
            {
                "name": "Paneer Butter Masala",
                "price": Decimal("220.00"),
                "preparation_time": 15,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80",
                "description": "Soft cottage cheese in a silky, creamy tomato and butter gravy.",
                "recipe": [
                    {"ingredient": "Paneer", "qty": Decimal("150"), "unit": "GRAM"},
                    {"ingredient": "Tomato", "qty": Decimal("100"), "unit": "GRAM"},
                    {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
                ]
            },
            {
                "name": "Dal Makhani",
                "price": Decimal("180.00"),
                "preparation_time": 15,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
                "description": "Slow cooked black lentils simmered overnight with butter and fresh cream.",
                "recipe": [
                    {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "GRAM"},
                    {"ingredient": "Tomato", "qty": Decimal("60"), "unit": "GRAM"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("40"), "unit": "GRAM"},
                ]
            }
        ]
    },
    {
        "category": "Starters",
        "description": "Crispy appetizers and tandoori bites that do not consume main raw materials by default",
        "items": [
            {
                "name": "Chicken Starter",
                "price": Decimal("190.00"),
                "preparation_time": 12,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80",
                "description": "Crispy fried spiced chicken chunks tossed with curry leaves and green chillies. (No main stock deduction)",
                "recipe": []  # 0 inventory deduction
            },
            {
                "name": "Chicken 65 Starter",
                "price": Decimal("200.00"),
                "preparation_time": 12,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
                "description": "Spicy, deep-fried chicken marinated in South Indian spices. (No main stock deduction)",
                "recipe": []  # 0 inventory deduction
            },
            {
                "name": "Paneer Tikka Starter",
                "price": Decimal("180.00"),
                "preparation_time": 12,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=600&auto=format&fit=crop&q=80",
                "description": "Char-grilled cottage cheese skewers with bell peppers and tandoori glaze. (No main stock deduction)",
                "recipe": []  # 0 inventory deduction
            },
            {
                "name": "Veg Crispy Starter",
                "price": Decimal("150.00"),
                "preparation_time": 10,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80",
                "description": "Crunchy seasonal vegetables tossed in sweet and tangy oriental sauce. (No main stock deduction)",
                "recipe": []  # 0 inventory deduction
            },
            {
                "name": "Crispy Corn Starter",
                "price": Decimal("160.00"),
                "preparation_time": 10,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80",
                "description": "Golden fried American sweet corn kernels tossed with spices and spring onion. (No main stock deduction)",
                "recipe": []  # 0 inventory deduction
            }
        ]
    }
]


def clean_and_seed():
    print("==================================================")
    print("  DineFlow: Cleaning & Seeding Complete System")
    print("==================================================")

    # 1. Clear Old Billing, Invoices, Payments, Orders & Tickets
    print("\n[1/5] Clearing old billing, orders, and tickets...")
    invoices_collection.delete_many({})
    payments_collection.delete_many({})
    orders_collection.delete_many({})
    order_items_collection.delete_many({})
    kitchen_tickets_collection.delete_many({})
    reservations_collection.delete_many({})
    print("  -> Invoices, Payments, Orders, OrderItems, Tickets wiped cleanly.")

    # 2. Reset Tables to Clean Names: T1, T2, T3 ... T12
    print("\n[2/5] Resetting tables to clean format: T1, T2, T3 ... T12...")
    restaurant_tables_collection.delete_many({})
    for tbl in STANDARD_TABLES:
        doc = {**tbl, "created_at": now_utc()}
        restaurant_tables_collection.insert_one(doc)
        print(f"  [+] Table {tbl['table_number']} created ({tbl['capacity']} seats, {tbl['location']})")

    # 3. Seed Central Raw Materials Inventory
    print("\n[3/5] Setting up centralized main inventory...")
    stock_movements_collection.delete_many({})
    ing_map = {}
    for raw in RAW_MATERIALS:
        existing = ingredients_collection.find_one({"name": raw["name"]})
        doc = {
            "name": raw["name"],
            "unit": raw["unit"],
            "current_stock": decimal128(raw["current_stock"]),
            "available_quantity": decimal128(raw["current_stock"]),
            "low_stock_threshold": decimal128(raw["low_stock_threshold"]),
            "minimum_stock_level": decimal128(raw["low_stock_threshold"]),
            "cost_per_unit": decimal128(raw["cost_per_unit"]),
            "is_active": True,
            "created_at": now_utc(),
        }
        if existing:
            ingredients_collection.update_one({"_id": existing["_id"]}, {"$set": doc})
            ing_id = existing["_id"]
            print(f"  [OK] Updated raw stock: {raw['name']} = {raw['current_stock']} {raw['unit']}")
        else:
            res = ingredients_collection.insert_one(doc)
            ing_id = res.inserted_id
            print(f"  [+] Inserted raw stock: {raw['name']} = {raw['current_stock']} {raw['unit']}")

        ing_map[raw["name"]] = ing_id

        # Record initial PURCHASE movement for audit trail
        stock_movements_collection.insert_one({
            "ingredient_id": ing_id,
            "ingredient_name": raw["name"],
            "unit": raw["unit"],
            "quantity": decimal128(raw["current_stock"]),
            "movement_type": "PURCHASE",
            "reference_type": "INITIAL_WAREHOUSE_SETUP",
            "reference_id": "INIT-001",
            "reason": "Centralized main warehouse initial stock provision",
            "created_by": "SYSTEM_ADMIN",
            "created_at": now_utc(),
        })

    # 4. Configure Categories & Dishes with BOM Recipes
    print("\n[4/5] Setting up Menu Categories & Recipe Mapping...")
    for cat_data in MENU_DATA:
        cat_name = cat_data["category"]
        existing_cat = menu_categories_collection.find_one({"name": cat_name})
        if existing_cat:
            cat_id = existing_cat["_id"]
            menu_categories_collection.update_one({"_id": cat_id}, {"$set": {"description": cat_data["description"]}})
            print(f"  [OK] Category exists: {cat_name}")
        else:
            res = menu_categories_collection.insert_one({
                "name": cat_name,
                "description": cat_data["description"],
                "created_at": now_utc(),
            })
            cat_id = res.inserted_id
            print(f"  [+] Created Category: {cat_name}")

        for dish in cat_data["items"]:
            dish_name = dish["name"]
            existing_dish = menu_items_collection.find_one({"name": dish_name})
            dish_doc = {
                "name": dish_name,
                "category_id": cat_id,
                "category_name": cat_name,
                "price": decimal128(dish["price"]),
                "preparation_time": dish["preparation_time"],
                "is_vegetarian": dish["is_vegetarian"],
                "is_available": True,
                "image_url": dish["image_url"],
                "description": dish["description"],
                "created_at": now_utc(),
            }
            if existing_dish:
                menu_items_collection.update_one({"_id": existing_dish["_id"]}, {"$set": dish_doc})
                dish_id = existing_dish["_id"]
                print(f"    [OK] Updated dish: {dish_name} (INR {dish['price']})")
            else:
                res = menu_items_collection.insert_one(dish_doc)
                dish_id = res.inserted_id
                print(f"    [+] Inserted dish: {dish_name} (INR {dish['price']})")

            # BOM Recipe mapping
            recipes_collection.delete_many({"menu_item_id": dish_id})
            recipe_items = dish.get("recipe", [])
            if recipe_items:
                for r in recipe_items:
                    raw_id = ing_map.get(r["ingredient"])
                    if raw_id:
                        recipes_collection.insert_one({
                            "menu_item_id": dish_id,
                            "ingredient_id": raw_id,
                            "quantity_required": decimal128(r["qty"]),
                            "unit": r["unit"],
                            "created_at": now_utc(),
                        })
                        print(f"      -> BOM: {r['qty']} {r['unit']} {r['ingredient']}")
            else:
                print(f"      -> 0 Inventory Recipe (Starter exemption)")

    print("\n[5/5] Seed completed cleanly and successfully!")
    print("==================================================")


if __name__ == "__main__":
    clean_and_seed()
