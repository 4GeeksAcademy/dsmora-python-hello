from dataclasses import dataclass
from typing import Optional


@dataclass
class ShoppingItem:
    id: int
    name: str
    quantity: int
    completed: bool


@dataclass
class ShoppingItemCreate:
    name: str
    quantity: int
    completed: bool = False


@dataclass
class ShoppingItemUpdate:
    name: Optional[str] = None
    quantity: Optional[int] = None
    completed: Optional[bool] = None
