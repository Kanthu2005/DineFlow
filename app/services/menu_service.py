"""
Menu Management Service.
Handles Menu Categories and Menu Items with OOP domain entity validation.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.repositories.menu_repository import MenuRepository
from app.models.entities import MenuItem as MenuItemEntity
from app.services.common import to_object_id, decimal128, now_utc, get_field, serialize_document, serialize_documents

menu_repo = MenuRepository()


class MenuCategoryService:

    @staticmethod
    def create_category(data: Any) -> Dict[str, Any]:
        name = str(get_field(data, "name", "")).strip()
        description = get_field(data, "description")

        if not name:
            raise ValueError("Category name cannot be empty")

        existing = menu_repo.find_category_by_name(name)
        if existing:
            return existing

        doc = {
            "name": name,
            "description": description,
            "created_at": now_utc(),
        }
        return menu_repo.create_category(doc)

    @staticmethod
    def get_categories() -> List[Dict[str, Any]]:
        return menu_repo.find_all_categories()

    @staticmethod
    def get_category(category_id: str) -> Dict[str, Any]:
        cat = menu_repo.find_category_by_id(category_id)
        if not cat:
            raise ValueError("Category not found")
        return cat

    @staticmethod
    def update_category(category_id: str, data: Any) -> Dict[str, Any]:
        update_data = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.copy()
        if "name" in update_data:
            update_data["name"] = update_data["name"].strip()
            existing = menu_repo.find_category_by_name(update_data["name"])
            if existing and str(existing.get("id")) != str(category_id):
                raise ValueError(f"Category '{update_data['name']}' already exists")

        cat = menu_repo.update_category(category_id, update_data)
        if not cat:
            raise ValueError("Category not found")
        return cat

    @staticmethod
    def delete_category(category_id: str) -> Dict[str, Any]:
        cat = menu_repo.find_category_by_id(category_id)
        if not cat:
            raise ValueError("Category not found")
        raw_id = cat.get("id") or cat.get("_id")
        menu_repo.delete_category(raw_id)
        return {"message": f"Category '{cat['name']}' deleted successfully"}


class MenuItemService:

    @staticmethod
    def create_item(data: Any) -> Dict[str, Any]:
        name = str(get_field(data, "name", "")).strip()
        price = get_field(data, "price")
        prep_time = get_field(data, "preparation_time")
        cat_id = get_field(data, "category_id")
        desc = get_field(data, "description")
        is_avail = get_field(data, "is_available", True)
        is_veg = get_field(data, "is_vegetarian", False)
        img_url = get_field(data, "image_url")
        if img_url is not None:
            img_url = str(img_url).strip() or None

        # Domain Entity validation: rejects negative price, zero/neg prep time
        entity = MenuItemEntity(
            name=name,
            price=price,
            preparation_time=prep_time,
            category_id=cat_id,
            description=desc,
            is_available=is_avail,
            is_vegetarian=is_veg,
            image_url=img_url,
        )

        category = menu_repo.find_category_by_id(entity.category_id)
        if not category:
            # Fallback to name search or auto-create to never drop user dish creations
            category = menu_repo.find_category_by_name(str(entity.category_id))
            if not category:
                category = MenuCategoryService.create_category({"name": str(entity.category_id)})

        target_cat_id = category.get("id") or category.get("_id")
        cat_oid = ObjectId(str(target_cat_id)) if ObjectId.is_valid(str(target_cat_id)) else str(target_cat_id)

        doc = {
            "name": entity.name,
            "description": entity.description,
            "category_id": cat_oid,
            "price": decimal128(entity.price),
            "preparation_time": entity.preparation_time,
            "is_available": entity.is_available,
            "is_vegetarian": entity.is_vegetarian,
            "image_url": entity.image_url,
            "created_at": now_utc(),
        }
        return menu_repo.insert(doc)

    @staticmethod
    def get_items() -> List[Dict[str, Any]]:
        return menu_repo.find_all(sort_field="name", sort_dir=1)

    @staticmethod
    def get_item(item_id: str) -> Dict[str, Any]:
        item = menu_repo.find_by_id(item_id)
        if not item:
            raise ValueError("Menu item not found")
        return item

    @staticmethod
    def get_available_items() -> List[Dict[str, Any]]:
        return menu_repo.find_available()

    @staticmethod
    def get_items_by_category(category_id: str) -> List[Dict[str, Any]]:
        return menu_repo.find_by_category(category_id)

    @staticmethod
    def search_items(query: str) -> List[Dict[str, Any]]:
        if not query:
            return MenuItemService.get_items()
        return menu_repo.search(query.strip())

    @staticmethod
    def update_item(item_id: str, data: Any) -> Dict[str, Any]:
        update_data = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.copy()

        if "price" in update_data and update_data["price"] is not None:
            dec_price = Decimal(str(update_data["price"]))
            if dec_price < 0:
                raise ValueError("Price cannot be negative")
            update_data["price"] = decimal128(dec_price)

        if "preparation_time" in update_data and update_data["preparation_time"] is not None:
            if int(update_data["preparation_time"]) <= 0:
                raise ValueError("Preparation time must be greater than zero")

        if "category_id" in update_data and update_data["category_id"]:
            cat = menu_repo.find_category_by_id(update_data["category_id"])
            if not cat:
                raise ValueError("Category not found")
            update_data["category_id"] = to_object_id(update_data["category_id"])

        updated = menu_repo.update(item_id, update_data)
        if not updated:
            raise ValueError("Menu item not found")
        return updated

    @staticmethod
    def update_availability(item_id: str, is_available: bool) -> Dict[str, Any]:
        updated = menu_repo.update(item_id, {"is_available": bool(is_available)})
        if not updated:
            raise ValueError("Menu item not found")
        return updated

    @staticmethod
    def delete_item(item_id: str) -> Dict[str, Any]:
        existing = menu_repo.find_by_id(item_id)
        if not existing:
            raise ValueError("Menu item not found")
        menu_repo.delete(item_id)
        return {"message": f"Menu item '{existing['name']}' deleted successfully"}
