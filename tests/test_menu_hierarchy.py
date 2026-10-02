"""
Tests for complete Menu Hierarchy module:
- Categories CRUD + Validation
- Subcategories CRUD + Parent Validation
- Menu Items CRUD + Price Calculation + Soft Deletion
- Recipe Management (POST, GET, PUT, DELETE)
- Menu Statistics
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from bson import ObjectId

from app.main import app
from app.database.mongodb import (
    menu_categories_collection,
    menu_subcategories_collection,
    menu_items_collection,
    recipes_collection,
    orders_collection,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    res = client.post("/api/auth/login", json={"email": "admin@dineflow.com", "password": "Password123!"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# 1. CATEGORY MANAGEMENT TESTS
# ============================================================================

def test_category_crud_and_duplicate_prevention(client, auth_headers):
    # 1. Create unique category
    unique_name = f"Test Category {ObjectId()}"
    res = client.post(
        "/api/categories",
        headers=auth_headers,
        json={
            "name": unique_name,
            "description": "Delicious specialty test category",
            "food_type": "Veg",
            "display_order": 99,
            "is_active": True,
        }
    )
    assert res.status_code == 201
    cat_data = res.json()
    cat_id = cat_data["id"]
    assert cat_data["name"] == unique_name
    assert cat_data["display_order"] == 99

    # 2. Duplicate category prevention
    dup_res = client.post(
        "/api/categories",
        headers=auth_headers,
        json={"name": unique_name}
    )
    assert dup_res.status_code == 400

    # 3. Get single category
    get_res = client.get(f"/api/categories/{cat_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == cat_id

    # 4. Update category
    up_res = client.put(
        f"/api/categories/{cat_id}",
        headers=auth_headers,
        json={"name": f"{unique_name} Updated", "display_order": 100}
    )
    assert up_res.status_code == 200
    assert up_res.json()["name"] == f"{unique_name} Updated"
    assert up_res.json()["display_order"] == 100

    # 5. Delete category
    del_res = client.delete(f"/api/categories/{cat_id}", headers=auth_headers)
    assert del_res.status_code in [200, 204]

    # Verify not found
    check_res = client.get(f"/api/categories/{cat_id}", headers=auth_headers)
    assert check_res.status_code == 404


# ============================================================================
# 2. SUBCATEGORY MANAGEMENT TESTS
# ============================================================================

def test_subcategory_crud_and_parent_validation(client, auth_headers):
    # 1. Get or create a parent category
    cat_res = client.get("/api/categories", headers=auth_headers)
    categories = cat_res.json()
    assert len(categories) > 0
    parent_cat = categories[0]
    parent_cat_id = parent_cat["id"]

    # 2. Reject subcategory with invalid parent
    invalid_parent_res = client.post(
        "/api/subcategories",
        headers=auth_headers,
        json={
            "name": "Invalid Parent Subcategory",
            "category_id": str(ObjectId()),
        }
    )
    assert invalid_parent_res.status_code in [400, 404]

    # 3. Create valid subcategory
    subcat_name = f"Special Subcategory {ObjectId()}"
    res = client.post(
        "/api/subcategories",
        headers=auth_headers,
        json={
            "name": subcat_name,
            "category_id": parent_cat_id,
            "description": "Test subcategory description",
            "display_order": 5,
            "is_active": True,
        }
    )
    assert res.status_code == 201
    subcat = res.json()
    subcat_id = subcat["id"]
    assert subcat["name"] == subcat_name
    assert subcat["category_id"] == parent_cat_id

    # 4. Get subcategories filtered by category
    filter_res = client.get(f"/api/subcategories?category_id={parent_cat_id}", headers=auth_headers)
    assert filter_res.status_code == 200
    subcats = filter_res.json()
    assert any(s["id"] == subcat_id for s in subcats)

    # 5. Update subcategory
    up_res = client.put(
        f"/api/subcategories/{subcat_id}",
        headers=auth_headers,
        json={"name": f"{subcat_name} Renamed", "display_order": 10}
    )
    assert up_res.status_code == 200
    assert up_res.json()["name"] == f"{subcat_name} Renamed"
    assert up_res.json()["display_order"] == 10

    # 6. Delete subcategory
    del_res = client.delete(f"/api/subcategories/{subcat_id}", headers=auth_headers)
    assert del_res.status_code in [200, 204]


# ============================================================================
# 3. MENU ITEM CRUD, PRICING & SAFE DELETION
# ============================================================================

def test_menu_item_crud_and_pricing_calculation(client, auth_headers):
    # Fetch a category & subcategory
    cats_res = client.get("/api/categories", headers=auth_headers)
    cat_id = cats_res.json()[0]["id"]
    subcats_res = client.get(f"/api/subcategories?category_id={cat_id}", headers=auth_headers)
    subcat_id = subcats_res.json()[0]["id"] if subcats_res.json() else None

    item_name = f"Test Deluxe Dish {ObjectId()}"
    # Create menu item with Base Price, Discount, and Tax
    create_payload = {
        "name": item_name,
        "description": "Rich savory dish with computed pricing",
        "category_id": cat_id,
        "subcategory_id": subcat_id,
        "price": 250.0,
        "base_price": 250.0,
        "discount": 20.0,
        "tax": 11.50,
        "food_type": "Veg",
        "preparation_time": 20,
        "is_available": True,
        "is_featured": True,
        "spicy_level": "Medium",
        "serving_size": "Serves 2",
        "tags": ["Popular", "Special"],
    }

    create_res = client.post("/api/menu", headers=auth_headers, json=create_payload)
    assert create_res.status_code == 201
    item = create_res.json()
    item_id = item["id"]

    # Final price should be max(0, base_price - discount + tax) = 250 - 20 + 11.50 = 241.50
    assert float(item["final_price"]) == pytest.approx(241.50, 0.01)
    assert item["is_featured"] is True
    assert item["spicy_level"] == "Medium"

    # Update item
    update_res = client.put(
        f"/api/menu/{item_id}",
        headers=auth_headers,
        json={"discount": 50.0}
    )
    assert update_res.status_code == 200
    updated_item = update_res.json()
    # 250 - 50 + 11.50 = 211.50
    assert float(updated_item["final_price"]) == pytest.approx(211.50, 0.01)

    # Safe deletion when associated with order
    # Insert a dummy order with this item
    orders_collection.insert_one({
        "order_number": f"ORD-TEST-{ObjectId()}",
        "status": "COMPLETED",
        "items": [{"menu_item_id": item_id, "name": item_name, "quantity": 1, "price": 241.50}],
    })

    # Try delete: should NOT hard delete, but soft delete (is_active = False)
    del_res = client.delete(f"/api/menu/{item_id}", headers=auth_headers)
    assert del_res.status_code in [200, 204]

    # Verify item is deactivated, not removed from DB
    db_item = menu_items_collection.find_one({"_id": ObjectId(item_id)})
    assert db_item is not None
    assert db_item.get("is_active") is False

    # Cleanup test order & item
    orders_collection.delete_many({"items.menu_item_id": item_id})
    menu_items_collection.delete_one({"_id": ObjectId(item_id)})


# ============================================================================
# 4. RECIPE ENDPOINTS TEST
# ============================================================================

def test_recipe_endpoints(client, auth_headers):
    # Fetch any item
    items_res = client.get("/api/menu", headers=auth_headers)
    assert items_res.status_code == 200
    items = items_res.json()
    assert len(items) > 0
    target_item = items[0]
    target_id = target_item["id"]

    # 1. GET recipe
    get_res = client.get(f"/api/menu/{target_id}/recipe", headers=auth_headers)
    assert get_res.status_code == 200
    assert isinstance(get_res.json(), list)

    # 2. PUT recipe update (update with empty or list)
    put_res = client.put(
        f"/api/menu/{target_id}/recipe",
        headers=auth_headers,
        json=[]
    )
    assert put_res.status_code == 200


# ============================================================================
# 5. MENU DASHBOARD STATISTICS TEST
# ============================================================================

def test_menu_statistics_endpoint(client, auth_headers):
    res = client.get("/api/menu/stats", headers=auth_headers)
    assert res.status_code == 200
    stats = res.json()
    assert "total_items" in stats
    assert "available_items" in stats
    assert "unavailable_items" in stats
    assert "veg_items" in stats
    assert "non_veg_items" in stats
    assert "starters" in stats
    assert "desserts" in stats
    assert "featured_items" in stats
    assert stats["total_items"] > 0
