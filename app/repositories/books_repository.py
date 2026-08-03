from typing import Any

from tinydb import Query

from app.db import get_db
from app.models.book import BookCreate, BookGenre, BookResponse, BookStatus


class BooksRepository:
    def __init__(self) -> None:
        self.table = get_db().table("books")

    def create(self, book: BookCreate) -> BookResponse:
        payload = book.model_dump() if hasattr(book, "model_dump") else book.dict()
        doc_id = self.table.insert(payload)
        return BookResponse(id=doc_id, **payload)

    def list(
        self,
        genre: BookGenre | None = None,
        status: BookStatus | None = None,
    ) -> list[BookResponse]:
        query = Query()
        condition = None

        if genre is not None:
            condition = query.genre == genre.value

        if status is not None:
            status_condition = query.status == status.value
            condition = status_condition if condition is None else condition & status_condition

        records = self.table.search(condition) if condition is not None else self.table.all()
        return [self._to_response(record) for record in records]

    def get_by_id(self, book_id: int) -> BookResponse | None:
        record = self.table.get(doc_id=book_id)
        if record is None:
            return None
        return self._to_response(record)

    def update_status(self, book_id: int, status: BookStatus) -> BookResponse | None:
        updated = self.table.update({"status": status.value}, doc_ids=[book_id])
        if not updated:
            return None
        record = self.table.get(doc_id=book_id)
        return self._to_response(record)

    def delete(self, book_id: int) -> bool:
        removed = self.table.remove(doc_ids=[book_id])
        return bool(removed)

    def exists_by_title_author(self, title: str, author: str) -> bool:
        query = Query()
        return self.table.contains((query.title == title) & (query.author == author))

    def _to_response(self, record: Any) -> BookResponse:
        return BookResponse(id=record.doc_id, **dict(record))