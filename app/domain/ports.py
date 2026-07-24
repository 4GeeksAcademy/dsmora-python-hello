from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models import ShoppingItem, ShoppingItemCreate, ShoppingItemUpdate


class ShoppingRepository(ABC):
    @abstractmethod
    def list_items(self) -> List[ShoppingItem]:
        raise NotImplementedError

    @abstractmethod
    def add_item(self, item: ShoppingItemCreate) -> ShoppingItem:
        raise NotImplementedError

    @abstractmethod
    def get_item(self, item_id: int) -> Optional[ShoppingItem]:
        raise NotImplementedError

    @abstractmethod
    def update_item(self, item_id: int, item: ShoppingItemUpdate) -> Optional[ShoppingItem]:
        raise NotImplementedError

    @abstractmethod
    def delete_item(self, item_id: int) -> bool:
        raise NotImplementedError
