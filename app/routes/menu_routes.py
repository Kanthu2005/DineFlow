"""
Menu Management Routes.
Supports /categories, /subcategories, /menu, /menu-items, /menu/items conventions.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.menu_schema import (
    MenuCategoryCreate,
    MenuCategoryUpdate,
    MenuCategoryResponse,
    MenuSubcategoryCreate,
    MenuSubcategoryUpdate,
    MenuSubcategoryResponse,
    MenuItemCreate,
    MenuItemUpdate,
    MenuItemResponse,
    MenuStatsResponse,
    MessageResponse,
)
from app.services.menu_service import MenuCategoryService, MenuSubcategoryService, MenuItemService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Menu"])


# ==========================================
# Category Routes
# ==========================================

@router.post(
    "/categories",
    response_model=MenuCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Category",
)
@router.post(
    "/menu/categories",
    response_model=MenuCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
@router.post(
    "/menu-categories",
    response_model=MenuCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_category(
    data: MenuCategoryCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return MenuCategoryService.create_category(data)
    except Exception as e:
        handle_error(e)


@router.get(
    "/categories",
    response_model=List[MenuCategoryResponse],
    summary="List All Categories",
)
@router.get(
    "/menu/categories",
    response_model=List[MenuCategoryResponse],
    include_in_schema=False,
)
@router.get(
    "/menu-categories",
    response_model=List[MenuCategoryResponse],
    include_in_schema=False,
)
def get_categories(
    active_only: bool = Query(default=True, description="Filter only active categories"),
    current_user: dict = Depends(get_current_user),
):
    try:
        return MenuCategoryService.get_categories(active_only=active_only)
    except Exception as e:
        handle_error(e)


@router.get(
    "/categories/{category_id}",
    response_model=MenuCategoryResponse,
    summary="Get Category Details",
)
@router.get(
    "/menu/categories/{category_id}",
    response_model=MenuCategoryResponse,
    include_in_schema=False,
)
@router.get(
    "/menu-categories/{category_id}",
    response_model=MenuCategoryResponse,
    include_in_schema=False,
)
def get_category(category_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return MenuCategoryService.get_category(category_id)
    except Exception as e:
        handle_error(e)


@router.put(
    "/categories/{category_id}",
    response_model=MenuCategoryResponse,
    summary="Update Category",
)
@router.put(
    "/menu/categories/{category_id}",
    response_model=MenuCategoryResponse,
    include_in_schema=False,
)
@router.put(
    "/menu-categories/{category_id}",
    response_model=MenuCategoryResponse,
    include_in_schema=False,
)
def update_category(
    category_id: str,
    data: MenuCategoryUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return MenuCategoryService.update_category(category_id, data)
    except Exception as e:
        handle_error(e)


@router.delete(
    "/categories/{category_id}",
    response_model=MessageResponse,
    summary="Delete Category",
)
@router.delete(
    "/menu/categories/{category_id}",
    response_model=MessageResponse,
    include_in_schema=False,
)
@router.delete(
    "/menu-categories/{category_id}",
    response_model=MessageResponse,
    include_in_schema=False,
)
def delete_category(
    category_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return MenuCategoryService.delete_category(category_id)
    except Exception as e:
        handle_error(e)


# ==========================================
# Subcategory Routes
# ==========================================

@router.post(
    "/subcategories",
    response_model=MenuSubcategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Subcategory",
)
@router.post(
    "/menu/subcategories",
    response_model=MenuSubcategoryResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def create_subcategory(
    data: MenuSubcategoryCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return MenuSubcategoryService.create_subcategory(data)
    except Exception as e:
        handle_error(e)


@router.get(
    "/subcategories",
    response_model=List[MenuSubcategoryResponse],
    summary="List All Subcategories",
)
@router.get(
    "/menu/subcategories",
    response_model=List[MenuSubcategoryResponse],
    include_in_schema=False,
)
def get_subcategories(
    category_id: Optional[str] = Query(default=None, description="Optional parent category filter"),
    active_only: bool = Query(default=True, description="Filter only active subcategories"),
    current_user: dict = Depends(get_current_user),
):
    try:
        return MenuSubcategoryService.get_subcategories(category_id=category_id, active_only=active_only)
    except Exception as e:
        handle_error(e)


@router.get(
    "/categories/{category_id}/subcategories",
    response_model=List[MenuSubcategoryResponse],
    summary="List Subcategories of Category",
)
@router.get(
    "/menu/categories/{category_id}/subcategories",
    response_model=List[MenuSubcategoryResponse],
    include_in_schema=False,
)
def get_subcategories_by_category(
    category_id: str,
    active_only: bool = Query(default=True),
    current_user: dict = Depends(get_current_user),
):
    try:
        return MenuSubcategoryService.get_subcategories(category_id=category_id, active_only=active_only)
    except Exception as e:
        handle_error(e)


@router.get(
    "/subcategories/{subcategory_id}",
    response_model=MenuSubcategoryResponse,
    summary="Get Subcategory Details",
)
@router.get(
    "/menu/subcategories/{subcategory_id}",
    response_model=MenuSubcategoryResponse,
    include_in_schema=False,
)
def get_subcategory(subcategory_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return MenuSubcategoryService.get_subcategory(subcategory_id)
    except Exception as e:
        handle_error(e)


@router.put(
    "/subcategories/{subcategory_id}",
    response_model=MenuSubcategoryResponse,
    summary="Update Subcategory",
)
@router.put(
    "/menu/subcategories/{subcategory_id}",
    response_model=MenuSubcategoryResponse,
    include_in_schema=False,
)
def update_subcategory(
    subcategory_id: str,
    data: MenuSubcategoryUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return MenuSubcategoryService.update_subcategory(subcategory_id, data)
    except Exception as e:
        handle_error(e)


@router.delete(
    "/subcategories/{subcategory_id}",
    response_model=MessageResponse,
    summary="Delete Subcategory",
)
@router.delete(
    "/menu/subcategories/{subcategory_id}",
    response_model=MessageResponse,
    include_in_schema=False,
)
def delete_subcategory(
    subcategory_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return MenuSubcategoryService.delete_subcategory(subcategory_id)
    except Exception as e:
        handle_error(e)


# ==========================================
# Menu Items Routes
# ==========================================

@router.get(
    "/menu/stats",
    response_model=MenuStatsResponse,
    summary="Get Menu Dashboard Statistics",
)
@router.get(
    "/menu/statistics",
    response_model=MenuStatsResponse,
    include_in_schema=False,
)
def get_menu_statistics(current_user: dict = Depends(get_current_user)):
    try:
        return MenuItemService.get_statistics()
    except Exception as e:
        handle_error(e)


@router.post(
    "/menu",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Menu Item",
)
@router.post(
    "/menu-items",
    response_model=MenuItemResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
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
    "/menu/available",
    response_model=List[MenuItemResponse],
    summary="Get Available Menu Items",
)
@router.get(
    "/menu-items/available",
    response_model=List[MenuItemResponse],
    include_in_schema=False,
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
    "/menu/search",
    response_model=List[MenuItemResponse],
    summary="Search Menu Items",
)
@router.get(
    "/menu-items/search",
    response_model=List[MenuItemResponse],
    include_in_schema=False,
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
    "/menu/category/{category_id}",
    response_model=List[MenuItemResponse],
    summary="Get Menu Items by Category",
)
@router.get(
    "/menu-items/category/{category_id}",
    response_model=List[MenuItemResponse],
    include_in_schema=False,
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
    "/menu/subcategory/{subcategory_id}",
    response_model=List[MenuItemResponse],
    summary="Get Menu Items by Subcategory",
)
def get_menu_items_by_subcategory(subcategory_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return MenuItemService.get_items_by_subcategory(subcategory_id)
    except Exception as e:
        handle_error(e)


@router.get(
    "/menu",
    response_model=List[MenuItemResponse],
    summary="List All Menu Items",
)
@router.get(
    "/menu-items",
    response_model=List[MenuItemResponse],
    include_in_schema=False,
)
@router.get(
    "/menu/items",
    response_model=List[MenuItemResponse],
    include_in_schema=False,
)
def get_menu_items(
    category: Optional[str] = Query(default=None, description="Optional category filter"),
    subcategory: Optional[str] = Query(default=None, description="Optional subcategory filter"),
    active_only: bool = Query(default=False, description="Filter only active items"),
    current_user: dict = Depends(get_current_user),
):
    try:
        return MenuItemService.get_items(category_id=category, subcategory_id=subcategory, active_only=active_only)
    except Exception as e:
        handle_error(e)


@router.get(
    "/menu/{item_id}",
    response_model=MenuItemResponse,
    summary="Get Menu Item Details",
)
@router.get(
    "/menu-items/{item_id}",
    response_model=MenuItemResponse,
    include_in_schema=False,
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
    "/menu/{item_id}",
    response_model=MenuItemResponse,
    summary="Update Menu Item",
)
@router.put(
    "/menu-items/{item_id}",
    response_model=MenuItemResponse,
    include_in_schema=False,
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
    "/menu/{item_id}/availability",
    response_model=MenuItemResponse,
    summary="Update Menu Item Availability",
)
@router.patch(
    "/menu-items/{item_id}/availability",
    response_model=MenuItemResponse,
    include_in_schema=False,
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
    "/menu/{item_id}",
    response_model=MessageResponse,
    summary="Delete Menu Item (Safe Deletion)",
)
@router.delete(
    "/menu-items/{item_id}",
    response_model=MessageResponse,
    include_in_schema=False,
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
