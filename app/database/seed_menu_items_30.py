"""
DineFlow - 30 Core Menu Items Seeder
Seeds and updates the exact 30 realistic restaurant menu items across 7 core categories:
1. Starters
2. Biryani
3. Main Course
4. Breads
5. Rice & Noodles
6. Desserts
7. Beverages
"""

import sys
from decimal import Decimal
from bson import ObjectId

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database.mongodb import menu_categories_collection, menu_items_collection
from app.services.common import now_utc, decimal128

CATEGORIES = [
    {
        "name": "Starters",
        "description": "Appetizers, crispy bites, and sizzling skewers to kickstart your dining experience.",
    },
    {
        "name": "Biryani",
        "description": "Fragrant long-grain basmati rice layered with rich spices and choice proteins.",
    },
    {
        "name": "Main Course",
        "description": "Hearty, aromatic curries and gravies prepared with authentic traditional recipes.",
    },
    {
        "name": "Breads",
        "description": "Freshly baked tandoori naans, layered parathas, and traditional rotis.",
    },
    {
        "name": "Rice & Noodles",
        "description": "Wok-tossed fried rice and flavorful Indo-Chinese noodles cooked to perfection.",
    },
    {
        "name": "Desserts",
        "description": "Delectable traditional sweets and chilled sweet treats to end your meal.",
    },
    {
        "name": "Beverages",
        "description": "Cooling yogurts, chilled drinks, coffees, and freshly brewed Indian chai.",
    },
]

