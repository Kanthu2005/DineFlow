"""
Automated Pytest Suite for Restaurant Order & Kitchen Operations System.
Covers all 30 core assignment test requirements + advanced features.
Runs against FastAPI application with 100% MongoDB backend.
"""

import uuid
import pytest
from decimal import Decimal
from bson import ObjectId
from fastapi.testclient import TestClient
from app.main import app
from app.database.mongodb import (
    users_collection,
    customers_collection,
    menu_categories_collection,
    menu_items_collection,
    ingredients_collection,
    recipes_collection,
    restaurant_tables_collection,
    reservations_collection,
    orders_collection,
    order_items_collection,
    kitchen_tickets_collection,
    invoices_collection,
    payments_collection,
    refunds_collection,
    order_activity_logs_collection,
    kitchen_events_collection,
    customer_feedback_collection,
)
from app.services.service import hash_password, now_utc

client = TestClient(app)


@pytest.fixture(scope="session")
def auth_tokens():
    """Seeds test users if not present and returns authorization headers for roles."""
    roles = {
        "admin": ("admin@dineflow.com", "Password123!", "ADMIN"),
        "manager": ("manager@dineflow.com", "Password123!", "MANAGER"),
        "chef": ("chef@dineflow.com", "Password123!", "CHEF"),
        "waiter": ("waiter@dineflow.com", "Password123!", "WAITER"),
        "cashier": ("cashier@dineflow.com", "Password123!", "CASHIER"),
    }

    headers = {}
    for role_key, (email, pwd, role_val) in roles.items():
        # Ensure user exists in MongoDB
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

        # Authenticate
        login_res = client.post("/api/auth/login", json={"email": email, "password": pwd})
        assert login_res.status_code == 200, f"Failed to login as {email}: {login_res.text}"
        token = login_res.json()["access_token"]
        headers[role_key] = {"Authorization": f"Bearer {token}"}

    return headers


# ==============================================================================
# MENU TESTS (1 - 5)
# ==============================================================================

def test_01_create_menu_item_successfully(auth_tokens):
    """1. Create menu item successfully."""
    # Create category first
    cat_res = client.post(
        "/api/menu/categories",
        json={"name": "Biryani Specials", "description": "Royal biryanis"},
        headers=auth_tokens["admin"],
    )
    if cat_res.status_code == 201:
        cat_id = cat_res.json()["id"]
    else:
        # already exists
        cat_id = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]["id"]

    res = client.post(
        "/api/menu-items",
        json={
            "name": "Chicken Biryani",
            "description": "Fragrant basmati rice cooked with spiced chicken",
            "category_id": cat_id,
            "price": "280.00",
            "preparation_time": 25,
            "is_available": True,
            "is_vegetarian": False,
        },
        headers=auth_tokens["admin"],
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Chicken Biryani"
    assert Decimal(str(data["price"])) == Decimal("280.00")
    assert data["preparation_time"] == 25


def test_02_reject_negative_price(auth_tokens):
    """2. Reject a negative price."""
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]
    res = client.post(
        "/api/menu-items",
        json={
            "name": "Invalid Price Item",
            "category_id": cat["id"],
            "price": "-10.00",
            "preparation_time": 15,
            "is_available": True,
        },
        headers=auth_tokens["admin"],
    )
    assert res.status_code in [400, 422]


def test_03_reject_zero_preparation_time(auth_tokens):
    """3. Reject zero preparation time."""
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]
    res = client.post(
        "/api/menu-items",
        json={
            "name": "Zero Prep Item",
            "category_id": cat["id"],
            "price": "150.00",
            "preparation_time": 0,
            "is_available": True,
        },
        headers=auth_tokens["admin"],
    )
    assert res.status_code in [400, 422]


def test_04_disable_unavailable_menu_item(auth_tokens):
    """4. Disable unavailable menu item."""
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]
    create_res = client.post(
        "/api/menu-items",
        json={
            "name": "Seasonal Fish Curry",
            "category_id": cat["id"],
            "price": "350.00",
            "preparation_time": 30,
            "is_available": True,
        },
        headers=auth_tokens["admin"],
    )
    assert create_res.status_code == 201
    item_id = create_res.json()["id"]

    # Disable availability
    patch_res = client.patch(
        f"/api/menu-items/{item_id}/availability?is_available=false",
        headers=auth_tokens["admin"],
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["is_available"] is False


def test_05_search_menu_by_category(auth_tokens):
    """5. Search menu by category."""
    cats = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()
    cat_id = cats[0]["id"]
    res = client.get(f"/api/menu-items/category/{cat_id}", headers=auth_tokens["admin"])
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)
    for it in items:
        assert it["category_id"] == cat_id


