"""
OOP Domain Entity Classes for Restaurant Order & Kitchen Operations System.
Encapsulates domain logic, calculations, invariants, and state transitions
as specified in Section 21 & 22 of the system architecture.
"""

from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any


class MenuItem:
    """Represents a food or beverage item on the restaurant menu."""

    def __init__(
        self,
        name: str,
        price: Decimal | float | int | str,
        preparation_time: int,
        category_id: Optional[str] = None,
        subcategory_id: Optional[str] = None,
        description: Optional[str] = None,
        is_available: bool = True,
        is_vegetarian: bool = False,
        item_id: Optional[str] = None,
        image_url: Optional[str] = None,
        type: Optional[str] = None,
        food_type: Optional[str] = None,
        base_price: Optional[Decimal | float | int | str] = None,
        discount: Optional[Decimal | float | int | str] = 0,
        tax: Optional[Decimal | float | int | str] = 0,
        final_price: Optional[Decimal | float | int | str] = None,
        is_featured: bool = False,
        is_active: bool = True,
        display_order: int = 0,
        spicy_level: Optional[str] = None,
        serving_size: Optional[str] = None,
        tags: Optional[List[str]] = None,
        inventory_tracking_enabled: bool = True,
    ):
        if Decimal(str(price)) < 0:
            raise ValueError("Price cannot be negative")
        if int(preparation_time) <= 0:
            raise ValueError("Preparation time must be greater than zero")

        self.id = item_id
        self.name = name.strip()
        self.price = Decimal(str(price))
        self.base_price = Decimal(str(base_price)) if base_price is not None else self.price
        self.discount = Decimal(str(discount)) if discount is not None else Decimal("0")
        self.tax = Decimal(str(tax)) if tax is not None else Decimal("0")
        if final_price is not None:
            self.final_price = Decimal(str(final_price))
        else:
            calc_final = (self.base_price - self.discount) + self.tax
            self.final_price = max(Decimal("0"), calc_final)

        self.preparation_time = int(preparation_time)
        self.category_id = category_id
        self.subcategory_id = subcategory_id
        self.description = description
        self.is_available = is_available
        self.is_active = is_active
        self.is_featured = bool(is_featured)
        self.display_order = int(display_order)
        self.spicy_level = spicy_level
        self.serving_size = serving_size
        self.tags = tags or []
        self.inventory_tracking_enabled = bool(inventory_tracking_enabled)
        
        # Determine type & is_vegetarian compatibility
        resolved_type = food_type or type
        if resolved_type:
            norm_type = resolved_type.strip()
            if norm_type.lower() in ["veg", "vegetarian"]:
                self.type = "Veg"
                self.food_type = "Veg"
                self.is_vegetarian = True
            elif norm_type.lower() in ["non-veg", "non-vegetarian", "nonveg"]:
                self.type = "Non-Veg"
                self.food_type = "Non-Veg"
                self.is_vegetarian = False
            elif norm_type.lower() in ["egg", "eggetarian"]:
                self.type = "Egg"
                self.food_type = "Non-Veg"
                self.is_vegetarian = False
            elif norm_type.lower() in ["beverage", "beverages", "drink", "drinks"]:
                self.type = "Beverage"
                self.food_type = "Veg"
                self.is_vegetarian = True
            else:
                self.type = norm_type
                self.food_type = norm_type
                self.is_vegetarian = is_vegetarian
        else:
            self.is_vegetarian = is_vegetarian
            self.type = "Veg" if is_vegetarian else "Non-Veg"
            self.food_type = self.type

        self.image_url = image_url

    def update_price(self, new_price: Decimal | float | int | str) -> None:
        dec_price = Decimal(str(new_price))
        if dec_price < 0:
            raise ValueError("Price cannot be negative")
        self.price = dec_price

    def set_availability(self, available: bool) -> None:
        self.is_available = bool(available)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "price": self.price,
            "base_price": self.base_price,
            "discount": self.discount,
            "tax": self.tax,
            "final_price": self.final_price,
            "preparation_time": self.preparation_time,
            "category_id": self.category_id,
            "subcategory_id": self.subcategory_id,
            "description": self.description,
            "is_available": self.is_available,
            "is_active": self.is_active,
            "is_featured": self.is_featured,
            "display_order": self.display_order,
            "spicy_level": self.spicy_level,
            "serving_size": self.serving_size,
            "tags": self.tags,
            "is_vegetarian": self.is_vegetarian,
            "type": self.type,
            "food_type": self.food_type,
            "image_url": self.image_url,
            "inventory_tracking_enabled": self.inventory_tracking_enabled,
        }


