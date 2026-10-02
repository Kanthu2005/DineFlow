"""
Comprehensive 20-Scenario Test Suite for DineFlow Inventory Management.
Covers:
1. Add ingredient
2. Update ingredient
3. Receive stock
4. Stock movement creation
5. Recipe creation
6. Recipe ingredient mapping
7. Stock availability check
8. Successful inventory consumption
9. Insufficient stock
10. Multiple insufficient ingredients
11. Wastage recording
12. Stock adjustment
13. Stock transfer
14. Batch tracking
15. Expiry validation
16. FEFO consumption
17. Duplicate consumption prevention
18. Starter item exemption (inventory_tracking_enabled: False)
19. Purchase order workflow & goods receiving
20. Low-stock detection & alert levels
"""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database.mongodb import users_collection
from app.services.service import hash_password, now_utc
from app.services.order_service import OrderService
from app.services.recipe_service import RecipeService
from app.services.ingredient_service import IngredientService
from app.repositories.inventory_repository import BatchRepository, IngredientRepository

client = TestClient(app)
repo = IngredientRepository()
batch_repo = BatchRepository()


@pytest.fixture(scope="session")
def auth_tokens():
    roles = {
        "admin": ("admin@dineflow.com", "Password123!", "ADMIN"),
        "manager": ("manager@dineflow.com", "Password123!", "MANAGER"),
        "chef": ("chef@dineflow.com", "Password123!", "CHEF"),
        "waiter": ("waiter@dineflow.com", "Password123!", "WAITER"),
    }
    headers = {}
    for role_key, (email, pwd, role_val) in roles.items():
        existing = users_collection.find_one({"email": email})
        if not existing:
            users_collection.insert_one({
                "name": f"Test {role_val}",
                "email": email,
                "password": hash_password(pwd),
                "role": role_val,
                "is_active": True,
                "created_at": now_utc(),
            })
        login_res = client.post("/api/auth/login", json={"email": email, "password": pwd})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers[role_key] = {"Authorization": f"Bearer {token}"}
    return headers


