"""
DineFlow - Menu Hierarchy Seeder.
Seeds the required Menu Hierarchy:
Category -> Subcategory -> Menu Item
Categories:
  - VEG (Main Course, Indian Breads)
  - NON-VEG (Main Course, Biryani)
  - STARTERS (Veg Starters, Non-Veg Starters)
  - DESSERTS (Desserts)
Includes realistic pricing, recipe ingredient links, and inventory stocks.
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

CATEGORIES_DEF = [
    {
        "name": "VEG",
        "description": "Vegetarian specialties prepared with pure, fresh produce, paneer, and rich gravies.",
        "food_type": "Veg",
        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600",
        "display_order": 1,
        "is_active": True,
        "subcategories": [
            {
                "name": "Main Course",
                "description": "Traditional North & South Indian vegetarian curries and gravies.",
                "display_order": 1,
                "items": [
                    {
                        "name": "Paneer Butter Masala",
                        "price": Decimal("220"),
                        "base_price": Decimal("220"),
                        "discount": Decimal("0"),
                        "tax": Decimal("11.00"),
                        "final_price": Decimal("231.00"),
                        "preparation_time": 20,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "spicy_level": "Medium",
                        "serving_size": "Serves 2",
                        "tags": ["Chef Special", "Popular", "Paneer"],
                        "description": "Cottage cheese cubes cooked in a rich, buttery tomato cream gravy with aromatic spices.",
                        "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600",
                        "recipe": [
                            {"ingredient": "Paneer", "qty": Decimal("150"), "unit": "GRAM"},
                            {"ingredient": "Butter", "qty": Decimal("30"), "unit": "GRAM"},
                            {"ingredient": "Tomato", "qty": Decimal("100"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("20"), "unit": "ML"},
                            {"ingredient": "Garam Masala", "qty": Decimal("10"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Kaju Curry",
                        "price": Decimal("220"),
                        "base_price": Decimal("220"),
                        "discount": Decimal("0"),
                        "tax": Decimal("11.00"),
                        "final_price": Decimal("231.00"),
                        "preparation_time": 20,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "spicy_level": "Mild",
                        "serving_size": "Serves 2",
                        "tags": ["Rich", "Cashew", "Mughlai"],
                        "description": "Roasted cashew nuts simmered in a luscious onion-tomato cream gravy.",
                        "image_url": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=600",
                        "recipe": [
                            {"ingredient": "Cashew Nuts", "qty": Decimal("80"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("25"), "unit": "ML"},
                            {"ingredient": "Onion", "qty": Decimal("80"), "unit": "GRAM"},
                            {"ingredient": "Tomato", "qty": Decimal("60"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Veg Kadai",
                        "price": Decimal("200"),
                        "base_price": Decimal("200"),
                        "discount": Decimal("0"),
                        "tax": Decimal("10.00"),
                        "final_price": Decimal("210.00"),
                        "preparation_time": 18,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "spicy_level": "Spicy",
                        "serving_size": "Serves 2",
                        "tags": ["Kadai", "Fresh Veggies"],
                        "description": "Assorted garden vegetables and bell peppers wok-tossed in freshly ground kadai spices.",
                        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600",
                        "recipe": [
                            {"ingredient": "Onion", "qty": Decimal("60"), "unit": "GRAM"},
                            {"ingredient": "Tomato", "qty": Decimal("60"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("25"), "unit": "ML"},
                            {"ingredient": "Garam Masala", "qty": Decimal("15"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Mushroom Masala",
                        "price": Decimal("210"),
                        "base_price": Decimal("210"),
                        "discount": Decimal("0"),
                        "tax": Decimal("10.50"),
                        "final_price": Decimal("220.50"),
                        "preparation_time": 20,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "spicy_level": "Medium",
                        "serving_size": "Serves 2",
                        "tags": ["Mushroom", "Spicy Gravy"],
                        "description": "Tender button mushrooms cooked in a spiced onion-tomato masala with herbs.",
                        "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600",
                        "recipe": [
                            {"ingredient": "Onion", "qty": Decimal("70"), "unit": "GRAM"},
                            {"ingredient": "Tomato", "qty": Decimal("60"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("20"), "unit": "ML"},
                        ]
                    },
                    {
                        "name": "Dal Tadka",
                        "price": Decimal("160"),
                        "base_price": Decimal("160"),
                        "discount": Decimal("0"),
                        "tax": Decimal("8.00"),
                        "final_price": Decimal("168.00"),
                        "preparation_time": 15,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "spicy_level": "Medium",
                        "serving_size": "Serves 2",
                        "tags": ["Comfort Food", "Dal", "Tadka"],
                        "description": "Yellow lentils tempered with ghee, cumin seeds, garlic, dried red chili, and fresh coriander.",
                        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600",
                        "recipe": [
                            {"ingredient": "Onion", "qty": Decimal("40"), "unit": "GRAM"},
                            {"ingredient": "Tomato", "qty": Decimal("40"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("20"), "unit": "ML"},
                        ]
                    },
                ]
            },
            {
                "name": "Indian Breads",
                "description": "Clay-oven baked naans, crispy tandoori rotis, and delicate flatbreads.",
                "display_order": 2,
                "items": [
                    {
                        "name": "Naan",
                        "price": Decimal("50"),
                        "base_price": Decimal("50"),
                        "discount": Decimal("0"),
                        "tax": Decimal("2.50"),
                        "final_price": Decimal("52.50"),
                        "preparation_time": 10,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "serving_size": "1 Piece",
                        "tags": ["Tandoor", "Bread"],
                        "description": "Traditional leavened oven-baked flatbread cooked on clay tandoor walls.",
                        "image_url": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600",
                        "recipe": [
                            {"ingredient": "Flour", "qty": Decimal("100"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Butter Naan",
                        "price": Decimal("50"),
                        "base_price": Decimal("50"),
                        "discount": Decimal("0"),
                        "tax": Decimal("2.50"),
                        "final_price": Decimal("52.50"),
                        "preparation_time": 8,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "serving_size": "1 Piece",
                        "tags": ["Tandoor", "Butter", "Bread"],
                        "description": "Crispy yet soft tandoori naan brushed generously with melted dairy butter.",
                        "image_url": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600",
                        "recipe": [
                            {"ingredient": "Flour", "qty": Decimal("100"), "unit": "GRAM"},
                            {"ingredient": "Butter", "qty": Decimal("15"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Garlic Naan",
                        "price": Decimal("70"),
                        "base_price": Decimal("70"),
                        "discount": Decimal("0"),
                        "tax": Decimal("3.50"),
                        "final_price": Decimal("73.50"),
                        "preparation_time": 10,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "serving_size": "1 Piece",
                        "tags": ["Garlic", "Aromatic", "Bread"],
                        "description": "Clay oven baked flatbread infused with roasted garlic and fresh coriander.",
                        "image_url": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600",
                        "recipe": [
                            {"ingredient": "Flour", "qty": Decimal("100"), "unit": "GRAM"},
                            {"ingredient": "Butter", "qty": Decimal("15"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Rumali Roti",
                        "price": Decimal("40"),
                        "base_price": Decimal("40"),
                        "discount": Decimal("0"),
                        "tax": Decimal("2.00"),
                        "final_price": Decimal("42.00"),
                        "preparation_time": 8,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "serving_size": "1 Piece",
                        "tags": ["Thin", "Mughlai"],
                        "description": "Ultra-thin, soft handkerchief flatbread hand-stretched and cooked on an inverted kadai.",
                        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600",
                        "recipe": [
                            {"ingredient": "Flour", "qty": Decimal("80"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Tandoori Roti",
                        "price": Decimal("35"),
                        "base_price": Decimal("35"),
                        "discount": Decimal("0"),
                        "tax": Decimal("1.75"),
                        "final_price": Decimal("36.75"),
                        "preparation_time": 6,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "serving_size": "1 Piece",
                        "tags": ["Whole Wheat", "Healthy"],
                        "description": "Whole wheat flatbread baked crisp and smoking hot in the traditional clay tandoor.",
                        "image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=600",
                        "recipe": [
                            {"ingredient": "Flour", "qty": Decimal("80"), "unit": "GRAM"},
                        ]
                    },
                ]
            }
        ]
    },
    {
        "name": "NON-VEG",
        "description": "Succulent chicken, mutton, and fresh seafood specialties prepared with aromatic spices.",
        "food_type": "Non-Veg",
        "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600",
        "display_order": 2,
        "is_active": True,
        "subcategories": [
            {
                "name": "Main Course",
                "description": "Rich chicken, mutton, and coastal fish curries.",
                "display_order": 1,
                "items": [
                    {
                        "name": "Chicken Curry",
                        "price": Decimal("260"),
                        "base_price": Decimal("260"),
                        "discount": Decimal("0"),
                        "tax": Decimal("13.00"),
                        "final_price": Decimal("273.00"),
                        "preparation_time": 22,
                        "is_vegetarian": False,
                        "food_type": "Non-Veg",
                        "type": "Non-Veg",
                        "spicy_level": "Spicy",
                        "serving_size": "Serves 2",
                        "tags": ["Homestyle", "Spicy"],
                        "description": "Tender bone-in chicken simmered in an aromatic onion, ginger-garlic, and whole-spice gravy.",
                        "image_url": "https://images.unsplash.com/photo-1545247181-516773cae754?w=600",
                        "recipe": [
                            {"ingredient": "Chicken", "qty": Decimal("220"), "unit": "GRAM"},
                            {"ingredient": "Onion", "qty": Decimal("70"), "unit": "GRAM"},
                            {"ingredient": "Tomato", "qty": Decimal("60"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("25"), "unit": "ML"},
                        ]
                    },
                    {
                        "name": "Butter Chicken",
                        "price": Decimal("280"),
                        "base_price": Decimal("280"),
                        "discount": Decimal("0"),
                        "tax": Decimal("14.00"),
                        "final_price": Decimal("294.00"),
                        "preparation_time": 25,
                        "is_vegetarian": False,
                        "food_type": "Non-Veg",
                        "type": "Non-Veg",
                        "spicy_level": "Mild",
                        "serving_size": "Serves 2",
                        "tags": ["Chef Special", "Popular", "Makhani"],
                        "description": "Smoked tandoori chicken cooked in a velvety tomato, dairy butter, and cashew cream gravy.",
                        "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600",
                        "recipe": [
                            {"ingredient": "Chicken", "qty": Decimal("200"), "unit": "GRAM"},
                            {"ingredient": "Butter", "qty": Decimal("35"), "unit": "GRAM"},
                            {"ingredient": "Tomato", "qty": Decimal("100"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("20"), "unit": "ML"},
                        ]
                    },
                    {
                        "name": "Chicken Tikka Masala",
                        "price": Decimal("290"),
                        "base_price": Decimal("290"),
                        "discount": Decimal("0"),
                        "tax": Decimal("14.50"),
                        "final_price": Decimal("304.50"),
                        "preparation_time": 22,
                        "is_vegetarian": False,
                        "food_type": "Non-Veg",
                        "type": "Non-Veg",
                        "spicy_level": "Medium",
                        "serving_size": "Serves 2",
                        "tags": ["Tandoor", "Tikka"],
                        "description": "Char-grilled marinated chicken tikka pieces in a robust, spiced bell pepper and tomato gravy.",
                        "image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=600",
                        "recipe": [
                            {"ingredient": "Chicken", "qty": Decimal("200"), "unit": "GRAM"},
                            {"ingredient": "Onion", "qty": Decimal("60"), "unit": "GRAM"},
                            {"ingredient": "Tomato", "qty": Decimal("70"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("20"), "unit": "ML"},
                        ]
                    },
                    {
                        "name": "Mutton Curry",
                        "price": Decimal("320"),
                        "base_price": Decimal("320"),
                        "discount": Decimal("0"),
                        "tax": Decimal("16.00"),
                        "final_price": Decimal("336.00"),
                        "preparation_time": 25,
                        "is_vegetarian": False,
                        "food_type": "Non-Veg",
                        "type": "Non-Veg",
                        "spicy_level": "Spicy",
                        "serving_size": "Serves 2",
                        "tags": ["Mutton", "Royal"],
                        "description": "Slow-cooked tender bone-in goat meat braised with whole spices, browned onions, and yogurt.",
                        "image_url": "https://images.unsplash.com/photo-1545247181-516773cae754?w=600",
                        "recipe": [
                            {"ingredient": "Mutton", "qty": Decimal("220"), "unit": "GRAM"},
                            {"ingredient": "Onion", "qty": Decimal("80"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("30"), "unit": "ML"},
                            {"ingredient": "Garam Masala", "qty": Decimal("15"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Fish Curry",
                        "price": Decimal("320"),
                        "base_price": Decimal("320"),
                        "discount": Decimal("0"),
                        "tax": Decimal("16.00"),
                        "final_price": Decimal("336.00"),
                        "preparation_time": 20,
                        "is_vegetarian": False,
                        "food_type": "Non-Veg",
                        "type": "Non-Veg",
                        "spicy_level": "Medium",
                        "serving_size": "Serves 2",
                        "tags": ["Coastal", "Seafood"],
                        "description": "Fresh fish steaks simmered in a tangy coconut, tamarind, and mustard seed coastal gravy.",
                        "image_url": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=600",
                        "recipe": [
                            {"ingredient": "Fish", "qty": Decimal("200"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("25"), "unit": "ML"},
                            {"ingredient": "Tomato", "qty": Decimal("50"), "unit": "GRAM"},
                        ]
                    },
                ]
            },
            {
                "name": "Biryani",
                "description": "Authentic dum biryanis cooked in sealed copper handis.",
                "display_order": 2,
                "items": [
                    {
                        "name": "Chicken Dum Biryani",
                        "price": Decimal("250"),
                        "base_price": Decimal("250"),
                        "discount": Decimal("0"),
                        "tax": Decimal("12.50"),
                        "final_price": Decimal("262.50"),
                        "preparation_time": 25,
                        "is_vegetarian": False,
                        "food_type": "Non-Veg",
                        "type": "Non-Veg",
                        "spicy_level": "Medium",
                        "serving_size": "Serves 1-2",
                        "tags": ["Bestseller", "Hyderabadi", "Dum Biryani"],
                        "description": "Aromatic basmati rice cooked with marinated chicken and traditional spices in authentic dum style.",
                        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600",
                        "recipe": [
                            {"ingredient": "Basmati Rice", "qty": Decimal("250"), "unit": "GRAM"},
                            {"ingredient": "Chicken", "qty": Decimal("200"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("30"), "unit": "ML"},
                            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
                            {"ingredient": "Garam Masala", "qty": Decimal("10"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Mutton Biryani",
                        "price": Decimal("320"),
                        "base_price": Decimal("320"),
                        "discount": Decimal("0"),
                        "tax": Decimal("16.00"),
                        "final_price": Decimal("336.00"),
                        "preparation_time": 30,
                        "is_vegetarian": False,
                        "food_type": "Non-Veg",
                        "type": "Non-Veg",
                        "spicy_level": "Spicy",
                        "serving_size": "Serves 1-2",
                        "tags": ["Chef Special", "Mutton", "Royal"],
                        "description": "Fragrant basmati rice layered with succulent spiced goat meat, caramelized onions, and saffron milk.",
                        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600",
                        "recipe": [
                            {"ingredient": "Basmati Rice", "qty": Decimal("250"), "unit": "GRAM"},
                            {"ingredient": "Mutton", "qty": Decimal("200"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("30"), "unit": "ML"},
                            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
                            {"ingredient": "Garam Masala", "qty": Decimal("12"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Egg Biryani",
                        "price": Decimal("190"),
                        "base_price": Decimal("190"),
                        "discount": Decimal("0"),
                        "tax": Decimal("9.50"),
                        "final_price": Decimal("199.50"),
                        "preparation_time": 20,
                        "is_vegetarian": False,
                        "food_type": "Non-Veg",
                        "type": "Egg",
                        "spicy_level": "Medium",
                        "serving_size": "Serves 1-2",
                        "tags": ["Egg", "Biryani"],
                        "description": "Hard-boiled golden fried eggs simmered with fragrant basmati dum rice and aromatic masala.",
                        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600",
                        "recipe": [
                            {"ingredient": "Basmati Rice", "qty": Decimal("250"), "unit": "GRAM"},
                            {"ingredient": "Eggs", "qty": Decimal("2"), "unit": "PIECES"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("25"), "unit": "ML"},
                            {"ingredient": "Onion", "qty": Decimal("40"), "unit": "GRAM"},
                        ]
                    },
                ]
            }
        ]
    },
    {
        "name": "STARTERS",
        "description": "Crispy bites, tandoori skewers, and wok-tossed appetizers to kick off your dining experience.",
        "food_type": "Both",
        "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600",
        "display_order": 3,
        "is_active": True,
        "subcategories": [
            {
                "name": "Veg Starters",
                "description": "Crispy, spiced, and clay-oven grilled vegetarian appetizers.",
                "display_order": 1,
                "items": [
                    {
                        "name": "Paneer Tikka",
                        "price": Decimal("220"),
                        "base_price": Decimal("220"),
                        "discount": Decimal("0"),
                        "tax": Decimal("11.00"),
                        "final_price": Decimal("231.00"),
                        "preparation_time": 20,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "spicy_level": "Medium",
                        "serving_size": "6 Pieces",
                        "tags": ["Tandoor", "Paneer", "Starters"],
                        "description": "Succulent cubes of paneer marinated in spiced yogurt and grilled over hot tandoor coals.",
                        "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600",
                        "recipe": [
                            {"ingredient": "Paneer", "qty": Decimal("180"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("20"), "unit": "ML"},
                            {"ingredient": "Garam Masala", "qty": Decimal("10"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Gobi Manchurian",
                        "price": Decimal("180"),
                        "base_price": Decimal("180"),
                        "discount": Decimal("0"),
                        "tax": Decimal("9.00"),
                        "final_price": Decimal("189.00"),
                        "preparation_time": 18,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "spicy_level": "Medium",
                        "serving_size": "Serves 2",
                        "tags": ["Indo-Chinese", "Crispy"],
                        "description": "Crispy battered cauliflower florets glazed in a garlic-infused sweet and spicy Manchurian sauce.",
                        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600",
                        "recipe": [
                            {"ingredient": "Flour", "qty": Decimal("50"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("30"), "unit": "ML"},
                        ]
                    },
                    {
                        "name": "Crispy Corn",
                        "price": Decimal("190"),
                        "base_price": Decimal("190"),
                        "discount": Decimal("0"),
                        "tax": Decimal("9.50"),
                        "final_price": Decimal("199.50"),
                        "preparation_time": 15,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "spicy_level": "Medium",
                        "serving_size": "Serves 2",
                        "tags": ["Crispy", "Corn", "Snack"],
                        "description": "Golden sweet corn kernels flash-fried until crunchy, seasoned with chaat masala and lime.",
                        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600",
                        "recipe": [
                            {"ingredient": "Flour", "qty": Decimal("40"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("25"), "unit": "ML"},
                        ]
                    },
                    {
                        "name": "Veg Manchurian",
                        "price": Decimal("180"),
                        "base_price": Decimal("180"),
                        "discount": Decimal("0"),
                        "tax": Decimal("9.00"),
                        "final_price": Decimal("189.00"),
                        "preparation_time": 18,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "spicy_level": "Medium",
                        "serving_size": "Serves 2",
                        "tags": ["Indo-Chinese", "Vegetables"],
                        "description": "Deep-fried mixed vegetable dumplings tossed in a savory ginger, garlic, and scallion sauce.",
                        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600",
                        "recipe": [
                            {"ingredient": "Flour", "qty": Decimal("50"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("30"), "unit": "ML"},
                        ]
                    },
                ]
            },
            {
                "name": "Non-Veg Starters",
                "description": "Crispy chicken skewers, spicy wings, and Indo-Chinese bites.",
                "display_order": 2,
                "items": [
                    {
                        "name": "Chicken 65",
                        "price": Decimal("240"),
                        "base_price": Decimal("240"),
                        "discount": Decimal("0"),
                        "tax": Decimal("12.00"),
                        "final_price": Decimal("252.00"),
                        "preparation_time": 20,
                        "is_vegetarian": False,
                        "food_type": "Non-Veg",
                        "type": "Non-Veg",
                        "spicy_level": "Spicy",
                        "serving_size": "Serves 2",
                        "tags": ["Bestseller", "South Indian", "Crispy"],
                        "description": "Crispy deep-fried chicken tossed in a spicy, tangy tempering of curry leaves and red chilies.",
                        "image_url": "https://images.unsplash.com/photo-1610057099431-d73a1c9d2f2f?w=600",
                        "recipe": [
                            {"ingredient": "Chicken", "qty": Decimal("200"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("35"), "unit": "ML"},
                            {"ingredient": "Garam Masala", "qty": Decimal("10"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Chicken Lollipop",
                        "price": Decimal("280"),
                        "base_price": Decimal("280"),
                        "discount": Decimal("0"),
                        "tax": Decimal("14.00"),
                        "final_price": Decimal("294.00"),
                        "preparation_time": 22,
                        "is_vegetarian": False,
                        "food_type": "Non-Veg",
                        "type": "Non-Veg",
                        "spicy_level": "Medium",
                        "serving_size": "6 Pieces",
                        "tags": ["Appetizer", "Indo-Chinese"],
                        "description": "Frenched chicken winglets tossed in fiery Indo-Chinese Szechuan glaze.",
                        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600",
                        "recipe": [
                            {"ingredient": "Chicken", "qty": Decimal("220"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("35"), "unit": "ML"},
                        ]
                    },
                    {
                        "name": "Chilli Chicken",
                        "price": Decimal("250"),
                        "base_price": Decimal("250"),
                        "discount": Decimal("0"),
                        "tax": Decimal("12.50"),
                        "final_price": Decimal("262.50"),
                        "preparation_time": 20,
                        "is_vegetarian": False,
                        "food_type": "Non-Veg",
                        "type": "Non-Veg",
                        "spicy_level": "Spicy",
                        "serving_size": "Serves 2",
                        "tags": ["Indo-Chinese", "Chilli"],
                        "description": "Tender chicken chunks wok-tossed with green chilies, bell peppers, soy sauce, and scallions.",
                        "image_url": "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=600",
                        "recipe": [
                            {"ingredient": "Chicken", "qty": Decimal("200"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("25"), "unit": "ML"},
                            {"ingredient": "Onion", "qty": Decimal("40"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Chicken Manchurian",
                        "price": Decimal("250"),
                        "base_price": Decimal("250"),
                        "discount": Decimal("0"),
                        "tax": Decimal("12.50"),
                        "final_price": Decimal("262.50"),
                        "preparation_time": 20,
                        "is_vegetarian": False,
                        "food_type": "Non-Veg",
                        "type": "Non-Veg",
                        "spicy_level": "Medium",
                        "serving_size": "Serves 2",
                        "tags": ["Indo-Chinese", "Manchurian"],
                        "description": "Chicken bites tossed in garlic-rich Indo-Chinese dark soya sauce with ginger and scallions.",
                        "image_url": "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=600",
                        "recipe": [
                            {"ingredient": "Chicken", "qty": Decimal("200"), "unit": "GRAM"},
                            {"ingredient": "Cooking Oil", "qty": Decimal("25"), "unit": "ML"},
                        ]
                    },
                ]
            }
        ]
    },
    {
        "name": "DESSERTS",
        "description": "Delectable traditional Indian sweets and chilled artisan desserts to complete your meal.",
        "food_type": "Veg",
        "image_url": "https://images.unsplash.com/photo-1605197586548-932f146a782b?w=600",
        "display_order": 4,
        "is_active": True,
        "subcategories": [
            {
                "name": "Desserts",
                "description": "Warm milk dumplings, chilled creams, and chocolate brownies.",
                "display_order": 1,
                "items": [
                    {
                        "name": "Gulab Jamun",
                        "price": Decimal("80"),
                        "base_price": Decimal("80"),
                        "discount": Decimal("0"),
                        "tax": Decimal("4.00"),
                        "final_price": Decimal("84.00"),
                        "preparation_time": 8,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "serving_size": "2 Pieces",
                        "tags": ["Traditional", "Warm", "Sweet"],
                        "description": "Deep-fried milk dumplings soaked in warm rosewater and green cardamom scented sugar syrup.",
                        "image_url": "https://images.unsplash.com/photo-1605197586548-932f146a782b?w=600",
                        "recipe": [
                            {"ingredient": "Sugar", "qty": Decimal("50"), "unit": "GRAM"},
                            {"ingredient": "Milk", "qty": Decimal("100"), "unit": "ML"},
                        ]
                    },
                    {
                        "name": "Rasmalai",
                        "price": Decimal("110"),
                        "base_price": Decimal("110"),
                        "discount": Decimal("0"),
                        "tax": Decimal("5.50"),
                        "final_price": Decimal("115.50"),
                        "preparation_time": 10,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "serving_size": "2 Pieces",
                        "tags": ["Chilled", "Royal", "Saffron"],
                        "description": "Soft cottage cheese patties immersed in chilled, saffron and pistachio infused sweetened milk.",
                        "image_url": "https://images.unsplash.com/photo-1605197586548-932f146a782b?w=600",
                        "recipe": [
                            {"ingredient": "Milk", "qty": Decimal("150"), "unit": "ML"},
                            {"ingredient": "Sugar", "qty": Decimal("40"), "unit": "GRAM"},
                        ]
                    },
                    {
                        "name": "Ice Cream",
                        "price": Decimal("100"),
                        "base_price": Decimal("100"),
                        "discount": Decimal("0"),
                        "tax": Decimal("5.00"),
                        "final_price": Decimal("105.00"),
                        "preparation_time": 5,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "serving_size": "2 Scoops",
                        "tags": ["Chilled", "Classic"],
                        "description": "Rich and creamy vanilla and Belgian chocolate scoops served chilled.",
                        "image_url": "https://images.unsplash.com/photo-1501443762994-82bd5dace89a?w=600",
                        "recipe": []
                    },
                    {
                        "name": "Brownie",
                        "price": Decimal("140"),
                        "base_price": Decimal("140"),
                        "discount": Decimal("0"),
                        "tax": Decimal("7.00"),
                        "final_price": Decimal("147.00"),
                        "preparation_time": 10,
                        "is_vegetarian": True,
                        "food_type": "Veg",
                        "type": "Veg",
                        "serving_size": "1 Piece",
                        "tags": ["Chocolate", "Warm"],
                        "description": "Warm, fudgy chocolate walnut brownie drizzled with rich chocolate ganache.",
                        "image_url": "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=600",
                        "recipe": []
                    },
                ]
            }
        ]
    }
]

# Ensure base inventory ingredients exist for these recipes
BASE_INGREDIENTS = [
    {"name": "Basmati Rice", "unit": "GRAM", "stock": Decimal("10000"), "min": Decimal("2000"), "cost": Decimal("0.08"), "category": "Grains"},
    {"name": "Chicken", "unit": "GRAM", "stock": Decimal("5000"), "min": Decimal("1000"), "cost": Decimal("0.25"), "category": "Meat"},
    {"name": "Mutton", "unit": "GRAM", "stock": Decimal("4000"), "min": Decimal("1000"), "cost": Decimal("0.55"), "category": "Meat"},
    {"name": "Fish", "unit": "GRAM", "stock": Decimal("3000"), "min": Decimal("800"), "cost": Decimal("0.40"), "category": "Seafood"},
    {"name": "Paneer", "unit": "GRAM", "stock": Decimal("4000"), "min": Decimal("800"), "cost": Decimal("0.30"), "category": "Dairy"},
    {"name": "Butter", "unit": "GRAM", "stock": Decimal("3000"), "min": Decimal("500"), "cost": Decimal("0.45"), "category": "Dairy"},
    {"name": "Milk", "unit": "ML", "stock": Decimal("10000"), "min": Decimal("2000"), "cost": Decimal("0.06"), "category": "Dairy"},
    {"name": "Flour", "unit": "GRAM", "stock": Decimal("8000"), "min": Decimal("1500"), "cost": Decimal("0.04"), "category": "Pantry"},
    {"name": "Cooking Oil", "unit": "ML", "stock": Decimal("10000"), "min": Decimal("2000"), "cost": Decimal("0.15"), "category": "Oils"},
    {"name": "Onion", "unit": "GRAM", "stock": Decimal("8000"), "min": Decimal("1500"), "cost": Decimal("0.03"), "category": "Vegetables"},
    {"name": "Tomato", "unit": "GRAM", "stock": Decimal("6000"), "min": Decimal("1500"), "cost": Decimal("0.04"), "category": "Vegetables"},
    {"name": "Cashew Nuts", "unit": "GRAM", "stock": Decimal("2000"), "min": Decimal("500"), "cost": Decimal("0.90"), "category": "Pantry"},
    {"name": "Sugar", "unit": "GRAM", "stock": Decimal("5000"), "min": Decimal("1000"), "cost": Decimal("0.05"), "category": "Pantry"},
    {"name": "Garam Masala", "unit": "GRAM", "stock": Decimal("2000"), "min": Decimal("400"), "cost": Decimal("0.60"), "category": "Spices"},
    {"name": "Eggs", "unit": "PIECES", "stock": Decimal("100"), "min": Decimal("20"), "cost": Decimal("6.00"), "category": "Poultry"},
]


def seed_menu_hierarchy():
    print("=== Seeding Menu Hierarchy (Category -> Subcategory -> Item) ===")

    # 1. Ensure master ingredients exist
    ing_map = {}
    for ing in BASE_INGREDIENTS:
        existing = ingredients_collection.find_one({"name": {"$regex": f"^{ing['name']}$", "$options": "i"}})
        if existing:
            ing_map[ing["name"].lower()] = existing["_id"]
        else:
            ins = ingredients_collection.insert_one({
                "name": ing["name"],
                "unit": ing["unit"],
                "available_quantity": decimal128(ing["stock"]),
                "current_stock": decimal128(ing["stock"]),
                "minimum_stock_level": decimal128(ing["min"]),
                "reorder_level": decimal128(ing["min"]),
                "cost_per_unit": decimal128(ing["cost"]),
                "category": ing["category"],
                "is_active": True,
                "created_at": now_utc(),
            })
            ing_map[ing["name"].lower()] = ins.inserted_id

    # 2. Iterate categories, subcategories, items
    for cat_def in CATEGORIES_DEF:
        cat_name = cat_def["name"]
        cat_doc = menu_categories_collection.find_one({"name": {"$regex": f"^{cat_name}$", "$options": "i"}})
        if not cat_doc:
            cat_ins = menu_categories_collection.insert_one({
                "name": cat_name,
                "description": cat_def["description"],
                "food_type": cat_def["food_type"],
                "image_url": cat_def["image_url"],
                "display_order": cat_def["display_order"],
                "is_active": True,
                "created_at": now_utc(),
                "updated_at": now_utc(),
            })
            cat_id = cat_ins.inserted_id
        else:
            cat_id = cat_doc["_id"]
            menu_categories_collection.update_one(
                {"_id": cat_id},
                {"$set": {
                    "food_type": cat_def["food_type"],
                    "display_order": cat_def["display_order"],
                    "is_active": True,
                    "updated_at": now_utc(),
                }}
            )

        # Subcategories
        for sub_def in cat_def.get("subcategories", []):
            sub_name = sub_def["name"]
            sub_doc = menu_subcategories_collection.find_one({
                "category_id": {"$in": [cat_id, str(cat_id)]},
                "name": {"$regex": f"^{sub_name}$", "$options": "i"},
            })
            if not sub_doc:
                sub_ins = menu_subcategories_collection.insert_one({
                    "name": sub_name,
                    "category_id": cat_id,
                    "category_name": cat_name,
                    "description": sub_def["description"],
                    "display_order": sub_def["display_order"],
                    "is_active": True,
                    "created_at": now_utc(),
                    "updated_at": now_utc(),
                })
                sub_id = sub_ins.inserted_id
            else:
                sub_id = sub_doc["_id"]
                menu_subcategories_collection.update_one(
                    {"_id": sub_id},
                    {"$set": {
                        "category_name": cat_name,
                        "display_order": sub_def["display_order"],
                        "is_active": True,
                        "updated_at": now_utc(),
                    }}
                )

            # Items
            for item_idx, itm_def in enumerate(sub_def.get("items", []), start=1):
                item_name = itm_def["name"]
                item_doc = menu_items_collection.find_one({"name": {"$regex": f"^{item_name}$", "$options": "i"}})
                item_payload = {
                    "name": item_name,
                    "description": itm_def.get("description"),
                    "category_id": cat_id,
                    "category_name": cat_name,
                    "subcategory_id": sub_id,
                    "subcategory_name": sub_name,
                    "price": decimal128(itm_def["price"]),
                    "base_price": decimal128(itm_def.get("base_price", itm_def["price"])),
                    "discount": decimal128(itm_def.get("discount", Decimal("0"))),
                    "tax": decimal128(itm_def.get("tax", Decimal("0"))),
                    "final_price": decimal128(itm_def.get("final_price", itm_def["price"])),
                    "preparation_time": itm_def["preparation_time"],
                    "is_available": True,
                    "is_active": True,
                    "is_vegetarian": itm_def["is_vegetarian"],
                    "food_type": itm_def.get("food_type", "Veg" if itm_def["is_vegetarian"] else "Non-Veg"),
                    "type": itm_def.get("type", "Veg" if itm_def["is_vegetarian"] else "Non-Veg"),
                    "image_url": itm_def.get("image_url"),
                    "display_order": item_idx,
                    "spicy_level": itm_def.get("spicy_level"),
                    "serving_size": itm_def.get("serving_size"),
                    "tags": itm_def.get("tags", []),
                    "inventory_tracking_enabled": True,
                    "updated_at": now_utc(),
                }

                if not item_doc:
                    item_payload["created_at"] = now_utc()
                    ins = menu_items_collection.insert_one(item_payload)
                    menu_item_id = ins.inserted_id
                else:
                    menu_item_id = item_doc["_id"]
                    menu_items_collection.update_one({"_id": menu_item_id}, {"$set": item_payload})

                # Seed recipes
                recipes_list = itm_def.get("recipe", [])
                for r in recipes_list:
                    ing_key = r["ingredient"].lower()
                    ing_id = ing_map.get(ing_key)
                    if not ing_id:
                        found = ingredients_collection.find_one({"name": {"$regex": f"^{r['ingredient']}$", "$options": "i"}})
                        if found:
                            ing_id = found["_id"]
                    if ing_id:
                        rec_doc = recipes_collection.find_one({
                            "menu_item_id": {"$in": [menu_item_id, str(menu_item_id)]},
                            "ingredient_id": {"$in": [ing_id, str(ing_id)]},
                        })
                        if not rec_doc:
                            recipes_collection.insert_one({
                                "menu_item_id": menu_item_id,
                                "ingredient_id": ing_id,
                                "quantity_required": decimal128(r["qty"]),
                                "unit": r["unit"],
                                "is_optional": False,
                                "created_at": now_utc(),
                            })

    print("=== Menu Hierarchy successfully seeded ===")


if __name__ == "__main__":
    seed_menu_hierarchy()