# ==============================================================================
# INVENTORY TESTS (6 - 10)
# ==============================================================================

def test_06_add_ingredient_stock(auth_tokens):
    """6. Add ingredient stock."""
    # Create or find Basmati Rice
    ing_res = client.post(
        "/api/ingredients",
        json={
            "name": "Basmati Rice Test",
            "unit": "KG",
            "available_quantity": "50.0",
            "minimum_stock_level": "10.0",
            "cost_per_unit": "80.0",
            "supplier_name": "ABC Suppliers",
        },
        headers=auth_tokens["manager"],
    )
    if ing_res.status_code == 201:
        ing = ing_res.json()
    else:
        ing = client.get("/api/ingredients", headers=auth_tokens["manager"]).json()[0]

    # Add 10 KG
    stock_res = client.post(
        f"/api/ingredients/{ing['id']}/stock",
        json={"quantity": 10.0},
        headers=auth_tokens["manager"],
    )
    assert stock_res.status_code == 200
    updated_stock = Decimal(str(stock_res.json()["available_quantity"]))
    orig_stock = Decimal(str(ing["available_quantity"]))
    assert updated_stock == orig_stock + Decimal("10.0")


def test_07_deduct_available_stock(auth_tokens):
    """7. Deduct available stock."""
    ing = client.get("/api/ingredients", headers=auth_tokens["manager"]).json()[0]
    stock_before = Decimal(str(ing["available_quantity"]))

    # Deduct 2 KG
    deduct_res = client.post(
        f"/api/ingredients/{ing['id']}/stock",
        json={"quantity": -2.0},
        headers=auth_tokens["manager"],
    )
    assert deduct_res.status_code == 200
    stock_after = Decimal(str(deduct_res.json()["available_quantity"]))
    assert stock_after == stock_before - Decimal("2.0")


def test_08_reject_deduction_when_stock_is_insufficient(auth_tokens):
    """8. Reject deduction when stock is insufficient."""
    ing_name = f"Saffron Threads Test {uuid.uuid4().hex[:6]}"
    ing_res = client.post(
        "/api/ingredients",
        json={
            "name": ing_name,
            "unit": "G",
            "available_quantity": "5.0",
            "minimum_stock_level": "2.0",
            "cost_per_unit": "200.0",
        },
        headers=auth_tokens["manager"],
    )
    ing_id = ing_res.json()["id"]

    # Try deducting 100 G when only 5 G exists
    res = client.post(
        f"/api/ingredients/{ing_id}/stock",
        json={"quantity": -100.0},
        headers=auth_tokens["manager"],
    )
    assert res.status_code in [400, 422]


def test_09_prevent_negative_stock(auth_tokens):
    """9. Prevent negative stock."""
    ing = client.get("/api/ingredients", headers=auth_tokens["manager"]).json()[-1]
    curr_qty = Decimal(str(ing["available_quantity"]))
    excessive_deduction = -(curr_qty + Decimal("50.0"))

    res = client.post(
        f"/api/ingredients/{ing['id']}/stock",
        json={"quantity": float(excessive_deduction)},
        headers=auth_tokens["manager"],
    )
    assert res.status_code in [400, 422]


def test_10_generate_low_stock_alert(auth_tokens):
    """10. Generate low-stock alert."""
    # Create ingredient with available <= minimum
    low_name = f"Fresh Cream Low Stock Test {uuid.uuid4().hex[:6]}"
    res = client.post(
        "/api/ingredients",
        json={
            "name": low_name,
            "unit": "L",
            "available_quantity": "3.0",
            "minimum_stock_level": "5.0",
            "cost_per_unit": "120.0",
        },
        headers=auth_tokens["manager"],
    )
    assert res.status_code == 201
    ing = res.json()

    # Query low stock endpoint
    low_res = client.get("/api/ingredients/low-stock", headers=auth_tokens["manager"])
    assert low_res.status_code == 200
    low_items = low_res.json()
    matching = [i for i in low_items if i["id"] == ing["id"]]
    assert len(matching) == 1
    assert matching[0]["alert_level"] in ["CRITICAL", "LOW", "OUT_OF_STOCK"]


# ==============================================================================
# ORDER TESTS (11 - 18)
# ==============================================================================

