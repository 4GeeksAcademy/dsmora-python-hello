from pydantic import BaseModel, Field

from app.models.profile import ProfileResponse
from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthMeResponse(BaseModel):
    email: str
    role: UserRole
    profile: ProfileResponse


class AuthAuthorizeResponse(BaseModel):
    authorized: bool = True
    role: UserRole
