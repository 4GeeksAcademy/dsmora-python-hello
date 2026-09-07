from typing import Annotated, Optional

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.models.user import UserModel
from app.repositories.users_repository import UsersRepository
from app.security import decode_access_token
from app.views.auth_view import forbidden_exception, unauthorized_exception


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserModel:
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or user_id == "":
            raise unauthorized_exception()
    except JWTError as error:
        raise unauthorized_exception() from error

    user = UsersRepository().get_by_id(user_id)
    if user is None:
        raise unauthorized_exception()
    return user


def get_optional_current_user(token: Annotated[Optional[str], Depends(oauth2_scheme)]) -> UserModel | None:
    """Devuelve el usuario si hay JWT válido, o None si no hay token."""
    if token is None:
        return None
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or user_id == "":
            return None
    except JWTError:
        return None

    user = UsersRepository().get_by_id(user_id)
    return user


def require_roles(current_user: UserModel, allowed_roles: set[str]) -> None:
    if current_user.role.value not in allowed_roles:
        raise forbidden_exception("Insufficient permissions")
