"""
Seed script to create initial users with hashed passwords for all restaurant roles.
Roles: ADMIN, MANAGER, CHEF, WAITER, CASHIER
"""
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app.database.mongodb import users_collection
from app.services.service import hash_password, now_utc

SAMPLE_USERS = [
    {
        "name": "System Administrator",
        "email": "admin@dineflow.com",
        "password": "Password123!",
        "role": "ADMIN",
        "is_active": True,
    },
    {
        "name": "General Manager",
        "email": "manager@dineflow.com",
        "password": "Password123!",
        "role": "MANAGER",
        "is_active": True,
    },
    {
        "name": "Head Chef",
        "email": "chef@dineflow.com",
        "password": "Password123!",
        "role": "CHEF",
        "is_active": True,
    },
    {
        "name": "Floor Waiter",
        "email": "waiter@dineflow.com",
        "password": "Password123!",
        "role": "WAITER",
        "is_active": True,
    },
    {
        "name": "Billing Cashier",
        "email": "cashier@dineflow.com",
        "password": "Password123!",
        "role": "CASHIER",
        "is_active": True,
    },
]


def seed_users():
    print(">>> Seeding roles and default users...")
    for user_info in SAMPLE_USERS:
        email = user_info["email"].lower()
        existing = users_collection.find_one({"email": email})
        if existing:
            # Update password to ensure it is hashed with the new bcrypt helper
            users_collection.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "password": hash_password(user_info["password"]),
                        "role": user_info["role"],
                        "is_active": True,
                        "updated_at": now_utc(),
                    }
                }
            )
            print(f"  [INFO] User '{email}' ({user_info['role']}) already exists. Password updated.")
            continue

        doc = {
            "name": user_info["name"],
            "email": email,
            "password": hash_password(user_info["password"]),
            "role": user_info["role"],
            "is_active": user_info["is_active"],
            "created_at": now_utc(),
            "updated_at": now_utc(),
        }
        res = users_collection.insert_one(doc)
        print(f"  [SUCCESS] Created {user_info['role']} user: {email} (ID: {res.inserted_id})")

    print("\nSeeding completed successfully!")
    print("All accounts have password: Password123!")


if __name__ == "__main__":
    seed_users()
