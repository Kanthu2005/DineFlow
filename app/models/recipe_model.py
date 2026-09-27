from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict


class RecipeModel(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True
    )

    id: Optional[ObjectId] = None

    menu_item_id: ObjectId
    ingredient_id: ObjectId
    quantity_required: float = Field(...)