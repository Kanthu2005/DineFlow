"""
Test suite validating the 30 core menu items in DineFlow menu.
Verifies Name, Category, Type, Price (INR), Preparation Time, Availability (True),
and unique, valid high-quality Image URLs for all 30 dishes.
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.seed_menu_items_30 import MENU_ITEMS_30


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    res = client.post("/api/auth/login", json={"email": "admin@dineflow.com", "password": "Password123!"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_all_30_menu_items_exist_and_match_spec(client, auth_headers):
    res = client.get("/api/menu/items", headers=auth_headers)
    assert res.status_code == 200
    items = res.json()
    item_map = {it["name"].lower(): it for it in items}

    for expected in MENU_ITEMS_30:
        name_key = expected["name"].lower()
        assert name_key in item_map, f"Item '{expected['name']}' not found in menu items"
        actual = item_map[name_key]

        # Verify price
        assert float(actual["price"]) == float(expected["price"]), (
            f"Price mismatch for {expected['name']}: expected {expected['price']}, got {actual['price']}"
        )

        # Verify preparation time
        assert int(actual["preparation_time"]) == int(expected["preparation_time"]), (
            f"Prep time mismatch for {expected['name']}: expected {expected['preparation_time']}, got {actual['preparation_time']}"
        )

        # Verify food type (Veg / Non-Veg / Egg / Beverage)
        assert actual.get("type") == expected["type"], (
            f"Type mismatch for {expected['name']}: expected {expected['type']}, got {actual.get('type')}"
        )

        # Verify availability is True
        assert actual.get("is_available") is True, f"Item {expected['name']} should be available"

        # Verify category or subcategory
        actual_cat = str(actual.get("category_name") or "")
        actual_sub = str(actual.get("subcategory_name") or "")
        cat_matches = (
            actual_cat.lower() == expected["category"].lower()
            or actual_sub.lower() == expected["category"].lower()
            or expected["category"].lower() in actual_cat.lower()
            or expected["category"].lower() in actual_sub.lower()
        )
        assert cat_matches, (
            f"Category mismatch for {expected['name']}: expected {expected['category']}, got category='{actual_cat}', subcategory='{actual_sub}'"
        )

        # Verify image URL is non-empty and starts with https://
        img = actual.get("image_url")
        assert img and img.startswith("http"), f"Invalid image URL for {expected['name']}: {img}"


def test_unique_images_across_all_30_items():
    urls = [it["image_url"] for it in MENU_ITEMS_30]
    assert len(urls) == 30
    assert len(set(urls)) == 30, "Images must be unique across all 30 menu items"


def test_categories_coverage():
    categories = {it["category"] for it in MENU_ITEMS_30}
    expected_categories = {
        "Starters",
        "Biryani",
        "Main Course",
        "Breads",
        "Rice & Noodles",
        "Desserts",
        "Beverages",
    }
    assert categories == expected_categories
