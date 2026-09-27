"""
Table Management Service.
Handles Restaurant Tables, capacity, occupancy, and status transitions.
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.repositories.table_repository import TableRepository
from app.repositories.order_repository import OrderRepository
from app.models.entities import RestaurantTable as TableEntity
from app.services.common import to_object_id, now_utc, get_field, serialize_document, serialize_documents

table_repo = TableRepository()
order_repo = OrderRepository()


class RestaurantTableService:

    @staticmethod
    def create_table(data: Any) -> Dict[str, Any]:
        number = str(get_field(data, "table_number", ""))
        capacity = int(get_field(data, "capacity", 0))
        location = str(get_field(data, "location", "Ground Floor"))
        is_active = bool(get_field(data, "is_active", True))

        entity = TableEntity(
            table_number=number,
            capacity=capacity,
            location=location,
            status="AVAILABLE",
            is_active=is_active,
        )

        if table_repo.find_by_number(entity.table_number):
            raise ValueError(f"Table number '{entity.table_number}' already exists")

        doc = {
            "table_number": entity.table_number,
            "capacity": entity.capacity,
            "location": entity.location,
            "status": entity.status,
            "is_active": entity.is_active,
            "created_at": now_utc(),
        }
        return table_repo.insert(doc)

    @staticmethod
    def get_tables() -> List[Dict[str, Any]]:
        return table_repo.find_all(sort_field="table_number", sort_dir=1)

    @staticmethod
    def get_table(table_id: str) -> Dict[str, Any]:
        table = table_repo.find_by_id(table_id)
        if not table:
            raise ValueError("Table not found")
        return table

    @staticmethod
    def get_available_tables() -> List[Dict[str, Any]]:
        return table_repo.find_available()

    @staticmethod
    def update_table(table_id: str, data: Any) -> Dict[str, Any]:
        update_data = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.copy()

        if "capacity" in update_data and update_data["capacity"] is not None:
            if int(update_data["capacity"]) <= 0:
                raise ValueError("Table capacity must be positive")

        if "status" in update_data and update_data["status"]:
            if update_data["status"] not in TableEntity.VALID_STATUSES:
                raise ValueError(f"Invalid table status: {update_data['status']}")

        updated = table_repo.update(table_id, update_data)
        if not updated:
            raise ValueError("Table not found")
        return updated

    @staticmethod
    def update_status(table_id: str, status: str) -> Dict[str, Any]:
        status_upper = status.upper()
        if status_upper not in TableEntity.VALID_STATUSES:
            raise ValueError(f"Invalid table status: {status_upper}")

        table = RestaurantTableService.get_table(table_id)
        if not table["is_active"] and status_upper in ["AVAILABLE", "OCCUPIED", "RESERVED"]:
            raise ValueError("Cannot set active status on inactive table")

        updated = table_repo.set_status(table_id, status_upper)
        return updated

    @staticmethod
    def occupy_table(table_id: str, order_id: Optional[str] = None) -> Dict[str, Any]:
        table = RestaurantTableService.get_table(table_id)
        if not table["is_active"]:
            raise ValueError("Table is inactive")
        if table["status"] == "OCCUPIED":
            # Check if assigned to another active order
            active_orders = order_repo.find_active_by_table(table_id)
            if active_orders:
                if order_id and any(str(o["id"]) != str(order_id) for o in active_orders):
                    raise ValueError(f"Table {table['table_number']} is already assigned to another active order")
                elif not order_id and len(active_orders) > 0:
                    raise ValueError(f"Table {table['table_number']} is already occupied")

        return table_repo.set_status(table_id, "OCCUPIED")

    @staticmethod
    def release_table(table_id: str) -> Dict[str, Any]:
        return table_repo.set_status(table_id, "AVAILABLE")