class OrderItem:
    """Represents an individual menu item line within an order."""

    VALID_STATUSES = [
        "PENDING",
        "CONFIRMED",
        "PREPARING",
        "READY",
        "DELIVERED",
        "SERVED",
        "CANCELLED",
    ]

    def __init__(
        self,
        menu_item_id: str,
        item_name_snapshot: str,
        unit_price_snapshot: Decimal | float | int | str,
        quantity: int,
        special_instructions: Optional[str] = None,
        item_id: Optional[str] = None,
        status: str = "PENDING",
        batch_number: int = 1,
        is_additional: bool = False,
        added_at: Optional[datetime] = None,
        inventory_deducted: bool = False,
    ):
        if quantity <= 0:
            raise ValueError("Order item quantity must be greater than zero")
        unit_price = Decimal(str(unit_price_snapshot))
        if unit_price < 0:
            raise ValueError("Item price snapshot cannot be negative")

        self.id = item_id
        self.menu_item_id = menu_item_id
        self.item_name_snapshot = item_name_snapshot
        self.unit_price_snapshot = unit_price
        self.price_at_addition = unit_price
        self.quantity = int(quantity)
        self.special_instructions = special_instructions
        self.status = status.upper() if status else "PENDING"
        self.batch_number = int(batch_number)
        self.is_additional = bool(is_additional)
        self.added_at = added_at or datetime.now(timezone.utc)
        self.inventory_deducted = bool(inventory_deducted)
        self.item_total = self.calculate_total()

    def calculate_total(self) -> Decimal:
        return self.unit_price_snapshot * Decimal(self.quantity)

    def update_quantity(self, new_quantity: int) -> None:
        if new_quantity <= 0:
            raise ValueError("Order item quantity must be greater than zero")
        self.quantity = int(new_quantity)
        self.item_total = self.calculate_total()

    def update_status(self, new_status: str) -> None:
        st_upper = new_status.upper()
        if st_upper not in self.VALID_STATUSES:
            raise ValueError(f"Invalid order item status: {st_upper}")
        self.status = st_upper

    def to_dict(self) -> Dict[str, Any]:
        return {
            "menu_item_id": self.menu_item_id,
            "item_name_snapshot": self.item_name_snapshot,
            "unit_price_snapshot": self.unit_price_snapshot,
            "price_at_addition": self.price_at_addition,
            "quantity": self.quantity,
            "special_instructions": self.special_instructions,
            "status": self.status,
            "batch_number": self.batch_number,
            "is_additional": self.is_additional,
            "added_at": self.added_at,
            "inventory_deducted": self.inventory_deducted,
            "item_total": self.item_total,
        }


