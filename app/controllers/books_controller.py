from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.models.book import BookCreate, BookGenre, BookResponse, BookStatus, BookStatusUpdate
from app.services.books_service import BookNotFoundError, BooksService
from app.views.books_view import book_not_found_exception


router = APIRouter(prefix="/books", tags=["books"])
service = BooksService()


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(payload: BookCreate) -> BookResponse:
    return service.create_book(payload)


@router.get("", response_model=list[BookResponse])
def list_books(
    genre: BookGenre | None = None,
    status: Annotated[BookStatus | None, Query()] = None,
) -> list[BookResponse]:
    return service.list_books(genre=genre, status=status)


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int) -> BookResponse:
    try:
        return service.get_book(book_id)
    except BookNotFoundError as error:
        raise book_not_found_exception() from error


@router.patch("/{book_id}/status", response_model=BookResponse)
def update_book_status(book_id: int, payload: BookStatusUpdate) -> BookResponse:
    try:
        return service.update_book_status(book_id, payload.status)
    except BookNotFoundError as error:
        raise book_not_found_exception() from error


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int) -> Response:
    try:
        service.delete_book(book_id)
    except BookNotFoundError as error:
        raise book_not_found_exception() from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)