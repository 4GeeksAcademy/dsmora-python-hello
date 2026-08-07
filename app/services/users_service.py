from app.models.profile import ProfileModel, ProfileResponse
from app.models.user import UserCredentialsUpdate, UserModel, UserRegisterRequest, UserResponse, UserWithProfileResponse
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.users_repository import UsersRepository
from app.security import get_password_hash


class UserNotFoundError(Exception):
    pass


class UserEmailConflictError(Exception):
    pass


class UsersService:
    def __init__(
        self,
        users_repository: UsersRepository | None = None,
        profiles_repository: ProfilesRepository | None = None,
    ) -> None:
        self.users_repository = users_repository or UsersRepository()
        self.profiles_repository = profiles_repository or ProfilesRepository()

    def register_user(self, payload: UserRegisterRequest) -> UserWithProfileResponse:
        if self.users_repository.exists_by_email(payload.email):
            raise UserEmailConflictError()

        user = UserModel(
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            role=payload.role,
        )
        created_user = self.users_repository.create(user)

        profile = ProfileModel(
            user_id=created_user.id,
            name=payload.name,
            phone=payload.phone,
            address=payload.address,
        )
        created_profile = self.profiles_repository.create(profile)

        return UserWithProfileResponse(
            user=self._to_response(created_user),
            profile=ProfileResponse(**created_profile.model_dump()),
        )

    def list_users(self) -> list[UserResponse]:
        return self.users_repository.list()

    def get_user(self, user_id: str) -> UserResponse:
        user = self.users_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        return self._to_response(user)

    def update_user_email(self, user_id: str, payload: UserCredentialsUpdate) -> UserResponse:
        email = payload.email

        existing = self.users_repository.get_by_email(email)
        if existing is not None and existing.id != user_id:
            raise UserEmailConflictError()

        user = self.users_repository.update_email(user_id, email)
        if user is None:
            raise UserNotFoundError()
        return self._to_response(user)

    def delete_user(self, user_id: str) -> None:
        deleted = self.users_repository.delete(user_id)
        self.profiles_repository.delete_by_user_id(user_id)
        if not deleted:
            raise UserNotFoundError()

    def _to_response(self, user: UserModel) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            role=user.role,
            created_at=user.created_at,
        )
