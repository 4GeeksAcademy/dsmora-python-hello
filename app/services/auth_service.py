from app.models.auth import AuthMeResponse, LoginRequest, TokenResponse
from app.models.profile import ProfileResponse
from app.models.user import UserModel
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.users_repository import UsersRepository
from app.security import create_access_token, verify_password


class InvalidCredentialsError(Exception):
    pass


class AuthProfileNotFoundError(Exception):
    pass


class AuthService:
    def __init__(
        self,
        users_repository: UsersRepository | None = None,
        profiles_repository: ProfilesRepository | None = None,
    ) -> None:
        self.users_repository = users_repository or UsersRepository()
        self.profiles_repository = profiles_repository or ProfilesRepository()

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.users_repository.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise InvalidCredentialsError()

        token = create_access_token({"sub": user.id, "role": user.role.value, "email": user.email})
        return TokenResponse(access_token=token)

    def get_me(self, current_user: UserModel) -> AuthMeResponse:
        profile = self.profiles_repository.get_by_user_id(current_user.id)
        if profile is None:
            raise AuthProfileNotFoundError()

        return AuthMeResponse(
            email=current_user.email,
            role=current_user.role,
            profile=ProfileResponse(**profile.model_dump()),
        )
