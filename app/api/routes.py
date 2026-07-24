from typing import List

from fastapi import APIRouter, FastAPI, status

from app.controllers.shopping_controller import ShoppingController
from app.models.shopping_item import ShoppingItem, ShoppingItemCreate, ShoppingItemUpdate
from app.models.repository import PostgreSQLDummyRepository


router = APIRouter(prefix="/shopping-list", tags=["shopping-list"])


def register_routes(app: FastAPI, repository: PostgreSQLDummyRepository) -> None:
    controller = ShoppingController(repository)

    @router.get("", response_model=List[ShoppingItem]) ## GET - "/shopping-list"
    ## Codigos 3XX - 301 - Redirect 

    def list_items() -> List[ShoppingItem]:
        return controller.list_items()

    @router.post("", response_model=ShoppingItem, status_code=status.HTTP_201_CREATED)
    ## Codigos 2XX - 200, 201, 204 OK. 
    def create_item(item: ShoppingItemCreate) -> ShoppingItem:
        return controller.create_item(item)

    @router.get("/{item_id}", response_model=ShoppingItem)
    ### Codigos 4XX - 400, 404, 422 - Bad Request, Not Found, Unprocessable Entity
    def get_item(item_id: int) -> ShoppingItem:
        return controller.get_item(item_id)

    @router.put("/{item_id}", response_model=ShoppingItem)
    ### Codigos 5XX - 500, 502, 503 - Internal Server Error, Bad Gateway, Service Unavailable
    def update_item(item_id: int, item: ShoppingItemUpdate) -> ShoppingItem:
        return controller.update_item(item_id, item)

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_item(item_id: int) -> None:
        controller.delete_item(item_id)

    app.include_router(router)
