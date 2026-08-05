from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.models.auth import AuthMeResponse, LoginRequest, TokenResponse
from app.models.user import UserModel
from app.services.auth_service import AuthProfileNotFoundError, AuthService, InvalidCredentialsError
from app.views.auth_view import unauthorized_exception
from app.views.profiles_view import profile_not_found_exception


router = APIRouter(prefix="/auth", tags=["auth"])
service = AuthService()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    try:
        return service.login(payload)
    except InvalidCredentialsError as error:
        raise unauthorized_exception() from error


@router.get("/me", response_model=AuthMeResponse)
def get_me(current_user: Annotated[UserModel, Depends(get_current_user)]) -> AuthMeResponse:
    try:
        return service.get_me(current_user)
    except AuthProfileNotFoundError as error:
        raise profile_not_found_exception() from error
