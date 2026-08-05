from app.models.profile import ProfileResponse, ProfileUpdate
from app.repositories.profiles_repository import ProfilesRepository


class ProfileNotFoundError(Exception):
    pass


class ProfilesService:
    def __init__(self, repository: ProfilesRepository | None = None) -> None:
        self.repository = repository or ProfilesRepository()

    def get_my_profile(self, user_id: str) -> ProfileResponse:
        profile = self.repository.get_by_user_id(user_id)
        if profile is None:
            raise ProfileNotFoundError()
        return ProfileResponse(**profile.model_dump())

    def update_my_profile(self, user_id: str, payload: ProfileUpdate) -> ProfileResponse:
        update_payload = payload.model_dump(exclude_none=True)
        if not update_payload:
            profile = self.repository.get_by_user_id(user_id)
            if profile is None:
                raise ProfileNotFoundError()
            return ProfileResponse(**profile.model_dump())

        updated_profile = self.repository.update_by_user_id(user_id, update_payload)
        if updated_profile is None:
            raise ProfileNotFoundError()
        return ProfileResponse(**updated_profile.model_dump())
