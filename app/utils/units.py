"""
Unit normalization and conversion helper for restaurant inventory.
Supports standard kitchen conversions (KG <-> G, L <-> ML, PCS).
"""

from decimal import Decimal


def convert_quantity(quantity: Decimal | float | int | str, from_unit: str, to_unit: str) -> Decimal:
    """
    Converts quantity from recipe unit to inventory stock unit.
    E.g., 250 grams to KG -> 0.25 KG.
    """
    qty = Decimal(str(quantity))
    f_unit = from_unit.strip().upper()
    t_unit = to_unit.strip().upper()

    if f_unit == t_unit:
        return qty

    # Weight conversions
    weight_to_grams = {
        "G": Decimal("1"),
        "GRAM": Decimal("1"),
        "GRAMS": Decimal("1"),
        "GM": Decimal("1"),
        "KG": Decimal("1000"),
        "KILOGRAM": Decimal("1000"),
        "KILOGRAMS": Decimal("1000"),
    }

    if f_unit in weight_to_grams and t_unit in weight_to_grams:
        in_grams = qty * weight_to_grams[f_unit]
        return in_grams / weight_to_grams[t_unit]

    # Volume conversions
    volume_to_ml = {
        "ML": Decimal("1"),
        "MILLILITER": Decimal("1"),
        "MILLILITERS": Decimal("1"),
        "L": Decimal("1000"),
        "LITER": Decimal("1000"),
        "LITERS": Decimal("1000"),
        "LITRE": Decimal("1000"),
        "LITRES": Decimal("1000"),
        "LTR": Decimal("1000"),
    }

    if f_unit in volume_to_ml and t_unit in volume_to_ml:
        in_ml = qty * volume_to_ml[f_unit]
        return in_ml / volume_to_ml[t_unit]

    # Discrete counts (PCS, PACKET)
    count_units = {
        "PIECE": "PIECE",
        "PIECES": "PIECE",
        "PCS": "PIECE",
        "PC": "PIECE",
        "PACKET": "PACKET",
        "PACKETS": "PACKET",
        "PKT": "PACKET",
    }
    if f_unit in count_units and t_unit in count_units:
        if count_units[f_unit] == count_units[t_unit]:
            return qty

    # Direct fallback if identical or custom units
    return qty
