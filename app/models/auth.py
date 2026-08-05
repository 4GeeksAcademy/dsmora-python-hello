from pydantic import BaseModel, Field

from app.models.profile import ProfileResponse


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthMeResponse(BaseModel):
    email: str
    profile: ProfileResponse
