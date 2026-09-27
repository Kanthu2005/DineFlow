"""
Backward-compatibility bridge for typo schema filename.
"""
from app.schemas.stock_movement_schema import (
    StockMovementCreate,
    StockMovementResponse,
)

__all__ = [
    "StockMovementCreate",
    "StockMovementResponse",
]