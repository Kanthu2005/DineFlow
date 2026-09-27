from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.customer_schema import CustomerCreate, CustomerUpdate
from app.services.customer_service import CustomerService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Customers"])


@router.post("/customers", status_code=status.HTTP_201_CREATED)
def create_customer(
    data: CustomerCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return CustomerService.create_customer(data)
    except Exception as e:
        handle_error(e)


@router.get("/customers")
def get_customers(
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return CustomerService.get_customers()
    except Exception as e:
        handle_error(e)


@router.get("/customers/{customer_id}")
def get_customer(
    customer_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return CustomerService.get_customer(customer_id)
    except Exception as e:
        handle_error(e)


@router.put("/customers/{customer_id}")
def update_customer(
    customer_id: str,
    data: CustomerUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "WAITER", "CASHIER")),
):
    try:
        return CustomerService.update_customer(
            customer_id,
            data,
        )
    except Exception as e:
        handle_error(e)
