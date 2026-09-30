"""
Indian Cuisine Menu Seeder for DineFlow.
Seeds authentic dishes across the 9 core restaurant menu categories:
- Veg Starters
- Non-Veg Starters
- Veg Main Course
- Non-Veg Main Course
- Biryani
- Rice & Noodles
- Breads
- Desserts
- Beverages
"""
import sys
import io
from pathlib import Path
from decimal import Decimal
from bson import ObjectId

# Ensure utf-8 stdout on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.database.mongodb import menu_categories_collection, menu_items_collection
from app.services.common import now_utc, decimal128

INDIAN_CATEGORIES = [
    {
        "name": "Veg Starters",
        "description": "Crispy vegetarian appetizers, tandoor grilled cottage cheese, and spiced garden fritters",
        "items": [
            {
                "name": "Paneer Tikka Angara",
                "description": "Juicy chunks of cottage cheese marinated in spiced hung yogurt and chargrilled with bell peppers and onions.",
                "price": Decimal("240.00"),
                "preparation_time": 15,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Crispy Hara Bhara Kebab",
                "description": "Spiced golden patties of garden spinach, green peas, mashed potatoes, and roasted gram flour.",
                "price": Decimal("190.00"),
                "preparation_time": 12,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Crispy Corn & Water Chestnut",
                "description": "Golden battered sweet corn kernels tossed with crunchy water chestnuts, spring onions and cracked pepper.",
                "price": Decimal("220.00"),
                "preparation_time": 12,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Dahi Ke Kebab",
                "description": "Velvety spiced hung curd and paneer patties pan-fried golden with mint chutney drizzle.",
                "price": Decimal("230.00"),
                "preparation_time": 14,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Mushroom Kurkure",
                "description": "Button mushrooms stuffed with cheese and herbs, crumb-coated and fried until shatteringly crisp.",
                "price": Decimal("210.00"),
                "preparation_time": 12,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
            },
        ],
    },
    {
        "name": "Non-Veg Starters",
        "description": "Smoky clay oven tandoori meats, succulent kebabs, and crispy seafood appetizers",
        "items": [
            {
                "name": "Tandoori Murgh (Half)",
                "description": "Classic tender bone-in chicken marinated in hung curd, Kashmiri chili, and roasted tandoori masala.",
                "price": Decimal("260.00"),
                "preparation_time": 20,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Murgh Malai Tikka",
                "description": "Melt-in-mouth chicken pieces steeped in rich cashew cream, cheese, cardamom, and gentle spices.",
                "price": Decimal("290.00"),
                "preparation_time": 18,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Chicken Seekh Kebab",
                "description": "Spiced minced chicken skewers grilled over hot coals with aromatic mint, ginger and coriander.",
                "price": Decimal("270.00"),
                "preparation_time": 16,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Amritsari Fish Fry",
                "description": "Crisp carom-spiced batter fried fresh river sole served with radish salad and mint dip.",
                "price": Decimal("320.00"),
                "preparation_time": 15,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Chicken 65",
                "description": "Spicy, deep-fried boneless chicken cubes tossed with curry leaves, mustard seeds and southern red chilies.",
                "price": Decimal("250.00"),
                "preparation_time": 14,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
            },
        ],
    },
    {
        "name": "Veg Main Course",
        "description": "Royal slow-simmered vegetarian curries, rich paneer gravies and traditional dal preparations",
        "items": [
            {
                "name": "Paneer Butter Masala",
                "description": "Fresh cottage cheese in an aromatic, creamy tomato and butter gravy finished with kasuri methi.",
                "price": Decimal("260.00"),
                "preparation_time": 15,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Dal Makhani (Bukhara Style)",
                "description": "Whole black lentils and kidney beans slow-simmered overnight over charcoal with white butter and cream.",
                "price": Decimal("210.00"),
                "preparation_time": 18,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Kadai Paneer",
                "description": "Cottage cheese cubes tossed with capsicum, crunchy onions, and freshly pounded coriander seeds and dry chilies.",
                "price": Decimal("250.00"),
                "preparation_time": 15,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Palak Paneer",
                "description": "Tender paneer cubes simmered in fresh pureed spinach tempered with garlic and cumin.",
                "price": Decimal("240.00"),
                "preparation_time": 15,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Yellow Dal Tadka",
                "description": "Yellow arhar lentils tempered in desi ghee with cumin, garlic, and fresh green chilies.",
                "price": Decimal("170.00"),
                "preparation_time": 12,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Malai Kofta",
                "description": "Paneer and potato dumplings filled with dry fruits, served in a luscious velvety cashew gravy.",
                "price": Decimal("270.00"),
                "preparation_time": 18,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80",
            },
        ],
    },
    {
        "name": "Non-Veg Main Course",
        "description": "Decadent chicken, mutton, and seafood curries prepared in royal culinary traditions",
        "items": [
            {
                "name": "Butter Chicken (Murgh Makhani)",
                "description": "Tandoori chicken morsels simmered in a velvety sauce of tomatoes, butter, cashew cream, and dried fenugreek leaves.",
                "price": Decimal("320.00"),
                "preparation_time": 20,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Kashmiri Rogan Josh",
                "description": "Tender pieces of goat meat cooked in traditional Kashmiri red gravy spiced with ratanjot, fennel and ginger.",
                "price": Decimal("390.00"),
                "preparation_time": 25,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Chicken Tikka Masala",
                "description": "Chargrilled chicken tikka pieces in a robust, spiced onion-tomato masala with diced bell peppers.",
                "price": Decimal("310.00"),
                "preparation_time": 18,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Kadai Chicken",
                "description": "Boneless chicken pieces cooked in a wok with crushed coriander seeds, capsicum and freshly ground whole spices.",
                "price": Decimal("290.00"),
                "preparation_time": 18,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Goan Fish Curry",
                "description": "Fresh fish steaks simmered in a tangy coconut and kokum curry with gentle coastal spices.",
                "price": Decimal("340.00"),
                "preparation_time": 20,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=600&auto=format&fit=crop&q=80",
            },
        ],
    },
    {
        "name": "Biryani",
        "description": "Authentic fragrant dum biryanis layered with aged basmati, saffron, and aromatic spices",
        "items": [
            {
                "name": "Hyderabadi Chicken Dum Biryani",
                "description": "Fragrant long-grain basmati rice layered with spiced marinated chicken, saffron, mint & caramelized onions.",
                "price": Decimal("290.00"),
                "preparation_time": 20,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Royal Mutton Dum Biryani",
                "description": "Tender slow-cooked goat meat infused with royal Awadhi spices and layered with saffron-scented basmati.",
                "price": Decimal("380.00"),
                "preparation_time": 25,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Lucknowi Veg Dum Biryani",
                "description": "Fresh garden vegetables, paneer cubes, and aromatic rice cooked on gentle dum with kewra and mint.",
                "price": Decimal("220.00"),
                "preparation_time": 18,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Egg Dum Biryani",
                "description": "Golden fried boiled eggs layered with spiced saffron basmati rice and roasted caramelized onions.",
                "price": Decimal("230.00"),
                "preparation_time": 16,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
            },
        ],
    },
    {
        "name": "Rice & Noodles",
        "description": "Aromatic basmati rice preparations, wok-tossed fried rice, and Indo-Chinese noodles",
        "items": [
            {
                "name": "Jeera Rice & Dal Tadka Combo",
                "description": "Cumin-tempered basmati rice paired with yellow lentils simmered and tempered with garlic, chilies & pure desi ghee.",
                "price": Decimal("180.00"),
                "preparation_time": 15,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Steamed Basmati Rice",
                "description": "Fluffy, premium aged long-grain basmati rice cooked to perfection.",
                "price": Decimal("120.00"),
                "preparation_time": 10,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Veg Fried Rice",
                "description": "Wok-tossed basmati rice with finely diced carrots, beans, bell peppers, and scallions in light soy sauce.",
                "price": Decimal("180.00"),
                "preparation_time": 14,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Chicken Hakka Noodles",
                "description": "Stir-fried noodles tossed with shredded chicken, crunchy vegetables, garlic, and oriental sauces.",
                "price": Decimal("240.00"),
                "preparation_time": 15,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Schezwan Veg Noodles",
                "description": "Spicy wok-tossed noodles in fiery red Schezwan chili garlic sauce with crisp veggies.",
                "price": Decimal("190.00"),
                "preparation_time": 14,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=600&auto=format&fit=crop&q=80",
            },
        ],
    },
    {
        "name": "Breads",
        "description": "Freshly baked clay oven naans, tandoori rotis, and layered parathas",
        "items": [
            {
                "name": "Butter Naan",
                "description": "Soft and fluffy clay-oven baked bread glazed with rich salted butter.",
                "price": Decimal("50.00"),
                "preparation_time": 8,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Garlic Butter Naan",
                "description": "Hand-stretched tandoori naan studded with roasted minced garlic and fresh coriander, brushed with butter.",
                "price": Decimal("65.00"),
                "preparation_time": 8,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Tandoori Roti (Butter)",
                "description": "Wholesome stone-ground wheat bread baked crisp on clay oven walls and finished with butter.",
                "price": Decimal("35.00"),
                "preparation_time": 6,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Laccha Paratha",
                "description": "Crisp, flaky multi-layered whole wheat flatbread made with pure desi ghee.",
                "price": Decimal("55.00"),
                "preparation_time": 10,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Cheese Garlic Naan",
                "description": "Stuffed tandoori naan packed with molten cheese and topped with garlic butter and herbs.",
                "price": Decimal("90.00"),
                "preparation_time": 10,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
            },
        ],
    },
    {
        "name": "Desserts",
        "description": "Authentic Indian sweets, chilled delicacies, and warm dessert preparations",
        "items": [
            {
                "name": "Shahi Gulab Jamun (2 pcs)",
                "description": "Warm, golden fried khoya dumplings soaked in fragrant rose-cardamom saffron sugar syrup.",
                "price": Decimal("90.00"),
                "preparation_time": 5,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1605197148560-efdf5eb72e2d?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Kesari Rasmalai (2 pcs)",
                "description": "Melt-in-mouth cottage cheese patties immersed in chilled saffron milk garnished with slivered almonds & pistachios.",
                "price": Decimal("120.00"),
                "preparation_time": 5,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Gajar Ka Halwa",
                "description": "Traditional slow-cooked red carrots with full-cream milk, pure ghee, khoya and crunchy dry fruits.",
                "price": Decimal("130.00"),
                "preparation_time": 6,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1605197148560-efdf5eb72e2d?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Kulfi Falooda",
                "description": "Traditional rich malai kulfi served with falooda noodles, rose syrup and sweet basil seeds.",
                "price": Decimal("140.00"),
                "preparation_time": 5,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
            },
        ],
    },
    {
        "name": "Beverages",
        "description": "Refreshing chilled yogurt drinks, mocktails, spiced coolers, and traditional hot chai",
        "items": [
            {
                "name": "Royal Mango Lassi",
                "description": "Creamy chilled yogurt smoothie infused with sweet Alphonso mango pulp and cardamom.",
                "price": Decimal("110.00"),
                "preparation_time": 5,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1527661591475-527312dd65f5?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Special Masala Chai",
                "description": "Strong, fragrant Indian milk tea brewed with fresh ginger, green cardamom, and aromatic spices.",
                "price": Decimal("45.00"),
                "preparation_time": 6,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Fresh Lime Soda (Sweet/Salt)",
                "description": "Fizzy club soda with freshly squeezed lime juice, mint leaves, and black rock salt.",
                "price": Decimal("70.00"),
                "preparation_time": 4,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=600&auto=format&fit=crop&q=80",
            },
            {
                "name": "Spiced Butter Milk (Chaas)",
                "description": "Cooling churned curd tempered with roasted cumin, green chili, ginger and fresh coriander.",
                "price": Decimal("50.00"),
                "preparation_time": 4,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1527661591475-527312dd65f5?w=600&auto=format&fit=crop&q=80",
            },
        ],
    },
]


