from app.db import get_db
from app.models.reserved_book import ReservationStatus, ReservedBookModel
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

    def list_active_by_user_id(self, user_id: str) -> list[ReservedBookModel]:
        query = Query()
        records = self.table.search(
            (query.user_id == user_id) & (query.status == ReservationStatus.reserved.value)
        )
        return [ReservedBookModel(**record) for record in records]

    def get_latest_by_book_id(self, book_id: int) -> ReservedBookModel | None:
        query = Query()
        records = self.table.search(query.book_id == book_id)
        if not records:
            return None
        return ReservedBookModel(**records[-1])

    def update_status(self, reservation_id: str, status: ReservationStatus) -> bool:
        query = Query()
        updated = self.table.update({"status": status.value}, query.id == reservation_id)
        return bool(updated)
