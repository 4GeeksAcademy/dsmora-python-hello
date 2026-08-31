from app.models.book import BookCreate, BookGenre, BookResponse, BookStatus
from app.models.reserved_book import ReservationStatus, ReservedBookModel
from app.repositories.books_repository import BooksRepository
from app.repositories.reserved_books_repository import ReservedBooksRepository


class BookNotFoundError(Exception):
    pass


class BookUnavailableError(Exception):
    pass


class ReservationNotFoundError(Exception):
    pass


class ReservationForbiddenError(Exception):
    pass


class BooksService:
    def __init__(
        self,
        repository: BooksRepository | None = None,
        reserved_books_repository: ReservedBooksRepository | None = None,
    ) -> None:
        self.repository = repository or BooksRepository()
        self.reserved_books_repository = reserved_books_repository or ReservedBooksRepository()

    def create_book(self, book: BookCreate) -> BookResponse:
        return self.repository.create(book)

    def list_books(
        self,
        genre: BookGenre | None = None,
        status: BookStatus | None = None,
    ) -> list[BookResponse]:
        return self.repository.list(genre=genre, status=status)

    def get_book(self, book_id: int) -> BookResponse:
        book = self.repository.get_by_id(book_id)
        if book is None:
            raise BookNotFoundError()
        return book

    def reserve_book(self, book_id: int, user_id: str) -> BookResponse:
        book = self.get_book(book_id)
        if book.status != BookStatus.available:
            raise BookUnavailableError()

        updated_book = self.repository.update_status(book_id, BookStatus.checked_out)
        if updated_book is None:
            raise BookNotFoundError()

        self.reserved_books_repository.create(
            ReservedBookModel(user_id=user_id, book_id=book_id)
        )
        return updated_book

    def release_book(self, book_id: int, user_id: str) -> BookResponse:
        self.get_book(book_id)
        reservation = self.reserved_books_repository.get_latest_by_book_id(book_id)
        if reservation is None or reservation.status != ReservationStatus.reserved:
            raise ReservationNotFoundError()
        if reservation.user_id != user_id:
            raise ReservationForbiddenError()

        updated_book = self.repository.update_status(book_id, BookStatus.available)
        if updated_book is None:
            raise BookNotFoundError()
        self.reserved_books_repository.update_status(reservation.id, ReservationStatus.cancelled)
        return updated_book

    def delete_book(self, book_id: int) -> None:
        deleted = self.repository.delete(book_id)
        if not deleted:
            raise BookNotFoundError()