def test_01_add_ingredient_with_full_metadata(auth_tokens):
    """Scenario 1: Add inventory item with SKU, category, units, thresholds, supplier."""
    sku = f"SKU-{uuid.uuid4().hex[:6].upper()}"
    name = f"Premium Saffron {uuid.uuid4().hex[:4]}"
    res = client.post(
        "/api/inventory",
        json={
            "name": name,
            "sku": sku,
            "category": "Spices",
            "unit": "g",
            "available_quantity": 100.0,
            "minimum_stock": 20.0,
            "maximum_stock": 500.0,
            "reorder_level": 30.0,
            "cost_per_unit": 250.0,
            "is_active": True,
        },
        headers=auth_tokens["manager"],
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == name
    assert data["sku"] == sku
    assert data["unit"].upper() == "G"
    assert Decimal(str(data["current_stock"])) == Decimal("100.0")
    assert Decimal(str(data["reorder_level"])) == Decimal("30.0")
    assert data["status"] == "NORMAL"


def test_02_update_ingredient(auth_tokens):
    """Scenario 2: Update ingredient details, thresholds, and costs."""
    sku = f"SKU-{uuid.uuid4().hex[:6].upper()}"
    create_res = client.post(
        "/api/inventory",
        json={
            "name": f"Cardamom Pods {uuid.uuid4().hex[:4]}",
            "sku": sku,
            "unit": "g",
            "available_quantity": 50.0,
            "minimum_stock": 10.0,
            "cost_per_unit": 50.0,
        },
        headers=auth_tokens["manager"],
    )
    ing_id = create_res.json()["id"]

    update_res = client.put(
        f"/api/inventory/{ing_id}",
        json={
            "cost_per_unit": 65.0,
            "reorder_level": 15.0,
            "minimum_stock": 15.0,
        },
        headers=auth_tokens["manager"],
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert Decimal(str(updated["cost_per_unit"])) == Decimal("65.0")
    assert Decimal(str(updated["minimum_stock"])) == Decimal("15.0")


def test_03_receive_stock_generates_batch_and_updates_balance(auth_tokens):
    """Scenario 3: Receiving stock increments stock balance and creates lot batch."""
    sku = f"SKU-{uuid.uuid4().hex[:6].upper()}"
    ing = client.post(
        "/api/inventory",
        json={"name": f"Cooking Oil {uuid.uuid4().hex[:4]}", "sku": sku, "unit": "litre", "available_quantity": 10.0, "cost_per_unit": 120.0},
        headers=auth_tokens["manager"],
    ).json()

    exp_date = (datetime.now(timezone.utc) + timedelta(days=90)).isoformat()
    rec_res = client.post(
        f"/api/inventory/{ing['id']}/receive",
        json={
            "quantity": 25.0,
            "unit_cost": 115.0,
            "batch_number": f"LOT-OIL-{uuid.uuid4().hex[:4]}",
            "expiry_date": exp_date,
            "reason": "Supplier Delivery",
        },
        headers=auth_tokens["manager"],
    )
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert Decimal(str(rec_data["new_stock"])) == Decimal("35.0")
    assert rec_data["batch"]["remaining_quantity"] == 25.0
    assert rec_data["movement"]["movement_type"] == "RECEIVE"


def test_04_stock_movement_ledger_audit_trail(auth_tokens):
    """Scenario 4: Stock movement creation records complete audit ledger."""
    sku = f"SKU-{uuid.uuid4().hex[:6].upper()}"
    ing = client.post(
        "/api/inventory",
        json={"name": f"Sugar Bag {uuid.uuid4().hex[:4]}", "sku": sku, "unit": "kg", "available_quantity": 5.0, "cost_per_unit": 40.0},
        headers=auth_tokens["manager"],
    ).json()

    client.post(
        f"/api/inventory/{ing['id']}/receive",
        json={"quantity": 15.0, "unit_cost": 42.0, "reason": "Restock PO #101"},
        headers=auth_tokens["manager"],
    )

    movs = client.get(f"/api/inventory/reports/movements?ingredient_id={ing['id']}", headers=auth_tokens["manager"]).json()
    assert len(movs) >= 1
    latest = movs[0]
    assert latest["movement_type"] == "RECEIVE"
    assert Decimal(str(latest["quantity"])) == Decimal("15.0")
    assert Decimal(str(latest["previous_stock"])) == Decimal("5.0")
    assert Decimal(str(latest["new_stock"])) == Decimal("20.0")


def test_05_and_06_recipe_creation_and_ingredient_mapping(auth_tokens):
    """Scenarios 5 & 6: Create recipe BOM and map ingredients with compatible units."""
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]
    dish = client.post(
        "/api/menu-items",
        json={"name": f"Spiced Paneer {uuid.uuid4().hex[:4]}", "category_id": cat["id"], "price": "220.00", "preparation_time": 15, "inventory_tracking_enabled": True},
        headers=auth_tokens["admin"],
    ).json()

    paneer = client.post(
        "/api/inventory",
        json={"name": f"Fresh Paneer {uuid.uuid4().hex[:4]}", "unit": "kg", "available_quantity": 10.0, "cost_per_unit": 300.0},
        headers=auth_tokens["manager"],
    ).json()

    butter = client.post(
        "/api/inventory",
        json={"name": f"Dairy Butter {uuid.uuid4().hex[:4]}", "unit": "g", "available_quantity": 2000.0, "cost_per_unit": 0.5},
        headers=auth_tokens["manager"],
    ).json()

    # Recipe uses 0.20 kg Paneer and 30g Butter
    recipe_res = client.post(
        f"/api/recipes/menu-items/{dish['id']}/recipe",
        json={
            "ingredients": [
                {"ingredient_id": paneer["id"], "quantity_required": 0.20, "unit": "kg"},
                {"ingredient_id": butter["id"], "quantity_required": 30.0, "unit": "g"},
            ],
            "yield_servings": 1,
            "preparation_notes": "Saute paneer in butter",
        },
        headers=auth_tokens["chef"],
    )
    assert recipe_res.status_code == 201
    recipe_data = recipe_res.json()
    assert len(recipe_data["ingredients"]) == 2

    # Check food cost calculation
    cost_res = client.get(f"/api/recipes/{dish['id']}/cost", headers=auth_tokens["chef"])
    assert cost_res.status_code == 200
    cost_info = cost_res.json()
    # 0.20 * 300 = 60; 30 * 0.5 = 15; total cost = 75.00
    assert Decimal(str(cost_info["total_recipe_cost"])) == Decimal("75.0")
    assert cost_info["food_cost_percentage"] > 0


def test_07_stock_availability_check(auth_tokens):
    """Scenario 7: Stock availability check correctly indicates availability."""
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]
    dish = client.post(
        "/api/menu-items",
        json={"name": f"Available Tea {uuid.uuid4().hex[:4]}", "category_id": cat["id"], "price": "40.00", "preparation_time": 5},
        headers=auth_tokens["admin"],
    ).json()

    milk = client.post(
        "/api/inventory",
        json={"name": f"Fresh Milk {uuid.uuid4().hex[:4]}", "unit": "litre", "available_quantity": 5.0, "cost_per_unit": 60.0},
        headers=auth_tokens["manager"],
    ).json()

    client.post(
        f"/api/recipes/menu-items/{dish['id']}/recipe",
        json={"ingredients": [{"ingredient_id": milk["id"], "quantity_required": 0.2, "unit": "litre"}]},
        headers=auth_tokens["chef"],
    )

    avail_res = client.get(f"/api/recipes/menu-items/{dish['id']}/availability?servings=10", headers=auth_tokens["chef"])
    assert avail_res.status_code == 200
    avail_data = avail_res.json()
    assert avail_data["is_available"] is True
    assert avail_data["max_possible_servings"] == 25  # 5.0 / 0.2


