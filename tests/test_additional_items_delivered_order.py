"""
Tests for adding new items to an already delivered order.
Covers:
- Order lifecycle: placed -> prepared -> DELIVERED
- Adding new items to an existing delivered order keeping the same order ID
- Preserving existing delivered items and their statuses
- Appending new items with item-level status (PENDING -> PREPARING -> READY -> DELIVERED)
- Batch/round tracking and timestamps
- Recalculating billing: previous item total, newly added item total, taxes, discounts, final payable amount
- Kitchen ticket workflow integration for additional items
- Inventory deduction for newly added items without double-deducting original items
- Item-level status updates and overall order status calculation
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.mongodb import (
    orders_collection,
    order_items_collection,
    menu_items_collection,
    ingredients_collection,
    recipes_collection,
    kitchen_tickets_collection,
    invoices_collection,
)
from app.services.common import decimal128, to_object_id
from app.services.order_service import OrderService, OrderItemService


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    res = client.post("/api/auth/login", json={"email": "admin@dineflow.com", "password": "Password123!"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_menu_items():
    """Ensure menu items with and without recipes exist for test."""
    # 1. Chicken Biryani (with recipe)
    cb = menu_items_collection.find_one({"name": "Test Chicken Biryani"})
    if not cb:
        res = menu_items_collection.insert_one({
            "name": "Test Chicken Biryani",
            "price": decimal128("250.00"),
            "preparation_time": 20,
            "category_id": None,
            "is_available": True,
            "is_vegetarian": False,
        })
        cb = menu_items_collection.find_one({"_id": res.inserted_id})

    # 2. Coke (beverage, no recipe)
    coke = menu_items_collection.find_one({"name": "Test Coke"})
    if not coke:
        res = menu_items_collection.insert_one({
            "name": "Test Coke",
            "price": decimal128("50.00"),
            "preparation_time": 5,
            "category_id": None,
            "is_available": True,
            "is_vegetarian": True,
        })
        coke = menu_items_collection.find_one({"_id": res.inserted_id})

    # 3. Chicken 65 (starter with recipe)
    c65 = menu_items_collection.find_one({"name": "Test Chicken 65"})
    if not c65:
        res = menu_items_collection.insert_one({
            "name": "Test Chicken 65",
            "price": decimal128("180.00"),
            "preparation_time": 15,
            "category_id": None,
            "is_available": True,
            "is_vegetarian": False,
        })
        c65 = menu_items_collection.find_one({"_id": res.inserted_id})

    # 4. Ice Cream (dessert, no recipe)
    icecream = menu_items_collection.find_one({"name": "Test Ice Cream"})
    if not icecream:
        res = menu_items_collection.insert_one({
            "name": "Test Ice Cream",
            "price": decimal128("100.00"),
            "preparation_time": 5,
            "category_id": None,
            "is_available": True,
            "is_vegetarian": True,
        })
        icecream = menu_items_collection.find_one({"_id": res.inserted_id})

    # Ensure chicken ingredient exists with sufficient stock
    chicken_ing = ingredients_collection.find_one({"name": "Test Chicken Meat"})
    if not chicken_ing:
        res = ingredients_collection.insert_one({
            "name": "Test Chicken Meat",
            "unit": "KG",
            "available_quantity": decimal128("50.00"),
            "minimum_stock_level": decimal128("5.00"),
            "cost_per_unit": decimal128("200.00"),
            "is_active": True,
        })
        chicken_ing = ingredients_collection.find_one({"_id": res.inserted_id})
    else:
        ingredients_collection.update_one(
            {"_id": chicken_ing["_id"]},
            {"$set": {"available_quantity": decimal128("50.00")}}
        )

    # Attach recipe for Chicken Biryani (0.2 kg chicken) and Chicken 65 (0.15 kg chicken)
    recipes_collection.delete_many({"menu_item_id": cb["_id"]})
    recipes_collection.insert_one({
        "menu_item_id": cb["_id"],
        "ingredient_id": chicken_ing["_id"],
        "quantity_required": decimal128("0.20"),
        "unit": "KG",
    })

    recipes_collection.delete_many({"menu_item_id": c65["_id"]})
    recipes_collection.insert_one({
        "menu_item_id": c65["_id"],
        "ingredient_id": chicken_ing["_id"],
        "quantity_required": decimal128("0.15"),
        "unit": "KG",
    })

    return {
        "chicken_biryani": cb,
        "coke": coke,
        "chicken_65": c65,
        "ice_cream": icecream,
        "chicken_ingredient": chicken_ing,
    }


def test_add_items_to_already_delivered_order_flow(client, auth_headers, sample_menu_items):
    cb = sample_menu_items["chicken_biryani"]
    coke = sample_menu_items["coke"]
    c65 = sample_menu_items["chicken_65"]
    ice_cream = sample_menu_items["ice_cream"]
    chicken_ing = sample_menu_items["chicken_ingredient"]

    # 1. Place initial order with Chicken Biryani x 1 (250) and Coke x 1 (50) -> subtotal = 300
    order_res = client.post(
        "/api/orders",
        headers=auth_headers,
        json={
            "customer_name": "Test Customer",
            "order_type": "DINE_IN",
            "items": [
                {"menu_item_id": str(cb["_id"]), "quantity": 1},
                {"menu_item_id": str(coke["_id"]), "quantity": 1},
            ],
        },
    )
    assert order_res.status_code == 201, f"Create order failed: {order_res.json()}"
    order_data = order_res.json()
    order_id = order_data["id"]
    order_number = order_data["order_number"]

    # Confirm order
    confirm_res = client.post(f"/api/orders/{order_id}/confirm", headers=auth_headers)
    assert confirm_res.status_code == 200

    # Advance order through cooking and serve/deliver
    client.patch(f"/api/orders/{order_id}/status", headers=auth_headers, json={"status": "PREPARING"})
    client.patch(f"/api/orders/{order_id}/status", headers=auth_headers, json={"status": "READY"})
    deliver_res = client.patch(f"/api/orders/{order_id}/status", headers=auth_headers, json={"status": "DELIVERED"})
    assert deliver_res.status_code == 200
    delivered_order = deliver_res.json()
    assert delivered_order["status"] == "DELIVERED"
    assert float(delivered_order["subtotal"]) == 300.0

    # Verify inventory was deducted for round 1 (0.20 kg chicken)
    ing_after_r1 = ingredients_collection.find_one({"_id": chicken_ing["_id"]})
    stock_r1 = ing_after_r1["available_quantity"].to_decimal()
    assert stock_r1 == Decimal("49.80")  # 50 - 0.20

    # Verify order items are DELIVERED
    items_r1 = client.get(f"/api/orders/{order_id}/items", headers=auth_headers).json()
    assert len(items_r1) == 2
    for it in items_r1:
        assert it["status"] == "DELIVERED"
        assert it["batch_number"] == 1
        assert it["is_additional"] is False

    # 2. Customer orders additional items: Chicken 65 x 1 (180) and Ice Cream x 1 (100)
    add_res = client.post(
        f"/api/orders/{order_id}/additional-items",
        headers=auth_headers,
        json={
            "items": [
                {"menu_item_id": str(c65["_id"]), "quantity": 1, "special_instructions": "Extra crispy"},
                {"menu_item_id": str(ice_cream["_id"]), "quantity": 1},
            ]
        },
    )
    assert add_res.status_code == 200, f"add_res failed: {add_res.json()}"
    updated_order = add_res.json()

    # Rule Check: SAME order ID and order number!
    assert updated_order["id"] == order_id
    assert updated_order["order_number"] == order_number

    # Rule Check: Statuses of items and overall order
    # Original items remain DELIVERED, new items are PENDING
    all_items = client.get(f"/api/orders/{order_id}/items", headers=auth_headers).json()
    assert len(all_items) == 4

    original_items = [it for it in all_items if not it["is_additional"]]
    new_items = [it for it in all_items if it["is_additional"]]

    assert len(original_items) == 2
    assert len(new_items) == 2

    # Original items unchanged and still DELIVERED
    assert {it["item_name_snapshot"] for it in original_items} == {"Test Chicken Biryani", "Test Coke"}
    for it in original_items:
        assert it["status"] == "DELIVERED"
        assert it["batch_number"] == 1

    # Newly added items are PENDING, batch_number=2, price_at_addition recorded
    assert {it["item_name_snapshot"] for it in new_items} == {"Test Chicken 65", "Test Ice Cream"}
    for it in new_items:
        assert it["status"] == "PENDING"
        assert it["batch_number"] == 2
        assert it["is_additional"] is True
        assert it["added_at"] is not None
        assert float(it["price_at_addition"]) in [180.0, 100.0]

    # Rule Check: Billing breakdown recalculation
    # Previous total = 300, Additional items = 280, New subtotal = 580, Tax = 5% of 580 = 29, Total = 609
    assert float(updated_order["previous_item_total"]) == 300.0
    assert float(updated_order["new_item_total"]) == 280.0
    assert float(updated_order["subtotal"]) == 580.0
    assert float(updated_order["tax_amount"]) == 29.0
    assert float(updated_order["total_amount"]) == 609.0

    # Rule Check: Kitchen ticket was updated or queued for round 2
    ticket = kitchen_tickets_collection.find_one({"order_id": to_object_id(order_id)})
    assert ticket is not None
    assert ticket["status"] in ["QUEUED", "PREPARING"]

    # 3. Advance new items through cooking process
    c65_item = next(it for it in new_items if it["item_name_snapshot"] == "Test Chicken 65")
    ice_cream_item = next(it for it in new_items if it["item_name_snapshot"] == "Test Ice Cream")

    # Move C65 to PREPARING
    patch_item_res = client.patch(
        f"/api/orders/{order_id}/items/{c65_item['id']}/status",
        headers=auth_headers,
        json={"status": "PREPARING"},
    )
    assert patch_item_res.status_code == 200

    # Move C65 to READY
    client.patch(
        f"/api/orders/{order_id}/items/{c65_item['id']}/status",
        headers=auth_headers,
        json={"status": "READY"},
    )

    # Deliver C65: triggers its recipe inventory deduction (0.15 kg chicken) without re-deducting biryani!
    deliver_c65_res = client.patch(
        f"/api/orders/{order_id}/items/{c65_item['id']}/status",
        headers=auth_headers,
        json={"status": "DELIVERED"},
    )
    assert deliver_c65_res.status_code == 200

    ing_after_c65 = ingredients_collection.find_one({"_id": chicken_ing["_id"]})
    stock_after_c65 = ing_after_c65["available_quantity"].to_decimal()
    # 49.80 - 0.15 = 49.65 kg (only C65 was deducted!)
    assert stock_after_c65 == Decimal("49.65")

    # Deliver Ice Cream (no recipe)
    client.patch(
        f"/api/orders/{order_id}/items/{ice_cream_item['id']}/status",
        headers=auth_headers,
        json={"status": "DELIVERED"},
    )

    # Now all items are DELIVERED -> overall order status is DELIVERED!
    final_order = client.get(f"/api/orders/{order_id}", headers=auth_headers).json()
    assert final_order["status"] == "DELIVERED"
    assert float(final_order["subtotal"]) == 580.0
    assert float(final_order["total_amount"]) == 609.0

    # 4. Generate Invoice and verify breakdown in invoice
    inv_res = client.post(f"/api/orders/{order_id}/invoice", headers=auth_headers)
    assert inv_res.status_code == 201
    invoice = inv_res.json()
    assert float(invoice["subtotal"]) == 580.0
    assert float(invoice["previous_item_total"]) == 300.0
    assert float(invoice["new_item_total"]) == 280.0
    assert float(invoice["total_amount"]) == 609.0
    assert len(invoice["items"]) == 4
