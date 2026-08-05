from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from app.models.profile import ProfileResponse
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    user = "user"


class UserCreate(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)


class UserRegisterRequest(UserCreate):
    name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)


class UserCredentialsUpdate(BaseModel):
    email: str = Field(..., min_length=1)


class UserModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    email: str = Field(..., min_length=1)
    hashed_password: str
    is_active: bool = True
    role: UserRole = UserRole.user
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserResponse(BaseModel):
    id: str
    email: str
    is_active: bool
    role: UserRole
    created_at: datetime


class UserWithProfileResponse(BaseModel):
    user: UserResponse
    profile: ProfileResponse