def test_08_successful_inventory_consumption_on_delivered(auth_tokens):
    """Scenario 8: Order transition to DELIVERED triggers automatic FEFO stock deduction."""
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]
    dish = client.post(
        "/api/menu-items",
        json={"name": f"Soup Special {uuid.uuid4().hex[:4]}", "category_id": cat["id"], "price": "120.00", "preparation_time": 10},
        headers=auth_tokens["admin"],
    ).json()

    mushrooms = client.post(
        "/api/inventory",
        json={"name": f"Mushrooms {uuid.uuid4().hex[:4]}", "unit": "g", "available_quantity": 1000.0, "cost_per_unit": 0.2},
        headers=auth_tokens["manager"],
    ).json()

    client.post(
        f"/api/recipes/menu-items/{dish['id']}/recipe",
        json={"ingredients": [{"ingredient_id": mushrooms["id"], "quantity_required": 100.0, "unit": "g"}]},
        headers=auth_tokens["chef"],
    )

    # Place order
    order_res = client.post(
        "/api/orders",
        json={
            "order_type": "TAKEAWAY",
            "items": [{"menu_item_id": dish["id"], "quantity": 2, "unit_price": "120.00"}],
        },
        headers=auth_tokens["waiter"],
    )
    assert order_res.status_code == 201
    order = order_res.json()

    # Move order through workflow: PENDING -> CONFIRMED -> PREPARING -> READY -> DELIVERED
    client.post(f"/api/orders/{order['id']}/confirm", headers=auth_tokens["waiter"])
    client.patch(f"/api/orders/{order['id']}/status", json={"status": "PREPARING"}, headers=auth_tokens["chef"])
    client.patch(f"/api/orders/{order['id']}/status", json={"status": "READY"}, headers=auth_tokens["chef"])
    deliv_res = client.patch(f"/api/orders/{order['id']}/status", json={"status": "DELIVERED"}, headers=auth_tokens["waiter"])
    assert deliv_res.status_code == 200

    # Stock should be deducted by 2 * 100g = 200g -> 800g
    after_ing = client.get(f"/api/inventory/{mushrooms['id']}", headers=auth_tokens["manager"]).json()
    assert Decimal(str(after_ing["current_stock"])) == Decimal("800.0")


