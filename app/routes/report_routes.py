"""
Reports and Analytics Routes.
Provides daily sales, kitchen metrics, most-ordered items, and serving capacity estimation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.services.report_service import ReportService
from app.services.ingredient_service import IngredientService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])


@router.get("/daily-sales")
def get_daily_sales_report(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CASHIER")),
):
    try:
        return ReportService.get_daily_sales_report(date)
    except Exception as e:
        handle_error(e)


@router.get("/most-ordered")
def get_most_ordered_items_report(
    limit: int = 10,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return ReportService.get_most_ordered_items(limit)
    except Exception as e:
        handle_error(e)


@router.get("/kitchen-performance")
def get_kitchen_performance_report(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return ReportService.get_kitchen_performance()
    except Exception as e:
        handle_error(e)


@router.get("/serving-capacity")
def get_serving_capacity_report(
    menu_item_id: Optional[str] = None,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER")),
):
    try:
        return IngredientService.estimate_serving_capacity(menu_item_id)
    except Exception as e:
        handle_error(e)