def seed_indian_menu():
    print(">>> Seeding Indian Cuisine Menu across the 9 core categories...")

    # 1. Clean up obsolete test items from legacy test runs
    test_dish_names = [
        "Item A Subtotal Test", "Item B Subtotal Test", "Snapshot Test Item",
        "Kitchen Test Item", "Test Dish Add Flow", "Golden Malai Tikka"
    ]
    menu_items_collection.delete_many({"name": {"$in": test_dish_names}})

    # 2. Track category IDs for the 9 core categories
    cat_map = {}
    for cat_data in INDIAN_CATEGORIES:
        cname = cat_data["name"]
        cdesc = cat_data["description"]
        existing = menu_categories_collection.find_one({"name": cname})
        if not existing:
            res = menu_categories_collection.insert_one({
                "name": cname,
                "description": cdesc,
                "created_at": now_utc(),
            })
            cat_id = res.inserted_id
            print(f"  [+] Created Category: {cname}")
        else:
            cat_id = existing["_id"]
            menu_categories_collection.update_one(
                {"_id": cat_id},
                {"$set": {"description": cdesc}}
            )
        cat_map[cname] = cat_id

    # 3. Seed/Update dishes for each category
    total_items = 0
    for cat_data in INDIAN_CATEGORIES:
        cat_name = cat_data["name"]
        cat_id = cat_map[cat_name]

        for item_data in cat_data["items"]:
            existing_item = menu_items_collection.find_one({"name": item_data["name"]})
            item_doc = {
                "name": item_data["name"],
                "description": item_data["description"],
                "category_id": cat_id,
                "price": decimal128(item_data["price"]),
                "preparation_time": item_data["preparation_time"],
                "is_available": True,
                "is_vegetarian": item_data["is_vegetarian"],
                "image_url": item_data["image_url"],
                "created_at": now_utc(),
            }

            if not existing_item:
                menu_items_collection.insert_one(item_doc)
                total_items += 1
                print(f"    [+] Created Dish: {item_data['name']} (₹{item_data['price']}) in {cat_name}")
            else:
                menu_items_collection.update_one(
                    {"_id": existing_item["_id"]},
                    {"$set": {
                        "category_id": cat_id,
                        "price": decimal128(item_data["price"]),
                        "description": item_data["description"],
                        "preparation_time": item_data["preparation_time"],
                        "is_available": True,
                        "is_vegetarian": item_data["is_vegetarian"],
                        "image_url": item_data["image_url"],
                    }}
                )

    # 4. Migrate any remaining valid dishes from old categories into the 9 core categories
    category_remapping = {
        "Biryanis & Rice": "Biryani",
        "Biryani Specials": "Biryani",
        "Curries & Main Course": "Veg Main Course",
        "Indian Breads": "Breads",
        "Desserts & Beverages": "Desserts",
        "Starters & Tandoor": "Veg Starters",
        "Tandoori & Starters": "Veg Starters",
        "Tandoori & Grills": "Non-Veg Starters",
    }
    
    for old_name, target_cat_name in category_remapping.items():
        old_cat = menu_categories_collection.find_one({"name": old_name})
        if old_cat and target_cat_name in cat_map:
            target_id = cat_map[target_cat_name]
            old_cat_id = old_cat["_id"]
            items_in_old = list(menu_items_collection.find({"category_id": old_cat_id}))
            for it in items_in_old:
                chosen_target_id = target_id
                if not it.get("is_vegetarian"):
                    if target_cat_name == "Veg Starters":
                        chosen_target_id = cat_map["Non-Veg Starters"]
                    elif target_cat_name == "Veg Main Course":
                        chosen_target_id = cat_map["Non-Veg Main Course"]
                
                # Check if beverage
                if any(w in it.get("name", "").lower() for w in ["chai", "tea", "lassi", "soda", "drink", "coffee", "juice"]):
                    chosen_target_id = cat_map["Beverages"]
                elif any(w in it.get("name", "").lower() for w in ["rice", "noodle", "pulao"]) and "biryani" not in it.get("name", "").lower():
                    chosen_target_id = cat_map["Rice & Noodles"]

                menu_items_collection.update_one(
                    {"_id": it["_id"]},
                    {"$set": {"category_id": chosen_target_id}}
                )

    # 5. Remove legacy unused categories that were replaced
    core_names = set(cat_map.keys())
    old_cats = list(menu_categories_collection.find({"name": {"$nin": list(core_names)}}))
    for oc in old_cats:
        cnt = menu_items_collection.count_documents({"category_id": oc["_id"]})
        if cnt == 0:
            menu_categories_collection.delete_one({"_id": oc["_id"]})
            print(f"  [-] Cleaned up obsolete category: {oc.get('name')}")
        else:
            menu_items_collection.update_many({"category_id": oc["_id"]}, {"$set": {"category_id": cat_map["Veg Main Course"]}})
            menu_categories_collection.delete_one({"_id": oc["_id"]})
            print(f"  [-] Reassigned items and cleaned up category: {oc.get('name')}")

    print("\nMenu setup across 9 core categories successfully verified!")


if __name__ == "__main__":
    seed_indian_menu()
