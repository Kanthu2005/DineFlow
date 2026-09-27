"""
Indian Cuisine Menu Seeder for DineFlow.
Seeds authentic Indian dishes, categories, realistic INR pricing, and high quality dish imagery.
"""
import sys
import io
from pathlib import Path
from decimal import Decimal

# Ensure utf-8 stdout on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.database.mongodb import menu_categories_collection, menu_items_collection
from app.services.common import now_utc, decimal128

INDIAN_CATEGORIES = [
    {
        "name": "Biryanis & Rice",
        "description": "Slow-cooked fragrant basmati rice dishes, dum biryanis and royal pulaos",
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
                "name": "Jeera Rice & Dal Tadka Combo",
                "description": "Cumin-tempered basmati rice paired with yellow lentils simmered and tempered with garlic, chilies & pure desi ghee.",
                "price": Decimal("180.00"),
                "preparation_time": 15,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
            },
        ],
    },
    {
        "name": "Tandoori & Starters",
        "description": "Clay oven roasted delicacies, smoky tikkas and crispy starters",
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
                "name": "Paneer Tikka Angara",
                "description": "Juicy chunks of cottage cheese marinated in spiced yogurt and chargrilled with bell peppers and onions.",
                "price": Decimal("240.00"),
                "preparation_time": 15,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=600&auto=format&fit=crop&q=80",
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
                "name": "Crispy Hara Bhara Kebab",
                "description": "Spiced golden patties of garden spinach, green peas, mashed potatoes, and roasted gram flour.",
                "price": Decimal("190.00"),
                "preparation_time": 12,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&auto=format&fit=crop&q=80",
            },
        ],
    },
    {
        "name": "Curries & Main Course",
        "description": "Rich traditional gravies, slow-cooked royal curries and authentic specialties",
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
                "name": "Paneer Butter Masala",
                "description": "Fresh cottage cheese in an aromatic, creamy tomato and butter gravy finished with cream.",
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
                "name": "Kashmiri Rogan Josh",
                "description": "Tender pieces of goat cooked in traditional Kashmiri red gravy spiced with fennel seeds and ginger.",
                "price": Decimal("390.00"),
                "preparation_time": 25,
                "is_vegetarian": False,
                "image_url": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600&auto=format&fit=crop&q=80",
            },
        ],
    },
    {
        "name": "Indian Breads",
        "description": "Freshly baked clay oven naans, rotis, and layered parathas",
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
                "description": "Wholesome stone-ground wheat bread baked crisp on the clay oven walls and finished with butter.",
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
        ],
    },
    {
        "name": "Desserts & Beverages",
        "description": "Authentic Indian sweets, chilled lassis and spiced hot beverages",
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
                "name": "Special Masala Chai",
                "description": "Strong, fragrant Indian milk tea brewed with fresh ginger, green cardamom, and aromatic spices.",
                "price": Decimal("45.00"),
                "preparation_time": 6,
                "is_vegetarian": True,
                "image_url": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80",
            },
        ],
    },
]


def seed_indian_menu():
    print(">>> Seeding Indian Cuisine Menu with realistic INR pricing and dish images...")
    total_cats = 0
    total_items = 0

    for cat_data in INDIAN_CATEGORIES:
        cat_name = cat_data["name"]
        cat_desc = cat_data["description"]

        existing_cat = menu_categories_collection.find_one({"name": cat_name})
        if not existing_cat:
            cat_doc = {
                "name": cat_name,
                "description": cat_desc,
                "created_at": now_utc(),
            }
            res = menu_categories_collection.insert_one(cat_doc)
            cat_id = res.inserted_id
            total_cats += 1
            print(f"  [+] Created Category: {cat_name}")
        else:
            cat_id = existing_cat["_id"]
            # update description if needed
            menu_categories_collection.update_one(
                {"_id": cat_id},
                {"$set": {"description": cat_desc}}
            )

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
                print(f"    [+] Created Dish: {item_data['name']} (₹{item_data['price']})")
            else:
                # Update dish with authentic price, image_url, and category
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
                print(f"    [*] Updated Dish: {item_data['name']} (₹{item_data['price']})")

    print(f"\nSuccessfully seeded {total_cats} new categories and {total_items} new dishes!")

    # Backfill any legacy or test dishes missing image_url
    DEFAULT_IMAGES = {
        "biryani": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
        "rice": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
        "burger": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&auto=format&fit=crop&q=80",
        "pizza": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&auto=format&fit=crop&q=80",
        "paneer": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80",
        "chicken": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop&q=80",
        "mutton": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600&auto=format&fit=crop&q=80",
        "tikka": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80",
        "kebab": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&auto=format&fit=crop&q=80",
        "naan": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
        "roti": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
        "chai": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80",
        "tea": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80",
        "dessert": "https://images.unsplash.com/photo-1605197148560-efdf5eb72e2d?w=600&auto=format&fit=crop&q=80",
        "sweet": "https://images.unsplash.com/photo-1605197148560-efdf5eb72e2d?w=600&auto=format&fit=crop&q=80",
        "lassi": "https://images.unsplash.com/photo-1527661591475-527312dd65f5?w=600&auto=format&fit=crop&q=80",
    }
    fallback_img = "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80"

    items_without_img = list(menu_items_collection.find({"$or": [{"image_url": None}, {"image_url": {"$exists": False}}]}))
    for doc in items_without_img:
        name_lower = (doc.get("name") or "").lower()
        selected_img = fallback_img
        for kw, img_url in DEFAULT_IMAGES.items():
            if kw in name_lower:
                selected_img = img_url
                break
        menu_items_collection.update_one({"_id": doc["_id"]}, {"$set": {"image_url": selected_img}})

    print(f"Backfilled images for {len(items_without_img)} dishes!")


if __name__ == "__main__":
    seed_indian_menu()
