from pydantic import BaseModel, Field


class RestaurantTableCreate(BaseModel):
    table_number: str = Field(min_length=1, max_length=20)
    capacity: int = Field(gt=0)
    location: str | None = None
    is_active: bool = True


class RestaurantTableUpdate(BaseModel):
    table_number: str | None = Field(
        default=None,
        min_length=1,
        max_length=20
    )
    capacity: int | None = Field(default=None, gt=0)
    location: str | None = None
    is_active: bool | None = None


class TableStatusUpdate(BaseModel):
    status: str


class RestaurantTableResponse(BaseModel):
    id: str
    table_number: str
    capacity: int
    location: str | None = None
    status: str
    is_active: bool