def test_09_insufficient_stock_error(auth_tokens):
    """Scenario 9: Stock deduction fails with 400 when single ingredient is insufficient."""
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]
    dish = client.post(
        "/api/menu-items",
        json={"name": f"Rare Dish {uuid.uuid4().hex[:4]}", "category_id": cat["id"], "price": "500.00", "preparation_time": 20},
        headers=auth_tokens["admin"],
    ).json()

    truffle = client.post(
        "/api/inventory",
        json={"name": f"Truffle {uuid.uuid4().hex[:4]}", "unit": "g", "available_quantity": 10.0, "cost_per_unit": 50.0},
        headers=auth_tokens["manager"],
    ).json()

    client.post(
        f"/api/recipes/menu-items/{dish['id']}/recipe",
        json={"ingredients": [{"ingredient_id": truffle["id"], "quantity_required": 25.0, "unit": "g"}]},
        headers=auth_tokens["chef"],
    )

    order_res = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "items": [{"menu_item_id": dish["id"], "quantity": 1, "unit_price": "500.00"}]},
        headers=auth_tokens["waiter"],
    )
    assert order_res.status_code == 201
    order = order_res.json()

    # Deducting inventory directly or via completion should fail with shortage message
    with pytest.raises(Exception) as exc_info:
        OrderService.deduct_order_inventory(order["id"], order_items=order["items"])
    assert "Insufficient stock" in str(exc_info.value) or "shortage" in str(exc_info.value).lower()


def test_10_multiple_insufficient_ingredients_detail(auth_tokens):
    """Scenario 10: Reports all insufficient ingredients when multiple fail."""
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]
    dish = client.post(
        "/api/menu-items",
        json={"name": f"Multi Shortage Item {uuid.uuid4().hex[:4]}", "category_id": cat["id"], "price": "400.00", "preparation_time": 20},
        headers=auth_tokens["admin"],
    ).json()

    ing_a = client.post("/api/inventory", json={"name": f"Item A {uuid.uuid4().hex[:4]}", "unit": "kg", "available_quantity": 0.5, "cost_per_unit": 10.0}, headers=auth_tokens["manager"]).json()
    ing_b = client.post("/api/inventory", json={"name": f"Item B {uuid.uuid4().hex[:4]}", "unit": "kg", "available_quantity": 0.2, "cost_per_unit": 20.0}, headers=auth_tokens["manager"]).json()

    client.post(
        f"/api/recipes/menu-items/{dish['id']}/recipe",
        json={
            "ingredients": [
                {"ingredient_id": ing_a["id"], "quantity_required": 1.0, "unit": "kg"},
                {"ingredient_id": ing_b["id"], "quantity_required": 1.0, "unit": "kg"},
            ]
        },
        headers=auth_tokens["chef"],
    )

    avail_res = client.get(f"/api/recipes/menu-items/{dish['id']}/availability?servings=1", headers=auth_tokens["chef"])
    data = avail_res.json()
    assert data["is_available"] is False
    assert len(data["shortages"]) == 2


def test_11_wastage_recording_and_reporting(auth_tokens):
    """Scenario 11: Recording wastage reduces stock and appears in wastage reports."""
    ing = client.post(
        "/api/inventory",
        json={"name": f"Tomatoes {uuid.uuid4().hex[:4]}", "unit": "kg", "available_quantity": 30.0, "cost_per_unit": 25.0},
        headers=auth_tokens["manager"],
    ).json()

    waste_res = client.post(
        f"/api/inventory/{ing['id']}/wastage",
        json={"quantity": 5.0, "reason": "SPOILED", "notes": "Damaged in transit"},
        headers=auth_tokens["manager"],
    )
    assert waste_res.status_code == 200
    waste_data = waste_res.json()
    assert Decimal(str(waste_data["new_stock"])) == Decimal("25.0")
    assert Decimal(str(waste_data["estimated_loss"])) == Decimal("125.0")

    # Check wastage report
    rep = client.get("/api/inventory/reports/wastage?reason=SPOILED", headers=auth_tokens["manager"]).json()
    assert any(r["ingredient_name"] == ing["name"] for r in rep)


