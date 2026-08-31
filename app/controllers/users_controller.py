from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.dependencies.auth import get_current_user
from app.models.auth import TokenResponse
from app.models.user import UserCredentialsUpdate, UserModel, UserRegisterRequest, UserResponse, UserWithProfileResponse
from app.security import create_access_token
from app.services.users_service import UserEmailConflictError, UserNotFoundError, UsersService
from app.views.auth_view import forbidden_exception
from app.views.users_view import user_conflict_exception, user_not_found_exception


router = APIRouter(prefix="/users", tags=["users"])
service = UsersService()


@router.post("", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserRegisterRequest) -> TokenResponse:
    try:
        registration = service.register_user(payload)
        user = registration.user
        token = create_access_token({"sub": user.id, "role": user.role.value, "email": user.email})
        return TokenResponse(access_token=token)
    except UserEmailConflictError as error:
        raise user_conflict_exception() from error


@router.get("", response_model=list[UserResponse])
def list_users(current_user: Annotated[UserModel, Depends(get_current_user)]) -> list[UserResponse]:
    _ = current_user
    return service.list_users()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, current_user: Annotated[UserModel, Depends(get_current_user)]) -> UserResponse:
    _ = current_user
    try:
        return service.get_user(user_id)
    except UserNotFoundError as error:
        raise user_not_found_exception() from error


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserCredentialsUpdate,
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> UserResponse:
    if current_user.id != user_id:
        raise forbidden_exception("You can only update your own user")

    try:
        return service.update_user_email(user_id, payload)
    except UserNotFoundError as error:
        raise user_not_found_exception() from error
    except UserEmailConflictError as error:
        raise user_conflict_exception() from error


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, current_user: Annotated[UserModel, Depends(get_current_user)]) -> Response:
    if current_user.id != user_id:
        raise forbidden_exception("You can only delete your own user")

    try:
        service.delete_user(user_id)
    except UserNotFoundError as error:
        raise user_not_found_exception() from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
