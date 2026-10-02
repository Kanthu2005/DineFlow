from fastapi import APIRouter

from app.routes.dependencies import (
    handle_error,
    get_current_user,
    require_roles,
    security,
)

from app.routes.auth_routes import router as auth_router
from app.routes.user_routes import router as user_router
from app.routes.customer_routes import router as customer_router
from app.routes.menu_routes import router as menu_router
from app.routes.ingredient_routes import router as ingredient_router
from app.routes.recipe_routes import router as recipe_router
from app.routes.table_routes import router as table_router
from app.routes.reservation_routes import router as reservation_router
from app.routes.order_routes import router as order_router
from app.routes.kitchen_routes import router as kitchen_router
from app.routes.stock_movement_routes import router as stock_movement_router
from app.routes.payment_routes import router as payment_router
from app.routes.activity_log_routes import router as activity_log_router
from app.routes.kitchen_event_routes import router as kitchen_event_router
from app.routes.feedback_routes import router as feedback_router
from app.routes.report_routes import router as report_router
from app.routes.purchase_routes import router as purchase_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(user_router)
router.include_router(customer_router)
router.include_router(menu_router)
router.include_router(ingredient_router)
router.include_router(recipe_router)
router.include_router(table_router)
router.include_router(reservation_router)
router.include_router(order_router)
router.include_router(kitchen_router)
router.include_router(stock_movement_router)
router.include_router(payment_router)
router.include_router(activity_log_router)
router.include_router(kitchen_event_router)
router.include_router(feedback_router)
router.include_router(report_router)
router.include_router(purchase_router)

__all__ = [
    "router",
    "handle_error",
    "get_current_user",
    "require_roles",
    "security",
    "auth_router",
    "user_router",
    "customer_router",
    "menu_router",
    "ingredient_router",
    "recipe_router",
    "table_router",
    "reservation_router",
    "order_router",
    "kitchen_router",
    "stock_movement_router",
    "payment_router",
    "activity_log_router",
    "kitchen_event_router",
    "feedback_router",
    "report_router",
    "purchase_router",
]
