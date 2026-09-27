from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.activity_schema import ActivityLogCreate
from app.services.activity_log_service import ActivityLogService
from app.routes.dependencies import handle_error, get_current_user, require_roles
from app.services.common import get_field

router = APIRouter(tags=["Activity Logs"])


@router.post(
    "/orders/{order_id}/activity",
    status_code=status.HTTP_201_CREATED,
    summary="Record Order Activity Log",
)
def create_activity_log(
    order_id: str,
    data: ActivityLogCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        action = get_field(data, "action")
        if not action:
            raise ValueError("action is required")

        return ActivityLogService.create_log(
            order_id=order_id,
            action=action,
            performed_by=get_field(data, "performed_by") or current_user.get("id"),
            details=get_field(data, "details"),
        )
    except Exception as e:
        handle_error(e)


@router.get(
    "/activity-logs/order/{order_id}",
    summary="Get Order Activity Logs",
)
@router.get("/activity-logs/{order_id}", include_in_schema=False)
@router.get("/orders/{order_id}/activity", include_in_schema=False)
def get_order_activity(
    order_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER", "CHEF")),
):
    try:
        return ActivityLogService.get_order_logs(order_id)
    except Exception as e:
        handle_error(e)