def test_11_create_order_with_valid_items(auth_tokens):
    """11. Create an order with valid items."""
    # Create order
    order_res = client.post(
        "/api/orders",
        json={"order_type": "DINE_IN", "created_by": "WAITER"},
        headers=auth_tokens["waiter"],
    )
    assert order_res.status_code == 201
    order = order_res.json()
    assert order["status"] == "DRAFT"

    # Add available menu item
    items = client.get("/api/menu-items/available", headers=auth_tokens["waiter"]).json()
    assert len(items) > 0
    menu_item = items[0]

    item_res = client.post(
        f"/api/orders/{order['id']}/items",
        json={"menu_item_id": menu_item["id"], "quantity": 2, "special_instructions": "Less spicy"},
        headers=auth_tokens["waiter"],
    )
    assert item_res.status_code == 201
    item_data = item_res.json()
    assert item_data["quantity"] == 2
    assert item_data["item_name_snapshot"] == menu_item["name"]


def test_12_reject_unavailable_menu_item(auth_tokens):
    """12. Reject an unavailable menu item."""
    # Create unavailable menu item
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]
    unavail_item = client.post(
        "/api/menu-items",
        json={
            "name": "Out of Season Mango Lassi",
            "category_id": cat["id"],
            "price": "90.00",
            "preparation_time": 5,
            "is_available": False,
        },
        headers=auth_tokens["admin"],
    ).json()

    order = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "created_by": "WAITER"},
        headers=auth_tokens["waiter"],
    ).json()

    res = client.post(
        f"/api/orders/{order['id']}/items",
        json={"menu_item_id": unavail_item["id"], "quantity": 1},
        headers=auth_tokens["waiter"],
    )
    assert res.status_code in [400, 422]


def test_13_reject_empty_order(auth_tokens):
    """13. Reject an empty order confirmation."""
    order = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "created_by": "WAITER"},
        headers=auth_tokens["waiter"],
    ).json()

    # Try to confirm empty order
    res = client.post(f"/api/orders/{order['id']}/confirm", headers=auth_tokens["waiter"])
    assert res.status_code in [400, 422]


def test_14_calculate_subtotal_correctly(auth_tokens):
    """14. Calculate subtotal correctly."""
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]

    # Create 2 items with known prices
    item1 = client.post(
        "/api/menu-items",
        json={"name": "Item A Subtotal Test", "category_id": cat["id"], "price": "200.00", "preparation_time": 10},
        headers=auth_tokens["admin"],
    ).json()

    item2 = client.post(
        "/api/menu-items",
        json={"name": "Item B Subtotal Test", "category_id": cat["id"], "price": "150.00", "preparation_time": 10},
        headers=auth_tokens["admin"],
    ).json()

    order = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "created_by": "WAITER"},
        headers=auth_tokens["waiter"],
    ).json()

    client.post(f"/api/orders/{order['id']}/items", json={"menu_item_id": item1["id"], "quantity": 2}, headers=auth_tokens["waiter"])
    client.post(f"/api/orders/{order['id']}/items", json={"menu_item_id": item2["id"], "quantity": 3}, headers=auth_tokens["waiter"])

    order_fetched = client.get(f"/api/orders/{order['id']}", headers=auth_tokens["waiter"]).json()
    # 2 * 200 + 3 * 150 = 400 + 450 = 850
    assert Decimal(str(order_fetched["subtotal"])) == Decimal("850.00")
    # 5% tax = 42.50
    assert Decimal(str(order_fetched["tax_amount"])) == Decimal("42.50")
    # total = 892.50
    assert Decimal(str(order_fetched["total_amount"])) == Decimal("892.50")


def test_15_store_price_snapshot(auth_tokens):
    """15. Store price snapshot (Order retains original price even if menu price changes)."""
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]
    item = client.post(
        "/api/menu-items",
        json={"name": "Snapshot Test Item", "category_id": cat["id"], "price": "100.00", "preparation_time": 10},
        headers=auth_tokens["admin"],
    ).json()

    order = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "created_by": "WAITER"},
        headers=auth_tokens["waiter"],
    ).json()

    order_item = client.post(
        f"/api/orders/{order['id']}/items",
        json={"menu_item_id": item["id"], "quantity": 1},
        headers=auth_tokens["waiter"],
    ).json()
    assert Decimal(str(order_item["unit_price_snapshot"])) == Decimal("100.00")

    # Now change menu item price to 150.00
    client.put(
        f"/api/menu-items/{item['id']}",
        json={"price": "150.00"},
        headers=auth_tokens["admin"],
    )

    # Order item price snapshot must still remain 100.00
    saved_item = client.get(f"/api/orders/{order['id']}/items", headers=auth_tokens["waiter"]).json()[0]
    assert Decimal(str(saved_item["unit_price_snapshot"])) == Decimal("100.00")


