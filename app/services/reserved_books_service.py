from app.models.reserved_book import ReservedBookResponse
from app.repositories.books_repository import BooksRepository
from app.repositories.reserved_books_repository import ReservedBooksRepository


class ReservedBooksService:
    def __init__(
        self,
        reserved_repository: ReservedBooksRepository | None = None,
        books_repository: BooksRepository | None = None,
    ) -> None:
        self.reserved_repository = reserved_repository or ReservedBooksRepository()
        self.books_repository = books_repository or BooksRepository()

    def list_reserved_for_user(self, user_id: str) -> list[ReservedBookResponse]:
        reservations = self.reserved_repository.list_active_by_user_id(user_id)
        response: list[ReservedBookResponse] = []

        for reservation in reservations:
            book = self.books_repository.get_by_id(reservation.book_id)
            response.append(
                ReservedBookResponse(
                    id=reservation.id,
                    user_id=reservation.user_id,
                    book_id=reservation.book_id,
                    status=reservation.status,
                    created_at=reservation.created_at,
                    book=book,
                )
            )

        return response
