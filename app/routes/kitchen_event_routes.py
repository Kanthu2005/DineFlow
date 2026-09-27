from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.activity_schema import KitchenEventCreate
from app.services.kitchen_event_service import KitchenEventService
from app.routes.dependencies import handle_error, get_current_user, require_roles
from app.services.common import get_field

router = APIRouter(tags=["Kitchen Events"])


@router.post(
    "/kitchen/events",
    status_code=status.HTTP_201_CREATED,
    summary="Record Kitchen Event",
)
def create_kitchen_event(
    data: KitchenEventCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        order_id = get_field(data, "order_id")
        event_type = get_field(data, "event_type")
        if not order_id:
            raise ValueError("order_id is required")
        if not event_type:
            raise ValueError("event_type is required")

        return KitchenEventService.create_event(
            order_id=order_id,
            event_type=event_type,
            kitchen_ticket_id=get_field(data, "kitchen_ticket_id"),
            details=get_field(data, "details"),
        )
    except Exception as e:
        handle_error(e)


@router.get(
    "/kitchen-events/order/{order_id}",
    summary="Get Kitchen Events for Order",
)
@router.get("/kitchen-events/{order_id}", include_in_schema=False)
@router.get("/kitchen/events/order/{order_id}", include_in_schema=False)
def get_order_kitchen_events(
    order_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return KitchenEventService.get_order_events(order_id)
    except Exception as e:
        handle_error(e)
