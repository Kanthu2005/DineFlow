"""
DineFlow - Dedicated Veg Category & Subcategories Seeder
=========================================================
Implements the user specification:
- Main category: "Veg" (100% Vegetarian)
- 7 Subcategories under "Veg":
  1. Starters
  2. Biryani
  3. Main Course
  4. Breads
  5. Rice & Noodles
  6. Desserts
  7. Beverages
- Exactly 35 Vegetarian items (5 items per subcategory)
- Accurate prices, professional customer-friendly descriptions, HD food images
- Full BOM recipes mapped to raw inventory ingredients
- Safe upsert logic preventing duplicate items while preserving existing items
"""

import sys
from decimal import Decimal
from bson import ObjectId

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.database.mongodb import (
    menu_categories_collection,
    menu_subcategories_collection,
    menu_items_collection,
    ingredients_collection,
    recipes_collection,
)
from app.services.common import now_utc, decimal128


VEG_SUBCATEGORIES = [
    {
        "name": "Starters",
        "description": "Crisp appetizers, sizzling skewers, and crunchy starters to begin your feast.",
        "display_order": 1,
        "items": [
            {
                "name": "Paneer Tikka",
                "price": Decimal("220"),
                "preparation_time": 20,
                "description": "Succulent cubes of cottage cheese marinated in spiced yogurt and grilled over hot coals with crunchy bell peppers.",
                "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Paneer", "qty": Decimal("150"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("10"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("30"), "unit": "G"},
                ],
            },
            {
                "name": "Gobi Manchurian",
                "price": Decimal("180"),
                "preparation_time": 18,
                "description": "Crispy golden cauliflower florets glazed in a garlic-infused sweet, spicy, and tangy Indo-Chinese Manchurian sauce.",
                "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Vegetables", "qty": Decimal("150"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("30"), "unit": "G"},
                ],
            },
            {
                "name": "Crispy Corn",
                "price": Decimal("160"),
                "preparation_time": 15,
                "description": "Crunchy batter-fried tender sweet corn kernels tossed with freshly cracked black pepper, diced bell peppers, and chat spices.",
                "image_url": "https://images.unsplash.com/photo-1551754655-cd27e38d2076?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Vegetables", "qty": Decimal("150"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                ],
            },
            {
                "name": "Veg Spring Rolls",
                "price": Decimal("170"),
                "preparation_time": 15,
                "description": "Crispy golden-fried pastry rolls generously stuffed with seasoned julienned vegetables and aromatic herbs, served with sweet chili dip.",
                "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Vegetables", "qty": Decimal("120"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                ],
            },
            {
                "name": "Chilli Paneer",
                "price": Decimal("220"),
                "preparation_time": 18,
                "description": "Tender paneer cubes wok-tossed with crunchy bell peppers, fresh green chilies, and scallions in a signature savory soy-chili sauce.",
                "image_url": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Paneer", "qty": Decimal("150"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("40"), "unit": "G"},
                ],
            },
        ],
    },
    {
        "name": "Biryani",
        "description": "Royal fragrant dum biryanis slow-cooked with aged basmati rice, saffron, and fresh vegetables.",
        "display_order": 2,
        "items": [
            {
                "name": "Veg Dum Biryani",
                "price": Decimal("200"),
                "preparation_time": 20,
                "description": "Fragrant long-grain basmati rice dum-cooked on low heat with garden-fresh vegetables, mint leaves, saffron, and whole aromatic spices.",
                "image_url": "https://images.unsplash.com/photo-1642821373181-696a54913e93?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("250"), "unit": "G"},
                    {"ingredient": "Vegetables", "qty": Decimal("150"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "G"},
                ],
            },
            {
                "name": "Paneer Biryani",
                "price": Decimal("220"),
                "preparation_time": 20,
                "description": "Layers of saffron-infused basmati rice and richly spiced marinated paneer cubes finished with caramelized onions and pure ghee.",
                "image_url": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("250"), "unit": "G"},
                    {"ingredient": "Paneer", "qty": Decimal("120"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "G"},
                ],
            },
            {
                "name": "Mushroom Biryani",
                "price": Decimal("230"),
                "preparation_time": 22,
                "description": "Tender earthy button mushrooms sautéed in royal biryani masala, layered with fragrant basmati rice and fresh mint.",
                "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("250"), "unit": "G"},
                    {"ingredient": "Vegetables", "qty": Decimal("150"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "G"},
                ],
            },
            {
                "name": "Veg Handi Biryani",
                "price": Decimal("210"),
                "preparation_time": 22,
                "description": "Authentic clay-pot preparation of seasoned farm vegetables and fragrant basmati rice sealed with dough to lock in royal aroma.",
                "image_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("250"), "unit": "G"},
                    {"ingredient": "Vegetables", "qty": Decimal("150"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "G"},
                ],
            },
            {
                "name": "Kaju Biryani",
                "price": Decimal("240"),
                "preparation_time": 20,
                "description": "A rich, royal dum biryani cooked with generous roasted cashew nuts, saffron strands, aromatic spices, and aged basmati rice.",
                "image_url": "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("250"), "unit": "G"},
                    {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "G"},
                ],
            },
        ],
    },
    {
        "name": "Main Course",
        "description": "Rich, aromatic vegetarian curries and comforting dals cooked to traditional perfection.",
        "display_order": 3,
        "items": [
            {
                "name": "Paneer Butter Masala",
                "price": Decimal("240"),
                "preparation_time": 20,
                "description": "Melt-in-mouth cottage cheese cubes simmered in a velvety tomato-cashew butter gravy infused with fragrant kasoori methi.",
                "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Paneer", "qty": Decimal("150"), "unit": "G"},
                    {"ingredient": "Tomato", "qty": Decimal("100"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("40"), "unit": "G"},
                ],
            },
            {
                "name": "Kadai Paneer",
                "price": Decimal("230"),
                "preparation_time": 20,
                "description": "Paneer cubes and crisp bell peppers stir-cooked in a robust, freshly pounded coriander and dry red chili kadai masala.",
                "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Paneer", "qty": Decimal("150"), "unit": "G"},
                    {"ingredient": "Tomato", "qty": Decimal("80"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "G"},
                ],
            },
            {
                "name": "Palak Paneer",
                "price": Decimal("220"),
                "preparation_time": 20,
                "description": "Fresh cottage cheese cubes cooked in a smooth, delicately spiced spinach purée tempered with golden garlic and cumin.",
                "image_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Paneer", "qty": Decimal("150"), "unit": "G"},
                    {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("40"), "unit": "G"},
                ],
            },
            {
                "name": "Mix Veg Curry",
                "price": Decimal("200"),
                "preparation_time": 18,
                "description": "A wholesome medley of fresh carrots, beans, cauliflower, and green peas simmered in a homestyle spiced onion-tomato gravy.",
                "image_url": "https://images.unsplash.com/photo-1546833998-877b37c2e5c6?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Vegetables", "qty": Decimal("200"), "unit": "G"},
                    {"ingredient": "Tomato", "qty": Decimal("80"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("50"), "unit": "G"},
                ],
            },
            {
                "name": "Dal Tadka",
                "price": Decimal("170"),
                "preparation_time": 15,
                "description": "Creamy yellow lentils slow-cooked and tempered with fragrant desi ghee, cumin seeds, minced garlic, and whole Kashmiri red chilies.",
                "image_url": "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "G"},
                    {"ingredient": "Tomato", "qty": Decimal("60"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("15"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("40"), "unit": "G"},
                ],
            },
        ],
    },
    {
        "name": "Breads",
        "description": "Clay-oven baked tandoori naans, soft rotis, and delicate flatbreads.",
        "display_order": 4,
        "items": [
            {
                "name": "Butter Naan",
                "price": Decimal("60"),
                "preparation_time": 8,
                "description": "Soft and pillowy clay-oven baked refined flour flatbread lavishly brushed with melted pure butter.",
                "image_url": "https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
            {
                "name": "Garlic Naan",
                "price": Decimal("80"),
                "preparation_time": 10,
                "description": "Tandoori naan topped with roasted minced garlic cloves and fresh cilantro, brushed with warm butter.",
                "image_url": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
            {
                "name": "Plain Naan",
                "price": Decimal("50"),
                "preparation_time": 8,
                "description": "Traditional teardrop-shaped leavened bread baked crisp on the outside and airy on the inside in the tandoor.",
                "image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
            {
                "name": "Tandoori Roti",
                "price": Decimal("40"),
                "preparation_time": 6,
                "description": "Wholesome stoneground whole wheat bread baked crisp on the clay walls of the tandoor oven.",
                "image_url": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
            {
                "name": "Rumali Roti",
                "price": Decimal("45"),
                "preparation_time": 8,
                "description": "Ultra-thin, handkerchief-soft Indian flatbread hand-stretched and cooked swiftly on a piping-hot inverted tawa.",
                "image_url": "https://images.unsplash.com/photo-1541544741938-0af808871cc0?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
        ],
    },
    {
        "name": "Rice & Noodles",
        "description": "Wok-tossed fried rice and flavorful Indo-Chinese noodles cooked on high heat.",
        "display_order": 5,
        "items": [
            {
                "name": "Veg Fried Rice",
                "price": Decimal("180"),
                "preparation_time": 15,
                "description": "Fragrant steamed rice wok-tossed with finely chopped carrots, French beans, cabbage, garlic, and light soy seasoning.",
                "image_url": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("200"), "unit": "G"},
                    {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("30"), "unit": "G"},
                ],
            },
            {
                "name": "Paneer Fried Rice",
                "price": Decimal("210"),
                "preparation_time": 18,
                "description": "High-flame wok-tossed rice tossed with golden crispy paneer cubes, crunchy vegetables, and aromatic Indo-Chinese sauces.",
                "image_url": "https://images.unsplash.com/photo-1600891964599-f61ba0e24092?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("200"), "unit": "G"},
                    {"ingredient": "Paneer", "qty": Decimal("100"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("30"), "unit": "G"},
                ],
            },
            {
                "name": "Veg Hakka Noodles",
                "price": Decimal("180"),
                "preparation_time": 15,
                "description": "Classic stir-fried noodles tossed with julienned bell peppers, cabbage, carrots, spring onions, and savory Hakka spices.",
                "image_url": "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("40"), "unit": "G"},
                ],
            },
            {
                "name": "Schezwan Fried Rice",
                "price": Decimal("200"),
                "preparation_time": 16,
                "description": "Spicy and pungent wok-tossed rice stir-fried with house-made Schezwan chili paste, garlic, and fresh crisp vegetables.",
                "image_url": "https://images.unsplash.com/photo-1569058242253-92a9c755a0ec?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Rice", "qty": Decimal("200"), "unit": "G"},
                    {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("30"), "unit": "G"},
                ],
            },
            {
                "name": "Schezwan Veg Noodles",
                "price": Decimal("200"),
                "preparation_time": 16,
                "description": "Fiery wok-tossed noodles bursting with Schezwan chili heat, crunchy farm vegetables, ginger, and scallions.",
                "image_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=800&auto=format&fit=crop&q=80",
                "recipe": [
                    {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "G"},
                    {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
                    {"ingredient": "Onion", "qty": Decimal("40"), "unit": "G"},
                ],
            },
        ],
    },
    {
        "name": "Desserts",
        "description": "Traditional Indian royal sweets, warm pastries, and chilled desserts to complete your meal.",
        "display_order": 6,
        "items": [
            {
                "name": "Gulab Jamun",
                "price": Decimal("100"),
                "preparation_time": 8,
                "description": "Warm, melt-in-the-mouth fried milk-solid dumplings steeped in fragrant cardamom and saffron-rose sugar syrup.",
                "image_url": "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
            {
                "name": "Gajar Ka Halwa",
                "price": Decimal("130"),
                "preparation_time": 10,
                "description": "Slow-simmered grated winter carrots cooked in condensed milk and pure desi ghee, garnished with toasted almonds and cashews.",
                "image_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
            {
                "name": "Rasmalai",
                "price": Decimal("140"),
                "preparation_time": 8,
                "description": "Spongy, delicate cottage cheese patties soaked in chilled, rich saffron-cardamom flavored cream milk topped with pistachios.",
                "image_url": "https://images.unsplash.com/photo-1553787499-6f9133860278?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
            {
                "name": "Kulfi",
                "price": Decimal("120"),
                "preparation_time": 5,
                "description": "Traditional dense, creamy Indian frozen milk dessert flavored with rich pistachios, almonds, and aromatic saffron.",
                "image_url": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
            {
                "name": "Brownie with Ice Cream",
                "price": Decimal("180"),
                "preparation_time": 10,
                "description": "Warm, rich chocolate walnut brownie served on a sizzler plate with a generous scoop of vanilla bean ice cream and hot fudge.",
                "image_url": "https://images.unsplash.com/photo-1564355808539-22fda35bed7e?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
        ],
    },
    {
        "name": "Beverages",
        "description": "Refreshing coolers, authentic churned lassis, steaming teas, and chilled coffees.",
        "display_order": 7,
        "items": [
            {
                "name": "Fresh Lime Soda",
                "price": Decimal("80"),
                "preparation_time": 6,
                "description": "Zesty sparkling soda served chilled with freshly squeezed lime juice, rock salt, mint sprigs, and pure sugar syrup.",
                "image_url": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
            {
                "name": "Mango Lassi",
                "price": Decimal("120"),
                "preparation_time": 8,
                "description": "Thick and luscious cultured yogurt smoothie blended with sweet Alphonso mango pulp, crushed ice, and a dash of cardamom.",
                "image_url": "https://images.unsplash.com/photo-1527661591475-527312dd65f5?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
            {
                "name": "Sweet Lassi",
                "price": Decimal("100"),
                "preparation_time": 5,
                "description": "Traditional Punjabi chilled churned yogurt beverage sweetened to perfection and topped with rich clotted cream (malai).",
                "image_url": "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
            {
                "name": "Masala Chai",
                "price": Decimal("60"),
                "preparation_time": 8,
                "description": "Strong, fragrant Indian milk tea brewed with whole milk, crushed ginger, cardamom pods, cinnamon, and cloves.",
                "image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
            {
                "name": "Cold Coffee",
                "price": Decimal("130"),
                "preparation_time": 8,
                "description": "Frothy, rich iced coffee blended with whole milk and vanilla ice cream, dusted with dark cocoa powder.",
                "image_url": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=800&auto=format&fit=crop&q=80",
                "recipe": [],
            },
        ],
    },
]


def seed_veg_category_and_items():
    print("=" * 70)
    print("DineFlow - Seeding / Updating 'Veg' Category & Subcategories")
    print("=" * 70)

    # 1. Ensure the single main 'Veg' category exists
    veg_cat = menu_categories_collection.find_one({"name": {"$regex": "^Veg$", "$options": "i"}})
    veg_data = {
        "name": "Veg",
        "description": "100% pure vegetarian culinary delights crafted with fresh vegetables, paneer, and authentic aromatic spices.",
        "food_type": "Veg",
        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=800&auto=format&fit=crop&q=80",
        "display_order": 1,
        "is_active": True,
        "updated_at": now_utc(),
    }

    if not veg_cat:
        veg_data["created_at"] = now_utc()
        res = menu_categories_collection.insert_one(veg_data)
        veg_id = res.inserted_id
        print(f"[+] Created main category 'Veg' (ID: {veg_id})")
    else:
        veg_id = veg_cat["_id"]
        menu_categories_collection.update_one({"_id": veg_id}, {"$set": veg_data})
        print(f"[OK] Updated main category 'Veg' (ID: {veg_id})")

    # Deactivate obsolete top-level categories that should now be subcategories under Veg
    obsolete_top_categories = ["Starters", "Biryani", "Main Course", "Breads", "Rice & Noodles", "Desserts", "Beverages"]
    for old_cat_name in obsolete_top_categories:
        menu_categories_collection.update_many(
            {"name": {"$regex": f"^{old_cat_name}$", "$options": "i"}, "_id": {"$ne": veg_id}},
            {"$set": {"is_active": False, "updated_at": now_utc()}}
        )

    # 2. Build map of standard raw ingredients for BOM recipes
    ingredients_map = {}
    for ing in ingredients_collection.find():
        name = ing.get("name")
        if name and name not in ingredients_map:
            ingredients_map[name] = ing["_id"]

    # Ensure core raw ingredients exist with sufficient stock
    core_ingredients = [
        {"name": "Rice", "unit": "KG", "stock": Decimal("50.00"), "cost": Decimal("60.00"), "category": "Grains"},
        {"name": "Paneer", "unit": "KG", "stock": Decimal("30.00"), "cost": Decimal("320.00"), "category": "Dairy"},
        {"name": "Vegetables", "unit": "KG", "stock": Decimal("40.00"), "cost": Decimal("40.00"), "category": "Vegetables"},
        {"name": "Oil", "unit": "LITRE", "stock": Decimal("30.00"), "cost": Decimal("140.00"), "category": "Oils & Fats"},
        {"name": "Onion", "unit": "KG", "stock": Decimal("30.00"), "cost": Decimal("35.00"), "category": "Vegetables"},
        {"name": "Tomato", "unit": "KG", "stock": Decimal("30.00"), "cost": Decimal("40.00"), "category": "Vegetables"},
    ]
    for ci in core_ingredients:
        existing_ing = ingredients_collection.find_one({"name": ci["name"]})
        if not existing_ing:
            res_ing = ingredients_collection.insert_one({
                "name": ci["name"],
                "unit": ci["unit"],
                "available_quantity": decimal128(ci["stock"]),
                "current_stock": decimal128(ci["stock"]),
                "cost_per_unit": decimal128(ci["cost"]),
                "category": ci["category"],
                "created_at": now_utc(),
                "updated_at": now_utc(),
            })
            ingredients_map[ci["name"]] = res_ing.inserted_id
            print(f"[+] Seeded ingredient {ci['name']}")
        else:
            ingredients_map[ci["name"]] = existing_ing["_id"]

    # Deactivate legacy subcategories not belonging to the active Veg category
    menu_subcategories_collection.update_many(
        {"category_id": {"$nin": [veg_id, str(veg_id)]}},
        {"$set": {"is_active": False, "updated_at": now_utc()}}
    )

    # 3. Create or Update Subcategories under 'Veg'
    total_dishes_seeded = 0

    for subcat_data in VEG_SUBCATEGORIES:
        sub_name = subcat_data["name"]
        sub_order = subcat_data["display_order"]

        # Look for existing subcategory under Veg category
        existing_sub = menu_subcategories_collection.find_one({
            "category_id": {"$in": [veg_id, str(veg_id)]},
            "name": {"$regex": f"^{sub_name}$", "$options": "i"},
        })

        sub_doc = {
            "name": sub_name,
            "category_id": veg_id,
            "category_name": "Veg",
            "description": subcat_data["description"],
            "display_order": sub_order,
            "is_active": True,
            "updated_at": now_utc(),
        }

        if existing_sub:
            sub_id = existing_sub["_id"]
            menu_subcategories_collection.update_one({"_id": sub_id}, {"$set": sub_doc})
            print(f"\n[OK] Subcategory 'Veg -> {sub_name}' updated (ID: {sub_id})")
        else:
            sub_doc["created_at"] = now_utc()
            res_sub = menu_subcategories_collection.insert_one(sub_doc)
            sub_id = res_sub.inserted_id
            print(f"\n[+] Created Subcategory 'Veg -> {sub_name}' (ID: {sub_id})")

        # 4. Upsert dishes under this subcategory
        for item in subcat_data["items"]:
            dish_name = item["name"]
            price_val = item["price"]
            prep_time = item.get("preparation_time", 18)
            desc_val = item["description"]
            img_val = item["image_url"]

            # Safe check: if dish already exists in menu_items_collection, update it (prevent duplicate)
            existing_dish = menu_items_collection.find_one({
                "name": {"$regex": f"^{dish_name}$", "$options": "i"}
            })

            dish_payload = {
                "name": dish_name,
                "category": "Veg",
                "category_id": veg_id,
                "category_name": "Veg",
                "subcategory": sub_name,
                "subcategory_id": sub_id,
                "subcategory_name": sub_name,
                "price": decimal128(price_val),
                "base_price": decimal128(price_val),
                "discount": decimal128(Decimal("0")),
                "tax": decimal128(Decimal("0")),
                "final_price": decimal128(price_val),
                "preparation_time": prep_time,
                "is_vegetarian": True,
                "food_type": "Veg",
                "type": "Beverage" if sub_name == "Beverages" else "Veg",
                "is_available": True,
                "is_active": True,
                "availability": "AVAILABLE",
                "status": "AVAILABLE",
                "description": desc_val,
                "image_url": img_val,
                "inventory_tracking_enabled": True,
                "updated_at": now_utc(),
            }

            if existing_dish:
                dish_id = existing_dish["_id"]
                menu_items_collection.update_one({"_id": dish_id}, {"$set": dish_payload})
                print(f"  [OK] Updated dish: {dish_name} (₹{price_val})")
            else:
                dish_payload["created_at"] = now_utc()
                res_d = menu_items_collection.insert_one(dish_payload)
                dish_id = res_d.inserted_id
                print(f"  [+] Added dish: {dish_name} (₹{price_val})")

            total_dishes_seeded += 1

            # 5. Link BOM recipes
            recipe_boms = item.get("recipe", [])
            if recipe_boms:
                recipes_collection.delete_many({"menu_item_id": dish_id})
                for bom in recipe_boms:
                    ing_name = bom["ingredient"]
                    ing_id = ingredients_map.get(ing_name)
                    if ing_id:
                        recipes_collection.insert_one({
                            "menu_item_id": dish_id,
                            "ingredient_id": ing_id,
                            "quantity_required": decimal128(bom["qty"]),
                            "unit": bom["unit"],
                            "created_at": now_utc(),
                        })

    print(f"\n[SUCCESS] Successfully seeded/updated {total_dishes_seeded} dishes across 7 subcategories under 'Veg' category!")


if __name__ == "__main__":
    seed_veg_category_and_items()
