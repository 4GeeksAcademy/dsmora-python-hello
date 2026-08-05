from uuid import uuid4

from pydantic import BaseModel, Field


class ProfileModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    phone: str | None = Field(default=None, min_length=1)
    address: str | None = Field(default=None, min_length=1)


class ProfileResponse(BaseModel):
    id: str
    user_id: str
    name: str
    phone: str
    address: str
