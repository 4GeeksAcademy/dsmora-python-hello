from app.db import get_db
from app.models.profile import ProfileModel
from tinydb import Query


class ProfilesRepository:
    def __init__(self) -> None:
        self.table = get_db().table("profiles")

    def create(self, profile: ProfileModel) -> ProfileModel:
        payload = profile.model_dump(mode="json") if hasattr(profile, "model_dump") else profile.dict()
        self.table.insert(payload)
        return profile

    def get_by_user_id(self, user_id: str) -> ProfileModel | None:
        query = Query()
        record = self.table.get(query.user_id == user_id)
        if record is None:
            return None
        return ProfileModel(**record)

    def update_by_user_id(self, user_id: str, payload: dict) -> ProfileModel | None:
        query = Query()
        updated = self.table.update(payload, query.user_id == user_id)
        if not updated:
            return None
        record = self.table.get(query.user_id == user_id)
        if record is None:
            return None
        return ProfileModel(**record)

    def delete_by_user_id(self, user_id: str) -> bool:
        query = Query()
        removed = self.table.remove(query.user_id == user_id)
        return bool(removed)
