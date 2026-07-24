from typing import List, Optional

from app.models.shopping_item import ShoppingItem, ShoppingItemCreate, ShoppingItemUpdate


class PostgreSQLDummyRepository:
    def __init__(self):
        self._items: List[ShoppingItem] = [
            ShoppingItem(id=1, name="Pan", quantity=2, completed=False),
            ShoppingItem(id=2, name="Leche", quantity=1, completed=True),
        ]
        self._next_id = 3

    def list_items(self) -> List[ShoppingItem]:
        return list(self._items)

    def add_item(self, item: ShoppingItemCreate) -> ShoppingItem:
        created = ShoppingItem(
            id=self._next_id,
            name=item.name,
            quantity=item.quantity,
            completed=item.completed,
        )
        self._items.append(created)
        self._next_id += 1
        return created

    def get_item(self, item_id: int) -> Optional[ShoppingItem]:
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    def update_item(self, item_id: int, item: ShoppingItemUpdate) -> Optional[ShoppingItem]:
        for index, current in enumerate(self._items):
            if current.id == item_id:
                updated = ShoppingItem(
                    id=current.id,
                    name=item.name if item.name is not None else current.name,
                    quantity=item.quantity if item.quantity is not None else current.quantity,
                    completed=item.completed if item.completed is not None else current.completed,
                )
                self._items[index] = updated
                return updated
        return None

    def delete_item(self, item_id: int) -> bool:
        for index, item in enumerate(self._items):
            if item.id == item_id:
                del self._items[index]
                return True
        return False
