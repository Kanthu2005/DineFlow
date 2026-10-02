"""
Comprehensive Sample Menu Seed Script for DineFlow.
Seeds realistic, accurately categorized dishes with correct names, prices, descriptions,
prep times, high-definition images, veg/non-veg flags, and BOM recipe linkages.
"""

import sys
import io
from decimal import Decimal
from pathlib import Path

# Fix Windows console encoding for UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database.mongodb import (
    db,
    menu_categories_collection,
    menu_items_collection,
    ingredients_collection,
    recipes_collection,
)
from app.services.common import now_utc, decimal128

CATEGORIES_DATA = [
    {
        "name": "Veg Starters",
        "description": "Crispy appetizers, kebabs, and tandoori bites made from fresh paneer, vegetables, and aromatic spices.",
    },
    {
        "name": "Non-Veg Starters",
        "description": "Succulent charcoal-grilled tikkas, crispy chicken specials, and spiced minced lamb kebabs.",
    },
    {
        "name": "Veg Main Course",
        "description": "Rich paneer gravies, slow-cooked lentils, and aromatic vegetable dum biryani.",
    },
    {
        "name": "Non-Veg Main Course",
        "description": "Authentic Hyderabadi chicken biryani, butter chicken, and slow-braised Kashmiri mutton rogan josh.",
    },
    {
        "name": "Breads & Rice",
        "description": "Freshly baked clay oven naans, rotis, and fragrant cumin basmati rice.",
    },
    {
        "name": "Desserts & Beverages",
        "description": "Traditional sweet treats, creamy Alphonso mango lassi, and chilled refreshments.",
    },
]

