"""
Recipe Management Routes.
Supports both /menu-items/{id}/ingredients and /recipes conventions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.recipe_schema import RecipeCreate, RecipeUpdate
from app.services.recipe_service import RecipeService
from app.routes.dependencies import handle_error, get_current_user, require_roles

router = APIRouter(tags=["Recipes"])


@router.post("/menu-items/{menu_item_id}/ingredients", status_code=status.HTTP_201_CREATED, summary="Add Ingredient to Menu Item Recipe")
@router.post("/menu/items/{menu_item_id}/ingredients", status_code=status.HTTP_201_CREATED, include_in_schema=False)
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
def get_recipes_by_menu_item(
    menu_item_id: str,
    current_user: dict = Depends(require_roles("ADMIN", "MANAGER", "CHEF")),
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
