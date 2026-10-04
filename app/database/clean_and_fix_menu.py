"""
Comprehensive Menu Cleaner and Seeder for DineFlow.
1. Resets Categories to the 7 core standard categories:
   - Starters
   - Biryani
   - Main Course
   - Breads
   - Rice & Noodles
   - Desserts
   - Beverages
2. Creates clean subcategories for each category.
3. Cleans junk/test dishes and re-maps all real dishes to their accurate categories, subcategories,
   high-definition matching image URLs, accurate prep times, prices, and veg/non-veg tags.
4. Ensures recipes for Chicken Biryani and other main courses are linked for BOM inventory tracking,
   and starters have 0 recipe deduction.
"""

import sys
import io
import re
from decimal import Decimal
from pathlib import Path
from bson import ObjectId

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database.mongodb import (
    menu_categories_collection,
    menu_subcategories_collection,
    menu_items_collection,
    ingredients_collection,
    recipes_collection,
    db,
)
from app.services.common import now_utc, decimal128

CATEGORIES_SPEC = [
    {
        "name": "Starters",
        "description": "Crispy appetizers, charcoal-grilled tikkas, and sizzling skewers to kickstart your dining experience.",
        "food_type": "Both",
        "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600",
        "display_order": 1,
        "subcategories": [
            {"name": "Veg Starters", "description": "Paneer tikkas, crispy corn, kebabs and vegetable fritters", "display_order": 1},
            {"name": "Non-Veg Starters", "description": "Chicken 65, tikkas, lollipops and seekh kebabs", "display_order": 2},
        ],
    },
    {
        "name": "Biryani",
        "description": "Authentic dum biryanis slow-cooked with aged basmati rice, saffron, and aromatic spices.",
        "food_type": "Both",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600",
        "display_order": 2,
        "subcategories": [
            {"name": "Non-Veg Biryani", "description": "Dum cooked chicken, mutton and egg biryanis", "display_order": 1},
            {"name": "Veg Biryani", "description": "Fresh vegetable and paneer dum biryanis", "display_order": 2},
        ],
    },
    {
        "name": "Main Course",
        "description": "Rich paneer gravies, slow-cooked dal, and hearty chicken and mutton curries.",
        "food_type": "Both",
        "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600",
        "display_order": 3,
        "subcategories": [
            {"name": "Veg Main Course", "description": "Paneer butter masala, kadai paneer, and dal makhani", "display_order": 1},
            {"name": "Non-Veg Main Course", "description": "Butter chicken, chicken curry, and mutton rogan josh", "display_order": 2},
        ],
    },
    {
        "name": "Breads",
        "description": "Freshly baked clay-oven tandoori naans, layered parathas, and traditional rotis.",
        "food_type": "Veg",
        "image_url": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600",
        "display_order": 4,
        "subcategories": [
            {"name": "Tandoori Breads", "description": "Butter naans, garlic naans, and plain naans", "display_order": 1},
            {"name": "Roti & Paratha", "description": "Whole-wheat tandoori rotis and layered laccha parathas", "display_order": 2},
        ],
    },
    {
        "name": "Rice & Noodles",
        "description": "Wok-tossed fried rice and flavorful Indo-Chinese noodles cooked to perfection.",
        "food_type": "Both",
        "image_url": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=600",
        "display_order": 5,
        "subcategories": [
            {"name": "Fried Rice", "description": "Veg, chicken, egg fried rice and jeera rice", "display_order": 1},
            {"name": "Noodles", "description": "Hakka noodles and stir-fried Asian noodles", "display_order": 2},
        ],
    },
    {
        "name": "Desserts",
        "description": "Royal traditional Indian sweets, warm gulab jamuns, and chilled ice creams.",
        "food_type": "Veg",
        "image_url": "https://images.unsplash.com/photo-1553787499-6f9133860278?w=600",
        "display_order": 6,
        "subcategories": [
            {"name": "Traditional Sweets", "description": "Gulab jamun, rasmalai, and double ka meetha", "display_order": 1},
            {"name": "Ice Creams & Sundaes", "description": "Chilled dairy ice creams and sundae scoops", "display_order": 2},
        ],
    },
    {
        "name": "Beverages",
        "description": "Refreshing lassis, cooling lime sodas, frothy cold coffees, and steaming masala chai.",
        "food_type": "Beverage",
        "image_url": "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=600",
        "display_order": 7,
        "subcategories": [
            {"name": "Lassi & Coolers", "description": "Mango lassi, sweet lassi, and fresh lime soda", "display_order": 1},
            {"name": "Hot Beverages & Chai", "description": "Special masala chai and iced cold coffees", "display_order": 2},
        ],
    },
]