DISHES_DATA = [
    # ----------------- Veg Starters -----------------
    {
        "name": "Paneer Tikka",
        "category": "Veg Starters",
        "price": Decimal("220.00"),
        "preparation_time": 12,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80",
        "description": "Fresh cottage cheese cubes marinated in spiced hung yogurt, mustard oil, and carom seeds, skewered with bell peppers and char-grilled in a clay oven.",
        "recipe": [],
    },
    {
        "name": "Hara Bhara Kebab",
        "category": "Veg Starters",
        "price": Decimal("190.00"),
        "preparation_time": 10,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
        "description": "Crisp pan-seared patties prepared with blanched spinach, mashed potatoes, green peas, and ground spices, centered with roasted cashew nuts.",
        "recipe": [],
    },
    {
        "name": "Crispy Corn Pepper Salt",
        "category": "Veg Starters",
        "price": Decimal("180.00"),
        "preparation_time": 10,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80",
        "description": "Golden fried American sweet corn kernels tossed with crushed black pepper, spring onions, diced capsicum, and roasted cumin.",
        "recipe": [],
    },
    {
        "name": "Veg Manchurian Dry",
        "category": "Veg Starters",
        "price": Decimal("190.00"),
        "preparation_time": 12,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
        "description": "Crispy minced vegetable dumplings tossed with fresh garlic, ginger, chopped scallions, and Indo-Chinese soya chili glaze.",
        "recipe": [],
    },
    {
        "name": "Tandoori Soya Chaap",
        "category": "Veg Starters",
        "price": Decimal("210.00"),
        "preparation_time": 14,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=600&auto=format&fit=crop&q=80",
        "description": "Tender soya chaap marinated in Kashmiri red chili paste, hung curd, and secret tandoori spices, char-grilled to a smoky finish.",
        "recipe": [],
    },

    # ----------------- Non-Veg Starters -----------------
    {
        "name": "Chicken Tikka",
        "category": "Non-Veg Starters",
        "price": Decimal("260.00"),
        "preparation_time": 15,
        "is_vegetarian": False,
        "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80",
        "description": "Succulent boneless chicken morsels steeped in spiced yogurt, smoked paprika, and lime, roasted in a traditional charcoal clay tandoor.",
        "recipe": [],
    },
    {
        "name": "Chicken 65",
        "category": "Non-Veg Starters",
        "price": Decimal("240.00"),
        "preparation_time": 12,
        "is_vegetarian": False,
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
        "description": "Authentic Chennai-style crispy fried chicken bites tossed with fresh curry leaves, whole red chillies, ginger, and garlic.",
        "recipe": [],
    },
    {
        "name": "Mutton Seekh Kebab",
        "category": "Non-Veg Starters",
        "price": Decimal("340.00"),
        "preparation_time": 16,
        "is_vegetarian": False,
        "image_url": "https://images.unsplash.com/photo-1545247181-516773cae754?w=600&auto=format&fit=crop&q=80",
        "description": "Minced lamb blended with mint, coriander, ginger-garlic paste, and royal garam masala, mounted on skewers and flame grilled.",
        "recipe": [],
    },
    {
        "name": "Tandoori Murgh (Half)",
        "category": "Non-Veg Starters",
        "price": Decimal("290.00"),
        "preparation_time": 18,
        "is_vegetarian": False,
        "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80",
        "description": "Bone-in tender chicken marinated overnight with Kashmiri deggi mirch, hung curd, and freshly ground whole spices, fire-roasted in the tandoor.",
        "recipe": [],
    },
    {
        "name": "Chilli Chicken Dry",
        "category": "Non-Veg Starters",
        "price": Decimal("250.00"),
        "preparation_time": 12,
        "is_vegetarian": False,
        "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop&q=80",
        "description": "Crispy batter-fried boneless chicken cubes tossed with sliced onions, crunchy capsicum, green chillies, and savory dark soy sauce.",
        "recipe": [],
    },

    # ----------------- Veg Main Course -----------------
    {
        "name": "Paneer Butter Masala",
        "category": "Veg Main Course",
        "price": Decimal("240.00"),
        "preparation_time": 15,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80",
        "description": "Soft malai paneer cubes simmered in a velvety, mildly sweet and savory tomato-cashew nut gravy with a dollop of white butter.",
        "recipe": [
            {"ingredient": "Paneer", "qty": Decimal("150"), "unit": "GRAM"},
            {"ingredient": "Tomato", "qty": Decimal("100"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Dal Makhani",
        "category": "Veg Main Course",
        "price": Decimal("200.00"),
        "preparation_time": 15,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
        "description": "Traditional slow-cooked whole black lentils and red kidney beans simmered overnight on low embers with butter and dairy cream.",
        "recipe": [
            {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "GRAM"},
            {"ingredient": "Tomato", "qty": Decimal("60"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("40"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Kadhai Paneer",
        "category": "Veg Main Course",
        "price": Decimal("230.00"),
        "preparation_time": 15,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=600&auto=format&fit=crop&q=80",
        "description": "Fresh cottage cheese batons tossed with bell peppers and roasted freshly-crushed coriander seeds and dry red chillies.",
        "recipe": [
            {"ingredient": "Paneer", "qty": Decimal("140"), "unit": "GRAM"},
            {"ingredient": "Vegetables", "qty": Decimal("80"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Royal Veg Dum Biryani",
        "category": "Veg Main Course",
        "price": Decimal("210.00"),
        "preparation_time": 18,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1645177628172-a94c1f96e6db?w=600&auto=format&fit=crop&q=80",
        "description": "Fragrant long-grain aged basmati rice layered with garden vegetables, mint, saffron milk, and fried onions, sealed and slow cooked.",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
            {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },

    # ----------------- Non-Veg Main Course -----------------
    {
        "name": "Hyderabadi Chicken Dum Biryani",
        "category": "Non-Veg Main Course",
        "price": Decimal("260.00"),
        "preparation_time": 20,
        "is_vegetarian": False,
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
        "description": "Aged basmati rice infused with whole royal spices and layered with tender marinated chicken pieces, slow-cooked in sealed handi.",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
            {"ingredient": "Chicken", "qty": Decimal("160"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Butter Chicken (Murgh Makhani)",
        "category": "Non-Veg Main Course",
        "price": Decimal("290.00"),
        "preparation_time": 18,
        "is_vegetarian": False,
        "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop&q=80",
        "description": "Tandoori shredded chicken steeped in a rich, satin-smooth tomato, cashew, and cream gravy finished with crushed kasuri methi.",
        "recipe": [
            {"ingredient": "Chicken", "qty": Decimal("180"), "unit": "GRAM"},
            {"ingredient": "Tomato", "qty": Decimal("100"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Kashmiri Mutton Rogan Josh",
        "category": "Non-Veg Main Course",
        "price": Decimal("360.00"),
        "preparation_time": 25,
        "is_vegetarian": False,
        "image_url": "https://images.unsplash.com/photo-1545247181-516773cae754?w=600&auto=format&fit=crop&q=80",
        "description": "Succulent cuts of lamb braised with gravy flavored with garlic, ginger, and aromatic spices including cloves, bay leaves, and Kashmiri chili.",
        "recipe": [
            {"ingredient": "Mutton", "qty": Decimal("180"), "unit": "GRAM"},
            {"ingredient": "Tomato", "qty": Decimal("80"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("60"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Chicken Tikka Masala",
        "category": "Non-Veg Main Course",
        "price": Decimal("280.00"),
        "preparation_time": 18,
        "is_vegetarian": False,
        "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop&q=80",
        "description": "Charcoal grilled boneless chicken tikka cooked in an aromatic, hearty spiced onion, tomato, and bell pepper gravy.",
        "recipe": [
            {"ingredient": "Chicken", "qty": Decimal("160"), "unit": "GRAM"},
            {"ingredient": "Tomato", "qty": Decimal("80"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Royal Mutton Dum Biryani",
        "category": "Non-Veg Main Course",
        "price": Decimal("370.00"),
        "preparation_time": 25,
        "is_vegetarian": False,
        "image_url": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600&auto=format&fit=crop&q=80",
        "description": "Tender, juicy mutton pieces layered with long-grain saffron basmati rice, clarified ghee, and roasted whole spices.",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
            {"ingredient": "Mutton", "qty": Decimal("180"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("60"), "unit": "GRAM"},
        ],
    },

    # ----------------- Breads & Rice -----------------
    {
        "name": "Butter Garlic Naan",
        "category": "Breads & Rice",
        "price": Decimal("65.00"),
        "preparation_time": 6,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600&auto=format&fit=crop&q=80",
        "description": "Fluffy leavened flatbread freshly baked in tandoor, topped with minced garlic, fresh coriander, and brushed with melted butter.",
        "recipe": [],
    },
    {
        "name": "Butter Tandoori Roti",
        "category": "Breads & Rice",
        "price": Decimal("35.00"),
        "preparation_time": 5,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600&auto=format&fit=crop&q=80",
        "description": "Crisp whole wheat bread baked on the clay oven walls and finished with golden butter.",
        "recipe": [],
    },
    {
        "name": "Jeera Rice",
        "category": "Breads & Rice",
        "price": Decimal("140.00"),
        "preparation_time": 8,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
        "description": "Aromatic basmati rice tempered with roasted cumin seeds, fresh coriander, and pure ghee.",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("200"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("15"), "unit": "ML"},
        ],
    },

    {
        "name": "Veg Fried Rice",
        "category": "Breads & Rice",
        "price": Decimal("180.00"),
        "preparation_time": 10,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=600&auto=format&fit=crop&q=80",
        "description": "Wok-tossed long-grain basmati rice with finely chopped carrots, French beans, baby corn, spring onions, and a touch of light soy.",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("200"), "unit": "GRAM"},
            {"ingredient": "Vegetables", "qty": Decimal("80"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("15"), "unit": "ML"},
        ],
    },
    {
        "name": "Schezwan Veg Noodles",
        "category": "Breads & Rice",
        "price": Decimal("190.00"),
        "preparation_time": 12,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=600&auto=format&fit=crop&q=80",
        "description": "Stir-fried noodles loaded with crunchy vegetables tossed in spicy in-house fiery Schezwan chili garlic sauce.",
        "recipe": [],
    },

    # ----------------- Desserts & Beverages -----------------
    {
        "name": "Gulab Jamun with Rabdi",
        "category": "Desserts & Beverages",
        "price": Decimal("120.00"),
        "preparation_time": 5,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1605197586548-932f146a782b?w=600&auto=format&fit=crop&q=80",
        "description": "Warm, melt-in-mouth cottage cheese and mawa dumplings dipped in saffron rose syrup, paired with chilled rich rabdi.",
        "recipe": [],
    },
    {
        "name": "Kulfi Falooda",
        "category": "Desserts & Beverages",
        "price": Decimal("140.00"),
        "preparation_time": 5,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1579954115545-a95591f28bfc?w=600&auto=format&fit=crop&q=80",
        "description": "Traditional rich malai kulfi slices topped with silky falooda sev, sweet basil sabja seeds, and fragrant rose syrup.",
        "recipe": [],
    },
    {
        "name": "Royal Mango Lassi",
        "category": "Desserts & Beverages",
        "price": Decimal("90.00"),
        "preparation_time": 5,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
        "description": "Rich and creamy churned yogurt shake with sweet Alphonso mango pulp, green cardamom, and slivered pistachios.",
        "recipe": [],
    },
    {
        "name": "Special Masala Chai",
        "category": "Desserts & Beverages",
        "price": Decimal("45.00"),
        "preparation_time": 5,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80",
        "description": "Freshly brewed full-cream milk tea infused with crushed green cardamom, cloves, cinnamon, and fresh ginger.",
        "recipe": [],
    },
    {
        "name": "Spiced Butter Milk (Chaas)",
        "category": "Desserts & Beverages",
        "price": Decimal("50.00"),
        "preparation_time": 4,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=600&auto=format&fit=crop&q=80",
        "description": "Cool churned buttermilk seasoned with roasted cumin powder, black salt, crushed mint leaves, and green chillies.",
        "recipe": [],
    },
    {
        "name": "Fresh Lime Soda (Sweet & Salt)",
        "category": "Desserts & Beverages",
        "price": Decimal("70.00"),
        "preparation_time": 4,
        "is_vegetarian": True,
        "image_url": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=600&auto=format&fit=crop&q=80",
        "description": "Chilled sparkling soda with freshly squeezed lime juice, rock salt, mint sprigs, and sugar syrup.",
        "recipe": [],
    },
]


def seed_menu():
    print("==================================================")
    print("  DineFlow: Seeding Realistic Sample Menu")
    print("==================================================")

    # Clean up test/incomplete dishes with empty categories or names like 'samosa'
    menu_items_collection.delete_many({
        "name": {
            "$in": [
                "samosa",
                "Veg Crispy Starter",
                "Crispy Corn Starter",
                "Chicken Starter",
                "Chicken 65 Starter",
                "Paneer Tikka Starter",
                "Seasonal Fish Curry",
                "Out of Season Mango Lassi",
                "Mutton Biryani",
            ]
        }
    })

    # Fetch ingredient map
    ing_map = {}
    for ing in ingredients_collection.find({}):
        ing_map[ing["name"]] = ing["_id"]

    # 1. Ensure Categories exist
    cat_map = {}
    print("\n[1/3] Setting up Categories...")
    for cat in CATEGORIES_DATA:
        existing = menu_categories_collection.find_one({"name": cat["name"]})
        if existing:
            cat_id = existing["_id"]
            menu_categories_collection.update_one({"_id": cat_id}, {"$set": {"description": cat["description"]}})
            print(f"  [OK] Category: {cat['name']}")
        else:
            res = menu_categories_collection.insert_one({
                "name": cat["name"],
                "description": cat["description"],
                "created_at": now_utc(),
            })
            cat_id = res.inserted_id
            print(f"  [+] Created Category: {cat['name']}")
        cat_map[cat["name"]] = cat_id

    # Clean up obsolete legacy categories that have been consolidated
    legacy_cats = ["Biryani", "Breads", "Veg", "Non-Veg", "Starters", "Rice & Noodles", "Desserts", "Beverages"]
    for l_name in legacy_cats:
        c = menu_categories_collection.find_one({"name": l_name})
        if c:
            # Reassign any dishes in legacy cat to appropriate new category
            target_cat_name = "Non-Veg Main Course" if l_name in ["Biryani", "Non-Veg"] else "Breads & Rice"
            if l_name == "Starters":
                target_cat_name = "Veg Starters"
            elif l_name in ["Desserts", "Beverages"]:
                target_cat_name = "Desserts & Beverages"
            menu_items_collection.update_many(
                {"category_id": c["_id"]},
                {"$set": {"category_id": cat_map[target_cat_name], "category_name": target_cat_name}}
            )
            menu_categories_collection.delete_one({"_id": c["_id"]})
            print(f"  [-] Cleaned legacy category: {l_name}")

    # 2. Seed Dishes
    print("\n[2/3] Seeding Dishes with accurate details...")
    seeded_count = 0
    for dish in DISHES_DATA:
        cat_id = cat_map.get(dish["category"])
        if not cat_id:
            print(f"  [!] Missing category for {dish['name']}")
            continue

        doc = {
            "name": dish["name"],
            "category_id": cat_id,
            "category_name": dish["category"],
            "price": decimal128(dish["price"]),
            "preparation_time": dish["preparation_time"],
            "is_vegetarian": dish["is_vegetarian"],
            "is_available": True,
            "image_url": dish["image_url"],
            "description": dish["description"],
            "updated_at": now_utc(),
        }

        existing = menu_items_collection.find_one({"name": dish["name"]})
        if existing:
            menu_items_collection.update_one({"_id": existing["_id"]}, {"$set": doc})
            dish_id = existing["_id"]
            print(f"  [OK] Updated: {dish['name']} (₹{dish['price']}) - {dish['category']}")
        else:
            doc["created_at"] = now_utc()
            res = menu_items_collection.insert_one(doc)
            dish_id = res.inserted_id
            print(f"  [+] Added: {dish['name']} (₹{dish['price']}) - {dish['category']}")

        # Map Recipe
        recipe_items = dish.get("recipe", [])
        recipes_collection.delete_many({"menu_item_id": dish_id})
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
        seeded_count += 1

    print(f"\n[3/3] Successfully seeded {seeded_count} complete menu items across {len(cat_map)} categories!")
    print("==================================================")


if __name__ == "__main__":
    seed_menu()
