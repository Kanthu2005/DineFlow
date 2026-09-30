"""
Menu Management Routes.
Supports both /menu-items and /menu/items conventions with complete Swagger UI response models.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.menu_schema import (
    MenuCategoryCreate,
    MenuCategoryUpdate,
    MenuCategoryResponse,
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse,
    MessageResponse,
)
from app.services.menu_service import MenuCategoryService, MenuItemService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Menu"])


# ==========================================
# Category Routes
# ==========================================

@router.post(
    "/menu/categories",
    response_model=MenuCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Menu Category",
)
@router.post(
    "/menu-categories",
    response_model=MenuCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_menu_category(
    data: MenuCategoryCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return MenuCategoryService.create_category(data)
    except Exception as e:
        handle_error(e)


@router.get(
    "/menu/categories",
    response_model=List[MenuCategoryResponse],
    summary="List All Menu Categories",
)
@router.get(
    "/menu-categories",
    response_model=List[MenuCategoryResponse],
    include_in_schema=False,
)
def get_menu_categories(current_user: dict = Depends(get_current_user)):
    try:
        return MenuCategoryService.get_categories()
    except Exception as e:
        handle_error(e)


@router.get(
    "/menu/categories/{category_id}",
    response_model=MenuCategoryResponse,
    summary="Get Menu Category Details",
)
@router.get(
    "/menu-categories/{category_id}",
    response_model=MenuCategoryResponse,
    include_in_schema=False,
)
def get_menu_category(category_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return MenuCategoryService.get_category(category_id)
    except Exception as e:
        handle_error(e)


@router.put(
    "/menu/categories/{category_id}",
    response_model=MenuCategoryResponse,
    summary="Update Menu Category",
)
@router.put(
    "/menu-categories/{category_id}",
    response_model=MenuCategoryResponse,
    include_in_schema=False,
)
def update_menu_category(
    category_id: str,
    data: MenuCategoryUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return MenuCategoryService.update_category(category_id, data)
    except Exception as e:
        handle_error(e)


@router.delete(
    "/menu/categories/{category_id}",
    response_model=MessageResponse,
    summary="Delete Menu Category",
)
@router.delete(
    "/menu-categories/{category_id}",
    response_model=MessageResponse,
    include_in_schema=False,
)
def delete_menu_category(
    category_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return MenuCategoryService.delete_category(category_id)
    except Exception as e:
        handle_error(e)


# ==========================================
# Menu Item Routes (Supports /menu-items and /menu/items)
# ==========================================

@router.post(
    "/menu-items",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Menu Item",
)
@router.post(
    "/menu/items",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_menu_item(
    data: MenuItemCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return MenuItemService.create_item(data)
    except Exception as e:
        handle_error(e)


@router.get(
    "/menu-items/available",
    response_model=List[MenuItemResponse],
    summary="Get Available Menu Items",
)
@router.get(
    "/menu/items/available",
    response_model=List[MenuItemResponse],
    include_in_schema=False,
)
def get_available_menu_items(current_user: dict = Depends(get_current_user)):
    try:
        return MenuItemService.get_available_items()
    except Exception as e:
        handle_error(e)


@router.get(
    "/menu-items/search",
    response_model=List[MenuItemResponse],
    summary="Search Menu Items",
)
@router.get(
    "/menu/items/search",
    response_model=List[MenuItemResponse],
    include_in_schema=False,
)
def search_menu_items(
    q: str = Query(..., description="Search query string"),
    current_user: dict = Depends(get_current_user),
):
    try:
        return MenuItemService.search_items(q)
    except Exception as e:
        handle_error(e)


@router.get(
    "/menu-items/category/{category_id}",
    response_model=List[MenuItemResponse],
    summary="Get Menu Items by Category",
)
@router.get(
    "/menu/items/category/{category_id}",
    response_model=List[MenuItemResponse],
    include_in_schema=False,
)
def get_menu_items_by_category(category_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return MenuItemService.get_items_by_category(category_id)
    except Exception as e:
        handle_error(e)


@router.get(
    "/menu-items",
    response_model=List[MenuItemResponse],
    summary="List All Menu Items",
)
@router.get(
    "/menu/items",
    response_model=List[MenuItemResponse],
    include_in_schema=False,
)
def get_menu_items(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    try:
        if category:
            return MenuItemService.get_items_by_category(category)
        return MenuItemService.get_items()
    except Exception as e:
        handle_error(e)


@router.get(
    "/menu-items/{item_id}",
    response_model=MenuItemResponse,
    summary="Get Menu Item Details",
)
@router.get(
    "/menu/items/{item_id}",
    response_model=MenuItemResponse,
    include_in_schema=False,
)
def get_menu_item(item_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return MenuItemService.get_item(item_id)
    except Exception as e:
        handle_error(e)


@router.put(
    "/menu-items/{item_id}",
    response_model=MenuItemResponse,
    summary="Update Menu Item",
)
@router.put(
    "/menu/items/{item_id}",
    response_model=MenuItemResponse,
    include_in_schema=False,
)
def update_menu_item(
    item_id: str,
    data: MenuItemUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return MenuItemService.update_item(item_id, data)
    except Exception as e:
        handle_error(e)


@router.patch(
    "/menu-items/{item_id}/availability",
    response_model=MenuItemResponse,
    summary="Update Menu Item Availability",
)
@router.patch(
    "/menu/items/{item_id}/availability",
    response_model=MenuItemResponse,
    include_in_schema=False,
)
def update_menu_item_availability(
    item_id: str,
    is_available: bool = Query(..., description="Whether the item is available"),
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return MenuItemService.update_availability(item_id, is_available)
    except Exception as e:
        handle_error(e)


@router.delete(
    "/menu-items/{item_id}",
    response_model=MessageResponse,
    summary="Delete Menu Item",
)
@router.delete(
    "/menu/items/{item_id}",
    response_model=MessageResponse,
    include_in_schema=False,
)
def delete_menu_item(
    item_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return MenuItemService.delete_item(item_id)
    except Exception as e:
        handle_error(e)