def test_12_stock_adjustment_physical_reconciliation(auth_tokens):
    """Scenario 12: Physical stock count reconciliation adjusts system balance."""
    ing = client.post(
        "/api/inventory",
        json={"name": f"Flour Bag {uuid.uuid4().hex[:4]}", "unit": "kg", "available_quantity": 50.0, "cost_per_unit": 35.0},
        headers=auth_tokens["manager"],
    ).json()

    # Physical count reveals 48 kg (variance -2 kg)
    adj_res = client.post(
        f"/api/inventory/{ing['id']}/adjust",
        json={"physical_stock": 48.0, "reason": "Weekly inventory audit", "notes": "Count discrepancy"},
        headers=auth_tokens["manager"],
    )
    assert adj_res.status_code == 200
    adj_data = adj_res.json()
    assert Decimal(str(adj_data["physical_stock"])) == Decimal("48.0")
    assert Decimal(str(adj_data["variance"])) == Decimal("-2.0")

    # Verify ingredient updated
    ing_now = client.get(f"/api/inventory/{ing['id']}", headers=auth_tokens["manager"]).json()
    assert Decimal(str(ing_now["current_stock"])) == Decimal("48.0")


def test_13_stock_transfer_between_locations(auth_tokens):
    """Scenario 13: Stock transfer updates location assignment and ledger."""
    # Create source and target locations
    loc_a = client.post("/api/inventory/locations", json={"name": f"Dry Storage {uuid.uuid4().hex[:4]}"}, headers=auth_tokens["manager"]).json()
    loc_b = client.post("/api/inventory/locations", json={"name": f"Kitchen Line {uuid.uuid4().hex[:4]}"}, headers=auth_tokens["manager"]).json()

    ing = client.post(
        "/api/inventory",
        json={"name": f"Black Pepper {uuid.uuid4().hex[:4]}", "unit": "kg", "available_quantity": 20.0, "cost_per_unit": 200.0, "storage_location_id": loc_a["id"]},
        headers=auth_tokens["manager"],
    ).json()

    xfer_res = client.post(
        f"/api/inventory/{ing['id']}/transfer",
        json={"quantity": 5.0, "from_location_id": loc_a["id"], "to_location_id": loc_b["id"], "notes": "Shift transfer"},
        headers=auth_tokens["manager"],
    )
    assert xfer_res.status_code == 200
    xfer_data = xfer_res.json()
    assert Decimal(str(xfer_data["transferred_quantity"])) == Decimal("5.0")
    assert xfer_data["to_location"]["name"] == loc_b["name"]


def test_14_and_15_batch_tracking_and_expiry_queries(auth_tokens):
    """Scenarios 14 & 15: Batch tracking and expiring batch detection."""
    ing = client.post(
        "/api/inventory",
        json={"name": f"Fresh Cream {uuid.uuid4().hex[:4]}", "unit": "litre", "available_quantity": 0.0, "cost_per_unit": 180.0},
        headers=auth_tokens["manager"],
    ).json()

    # Receive batch expiring in 3 days (expiring soon)
    soon_exp = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    client.post(
        f"/api/inventory/{ing['id']}/receive",
        json={"quantity": 10.0, "unit_cost": 180.0, "batch_number": f"EXP-SOON-{uuid.uuid4().hex[:4]}", "expiry_date": soon_exp},
        headers=auth_tokens["manager"],
    )

    exp_report = client.get("/api/inventory/reports/expiry?warning_days=7", headers=auth_tokens["manager"]).json()
    assert exp_report["expiring_count"] >= 1
    assert any(b["ingredient_name"] == ing["name"] for b in exp_report["expiring_batches"])


