import urllib.request
import json
import uuid

base_url = 'http://127.0.0.1:8000/api'

def run_e2e():
    # 1. Login
    req = urllib.request.Request(
        f'{base_url}/auth/login',
        data=json.dumps({'email': 'admin@dineflow.com', 'password': 'Password123!'}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        token = json.loads(resp.read().decode())['access_token']
    print("1. Login Success! Token length:", len(token))

    # 2. Get Categories
    req = urllib.request.Request(
        f'{base_url}/menu/categories',
        headers={'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(req) as resp:
        cats = json.loads(resp.read().decode())
    print(f"2. Found {len(cats)} categories")
    cat_id = cats[0]['id'] if cats else None

    # 3. Create a New Category test
    cat_test_name = f'Tandoori & Grills {uuid.uuid4().hex[:6]}'
    req = urllib.request.Request(
        f'{base_url}/menu/categories',
        data=json.dumps({'name': cat_test_name}).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(req) as resp:
        new_cat = json.loads(resp.read().decode())
    print("3. Category created/retrieved:", new_cat['name'], new_cat['id'])
    target_cat_id = new_cat['id']

    # 4. Create Dish
    dish_payload = {
        'name': 'Golden Malai Tikka',
        'category_id': target_cat_id,
        'price': 299.00,
        'preparation_time': 18,
        'is_vegetarian': False,
        'is_available': True,
        'description': 'Mouth melting chargrilled chicken with cream and mild cardamom',
        'image_url': 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=600'
    }
    req = urllib.request.Request(
        f'{base_url}/menu/items',
        data=json.dumps(dish_payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(req) as resp:
        dish = json.loads(resp.read().decode())
    dish_id = dish['id']
    print(f"4. Dish created successfully: {dish['name']} (ID: {dish_id})")

    # 5. Delete Dish
    req = urllib.request.Request(
        f'{base_url}/menu/items/{dish_id}',
        headers={'Authorization': f'Bearer {token}'},
        method='DELETE'
    )
    with urllib.request.urlopen(req) as resp:
        del_dish_res = json.loads(resp.read().decode())
    print("5. Dish deleted successfully:", del_dish_res)

    # 6. Delete Category
    req = urllib.request.Request(
        f'{base_url}/menu/categories/{target_cat_id}',
        headers={'Authorization': f'Bearer {token}'},
        method='DELETE'
    )
    with urllib.request.urlopen(req) as resp:
        del_cat_res = json.loads(resp.read().decode())
    print("6. Category deleted successfully:", del_cat_res)

    print("\nALL MENU CRUD VERIFICATIONS PASSED 100%!")


if __name__ == '__main__':
    run_e2e()

