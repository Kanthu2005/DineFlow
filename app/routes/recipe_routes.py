"""
Recipe Management Routes.
Supports /recipes, /menu/{menu_id}/recipe, and live availability calculation endpoints.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.recipe_schema import RecipeCreate, RecipeUpdate
from app.services.recipe_service import RecipeService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Recipes & Stock Availability"])


# ==========================================
# Real-Time Stock Availability Endpoints
# ==========================================

@router.get("/menu-items/availability", summary="Get Live Availability for All Menu Items")
@router.get("/menu/items/availability", include_in_schema=False)
@router.get("/menu/availability", include_in_schema=False)
def get_all_menu_items_availability(
    current_user: dict = Depends(get_current_user),
):
    """
    Returns real-time stock availability state for all menu items:
    - AVAILABLE (🟢)
    - LOW_STOCK (🟡 with portions remaining)
    - OUT_OF_STOCK (🔴 with limiting ingredient)
    """
    try:
        return RecipeService.get_all_availability()
    except Exception as e:
        handle_error(e)


@router.get("/menu-items/{menu_item_id}/availability", summary="Get Live Availability for Single Menu Item")
@router.get("/menu/items/{menu_item_id}/availability", include_in_schema=False)
def get_menu_item_availability(
    menu_item_id: str,
    quantity: int = Query(default=1, ge=1, description="Quantity requested to evaluate"),
    current_user: dict = Depends(get_current_user),
):
    """
    Evaluates item recipe against warehouse stock.
    Returns remaining portions capacity and shortage details if requested quantity exceeds stock.
    """
    try:
        return RecipeService.calculate_item_availability(menu_item_id, requested_quantity=quantity)
    except Exception as e:
        handle_error(e)


# ==========================================
# Recipe CRUD Operations
# ==========================================

@router.post("/menu-items/{menu_item_id}/ingredients", status_code=status.HTTP_201_CREATED, summary="Add Ingredient to Menu Item Recipe")
@router.post("/menu/items/{menu_item_id}/ingredients", status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/menu/{menu_item_id}/recipe", status_code=status.HTTP_201_CREATED, summary="Configure Recipe for Menu Item")
def add_ingredient_to_menu_item(
    menu_item_id: str,
    data: RecipeCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return RecipeService.create_recipe(menu_item_id, data)
    except Exception as e:
        handle_error(e)


@router.post("/recipes", status_code=status.HTTP_201_CREATED, summary="Create Recipe Mapping")
def create_recipe(
    data: RecipeCreate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return RecipeService.create_recipe(data)
    except Exception as e:
        handle_error(e)


@router.get("/menu-items/{menu_item_id}/recipe", summary="Get Recipe by Menu Item")
@router.get("/menu-items/{menu_item_id}/recipes", include_in_schema=False)
@router.get("/menu/items/{menu_item_id}/recipes", include_in_schema=False)
@router.get("/menu/{menu_item_id}/recipe", include_in_schema=False)
def get_recipes_by_menu_item(
    menu_item_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF", "WAITER", "CASHIER")),
):
    try:
        return RecipeService.get_by_menu_item(menu_item_id)
    except Exception as e:
        handle_error(e)


@router.get("/recipes/{recipe_id}")
def get_recipe(
    recipe_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return RecipeService.get_recipe(recipe_id)
    except Exception as e:
        handle_error(e)


@router.put("/recipes/{recipe_id}")
def update_recipe(
    recipe_id: str,
    data: RecipeUpdate,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return RecipeService.update_recipe(recipe_id, data)
    except Exception as e:
        handle_error(e)


@router.delete("/recipes/{recipe_id}")
def delete_recipe(
    recipe_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return RecipeService.delete_recipe(recipe_id)
    except Exception as e:
        handle_error(e)


@router.delete("/menu/{menu_item_id}/recipe/{ingredient_id}")
@router.delete("/menu-items/{menu_item_id}/recipe/{ingredient_id}", include_in_schema=False)
def delete_menu_recipe_ingredient(
    menu_item_id: str,
    ingredient_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
):
    try:
        return RecipeService.delete_by_menu_item_and_ingredient(menu_item_id, ingredient_id)
    except Exception as e:
        handle_error(e)
