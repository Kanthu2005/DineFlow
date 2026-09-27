from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.feedback_schema import FeedbackCreate
from app.services.feedback_service import FeedbackService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Feedback"])


@router.post(
    "/orders/{order_id}/feedback",
    status_code=status.HTTP_201_CREATED,
)
def create_feedback(
    order_id: str,
    data: FeedbackCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return FeedbackService.create_feedback(
            order_id,
            data,
        )
    except Exception as e:
        handle_error(e)


@router.get("/feedback/summary")
def get_feedback_summary(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return FeedbackService.get_summary()
    except Exception as e:
        handle_error(e)


@router.get("/feedback/customer/{customer_id}")
def get_feedback_by_customer(
    customer_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return FeedbackService.get_customer_feedback(
            customer_id
        )
    except Exception as e:
        handle_error(e)


@router.get("/feedback/order/{order_id}")
def get_feedback_by_order(
    order_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return FeedbackService.get_order_feedback(order_id)
    except Exception as e:
        handle_error(e)


@router.get("/feedback/{feedback_id}")
def get_feedback(
    feedback_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return FeedbackService.get_feedback(feedback_id)
    except Exception as e:
        handle_error(e)


@router.get("/feedback")
def get_all_feedback(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER")),
):
    try:
        return FeedbackService.get_all_feedback()
    except Exception as e:
        handle_error(e)