def test_16_reject_invalid_quantity(auth_tokens):
    """16. Reject invalid quantity (zero or negative)."""
    items = client.get("/api/menu-items/available", headers=auth_tokens["waiter"]).json()
    order = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "created_by": "WAITER"},
        headers=auth_tokens["waiter"],
    ).json()

    res = client.post(
        f"/api/orders/{order['id']}/items",
        json={"menu_item_id": items[0]["id"], "quantity": -5},
        headers=auth_tokens["waiter"],
    )
    assert res.status_code in [400, 422]


def test_17_prevent_invalid_status_transition(auth_tokens):
    """17. Prevent invalid status transition (e.g. from FINALIZED status)."""
    order = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "created_by": "WAITER"},
        headers=auth_tokens["waiter"],
    ).json()

    # Cancel order
    client.post(f"/api/orders/{order['id']}/cancel", headers=auth_tokens["waiter"])

    # Try moving cancelled order to PREPARING
    res = client.patch(
        f"/api/orders/{order['id']}/status",
        json={"status": "PREPARING"},
        headers=auth_tokens["waiter"],
    )
    assert res.status_code in [400, 422]


def test_18_cancel_eligible_order(auth_tokens):
    """18. Cancel an eligible order."""
    order = client.post(
        "/api/orders",
        json={"order_type": "DINE_IN", "created_by": "WAITER"},
        headers=auth_tokens["waiter"],
    ).json()

    cancel_res = client.post(
        f"/api/orders/{order['id']}/cancel",
        json={"reason": "Customer changed mind"},
        headers=auth_tokens["waiter"],
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"


# ==============================================================================
# KITCHEN TESTS (19 - 23)
# ==============================================================================

def test_19_create_kitchen_ticket_after_confirmation(auth_tokens):
    """19. Create kitchen ticket after order confirmation."""
    cat = client.get("/api/menu/categories", headers=auth_tokens["admin"]).json()[0]
    item = client.post(
        "/api/menu-items",
        json={"name": "Kitchen Test Item", "category_id": cat["id"], "price": "180.00", "preparation_time": 15},
        headers=auth_tokens["admin"],
    ).json()

    order = client.post(
        "/api/orders",
        json={"order_type": "TAKEAWAY", "created_by": "WAITER"},
        headers=auth_tokens["waiter"],
    ).json()

    client.post(
        f"/api/orders/{order['id']}/items",
        json={"menu_item_id": item["id"], "quantity": 1},
        headers=auth_tokens["waiter"],
    )

    confirm_res = client.post(f"/api/orders/{order['id']}/confirm", headers=auth_tokens["waiter"])
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] in ["CONFIRMED", "SENT_TO_KITCHEN"]

    tickets = client.get("/api/kitchen/tickets", headers=auth_tokens["chef"]).json()
    matching = [t for t in tickets if t["order_id"] == order["id"]]
    assert len(matching) == 1
    assert matching[0]["status"] == "QUEUED"