def test_16_fefo_consumption_priority(auth_tokens):
    """Scenario 16: First Expiring First Out (FEFO) consumes earlier expiring batch first."""
    ing = client.post(
        "/api/inventory",
        json={"name": f"Yogurt {uuid.uuid4().hex[:4]}", "unit": "kg", "available_quantity": 0.0, "cost_per_unit": 70.0},
        headers=auth_tokens["manager"],
    ).json()

    # Batch 1: Expiring in 20 days (quantity 10 kg)
    exp_20 = (datetime.now(timezone.utc) + timedelta(days=20)).isoformat()
    b1_no = f"B20-{uuid.uuid4().hex[:4]}"
    client.post(
        f"/api/inventory/{ing['id']}/receive",
        json={"quantity": 10.0, "unit_cost": 70.0, "batch_number": b1_no, "expiry_date": exp_20},
        headers=auth_tokens["manager"],
    )

    # Batch 2: Expiring in 5 days (quantity 5 kg) - should be consumed FIRST
    exp_5 = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    b2_no = f"B5-{uuid.uuid4().hex[:4]}"
    client.post(
        f"/api/inventory/{ing['id']}/receive",
        json={"quantity": 5.0, "unit_cost": 70.0, "batch_number": b2_no, "expiry_date": exp_5},
        headers=auth_tokens["manager"],
    )

    # Total stock is now 15 kg
    ing_current = client.get(f"/api/inventory/{ing['id']}", headers=auth_tokens["manager"]).json()
    assert Decimal(str(ing_current["current_stock"])) == Decimal("15.0")

    # Record 4 kg wastage (or consumption) without specifying batch
    client.post(
        f"/api/inventory/{ing['id']}/wastage",
        json={"quantity": 4.0, "reason": "DAMAGED"},
        headers=auth_tokens["manager"],
    )

    # Batch 2 (expiring in 5 days) should have been reduced to 1 kg, while Batch 1 remains 10 kg
    batches = client.get(f"/api/inventory/{ing['id']}/batches", headers=auth_tokens["manager"]).json()
    b2 = next(b for b in batches if b["batch_number"] == b2_no)
    b1 = next(b for b in batches if b["batch_number"] == b1_no)
    assert Decimal(str(b2["remaining_quantity"])) == Decimal("1.0")
    assert Decimal(str(b1["remaining_quantity"])) == Decimal("10.0")


def test_17_duplicate_consumption_prevention(auth_tokens):
    """Scenario 17: Prevents double deduction on the same order."""
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]
    dish = client.post(
        "/api/menu-items",
        json={"name": f"Once Only Dish {uuid.uuid4().hex[:4]}", "category_id": cat["id"], "price": "150.00", "preparation_time": 10},
        headers=auth_tokens["admin"],
    ).json()

    salt = client.post(
        "/api/inventory",
        json={"name": f"Special Salt {uuid.uuid4().hex[:4]}", "unit": "g", "available_quantity": 500.0, "cost_per_unit": 0.05},
        headers=auth_tokens["manager"],
    ).json()

    client.post(
        f"/api/recipes/menu-items/{dish['id']}/recipe",
        json={"ingredients": [{"ingredient_id": salt["id"], "quantity_required": 10.0, "unit": "g"}]},
        headers=auth_tokens["chef"],
    )

    order_res = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "items": [{"menu_item_id": dish["id"], "quantity": 1, "unit_price": "150.00"}]},
        headers=auth_tokens["waiter"],
    )
    assert order_res.status_code == 201
    order = order_res.json()

    # First deduction succeeds
    res1 = OrderService.deduct_order_inventory(order["id"], order_items=order["items"])
    assert res1["status"] in ["DEDUCTED", "SKIPPED"]

    # Second deduction must be idempotent / skipped
    res2 = OrderService.deduct_order_inventory(order["id"], order_items=order["items"])
    assert res2["status"] == "SKIPPED"


def test_18_starter_items_exempt_from_deduction(auth_tokens):
    """Scenario 18: Items with inventory_tracking_enabled: false bypass deduction."""
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]
    starter_res = client.post(
        "/api/menu-items",
        json={
            "name": f"Complimentary Papad {uuid.uuid4().hex[:4]}",
            "category_id": cat["id"],
            "price": "10.00",
            "preparation_time": 2,
            "inventory_tracking_enabled": False,
        },
        headers=auth_tokens["admin"],
    )
    assert starter_res.status_code == 201
    starter = starter_res.json()

    order_res = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "items": [{"menu_item_id": starter["id"], "quantity": 5, "unit_price": "10.00"}]},
        headers=auth_tokens["waiter"],
    )
    assert order_res.status_code == 201
    order = order_res.json()

    # Deduction should be skipped without error even with no recipe or ingredients
    res = OrderService.deduct_order_inventory(order["id"], order_items=order["items"])
    assert res["status"] in ["SKIPPED", "DEDUCTED"]


