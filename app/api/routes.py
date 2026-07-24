from typing import List

from fastapi import APIRouter, FastAPI, HTTPException, status

from app.adapters import PostgreSQLDummyRepository
from app.domain.models import ShoppingItem, ShoppingItemCreate, ShoppingItemUpdate


router = APIRouter(prefix="/shopping-list", tags=["shopping-list"])


def register_routes(app: FastAPI, repository: PostgreSQLDummyRepository) -> None:
    @router.get("", response_model=List[ShoppingItem])
    def list_items() -> List[ShoppingItem]:
        return repository.list_items()

    @router.post("", response_model=ShoppingItem, status_code=status.HTTP_201_CREATED)
    def create_item(item: ShoppingItemCreate) -> ShoppingItem:
        return repository.add_item(item)

    @router.get("/{item_id}", response_model=ShoppingItem)
    def get_item(item_id: int) -> ShoppingItem:
        item = repository.get_item(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return item

    @router.put("/{item_id}", response_model=ShoppingItem)
    def update_item(item_id: int, item: ShoppingItemUpdate) -> ShoppingItem:
        updated = repository.update_item(item_id, item)
        if updated is None:
            raise HTTPException(status_code=404, detail="Item not found")
        return updated

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_item(item_id: int) -> None:
        deleted = repository.delete_item(item_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Item not found")

    app.include_router(router)
