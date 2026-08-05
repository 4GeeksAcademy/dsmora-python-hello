from app.db import get_db
from app.models.user import UserModel, UserResponse
from tinydb import Query


class UsersRepository:
    def __init__(self) -> None:
        self.table = get_db().table("users")

    def create(self, user: UserModel) -> UserModel:
        payload = user.model_dump(mode="json") if hasattr(user, "model_dump") else user.dict()
        self.table.insert(payload)
        return user

    def list(self) -> list[UserResponse]:
        return [self._to_response(record) for record in self.table.all()]

    def get_by_id(self, user_id: str) -> UserModel | None:
        query = Query()
        record = self.table.get(query.id == user_id)
        if record is None:
            return None
        return UserModel(**record)

    def get_by_email(self, email: str) -> UserModel | None:
        query = Query()
        record = self.table.get(query.email == email)
        if record is None:
            return None
        return UserModel(**record)

    def exists_by_email(self, email: str) -> bool:
        return self.get_by_email(email) is not None

    def update_email(self, user_id: str, email: str) -> UserModel | None:
        query = Query()
        updated = self.table.update({"email": email}, query.id == user_id)
        if not updated:
            return None
        record = self.table.get(query.id == user_id)
        if record is None:
            return None
        return UserModel(**record)

    def delete(self, user_id: str) -> bool:
        query = Query()
        removed = self.table.remove(query.id == user_id)
        return bool(removed)

    def _to_response(self, record: dict) -> UserResponse:
        return UserResponse(
            id=record["id"],
            email=record["email"],
            is_active=record["is_active"],
            role=record["role"],
            created_at=record["created_at"],
        )
