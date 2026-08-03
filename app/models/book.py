from enum import Enum

from pydantic import BaseModel, Field


class BookGenre(str, Enum):
    fiction = "fiction"
    non_fiction = "non-fiction"
    mystery = "mystery"
    sci_fi = "sci-fi"


class BookStatus(str, Enum):
    available = "available"
    checked_out = "checked_out"


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    genre: BookGenre
    pages: int = Field(..., gt=0)
    status: BookStatus


class BookStatusUpdate(BaseModel):
    status: BookStatus


class BookResponse(BookCreate):
    id: int