MENU_ITEMS_30 = [
    # --- Starters (15-25 mins) ---
    {
        "name": "Paneer Tikka",
        "category": "Starters",
        "type": "Veg",
        "price": Decimal("220"),
        "preparation_time": 20,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Succulent cubes of paneer marinated in spiced yogurt and grilled over hot tandoor coals with crunchy bell peppers.",
        "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Chicken 65",
        "category": "Starters",
        "type": "Non-Veg",
        "price": Decimal("240"),
        "preparation_time": 20,
        "is_available": True,
        "is_vegetarian": False,
        "description": "Crispy deep-fried chicken tossed in a spicy, tangy South Indian tempering of curry leaves, mustard seeds, and red chili.",
        "image_url": "https://images.unsplash.com/photo-1610057099431-d73a1c9d2f2f?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Chilli Chicken",
        "category": "Starters",
        "type": "Non-Veg",
        "price": Decimal("250"),
        "preparation_time": 20,
        "is_available": True,
        "is_vegetarian": False,
        "description": "Tender chicken chunks wok-tossed with green chilies, bell peppers, soy sauce, and scallions in signature Indo-Chinese style.",
        "image_url": "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Gobi Manchurian",
        "category": "Starters",
        "type": "Veg",
        "price": Decimal("180"),
        "preparation_time": 18,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Crispy battered cauliflower florets glazed in a garlic-infused sweet and spicy Indo-Chinese Manchurian sauce.",
        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Chicken Lollipop",
        "category": "Starters",
        "type": "Non-Veg",
        "price": Decimal("280"),
        "preparation_time": 22,
        "is_available": True,
        "is_vegetarian": False,
        "description": "Frenched chicken winglets coated in seasoned spicy red batter, fried until crunchy and served with spicy garlic dip.",
        "image_url": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=600&auto=format&fit=crop&q=80",
    },

    # --- Biryani (20-30 mins) ---
    {
        "name": "Chicken Dum Biryani",
        "category": "Biryani",
        "type": "Non-Veg",
        "price": Decimal("250"),
        "preparation_time": 25,
        "is_available": True,
        "is_vegetarian": False,
        "description": "Authentic dum biryani slow-cooked with bone-in chicken, fragrant basmati rice, caramelized onions, mint, and saffron.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Chicken Fry Piece Biryani",
        "category": "Biryani",
        "type": "Non-Veg",
        "price": Decimal("280"),
        "preparation_time": 25,
        "is_available": True,
        "is_vegetarian": False,
        "description": "Aromatic spiced biryani rice crowned with fiery, crisp pan-fried chicken morsels and roasted cashews.",
        "image_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Mutton Biryani",
        "category": "Biryani",
        "type": "Non-Veg",
        "price": Decimal("320"),
        "preparation_time": 30,
        "is_available": True,
        "is_vegetarian": False,
        "description": "Royal slow-cooked mutton pieces infused with rich shahi spices, layered with aged basmati rice and pure ghee.",
        "image_url": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Egg Biryani",
        "category": "Biryani",
        "type": "Egg",
        "price": Decimal("190"),
        "preparation_time": 20,
        "is_available": True,
        "is_vegetarian": False,
        "description": "Golden roasted boiled eggs seasoned with biryani spices and nestled in fragrant saffron-scented dum basmati rice.",
        "image_url": "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Veg Biryani",
        "category": "Biryani",
        "type": "Veg",
        "price": Decimal("180"),
        "preparation_time": 20,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Garden vegetables, green peas, and paneer cubes dum-cooked with aromatic spices, kewra water, and basmati rice.",
        "image_url": "https://images.unsplash.com/photo-1642821373181-696a54913e93?w=600&auto=format&fit=crop&q=80",
    },

    # --- Main Course (15-25 mins) ---
    {
        "name": "Paneer Butter Masala",
        "category": "Main Course",
        "type": "Veg",
        "price": Decimal("220"),
        "preparation_time": 20,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Soft cottage cheese simmered in a silky tomato, cashew, and butter gravy flavored with dried fenugreek leaves (kasoori methi).",
        "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Kadai Paneer",
        "category": "Main Course",
        "type": "Veg",
        "price": Decimal("210"),
        "preparation_time": 20,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Paneer cubes and crunchy bell peppers cooked in a robust, freshly pounded coriander and red chili kadai masala.",
        "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Butter Chicken",
        "category": "Main Course",
        "type": "Non-Veg",
        "price": Decimal("280"),
        "preparation_time": 25,
        "is_available": True,
        "is_vegetarian": False,
        "description": "Tandoori grilled chicken morsels enveloped in a rich, mildly spiced tomato butter gravy finished with fresh cream.",
        "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Chicken Curry",
        "category": "Main Course",
        "type": "Non-Veg",
        "price": Decimal("260"),
        "preparation_time": 22,
        "is_available": True,
        "is_vegetarian": False,
        "description": "Homestyle chicken simmered in an onion-tomato gravy infused with ground coriander, cumin, ginger, and garlic.",
        "image_url": "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Mutton Curry",
        "category": "Main Course",
        "type": "Non-Veg",
        "price": Decimal("320"),
        "preparation_time": 25,
        "is_available": True,
        "is_vegetarian": False,
        "description": "Tender pieces of mutton slow-cooked in a dark, robust spiced gravy with cinnamon, cloves, and whole black cardamom.",
        "image_url": "https://images.unsplash.com/photo-1545247181-516773cae754?w=600&auto=format&fit=crop&q=80",
    },

    # --- Breads (5-15 mins) ---
    {
        "name": "Butter Naan",
        "category": "Breads",
        "type": "Veg",
        "price": Decimal("50"),
        "preparation_time": 8,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Soft and pillowy clay-oven baked refined flour flatbread lavishly brushed with melted butter.",
        "image_url": "https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Garlic Naan",
        "category": "Breads",
        "type": "Veg",
        "price": Decimal("70"),
        "preparation_time": 10,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Tandoori naan topped with roasted minced garlic cloves and fresh cilantro, brushed with warm butter.",
        "image_url": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Tandoori Roti",
        "category": "Breads",
        "type": "Veg",
        "price": Decimal("35"),
        "preparation_time": 6,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Wholesome stoneground whole wheat bread baked crisp on the clay walls of the tandoor oven.",
        "image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Laccha Paratha",
        "category": "Breads",
        "type": "Veg",
        "price": Decimal("60"),
        "preparation_time": 10,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Crispy, flaky whole wheat flatbread rolled with distinctive spiral layers and cooked on tawa with ghee.",
        "image_url": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
    },

    # --- Rice & Noodles (10-20 mins) ---
    {
        "name": "Veg Fried Rice",
        "category": "Rice & Noodles",
        "type": "Veg",
        "price": Decimal("180"),
        "preparation_time": 15,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Fragrant steamed rice wok-tossed with finely chopped carrots, French beans, cabbage, garlic, and light soy seasoning.",
        "image_url": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Chicken Fried Rice",
        "category": "Rice & Noodles",
        "type": "Non-Veg",
        "price": Decimal("220"),
        "preparation_time": 18,
        "is_available": True,
        "is_vegetarian": False,
        "description": "High-flame wok-tossed rice with shredded tender chicken breast, scrambled egg, scallions, and toasted sesame oil.",
        "image_url": "https://images.unsplash.com/photo-1600891964599-f61ba0e24092?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Egg Fried Rice",
        "category": "Rice & Noodles",
        "type": "Egg",
        "price": Decimal("200"),
        "preparation_time": 15,
        "is_available": True,
        "is_vegetarian": False,
        "description": "Fluffy long-grain rice tossed on a sizzling wok with golden scrambled eggs, spring onions, and oriental spices.",
        "image_url": "https://images.unsplash.com/photo-1596797038530-2c107229654b?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Chicken Hakka Noodles",
        "category": "Rice & Noodles",
        "type": "Non-Veg",
        "price": Decimal("230"),
        "preparation_time": 18,
        "is_available": True,
        "is_vegetarian": False,
        "description": "Classic Hakka style boiled noodles tossed with juicy chicken slices, shredded vegetables, white pepper, and soy.",
        "image_url": "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=600&auto=format&fit=crop&q=80",
    },

    # --- Desserts (5-10 mins) ---
    {
        "name": "Gulab Jamun",
        "category": "Desserts",
        "type": "Veg",
        "price": Decimal("80"),
        "preparation_time": 8,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Two warm, golden milk-solid dumplings soaked in aromatic cardamom and rose-infused sugar syrup.",
        "image_url": "https://images.unsplash.com/photo-1553787499-6f9133860278?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Double Ka Meetha",
        "category": "Desserts",
        "type": "Veg",
        "price": Decimal("120"),
        "preparation_time": 10,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Hyderabadi royal dessert of golden fried bread soaked in saffron-cardamom rabri and garnished with roasted pistachios.",
        "image_url": "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Ice Cream",
        "category": "Desserts",
        "type": "Veg",
        "price": Decimal("100"),
        "preparation_time": 5,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Rich and creamy artisanal scoops of dairy ice cream topped with chocolate drizzle and roasted nuts.",
        "image_url": "https://images.unsplash.com/photo-1570197788417-0e82375c9371?w=600&auto=format&fit=crop&q=80",
    },

    # --- Beverages (5-10 mins) ---
    {
        "name": "Fresh Lime Soda",
        "category": "Beverages",
        "type": "Beverage",
        "price": Decimal("80"),
        "preparation_time": 6,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Crisp effervescent club soda mixed with freshly pressed lime juice, mint leaves, and choice of sweet or salt.",
        "image_url": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Mango Lassi",
        "category": "Beverages",
        "type": "Beverage",
        "price": Decimal("120"),
        "preparation_time": 8,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Thick, chilled traditional yogurt drink blended smoothly with sweet Alphonso mango pulp and a pinch of cardamom.",
        "image_url": "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Cold Coffee",
        "category": "Beverages",
        "type": "Beverage",
        "price": Decimal("140"),
        "preparation_time": 8,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Frothy, refreshing iced coffee blended with chilled full-cream milk, dark roast espresso, and chocolate syrup.",
        "image_url": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=600&auto=format&fit=crop&q=80",
    },
    {
        "name": "Masala Tea",
        "category": "Beverages",
        "type": "Beverage",
        "price": Decimal("50"),
        "preparation_time": 7,
        "is_available": True,
        "is_vegetarian": True,
        "description": "Authentic Indian cutting chai brewed with strong Assam black tea, fresh crushed ginger, green cardamom, and milk.",
        "image_url": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=600&auto=format&fit=crop&q=80",
    },
]


