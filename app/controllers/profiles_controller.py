from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.models.profile import ProfileResponse, ProfileUpdate
from app.models.user import UserModel
from app.services.profiles_service import ProfileNotFoundError, ProfilesService
from app.views.profiles_view import profile_not_found_exception


router = APIRouter(prefix="/profiles", tags=["profiles"])
service = ProfilesService()


@router.get("/me", response_model=ProfileResponse)
def get_profile_me(current_user: Annotated[UserModel, Depends(get_current_user)]) -> ProfileResponse:
    try:
        return service.get_my_profile(current_user.id)
    except ProfileNotFoundError as error:
        raise profile_not_found_exception() from error


@router.put("/me", response_model=ProfileResponse)
def update_profile_me(
    payload: ProfileUpdate,
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> ProfileResponse:
    try:
        return service.update_my_profile(current_user.id, payload)
    except ProfileNotFoundError as error:
        raise profile_not_found_exception() from error
