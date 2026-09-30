import urllib.request
import json

def e2e():
    # 1. Test Swagger UI & health
    docs = urllib.request.urlopen("http://127.0.0.1:8000/docs")
    assert docs.status == 200, "Swagger /docs unreachable"
    print("[PASS] Swagger UI (/docs) is live and returning HTTP 200")

    # 2. Test logins for all 5 roles
    roles = ["admin", "manager", "chef", "waiter", "cashier"]
    tokens = {}
    for r in roles:
        req = urllib.request.Request(
            "http://127.0.0.1:8000/auth/login",
            data=json.dumps({"email": f"{r}@dineflow.com", "password": "Password123!"}).encode(),
            headers={"Content-Type": "application/json"}
        )
        res = urllib.request.urlopen(req)
        tokens[r] = json.loads(res.read())["access_token"]
        print(f"[PASS] Logged in as {r.upper()}")

    # 3. Create category as Chef
    chef_headers = {"Authorization": f"Bearer {tokens['chef']}", "Content-Type": "application/json"}
    cat_payload = {"name": "E2E Chef Specials", "description": "Specially curated dishes"}
    req = urllib.request.Request("http://127.0.0.1:8000/api/menu/categories", data=json.dumps(cat_payload).encode(), headers=chef_headers)
    cat_res = json.loads(urllib.request.urlopen(req).read())
    cat_id = cat_res["id"]
    print(f"[PASS] Created Category: {cat_id} ({cat_res['name']})")

    # 4. Create dish as Waiter
    waiter_headers = {"Authorization": f"Bearer {tokens['waiter']}", "Content-Type": "application/json"}
    dish_payload = {
        "name": "E2E Kadhai Paneer",
        "category_id": cat_id,
        "price": 280.0,
        "preparation_time": 18,
        "is_vegetarian": True,
        "is_available": True,
        "description": "Fresh cottage cheese tossed with bell peppers and whole roasted coriander"
    }
    req = urllib.request.Request("http://127.0.0.1:8000/api/menu-items", data=json.dumps(dish_payload).encode(), headers=waiter_headers)
    dish_res = json.loads(urllib.request.urlopen(req).read())
    dish_id = dish_res["id"]
    print(f"[PASS] Waiter created dish: {dish_id} ({dish_res['name']})")

    # 5. Update dish as Cashier
    cashier_headers = {"Authorization": f"Bearer {tokens['cashier']}", "Content-Type": "application/json"}
    update_payload = {"price": 295.0, "description": "Updated description"}
    req = urllib.request.Request(f"http://127.0.0.1:8000/api/menu-items/{dish_id}", data=json.dumps(update_payload).encode(), headers=cashier_headers, method="PUT")
    up_res = json.loads(urllib.request.urlopen(req).read())
    print(f"[PASS] Cashier updated dish: new price {up_res['price']}")

    # 6. Delete dish as Admin
    admin_headers = {"Authorization": f"Bearer {tokens['admin']}", "Content-Type": "application/json"}
    req = urllib.request.Request(f"http://127.0.0.1:8000/api/menu-items/{dish_id}", headers=admin_headers, method="DELETE")
    del_dish_res = json.loads(urllib.request.urlopen(req).read())
    print(f"[PASS] Deleted dish: {del_dish_res}")

    # 7. Delete category as Admin
    req = urllib.request.Request(f"http://127.0.0.1:8000/api/menu/categories/{cat_id}", headers=admin_headers, method="DELETE")
    del_cat_res = json.loads(urllib.request.urlopen(req).read())
    print(f"[PASS] Deleted category: {del_cat_res}")

    print("=== ALL 7 E2E CRITICAL PATH TESTS PASSED PERFECTLY ===")

if __name__ == "__main__":
    e2e()
