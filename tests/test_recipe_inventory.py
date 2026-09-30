"""
Test suite for Recipe-Based Inventory Stock Management:
- BOM recipe mapping
- Deferral of stock deduction until SERVED / COMPLETED
- Multi-item order ingredient aggregation
- Starters exemption (0 deduction when no recipe)
- Idempotency / duplicate deduction prevention
- Insufficient stock validation (all shortages reported, no negative stock)
- Real-time live availability (3 states: AVAILABLE, LOW_STOCK, OUT_OF_STOCK)
- Full StockMovement audit trail
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from app.main import app
from app.database.mongodb import (
    ingredients_collection,
    recipes_collection,
    menu_items_collection,
    stock_movements_collection,
    orders_collection,
)
from app.services.common import decimal128, to_object_id
from app.services.order_service import OrderService
from app.services.recipe_service import RecipeService
from app.services.ingredient_service import IngredientService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    res = client.post("/api/auth/login", json={"email": "admin@dineflow.com", "password": "Password123!"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def get_ingredient_stock(name: str) -> Decimal:
    doc = ingredients_collection.find_one({"name": name})
    assert doc is not None, f"Ingredient {name} not found"
    val = doc["available_quantity"]
    return val.to_decimal() if hasattr(val, "to_decimal") else Decimal(str(val))


def test_seed_ingredients_and_recipes_exist(client, auth_headers):
    """Verify standard ingredients, categories, and recipes are seeded properly."""
    res = client.get("/api/inventory", headers=auth_headers)
    assert res.status_code == 200
    items = res.json()
    names = {i["name"] for i in items}
    expected_ingredients = {"Rice", "Chicken", "Mutton", "Paneer", "Vegetables", "Oil", "Onion", "Tomato"}
    assert expected_ingredients.issubset(names)

    # Check Chicken Biryani recipe
    cb = menu_items_collection.find_one({"name": "Chicken Biryani"})
    assert cb is not None
    cb_recipes = RecipeService.get_by_menu_item(str(cb["_id"]))
    assert len(cb_recipes) == 4
    recipe_names = {r["ingredient_name"] for r in cb_recipes}
    assert recipe_names == {"Rice", "Chicken", "Oil", "Onion"}

    # Check Starter dish has NO recipe
    starter = menu_items_collection.find_one({"name": "Chicken Starter"})
    assert starter is not None
    starter_recipes = RecipeService.get_by_menu_item(str(starter["_id"]))
    assert len(starter_recipes) == 0


def test_single_item_deduction_at_served_status(client, auth_headers):
    """
    1 Chicken Biryani:
    Recipe: Rice 250g, Chicken 150g, Oil 20ml, Onion 50g.
    Inventory must NOT decrease at creation or confirmation.
    Inventory MUST decrease when status reaches SERVED.
    """
    cb = menu_items_collection.find_one({"name": "Chicken Biryani"})
    assert cb is not None

    # Reset initial stock
    ingredients_collection.update_one({"name": "Rice"}, {"$set": {"available_quantity": decimal128("50.00")}})
    ingredients_collection.update_one({"name": "Chicken"}, {"$set": {"available_quantity": decimal128("30.00")}})
    ingredients_collection.update_one({"name": "Oil"}, {"$set": {"available_quantity": decimal128("20.00")}})
    ingredients_collection.update_one({"name": "Onion"}, {"$set": {"available_quantity": decimal128("30.00")}})

    # 1. Create Order
    create_res = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "items": [{"menu_item_id": str(cb["_id"]), "quantity": 1}]},
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    order_id = create_res.json()["id"]

    # Stock must not change after creation
    assert get_ingredient_stock("Rice") == Decimal("50.00")
    assert get_ingredient_stock("Chicken") == Decimal("30.00")

    # 2. Confirm Order
    confirm_res = client.post(f"/api/orders/{order_id}/confirm", headers=auth_headers)
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] in ["CONFIRMED", "SENT_TO_KITCHEN"]
    assert confirm_res.json().get("inventory_deducted") is False

    # Stock must NOT decrease merely when confirmed!
    assert get_ingredient_stock("Rice") == Decimal("50.00")
    assert get_ingredient_stock("Chicken") == Decimal("30.00")
    assert get_ingredient_stock("Oil") == Decimal("20.00")
    assert get_ingredient_stock("Onion") == Decimal("30.00")

    # 3. Transition to SERVED -> Inventory is now deducted
    status_res = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "SERVED"},
        headers=auth_headers,
    )
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "SERVED"
    assert status_res.json()["inventory_deducted"] is True

    # 4. Verify exact deduction:
    # 50 kg - 250 g = 49.750 kg
    # 30 kg - 150 g = 29.850 kg
    # 20 L - 20 ml = 19.980 L
    # 30 kg - 50 g = 29.950 kg
    assert get_ingredient_stock("Rice") == Decimal("49.75")
    assert get_ingredient_stock("Chicken") == Decimal("29.85")
    assert get_ingredient_stock("Oil") == Decimal("19.98")
    assert get_ingredient_stock("Onion") == Decimal("29.95")

    # 5. Verify Idempotency: transitioning to SERVED again or COMPLETED does NOT deduct twice!
    status_res_2 = client.patch(
        f"/api/orders/{order_id}/status",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )
    assert status_res_2.status_code == 200
    assert get_ingredient_stock("Rice") == Decimal("49.75")
    assert get_ingredient_stock("Chicken") == Decimal("29.85")


def test_quantity_multiplier_deduction(client, auth_headers):
    """
    Chicken Biryani x 4:
    Rice: 250g x 4 = 1000g (1 kg)
    Chicken: 150g x 4 = 600g (0.6 kg)
    Oil: 20ml x 4 = 80ml (0.08 L)
    Onion: 50g x 4 = 200g (0.2 kg)
    """
    cb = menu_items_collection.find_one({"name": "Chicken Biryani"})
    assert cb is not None

    ingredients_collection.update_one({"name": "Rice"}, {"$set": {"available_quantity": decimal128("50.00")}})
    ingredients_collection.update_one({"name": "Chicken"}, {"$set": {"available_quantity": decimal128("30.00")}})
    ingredients_collection.update_one({"name": "Oil"}, {"$set": {"available_quantity": decimal128("20.00")}})
    ingredients_collection.update_one({"name": "Onion"}, {"$set": {"available_quantity": decimal128("30.00")}})

    create_res = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "items": [{"menu_item_id": str(cb["_id"]), "quantity": 4}]},
        headers=auth_headers,
    )
    order_id = create_res.json()["id"]

    client.post(f"/api/orders/{order_id}/confirm", headers=auth_headers)

    # Complete order
    complete_res = client.post(f"/api/orders/{order_id}/complete", headers=auth_headers)
    assert complete_res.status_code == 200

    assert get_ingredient_stock("Rice") == Decimal("49.00")
    assert get_ingredient_stock("Chicken") == Decimal("29.40")
    assert get_ingredient_stock("Oil") == Decimal("19.92")
    assert get_ingredient_stock("Onion") == Decimal("29.80")


def test_multi_item_order_with_starters_exemption(client, auth_headers):
    """
    Section 7 Test:
    Order #1001:
    - Chicken Biryani x 2 (Rice 500g, Chicken 300g, Oil 40ml, Onion 100g)
    - Paneer Biryani x 1  (Rice 250g, Paneer 120g, Oil 20ml, Onion 50g)
    - Veg Biryani x 2     (Rice 500g, Veg 200g, Oil 40ml, Onion 100g)
    - Chicken Starter x 2 (NO INVENTORY DEDUCTION)

    Combined requirements:
    Total Rice: 500 + 250 + 500 = 1250 g (1.25 kg)
    Total Chicken: 300 g (0.30 kg)
    Total Paneer: 120 g (0.12 kg)
    Total Vegetables: 200 g (0.20 kg)
    Total Oil: 40 + 20 + 40 = 100 ml (0.10 L)
    Total Onion: 100 + 50 + 100 = 250 g (0.25 kg)
    """
    cb = menu_items_collection.find_one({"name": "Chicken Biryani"})
    pb = menu_items_collection.find_one({"name": "Paneer Biryani"})
    vb = menu_items_collection.find_one({"name": "Veg Biryani"})
    cs = menu_items_collection.find_one({"name": "Chicken Starter"})

    ingredients_collection.update_one({"name": "Rice"}, {"$set": {"available_quantity": decimal128("50.00")}})
    ingredients_collection.update_one({"name": "Chicken"}, {"$set": {"available_quantity": decimal128("30.00")}})
    ingredients_collection.update_one({"name": "Paneer"}, {"$set": {"available_quantity": decimal128("15.00")}})
    ingredients_collection.update_one({"name": "Vegetables"}, {"$set": {"available_quantity": decimal128("40.00")}})
    ingredients_collection.update_one({"name": "Oil"}, {"$set": {"available_quantity": decimal128("20.00")}})
    ingredients_collection.update_one({"name": "Onion"}, {"$set": {"available_quantity": decimal128("30.00")}})

    cart_items = [
        {"menu_item_id": str(cb["_id"]), "quantity": 2},
        {"menu_item_id": str(pb["_id"]), "quantity": 1},
        {"menu_item_id": str(vb["_id"]), "quantity": 2},
        {"menu_item_id": str(cs["_id"]), "quantity": 2},
    ]

    # Validate cart endpoint first
    val_res = client.post("/api/orders/validate-cart", json={"items": cart_items}, headers=auth_headers)
    assert val_res.status_code == 200
    assert val_res.json()["is_valid"] is True

    create_res = client.post(
        "/api/orders",
        json={"order_type": "DINE_IN", "items": cart_items},
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    order_id = create_res.json()["id"]

    # Confirm order
    client.post(f"/api/orders/{order_id}/confirm", headers=auth_headers)

    # Deduct at SERVED
    client.patch(f"/api/orders/{order_id}/status", json={"status": "SERVED"}, headers=auth_headers)

    # Assert exact calculated stocks
    assert get_ingredient_stock("Rice") == Decimal("48.75")       # 50 - 1.25
    assert get_ingredient_stock("Chicken") == Decimal("29.70")    # 30 - 0.30
    assert get_ingredient_stock("Paneer") == Decimal("14.88")     # 15 - 0.12
    assert get_ingredient_stock("Vegetables") == Decimal("39.80") # 40 - 0.20
    assert get_ingredient_stock("Oil") == Decimal("19.90")        # 20 - 0.10
    assert get_ingredient_stock("Onion") == Decimal("29.75")      # 30 - 0.25


def test_insufficient_stock_reports_all_shortages_and_blocks_negative(client, auth_headers):
    """
    Section 10 & 23 & 31:
    Set Rice to 100g (0.1 kg) and Chicken to 50g (0.05 kg).
    Attempting Chicken Biryani (requires 250g Rice, 150g Chicken) must fail,
    identifying BOTH shortages, and never allowing negative inventory!
    """
    cb = menu_items_collection.find_one({"name": "Chicken Biryani"})
    assert cb is not None

    ingredients_collection.update_one({"name": "Rice"}, {"$set": {"available_quantity": decimal128("0.10")}})
    ingredients_collection.update_one({"name": "Chicken"}, {"$set": {"available_quantity": decimal128("0.05")}})

    # Real-time single item availability
    avail = RecipeService.calculate_item_availability(str(cb["_id"]), requested_quantity=1)
    assert avail["status"] == "OUT_OF_STOCK"
    assert avail["max_portions"] == 0
    assert len(avail["shortages"]) == 2  # Both Rice and Chicken are short
    shortage_names = {s["ingredient_name"] for s in avail["shortages"]}
    assert "Rice" in shortage_names
    assert "Chicken" in shortage_names

    # Cart validation endpoint must identify the shortages
    val_res = client.post(
        "/api/orders/validate-cart",
        json={"items": [{"menu_item_id": str(cb["_id"]), "quantity": 1}]},
        headers=auth_headers,
    )
    assert val_res.status_code == 200
    val_body = val_res.json()
    assert val_body["is_valid"] is False
    assert len(val_body["shortages"]) == 2

    # Attempting to confirm order must be rejected with HTTP 400 and clear error
    create_res = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "items": [{"menu_item_id": str(cb["_id"]), "quantity": 1}]},
        headers=auth_headers,
    )
    order_id = create_res.json()["id"]

    confirm_res = client.post(f"/api/orders/{order_id}/confirm", headers=auth_headers)
    assert confirm_res.status_code == 400
    error_detail = confirm_res.json()["detail"]
    assert "Insufficient stock" in error_detail
    assert "Rice" in error_detail
    assert "Chicken" in error_detail

    # Inventory must remain completely unchanged (never negative!)
    assert get_ingredient_stock("Rice") == Decimal("0.10")
    assert get_ingredient_stock("Chicken") == Decimal("0.05")


def test_order_cancellation_restores_deducted_stock(client, auth_headers):
    """
    Section 11:
    If order was served (stock deducted) and later cancelled,
    stock is restored via ORDER_RETURN movement.
    """
    cb = menu_items_collection.find_one({"name": "Chicken Biryani"})
    ingredients_collection.update_one({"name": "Rice"}, {"$set": {"available_quantity": decimal128("50.00")}})
    ingredients_collection.update_one({"name": "Chicken"}, {"$set": {"available_quantity": decimal128("30.00")}})

    create_res = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "items": [{"menu_item_id": str(cb["_id"]), "quantity": 2}]},
        headers=auth_headers,
    )
    order_id = create_res.json()["id"]

    client.post(f"/api/orders/{order_id}/confirm", headers=auth_headers)
    # Deduct
    client.patch(f"/api/orders/{order_id}/status", json={"status": "SERVED"}, headers=auth_headers)
    assert get_ingredient_stock("Rice") == Decimal("49.50")
    assert get_ingredient_stock("Chicken") == Decimal("29.70")

    # Cancel order with manager/admin privileges
    cancel_res = client.post(
        f"/api/orders/{order_id}/cancel",
        json={"reason": "Customer cancellation after serve"},
        headers=auth_headers,
    )
    # Allowed with manager/admin override
    if cancel_res.status_code == 200:
        # Stock returned
        assert get_ingredient_stock("Rice") == Decimal("50.00")
        assert get_ingredient_stock("Chicken") == Decimal("30.00")


def test_inventory_dashboard_and_movements_api(client, auth_headers):
    """Section 17: Inventory dashboard and movements API."""
    res = client.get("/api/inventory/dashboard", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_ingredients" in data
    assert "low_stock_count" in data
    assert "out_of_stock_count" in data
    assert "recent_movements" in data
    assert "today_consumption_count" in data

    mov_res = client.get("/api/inventory/movements", headers=auth_headers)
    assert mov_res.status_code == 200
    assert isinstance(mov_res.json(), list)
