from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.dependencies.auth import get_current_user, require_roles
from app.models.auth import AuthAuthorizeResponse, AuthMeResponse, LoginRequest, TokenResponse
from app.models.user import UserModel, UserRole
from app.services.auth_service import AuthProfileNotFoundError, AuthService, InvalidCredentialsError
from app.views.auth_view import unauthorized_exception
from app.views.profiles_view import profile_not_found_exception


router = APIRouter(prefix="/auth", tags=["auth"])
service = AuthService()


@router.post("/login", response_model=TokenResponse)
async def login(request: Request) -> TokenResponse:
    try:
        payload = await _parse_login_request(request)
        return service.login(payload)
    except InvalidCredentialsError as error:
        raise unauthorized_exception() from error


async def _parse_login_request(request: Request) -> LoginRequest:
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        raw_payload = await request.json()
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form_data = await request.form()
        raw_payload = {
            "email": form_data.get("username", ""),
            "password": form_data.get("password", ""),
        }
    else:
        raw_payload = await request.json()

    try:
        return LoginRequest.model_validate(raw_payload)
    except ValidationError as error:
        raise RequestValidationError(error.errors()) from error


@router.get("/me", response_model=AuthMeResponse)
def get_me(current_user: Annotated[UserModel, Depends(get_current_user)]) -> AuthMeResponse:
    try:
        return service.get_me(current_user)
    except AuthProfileNotFoundError as error:
        raise profile_not_found_exception() from error


@router.get("/authorize", response_model=AuthAuthorizeResponse)
def authorize_by_role(
    allowed_roles: Annotated[list[UserRole], Query(min_length=1)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> AuthAuthorizeResponse:
    require_roles(current_user, {role.value for role in allowed_roles})
    return AuthAuthorizeResponse(authorized=True, role=current_user.role)