def seed_30_menu_items():
    print(">>> Seeding/Updating 30 Core Menu Items in DineFlow...")

    # 1. Ensure the 7 core categories exist
    category_map = {}
    for cat in CATEGORIES:
        name = cat["name"]
        existing = menu_categories_collection.find_one({"name": {"$regex": f"^{name}$", "$options": "i"}})
        if existing:
            cat_id = existing["_id"]
            menu_categories_collection.update_one(
                {"_id": cat_id},
                {"$set": {"name": name, "description": cat["description"]}}
            )
        else:
            res = menu_categories_collection.insert_one({
                "name": name,
                "description": cat["description"],
                "created_at": now_utc(),
            })
            cat_id = res.inserted_id
        category_map[name.lower()] = cat_id
        print(f"Category '{name}' confirmed with ID {cat_id}")

    # 2. Upsert each of the 30 menu items
    inserted_count = 0
    updated_count = 0

    for item in MENU_ITEMS_30:
        c_name = item["category"]
        c_oid = category_map[c_name.lower()]

        doc = {
            "name": item["name"],
            "category_id": c_oid,
            "category_name": c_name,
            "type": item["type"],
            "price": decimal128(item["price"]),
            "preparation_time": item["preparation_time"],
            "is_available": item["is_available"],
            "is_vegetarian": item["is_vegetarian"],
            "description": item["description"],
            "image_url": item["image_url"],
            "updated_at": now_utc(),
        }

        # Check by exact name match (case-insensitive)
        existing_item = menu_items_collection.find_one({
            "name": {"$regex": f"^{item['name']}$", "$options": "i"}
        })

        if existing_item:
            menu_items_collection.update_one(
                {"_id": existing_item["_id"]},
                {"$set": doc}
            )
            updated_count += 1
            print(f"  [UPDATED] {item['name']} (₹{item['price']}, {item['type']}, {item['preparation_time']}m) ID: {existing_item['_id']}")
        else:
            doc["created_at"] = now_utc()
            res = menu_items_collection.insert_one(doc)
            inserted_count += 1
            print(f"  [INSERTED] {item['name']} (₹{item['price']}, {item['type']}, {item['preparation_time']}m) ID: {res.inserted_id}")

    # 3. Ensure any existing recipes for seeded dishes point to their current menu_item_id
    from app.database.mongodb import recipes_collection
    vb = menu_items_collection.find_one({"name": "Veg Biryani"})
    if vb:
        recipes_collection.update_many(
            {"menu_item_id": ObjectId("6abd2cc9897e2194474609da")},
            {"$set": {"menu_item_id": vb["_id"]}}
        )

    print("\n-----------------------------------------------------")
    print(f"Finished: {inserted_count} inserted, {updated_count} updated. Total verified: {len(MENU_ITEMS_30)}")
    print("-----------------------------------------------------")


if __name__ == "__main__":
    seed_30_menu_items()
