"""
Unit normalization, conversion, and validation helper for restaurant inventory.
Supports standard restaurant units:
- Weight: kg, g
- Volume: litre, ml
- Count: piece, dozen, packet, box
"""

from decimal import Decimal
from typing import Set

SUPPORTED_UNITS = [
    "kg",
    "g",
    "litre",
    "ml",
    "piece",
    "dozen",
    "packet",
    "box",
]

# Normalization dictionary mapping various aliases to canonical units
UNIT_ALIASES = {
    # Weight
    "KG": "KG",
    "KILOGRAM": "KG",
    "KILOGRAMS": "KG",
    "KGS": "KG",
    "G": "G",
    "GM": "G",
    "GMS": "G",
    "GRAM": "G",
    "GRAMS": "G",
    # Volume
    "L": "LITRE",
    "LTR": "LITRE",
    "LTRS": "LITRE",
    "LITER": "LITRE",
    "LITERS": "LITRE",
    "LITRE": "LITRE",
    "LITRES": "LITRE",
    "ML": "ML",
    "MILLILITER": "ML",
    "MILLILITERS": "ML",
    "MILLILITRE": "ML",
    "MILLILITRES": "ML",
    # Count / Discrete
    "PIECE": "PIECE",
    "PIECES": "PIECE",
    "PC": "PIECE",
    "PCS": "PIECE",
    "DOZEN": "DOZEN",
    "DOZENS": "DOZENS",
    "DZ": "DOZEN",
    "PACKET": "PACKET",
    "PACKETS": "PACKET",
    "PKT": "PACKET",
    "PKTS": "PACKET",
    "BOX": "BOX",
    "BOXES": "BOX",
}

WEIGHT_UNITS: Set[str] = {"KG", "G"}
VOLUME_UNITS: Set[str] = {"LITRE", "ML"}
COUNT_UNITS: Set[str] = {"PIECE", "DOZEN", "PACKET", "BOX"}


def normalize_unit(unit: str) -> str:
    """Normalize input unit string to uppercase canonical form."""
    if not unit:
        return ""
    clean = unit.strip().upper()
    return UNIT_ALIASES.get(clean, clean)


def are_units_compatible(unit_a: str, unit_b: str) -> bool:
    """
    Checks if two units belong to the same dimension:
    - Weight: KG, G
    - Volume: LITRE, ML
    - Count: PIECE, DOZEN (Note: PACKET and BOX only convert to themselves unless custom ratio)
    """
    u_a = normalize_unit(unit_a)
    u_b = normalize_unit(unit_b)

    if u_a == u_b:
        return True

    if u_a in WEIGHT_UNITS and u_b in WEIGHT_UNITS:
        return True

    if u_a in VOLUME_UNITS and u_b in VOLUME_UNITS:
        return True

    if (u_a in {"PIECE", "DOZEN"}) and (u_b in {"PIECE", "DOZEN"}):
        return True

    return False


def convert_quantity(quantity: Decimal | float | int | str, from_unit: str, to_unit: str) -> Decimal:
    """
    Converts quantity from recipe unit to inventory stock unit.
    E.g.:
      - 250 g to KG -> 0.25 KG
      - 2 dozen to PIECE -> 24 PIECE
      - 500 ml to LITRE -> 0.5 LITRE
    Raises ValueError if units are incompatible.
    """
    qty = Decimal(str(quantity))
    f_unit = normalize_unit(from_unit)
    t_unit = normalize_unit(to_unit)

    if f_unit == t_unit:
        return qty

    # Weight conversions
    weight_to_grams = {
        "G": Decimal("1"),
        "KG": Decimal("1000"),
    }
    if f_unit in weight_to_grams and t_unit in weight_to_grams:
        in_grams = qty * weight_to_grams[f_unit]
        return in_grams / weight_to_grams[t_unit]

    # Volume conversions
    volume_to_ml = {
        "ML": Decimal("1"),
        "LITRE": Decimal("1000"),
    }
    if f_unit in volume_to_ml and t_unit in volume_to_ml:
        in_ml = qty * volume_to_ml[f_unit]
        return in_ml / volume_to_ml[t_unit]

    # Count conversions (DOZEN <-> PIECE)
    count_to_pieces = {
        "PIECE": Decimal("1"),
        "DOZEN": Decimal("12"),
    }
    if f_unit in count_to_pieces and t_unit in count_to_pieces:
        in_pieces = qty * count_to_pieces[f_unit]
        return in_pieces / count_to_pieces[t_unit]

    # If both are PACKET or BOX or unknown but identical
    if f_unit == t_unit:
        return qty

    raise ValueError(f"Invalid unit conversion: cannot convert from '{from_unit}' to '{to_unit}'. Units are incompatible.")
