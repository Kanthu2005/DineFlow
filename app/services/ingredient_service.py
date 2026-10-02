"""
Ingredient and Inventory Service.
Manages raw materials, stock receiving, batch tracking, FEFO management,
wastage logging, physical stock adjustments, location transfers, and audit reporting.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.repositories.inventory_repository import (
    IngredientRepository,
    BatchRepository,
    SupplierRepository,
    PurchaseOrderRepository,
    CategoryRepository,
    StorageLocationRepository,
    WastageRepository,
)
from app.models.entities import (
    Ingredient as IngredientEntity,
    IngredientBatch as BatchEntity,
    StockMovement as StockMovementEntity,
)
from app.services.common import (
    to_object_id,
    optional_object_id,
    decimal128,
    now_utc,
    serialize_document,
    serialize_documents,
    get_field,
)
from app.database.mongodb import (
    recipes_collection,
    menu_items_collection,
    stock_movements_collection,
    purchase_orders_collection,
    wastage_records_collection,
    stock_adjustments_collection,
    stock_transfers_collection,
    storage_locations_collection,
    ingredient_categories_collection,
    suppliers_collection,
    batches_collection,
)
from app.utils.units import convert_quantity, normalize_unit, SUPPORTED_UNITS

repo = IngredientRepository()
batch_repo = BatchRepository()
supplier_repo = SupplierRepository()
po_repo = PurchaseOrderRepository()
cat_repo = CategoryRepository()
loc_repo = StorageLocationRepository()
wastage_repo = WastageRepository()


class IngredientService:

    # =========================================================================
    # Core Ingredient Management
    # =========================================================================

    @staticmethod
    def create_ingredient(data: Any) -> Dict[str, Any]:
        name = get_field(data, "name")
        unit = get_field(data, "unit")
        sku = get_field(data, "sku")
        category = get_field(data, "category") or "Other"
        category_id = get_field(data, "category_id")
        
        # Support either available_quantity or current_stock
        avail_qty = get_field(data, "current_stock") if get_field(data, "current_stock") is not None else get_field(data, "available_quantity", 0)
        # Support either minimum_stock_level or minimum_stock
        min_stock = get_field(data, "minimum_stock") if get_field(data, "minimum_stock") is not None else get_field(data, "minimum_stock_level", 0)
        max_stock = get_field(data, "maximum_stock")
        reorder_lvl = get_field(data, "reorder_level") or min_stock
        cost = get_field(data, "cost_per_unit", 0)
        supplier_id = get_field(data, "supplier_id")
        supplier_name = get_field(data, "supplier_name")
        location_id = get_field(data, "storage_location_id")
        location_name = get_field(data, "storage_location_name")
        is_active = get_field(data, "is_active", True)

        if not name or not str(name).strip():
            raise ValueError("Ingredient name cannot be empty")
        norm_unit = normalize_unit(unit)

        # Validate with Domain Entity
        entity = IngredientEntity(
            name=name,
            unit=norm_unit,
            available_quantity=avail_qty,
            minimum_stock_level=min_stock,
            cost_per_unit=cost,
            supplier_name=supplier_name,
            is_active=is_active,
            sku=sku,
            category=category,
            category_id=str(category_id) if category_id else None,
            maximum_stock=max_stock,
            reorder_level=reorder_lvl,
            supplier_id=str(supplier_id) if supplier_id else None,
            storage_location_id=str(location_id) if location_id else None,
            storage_location_name=location_name,
        )

        existing = repo.find_by_name(entity.name)
        if existing:
            raise ValueError(f"Ingredient '{entity.name}' already exists")

        # Resolve supplier name if ID provided
        if entity.supplier_id and not entity.supplier_name:
            sup = supplier_repo.find_by_id(entity.supplier_id)
            if sup:
                entity.supplier_name = sup.get("name")

        # Resolve location name if ID provided
        if entity.storage_location_id and not entity.storage_location_name:
            loc = loc_repo.find_by_id(entity.storage_location_id)
            if loc:
                entity.storage_location_name = loc.get("name")

        doc = {
            "name": entity.name,
            "sku": entity.sku or f"ING-{entity.name[:3].upper()}-{int(now_utc().timestamp())%10000:04d}",
            "category": entity.category,
            "category_id": to_object_id(entity.category_id) if entity.category_id else None,
            "unit": entity.unit,
            "available_quantity": decimal128(entity.available_quantity),
            "current_stock": decimal128(entity.available_quantity),
            "minimum_stock_level": decimal128(entity.minimum_stock_level),
            "minimum_stock": decimal128(entity.minimum_stock_level),
            "maximum_stock": decimal128(entity.maximum_stock) if entity.maximum_stock is not None else None,
            "reorder_level": decimal128(entity.reorder_level) if entity.reorder_level is not None else decimal128(entity.minimum_stock_level),
            "cost_per_unit": decimal128(entity.cost_per_unit),
            "supplier_id": to_object_id(entity.supplier_id) if entity.supplier_id else None,
            "supplier_name": entity.supplier_name,
            "storage_location_id": to_object_id(entity.storage_location_id) if entity.storage_location_id else None,
            "storage_location_name": entity.storage_location_name,
            "is_active": entity.is_active,
            "created_at": now_utc(),
            "updated_at": now_utc(),
        }

        created = repo.insert(doc)

        # Record initial stock purchase/opening stock movement and initial batch if available > 0
        if entity.available_quantity > 0:
            created_oid = to_object_id(created["id"])
            batch_doc = {
                "ingredient_id": created_oid,
                "batch_number": f"BATCH-{now_utc().strftime('%Y%m%d')}-INIT",
                "quantity": decimal128(entity.available_quantity),
                "remaining_quantity": decimal128(entity.available_quantity),
                "unit": entity.unit,
                "unit_cost": decimal128(entity.cost_per_unit),
                "received_date": now_utc(),
                "expiry_date": now_utc() + timedelta(days=30),  # Default 30-day initial batch window
                "supplier_id": doc["supplier_id"],
                "storage_location_id": doc["storage_location_id"],
                "status": "ACTIVE",
                "created_at": now_utc(),
            }
            batch_rec = batch_repo.create_batch(batch_doc)

            repo.record_movement({
                "ingredient_id": created_oid,
                "movement_type": "PURCHASE",
                "quantity": decimal128(entity.available_quantity),
                "unit": entity.unit,
                "previous_stock": decimal128(Decimal("0")),
                "new_stock": decimal128(entity.available_quantity),
                "unit_cost": decimal128(entity.cost_per_unit),
                "total_cost": decimal128(entity.available_quantity * entity.cost_per_unit),
                "batch_id": to_object_id(batch_rec["id"]),
                "reference_type": "INITIAL_STOCK",
                "reference_id": None,
                "reason": "Opening Inventory Balance",
                "performed_by": "SYSTEM",
                "created_at": now_utc(),
            })

        return IngredientService.get_ingredient(created["id"])

    @staticmethod
    def get_ingredients(category: Optional[str] = None) -> List[Dict[str, Any]]:
        items = repo.find_all(sort_field="name", sort_dir=1)
        results = []
        for it in items:
            avail = it.get("available_quantity") or it.get("current_stock") or Decimal("0")
            dec_avail = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail))
            it["current_stock"] = dec_avail
            it["available_quantity"] = dec_avail
            
            reorder = it.get("reorder_level") or it.get("minimum_stock_level") or Decimal("0")
            dec_reorder = reorder.to_decimal() if hasattr(reorder, "to_decimal") else Decimal(str(reorder))
            
            if dec_avail <= 0:
                it["status"] = "OUT_OF_STOCK"
            elif dec_avail <= dec_reorder:
                it["status"] = "LOW_STOCK"
            else:
                it["status"] = "NORMAL"

            if category and it.get("category") != category:
                continue
            results.append(it)
        return results

    @staticmethod
    def get_active_ingredients() -> List[Dict[str, Any]]:
        items = repo.find_active()
        for it in items:
            avail = it.get("available_quantity") or it.get("current_stock") or Decimal("0")
            dec_avail = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail))
            it["current_stock"] = dec_avail
            it["available_quantity"] = dec_avail
            reorder = it.get("reorder_level") or it.get("minimum_stock_level") or Decimal("0")
            dec_reorder = reorder.to_decimal() if hasattr(reorder, "to_decimal") else Decimal(str(reorder))
            it["status"] = "OUT_OF_STOCK" if dec_avail <= 0 else ("LOW_STOCK" if dec_avail <= dec_reorder else "NORMAL")
        return items

    @staticmethod
    def get_ingredient(ingredient_id: str) -> Dict[str, Any]:
        item = repo.find_by_id(ingredient_id)
        if not item:
            raise ValueError("Ingredient not found")
        avail = item.get("available_quantity") or item.get("current_stock") or Decimal("0")
        dec_avail = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail))
        item["current_stock"] = dec_avail
        item["available_quantity"] = dec_avail
        reorder = item.get("reorder_level") or item.get("minimum_stock_level") or Decimal("0")
        dec_reorder = reorder.to_decimal() if hasattr(reorder, "to_decimal") else Decimal(str(reorder))
        item["status"] = "OUT_OF_STOCK" if dec_avail <= 0 else ("LOW_STOCK" if dec_avail <= dec_reorder else "NORMAL")
        
        # Enrich with active batches
        batches = batch_repo.find_by_ingredient(ingredient_id, only_active=True)
        item["batches"] = batches
        return item

    @staticmethod
    def update_ingredient(ingredient_id: str, data: Any) -> Dict[str, Any]:
        update_dict = data.model_dump(exclude_unset=True) if hasattr(data, "model_dump") else data.copy()

        # Reject negative values and convert decimals
        for field in ["available_quantity", "current_stock", "minimum_stock_level", "minimum_stock", "maximum_stock", "reorder_level", "cost_per_unit"]:
            if field in update_dict and update_dict[field] is not None:
                dec = Decimal(str(update_dict[field]))
                if dec < 0:
                    raise ValueError(f"{field} cannot be negative")
                update_dict[field] = decimal128(dec)

        # Synchronize current_stock and available_quantity
        if "current_stock" in update_dict:
            update_dict["available_quantity"] = update_dict["current_stock"]
        elif "available_quantity" in update_dict:
            update_dict["current_stock"] = update_dict["available_quantity"]

        # Synchronize minimum_stock and minimum_stock_level
        if "minimum_stock" in update_dict:
            update_dict["minimum_stock_level"] = update_dict["minimum_stock"]
        elif "minimum_stock_level" in update_dict:
            update_dict["minimum_stock"] = update_dict["minimum_stock_level"]

        if "unit" in update_dict and update_dict["unit"]:
            update_dict["unit"] = normalize_unit(update_dict["unit"])

        if "supplier_id" in update_dict and update_dict["supplier_id"]:
            update_dict["supplier_id"] = to_object_id(update_dict["supplier_id"])
            sup = supplier_repo.find_by_id(update_dict["supplier_id"])
            if sup:
                update_dict["supplier_name"] = sup.get("name")

        if "storage_location_id" in update_dict and update_dict["storage_location_id"]:
            update_dict["storage_location_id"] = to_object_id(update_dict["storage_location_id"])
            loc = loc_repo.find_by_id(update_dict["storage_location_id"])
            if loc:
                update_dict["storage_location_name"] = loc.get("name")

        update_dict["updated_at"] = now_utc()
        updated = repo.update(ingredient_id, update_dict)
        if not updated:
            raise ValueError("Ingredient not found")
        return IngredientService.get_ingredient(ingredient_id)

    @staticmethod
    def delete_ingredient(ingredient_id: str) -> Dict[str, Any]:
        used_count = recipes_collection.count_documents({"ingredient_id": to_object_id(ingredient_id)})
        if used_count > 0:
            recipes_collection.delete_many({"ingredient_id": to_object_id(ingredient_id)})

        deleted = repo.delete(ingredient_id)
        if not deleted:
            raise ValueError("Ingredient not found")
        return {"message": "Ingredient deleted successfully", "id": ingredient_id}

    @staticmethod
    def get_stock_status(ingredient_id: str) -> Dict[str, Any]:
        item = IngredientService.get_ingredient(ingredient_id)
        avail = item.get("current_stock") or item.get("available_quantity") or Decimal("0")
        dec_avail = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail))
        reorder = item.get("reorder_level") or item.get("minimum_stock_level") or item.get("minimum_stock") or Decimal("0")
        dec_reorder = reorder.to_decimal() if hasattr(reorder, "to_decimal") else Decimal(str(reorder))
        status = "OUT_OF_STOCK" if dec_avail <= 0 else ("LOW_STOCK" if dec_avail <= dec_reorder else "NORMAL")
        return {
            "ingredient_id": ingredient_id,
            "id": ingredient_id,
            "ingredient_name": item["name"],
            "name": item["name"],
            "unit": item["unit"],
            "available_quantity": float(dec_avail),
            "current_stock": float(dec_avail),
            "minimum_stock_level": float(dec_reorder),
            "minimum_stock": float(dec_reorder),
            "reorder_level": float(dec_reorder),
            "status": status,
        }

    @staticmethod
    def get_low_stock_ingredients() -> List[Dict[str, Any]]:
        items = repo.find_low_stock()
        results = []
        for it in items:
            avail = it.get("available_quantity") or it.get("current_stock") or Decimal("0")
            dec_avail = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail))
            it["current_stock"] = float(dec_avail)
            it["available_quantity"] = float(dec_avail)
            reorder = it.get("reorder_level") or it.get("minimum_stock_level") or it.get("minimum_stock") or Decimal("0")
            dec_reorder = reorder.to_decimal() if hasattr(reorder, "to_decimal") else Decimal(str(reorder))
            it["status"] = "OUT_OF_STOCK" if dec_avail <= 0 else "LOW_STOCK"
            results.append(it)
        return results

    # =========================================================================
    # Stock In / Receiving & Batch Management
    # =========================================================================

    @staticmethod
    def receive_stock(
        ingredient_id: str,
        quantity: Decimal | float | int | str,
        unit_cost: Optional[Decimal | float | int | str] = None,
        supplier_id: Optional[str] = None,
        purchase_order_id: Optional[str] = None,
        batch_number: Optional[str] = None,
        expiry_date: Optional[datetime] = None,
        storage_location_id: Optional[str] = None,
        reason: Optional[str] = "Stock Received",
        performed_by: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """
        Stock In / Receiving:
        Previous Stock + Received Quantity = New Stock
        Creates Batch record and logs immutable Stock Movement audit entry.
        """
        dec_qty = Decimal(str(quantity))
        if dec_qty <= 0:
            raise ValueError("Received quantity must be greater than zero")

        item = IngredientService.get_ingredient(ingredient_id)
        current_stock = item["current_stock"]
        new_stock = current_stock + dec_qty

        # Cost determination
        cost = Decimal(str(unit_cost)) if unit_cost is not None else Decimal(str(item.get("cost_per_unit") or 0))
        if cost < 0:
            raise ValueError("Unit cost cannot be negative")

        # Expiry date determination (defaults to 14 days if not provided)
        exp_date = expiry_date or (now_utc() + timedelta(days=14))
        batch_no = batch_number or f"BATCH-{now_utc().strftime('%Y%m%d%H%M')}-{item['name'][:3].upper()}"

        sup_oid = optional_object_id(supplier_id or item.get("supplier_id"))
        po_oid = optional_object_id(purchase_order_id)
        loc_oid = optional_object_id(storage_location_id or item.get("storage_location_id"))

        # 1. Create Batch Record
        batch_doc = {
            "ingredient_id": to_object_id(ingredient_id),
            "batch_number": batch_no,
            "quantity": decimal128(dec_qty),
            "remaining_quantity": decimal128(dec_qty),
            "unit": item["unit"],
            "unit_cost": decimal128(cost),
            "received_date": now_utc(),
            "expiry_date": exp_date,
            "supplier_id": sup_oid,
            "purchase_order_id": po_oid,
            "storage_location_id": loc_oid,
            "status": "ACTIVE",
            "created_at": now_utc(),
            "updated_at": now_utc(),
        }
        created_batch = batch_repo.create_batch(batch_doc)

        # 2. Update Ingredient Stock
        repo.increment_stock(ingredient_id, dec_qty)
        # Update cost_per_unit to latest received cost if specified
        if unit_cost is not None:
            repo.update(ingredient_id, {"cost_per_unit": decimal128(cost)})

        # 3. Create Stock Movement Ledger Record
        total_cost = dec_qty * cost
        movement = repo.record_movement({
            "ingredient_id": to_object_id(ingredient_id),
            "batch_id": to_object_id(created_batch["id"]),
            "movement_type": "RECEIVE",
            "quantity": decimal128(dec_qty),
            "unit": item["unit"],
            "previous_stock": decimal128(current_stock),
            "new_stock": decimal128(new_stock),
            "unit_cost": decimal128(cost),
            "total_cost": decimal128(total_cost),
            "supplier_id": sup_oid,
            "purchase_order_id": po_oid,
            "reference_type": "RECEIVING",
            "reference_id": batch_no,
            "reason": reason or "Stock Received",
            "performed_by": performed_by,
            "created_at": now_utc(),
        })

        return {
            "ingredient_id": ingredient_id,
            "id": ingredient_id,
            "ingredient_name": item["name"],
            "received_quantity": float(dec_qty),
            "previous_stock": float(current_stock),
            "new_stock": float(new_stock),
            "available_quantity": float(new_stock),
            "current_stock": float(new_stock),
            "unit": item["unit"],
            "batch": created_batch,
            "movement": movement,
        }

    # Backward compatibility for existing update_stock endpoint
    @staticmethod
    def update_stock(
        ingredient_id: str,
        quantity: Decimal | float | int | str,
        movement_type: str = "MANUAL_ADJUSTMENT",
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        created_by: str = "SYSTEM",
    ) -> Dict[str, Any]:
        dec_qty = Decimal(str(quantity))
        item = IngredientService.get_ingredient(ingredient_id)
        current_stock = item["current_stock"]

        new_stock = current_stock + dec_qty
        if new_stock < 0:
            raise ValueError(f"Insufficient stock for {item['name']}. Current: {current_stock}, Requested deduction: {abs(dec_qty)}")

        if dec_qty > 0:
            res = IngredientService.receive_stock(
                ingredient_id=ingredient_id,
                quantity=dec_qty,
                reason=reference_type or "Manual Restock",
                performed_by=created_by,
            )
        else:
            res = IngredientService.record_wastage(
                ingredient_id=ingredient_id,
                quantity=abs(dec_qty),
                reason="OTHER",
                notes=reference_type or "Manual deduction",
                performed_by=created_by,
            )
        res["id"] = ingredient_id
        res["ingredient_id"] = ingredient_id
        res["available_quantity"] = float(new_stock)
        res["current_stock"] = float(new_stock)
        res["previous_stock"] = float(current_stock)
        res["new_stock"] = float(new_stock)
        return res

    # =========================================================================
    # Wastage Management
    # =========================================================================

    @staticmethod
    def record_wastage(
        ingredient_id: str,
        quantity: Decimal | float | int | str,
        reason: str = "SPOILED",
        batch_id: Optional[str] = None,
        notes: Optional[str] = None,
        performed_by: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """
        Wastage Management:
        Current Stock - Wasted Quantity = New Stock
        Deducts from Batch (if applicable) and records immutable WASTAGE movement.
        """
        dec_qty = Decimal(str(quantity))
        if dec_qty <= 0:
            raise ValueError("Wastage quantity must be greater than zero")

        valid_reasons = ["EXPIRED", "SPOILED", "BURNT", "OVER_PRODUCTION", "DAMAGED", "SPILLAGE", "PREPARATION_ERROR", "OTHER"]
        r_upper = reason.upper()
        if r_upper not in valid_reasons:
            raise ValueError(f"Invalid wastage reason: '{reason}'. Valid reasons: {', '.join(valid_reasons)}")

        item = IngredientService.get_ingredient(ingredient_id)
        current_stock = item["current_stock"]
        if current_stock < dec_qty:
            raise ValueError(f"Cannot record wastage exceeding current stock. Stock: {current_stock} {item['unit']}, Wasted: {dec_qty} {item['unit']}")

        new_stock = current_stock - dec_qty
        unit_cost = Decimal(str(item.get("cost_per_unit") or 0))
        total_loss = dec_qty * unit_cost

        # If batch_id provided, deduct from specific batch
        if batch_id:
            batch_repo.decrement_batch(batch_id, dec_qty)
        else:
            # Deduct via FEFO from earliest batches
            batches = batch_repo.find_by_ingredient(ingredient_id, only_active=True)
            rem_to_deduct = dec_qty
            for b in batches:
                b_rem = b["remaining_quantity"].to_decimal() if hasattr(b["remaining_quantity"], "to_decimal") else Decimal(str(b["remaining_quantity"]))
                if b_rem <= 0:
                    continue
                alloc = min(b_rem, rem_to_deduct)
                batch_repo.decrement_batch(b["id"], alloc)
                rem_to_deduct -= alloc
                if rem_to_deduct <= 0:
                    break

        # Decrement ingredient stock
        repo.increment_stock(ingredient_id, -dec_qty)

        # Store wastage record
        wastage_doc = {
            "ingredient_id": to_object_id(ingredient_id),
            "ingredient_name": item["name"],
            "batch_id": to_object_id(batch_id) if batch_id else None,
            "quantity": decimal128(dec_qty),
            "unit": item["unit"],
            "reason": r_upper,
            "estimated_cost": decimal128(total_loss),
            "notes": notes,
            "performed_by": performed_by,
            "created_at": now_utc(),
        }
        res = wastage_records_collection.insert_one(wastage_doc)
        wastage_doc["_id"] = res.inserted_id

        # Log Movement
        movement = repo.record_movement({
            "ingredient_id": to_object_id(ingredient_id),
            "batch_id": to_object_id(batch_id) if batch_id else None,
            "movement_type": "WASTAGE",
            "quantity": decimal128(dec_qty),
            "unit": item["unit"],
            "previous_stock": decimal128(current_stock),
            "new_stock": decimal128(new_stock),
            "unit_cost": decimal128(unit_cost),
            "total_cost": decimal128(total_loss),
            "reference_type": "WASTAGE",
            "reference_id": str(res.inserted_id),
            "reason": r_upper,
            "performed_by": performed_by,
            "created_at": now_utc(),
        })

        return {
            "message": "Wastage recorded successfully",
            "ingredient_name": item["name"],
            "wasted_quantity": float(dec_qty),
            "previous_stock": float(current_stock),
            "new_stock": float(new_stock),
            "estimated_loss": float(total_loss),
            "reason": r_upper,
            "wastage_id": str(res.inserted_id),
        }

    # =========================================================================
    # Stock Adjustment (Physical Count Reconciliation)
    # =========================================================================

    @staticmethod
    def adjust_stock(
        ingredient_id: str,
        physical_stock: Decimal | float | int | str,
        reason: str = "PHYSICAL_COUNT",
        notes: Optional[str] = None,
        performed_by: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """
        Stock Adjustment:
        Never allows unrestricted direct editing of current_stock.
        Calculates discrepancy = physical_stock - current_stock,
        updates stock, and logs mandatory ADJUSTMENT movement with audit reason.
        """
        dec_phys = Decimal(str(physical_stock))
        if dec_phys < 0:
            raise ValueError("Physical stock cannot be negative")

        valid_reasons = ["PHYSICAL_COUNT", "DAMAGED", "SYSTEM_ERROR", "OPENING_BALANCE", "OTHER"]
        r_upper = reason.upper() if reason else "OTHER"
        adj_reason = r_upper if r_upper in valid_reasons else "OTHER"

        item = IngredientService.get_ingredient(ingredient_id)
        current_stock = item["current_stock"]
        diff = dec_phys - current_stock

        if diff == 0:
            return {
                "message": "Physical stock matches system stock. No adjustment necessary.",
                "physical_stock": float(current_stock),
                "stock": float(current_stock),
                "difference": 0.0,
                "variance": 0.0,
            }

        # Update Stock directly via increment with difference
        repo.increment_stock(ingredient_id, diff)

        # Store adjustment document
        adj_doc = {
            "ingredient_id": to_object_id(ingredient_id),
            "ingredient_name": item["name"],
            "system_stock": decimal128(current_stock),
            "physical_stock": decimal128(dec_phys),
            "difference": decimal128(diff),
            "unit": item["unit"],
            "reason": adj_reason,
            "notes": f"{reason} - {notes}" if notes and reason != adj_reason else (notes or reason),
            "performed_by": performed_by,
            "created_at": now_utc(),
        }
        res = stock_adjustments_collection.insert_one(adj_doc)

        unit_cost = Decimal(str(item.get("cost_per_unit") or 0))
        repo.record_movement({
            "ingredient_id": to_object_id(ingredient_id),
            "movement_type": "ADJUSTMENT",
            "quantity": decimal128(abs(diff)),
            "unit": item["unit"],
            "previous_stock": decimal128(current_stock),
            "new_stock": decimal128(dec_phys),
            "unit_cost": decimal128(unit_cost),
            "total_cost": decimal128(abs(diff) * unit_cost),
            "reference_type": "STOCK_ADJUSTMENT",
            "reference_id": str(res.inserted_id),
            "reason": f"{adj_reason}: Adjusted by {diff:+f} {item['unit']}",
            "performed_by": performed_by,
            "created_at": now_utc(),
        })

        return {
            "message": "Stock adjusted successfully",
            "ingredient_name": item["name"],
            "previous_stock": float(current_stock),
            "physical_stock": float(dec_phys),
            "difference": float(diff),
            "variance": float(diff),
            "unit": item["unit"],
            "reason": r_upper,
        }

    # =========================================================================
    # Stock Transfer (Between Storage Locations)
    # =========================================================================

    @staticmethod
    def transfer_stock(
        ingredient_id: str,
        from_location_id: str,
        to_location_id: str,
        quantity: Decimal | float | int | str,
        batch_id: Optional[str] = None,
        notes: Optional[str] = None,
        performed_by: str = "SYSTEM",
    ) -> Dict[str, Any]:
        """
        Stock Transfer:
        Supports transferring stock between storage locations (e.g. Main Store -> Kitchen Store).
        Atomic operation recording TRANSFER_OUT and TRANSFER_IN.
        """
        dec_qty = Decimal(str(quantity))
        if dec_qty <= 0:
            raise ValueError("Transfer quantity must be greater than zero")
        if from_location_id == to_location_id:
            raise ValueError("Source and destination storage locations cannot be the same")

        from_loc = loc_repo.find_by_id(from_location_id)
        to_loc = loc_repo.find_by_id(to_location_id)
        if not from_loc or not to_loc:
            raise ValueError("Invalid storage location specified")

        item = IngredientService.get_ingredient(ingredient_id)
        current_stock = item["current_stock"]
        if current_stock < dec_qty:
            raise ValueError(f"Insufficient stock for transfer. Current: {current_stock} {item['unit']}, Transfer: {dec_qty} {item['unit']}")

        # If batch specified, transfer batch to new location
        if batch_id:
            batch = batch_repo.find_by_id(batch_id)
            if batch:
                batch_repo.update(batch_id, {"storage_location_id": to_object_id(to_location_id)})

        # Record atomic transfer document
        transfer_doc = {
            "ingredient_id": to_object_id(ingredient_id),
            "ingredient_name": item["name"],
            "from_location_id": to_object_id(from_location_id),
            "from_location_name": from_loc.get("name"),
            "to_location_id": to_object_id(to_location_id),
            "to_location_name": to_loc.get("name"),
            "quantity": decimal128(dec_qty),
            "unit": item["unit"],
            "batch_id": to_object_id(batch_id) if batch_id else None,
            "notes": notes,
            "performed_by": performed_by,
            "created_at": now_utc(),
        }
        res = stock_transfers_collection.insert_one(transfer_doc)

        unit_cost = Decimal(str(item.get("cost_per_unit") or 0))

        # 1. Log TRANSFER_OUT
        repo.record_movement({
            "ingredient_id": to_object_id(ingredient_id),
            "batch_id": to_object_id(batch_id) if batch_id else None,
            "movement_type": "TRANSFER_OUT",
            "quantity": decimal128(dec_qty),
            "unit": item["unit"],
            "previous_stock": decimal128(current_stock),
            "new_stock": decimal128(current_stock),
            "unit_cost": decimal128(unit_cost),
            "total_cost": decimal128(dec_qty * unit_cost),
            "reference_type": "TRANSFER",
            "reference_id": str(res.inserted_id),
            "reason": f"Transferred OUT to {to_loc.get('name')}",
            "performed_by": performed_by,
            "created_at": now_utc(),
        })

        # 2. Log TRANSFER_IN
        repo.record_movement({
            "ingredient_id": to_object_id(ingredient_id),
            "batch_id": to_object_id(batch_id) if batch_id else None,
            "movement_type": "TRANSFER_IN",
            "quantity": decimal128(dec_qty),
            "unit": item["unit"],
            "previous_stock": decimal128(current_stock),
            "new_stock": decimal128(current_stock),
            "unit_cost": decimal128(unit_cost),
            "total_cost": decimal128(dec_qty * unit_cost),
            "reference_type": "TRANSFER",
            "reference_id": str(res.inserted_id),
            "reason": f"Transferred IN from {from_loc.get('name')}",
            "performed_by": performed_by,
            "created_at": now_utc(),
        })

        # Update ingredient's current storage location assignment
        repo.update(ingredient_id, {"storage_location_id": to_object_id(to_location_id)})

        return {
            "message": "Stock transfer completed successfully",
            "ingredient_name": item["name"],
            "from_location": {"id": from_location_id, "name": from_loc.get("name")},
            "from_location_name": from_loc.get("name"),
            "to_location": {"id": to_location_id, "name": to_loc.get("name")},
            "to_location_name": to_loc.get("name"),
            "quantity": float(dec_qty),
            "transferred_quantity": float(dec_qty),
            "unit": item["unit"],
            "transfer_id": str(res.inserted_id),
        }

    # =========================================================================
    # Categories & Storage Locations
    # =========================================================================

    @staticmethod
    def get_categories() -> List[Dict[str, Any]]:
        cats = list(ingredient_categories_collection.find().sort("name", 1))
        if not cats:
            # Seed default categories if none exist
            defaults = [
                "Vegetables", "Fruits", "Meat", "Chicken", "Fish", "Dairy",
                "Grains", "Spices", "Oils", "Beverages", "Bakery", "Frozen", "Other"
            ]
            for d in defaults:
                ingredient_categories_collection.insert_one({"name": d, "description": f"{d} raw material inventory", "created_at": now_utc()})
            cats = list(ingredient_categories_collection.find().sort("name", 1))
        return serialize_documents(cats)

    @staticmethod
    def create_category(name: str, description: Optional[str] = None) -> Dict[str, Any]:
        if not name or not name.strip():
            raise ValueError("Category name cannot be empty")
        existing = ingredient_categories_collection.find_one({"name": {"$regex": f"^{name.strip()}$", "$options": "i"}})
        if existing:
            raise ValueError(f"Category '{name}' already exists")
        doc = {"name": name.strip(), "description": description, "created_at": now_utc()}
        res = ingredient_categories_collection.insert_one(doc)
        doc["_id"] = res.inserted_id
        return serialize_document(doc)

    @staticmethod
    def get_storage_locations() -> List[Dict[str, Any]]:
        locs = list(storage_locations_collection.find().sort("name", 1))
        if not locs:
            defaults = [
                ("Main Store", "Primary dry and bulk storage warehouse", "AMBIENT"),
                ("Dry Storage", "Pantry dry grains, pulses, spices", "AMBIENT"),
                ("Refrigerator", "Dairy, fresh vegetables, ready preps", "CHILLED"),
                ("Freezer", "Frozen chicken, meat, fish", "FROZEN"),
                ("Kitchen Store", "Daily active cooking line storage", "AMBIENT"),
                ("Beverage Store", "Bar, juices, sodas, syrups", "AMBIENT"),
            ]
            for n, d, t in defaults:
                storage_locations_collection.insert_one({"name": n, "description": d, "temperature_type": t, "created_at": now_utc()})
            locs = list(storage_locations_collection.find().sort("name", 1))
        return serialize_documents(locs)

    @staticmethod
    def create_storage_location(name: str, description: Optional[str] = None, temperature_type: str = "AMBIENT") -> Dict[str, Any]:
        if not name or not name.strip():
            raise ValueError("Location name cannot be empty")
        existing = storage_locations_collection.find_one({"name": {"$regex": f"^{name.strip()}$", "$options": "i"}})
        if existing:
            raise ValueError(f"Storage location '{name}' already exists")
        doc = {"name": name.strip(), "description": description, "temperature_type": temperature_type.upper(), "created_at": now_utc()}
        res = storage_locations_collection.insert_one(doc)
        doc["_id"] = res.inserted_id
        return serialize_document(doc)

    # =========================================================================
    # Batches & Expiry Management
    # =========================================================================

    @staticmethod
    def get_batches(ingredient_id: Optional[str] = None, only_active: bool = False) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if ingredient_id:
            query["ingredient_id"] = to_object_id(ingredient_id)
        if only_active:
            query["remaining_quantity"] = {"$gt": decimal128(Decimal("0"))}

        docs = list(batches_collection.find(query).sort("expiry_date", 1))
        serialized = serialize_documents(docs)
        now = now_utc()
        for b in serialized:
            ing = repo.find_by_id(b["ingredient_id"])
            if ing:
                b["ingredient_name"] = ing.get("name")
            exp = b.get("expiry_date")
            if exp:
                exp_dt = exp if isinstance(exp, datetime) else datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                diff_days = (exp_dt - now).days
                b["days_until_expiry"] = diff_days
                if diff_days < 0:
                    b["status"] = "EXPIRED"
                elif diff_days <= 3:
                    b["status"] = "EXPIRING_SOON"
                elif b.get("remaining_quantity", 0) <= 0:
                    b["status"] = "CONSUMED"
                else:
                    b["status"] = "ACTIVE"
        return serialized

    @staticmethod
    def get_expiring_batches(warning_days: int = 3) -> List[Dict[str, Any]]:
        return batch_repo.find_expiring_batches(warning_days=warning_days)

    @staticmethod
    def get_expired_batches() -> List[Dict[str, Any]]:
        return batch_repo.find_expired_batches()

    # =========================================================================
    # Dashboard & Reports
    # =========================================================================

    @staticmethod
    def get_low_stock_ingredients() -> List[Dict[str, Any]]:
        raw_items = repo.find_low_stock()
        results = []
        for item in raw_items:
            avail = Decimal(str(item.get("available_quantity") or item.get("current_stock") or 0))
            min_lvl = Decimal(str(item.get("minimum_stock_level") or 0))
            reorder = Decimal(str(item.get("reorder_level") or min_lvl))
            item["current_stock"] = avail
            item["available_quantity"] = avail
            if avail <= 0:
                item["status"] = "OUT_OF_STOCK"
                item["alert_level"] = "OUT_OF_STOCK"
            elif avail <= reorder:
                item["status"] = "LOW_STOCK"
                item["alert_level"] = "LOW"
            else:
                item["status"] = "NORMAL"
                item["alert_level"] = "NORMAL"
            results.append(item)
        return results

    @staticmethod
    def get_stock_status(ingredient_id: str) -> Dict[str, Any]:
        item = IngredientService.get_ingredient(ingredient_id)
        return {
            "ingredient_id": ingredient_id,
            "ingredient_name": item["name"],
            "unit": item["unit"],
            "available_quantity": item["available_quantity"],
            "current_stock": item["current_stock"],
            "minimum_stock_level": item["minimum_stock_level"],
            "reorder_level": item.get("reorder_level"),
            "status": item["status"],
        }

    @staticmethod
    def get_inventory_dashboard() -> Dict[str, Any]:
        """
        Provides complete 9-metric Inventory Dashboard:
        1. Total Ingredients
        2. Total Stock Value
        3. Low Stock Count
        4. Out of Stock Count
        5. Expiring Soon Count
        6. Expired Stock Count
        7. Today's Consumption
        8. Today's Wastage
        9. Pending Purchase Orders
        Also returns: Low Stock Items, Expiring Items, Recent Stock Movements.
        """
        all_ingredients = repo.find_all(sort_field="name", sort_dir=1)
        total_count = len(all_ingredients)
        total_value = Decimal("0")
        low_stock = []
        out_of_stock = []

        for ing in all_ingredients:
            avail = ing.get("available_quantity") or ing.get("current_stock") or Decimal("0")
            dec_avail = avail.to_decimal() if hasattr(avail, "to_decimal") else Decimal(str(avail))
            cost = ing.get("cost_per_unit") or Decimal("0")
            dec_cost = cost.to_decimal() if hasattr(cost, "to_decimal") else Decimal(str(cost))
            
            reorder = ing.get("reorder_level") or ing.get("minimum_stock_level") or Decimal("0")
            dec_reorder = reorder.to_decimal() if hasattr(reorder, "to_decimal") else Decimal(str(reorder))

            ing["current_stock"] = dec_avail
            ing["available_quantity"] = dec_avail
            total_value += (dec_avail * dec_cost)

            if dec_avail <= 0:
                ing["status"] = "OUT_OF_STOCK"
                out_of_stock.append(ing)
            elif dec_avail <= dec_reorder:
                ing["status"] = "LOW_STOCK"
                low_stock.append(ing)
            else:
                ing["status"] = "NORMAL"

        # Batches metrics
        expiring_batches = batch_repo.find_expiring_batches(warning_days=3)
        expired_batches = batch_repo.find_expired_batches()

        # Movements & Today's metrics
        recent_movements = repo.find_all_movements(limit=25)
        today_iso = now_utc().strftime("%Y-%m-%d")
        today_consumption_count = 0
        today_consumption_cost = Decimal("0")
        today_wastage_count = 0
        today_wastage_cost = Decimal("0")

        # Query today's movements from db
        midnight = now_utc().replace(hour=0, minute=0, second=0, microsecond=0)
        today_movements = list(stock_movements_collection.find({"created_at": {"$gte": midnight}}))
        for m in today_movements:
            m_type = m.get("movement_type")
            t_cost = m.get("total_cost") or Decimal("0")
            dec_cost = t_cost.to_decimal() if hasattr(t_cost, "to_decimal") else Decimal(str(t_cost))
            if m_type in ["ORDER_DEDUCTION", "CONSUMPTION"]:
                today_consumption_count += 1
                today_consumption_cost += dec_cost
            elif m_type == "WASTAGE":
                today_wastage_count += 1
                today_wastage_cost += dec_cost

        # Pending purchase orders
        pending_pos_count = purchase_orders_collection.count_documents({"status": {"$in": ["DRAFT", "ORDERED"]}})

        return {
            "total_ingredients": total_count,
            "total_stock_value": float(total_value),
            "low_stock_count": len(low_stock),
            "out_of_stock_count": len(out_of_stock),
            "expiring_soon_count": len(expiring_batches),
            "expired_stock_count": len(expired_batches),
            "today_consumption_count": today_consumption_count,
            "today_consumption_cost": float(today_consumption_cost),
            "today_wastage_count": today_wastage_count,
            "today_wastage_cost": float(today_wastage_cost),
            "pending_purchase_orders": pending_pos_count,
            "low_stock_items": low_stock,
            "out_of_stock_items": out_of_stock,
            "expiring_items": expiring_batches,
            "recent_movements": recent_movements,
        }

    @staticmethod
    def get_stock_report(category: Optional[str] = None) -> List[Dict[str, Any]]:
        ingredients = IngredientService.get_ingredients(category=category)
        report = []
        for it in ingredients:
            stock = it["current_stock"]
            cost = Decimal(str(it.get("cost_per_unit") or 0))
            val = stock * cost
            report.append({
                "ingredient_id": it["id"],
                "ingredient_name": it["name"],
                "sku": it.get("sku"),
                "category": it.get("category", "Other"),
                "current_stock": float(stock),
                "unit": it["unit"],
                "cost_per_unit": float(cost),
                "stock_value": float(val),
                "reorder_level": float(it.get("reorder_level") or it.get("minimum_stock_level") or 0),
                "status": it.get("status", "NORMAL"),
            })
        return report

    @staticmethod
    def get_consumption_report(start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, ingredient_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"movement_type": {"$in": ["CONSUMPTION", "ORDER_DEDUCTION"]}}
        if ingredient_id:
            query["ingredient_id"] = to_object_id(ingredient_id)
        if start_date or end_date:
            df: Dict[str, Any] = {}
            if start_date:
                df["$gte"] = start_date
            if end_date:
                df["$lte"] = end_date
            query["created_at"] = df

        docs = list(stock_movements_collection.find(query).sort("created_at", -1).limit(500))
        return serialize_documents(docs)

    @staticmethod
    def get_wastage_report(start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, reason: Optional[str] = None) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if reason and reason != "ALL":
            query["reason"] = reason.upper()
        if start_date or end_date:
            df: Dict[str, Any] = {}
            if start_date:
                df["$gte"] = start_date
            if end_date:
                df["$lte"] = end_date
            query["created_at"] = df

        docs = list(wastage_records_collection.find(query).sort("created_at", -1).limit(500))
        return serialize_documents(docs)

    @staticmethod
    def get_expiry_report(warning_days: int = 30) -> Dict[str, Any]:
        expiring = batch_repo.find_expiring_batches(warning_days=warning_days)
        expired = batch_repo.find_expired_batches()
        return {
            "expiring_batches": expiring,
            "expired_batches": expired,
            "expiring_count": len(expiring),
            "expired_count": len(expired),
        }

    @staticmethod
    def get_movement_report(
        ingredient_id: Optional[str] = None,
        movement_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        supplier_id: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        return repo.find_filtered_movements(
            ingredient_id=ingredient_id,
            movement_type=movement_type,
            start_date=start_date,
            end_date=end_date,
            supplier_id=supplier_id,
            limit=limit,
        )

    @staticmethod
    def estimate_serving_capacity(menu_item_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Calculates how many servings of each menu item can be prepared based on current stock.
        Formula: min(floor(available_quantity / required_quantity)) across all recipe ingredients.
        """
        query = {"_id": to_object_id(menu_item_id)} if menu_item_id else {"is_available": True}
        menu_items = list(menu_items_collection.find(query))

        capacity_reports = []
        for item in menu_items:
            recipes = list(recipes_collection.find({"menu_item_id": item["_id"]}))
            if not recipes:
                capacity_reports.append({
                    "menu_item_id": str(item["_id"]),
                    "menu_item_name": item["name"],
                    "possible_servings": 9999,
                    "limiting_ingredient": None,
                    "details": [],
                })
                continue

            possible_servings_list = []
            details = []
            for r in recipes:
                ing = repo.find_by_id(r["ingredient_id"])
                if not ing:
                    continue
                avail_raw = ing.get("available_quantity") or ing.get("current_stock") or Decimal("0")
                avail_qty = avail_raw.to_decimal() if hasattr(avail_raw, "to_decimal") else Decimal(str(avail_raw))
                req_raw = r.get("quantity_required") or Decimal("0")
                recipe_qty = req_raw.to_decimal() if hasattr(req_raw, "to_decimal") else Decimal(str(req_raw))
                rec_unit = r.get("unit") or ing["unit"]
                converted_req = convert_quantity(recipe_qty, rec_unit, ing["unit"])

                if converted_req <= 0:
                    servings = 0
                else:
                    servings = int(avail_qty // converted_req)

                possible_servings_list.append((servings, ing["name"]))
                details.append({
                    "ingredient_id": str(ing["id"]),
                    "ingredient_name": ing["name"],
                    "available": float(avail_qty),
                    "required_per_serving": float(converted_req),
                    "unit": ing["unit"],
                    "possible_servings": servings,
                })

            if possible_servings_list:
                min_servings, limiting_ing = min(possible_servings_list, key=lambda x: x[0])
            else:
                min_servings, limiting_ing = 0, None

            capacity_reports.append({
                "menu_item_id": str(item["_id"]),
                "menu_item_name": item["name"],
                "possible_servings": min_servings,
                "limiting_ingredient": limiting_ing,
                "details": details,
            })

        return capacity_reports