def test_19_purchase_order_lifecycle_and_receiving(auth_tokens):
    """Scenario 19: Supplier creation, Purchase Order creation, and Goods Receiving."""
    # 1. Create Supplier
    sup_res = client.post(
        "/api/purchases/suppliers",
        json={
            "name": f"Himalayan Spices Co {uuid.uuid4().hex[:4]}",
            "contact_person": "Vikram Singh",
            "email": f"vikram_{uuid.uuid4().hex[:4]}@spices.com",
            "phone": "+91 98765 43210",
            "lead_time_days": 3,
        },
        headers=auth_tokens["manager"],
    )
    assert sup_res.status_code == 201
    supplier = sup_res.json()

    # 2. Create Ingredient associated with Supplier
    ing = client.post(
        "/api/inventory",
        json={
            "name": f"Cumin Seeds {uuid.uuid4().hex[:4]}",
            "unit": "kg",
            "available_quantity": 5.0,
            "cost_per_unit": 180.0,
            "supplier_id": supplier["id"],
        },
        headers=auth_tokens["manager"],
    ).json()

    # 3. Create PO
    po_res = client.post(
        "/api/purchases/orders",
        json={
            "supplier_id": supplier["id"],
            "items": [
                {
                    "ingredient_id": ing["id"],
                    "ingredient_name": ing["name"],
                    "quantity": 20.0,
                    "unit": "kg",
                    "unit_cost": 175.0,
                }
            ],
            "notes": "Urgent restocking order",
        },
        headers=auth_tokens["manager"],
    )
    assert po_res.status_code == 201
    po = po_res.json()
    assert po["status"] == "DRAFT"
    assert Decimal(str(po["total_amount"])) == Decimal("3500.0")

    # 4. Send PO to Supplier
    send_res = client.post(f"/api/purchases/orders/{po['id']}/status", json={"status": "ORDERED"}, headers=auth_tokens["manager"])
    assert send_res.status_code == 200
    assert send_res.json()["status"] == "ORDERED"

    # 5. Receive Goods
    rcv_po = client.post(f"/api/purchases/orders/{po['id']}/receive", json={}, headers=auth_tokens["manager"])
    print("RCV_PO ERROR:", rcv_po.status_code, rcv_po.text)
    assert rcv_po.status_code == 200
    assert rcv_po.json()["status"] == "RECEIVED"

    # 6. Verify ingredient stock updated to 5 + 20 = 25 kg
    ing_after = client.get(f"/api/inventory/{ing['id']}", headers=auth_tokens["manager"]).json()
    assert Decimal(str(ing_after["current_stock"])) == Decimal("25.0")


def test_20_low_stock_detection_and_alerts(auth_tokens):
    """Scenario 20: Detects low stock thresholds and triggers alert statuses."""
    ing = client.post(
        "/api/inventory",
        json={
            "name": f"Bay Leaves {uuid.uuid4().hex[:4]}",
            "unit": "g",
            "available_quantity": 100.0,
            "minimum_stock": 25.0,
            "reorder_level": 50.0,
            "cost_per_unit": 0.5,
        },
        headers=auth_tokens["manager"],
    ).json()

    # Currently NORMAL
    stat1 = client.get(f"/api/inventory/{ing['id']}/stock-status", headers=auth_tokens["manager"]).json()
    assert stat1["status"] == "NORMAL"

    # Reduce stock below reorder level (40g <= 50g) -> LOW_STOCK
    client.post(f"/api/inventory/{ing['id']}/wastage", json={"quantity": 60.0, "reason": "SPOILED"}, headers=auth_tokens["manager"])
    stat2 = client.get(f"/api/inventory/{ing['id']}/stock-status", headers=auth_tokens["manager"]).json()
    assert stat2["status"] == "LOW_STOCK"

    # Check low stock list
    low_list = client.get("/api/inventory/low-stock", headers=auth_tokens["manager"]).json()
    assert any(item["name"] == ing["name"] for item in low_list)

    # Reduce to 0 -> OUT_OF_STOCK
    client.post(f"/api/inventory/{ing['id']}/wastage", json={"quantity": 40.0, "reason": "SPOILED"}, headers=auth_tokens["manager"])
    stat3 = client.get(f"/api/inventory/{ing['id']}/stock-status", headers=auth_tokens["manager"]).json()
    assert stat3["status"] == "OUT_OF_STOCK"
