"""
DineFlow - 20 Standard Tables Seeder
Seeds and maintains exactly 20 tables: T1 through T20.
Cleans up obsolete or temporary test tables so only T1..T20 exist.
"""

import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database.mongodb import restaurant_tables_collection
from app.services.common import now_utc

TABLES_20 = [
    # Main Dining Hall (T1 - T6)
    {"table_number": "T1", "capacity": 2, "location": "MAIN_HALL", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T2", "capacity": 2, "location": "MAIN_HALL", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T3", "capacity": 4, "location": "MAIN_HALL", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T4", "capacity": 4, "location": "MAIN_HALL", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T5", "capacity": 4, "location": "MAIN_HALL", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T6", "capacity": 4, "location": "MAIN_HALL", "status": "AVAILABLE", "is_active": True},

    # Family Dining Section (T7 - T11)
    {"table_number": "T7", "capacity": 6, "location": "FAMILY_SECTION", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T8", "capacity": 6, "location": "FAMILY_SECTION", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T9", "capacity": 6, "location": "FAMILY_SECTION", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T10", "capacity": 8, "location": "FAMILY_SECTION", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T11", "capacity": 8, "location": "FAMILY_SECTION", "status": "AVAILABLE", "is_active": True},

    # Open Terrace Garden (T12 - T16)
    {"table_number": "T12", "capacity": 2, "location": "TERRACE", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T13", "capacity": 2, "location": "TERRACE", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T14", "capacity": 4, "location": "TERRACE", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T15", "capacity": 4, "location": "TERRACE", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T16", "capacity": 6, "location": "TERRACE", "status": "AVAILABLE", "is_active": True},

    # VIP Executive Lounge (T17 - T20)
    {"table_number": "T17", "capacity": 4, "location": "VIP_LOUNGE", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T18", "capacity": 4, "location": "VIP_LOUNGE", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T19", "capacity": 6, "location": "VIP_LOUNGE", "status": "AVAILABLE", "is_active": True},
    {"table_number": "T20", "capacity": 8, "location": "VIP_LOUNGE", "status": "AVAILABLE", "is_active": True},
]

VALID_TABLE_NUMBERS = [t["table_number"] for t in TABLES_20]


def seed_20_tables(clean_obsolete: bool = True):
    """
    Ensures restaurant_tables_collection contains only the 20 standard tables T1 through T20.
    """
    print("==================================================")
    print("  DineFlow: Seeding 20 Standard Tables (T1 - T20) ")
    print("==================================================")

    # 1. Remove obsolete or test tables if requested
    if clean_obsolete:
        del_res = restaurant_tables_collection.delete_many({
            "table_number": {"$nin": VALID_TABLE_NUMBERS}
        })
        if del_res.deleted_count > 0:
            print(f"  [-] Removed {del_res.deleted_count} obsolete/test tables.")

    # 2. Upsert T1 through T20
    upserted_count = 0
    for tbl in TABLES_20:
        existing = restaurant_tables_collection.find_one({"table_number": tbl["table_number"]})
        if existing:
            restaurant_tables_collection.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "capacity": tbl["capacity"],
                        "location": tbl["location"],
                        "is_active": True,
                        "updated_at": now_utc(),
                    }
                }
            )
            print(f"  [OK] Table {tbl['table_number']} verified ({tbl['capacity']} seats, {tbl['location']})")
        else:
            doc = {
                **tbl,
                "created_at": now_utc(),
                "updated_at": now_utc(),
            }
            restaurant_tables_collection.insert_one(doc)
            upserted_count += 1
            print(f"  [+] Table {tbl['table_number']} created ({tbl['capacity']} seats, {tbl['location']})")

    total_count = restaurant_tables_collection.count_documents({})
    print(f"\n[DONE] Tables count in database: {total_count} (T1 to T20)")
    print("==================================================")
    return total_count


if __name__ == "__main__":
    seed_20_tables()