class Order:
    """Represents a customer order throughout its entire lifecycle."""

    TAX_RATE = Decimal("0.05")  # Standard 5% restaurant tax policy

    VALID_STATUSES = [
        "DRAFT",
        "PLACED",
        "CONFIRMED",
        "SENT_TO_KITCHEN",
        "PREPARING",
        "READY",
        "SERVED",
        "DELIVERED",
        "PARTIALLY_DELIVERED",
        "COMPLETED",
        "CANCELLED",
        "REFUND_PENDING",
        "REFUNDED",
    ]

    def __init__(
        self,
        order_type: str = "DINE_IN",
        customer_id: Optional[str] = None,
        table_id: Optional[str] = None,
        created_by: str = "WAITER",
        order_number: Optional[str] = None,
        order_id: Optional[str] = None,
    ):
        self.id = order_id
        self.order_number = order_number
        self.order_type = order_type.upper()
        self.customer_id = customer_id
        self.table_id = table_id
        self.created_by = created_by
        self.status = "DRAFT"
        self.items: List[OrderItem] = []
        self.discount_amount = Decimal("0")
        self.subtotal = Decimal("0")
        self.previous_item_total = Decimal("0")
        self.new_item_total = Decimal("0")
        self.tax_amount = Decimal("0")
        self.total_amount = Decimal("0")

    def add_item(self, item: OrderItem, allow_delivered: bool = False) -> None:
        allowed_statuses = ["DRAFT"]
        if allow_delivered:
            allowed_statuses.extend(["DELIVERED", "SERVED", "COMPLETED", "READY", "PREPARING", "CONFIRMED", "PLACED"])
        if self.status not in allowed_statuses:
            raise ValueError(f"Items can only be added to DRAFT or active/delivered orders, not {self.status}")
        self.items.append(item)
        self.recalculate()

    def add_additional_item(self, item: OrderItem) -> None:
        """Appends a new order item to an existing order (even after delivery)."""
        if self.status in ["CANCELLED", "REFUNDED"]:
            raise ValueError(f"Cannot add items to {self.status} orders")
        item.is_additional = True
        self.items.append(item)
        self.recalculate()

    def remove_item(self, menu_item_id: str) -> None:
        if self.status != "DRAFT":
            raise ValueError("Items can only be removed from DRAFT orders")
        self.items = [i for i in self.items if str(i.menu_item_id) != str(menu_item_id)]
        self.recalculate()

    def apply_discount(self, discount: Decimal | float | int | str) -> None:
        dec_discount = Decimal(str(discount))
        if dec_discount < 0:
            raise ValueError("Discount cannot be negative")
        self.discount_amount = dec_discount
        self.recalculate()

    def calculate_previous_subtotal(self) -> Decimal:
        """Sum of original/previous items (batch_number == 1 or not is_additional)."""
        return sum(
            (item.item_total for item in self.items if not getattr(item, "is_additional", False) and getattr(item, "batch_number", 1) == 1),
            Decimal("0"),
        )

    def calculate_additional_subtotal(self) -> Decimal:
        """Sum of newly added items (batch_number > 1 or is_additional is True)."""
        return sum(
            (item.item_total for item in self.items if getattr(item, "is_additional", False) or getattr(item, "batch_number", 1) > 1),
            Decimal("0"),
        )

    def calculate_subtotal(self) -> Decimal:
        return sum((item.item_total for item in self.items), Decimal("0"))

    def calculate_tax(self, subtotal: Decimal) -> Decimal:
        return (subtotal * self.TAX_RATE).quantize(Decimal("0.01"))

    def calculate_overall_status(self) -> str:
        """
        Calculates the order's overall status based on its individual item statuses.
        - If all active items are DELIVERED/SERVED -> DELIVERED
        - If all active items are READY -> READY
        - If any active item is PREPARING -> PREPARING
        - If some are DELIVERED and some are PENDING/PREPARING -> PREPARING / PENDING
        """
        if not self.items:
            return self.status

        active_items = [i for i in self.items if i.status != "CANCELLED"]
        if not active_items:
            return "CANCELLED"

        statuses = [i.status for i in active_items]
        delivered_count = sum(1 for s in statuses if s in ["DELIVERED", "SERVED"])

        if delivered_count == len(active_items):
            return "DELIVERED"
        if any(s == "PREPARING" for s in statuses):
            return "PREPARING"
        if all(s == "READY" for s in statuses):
            return "READY"
        if any(s == "PENDING" for s in statuses):
            if delivered_count > 0:
                # Some items delivered, newly added items are in progress
                return "PREPARING"
            return "PENDING"
        return self.status

    def recalculate(self) -> None:
        self.previous_item_total = self.calculate_previous_subtotal()
        self.new_item_total = self.calculate_additional_subtotal()
        self.subtotal = self.calculate_subtotal()
        taxable = max(Decimal("0"), self.subtotal - self.discount_amount)
        self.tax_amount = self.calculate_tax(taxable)
        total = taxable + self.tax_amount
        self.total_amount = max(Decimal("0"), total.quantize(Decimal("0.01")))

    def can_confirm(self) -> bool:
        return self.status in ["DRAFT", "PLACED"] and len(self.items) > 0

    def can_cancel(self, role: str = "CUSTOMER") -> tuple[bool, str]:
        """
        Evaluates cancellation eligibility according to business policy:
        - DRAFT, PLACED: Always allowed
        - CONFIRMED, SENT_TO_KITCHEN: Allowed (ingredients returned to stock)
        - PREPARING: Allowed only with Manager/Admin approval (ingredients not returned)
        - READY: Restricted (disallowed without manager override)
        - SERVED, COMPLETED: Not allowed via standard cancellation (requires refund)
        """
        role_upper = role.upper()
        if self.status in ["DRAFT", "PLACED"]:
            return True, "Cancellation allowed."
        if self.status in ["CONFIRMED", "SENT_TO_KITCHEN"]:
            return True, "Cancellation allowed; inventory will be returned."
        if self.status == "PREPARING":
            if role_upper in ["ADMIN", "MANAGER", "RESTAURANT_MANAGER"]:
                return True, "Manager approved cancellation for order in preparation."
            return False, "Cancellation of preparing orders requires Manager approval."
        if self.status == "READY":
            if role_upper in ["ADMIN", "MANAGER"]:
                return True, "Manager approved cancellation for ready order."
            return False, "Order is already prepared and ready. Cancellation restricted."
        if self.status in ["SERVED", "DELIVERED", "COMPLETED"]:
            return False, "Served/Delivered/Completed orders cannot be cancelled directly. Request a refund."
        return False, f"Order in status {self.status} cannot be cancelled."