DISHES_SPEC = [
    # ==========================================
    # 1. STARTERS
    # ==========================================
    {
        "name": "Paneer Tikka",
        "category": "Starters",
        "subcategory": "Veg Starters",
        "type": "Veg",
        "price": Decimal("220.00"),
        "preparation_time": 20,
        "is_vegetarian": True,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2 (6 Pcs)",
        "tags": ["Chef Special", "Popular", "Tandoor"],
        "description": "Fresh cottage cheese cubes marinated in spiced hung yogurt, mustard oil, and carom seeds, skewered with bell peppers and char-grilled in a clay tandoor.",
        "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Hara Bhara Kebab",
        "category": "Starters",
        "subcategory": "Veg Starters",
        "type": "Veg",
        "price": Decimal("190.00"),
        "preparation_time": 12,
        "is_vegetarian": True,
        "is_available": True,
        "spicy_level": "Mild",
        "serving_size": "Serves 2 (6 Pcs)",
        "tags": ["Healthy", "Vegetarian", "Crispy"],
        "description": "Crispy pan-seared patties prepared with blanched spinach, green peas, mashed potatoes, and roasted gram flour, centered with roasted cashew nuts.",
        "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Crispy Corn Pepper Salt",
        "category": "Starters",
        "subcategory": "Veg Starters",
        "type": "Veg",
        "price": Decimal("180.00"),
        "preparation_time": 10,
        "is_vegetarian": True,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2",
        "tags": ["Crispy", "Popular", "Bar Nibble"],
        "description": "Golden fried American sweet corn kernels tossed with crushed black pepper, spring onions, diced bell peppers, and roasted cumin.",
        "image_url": "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Gobi Manchurian",
        "category": "Starters",
        "subcategory": "Veg Starters",
        "type": "Veg",
        "price": Decimal("180.00"),
        "preparation_time": 18,
        "is_vegetarian": True,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2",
        "tags": ["Indo-Chinese", "Crispy"],
        "description": "Crispy battered cauliflower florets glazed in a garlic-infused sweet and spicy Indo-Chinese Manchurian sauce with scallions.",
        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Veg Manchurian Dry",
        "category": "Starters",
        "subcategory": "Veg Starters",
        "type": "Veg",
        "price": Decimal("190.00"),
        "preparation_time": 14,
        "is_vegetarian": True,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2",
        "tags": ["Indo-Chinese", "Dumplings"],
        "description": "Crispy minced vegetable dumplings tossed with fresh garlic, ginger, chopped scallions, and Indo-Chinese soya chili glaze.",
        "image_url": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Chicken 65",
        "category": "Starters",
        "subcategory": "Non-Veg Starters",
        "type": "Non-Veg",
        "price": Decimal("240.00"),
        "preparation_time": 20,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Spicy",
        "serving_size": "Serves 2 (8 Pcs)",
        "tags": ["Best Seller", "South Indian", "Spicy"],
        "description": "Authentic Chennai-style crispy fried chicken bites tossed with fresh curry leaves, whole red chillies, ginger, and garlic.",
        "image_url": "https://images.unsplash.com/photo-1610057099431-d73a1c9d2f2f?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Chicken Tikka",
        "category": "Starters",
        "subcategory": "Non-Veg Starters",
        "type": "Non-Veg",
        "price": Decimal("260.00"),
        "preparation_time": 16,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2 (6 Pcs)",
        "tags": ["Tandoor", "Popular", "Smoky"],
        "description": "Succulent boneless chicken morsels steeped in spiced yogurt, smoked paprika, and lime, roasted in a traditional charcoal clay tandoor.",
        "image_url": "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Chicken Lollipop",
        "category": "Starters",
        "subcategory": "Non-Veg Starters",
        "type": "Non-Veg",
        "price": Decimal("280.00"),
        "preparation_time": 22,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2 (5 Pcs)",
        "tags": ["Indo-Chinese", "Crunchy"],
        "description": "Frenched chicken winglets coated in seasoned spicy red batter, fried until crunchy and served with hot Schezwan garlic dip.",
        "image_url": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Chilli Chicken",
        "category": "Starters",
        "subcategory": "Non-Veg Starters",
        "type": "Non-Veg",
        "price": Decimal("250.00"),
        "preparation_time": 20,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Spicy",
        "serving_size": "Serves 2",
        "tags": ["Indo-Chinese", "Spicy Chicken"],
        "description": "Tender chicken chunks wok-tossed with green chilies, crunchy bell peppers, dark soy sauce, and scallions in signature Indo-Chinese style.",
        "image_url": "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Tandoori Murgh (Half)",
        "category": "Starters",
        "subcategory": "Non-Veg Starters",
        "type": "Non-Veg",
        "price": Decimal("280.00"),
        "preparation_time": 20,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2",
        "tags": ["Tandoor", "Signature"],
        "description": "Bone-in tender chicken marinated overnight with Kashmiri deggi mirch, hung curd, and freshly ground whole spices, fire-roasted in the clay tandoor.",
        "image_url": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Chicken Starter",
        "category": "Starters",
        "subcategory": "Non-Veg Starters",
        "type": "Non-Veg",
        "price": Decimal("240.00"),
        "preparation_time": 14,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2",
        "tags": ["Crispy", "Popular"],
        "description": "Crispy spiced boneless chicken starter tossed with southern curry leaves and cracked black pepper.",
        "image_url": "https://images.unsplash.com/photo-1610057099431-d73a1c9d2f2f?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },

    # ==========================================
    # 2. BIRYANI
    # ==========================================
    {
        "name": "Chicken Dum Biryani",
        "category": "Biryani",
        "subcategory": "Non-Veg Biryani",
        "type": "Non-Veg",
        "price": Decimal("250.00"),
        "preparation_time": 25,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 1-2 (with Mirchi Ka Salan & Raita)",
        "tags": ["Best Seller", "Hyderabadi", "Signature"],
        "description": "Authentic dum biryani slow-cooked with bone-in chicken, fragrant aged basmati rice, caramelized onions, mint, and royal saffron.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
            {"ingredient": "Chicken", "qty": Decimal("160"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Chicken Biryani",
        "category": "Biryani",
        "subcategory": "Non-Veg Biryani",
        "type": "Non-Veg",
        "price": Decimal("220.00"),
        "preparation_time": 20,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 1-2",
        "tags": ["Classic", "Dum Biryani"],
        "description": "Dum cooked basmati rice with marinated chicken pieces, aromatic whole spices, and caramelized shallots.",
        "image_url": "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
            {"ingredient": "Chicken", "qty": Decimal("150"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Chicken Fry Piece Biryani",
        "category": "Biryani",
        "subcategory": "Non-Veg Biryani",
        "type": "Non-Veg",
        "price": Decimal("280.00"),
        "preparation_time": 25,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Spicy",
        "serving_size": "Serves 1-2",
        "tags": ["Andhra Style", "Spicy Fry"],
        "description": "Aromatic spiced biryani rice crowned with fiery, crisp pan-fried chicken morsels, curry leaves, and roasted cashews.",
        "image_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
            {"ingredient": "Chicken", "qty": Decimal("180"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("30"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Mutton Biryani",
        "category": "Biryani",
        "subcategory": "Non-Veg Biryani",
        "type": "Non-Veg",
        "price": Decimal("320.00"),
        "preparation_time": 30,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 1-2",
        "tags": ["Royal", "Shahi", "Mutton"],
        "description": "Royal slow-cooked tender mutton pieces infused with rich shahi spices, layered with aged basmati rice and pure desi ghee.",
        "image_url": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
            {"ingredient": "Mutton", "qty": Decimal("180"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("60"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Egg Biryani",
        "category": "Biryani",
        "subcategory": "Non-Veg Biryani",
        "type": "Egg",
        "price": Decimal("190.00"),
        "preparation_time": 20,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 1-2 (2 Eggs)",
        "tags": ["Egg Special", "Fragrant"],
        "description": "Golden roasted boiled eggs seasoned with biryani spices and nestled in fragrant saffron-scented dum basmati rice.",
        "image_url": "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("40"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Veg Biryani",
        "category": "Biryani",
        "subcategory": "Veg Biryani",
        "type": "Veg",
        "price": Decimal("180.00"),
        "preparation_time": 20,
        "is_vegetarian": True,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 1-2",
        "tags": ["Vegetarian", "Fragrant"],
        "description": "Garden vegetables, green peas, and paneer cubes dum-cooked with aromatic spices, kewra water, mint, and basmati rice.",
        "image_url": "https://images.unsplash.com/photo-1642821373181-696a54913e93?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
            {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Paneer Biryani",
        "category": "Biryani",
        "subcategory": "Veg Biryani",
        "type": "Veg",
        "price": Decimal("210.00"),
        "preparation_time": 20,
        "is_vegetarian": True,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 1-2",
        "tags": ["Paneer", "Rich"],
        "description": "Marinated malai paneer cubes layered with aromatic saffron basmati rice, mint leaves, and golden fried onions.",
        "image_url": "https://images.unsplash.com/photo-1645177628172-a94c1f96e6db?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("250"), "unit": "GRAM"},
            {"ingredient": "Paneer", "qty": Decimal("120"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },

    # ==========================================
    # 3. MAIN COURSE
    # ==========================================
    {
        "name": "Paneer Butter Masala",
        "category": "Main Course",
        "subcategory": "Veg Main Course",
        "type": "Veg",
        "price": Decimal("220.00"),
        "preparation_time": 20,
        "is_vegetarian": True,
        "is_available": True,
        "spicy_level": "Mild",
        "serving_size": "Serves 2",
        "tags": ["Best Seller", "Paneer", "Rich Gravy"],
        "description": "Soft cottage cheese cubes simmered in a silky tomato, cashew, and butter gravy flavored with dried fenugreek leaves (kasoori methi).",
        "image_url": "https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Paneer", "qty": Decimal("150"), "unit": "GRAM"},
            {"ingredient": "Tomato", "qty": Decimal("100"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Kadai Paneer",
        "category": "Main Course",
        "subcategory": "Veg Main Course",
        "type": "Veg",
        "price": Decimal("210.00"),
        "preparation_time": 20,
        "is_vegetarian": True,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2",
        "tags": ["Kadai", "Paneer"],
        "description": "Paneer cubes and crunchy bell peppers cooked in a robust, freshly pounded coriander and red chili kadai masala.",
        "image_url": "https://images.unsplash.com/photo-1567188040759-fb8a883dc6d8?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Paneer", "qty": Decimal("140"), "unit": "GRAM"},
            {"ingredient": "Vegetables", "qty": Decimal("80"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Dal Makhani",
        "category": "Main Course",
        "subcategory": "Veg Main Course",
        "type": "Veg",
        "price": Decimal("200.00"),
        "preparation_time": 15,
        "is_vegetarian": True,
        "is_available": True,
        "spicy_level": "Mild",
        "serving_size": "Serves 2",
        "tags": ["Slow Cooked", "Comfort Food"],
        "description": "Traditional slow-cooked whole black lentils and red kidney beans simmered overnight on low embers with butter and dairy cream.",
        "image_url": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Vegetables", "qty": Decimal("100"), "unit": "GRAM"},
            {"ingredient": "Tomato", "qty": Decimal("60"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("40"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Dal Tadka",
        "category": "Main Course",
        "subcategory": "Veg Main Course",
        "type": "Veg",
        "price": Decimal("160.00"),
        "preparation_time": 14,
        "is_vegetarian": True,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2",
        "tags": ["Comfort Food", "Yellow Dal"],
        "description": "Yellow lentils tempered with aromatic desi ghee, cumin seeds, garlic, dried red chili, and fresh coriander.",
        "image_url": "https://images.unsplash.com/photo-1546833998-877b37c2e5c6?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Tomato", "qty": Decimal("50"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("20"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("40"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Butter Chicken",
        "category": "Main Course",
        "subcategory": "Non-Veg Main Course",
        "type": "Non-Veg",
        "price": Decimal("280.00"),
        "preparation_time": 25,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Mild",
        "serving_size": "Serves 2",
        "tags": ["Best Seller", "Murgh Makhani", "Signature"],
        "description": "Tandoori grilled chicken morsels enveloped in a rich, mildly spiced satin-smooth tomato butter gravy finished with fresh cream.",
        "image_url": "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Chicken", "qty": Decimal("180"), "unit": "GRAM"},
            {"ingredient": "Tomato", "qty": Decimal("100"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Chicken Curry",
        "category": "Main Course",
        "subcategory": "Non-Veg Main Course",
        "type": "Non-Veg",
        "price": Decimal("260.00"),
        "preparation_time": 22,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2",
        "tags": ["Homestyle", "Curry"],
        "description": "Homestyle chicken simmered in an onion-tomato gravy infused with ground coriander, cumin, ginger, and garlic.",
        "image_url": "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Chicken", "qty": Decimal("160"), "unit": "GRAM"},
            {"ingredient": "Tomato", "qty": Decimal("80"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Chicken Tikka Masala",
        "category": "Main Course",
        "subcategory": "Non-Veg Main Course",
        "type": "Non-Veg",
        "price": Decimal("280.00"),
        "preparation_time": 20,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2",
        "tags": ["Tandoori Chicken", "Masala"],
        "description": "Charcoal grilled boneless chicken tikka cooked in an aromatic, hearty spiced onion, tomato, and bell pepper gravy.",
        "image_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Chicken", "qty": Decimal("160"), "unit": "GRAM"},
            {"ingredient": "Tomato", "qty": Decimal("80"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("50"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Mutton Curry",
        "category": "Main Course",
        "subcategory": "Non-Veg Main Course",
        "type": "Non-Veg",
        "price": Decimal("320.00"),
        "preparation_time": 25,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2",
        "tags": ["Mutton", "Rich Gravy"],
        "description": "Tender pieces of lamb slow-cooked in a dark, robust spiced gravy with cinnamon, cloves, and whole black cardamom.",
        "image_url": "https://images.unsplash.com/photo-1545247181-516773cae754?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Mutton", "qty": Decimal("180"), "unit": "GRAM"},
            {"ingredient": "Tomato", "qty": Decimal("80"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("60"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Kashmiri Mutton Rogan Josh",
        "category": "Main Course",
        "subcategory": "Non-Veg Main Course",
        "type": "Non-Veg",
        "price": Decimal("360.00"),
        "preparation_time": 25,
        "is_vegetarian": False,
        "is_available": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2",
        "tags": ["Kashmiri", "Royal", "Lamb"],
        "description": "Succulent cuts of lamb braised with gravy flavored with garlic, ginger, and aromatic spices including cloves, bay leaves, and Kashmiri chili.",
        "image_url": "https://images.unsplash.com/photo-1545247181-516773cae754?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Mutton", "qty": Decimal("180"), "unit": "GRAM"},
            {"ingredient": "Tomato", "qty": Decimal("80"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("25"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("60"), "unit": "GRAM"},
        ],
    },

    # ==========================================
    # 4. BREADS
    # ==========================================
    {
        "name": "Butter Naan",
        "category": "Breads",
        "subcategory": "Tandoori Breads",
        "type": "Veg",
        "price": Decimal("50.00"),
        "preparation_time": 8,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "1 Piece",
        "tags": ["Tandoor", "Butter", "Flatbread"],
        "description": "Soft and pillowy clay-oven baked refined flour flatbread lavishly brushed with melted dairy butter.",
        "image_url": "https://images.unsplash.com/photo-1601050690117-94f5f6fa8bd7?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Garlic Naan",
        "category": "Breads",
        "subcategory": "Tandoori Breads",
        "type": "Veg",
        "price": Decimal("70.00"),
        "preparation_time": 10,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "1 Piece",
        "tags": ["Garlic", "Aromatic", "Tandoor"],
        "description": "Tandoori naan topped with roasted minced garlic cloves and fresh cilantro, brushed with warm butter.",
        "image_url": "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Tandoori Roti",
        "category": "Breads",
        "subcategory": "Roti & Paratha",
        "type": "Veg",
        "price": Decimal("35.00"),
        "preparation_time": 6,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "1 Piece",
        "tags": ["Whole Wheat", "Healthy"],
        "description": "Wholesome stoneground whole wheat bread baked crisp on the clay walls of the tandoor oven.",
        "image_url": "https://images.unsplash.com/photo-1506084868230-bb9d95c24759?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Laccha Paratha",
        "category": "Breads",
        "subcategory": "Roti & Paratha",
        "type": "Veg",
        "price": Decimal("60.00"),
        "preparation_time": 10,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "1 Piece",
        "tags": ["Layered", "Ghee"],
        "description": "Crispy, flaky whole wheat flatbread rolled with distinctive spiral layers and cooked on tawa with golden ghee.",
        "image_url": "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },

    # ==========================================
    # 5. RICE & NOODLES
    # ==========================================
    {
        "name": "Veg Fried Rice",
        "category": "Rice & Noodles",
        "subcategory": "Fried Rice",
        "type": "Veg",
        "price": Decimal("180.00"),
        "preparation_time": 15,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "Serves 2",
        "tags": ["Indo-Chinese", "Wok Tossed"],
        "description": "Fragrant steamed rice wok-tossed with finely chopped carrots, French beans, cabbage, garlic, and light soy seasoning.",
        "image_url": "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("200"), "unit": "GRAM"},
            {"ingredient": "Vegetables", "qty": Decimal("80"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("15"), "unit": "ML"},
        ],
    },
    {
        "name": "Chicken Fried Rice",
        "category": "Rice & Noodles",
        "subcategory": "Fried Rice",
        "type": "Non-Veg",
        "price": Decimal("220.00"),
        "preparation_time": 18,
        "is_vegetarian": False,
        "is_available": True,
        "serving_size": "Serves 2",
        "tags": ["Indo-Chinese", "Chicken Rice"],
        "description": "High-flame wok-tossed rice with shredded tender chicken breast, scrambled egg, scallions, and toasted sesame oil.",
        "image_url": "https://images.unsplash.com/photo-1600891964599-f61ba0e24092?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("200"), "unit": "GRAM"},
            {"ingredient": "Chicken", "qty": Decimal("100"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("15"), "unit": "ML"},
        ],
    },
    {
        "name": "Egg Fried Rice",
        "category": "Rice & Noodles",
        "subcategory": "Fried Rice",
        "type": "Egg",
        "price": Decimal("200.00"),
        "preparation_time": 15,
        "is_vegetarian": False,
        "is_available": True,
        "serving_size": "Serves 2",
        "tags": ["Egg", "Wok Special"],
        "description": "Fluffy long-grain rice tossed on a sizzling wok with golden scrambled eggs, spring onions, and oriental spices.",
        "image_url": "https://images.unsplash.com/photo-1596797038530-2c107229654b?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("200"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("15"), "unit": "ML"},
            {"ingredient": "Onion", "qty": Decimal("30"), "unit": "GRAM"},
        ],
    },
    {
        "name": "Chicken Hakka Noodles",
        "category": "Rice & Noodles",
        "subcategory": "Noodles",
        "type": "Non-Veg",
        "price": Decimal("230.00"),
        "preparation_time": 18,
        "is_vegetarian": False,
        "is_available": True,
        "serving_size": "Serves 2",
        "tags": ["Hakka Noodles", "Chicken"],
        "description": "Classic Hakka style boiled noodles tossed with juicy chicken slices, shredded vegetables, white pepper, and dark soy.",
        "image_url": "https://images.unsplash.com/photo-1585032226651-759b368d7246?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Chicken", "qty": Decimal("100"), "unit": "GRAM"},
            {"ingredient": "Vegetables", "qty": Decimal("60"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("15"), "unit": "ML"},
        ],
    },
    {
        "name": "Jeera Rice",
        "category": "Rice & Noodles",
        "subcategory": "Fried Rice",
        "type": "Veg",
        "price": Decimal("140.00"),
        "preparation_time": 10,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "Serves 2",
        "tags": ["Cumin", "Basmati Rice"],
        "description": "Aromatic aged basmati rice tempered with roasted cumin seeds, fresh coriander, and pure desi ghee.",
        "image_url": "https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=600&auto=format&fit=crop&q=80",
        "recipe": [
            {"ingredient": "Rice", "qty": Decimal("200"), "unit": "GRAM"},
            {"ingredient": "Oil", "qty": Decimal("15"), "unit": "ML"},
        ],
    },

    # ==========================================
    # 6. DESSERTS
    # ==========================================
    {
        "name": "Gulab Jamun",
        "category": "Desserts",
        "subcategory": "Traditional Sweets",
        "type": "Veg",
        "price": Decimal("80.00"),
        "preparation_time": 8,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "2 Pieces",
        "tags": ["Sweet", "Classic", "Mawa"],
        "description": "Two warm, melt-in-mouth golden milk-solid dumplings soaked in aromatic cardamom and rose-infused sugar syrup.",
        "image_url": "https://images.unsplash.com/photo-1553787499-6f9133860278?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Double Ka Meetha",
        "category": "Desserts",
        "subcategory": "Traditional Sweets",
        "type": "Veg",
        "price": Decimal("120.00"),
        "preparation_time": 10,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "Serves 1-2",
        "tags": ["Hyderabadi", "Royal"],
        "description": "Hyderabadi royal dessert of golden fried bread soaked in saffron-cardamom rabri and garnished with roasted pistachios.",
        "image_url": "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Ice Cream",
        "category": "Desserts",
        "subcategory": "Ice Creams & Sundaes",
        "type": "Veg",
        "price": Decimal("100.00"),
        "preparation_time": 5,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "2 Scoops",
        "tags": ["Cold", "Dessert"],
        "description": "Rich and creamy artisanal scoops of dairy ice cream topped with chocolate drizzle and roasted nuts.",
        "image_url": "https://images.unsplash.com/photo-1570197788417-0e82375c9371?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Rasmalai",
        "category": "Desserts",
        "subcategory": "Traditional Sweets",
        "type": "Veg",
        "price": Decimal("110.00"),
        "preparation_time": 8,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "2 Pieces",
        "tags": ["Bengali Sweet", "Saffron Milk"],
        "description": "Soft, spongy cottage cheese discs steeped in chilled clotted saffron milk, slivered almonds, and green cardamom.",
        "image_url": "https://images.unsplash.com/photo-1579954115545-a95591f28bfc?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },

    # ==========================================
    # 7. BEVERAGES
    # ==========================================
    {
        "name": "Fresh Lime Soda",
        "category": "Beverages",
        "subcategory": "Lassi & Coolers",
        "type": "Beverage",
        "price": Decimal("80.00"),
        "preparation_time": 6,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "300 ml Glass",
        "tags": ["Refreshing", "Chilled"],
        "description": "Crisp effervescent club soda mixed with freshly pressed lime juice, mint leaves, and choice of sweet or salt.",
        "image_url": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Mango Lassi",
        "category": "Beverages",
        "subcategory": "Lassi & Coolers",
        "type": "Beverage",
        "price": Decimal("120.00"),
        "preparation_time": 8,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "350 ml Glass",
        "tags": ["Alphonso Mango", "Yogurt Shake"],
        "description": "Thick, chilled traditional yogurt drink blended smoothly with sweet Alphonso mango pulp and a pinch of cardamom.",
        "image_url": "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Cold Coffee",
        "category": "Beverages",
        "subcategory": "Hot Beverages & Chai",
        "type": "Beverage",
        "price": Decimal("140.00"),
        "preparation_time": 8,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "350 ml Glass",
        "tags": ["Espresso", "Chilled"],
        "description": "Frothy, refreshing iced coffee blended with chilled full-cream milk, dark roast espresso, and chocolate syrup.",
        "image_url": "https://images.unsplash.com/photo-1517701604599-bb29b565090c?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
    {
        "name": "Masala Tea",
        "category": "Beverages",
        "subcategory": "Hot Beverages & Chai",
        "type": "Beverage",
        "price": Decimal("50.00"),
        "preparation_time": 7,
        "is_vegetarian": True,
        "is_available": True,
        "serving_size": "150 ml Cup",
        "tags": ["Chai", "Hot", "Assam Tea"],
        "description": "Authentic Indian cutting chai brewed with strong Assam black tea, fresh crushed ginger, green cardamom, and milk.",
        "image_url": "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=600&auto=format&fit=crop&q=80",
        "recipe": [],
    },
]


STANDARD_INGREDIENTS = [
    {"name": "Rice", "unit": "KG", "available_quantity": Decimal("50.00"), "minimum_stock_level": Decimal("10.00"), "cost_per_unit": Decimal("60.00")},
    {"name": "Chicken", "unit": "KG", "available_quantity": Decimal("30.00"), "minimum_stock_level": Decimal("5.00"), "cost_per_unit": Decimal("180.00")},
    {"name": "Mutton", "unit": "KG", "available_quantity": Decimal("20.00"), "minimum_stock_level": Decimal("5.00"), "cost_per_unit": Decimal("600.00")},
    {"name": "Paneer", "unit": "KG", "available_quantity": Decimal("15.00"), "minimum_stock_level": Decimal("3.00"), "cost_per_unit": Decimal("320.00")},
    {"name": "Vegetables", "unit": "KG", "available_quantity": Decimal("40.00"), "minimum_stock_level": Decimal("8.00"), "cost_per_unit": Decimal("40.00")},
    {"name": "Oil", "unit": "LITRE", "available_quantity": Decimal("20.00"), "minimum_stock_level": Decimal("5.00"), "cost_per_unit": Decimal("130.00")},
    {"name": "Onion", "unit": "KG", "available_quantity": Decimal("30.00"), "minimum_stock_level": Decimal("5.00"), "cost_per_unit": Decimal("30.00")},
    {"name": "Tomato", "unit": "KG", "available_quantity": Decimal("25.00"), "minimum_stock_level": Decimal("5.00"), "cost_per_unit": Decimal("25.00")},
]


def clean_and_seed_menu():
    print("==========================================================")
    print("  DineFlow: Cleaning & Fixing Menu Categories & Dishes    ")
    print("==========================================================")

    # 1. Upsert standard Raw Materials and fetch ingredient map
    ing_map = {}
    for mat in STANDARD_INGREDIENTS:
        existing_ing = ingredients_collection.find_one({"name": mat["name"]})
        if not existing_ing:
            res_ing = ingredients_collection.insert_one({
                "name": mat["name"],
                "unit": mat["unit"],
                "available_quantity": decimal128(mat["available_quantity"]),
                "current_stock": decimal128(mat["available_quantity"]),
                "minimum_stock_level": decimal128(mat["minimum_stock_level"]),
                "cost_per_unit": decimal128(mat["cost_per_unit"]),
                "is_active": True,
                "created_at": now_utc(),
            })
            ing_map[mat["name"]] = res_ing.inserted_id
            print(f"  [+] Seeded ingredient: {mat['name']} -> {mat['available_quantity']} {mat['unit']}")
        else:
            ingredients_collection.update_one(
                {"_id": existing_ing["_id"]},
                {"$set": {
                    "unit": mat["unit"],
                    "available_quantity": decimal128(mat["available_quantity"]),
                    "current_stock": decimal128(mat["available_quantity"]),
                    "minimum_stock_level": decimal128(mat["minimum_stock_level"]),
                    "cost_per_unit": decimal128(mat["cost_per_unit"]),
                    "is_active": True,
                }}
            )
            ing_map[mat["name"]] = existing_ing["_id"]
            print(f"  [OK] Reset ingredient stock: {mat['name']} -> {mat['available_quantity']} {mat['unit']}")

    for ing in ingredients_collection.find({}):
        ing_map[ing["name"]] = ing["_id"]

    # 2. Clean up test junk from menu_items_collection
    test_keywords = [
        "soup special", "spiced paneer", "available tea", "rare dish",
        "multi shortage", "once only", "complimentary papad"
    ]
    junk_filter = {
        "$or": [
            {"name": {"$regex": kw, "$options": "i"}} for kw in test_keywords
        ]
    }
    # Keep the ones explicitly needed by tests if they exist
    keep_names = ["Test Chicken Biryani", "Test Coke", "Test Chicken 65", "Test Ice Cream", "Chicken Starter"]
    junk_docs = list(menu_items_collection.find(junk_filter))
    deleted_junk = 0
    for doc in junk_docs:
        if doc.get("name") not in keep_names:
            menu_items_collection.delete_one({"_id": doc["_id"]})
            deleted_junk += 1
    print(f"[1/4] Cleared {deleted_junk} leftover test/junk menu items.")

    # 3. Synchronize Categories and Subcategories
    print("\n[2/4] Setting up clean 7 standard Categories & Subcategories...")
    category_id_map = {}
    subcat_id_map = {}

    for cat_spec in CATEGORIES_SPEC:
        cat_name = cat_spec["name"]
        cat_doc = {
            "name": cat_name,
            "description": cat_spec["description"],
            "food_type": cat_spec["food_type"],
            "image_url": cat_spec["image_url"],
            "display_order": cat_spec["display_order"],
            "is_active": True,
            "updated_at": now_utc(),
        }

        existing_cat = menu_categories_collection.find_one({"name": {"$regex": f"^{cat_name}$", "$options": "i"}})
        if existing_cat:
            menu_categories_collection.update_one({"_id": existing_cat["_id"]}, {"$set": cat_doc})
            c_id = existing_cat["_id"]
            print(f"  [OK] Category: {cat_name} (ID: {c_id})")
        else:
            cat_doc["created_at"] = now_utc()
            res = menu_categories_collection.insert_one(cat_doc)
            c_id = res.inserted_id
            print(f"  [+] Created Category: {cat_name} (ID: {c_id})")

        category_id_map[cat_name] = c_id

        # Setup subcategories
        for sub_spec in cat_spec["subcategories"]:
            sub_name = sub_spec["name"]
            sub_doc = {
                "name": sub_name,
                "category_id": c_id,
                "category_name": cat_name,
                "description": sub_spec["description"],
                "display_order": sub_spec["display_order"],
                "is_active": True,
                "updated_at": now_utc(),
            }
            existing_sub = menu_subcategories_collection.find_one({
                "name": {"$regex": f"^{sub_name}$", "$options": "i"},
                "category_id": c_id,
            })
            if existing_sub:
                menu_subcategories_collection.update_one({"_id": existing_sub["_id"]}, {"$set": sub_doc})
                s_id = existing_sub["_id"]
            else:
                sub_doc["created_at"] = now_utc()
                res_sub = menu_subcategories_collection.insert_one(sub_doc)
                s_id = res_sub.inserted_id
            subcat_id_map[(cat_name, sub_name)] = s_id
            print(f"      -> Subcategory: {sub_name}")

    # Remove obsolete categories that were causing split/confusing tabs
    valid_cat_ids = list(category_id_map.values())
    obsolete_cats = list(menu_categories_collection.find({
        "_id": {"$nin": valid_cat_ids}
    }))
    for obs in obsolete_cats:
        print(f"  [-] Removing obsolete category: {obs.get('name')} ({obs['_id']})")
        menu_categories_collection.delete_one({"_id": obs["_id"]})

    # 4. Upsert Every Curated Dish
    print("\n[3/4] Correcting Dish Details, Categories & Matching Images...")
    updated_items = 0
    created_items = 0

    valid_dish_names = [d["name"] for d in DISHES_SPEC]

    for dish in DISHES_SPEC:
        cat_name = dish["category"]
        sub_name = dish["subcategory"]
        cat_id = category_id_map[cat_name]
        sub_id = subcat_id_map[(cat_name, sub_name)]

        price_dec = dish["price"]
        item_doc = {
            "name": dish["name"],
            "category_id": cat_id,
            "category_name": cat_name,
            "subcategory_id": sub_id,
            "subcategory_name": sub_name,
            "type": dish["type"],
            "food_type": dish["type"],
            "price": decimal128(price_dec),
            "base_price": decimal128(price_dec),
            "discount": decimal128("0"),
            "tax": decimal128(price_dec * Decimal("0.05")),
            "final_price": decimal128(price_dec * Decimal("1.05")),
            "preparation_time": dish["preparation_time"],
            "is_vegetarian": dish["is_vegetarian"],
            "is_available": dish["is_available"],
            "is_active": True,
            "is_featured": dish.get("tags", []) and "Best Seller" in dish.get("tags", []),
            "spicy_level": dish.get("spicy_level", "Medium"),
            "serving_size": dish.get("serving_size", "Serves 1-2"),
            "tags": dish.get("tags", []),
            "description": dish["description"],
            "image_url": dish["image_url"],
            "updated_at": now_utc(),
        }

        # Deduplicate: Find ALL existing dishes by exact name (case-insensitive)
        escaped_name = re.escape(dish['name'])
        existing_dishes = list(menu_items_collection.find({
            "name": {"$regex": f"^{escaped_name}$", "$options": "i"}
        }))

        if existing_dishes:
            primary_dish = existing_dishes[0]
            dish_id = primary_dish["_id"]
            menu_items_collection.update_one({"_id": dish_id}, {"$set": item_doc})
            updated_items += 1
            print(f"  [OK] Updated '{dish['name']}' -> [{cat_name} > {sub_name}]")

            # Remove duplicate duplicates if any
            for dup in existing_dishes[1:]:
                print(f"      [-] Removing duplicate '{dish['name']}' with ID {dup['_id']}")
                menu_items_collection.delete_one({"_id": dup["_id"]})
                recipes_collection.delete_many({"menu_item_id": dup["_id"]})
        else:
            item_doc["created_at"] = now_utc()
            res = menu_items_collection.insert_one(item_doc)
            dish_id = res.inserted_id
            created_items += 1
            print(f"  [+] Inserted '{dish['name']}' -> [{cat_name} > {sub_name}]")

        # 5. Link BOM Recipe
        recipes_collection.delete_many({"menu_item_id": dish_id})
        recipe_specs = dish.get("recipe", [])
        if recipe_specs:
            for r in recipe_specs:
                raw_id = ing_map.get(r["ingredient"])
                if raw_id:
                    unit_clean = "G" if r["unit"].upper() in ["GRAM", "G", "GRAMS"] else r["unit"].upper()
                    recipes_collection.insert_one({
                        "menu_item_id": dish_id,
                        "ingredient_id": raw_id,
                        "ingredient_name": r["ingredient"],
                        "quantity_required": decimal128(r["qty"]),
                        "unit": unit_clean,
                        "is_optional": False,
                        "created_at": now_utc(),
                    })
            print(f"       Recipes linked: {len(recipe_specs)} ingredients")
        else:
            print(f"       Recipe: 0 deduction (Starter / direct served item)")

    # 6. Ensure test dishes exist and are categorized properly for test suite
    test_dishes = [
        {"name": "Test Chicken Biryani", "price": Decimal("250.00"), "prep": 20, "veg": False, "category": "Biryani", "subcategory": "Non-Veg Biryani"},
        {"name": "Test Coke", "price": Decimal("50.00"), "prep": 5, "veg": True, "category": "Beverages", "subcategory": "Lassi & Coolers"},
        {"name": "Test Chicken 65", "price": Decimal("180.00"), "prep": 15, "veg": False, "category": "Starters", "subcategory": "Non-Veg Starters"},
        {"name": "Test Ice Cream", "price": Decimal("100.00"), "prep": 5, "veg": True, "category": "Desserts", "subcategory": "Ice Creams & Sundaes"},
    ]
    for td in test_dishes:
        td_cat_id = category_id_map.get(td["category"])
        td_sub_id = subcat_id_map.get((td["category"], td["subcategory"]))
        td_doc = {
            "name": td["name"],
            "price": decimal128(td["price"]),
            "preparation_time": td["prep"],
            "is_vegetarian": td["veg"],
            "is_available": True,
            "is_active": True,
            "category_id": td_cat_id,
            "category_name": td["category"],
            "subcategory_id": td_sub_id,
            "subcategory_name": td["subcategory"],
        }
        existing = menu_items_collection.find_one({"name": td["name"]})
        if existing:
            menu_items_collection.update_one(
                {"_id": existing["_id"]},
                {"$set": td_doc}
            )
        else:
            td_doc["created_at"] = now_utc()
            menu_items_collection.insert_one(td_doc)

    # Clean any lingering dishes not in valid_dish_names or keep_names
    all_current_items = list(menu_items_collection.find({}))
    for item in all_current_items:
        iname = item.get("name", "")
        if iname not in valid_dish_names and iname not in keep_names:
            print(f"  [-] Deleting unlinked dish: {iname}")
            menu_items_collection.delete_one({"_id": item["_id"]})
            recipes_collection.delete_many({"menu_item_id": item["_id"]})

    print(f"\n[4/4] Seed complete! Total dishes: {menu_items_collection.count_documents({})}")
    print(f"Categories count: {menu_categories_collection.count_documents({})}")
    print("==========================================================")


if __name__ == "__main__":
    clean_and_seed_menu()
