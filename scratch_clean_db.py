from app.database.mongodb import menu_categories_collection, menu_items_collection
from decimal import Decimal
from bson import Decimal128
from app.services.service import now_utc

# 1. Clean out all test residue, duplicates, and test categories
print("Purging test residue...")
menu_categories_collection.delete_many({
    "$or": [
        {"name": {"$regex": r"^(Test|Billing|Unique|Dbg)", "$options": "i"}},
        {"name": {"$regex": r"@", "$options": "i"}},
        {"name": "Biryani Specials"}
    ]
})

menu_items_collection.delete_many({
    "$or": [
        {"name": {"$regex": r"^(Test|Billing|Dbg)", "$options": "i"}},
        {"name": {"$regex": r"(Test|Subtotal|Snapshot|Kitchen Test|Seasonal Fish|Out of Season)", "$options": "i"}}
    ]
})

# 2. Perfect curated Indian Menu with verified high-quality Unsplash food imagery
MENU_DATA = [
    {
        "category": "Starters & Tandoor",
        "description": "Charcoal grilled kebabs, crispy appetizers and sizzling tandoori delicacies",
        "dishes": [
            {
                "name": "Paneer Tikka Angara",
                "price": Decimal128("280.00"),
                "prep": 15,
                "veg": True,
                "desc": "Smoky cottage cheese cubes steeped in rich spiced yogurt marinade and char-grilled with crunchy peppers.",
                "img": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Tandoori Murgh (Half)",
                "price": Decimal128("340.00"),
                "prep": 20,
                "veg": False,
                "desc": "Tender spring chicken roasted over glowing charcoal with Kashmiri deggi mirch and garam masala.",
                "img": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Murgh Malai Kebab",
                "price": Decimal128("360.00"),
                "prep": 18,
                "veg": False,
                "desc": "Melt-in-mouth chicken chunks marinated in rich clotted cream, green cardamom, and cashew paste.",
                "img": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Crispy Corn & Water Chestnut",
                "price": Decimal128("240.00"),
                "prep": 12,
                "veg": True,
                "desc": "Golden crispy sweet corn wok-tossed with crushed black pepper, spring onions, and roasted garlic.",
                "img": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Crispy Hara Bhara Kebab",
                "price": Decimal128("220.00"),
                "prep": 12,
                "veg": True,
                "desc": "Pan-seared spinach, green pea, and cottage cheese patties centered with roasted pistachio.",
                "img": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80"
            }
        ]
    },
    {
        "category": "Curries & Main Course",
        "description": "Rich simmering gravies, slow-cooked royal curries, and comforting dals",
        "dishes": [
            {
                "name": "Paneer Butter Masala",
                "price": Decimal128("320.00"),
                "prep": 15,
                "veg": True,
                "desc": "Velvety spiced tomato and cashew butter reduction finished with fresh cream and dried fenugreek.",
                "img": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Butter Chicken (Murgh Makhani)",
                "price": Decimal128("380.00"),
                "prep": 18,
                "veg": False,
                "desc": "Tandoori chicken morsels simmered in a velvety sauce of tomatoes, butter, cashew cream, and dried fenugreek.",
                "img": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Dal Makhani Grand Cru",
                "price": Decimal128("280.00"),
                "prep": 15,
                "veg": True,
                "desc": "Whole black lentils slow-simmered for 24 hours on tandoor embers with churned white butter.",
                "img": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Kashmiri Mutton Rogan Josh",
                "price": Decimal128("460.00"),
                "prep": 25,
                "veg": False,
                "desc": "Prime mutton cuts slow-braised in aromatic Kashmiri shallot, fennel, and rattan jot gravy.",
                "img": "https://images.unsplash.com/photo-1545247181-516773cae754?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Kadhai Paneer Peshawari",
                "price": Decimal128("310.00"),
                "prep": 16,
                "veg": True,
                "desc": "Cottage cheese chunks tossed in iron wok with pounded coriander seeds, whole red chilies, and onions.",
                "img": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=600&auto=format&fit=crop&q=80"
            }
        ]
    },
    {
        "category": "Biryanis & Rice",
        "description": "Aromatic long-grain basmati dum biryanis layered with saffron, mint, and royal spices",
        "dishes": [
            {
                "name": "Hyderabadi Chicken Dum Biryani",
                "price": Decimal128("340.00"),
                "prep": 20,
                "veg": False,
                "desc": "Kacchi yakhni basmati rice sealed with dough and slow-cooked over gentle coals. Served with mirchi ka salan.",
                "img": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Nawabi Subz Dum Biryani",
                "price": Decimal128("280.00"),
                "prep": 18,
                "veg": True,
                "desc": "Seasonal garden vegetables, golden paneer, and long grain rice infused with rose water and saffron.",
                "img": "https://images.unsplash.com/photo-1642821373181-696a54913e9a?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Royal Mutton Dum Biryani",
                "price": Decimal128("480.00"),
                "prep": 25,
                "veg": False,
                "desc": "Juicy bone-in goat meat slow cooked with brown onions, mint, and pure ghee aged basmati rice.",
                "img": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Jeera Rice & Ghee Pulav",
                "price": Decimal128("190.00"),
                "prep": 10,
                "veg": True,
                "desc": "Fragrant steamed basmati tempered with royal cumin seeds and clarified desi cow ghee.",
                "img": "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&auto=format&fit=crop&q=80"
            }
        ]
    },
    {
        "category": "Indian Breads",
        "description": "Freshly slapped tandoor naans, crispy kulchas, and whole wheat rotis",
        "dishes": [
            {
                "name": "Butter Garlic Naan",
                "price": Decimal128("85.00"),
                "prep": 8,
                "veg": True,
                "desc": "Fluffy leavened refined flour bread studded with minced garlic, fresh cilantro, and generous farm butter.",
                "img": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Tandoori Butter Roti",
                "price": Decimal128("45.00"),
                "prep": 6,
                "veg": True,
                "desc": "Crisp whole wheat flatbread baked inside charcoal clay oven, topped with butter.",
                "img": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Amritsari Paneer Kulcha",
                "price": Decimal128("120.00"),
                "prep": 10,
                "veg": True,
                "desc": "Flaky layered bread stuffed with spiced crushed cottage cheese, ajwain, and chopped green chillies.",
                "img": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Lachha Paratha",
                "price": Decimal128("75.00"),
                "prep": 8,
                "veg": True,
                "desc": "Crispy multi-layered spiraled wheat bread roasted with ghee until golden crisp.",
                "img": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80"
            }
        ]
    },
    {
        "category": "Desserts & Beverages",
        "description": "Traditional royal sweet treats, rich creamy lassis, and hot aromatic tea",
        "dishes": [
            {
                "name": "Gulab Jamun with Rabri",
                "price": Decimal128("160.00"),
                "prep": 5,
                "veg": True,
                "desc": "Warm khoya dumplings steeped in rose cardamom syrup, crowned with chilled thickened rabri.",
                "img": "https://images.unsplash.com/photo-1541832676-9b763b0239ab?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Kesar Pista Rasmalai",
                "price": Decimal128("180.00"),
                "prep": 5,
                "veg": True,
                "desc": "Spongy chhena discs immersed in clotted saffron milk garnished with slivered pistachios and almonds.",
                "img": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Mango Kesar Lassi",
                "price": Decimal128("140.00"),
                "prep": 5,
                "veg": True,
                "desc": "Thick churned creamy yogurt whipped with Alphonso mango pulp and fragrant saffron strands.",
                "img": "https://images.unsplash.com/photo-1553787499-6f9133860278?w=600&auto=format&fit=crop&q=80"
            },
            {
                "name": "Kadak Masala Chai",
                "price": Decimal128("60.00"),
                "prep": 5,
                "veg": True,
                "desc": "Brewed Assam tea leaves infused with crushed fresh ginger, cardamom, cinnamon, and whole milk.",
                "img": "https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=600&auto=format&fit=crop&q=80"
            }
        ]
    }
]

# Wipe old dishes to eliminate all duplicates
menu_items_collection.delete_many({})

for section in MENU_DATA:
    cat_name = section["category"]
    cat_desc = section["description"]
    
    # Find or insert category
    cat_doc = menu_categories_collection.find_one({"name": cat_name})
    if not cat_doc:
        res = menu_categories_collection.insert_one({
            "name": cat_name,
            "description": cat_desc,
            "created_at": now_utc()
        })
        cat_id = res.inserted_id
    else:
        cat_id = cat_doc["_id"]
        menu_categories_collection.update_one({"_id": cat_id}, {"$set": {"description": cat_desc}})
    
    for d in section["dishes"]:
        menu_items_collection.insert_one({
            "name": d["name"],
            "description": d["desc"],
            "category_id": cat_id,
            "price": d["price"],
            "preparation_time": d["prep"],
            "is_available": True,
            "is_vegetarian": d["veg"],
            "image_url": d["img"],
            "created_at": now_utc()
        })

print(f"Categories ready: {menu_categories_collection.count_documents({})}")
print(f"Menu items ready: {menu_items_collection.count_documents({})}")