class Ingredient:
    """Represents raw material in the inventory."""

    def __init__(
        self,
        name: str,
        unit: str,
        available_quantity: Decimal | float | int | str,
        minimum_stock_level: Decimal | float | int | str,
        cost_per_unit: Decimal | float | int | str,
        supplier_name: Optional[str] = None,
        is_active: bool = True,
        ingredient_id: Optional[str] = None,
        sku: Optional[str] = None,
        category: Optional[str] = None,
        category_id: Optional[str] = None,
        maximum_stock: Optional[Decimal | float | int | str] = None,
        reorder_level: Optional[Decimal | float | int | str] = None,
        supplier_id: Optional[str] = None,
        storage_location_id: Optional[str] = None,
        storage_location_name: Optional[str] = None,
    ):
        qty = Decimal(str(available_quantity))
        min_stock = Decimal(str(minimum_stock_level))
        cost = Decimal(str(cost_per_unit))

        if qty < 0:
            raise ValueError("Available quantity cannot be negative")
        if min_stock < 0:
            raise ValueError("Minimum stock level cannot be negative")
        if cost < 0:
            raise ValueError("Cost per unit cannot be negative")

        self.id = ingredient_id
        self.name = name.strip()
        self.unit = unit.upper()
        self.available_quantity = qty
        self.minimum_stock_level = min_stock
        self.reorder_level = Decimal(str(reorder_level)) if reorder_level is not None else min_stock
        self.maximum_stock = Decimal(str(maximum_stock)) if maximum_stock is not None else None
        self.cost_per_unit = cost
        self.supplier_name = supplier_name
        self.supplier_id = supplier_id
        self.sku = sku
        self.category = category or "Other"
        self.category_id = category_id
        self.storage_location_id = storage_location_id
        self.storage_location_name = storage_location_name
        self.is_active = is_active

    @property
    def current_stock(self) -> Decimal:
        return self.available_quantity

    @current_stock.setter
    def current_stock(self, val: Decimal | float | int | str) -> None:
        self.available_quantity = Decimal(str(val))

    def deduct_stock(self, quantity: Decimal | float | int | str) -> Decimal:
        qty_to_deduct = Decimal(str(quantity))
        if qty_to_deduct <= 0:
            raise ValueError("Quantity to deduct must be greater than zero")
        if self.available_quantity < qty_to_deduct:
            raise ValueError(
                f"Insufficient stock for {self.name}. Available: {self.available_quantity}, Required: {qty_to_deduct}"
            )
        self.available_quantity -= qty_to_deduct
        return self.available_quantity

    def add_stock(self, quantity: Decimal | float | int | str) -> Decimal:
        qty_to_add = Decimal(str(quantity))
        if qty_to_add <= 0:
            raise ValueError("Quantity to add must be greater than zero")
        self.available_quantity += qty_to_add
        return self.available_quantity

    def get_alert_level(self) -> str:
        if self.available_quantity <= 0:
            return "OUT_OF_STOCK"
        threshold = self.reorder_level if self.reorder_level is not None else self.minimum_stock_level
        if self.available_quantity <= threshold:
            return "LOW_STOCK"
        if self.available_quantity <= self.minimum_stock_level:
            return "CRITICAL"
        return "NORMAL"

    def calculate_possible_servings(self, required_per_serving: Decimal | float | int | str) -> int:
        req = Decimal(str(required_per_serving))
        if req <= 0:
            return 0
        return int(self.available_quantity // req)


class IngredientBatch:
    """Represents a lot/batch of raw materials for expiry tracking and FEFO."""

    VALID_STATUSES = ["ACTIVE", "EXPIRING_SOON", "EXPIRED", "CONSUMED"]

    def __init__(
        self,
        ingredient_id: str,
        batch_number: str,
        quantity: Decimal | float | int | str,
        remaining_quantity: Decimal | float | int | str,
        unit_cost: Decimal | float | int | str,
        received_date: datetime,
        expiry_date: datetime,
        batch_id: Optional[str] = None,
        unit: Optional[str] = None,
        supplier_id: Optional[str] = None,
        purchase_order_id: Optional[str] = None,
        storage_location_id: Optional[str] = None,
        status: str = "ACTIVE",
    ):
        qty = Decimal(str(quantity))
        rem = Decimal(str(remaining_quantity))
        cost = Decimal(str(unit_cost))
        if qty < 0 or rem < 0:
            raise ValueError("Batch quantity cannot be negative")
        if cost < 0:
            raise ValueError("Unit cost cannot be negative")

        self.id = batch_id
        self.ingredient_id = ingredient_id
        self.batch_number = batch_number
        self.quantity = qty
        self.remaining_quantity = rem
        self.unit = unit
        self.unit_cost = cost
        self.received_date = received_date
        self.expiry_date = expiry_date
        self.supplier_id = supplier_id
        self.purchase_order_id = purchase_order_id
        self.storage_location_id = storage_location_id
        self.status = status.upper() if status else "ACTIVE"

    def compute_status(self, warning_days: int = 3) -> str:
        if self.remaining_quantity <= 0:
            self.status = "CONSUMED"
            return self.status

        now = datetime.now(timezone.utc)
        # Normalize timezone
        exp = self.expiry_date
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        if exp < now:
            self.status = "EXPIRED"
        elif (exp - now).days <= warning_days:
            self.status = "EXPIRING_SOON"
        else:
            self.status = "ACTIVE"

        return self.status

    def is_usable_for_kitchen(self) -> bool:
        """Expired or consumed batches cannot be used for kitchen consumption."""
        st = self.compute_status()
        return st in ["ACTIVE", "EXPIRING_SOON"] and self.remaining_quantity > 0


class Recipe:
    """Maps a menu item to its required ingredient quantities."""

    def __init__(
        self,
        menu_item_id: str,
        ingredient_id: str,
        quantity_required: Decimal | float | int | str,
        recipe_id: Optional[str] = None,
        unit: Optional[str] = None,
        is_optional: bool = False,
    ):
        qty = Decimal(str(quantity_required))
        if qty <= 0:
            raise ValueError("Quantity required in recipe must be greater than zero")

        self.id = recipe_id
        self.menu_item_id = menu_item_id
        self.ingredient_id = ingredient_id
        self.quantity_required = qty
        self.unit = unit
        self.is_optional = bool(is_optional)

    def calculate_required_quantity(self, multiplier: int) -> Decimal:
        if multiplier <= 0:
            raise ValueError("Multiplier must be positive")
        return self.quantity_required * Decimal(multiplier)


class StockMovement:
    """Represents an audit ledger movement for raw material inventory."""

    VALID_TYPES = [
        "PURCHASE",
        "RECEIVE",
        "CONSUMPTION",
        "ORDER_DEDUCTION",
        "WASTAGE",
        "TRANSFER_IN",
        "TRANSFER_OUT",
        "ADJUSTMENT",
        "RETURN",
        "ORDER_RETURN",
        "MANUAL_ADD",
        "MANUAL_ADJUSTMENT",
    ]

    def __init__(
        self,
        ingredient_id: str,
        movement_type: str,
        quantity: Decimal | float | int | str,
        unit: Optional[str] = None,
        previous_stock: Optional[Decimal | float | int | str] = None,
        new_stock: Optional[Decimal | float | int | str] = None,
        unit_cost: Optional[Decimal | float | int | str] = None,
        total_cost: Optional[Decimal | float | int | str] = None,
        batch_id: Optional[str] = None,
        supplier_id: Optional[str] = None,
        purchase_order_id: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        reason: Optional[str] = None,
        performed_by: Optional[str] = "SYSTEM",
        movement_id: Optional[str] = None,
    ):
        qty = Decimal(str(quantity))
        if qty <= 0:
            raise ValueError("Movement quantity must be greater than zero")
        m_type = movement_type.upper()
        if m_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid movement type: {m_type}")

        self.id = movement_id
        self.ingredient_id = ingredient_id
        self.movement_type = m_type
        self.quantity = qty
        self.unit = unit
        self.previous_stock = Decimal(str(previous_stock)) if previous_stock is not None else None
        self.new_stock = Decimal(str(new_stock)) if new_stock is not None else None
        self.unit_cost = Decimal(str(unit_cost)) if unit_cost is not None else None
        self.total_cost = Decimal(str(total_cost)) if total_cost is not None else None
        self.batch_id = batch_id
        self.supplier_id = supplier_id
        self.purchase_order_id = purchase_order_id
        self.reference_type = reference_type
        self.reference_id = reference_id
        self.reason = reason
        self.performed_by = performed_by


class Supplier:
    """Represents a vendor/supplier for raw materials."""

    def __init__(
        self,
        name: str,
        contact_number: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None,
        tax_id_gst: Optional[str] = None,
        is_active: bool = True,
        supplier_id: Optional[str] = None,
    ):
        if not name or not name.strip():
            raise ValueError("Supplier name cannot be empty")
        self.id = supplier_id
        self.name = name.strip()
        self.contact_number = contact_number
        self.email = email
        self.address = address
        self.tax_id_gst = tax_id_gst
        self.is_active = is_active


class PurchaseOrder:
    """Represents a procurement order placed with a supplier."""

    VALID_STATUSES = ["DRAFT", "ORDERED", "PARTIALLY_RECEIVED", "RECEIVED", "CANCELLED"]

    def __init__(
        self,
        po_number: str,
        supplier_id: str,
        items: List[Dict[str, Any]],
        total_expected_cost: Decimal | float | int | str = 0,
        status: str = "DRAFT",
        order_date: Optional[datetime] = None,
        expected_delivery_date: Optional[datetime] = None,
        po_id: Optional[str] = None,
    ):
        st = status.upper()
        if st not in self.VALID_STATUSES:
            raise ValueError(f"Invalid purchase order status: {st}")
        self.id = po_id
        self.po_number = po_number
        self.supplier_id = supplier_id
        self.items = items or []
        self.total_expected_cost = Decimal(str(total_expected_cost))
        self.status = st
        self.order_date = order_date or datetime.now(timezone.utc)
        self.expected_delivery_date = expected_delivery_date



class RestaurantTable:
    """Represents a dining table and its availability status."""

    VALID_STATUSES = ["AVAILABLE", "OCCUPIED", "RESERVED", "CLEANING", "OUT_OF_SERVICE"]

    def __init__(
        self,
        table_number: str,
        capacity: int,
        location: str = "Ground Floor",
        status: str = "AVAILABLE",
        is_active: bool = True,
        table_id: Optional[str] = None,
    ):
        if capacity <= 0:
            raise ValueError("Table capacity must be positive")
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid table status: {status}")

        self.id = table_id
        self.table_number = table_number.strip()
        self.capacity = int(capacity)
        self.location = location
        self.status = status
        self.is_active = is_active

    def can_accommodate(self, guests: int) -> bool:
        return guests <= self.capacity

    def occupy(self) -> None:
        if self.status == "OCCUPIED":
            raise ValueError(f"Table {self.table_number} is already occupied")
        if not self.is_active:
            raise ValueError(f"Table {self.table_number} is out of service/inactive")
        self.status = "OCCUPIED"

    def release(self) -> None:
        self.status = "AVAILABLE"


class Reservation:
    """Represents a table reservation with time-overlap verification."""

    VALID_STATUSES = ["REQUESTED", "CONFIRMED", "SEATED", "COMPLETED", "CANCELLED", "NO_SHOW"]

    def __init__(
        self,
        customer_id: str,
        table_id: str,
        reservation_date: str,
        start_time: str,
        end_time: str,
        guest_count: int,
        status: str = "REQUESTED",
        contact_number: Optional[str] = None,
        reservation_id: Optional[str] = None,
    ):
        if guest_count <= 0:
            raise ValueError("Guest count must be positive")
        if start_time >= end_time:
            raise ValueError("start_time must be earlier than end_time")

        self.id = reservation_id
        self.customer_id = customer_id
        self.table_id = table_id
        self.reservation_date = reservation_date
        self.start_time = start_time
        self.end_time = end_time
        self.guest_count = guest_count
        self.status = status
        self.contact_number = contact_number

    @staticmethod
    def check_overlap(
        start1: str, end1: str, start2: str, end2: str
    ) -> bool:
        """
        Overlap logic: new_start < existing_end and new_end > existing_start
        """
        return start1 < end2 and end1 > start2


class KitchenTicket:
    """Represents the preparation ticket sent to the kitchen."""

    VALID_STATUSES = ["QUEUED", "ACCEPTED", "PREPARING", "READY", "HANDED_OVER", "CANCELLED"]

    def __init__(
        self,
        order_id: str,
        priority: str = "NORMAL",
        ticket_id: Optional[str] = None,
    ):
        self.id = ticket_id
        self.order_id = order_id
        self.priority = priority
        self.status = "QUEUED"
        self.assigned_staff_id = None
        self.started_at = None
        self.ready_at = None
        self.completed_at = None

    def start_preparation(self, staff_id: Optional[str] = None) -> None:
        if self.status == "CANCELLED":
            raise ValueError("Cannot prepare a cancelled ticket")
        self.status = "PREPARING"
        self.started_at = datetime.now(timezone.utc)
        if staff_id:
            self.assigned_staff_id = staff_id

    def mark_ready(self) -> None:
        if self.status not in ["ACCEPTED", "PREPARING", "QUEUED"]:
            raise ValueError(f"Cannot mark ready from status {self.status}")
        self.status = "READY"
        self.ready_at = datetime.now(timezone.utc)

    def handover(self) -> None:
        if self.status != "READY":
            raise ValueError("Cannot handover order that is not ready")
        self.status = "HANDED_OVER"
        self.completed_at = datetime.now(timezone.utc)


class Invoice:
    """Represents a customer bill."""

    def __init__(
        self,
        order_id: str,
        invoice_number: str,
        subtotal: Decimal,
        discount_amount: Decimal,
        tax_amount: Decimal,
        total_amount: Decimal,
        status: str = "UNPAID",
        invoice_id: Optional[str] = None,
    ):
        self.id = invoice_id
        self.order_id = order_id
        self.invoice_number = invoice_number
        self.subtotal = Decimal(str(subtotal))
        self.discount_amount = Decimal(str(discount_amount))
        self.tax_amount = Decimal(str(tax_amount))
        self.total_amount = Decimal(str(total_amount))
        self.status = status

    def mark_paid(self) -> None:
        self.status = "PAID"
