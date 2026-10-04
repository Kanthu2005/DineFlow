import os
import certifi
from pymongo import MongoClient
from app.config.settings import settings
from app.database.indexes import create_indexes

def wipe_database(name: str, uri: str, db_name: str):
    print(f"\n==========================================")
    print(f"Connecting to {name}...")
    print(f"Database: {db_name}")
    print(f"==========================================")
    
    client_kwargs = {
        "serverSelectionTimeoutMS": 10000,
        "connectTimeoutMS": 10000,
        "retryWrites": True,
    }
    if uri.startswith("mongodb+srv://") or "tls=true" in uri.lower() or "ssl=true" in uri.lower():
        client_kwargs["tlsCAFile"] = certifi.where()

    client = MongoClient(uri, **client_kwargs)
    db = client[db_name]

    # Test connection
    client.admin.command("ping")
    print(f"Successfully connected to {name}.")

    collections = db.list_collection_names()
    print(f"Found {len(collections)} collections in {name}:")
    
    total_deleted = 0
    for col_name in sorted(collections):
        if col_name.startswith("system."):
            continue
        col = db[col_name]
        count = col.count_documents({})
        if count > 0:
            result = col.delete_many({})
            print(f"  - Deleted {result.deleted_count} documents from '{col_name}'")
            total_deleted += result.deleted_count
        else:
            print(f"  - '{col_name}' is already empty (0 documents)")

    # Ensure indexes are preserved/created
    try:
        create_indexes(db)
        print("Indexes verified.")
    except Exception as e:
        print(f"Index creation notice: {e}")

    # Verify zero documents remain
    print(f"\nVerification for {name}:")
    remaining_total = 0
    for col_name in db.list_collection_names():
        if col_name.startswith("system."):
            continue
        c = db[col_name].count_documents({})
        if c > 0:
            print(f"  WARNING: {col_name} still has {c} documents!")
            remaining_total += c
    
    if remaining_total == 0:
        print(f"ALL DATA WIPED! Total documents deleted from {name}: {total_deleted}")
    else:
        print(f"Total remaining documents: {remaining_total}")
    
    client.close()

if __name__ == "__main__":
    local_uri = settings.MONGO_URL or "mongodb://localhost:27017"
    atlas_uri = settings.ATLAS_URL or "mongodb+srv://Dineflow_db:ZNUImVl1go7GnUZm@cluster0.kbnyfeg.mongodb.net/?appName=Cluster0"
    db_name = settings.DATABASE_NAME or "restaurant_management"

    print("STARTING FULL DATABASE PURGE AS REQUESTED BY USER...")

    # 1. Wipe Local MongoDB
    try:
        wipe_database("Local MongoDB", local_uri, db_name)
    except Exception as e:
        print(f"Error wiping Local MongoDB: {e}")

    # 2. Wipe Atlas MongoDB
    try:
        wipe_database("Atlas MongoDB (Cloud)", atlas_uri, db_name)
    except Exception as e:
        print(f"Error wiping Atlas MongoDB: {e}")

    print("\n==========================================")
    print("Database purge process completed!")
    print("==========================================")
