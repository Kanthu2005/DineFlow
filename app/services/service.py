"""
Central re-export hub for all domain services.
Maintains 100% backward compatibility with existing code.
"""

from app.services.common import (
    now_utc,
    to_object_id,
    decimal128,
    clean_mongo_types,
    convert_decimal,
    serialize_document,
    serialize_documents,
    serialize_user_document,
    serialize_user_documents,
    generate_number,
)

from app.services.auth_service import (
    AuthService,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

from app.services.user_service import UserService
from app.services.customer_service import CustomerService
from app.services.menu_service import MenuCategoryService, MenuItemService
from app.services.ingredient_service import IngredientService
from app.services.recipe_service import RecipeService
from app.services.table_service import RestaurantTableService
from app.services.reservation_service import ReservationService
from app.services.order_service import OrderService, OrderItemService
from app.services.kitchen_service import KitchenService
from app.services.stock_movement_service import StockMovementService
from app.services.billing_service import BillingService
from app.services.payment_service import PaymentService
from app.services.refund_service import RefundService
from app.services.activity_log_service import ActivityLogService
from app.services.kitchen_event_service import KitchenEventService
from app.services.feedback_service import FeedbackService
from app.services.report_service import ReportService

__all__ = [
    "now_utc",
    "to_object_id",
    "decimal128",
    "clean_mongo_types",
    "convert_decimal",
    "serialize_document",
    "serialize_documents",
    "serialize_user_document",
    "serialize_user_documents",
    "generate_number",
    "AuthService",
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "UserService",
    "CustomerService",
    "MenuCategoryService",
    "MenuItemService",
    "IngredientService",
    "RecipeService",
    "RestaurantTableService",
    "ReservationService",
    "OrderService",
    "OrderItemService",
    "KitchenService",
    "StockMovementService",
    "BillingService",
    "PaymentService",
    "RefundService",
    "ActivityLogService",
    "KitchenEventService",
    "FeedbackService",
    "ReportService",
]