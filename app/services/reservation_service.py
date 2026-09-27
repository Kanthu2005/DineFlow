"""
Reservation Management Service.
Handles customer table bookings, overlap detection, and capacity checks.
"""

from datetime import datetime, date, timezone
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.repositories.table_repository import TableRepository, ReservationRepository
from app.models.entities import Reservation as ReservationEntity
from app.services.common import to_object_id, now_utc, get_field, serialize_document, serialize_documents
from app.database.mongodb import customers_collection

table_repo = TableRepository()
res_repo = ReservationRepository()


class ReservationService:

    @staticmethod
    def _normalize_time(t: Any) -> str:
        s = str(t).strip()
        parts = s.split(":")
        if len(parts) == 2:
            return f"{int(parts[0]):02d}:{int(parts[1]):02d}:00"
        elif len(parts) >= 3:
            return f"{int(parts[0]):02d}:{int(parts[1]):02d}:{int(parts[2]):02d}"
        return s

    @staticmethod
    def create_reservation(data: Any) -> Dict[str, Any]:
        customer_id = get_field(data, "customer_id")
        table_id = get_field(data, "table_id")
        res_date = str(get_field(data, "reservation_date")).strip()
        start_time = ReservationService._normalize_time(get_field(data, "start_time"))
        end_time = ReservationService._normalize_time(get_field(data, "end_time"))
        guest_count = int(get_field(data, "guest_count", 0))
        contact = get_field(data, "contact_number")

        # 1. Customer verification
        if customer_id:
            customer = customers_collection.find_one({"_id": to_object_id(customer_id)})
            if not customer:
                raise ValueError("Customer not found")

        # 2. Table verification
        table = table_repo.find_by_id(table_id)
        if not table:
            raise ValueError("Table not found")
        if not table["is_active"]:
            raise ValueError("Cannot reserve an inactive table")

        # 3. Capacity check
        if guest_count <= 0:
            raise ValueError("Guest count must be greater than zero")
        if guest_count > table["capacity"]:
            raise ValueError(
                f"Guest count ({guest_count}) exceeds table capacity ({table['capacity']})"
            )

        # 4. Start / End time validation
        if start_time >= end_time:
            raise ValueError("start_time must be earlier than end_time")

        # 5. Overlap detection: new_start < existing_end and new_end > existing_start
        overlapping = res_repo.find_overlapping(table_id, res_date, start_time, end_time)
        if overlapping:
            raise ValueError(
                f"Table is already reserved for this time slot ({res_date} {start_time}-{end_time})"
            )

        doc = {
            "customer_id": to_object_id(customer_id) if customer_id else None,
            "table_id": to_object_id(table_id),
            "reservation_date": res_date,
            "start_time": start_time,
            "end_time": end_time,
            "guest_count": guest_count,
            "status": "REQUESTED",
            "contact_number": contact,
            "created_at": now_utc(),
        }

        return res_repo.insert(doc)

    @staticmethod
    def get_reservations() -> List[Dict[str, Any]]:
        return res_repo.find_all(sort_field="created_at", sort_dir=-1)

    @staticmethod
    def get_reservation(reservation_id: str) -> Dict[str, Any]:
        res = res_repo.find_by_id(reservation_id)
        if not res:
            raise ValueError("Reservation not found")
        return res

    @staticmethod
    def get_by_customer(customer_id: str) -> List[Dict[str, Any]]:
        return res_repo.find_by_customer(customer_id)

    @staticmethod
    def get_by_table(table_id: str) -> List[Dict[str, Any]]:
        return res_repo.find_by_table(table_id)

    @staticmethod
    def update_reservation(reservation_id: str, data: Any) -> Dict[str, Any]:
        update_data = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.copy()

        current = ReservationService.get_reservation(reservation_id)
        table_id = update_data.get("table_id") or current["table_id"]
        res_date = str(update_data.get("reservation_date") or current["reservation_date"]).strip()
        start_time = ReservationService._normalize_time(update_data.get("start_time") or current["start_time"])
        end_time = ReservationService._normalize_time(update_data.get("end_time") or current["end_time"])

        if start_time >= end_time:
            raise ValueError("start_time must be earlier than end_time")

        overlapping = res_repo.find_overlapping(table_id, res_date, start_time, end_time, exclude_id=reservation_id)
        if overlapping:
            raise ValueError("Table already reserved for this time slot")

        update_data["start_time"] = start_time
        update_data["end_time"] = end_time
        updated = res_repo.update(reservation_id, update_data)
        return updated

    @staticmethod
    def confirm_reservation(reservation_id: str) -> Dict[str, Any]:
        res = ReservationService.get_reservation(reservation_id)
        if res["status"] in ["CANCELLED", "COMPLETED", "NO_SHOW"]:
            raise ValueError(f"Cannot confirm reservation in status {res['status']}")
        return res_repo.update(reservation_id, {"status": "CONFIRMED"})

    @staticmethod
    def cancel_reservation(reservation_id: str) -> Dict[str, Any]:
        res = ReservationService.get_reservation(reservation_id)
        return res_repo.update(reservation_id, {"status": "CANCELLED"})
