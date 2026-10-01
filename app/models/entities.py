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
        description: Optional[str] = None,
        is_available: bool = True,
        is_vegetarian: bool = False,
        item_id: Optional[str] = None,
        image_url: Optional[str] = None,
    ):
        if Decimal(str(price)) < 0:
            raise ValueError("Price cannot be negative")
        if int(preparation_time) <= 0:
            raise ValueError("Preparation time must be greater than zero")

        self.id = item_id
        self.name = name.strip()
        self.price = Decimal(str(price))
        self.preparation_time = int(preparation_time)
        self.category_id = category_id
        self.description = description
        self.is_available = is_available
        self.is_vegetarian = is_vegetarian
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
            "preparation_time": self.preparation_time,
            "category_id": self.category_id,
            "description": self.description,
            "is_available": self.is_available,
            "is_vegetarian": self.is_vegetarian,
            "image_url": self.image_url,
        }


class OrderItem:
    """Represents an individual menu item line within an order."""

    def __init__(
        self,
        menu_item_id: str,
        item_name_snapshot: str,
        unit_price_snapshot: Decimal | float | int | str,
        quantity: int,
        special_instructions: Optional[str] = None,
        item_id: Optional[str] = None,
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
        self.quantity = int(quantity)
        self.special_instructions = special_instructions
        self.item_total = self.calculate_total()

    def calculate_total(self) -> Decimal:
        return self.unit_price_snapshot * Decimal(self.quantity)

    def update_quantity(self, new_quantity: int) -> None:
        if new_quantity <= 0:
            raise ValueError("Order item quantity must be greater than zero")
        self.quantity = int(new_quantity)
        self.item_total = self.calculate_total()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "menu_item_id": self.menu_item_id,
            "item_name_snapshot": self.item_name_snapshot,
            "unit_price_snapshot": self.unit_price_snapshot,
            "quantity": self.quantity,
            "special_instructions": self.special_instructions,
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
        self.tax_amount = Decimal("0")
        self.total_amount = Decimal("0")

    def add_item(self, item: OrderItem) -> None:
        if self.status != "DRAFT":
            raise ValueError("Items can only be added to DRAFT orders")
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

    def calculate_subtotal(self) -> Decimal:
        return sum((item.item_total for item in self.items), Decimal("0"))

    def calculate_tax(self, subtotal: Decimal) -> Decimal:
        return (subtotal * self.TAX_RATE).quantize(Decimal("0.01"))

    def recalculate(self) -> None:
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
        if self.status in ["SERVED", "COMPLETED"]:
            return False, "Served/Completed orders cannot be cancelled directly. Request a refund."
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
        self.cost_per_unit = cost
        self.supplier_name = supplier_name
        self.is_active = is_active

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
        if self.available_quantity <= self.minimum_stock_level:
            return "CRITICAL"
        if self.available_quantity <= self.minimum_stock_level * Decimal("1.5"):
            return "LOW"
        return "NORMAL"

    def calculate_possible_servings(self, required_per_serving: Decimal | float | int | str) -> int:
        req = Decimal(str(required_per_serving))
        if req <= 0:
            return 0
        return int(self.available_quantity // req)


class Recipe:
    """Maps a menu item to its required ingredient quantities."""

    def __init__(
        self,
        menu_item_id: str,
        ingredient_id: str,
        quantity_required: Decimal | float | int | str,
        recipe_id: Optional[str] = None,
        unit: Optional[str] = None,
    ):
        qty = Decimal(str(quantity_required))
        if qty <= 0:
            raise ValueError("Quantity required in recipe must be greater than zero")

        self.id = recipe_id
        self.menu_item_id = menu_item_id
        self.ingredient_id = ingredient_id
        self.quantity_required = qty
        self.unit = unit

    def calculate_required_quantity(self, multiplier: int) -> Decimal:
        if multiplier <= 0:
            raise ValueError("Multiplier must be positive")
        return self.quantity_required * Decimal(multiplier)


class StockMovement:
    """Represents an audit movement for raw material inventory."""

    VALID_TYPES = [
        "PURCHASE",
        "MANUAL_ADD",
        "ORDER_DEDUCTION",
        "WASTAGE",
        "ADJUSTMENT",
        "RETURN",
        "ORDER_RETURN",
        "MANUAL_ADJUSTMENT",
    ]

    def __init__(
        self,
        ingredient_id: str,
        movement_type: str,
        quantity: Decimal | float | int | str,
        unit: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        created_by: Optional[str] = "SYSTEM",
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
        self.reference_type = reference_type
        self.reference_id = reference_id
        self.created_by = created_by


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
