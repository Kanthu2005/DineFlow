"""
Master router bridge module.
Re-exports the combined APIRouter from modular route modules in app/routes/.
Maintains 100% backward compatibility for all imports from app.routes.routes.
"""

from app.routes import (
    router,
    handle_error,
    get_current_user,
    require_roles,
    security,
    auth_router,
    user_router,
    customer_router,
    menu_router,
    ingredient_router,
    recipe_router,
    table_router,
    reservation_router,
    order_router,
    kitchen_router,
    stock_movement_router,
    payment_router,
    activity_log_router,
    kitchen_event_router,
    feedback_router,
    report_router,
)

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
]