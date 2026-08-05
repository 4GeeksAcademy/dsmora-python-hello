from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies.auth import get_current_user, require_roles
from app.models.book import BookCreate, BookGenre, BookResponse, BookStatus, BookStatusUpdate
from app.models.reserved_book import ReservedBookResponse
from app.models.user import UserModel
from app.services.reserved_books_service import ReservedBooksService
from app.services.books_service import BookNotFoundError, BooksService
from app.views.books_view import book_not_found_exception


router = APIRouter(prefix="/books", tags=["books"])
service = BooksService()
reserved_books_service = ReservedBooksService()

# si necesita token | un rol especial para crear libros
@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    payload: BookCreate,
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> BookResponse:
    require_roles(current_user, {"admin", "manager"})
    return service.create_book(payload)

# no necesita token 
@router.get("", response_model=list[BookResponse])
def list_books(
    genre: BookGenre | None = None,
    status: Annotated[BookStatus | None, Query()] = None,
) -> list[BookResponse]:
    return service.list_books(genre=genre, status=status)

# no necesita token 
@router.get("/reserved", response_model=list[ReservedBookResponse])
def list_reserved_books(
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> list[ReservedBookResponse]:
    return reserved_books_service.list_reserved_for_user(current_user.id)


# no necesita token 
@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int) -> BookResponse:
    try:
        return service.get_book(book_id)
    except BookNotFoundError as error:
        raise book_not_found_exception() from error

## necesita token | puede o no necesitar un rol especial
@router.patch("/{book_id}/status", response_model=BookResponse)
def update_book_status(
    book_id: int,
    payload: BookStatusUpdate,
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> BookResponse:
    try:
        return service.update_book_status(book_id, payload.status, current_user.id)
    except BookNotFoundError as error:
        raise book_not_found_exception() from error

# necesita token y un rol especial
@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> Response:
    require_roles(current_user, {"admin", "manager"})
    try:
        service.delete_book(book_id)
    except BookNotFoundError as error:
        raise book_not_found_exception() from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)