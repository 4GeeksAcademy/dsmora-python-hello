from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.config import APP_VERSION, TELEMETRY_ENV
from app.dependencies.auth import get_current_user, require_roles
from app.models.auth import AuthAuthorizeResponse, AuthMeResponse, LoginRequest, TokenResponse
from app.models.telemetry import EventEnvelope
from app.models.user import UserModel, UserRole
from app.services.auth_service import AuthProfileNotFoundError, AuthService, InvalidCredentialsError
from app.services.telemetry_service import telemetry_service
from app.views.auth_view import unauthorized_exception
from app.views.profiles_view import profile_not_found_exception


router = APIRouter(prefix="/auth", tags=["auth"])
service = AuthService()


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, background_tasks: BackgroundTasks) -> TokenResponse:
    try:
        payload = await _parse_login_request(request)
        result = service.login(payload)
        background_tasks.add_task(
            telemetry_service.track,
            EventEnvelope(
                event="user.logged_in",
                session_id=f"srv_login",
                context={"email": payload.email},
                metadata={"source": "backend-api", "environment": TELEMETRY_ENV, "app_version": APP_VERSION},
            ),
        )
        return result
    except InvalidCredentialsError as error:
        background_tasks.add_task(
            telemetry_service.track,
            EventEnvelope(
                event="user.login_failed",
                session_id=f"srv_login",
                context={"email": payload.email if 'payload' in locals() else "unknown"},
                properties={"reason": "invalid_credentials"},
                metadata={"source": "backend-api", "environment": TELEMETRY_ENV, "app_version": APP_VERSION},
            ),
        )
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
