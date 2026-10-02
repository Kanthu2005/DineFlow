"""
Menu Management Service.
Handles Menu Categories, Subcategories, and Menu Items with OOP domain entity validation,
safe deletion, hierarchical associations, price calculations, and statistics.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.repositories.menu_repository import MenuRepository
from app.models.entities import MenuItem as MenuItemEntity
from app.services.common import to_object_id, decimal128, now_utc, get_field, serialize_document, serialize_documents

menu_repo = MenuRepository()


# =============================================================================
# Category Service
# =============================================================================

class MenuCategoryService:

    @staticmethod
    def create_category(data: Any) -> Dict[str, Any]:
        name = str(get_field(data, "name", "")).strip()
        description = get_field(data, "description")
        food_type = get_field(data, "food_type")
        image_url = get_field(data, "image_url")
        is_active = get_field(data, "is_active", True)
        display_order = get_field(data, "display_order", 0)

        if not name:
            raise ValueError("Category name cannot be empty")

        existing = menu_repo.find_category_by_name(name)
        if existing:
            # If exists and caller wants to ensure it, return or raise error
            raise ValueError(f"Category '{name}' already exists")

        doc = {
            "name": name,
            "description": description,
            "food_type": food_type,
            "image_url": image_url,
            "is_active": bool(is_active),
            "display_order": int(display_order or 0),
            "created_at": now_utc(),
            "updated_at": now_utc(),
        }
        return menu_repo.create_category(doc)

    @staticmethod
    def get_categories(active_only: bool = False) -> List[Dict[str, Any]]:
        return menu_repo.find_all_categories(active_only=active_only)

    @staticmethod
    def get_category(category_id: str) -> Dict[str, Any]:
        cat = menu_repo.find_category_by_id(category_id)
        if not cat:
            raise ValueError("Category not found")
        return cat

    @staticmethod
    def update_category(category_id: str, data: Any) -> Dict[str, Any]:
        update_data = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.copy()
        
        target = menu_repo.find_category_by_id(category_id)
        if not target:
            raise ValueError("Category not found")

        if "name" in update_data and update_data["name"] is not None:
            update_data["name"] = str(update_data["name"]).strip()
            if not update_data["name"]:
                raise ValueError("Category name cannot be empty")
            existing = menu_repo.find_category_by_name(update_data["name"])
            if existing and str(existing.get("id")) != str(target.get("id")):
                raise ValueError(f"Category '{update_data['name']}' already exists")

        if "display_order" in update_data and update_data["display_order"] is not None:
            update_data["display_order"] = int(update_data["display_order"])

        update_data["updated_at"] = now_utc()
        cat = menu_repo.update_category(category_id, update_data)
        if not cat:
            raise ValueError("Category not found")

        # Sync category_name on items and subcategories if name changed
        if "name" in update_data:
            cat_raw_id = target.get("id") or target.get("_id")
            cat_oid = ObjectId(str(cat_raw_id)) if ObjectId.is_valid(str(cat_raw_id)) else cat_raw_id
            keys = [cat_raw_id, str(cat_raw_id), cat_oid]
            menu_repo.collection.update_many(
                {"category_id": {"$in": keys}},
                {"$set": {"category_name": update_data["name"]}}
            )
            menu_repo.subcategories_col.update_many(
                {"category_id": {"$in": keys}},
                {"$set": {"category_name": update_data["name"]}}
            )

        return cat

    @staticmethod
    def delete_category(category_id: str) -> Dict[str, Any]:
        cat = menu_repo.find_category_by_id(category_id)
        if not cat:
            raise ValueError("Category not found")
        raw_id = cat.get("id") or cat.get("_id") or category_id
        oid = ObjectId(str(raw_id)) if ObjectId.is_valid(str(raw_id)) else raw_id
        keys = [oid, str(raw_id), raw_id]

        # Reassign items and subcategories if another category exists
        fallback_cat = menu_repo.categories_col.find_one({"_id": {"$nin": [oid, str(raw_id)]}})
        if fallback_cat:
            fallback_id = fallback_cat["_id"]
            fallback_name = fallback_cat.get("name")
            menu_repo.collection.update_many(
                {"category_id": {"$in": keys}},
                {"$set": {"category_id": fallback_id, "category_name": fallback_name}}
            )
            menu_repo.subcategories_col.update_many(
                {"category_id": {"$in": keys}},
                {"$set": {"category_id": fallback_id, "category_name": fallback_name}}
            )

        deleted = menu_repo.delete_category(raw_id)
        if not deleted:
            raise ValueError(f"Could not delete category '{cat['name']}'")
        return {"message": f"Category '{cat['name']}' deleted successfully"}


# =============================================================================
# Subcategory Service
# =============================================================================

class MenuSubcategoryService:

    @staticmethod
    def create_subcategory(data: Any) -> Dict[str, Any]:
        name = str(get_field(data, "name", "")).strip()
        cat_id = get_field(data, "category_id")
        description = get_field(data, "description")
        is_active = get_field(data, "is_active", True)
        display_order = get_field(data, "display_order", 0)

        if not name:
            raise ValueError("Subcategory name cannot be empty")
        if not cat_id:
            raise ValueError("A subcategory must belong to a valid category")

        category = menu_repo.find_category_by_id(str(cat_id))
        if not category:
            category = menu_repo.find_category_by_name(str(cat_id))
        if not category:
            raise ValueError(f"Parent category '{cat_id}' does not exist")

        target_cat_id = str(category.get("id") or category.get("_id"))
        cat_oid = ObjectId(target_cat_id) if ObjectId.is_valid(target_cat_id) else target_cat_id

        # Check duplicate subcategory name under the same parent category
        existing = menu_repo.find_subcategory_by_name(target_cat_id, name)
        if existing:
            raise ValueError(f"Subcategory '{name}' already exists in category '{category.get('name')}'")

        doc = {
            "name": name,
            "category_id": cat_oid,
            "category_name": category.get("name"),
            "description": description,
            "is_active": bool(is_active),
            "display_order": int(display_order or 0),
            "created_at": now_utc(),
            "updated_at": now_utc(),
        }
        res = menu_repo.create_subcategory(doc)
        res["category_name"] = category.get("name")
        return res

    @staticmethod
    def get_subcategories(category_id: Optional[str] = None, active_only: bool = False) -> List[Dict[str, Any]]:
        if category_id:
            subcats = menu_repo.find_subcategories_by_category(category_id, active_only=active_only)
        else:
            subcats = menu_repo.find_all_subcategories(active_only=active_only)

        categories = {str(c["id"]): c["name"] for c in menu_repo.find_all_categories()}
        for s in subcats:
            cid = str(s.get("category_id"))
            if not s.get("category_name") and cid in categories:
                s["category_name"] = categories[cid]
        return subcats

    @staticmethod
    def get_subcategory(subcategory_id: str) -> Dict[str, Any]:
        subcat = menu_repo.find_subcategory_by_id(subcategory_id)
        if not subcat:
            raise ValueError("Subcategory not found")
        if not subcat.get("category_name") and subcat.get("category_id"):
            cat = menu_repo.find_category_by_id(str(subcat["category_id"]))
            if cat:
                subcat["category_name"] = cat.get("name")
        return subcat

    @staticmethod
    def update_subcategory(subcategory_id: str, data: Any) -> Dict[str, Any]:
        update_data = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.copy()

        target = menu_repo.find_subcategory_by_id(subcategory_id)
        if not target:
            raise ValueError("Subcategory not found")

        curr_cat_id = str(target.get("category_id"))

        if "category_id" in update_data and update_data["category_id"]:
            new_cat = menu_repo.find_category_by_id(str(update_data["category_id"]))
            if not new_cat:
                new_cat = menu_repo.find_category_by_name(str(update_data["category_id"]))
            if not new_cat:
                raise ValueError("Target parent category does not exist")
            target_cat_id = str(new_cat.get("id") or new_cat.get("_id"))
            update_data["category_id"] = ObjectId(target_cat_id) if ObjectId.is_valid(target_cat_id) else target_cat_id
            update_data["category_name"] = new_cat.get("name")
            curr_cat_id = target_cat_id

        if "name" in update_data and update_data["name"] is not None:
            update_data["name"] = str(update_data["name"]).strip()
            if not update_data["name"]:
                raise ValueError("Subcategory name cannot be empty")
            existing = menu_repo.find_subcategory_by_name(curr_cat_id, update_data["name"])
            if existing and str(existing.get("id")) != str(target.get("id")):
                raise ValueError(f"Subcategory '{update_data['name']}' already exists in this category")

        if "display_order" in update_data and update_data["display_order"] is not None:
            update_data["display_order"] = int(update_data["display_order"])

        update_data["updated_at"] = now_utc()
        subcat = menu_repo.update_subcategory(subcategory_id, update_data)
        if not subcat:
            raise ValueError("Subcategory not found")

        # Update subcategory_name on linked items if name changed
        if "name" in update_data:
            sub_raw_id = target.get("id") or target.get("_id")
            sub_oid = ObjectId(str(sub_raw_id)) if ObjectId.is_valid(str(sub_raw_id)) else sub_raw_id
            keys = [sub_raw_id, str(sub_raw_id), sub_oid]
            menu_repo.collection.update_many(
                {"subcategory_id": {"$in": keys}},
                {"$set": {"subcategory_name": update_data["name"]}}
            )

        return subcat

    @staticmethod
    def delete_subcategory(subcategory_id: str) -> Dict[str, Any]:
        subcat = menu_repo.find_subcategory_by_id(subcategory_id)
        if not subcat:
            raise ValueError("Subcategory not found")
        raw_id = subcat.get("id") or subcat.get("_id") or subcategory_id
        oid = ObjectId(str(raw_id)) if ObjectId.is_valid(str(raw_id)) else raw_id

        # Clear subcategory link on items belonging to this subcategory
        menu_repo.collection.update_many(
            {"subcategory_id": {"$in": [oid, str(raw_id), raw_id]}},
            {"$set": {"subcategory_id": None, "subcategory_name": None}}
        )

        deleted = menu_repo.delete_subcategory(raw_id)
        if not deleted:
            raise ValueError(f"Could not delete subcategory '{subcat['name']}'")
        return {"message": f"Subcategory '{subcat['name']}' deleted successfully"}


# =============================================================================
# Menu Item Service
# =============================================================================

class MenuItemService:

    @staticmethod
    def _enrich_item(item: Dict[str, Any], categories: Optional[Dict[str, str]] = None, subcategories: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        if not item:
            return item

        # Populate Category Name
        cid = str(item.get("category_id") or "")
        if not item.get("category_name"):
            if categories and cid in categories:
                item["category_name"] = categories[cid]
            elif cid:
                c = menu_repo.find_category_by_id(cid)
                if c:
                    item["category_name"] = c.get("name")

        # Populate Subcategory Name
        sid = str(item.get("subcategory_id") or "")
        if not item.get("subcategory_name") and sid:
            if subcategories and sid in subcategories:
                item["subcategory_name"] = subcategories[sid]
            else:
                s = menu_repo.find_subcategory_by_id(sid)
                if s:
                    item["subcategory_name"] = s.get("name")

        # Normalise type and food_type
        if not item.get("type"):
            item["type"] = "Veg" if item.get("is_vegetarian") else "Non-Veg"
        if not item.get("food_type"):
            item["food_type"] = item["type"]

        # Ensure pricing breakdown values
        price = item.get("price")
        price_dec = price.to_decimal() if hasattr(price, "to_decimal") else Decimal(str(price or 0))
        if item.get("base_price") is None:
            item["base_price"] = price_dec
        else:
            bp = item.get("base_price")
            item["base_price"] = bp.to_decimal() if hasattr(bp, "to_decimal") else Decimal(str(bp))

        disc = item.get("discount", 0)
        item["discount"] = disc.to_decimal() if hasattr(disc, "to_decimal") else Decimal(str(disc or 0))
        tx = item.get("tax", 0)
        item["tax"] = tx.to_decimal() if hasattr(tx, "to_decimal") else Decimal(str(tx or 0))

        if item.get("final_price") is None:
            item["final_price"] = max(Decimal("0"), (item["base_price"] - item["discount"]) + item["tax"])
        else:
            fp = item.get("final_price")
            item["final_price"] = fp.to_decimal() if hasattr(fp, "to_decimal") else Decimal(str(fp))

        if "is_active" not in item:
            item["is_active"] = True
        if "is_featured" not in item:
            item["is_featured"] = False
        if "display_order" not in item:
            item["display_order"] = 0

        return item

    @staticmethod
    def create_item(data: Any) -> Dict[str, Any]:
        name = str(get_field(data, "name", "")).strip()
        price = get_field(data, "price")
        prep_time = get_field(data, "preparation_time", 15)
        cat_id = get_field(data, "category_id")
        subcat_id = get_field(data, "subcategory_id")
        desc = get_field(data, "description")
        is_avail = get_field(data, "is_available", True)
        is_veg = get_field(data, "is_vegetarian", False)
        item_type = get_field(data, "type")
        food_type = get_field(data, "food_type")
        img_url = get_field(data, "image_url")
        base_price = get_field(data, "base_price")
        discount = get_field(data, "discount", Decimal("0"))
        tax = get_field(data, "tax", Decimal("0"))
        final_price = get_field(data, "final_price")
        is_featured = get_field(data, "is_featured", False)
        is_active = get_field(data, "is_active", True)
        display_order = get_field(data, "display_order", 0)
        spicy_level = get_field(data, "spicy_level")
        serving_size = get_field(data, "serving_size")
        tags = get_field(data, "tags", [])
        inv_tracking = get_field(data, "inventory_tracking_enabled", True)

        if not name:
            raise ValueError("Item name cannot be empty")
        if not cat_id:
            raise ValueError("Category is required")

        # Domain Entity validation: rejects negative price, zero/neg prep time
        entity = MenuItemEntity(
            name=name,
            price=price,
            base_price=base_price,
            discount=discount,
            tax=tax,
            final_price=final_price,
            preparation_time=prep_time,
            category_id=str(cat_id),
            subcategory_id=str(subcat_id) if subcat_id else None,
            description=desc,
            is_available=is_avail,
            is_vegetarian=is_veg,
            type=item_type,
            food_type=food_type,
            image_url=str(img_url).strip() if img_url else None,
            is_featured=is_featured,
            is_active=is_active,
            display_order=display_order,
            spicy_level=spicy_level,
            serving_size=serving_size,
            tags=tags,
            inventory_tracking_enabled=inv_tracking,
        )

        category = menu_repo.find_category_by_id(entity.category_id)
        if not category:
            category = menu_repo.find_category_by_name(str(entity.category_id))
            if not category:
                category = MenuCategoryService.create_category({"name": str(entity.category_id)})

        target_cat_id = str(category.get("id") or category.get("_id"))
        cat_oid = ObjectId(target_cat_id) if ObjectId.is_valid(target_cat_id) else target_cat_id
        cat_name = category.get("name")

        # Subcategory validation
        subcat_oid = None
        subcat_name = None
        if entity.subcategory_id:
            subcat = menu_repo.find_subcategory_by_id(str(entity.subcategory_id))
            if not subcat:
                subcat = menu_repo.find_subcategory_by_name(target_cat_id, str(entity.subcategory_id))
            if not subcat:
                raise ValueError(f"Subcategory '{entity.subcategory_id}' does not exist")

            # Validate that subcategory belongs to selected category
            subcat_parent_id = str(subcat.get("category_id"))
            if subcat_parent_id != target_cat_id:
                raise ValueError(f"Subcategory '{subcat.get('name')}' does not belong to category '{cat_name}'")

            target_sub_id = str(subcat.get("id") or subcat.get("_id"))
            subcat_oid = ObjectId(target_sub_id) if ObjectId.is_valid(target_sub_id) else target_sub_id
            subcat_name = subcat.get("name")

        doc = {
            "name": entity.name,
            "description": entity.description,
            "category_id": cat_oid,
            "category_name": cat_name,
            "subcategory_id": subcat_oid,
            "subcategory_name": subcat_name,
            "price": decimal128(entity.price),
            "base_price": decimal128(entity.base_price),
            "discount": decimal128(entity.discount),
            "tax": decimal128(entity.tax),
            "final_price": decimal128(entity.final_price),
            "preparation_time": entity.preparation_time,
            "is_available": entity.is_available,
            "is_active": entity.is_active,
            "is_featured": entity.is_featured,
            "display_order": entity.display_order,
            "is_vegetarian": entity.is_vegetarian,
            "type": entity.type,
            "food_type": entity.food_type,
            "image_url": entity.image_url,
            "spicy_level": entity.spicy_level,
            "serving_size": entity.serving_size,
            "tags": entity.tags,
            "inventory_tracking_enabled": entity.inventory_tracking_enabled,
            "created_at": now_utc(),
            "updated_at": now_utc(),
        }
        res = menu_repo.insert(doc)
        res["category_name"] = cat_name
        res["subcategory_name"] = subcat_name
        return MenuItemService._enrich_item(res)

    @staticmethod
    def get_items(category_id: Optional[str] = None, subcategory_id: Optional[str] = None, active_only: bool = False) -> List[Dict[str, Any]]:
        if subcategory_id:
            items = menu_repo.find_by_subcategory(subcategory_id, include_inactive=not active_only)
        elif category_id:
            items = menu_repo.find_by_category(category_id, include_inactive=not active_only)
        else:
            query = {"is_active": True} if active_only else {}
            docs = menu_repo.collection.find(query).sort([("display_order", 1), ("name", 1)])
            items = serialize_documents(docs)

        categories = {str(c["id"]): c["name"] for c in menu_repo.find_all_categories()}
        subcategories = {str(s["id"]): s["name"] for s in menu_repo.find_all_subcategories()}

        for it in items:
            MenuItemService._enrich_item(it, categories, subcategories)
        return items

    @staticmethod
    def get_item(item_id: str) -> Dict[str, Any]:
        item = menu_repo.find_by_id(item_id)
        if not item:
            item = menu_repo.find_by_name(item_id)
        if not item:
            raise ValueError("Menu item not found")
        return MenuItemService._enrich_item(item)

    @staticmethod
    def get_available_items() -> List[Dict[str, Any]]:
        items = menu_repo.find_available()
        categories = {str(c["id"]): c["name"] for c in menu_repo.find_all_categories()}
        subcategories = {str(s["id"]): s["name"] for s in menu_repo.find_all_subcategories()}
        for it in items:
            MenuItemService._enrich_item(it, categories, subcategories)
        return items

    @staticmethod
    def get_items_by_category(category_id: str, active_only: bool = False) -> List[Dict[str, Any]]:
        items = menu_repo.find_by_category(category_id, include_inactive=not active_only)
        cat = menu_repo.find_category_by_id(category_id)
        cat_name = cat.get("name") if cat else None
        categories = {str(c["id"]): c["name"] for c in menu_repo.find_all_categories()}
        subcategories = {str(s["id"]): s["name"] for s in menu_repo.find_all_subcategories()}
        for it in items:
            if not it.get("category_name") and cat_name:
                it["category_name"] = cat_name
            MenuItemService._enrich_item(it, categories, subcategories)
        return items

    @staticmethod
    def get_items_by_subcategory(subcategory_id: str, active_only: bool = False) -> List[Dict[str, Any]]:
        items = menu_repo.find_by_subcategory(subcategory_id, include_inactive=not active_only)
        categories = {str(c["id"]): c["name"] for c in menu_repo.find_all_categories()}
        subcategories = {str(s["id"]): s["name"] for s in menu_repo.find_all_subcategories()}
        for it in items:
            MenuItemService._enrich_item(it, categories, subcategories)
        return items

    @staticmethod
    def search_items(query: str, active_only: bool = False) -> List[Dict[str, Any]]:
        if not query:
            return MenuItemService.get_items(active_only=active_only)
        items = menu_repo.search(query.strip(), include_inactive=not active_only)
        categories = {str(c["id"]): c["name"] for c in menu_repo.find_all_categories()}
        subcategories = {str(s["id"]): s["name"] for s in menu_repo.find_all_subcategories()}
        for it in items:
            MenuItemService._enrich_item(it, categories, subcategories)
        return items

    @staticmethod
    def update_item(item_id: str, data: Any) -> Dict[str, Any]:
        update_data = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.copy()

        current_item = menu_repo.find_by_id(item_id)
        if not current_item:
            current_item = menu_repo.find_by_name(item_id)
        if not current_item:
            raise ValueError("Menu item not found")

        # Price validation & calculation
        base_price = None
        if "base_price" in update_data and update_data["base_price"] is not None:
            dec_bp = Decimal(str(update_data["base_price"]))
            if dec_bp < 0:
                raise ValueError("Base price cannot be negative")
            base_price = dec_bp
            update_data["base_price"] = decimal128(dec_bp)

        if "price" in update_data and update_data["price"] is not None:
            dec_price = Decimal(str(update_data["price"]))
            if dec_price < 0:
                raise ValueError("Price cannot be negative")
            update_data["price"] = decimal128(dec_price)
            if base_price is None:
                base_price = dec_price
                update_data["base_price"] = decimal128(dec_price)
        elif base_price is not None:
            update_data["price"] = decimal128(base_price)

        if "discount" in update_data and update_data["discount"] is not None:
            dec_disc = Decimal(str(update_data["discount"]))
            if dec_disc < 0:
                raise ValueError("Discount cannot be negative")
            update_data["discount"] = decimal128(dec_disc)

        if "tax" in update_data and update_data["tax"] is not None:
            dec_tax = Decimal(str(update_data["tax"]))
            if dec_tax < 0:
                raise ValueError("Tax cannot be negative")
            update_data["tax"] = decimal128(dec_tax)

        # Recalculate final_price
        curr_bp = Decimal(str(update_data.get("base_price") or current_item.get("base_price") or current_item.get("price") or 0))
        curr_disc = Decimal(str(update_data.get("discount") or current_item.get("discount") or 0))
        curr_tax = Decimal(str(update_data.get("tax") or current_item.get("tax") or 0))
        if "final_price" in update_data and update_data["final_price"] is not None:
            dec_fp = Decimal(str(update_data["final_price"]))
            if dec_fp < 0:
                raise ValueError("Final price cannot be negative")
            update_data["final_price"] = decimal128(dec_fp)
        else:
            calc_fp = max(Decimal("0"), (curr_bp - curr_disc) + curr_tax)
            update_data["final_price"] = decimal128(calc_fp)

        if "preparation_time" in update_data and update_data["preparation_time"] is not None:
            if int(update_data["preparation_time"]) <= 0:
                raise ValueError("Preparation time must be greater than zero")
            update_data["preparation_time"] = int(update_data["preparation_time"])

        target_cat_id = str(current_item.get("category_id"))
        if "category_id" in update_data and update_data["category_id"]:
            cat = menu_repo.find_category_by_id(str(update_data["category_id"]))
            if not cat:
                cat = menu_repo.find_category_by_name(str(update_data["category_id"]))
            if not cat:
                raise ValueError("Category not found")
            target_cat_id = str(cat.get("id") or cat.get("_id"))
            update_data["category_id"] = ObjectId(target_cat_id) if ObjectId.is_valid(target_cat_id) else target_cat_id
            update_data["category_name"] = cat.get("name")

        if "subcategory_id" in update_data:
            if update_data["subcategory_id"]:
                sub = menu_repo.find_subcategory_by_id(str(update_data["subcategory_id"]))
                if not sub:
                    sub = menu_repo.find_subcategory_by_name(target_cat_id, str(update_data["subcategory_id"]))
                if not sub:
                    raise ValueError(f"Subcategory '{update_data['subcategory_id']}' not found")
                if str(sub.get("category_id")) != target_cat_id:
                    raise ValueError("Subcategory does not belong to the selected category")
                target_sub_id = str(sub.get("id") or sub.get("_id"))
                update_data["subcategory_id"] = ObjectId(target_sub_id) if ObjectId.is_valid(target_sub_id) else target_sub_id
                update_data["subcategory_name"] = sub.get("name")
            else:
                update_data["subcategory_id"] = None
                update_data["subcategory_name"] = None

        resolved_type = update_data.get("food_type") or update_data.get("type")
        if resolved_type:
            t = str(resolved_type).strip()
            if t.lower() in ["veg", "vegetarian"]:
                update_data["type"] = "Veg"
                update_data["food_type"] = "Veg"
                update_data["is_vegetarian"] = True
            elif t.lower() in ["non-veg", "non-vegetarian", "nonveg"]:
                update_data["type"] = "Non-Veg"
                update_data["food_type"] = "Non-Veg"
                update_data["is_vegetarian"] = False
            elif t.lower() in ["egg", "eggetarian"]:
                update_data["type"] = "Egg"
                update_data["food_type"] = "Non-Veg"
                update_data["is_vegetarian"] = False
            elif t.lower() in ["beverage", "beverages", "drink", "drinks"]:
                update_data["type"] = "Beverage"
                update_data["food_type"] = "Veg"
                update_data["is_vegetarian"] = True

        if "display_order" in update_data and update_data["display_order"] is not None:
            update_data["display_order"] = int(update_data["display_order"])

        update_data["updated_at"] = now_utc()
        raw_item_id = current_item.get("id") or current_item.get("_id") or item_id
        updated = menu_repo.update(raw_item_id, update_data)
        if not updated:
            raise ValueError("Menu item not found")
        return MenuItemService._enrich_item(updated)

    @staticmethod
    def update_availability(item_id: str, is_available: bool) -> Dict[str, Any]:
        updated = menu_repo.update(item_id, {"is_available": bool(is_available), "updated_at": now_utc()})
        if not updated:
            raise ValueError("Menu item not found")
        return MenuItemService._enrich_item(updated)

    @staticmethod
    def delete_item(item_id: str) -> Dict[str, Any]:
        """
        Safe deletion implementation (Section 8):
        Before deleting an item, if it has historical associations in Orders,
        Kitchen operations, or Recipes, soft delete by setting `is_active = False`
        and `is_available = False` so that historical order records remain intact.
        """
        item_id_clean = str(item_id).strip()
        existing = menu_repo.find_by_id(item_id_clean)
        if not existing:
            existing = menu_repo.find_by_name(item_id_clean)
        if not existing:
            raise ValueError("Menu item not found")

        raw_id = existing.get("id") or existing.get("_id") or item_id_clean

        # Check associations
        has_associations = menu_repo.has_item_associations(str(raw_id))

        if has_associations:
            # Soft delete
            menu_repo.soft_delete_item(str(raw_id))
            return {
                "message": f"Menu item '{existing['name']}' has associated historical orders/operations and was safely deactivated.",
                "soft_deleted": True,
            }

        # Otherwise hard delete
        deleted = menu_repo.delete(raw_id)
        if not deleted and ObjectId.is_valid(str(raw_id)):
            deleted = menu_repo.collection.delete_one({"_id": ObjectId(str(raw_id))}).deleted_count > 0
        if not deleted:
            deleted = menu_repo.collection.delete_one({"_id": str(raw_id)}).deleted_count > 0

        # Clean up associated recipes
        from app.database.mongodb import recipes_collection
        try:
            oid = ObjectId(str(raw_id)) if ObjectId.is_valid(str(raw_id)) else raw_id
            recipes_collection.delete_many({"menu_item_id": {"$in": [oid, str(raw_id)]}})
        except Exception:
            pass

        return {
            "message": f"Menu item '{existing['name']}' deleted successfully.",
            "soft_deleted": False,
        }

    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """
        Calculates menu statistics for the dashboard (Section 21).
        """
        all_items = list(menu_repo.collection.find({"is_active": {"$ne": False}}))
        total_items = len(all_items)
        available_items = sum(1 for it in all_items if it.get("is_available", True))
        unavailable_items = total_items - available_items

        veg_items = 0
        non_veg_items = 0
        starters = 0
        desserts = 0
        featured_items = sum(1 for it in all_items if it.get("is_featured", False))

        categories = {str(c["_id"]): c["name"].lower() for c in menu_repo.categories_col.find()}
        subcategories = {str(s["_id"]): s["name"].lower() for s in menu_repo.subcategories_col.find()}

        for it in all_items:
            # Veg / Non-Veg
            t = str(it.get("food_type") or it.get("type") or "").lower()
            is_v = it.get("is_vegetarian", False)
            if is_v or t in ["veg", "vegetarian"]:
                veg_items += 1
            else:
                non_veg_items += 1

            # Starters check
            cid = str(it.get("category_id"))
            sid = str(it.get("subcategory_id"))
            c_name = categories.get(cid, "")
            s_name = subcategories.get(sid, "")
            it_name = it.get("name", "").lower()

            if "starter" in c_name or "starter" in s_name or "starter" in it_name or "tikka" in it_name or "manchurian" in it_name or "65" in it_name:
                starters += 1
            elif "dessert" in c_name or "dessert" in s_name or "dessert" in it_name or "jamun" in it_name or "ice cream" in it_name or "brownie" in it_name or "rasmalai" in it_name:
                desserts += 1

        cats_count = menu_repo.categories_col.count_documents({})
        subcats_count = menu_repo.subcategories_col.count_documents({})

        return {
            "total_items": total_items,
            "available_items": available_items,
            "unavailable_items": unavailable_items,
            "veg_items": veg_items,
            "non_veg_items": non_veg_items,
            "starters": starters,
            "desserts": desserts,
            "featured_items": featured_items,
            "categories_count": cats_count,
            "subcategories_count": subcats_count,
        }
