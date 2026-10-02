"""
Supplier Management Service.
Handles vendor/supplier profiles, contacts, payment terms, and active catalogs.
"""

from typing import Any, Dict, List, Optional
from app.repositories.inventory_repository import SupplierRepository
from app.models.entities import Supplier as SupplierEntity
from app.services.common import to_object_id, now_utc, get_field

repo = SupplierRepository()


class SupplierService:

    @staticmethod
    def create_supplier(data: Any) -> Dict[str, Any]:
        name = get_field(data, "name")
        contact = get_field(data, "contact_number")
        email = get_field(data, "email")
        address = get_field(data, "address")
        tax_id = get_field(data, "tax_id_gst")
        payment_terms = get_field(data, "payment_terms", "Net 30")
        is_active = get_field(data, "is_active", True)

        entity = SupplierEntity(
            name=name,
            contact_number=contact,
            email=email,
            address=address,
            tax_id_gst=tax_id,
            is_active=is_active,
        )

        existing = repo.find_by_name(entity.name)
        if existing:
            raise ValueError(f"Supplier '{entity.name}' already exists")

        doc = {
            "name": entity.name,
            "contact_number": entity.contact_number,
            "email": entity.email,
            "address": entity.address,
            "tax_id_gst": entity.tax_id_gst,
            "payment_terms": payment_terms,
            "is_active": entity.is_active,
            "created_at": now_utc(),
            "updated_at": now_utc(),
        }

        created = repo.insert(doc)
        return created

    @staticmethod
    def get_suppliers() -> List[Dict[str, Any]]:
        return repo.find_all(sort_field="name", sort_dir=1)

    @staticmethod
    def get_active_suppliers() -> List[Dict[str, Any]]:
        return repo.find_active()

    @staticmethod
    def get_supplier(supplier_id: str) -> Dict[str, Any]:
        sup = repo.find_by_id(supplier_id)
        if not sup:
            raise ValueError("Supplier not found")
        return sup

    @staticmethod
    def update_supplier(supplier_id: str, data: Any) -> Dict[str, Any]:
        update_dict = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.copy()
        update_dict["updated_at"] = now_utc()
        updated = repo.update(supplier_id, update_dict)
        if not updated:
            raise ValueError("Supplier not found")
        return updated

    @staticmethod
    def delete_supplier(supplier_id: str) -> Dict[str, Any]:
        deleted = repo.delete(supplier_id)
        if not deleted:
            raise ValueError("Supplier not found")
        return {"message": "Supplier deleted successfully", "id": supplier_id}
