"""
Reservation Management Routes.
Supports creation, time overlap checks, confirmations, and cancellations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.reservation_schema import ReservationCreate, ReservationUpdate
from app.services.reservation_service import ReservationService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Reservations"])


@router.post("/reservations", status_code=status.HTTP_201_CREATED)
def create_reservation(
    data: ReservationCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return ReservationService.create_reservation(data)
    except Exception as e:
        handle_error(e)


@router.get("/reservations")
def get_reservations(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return ReservationService.get_reservations()
    except Exception as e:
        handle_error(e)


@router.get("/reservations/customer/{customer_id}")
def get_customer_reservations(
    customer_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return ReservationService.get_by_customer(customer_id)
    except Exception as e:
        handle_error(e)


@router.get("/reservations/table/{table_id}")
def get_table_reservations(
    table_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return ReservationService.get_by_table(table_id)
    except Exception as e:
        handle_error(e)


@router.get("/reservations/{reservation_id}")
def get_reservation(
    reservation_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return ReservationService.get_reservation(reservation_id)
    except Exception as e:
        handle_error(e)


@router.put("/reservations/{reservation_id}")
def update_reservation(
    reservation_id: str,
    data: ReservationUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return ReservationService.update_reservation(reservation_id, data)
    except Exception as e:
        handle_error(e)


@router.patch("/reservations/{reservation_id}/confirm")
def confirm_reservation(
    reservation_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER")),
):
    try:
        return ReservationService.confirm_reservation(reservation_id)
    except Exception as e:
        handle_error(e)


@router.patch("/reservations/{reservation_id}/cancel")
def cancel_reservation(
    reservation_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER")),
):
    try:
        return ReservationService.cancel_reservation(reservation_id)
    except Exception as e:
        handle_error(e)
