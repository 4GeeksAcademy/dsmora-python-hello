from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from app.models.book import BookResponse
from pydantic import BaseModel, Field


class ReservationStatus(str, Enum):
    reserved = "reserved"
    cancelled = "cancelled"


class ReservedBookModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str = Field(..., min_length=1)
    book_id: int = Field(..., gt=0)
    status: ReservationStatus = ReservationStatus.reserved
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReservedBookResponse(BaseModel):
    id: str
    user_id: str
    book_id: int
    status: ReservationStatus
    created_at: datetime
    book: BookResponse | None = None
