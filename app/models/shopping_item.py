from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class ShoppingItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=1)
    completed: bool


class ShoppingItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=1)
    completed: bool = False


class ShoppingItemUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    quantity: Optional[int] = Field(default=None, ge=1)
    completed: Optional[bool] = None
