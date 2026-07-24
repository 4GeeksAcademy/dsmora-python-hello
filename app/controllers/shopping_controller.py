from typing import List

from fastapi import HTTPException, status

from app.models.shopping_item import ShoppingItem, ShoppingItemCreate, ShoppingItemUpdate


class ShoppingController:
    def __init__(self, repository):
        self.repository = repository

    def list_items(self) -> List[ShoppingItem]:
        return self.repository.list_items()

    def create_item(self, item: ShoppingItemCreate) -> ShoppingItem:
        return self.repository.add_item(item)

    def get_item(self, item_id: int) -> ShoppingItem:
        item = self.repository.get_item(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

    def update_item(self, item_id: int, item: ShoppingItemUpdate) -> ShoppingItem:
        updated = self.repository.update_item(item_id, item)
        if updated is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return updated

    def delete_item(self, item_id: int) -> None:
        deleted = self.repository.delete_item(item_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Item not found")
