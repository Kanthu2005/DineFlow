"""
Kitchen Operations Routes.
Supports ticket lifecycle, stage progression, workload tracking, and prep-time estimation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from pydantic import BaseModel
from app.schemas.kitchen_schema import (
    KitchenTicketCreate,
    KitchenStaffAssignment,
)
from app.services.kitchen_service import KitchenService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Kitchen"])


class TicketStaffAssignRequest(BaseModel):
    staff_id: str
    station: Optional[str] = None


class TicketStatusUpdateRequest(BaseModel):
    status: Optional[str] = None
    status_value: Optional[str] = None


@router.post("/kitchen/tickets", status_code=status.HTTP_201_CREATED)
def create_kitchen_ticket(
    data: KitchenTicketCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER")),
):
    try:
        return KitchenService.create_ticket(data.order_id, data.priority)
    except Exception as e:
        handle_error(e)


@router.get("/kitchen/tickets")
def get_kitchen_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER")),
):
    try:
        return KitchenService.get_tickets(status=status, priority=priority)
    except Exception as e:
        handle_error(e)


@router.get("/kitchen/delayed")
def get_delayed_kitchen_tickets(
    threshold_minutes: int = 30,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return KitchenService.get_delayed_orders(threshold_minutes)
    except Exception as e:
        handle_error(e)


@router.get("/kitchen/workload")
def get_kitchen_workload(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return KitchenService.get_workload()
    except Exception as e:
        handle_error(e)


@router.get("/kitchen/estimate-time/{order_id}")
def estimate_order_preparation_time(
    order_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER")),
):
    try:
        return KitchenService.estimate_preparation_time(order_id)
    except Exception as e:
        handle_error(e)


@router.get("/kitchen/tickets/{ticket_id}")
def get_kitchen_ticket(
    ticket_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER")),
):
    try:
        return KitchenService.get_ticket(ticket_id)
    except Exception as e:
        handle_error(e)


@router.post("/kitchen/tickets/{ticket_id}/accept")
def accept_kitchen_ticket(
    ticket_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return KitchenService.accept_ticket(ticket_id, staff_id=current_user.get("id"))
    except Exception as e:
        handle_error(e)


@router.post("/kitchen/tickets/{ticket_id}/start")
def start_kitchen_ticket_prep(
    ticket_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return KitchenService.start_preparation(ticket_id, staff_id=current_user.get("id"))
    except Exception as e:
        handle_error(e)


@router.post("/kitchen/tickets/{ticket_id}/ready")
def mark_kitchen_ticket_ready(
    ticket_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return KitchenService.mark_ready(ticket_id)
    except Exception as e:
        handle_error(e)


@router.post("/kitchen/tickets/{ticket_id}/handover")
def handover_kitchen_ticket(
    ticket_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER")),
):
    try:
        return KitchenService.handover(ticket_id)
    except Exception as e:
        handle_error(e)


@router.post("/kitchen/tickets/{ticket_id}/assign")
def assign_kitchen_staff(
    ticket_id: str,
    data: TicketStaffAssignRequest,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return KitchenService.assign_staff(ticket_id, data.staff_id, data.station)
    except Exception as e:
        handle_error(e)


@router.patch("/kitchen/tickets/{ticket_id}/status")
def update_ticket_status(
    ticket_id: str,
    status_value: Optional[str] = Query(None),
    payload: Optional[TicketStatusUpdateRequest] = Body(None),
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER")),
):
    try:
        chosen_status = status_value or (payload.status if payload and payload.status else (payload.status_value if payload else None))
        if not chosen_status:
            raise ValueError("Status parameter is required (either as query param status_value or in JSON body)")
        return KitchenService.update_ticket_status(
            ticket_id=ticket_id,
            new_status=chosen_status,
            staff_id=current_user.get("id"),
            user_role=current_user.get("role", "CHEF"),
        )
    except Exception as e:
        handle_error(e)
