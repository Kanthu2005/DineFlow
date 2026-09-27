from bson import ObjectId
from app.database.mongodb import users_collection
from app.services.common import (
    now_utc,
    to_object_id,
    serialize_user_document,
    serialize_user_documents,
)
from app.services.auth_service import hash_password, verify_password, AuthService


class UserService:

    @staticmethod
    def create_user(data):
        email = data.email.lower()
        if users_collection.find_one({"email": email}):
            raise ValueError("Email already exists")

        role = getattr(data, "role", "WAITER") or "WAITER"

        user = {
            "name": data.name,
            "email": email,
            "password": hash_password(data.password),
            "role": role.upper() if isinstance(role, str) else str(role),
            "is_active": True,
            "created_at": now_utc(),
        }

        result = users_collection.insert_one(user)
        user["_id"] = result.inserted_id

        return serialize_user_document(user)

    @staticmethod
    def get_user(user_id):
        user = users_collection.find_one({"_id": to_object_id(user_id)})
        if not user:
            raise ValueError("User not found")
        return serialize_user_document(user)

    @staticmethod
    def get_users():
        users = users_collection.find().sort("created_at", -1)
        return serialize_user_documents(users)

    @staticmethod
    def update_user(user_id, data):
        update_data = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.copy()
        if not update_data:
            raise ValueError("No data to update")

        if "email" in update_data and update_data["email"]:
            update_data["email"] = update_data["email"].lower()

        if "password" in update_data and update_data["password"]:
            update_data["password"] = hash_password(update_data["password"])

        if "role" in update_data and update_data["role"]:
            update_data["role"] = update_data["role"].upper()

        update_data["updated_at"] = now_utc()

        result = users_collection.update_one(
            {"_id": to_object_id(user_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            raise ValueError("User not found")

        return UserService.get_user(user_id)

    @staticmethod
    def delete_user(user_id):
        result = users_collection.delete_one({"_id": to_object_id(user_id)})
        if result.deleted_count == 0:
            raise ValueError("User not found")
        return {"message": "User deleted successfully"}

    @staticmethod
    def authenticate(email: str, password: str):
        return AuthService.authenticate(email, password)

    @staticmethod
    def login(email: str, password: str):
        return AuthService.login(email, password)

    @staticmethod
    def get_current_user_from_token(token: str):
        return AuthService.get_current_user_from_token(token)


#customerservice...