def test_20_assign_active_kitchen_staff(auth_tokens):
    """20. Assign active kitchen staff."""
    # Find chef user
    users = client.get("/api/users", headers=auth_tokens["admin"]).json()
    chef = next(u for u in users if u["role"] == "CHEF" and u["is_active"])
    users_collection.update_one({"_id": ObjectId(chef["id"])}, {"$set": {"maximum_active_orders": 999}})

    tickets = client.get("/api/kitchen/tickets", headers=auth_tokens["chef"]).json()
    ticket = tickets[0]

    assign_res = client.post(
        f"/api/kitchen/tickets/{ticket['id']}/assign",
        json={"staff_id": chef["id"], "station": "MAIN_COURSE"},
        headers=auth_tokens["manager"],
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["assigned_staff_id"] == chef["id"]


def test_21_reject_assignment_to_inactive_staff(auth_tokens):
    """21. Reject assignment to inactive staff."""
    # Create inactive chef
    chef_email = f"inactive_chef_{uuid.uuid4().hex[:6]}@dineflow.com"
    inactive_user = users_collection.insert_one({
        "name": "Inactive Chef",
        "email": chef_email,
        "password": hash_password("Password123!"),
        "role": "CHEF",
        "is_active": False,
        "created_at": now_utc(),
    })
    inactive_id = str(inactive_user.inserted_id)

    tickets = client.get("/api/kitchen/tickets", headers=auth_tokens["chef"]).json()
    ticket = tickets[0]

    res = client.post(
        f"/api/kitchen/tickets/{ticket['id']}/assign",
        json={"staff_id": inactive_id},
        headers=auth_tokens["manager"],
    )
    assert res.status_code in [400, 422]


def test_22_update_kitchen_status_correctly(auth_tokens):
    """22. Update kitchen status correctly (QUEUED -> ACCEPTED -> PREPARING -> READY -> HANDED_OVER)."""
    tickets = client.get("/api/kitchen/tickets?status=QUEUED", headers=auth_tokens["chef"]).json()
    if not tickets:
        # Create one
        item = client.get("/api/menu-items/available", headers=auth_tokens["waiter"]).json()[0]
        order = client.post("/api/orders", json={"order_type": "TAKEAWAY", "created_by": "WAITER"}, headers=auth_tokens["waiter"]).json()
        client.post(f"/api/orders/{order['id']}/items", json={"menu_item_id": item["id"], "quantity": 1}, headers=auth_tokens["waiter"])
        client.post(f"/api/orders/{order['id']}/confirm", headers=auth_tokens["waiter"])
        tickets = client.get("/api/kitchen/tickets?status=QUEUED", headers=auth_tokens["chef"]).json()

    ticket_id = tickets[0]["id"]

    # 1. Accept
    res_acc = client.post(f"/api/kitchen/tickets/{ticket_id}/accept", headers=auth_tokens["chef"])
    assert res_acc.status_code == 200
    assert res_acc.json()["status"] == "ACCEPTED"

    # 2. Start
    res_start = client.post(f"/api/kitchen/tickets/{ticket_id}/start", headers=auth_tokens["chef"])
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "PREPARING"

    # 3. Ready
    res_ready = client.post(f"/api/kitchen/tickets/{ticket_id}/ready", headers=auth_tokens["chef"])
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "READY"

    # 4. Handover
    res_handover = client.post(f"/api/kitchen/tickets/{ticket_id}/handover", headers=auth_tokens["waiter"])
    assert res_handover.status_code == 200
    assert res_handover.json()["status"] == "HANDED_OVER"


def test_23_estimate_preparation_time(auth_tokens):
    """23. Estimate preparation time."""
    items = client.get("/api/menu-items/available", headers=auth_tokens["waiter"]).json()
    order = client.post("/api/orders", json={"order_type": "TAKEAWAY", "created_by": "WAITER"}, headers=auth_tokens["waiter"]).json()
    client.post(f"/api/orders/{order['id']}/items", json={"menu_item_id": items[0]["id"], "quantity": 1}, headers=auth_tokens["waiter"])

    res = client.get(f"/api/kitchen/estimate-time/{order['id']}", headers=auth_tokens["chef"])
    assert res.status_code == 200
    data = res.json()
    assert "estimated_minutes" in data
    assert "estimated_ready_time" in data
    assert data["estimated_minutes"] >= items[0]["preparation_time"]


# ==============================================================================
# BILLING AND PAYMENT TESTS (24 - 28)
# ==============================================================================

def test_24_generate_invoice_correctly(auth_tokens):
    """24. Generate invoice correctly."""
    item = client.get("/api/menu-items/available", headers=auth_tokens["waiter"]).json()[0]
    order = client.post("/api/orders", json={"order_type": "TAKEAWAY", "created_by": "WAITER"}, headers=auth_tokens["waiter"]).json()
    client.post(f"/api/orders/{order['id']}/items", json={"menu_item_id": item["id"], "quantity": 2}, headers=auth_tokens["waiter"])

    inv_res = client.post(f"/api/orders/{order['id']}/invoice", headers=auth_tokens["cashier"])
    assert inv_res.status_code == 201
    invoice = inv_res.json()
    assert invoice["status"] == "UNPAID"
    assert "invoice_number" in invoice
    assert Decimal(str(invoice["total_amount"])) > 0


def test_25_reject_duplicate_payment(auth_tokens):
    """25. Reject duplicate payment transaction reference."""
    item = client.get("/api/menu-items/available", headers=auth_tokens["waiter"]).json()[0]
    order = client.post("/api/orders", json={"order_type": "TAKEAWAY", "created_by": "WAITER"}, headers=auth_tokens["waiter"]).json()
    client.post(f"/api/orders/{order['id']}/items", json={"menu_item_id": item["id"], "quantity": 1}, headers=auth_tokens["waiter"])
    inv = client.post(f"/api/orders/{order['id']}/invoice", headers=auth_tokens["cashier"]).json()

    ref = f"TXN_TEST_DUP_REF_{uuid.uuid4().hex[:8]}"
    half_amount = str(round(Decimal(str(inv["total_amount"])) / Decimal("2"), 2))
    # First payment: partial
    pay1 = client.post(
        "/api/payments",
        json={"invoice_id": inv["id"], "amount": half_amount, "payment_method": "UPI", "transaction_reference": ref},
        headers=auth_tokens["cashier"],
    )
    assert pay1.status_code == 201

    # Second payment with same transaction reference
    pay2 = client.post(
        "/api/payments",
        json={"invoice_id": inv["id"], "amount": half_amount, "payment_method": "UPI", "transaction_reference": ref},
        headers=auth_tokens["cashier"],
    )
    assert pay2.status_code in [400, 422]


def test_26_reject_payment_exceeding_outstanding_amount(auth_tokens):
    """26. Reject payment exceeding outstanding amount."""
    item = client.get("/api/menu-items/available", headers=auth_tokens["waiter"]).json()[0]
    order = client.post("/api/orders", json={"order_type": "TAKEAWAY", "created_by": "WAITER"}, headers=auth_tokens["waiter"]).json()
    client.post(f"/api/orders/{order['id']}/items", json={"menu_item_id": item["id"], "quantity": 1}, headers=auth_tokens["waiter"])
    inv = client.post(f"/api/orders/{order['id']}/invoice", headers=auth_tokens["cashier"]).json()

    total = Decimal(str(inv["total_amount"]))
    excessive_amount = total + Decimal("5000.00")

    res = client.post(
        "/api/payments",
        json={"invoice_id": inv["id"], "amount": str(excessive_amount), "payment_method": "CASH"},
        headers=auth_tokens["cashier"],
    )
    assert res.status_code in [400, 422]


def test_27_record_successful_payment(auth_tokens):
    """27. Record successful payment and mark invoice paid & order completed."""
    item = client.get("/api/menu-items/available", headers=auth_tokens["waiter"]).json()[0]
    order = client.post("/api/orders", json={"order_type": "TAKEAWAY", "created_by": "WAITER"}, headers=auth_tokens["waiter"]).json()
    client.post(f"/api/orders/{order['id']}/items", json={"menu_item_id": item["id"], "quantity": 1}, headers=auth_tokens["waiter"])
    inv = client.post(f"/api/orders/{order['id']}/invoice", headers=auth_tokens["cashier"]).json()

    pay_res = client.post(
        "/api/payments",
        json={
            "invoice_id": inv["id"],
            "amount": str(inv["total_amount"]),
            "payment_method": "CARD",
            "transaction_reference": f"TXN_{order['order_number']}",
        },
        headers=auth_tokens["cashier"],
    )
    assert pay_res.status_code == 201

    # Check invoice status is PAID
    inv_fetched = client.get(f"/api/invoices/{inv['id']}", headers=auth_tokens["cashier"]).json()
    assert inv_fetched["status"] == "PAID"

    # Check order is COMPLETED
    ord_fetched = client.get(f"/api/orders/{order['id']}", headers=auth_tokens["waiter"]).json()
    assert ord_fetched["status"] == "COMPLETED"


def test_28_reject_refund_exceeding_paid_amount(auth_tokens):
    """28. Reject refund exceeding paid amount."""
    # Find paid payment
    item = client.get("/api/menu-items/available", headers=auth_tokens["waiter"]).json()[0]
    order = client.post("/api/orders", json={"order_type": "TAKEAWAY", "created_by": "WAITER"}, headers=auth_tokens["waiter"]).json()
    client.post(f"/api/orders/{order['id']}/items", json={"menu_item_id": item["id"], "quantity": 1}, headers=auth_tokens["waiter"])
    inv = client.post(f"/api/orders/{order['id']}/invoice", headers=auth_tokens["cashier"]).json()

    pay = client.post(
        "/api/payments",
        json={"invoice_id": inv["id"], "amount": str(inv["total_amount"]), "payment_method": "CASH"},
        headers=auth_tokens["cashier"],
    ).json()

    paid_amt = Decimal(str(pay["amount"]))
    excessive_refund = paid_amt + Decimal("1000.00")

    res = client.post(
        "/api/refunds",
        json={
            "payment_id": pay["id"],
            "order_id": order["id"],
            "requested_amount": str(excessive_refund),
            "reason": "Excessive refund request",
        },
        headers=auth_tokens["cashier"],
    )
    assert res.status_code in [400, 422]


# ==============================================================================
# MONGODB LOGS & EVENTS TESTS (29 - 30)
# ==============================================================================

def test_29_store_order_activity_log(auth_tokens):
    """29. Store order activity log in MongoDB."""
    order = client.post("/api/orders", json={"order_type": "TAKEAWAY", "created_by": "WAITER"}, headers=auth_tokens["waiter"]).json()
    logs = client.get(f"/api/activity-logs/order/{order['id']}", headers=auth_tokens["admin"]).json()
    assert len(logs) >= 1
    assert any(log["action"] == "ORDER_CREATED" for log in logs)


def test_30_store_kitchen_status_change_event(auth_tokens):
    """30. Store kitchen status change event in MongoDB."""
    item = client.get("/api/menu-items/available", headers=auth_tokens["waiter"]).json()[0]
    order = client.post("/api/orders", json={"order_type": "TAKEAWAY", "created_by": "WAITER"}, headers=auth_tokens["waiter"]).json()
    client.post(f"/api/orders/{order['id']}/items", json={"menu_item_id": item["id"], "quantity": 1}, headers=auth_tokens["waiter"])
    client.post(f"/api/orders/{order['id']}/confirm", headers=auth_tokens["waiter"])

    tickets = client.get(f"/api/kitchen/tickets", headers=auth_tokens["chef"]).json()
    ticket = next(t for t in tickets if t["order_id"] == order["id"])

    # Update status
    client.post(f"/api/kitchen/tickets/{ticket['id']}/start", headers=auth_tokens["chef"])

    events = client.get(f"/api/kitchen-events/order/{order['id']}", headers=auth_tokens["chef"]).json()
    assert len(events) >= 1
    assert any(ev.get("new_status") == "PREPARING" or ev.get("event") == "STATUS_CHANGED" for ev in events)


# ==============================================================================
# ADDITIONAL ADVANCED TESTS (31 - 35)
# ==============================================================================

def test_31_table_management_occupy_and_release(auth_tokens):
    """31. Table occupation & duplicate assignment prevention."""
    table_num = f"T-TEST-{int(now_utc().timestamp()) % 10000}"
    table_res = client.post(
        "/api/tables",
        json={"table_number": table_num, "capacity": 4, "location": "Main Dining"},
        headers=auth_tokens["admin"],
    )
    assert table_res.status_code == 201
    table_id = table_res.json()["id"]

    # Create dine-in order on table
    order1 = client.post(
        "/api/orders",
        json={"table_id": table_id, "order_type": "DINE_IN", "created_by": "WAITER"},
        headers=auth_tokens["waiter"],
    ).json()

    item = client.get("/api/menu-items/available", headers=auth_tokens["waiter"]).json()[0]
    client.post(f"/api/orders/{order1['id']}/items", json={"menu_item_id": item["id"], "quantity": 1}, headers=auth_tokens["waiter"])
    client.post(f"/api/orders/{order1['id']}/confirm", headers=auth_tokens["waiter"])

    # Table is now OCCUPIED
    tbl = client.get(f"/api/tables/{table_id}", headers=auth_tokens["waiter"]).json()
    assert tbl["status"] == "OCCUPIED"

    # Attempting to assign another active dine-in order to occupied table must fail
    res2 = client.post(
        "/api/orders",
        json={"table_id": table_id, "order_type": "DINE_IN", "created_by": "WAITER"},
        headers=auth_tokens["waiter"],
    )
    assert res2.status_code in [400, 422]


def test_32_reservation_overlap_and_capacity_check(auth_tokens):
    """32. Reservation overlap rejection & capacity check."""
    # Create dedicated table to avoid collision with pre-existing reservations
    tbl_res = client.post(
        "/api/tables",
        json={"table_number": f"TR-{uuid.uuid4().hex[:6]}", "capacity": 4, "location": "MAIN_HALL"},
        headers=auth_tokens["admin"],
    )
    tbl = tbl_res.json()

    test_date = f"2028-{(int(uuid.uuid4().hex[:2], 16) % 12) + 1:02d}-{(int(uuid.uuid4().hex[2:4], 16) % 25) + 1:02d}"

    # Reject exceeding capacity
    exc_res = client.post(
        "/api/reservations",
        json={
            "table_id": tbl["id"],
            "reservation_date": test_date,
            "start_time": "19:00",
            "end_time": "21:00",
            "guest_count": tbl["capacity"] + 20,
        },
        headers=auth_tokens["waiter"],
    )
    assert exc_res.status_code in [400, 422]

    # Valid reservation
    r1 = client.post(
        "/api/reservations",
        json={
            "table_id": tbl["id"],
            "reservation_date": test_date,
            "start_time": "19:00",
            "end_time": "21:00",
            "guest_count": 2,
        },
        headers=auth_tokens["waiter"],
    )
    assert r1.status_code == 201

    # Overlapping reservation on same table and date
    r2 = client.post(
        "/api/reservations",
        json={
            "table_id": tbl["id"],
            "reservation_date": test_date,
            "start_time": "20:00",
            "end_time": "22:00",
            "guest_count": 2,
        },
        headers=auth_tokens["waiter"],
    )
    assert r2.status_code in [400, 422]


def test_33_customer_feedback_validation_and_duplicate_prevention(auth_tokens):
    """33. Customer feedback validation and duplicate prevention."""
    # Create and complete an order
    item = client.get("/api/menu-items/available", headers=auth_tokens["waiter"]).json()[0]
    order = client.post("/api/orders", json={"order_type": "TAKEAWAY", "created_by": "WAITER"}, headers=auth_tokens["waiter"]).json()
    client.post(f"/api/orders/{order['id']}/items", json={"menu_item_id": item["id"], "quantity": 1}, headers=auth_tokens["waiter"])
    inv = client.post(f"/api/orders/{order['id']}/invoice", headers=auth_tokens["cashier"]).json()
    client.post("/api/payments", json={"invoice_id": inv["id"], "amount": str(inv["total_amount"]), "payment_method": "CASH"}, headers=auth_tokens["cashier"])

    # Feedback with invalid rating (> 5)
    bad_res = client.post(
        f"/api/orders/{order['id']}/feedback",
        json={"rating": 10, "comments": "Invalid rating"},
        headers=auth_tokens["waiter"],
    )
    assert bad_res.status_code in [400, 422]

    # Valid feedback
    fb1 = client.post(
        f"/api/orders/{order['id']}/feedback",
        json={"rating": 5, "food_rating": 5, "service_rating": 4, "comments": "Delicious!"},
        headers=auth_tokens["waiter"],
    )
    assert fb1.status_code == 201

    # Duplicate feedback for same order
    fb2 = client.post(
        f"/api/orders/{order['id']}/feedback",
        json={"rating": 4, "comments": "Duplicate feedback"},
        headers=auth_tokens["waiter"],
    )
    assert fb2.status_code in [400, 422]


def test_34_serving_capacity_report(auth_tokens):
    """34. Serving capacity estimation report."""
    res = client.get("/api/reports/serving-capacity", headers=auth_tokens["chef"])
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if data:
        assert "possible_servings" in data[0]


def test_35_daily_sales_report(auth_tokens):
    """35. Daily sales report."""
    res = client.get("/api/reports/daily-sales", headers=auth_tokens["manager"])
    assert res.status_code == 200
    data = res.json()
    assert "total_orders" in data
    assert "gross_sales" in data
    assert "net_sales" in data


def test_36_user_registration():
    """36. User self-registration and duplicate protection."""
    unique_email = f"staff_{uuid.uuid4().hex[:6]}@dineflow.com"
    pwd = "SecurePassword123!"

    # 1. Register successfully
    reg_res = client.post(
        "/api/auth/register",
        json={
            "name": "Chef Marco",
            "email": unique_email,
            "password": pwd,
            "role": "CHEF",
        },
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == unique_email
    assert reg_data["user"]["role"] == "CHEF"

    # 2. Duplicate registration should fail
    dup_res = client.post(
        "/api/auth/register",
        json={
            "name": "Chef Marco Clone",
            "email": unique_email,
            "password": pwd,
            "role": "CHEF",
        },
    )
    assert dup_res.status_code in [400, 422]


def test_37_auth_login_and_aliases():
    """37. Verify login aliases and authenticated token response."""
    unique_email = f"waiter_{uuid.uuid4().hex[:6]}@dineflow.com"
    pwd = "SecurePassword123!"

    # Register via alias
    reg = client.post("/api/register", json={"name": "Alice Waiter", "email": unique_email, "password": pwd, "role": "WAITER"})
    assert reg.status_code == 201

    # Login via /api/auth/login
    l1 = client.post("/api/auth/login", json={"email": unique_email, "password": pwd})
    assert l1.status_code == 200
    assert "access_token" in l1.json()

    # Login via /api/login alias
    l2 = client.post("/api/login", json={"email": unique_email, "password": pwd})
    assert l2.status_code == 200
    assert "access_token" in l2.json()

    # Verify invalid password rejected
    bad = client.post("/api/auth/login", json={"email": unique_email, "password": "WrongPassword!"})
    assert bad.status_code in [400, 401]

