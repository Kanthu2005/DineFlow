import os
import certifi
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from app.config.settings import settings


def _build_client(uri: str, timeout_ms: int = 5000) -> MongoClient:
    """Create a MongoClient with appropriate pooling and TLS settings."""
    clean_uri = uri.strip()
    client_kwargs = {
        "serverSelectionTimeoutMS": timeout_ms,
        "connectTimeoutMS": timeout_ms,
        "socketTimeoutMS": 10000,
        "maxPoolSize": 50,
        "minPoolSize": 1,
        "retryWrites": True,
    }

    if (
        clean_uri.startswith("mongodb+srv://")
        or "tls=true" in clean_uri.lower()
        or "ssl=true" in clean_uri.lower()
    ):
        client_kwargs["tlsCAFile"] = certifi.where()

    return MongoClient(clean_uri, **client_kwargs)


def _create_mongo_client() -> MongoClient:
    """Resolve the best MongoDB connection (Atlas on Vercel/cloud, or local with Atlas fallback)."""
    mongo_url = (settings.MONGO_URL or "").strip()
    atlas_url = (settings.ATLAS_URL or os.getenv("MONGODB_URI") or "").strip()
    is_vercel = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV"))
    is_local_uri = "localhost" in mongo_url or "127.0.0.1" in mongo_url or not mongo_url

    # On Vercel, localhost does not exist — always prefer ATLAS_URL or non-local MONGO_URL
    if is_vercel:
        target_uri = atlas_url if (is_local_uri and atlas_url) else (mongo_url or atlas_url)
        return _build_client(target_uri or "mongodb://localhost:27017")

    # If MONGO_URL is already set to an Atlas / remote URI, use it directly
    if not is_local_uri:
        return _build_client(mongo_url)

    # Local environment: if local MongoDB is running, use it; otherwise seamlessly fall back to ATLAS_URL
    local_client = _build_client(mongo_url or "mongodb://localhost:27017", timeout_ms=2000)
    if atlas_url:
        try:
            local_client.admin.command("ping")
            return _build_client(mongo_url or "mongodb://localhost:27017", timeout_ms=5000)
        except Exception:
            local_client.close()
            return _build_client(atlas_url, timeout_ms=5000)

    return _build_client(mongo_url or "mongodb://localhost:27017", timeout_ms=5000)


client: MongoClient = _create_mongo_client()
db = client[settings.DATABASE_NAME]

# Collections for DineFlow data models
users_collection = db["users"]
customers_collection = db["customers"]
menu_categories_collection = db["menu_categories"]
menu_items_collection = db["menu_items"]
ingredients_collection = db["ingredients"]
recipes_collection = db["recipes"]
restaurant_tables_collection = db["restaurant_tables"]
reservations_collection = db["reservations"]
orders_collection = db["orders"]
order_items_collection = db["order_items"]
kitchen_tickets_collection = db["kitchen_tickets"]
kitchen_ticket_items_collection = db["kitchen_ticket_items"]
staff_assignments_collection = db["staff_assignments"]
stock_movements_collection = db["stock_movements"]
invoices_collection = db["invoices"]
payments_collection = db["payments"]
refunds_collection = db["refunds"]
order_activity_logs_collection = db["order_activity_logs"]
kitchen_events_collection = db["kitchen_events"]
customer_feedback_collection = db["customer_feedback"]


def get_database():
    """Return the active MongoDB database instance."""
    return db


def ping_database() -> bool:
    """Verify connectivity to the MongoDB server."""
    try:
        client.admin.command("ping")
        return True
    except PyMongoError:
        return False


def close_database() -> None:
    """Cleanly close the MongoDB client connection."""
    client.close()