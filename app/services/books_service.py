from app.models.book import BookCreate, BookGenre, BookResponse, BookStatus
from app.repositories.books_repository import BooksRepository


class BookNotFoundError(Exception):
    pass


class BooksService:
    def __init__(self, repository: BooksRepository | None = None) -> None:
        self.repository = repository or BooksRepository()

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

    def update_book_status(self, book_id: int, status: BookStatus) -> BookResponse:
        book = self.repository.update_status(book_id, status)
        if book is None:
            raise BookNotFoundError()
        return book

    def delete_book(self, book_id: int) -> None:
        deleted = self.repository.delete(book_id)
        if not deleted:
            raise BookNotFoundError()