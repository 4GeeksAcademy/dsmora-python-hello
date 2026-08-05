from app.db import get_db
from app.models.reserved_book import ReservedBookModel
from tinydb import Query


class ReservedBooksRepository:
    def __init__(self) -> None:
        self.table = get_db().table("reserved_books")

    def create(self, reservation: ReservedBookModel) -> ReservedBookModel:
        payload = reservation.model_dump(mode="json") if hasattr(reservation, "model_dump") else reservation.dict()
        self.table.insert(payload)
        return reservation

    def list_by_user_id(self, user_id: str) -> list[ReservedBookModel]:
        query = Query()
        records = self.table.search(query.user_id == user_id)
        return [ReservedBookModel(**record) for record in records]
