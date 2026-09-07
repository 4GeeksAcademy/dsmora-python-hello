from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AllowedEvent(str, Enum):
    """Whitelist cerrada de eventos de telemetría."""
    book_viewed = "book.viewed"
    book_listed = "book.listed"
    book_reserved = "book.reserved"
    book_reservation_failed = "book.reservation_failed"
    book_released = "book.released"
    user_registered = "user.registered"
    user_logged_in = "user.logged_in"
    user_login_failed = "user.login_failed"


class EventSource(str, Enum):
    backend_api = "backend-api"
    frontend_web = "frontend-web"


class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid4()}")
    event: str = Field(..., min_length=1, max_length=100)
    schema_version: str = "1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: str | None = None
    anonymous_id: str | None = None
    session_id: str
    context: dict[str, Any] = Field(default_factory=dict)
    properties: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TelemetryEvent(BaseModel):
    """Modelo para el pipeline de análisis con Supabase.

    Mapea las columnas de la tabla telemetry_events.
    """
    event_type: str
    timestamp: datetime
    service: str = "backoffice"
    level: str = "info"
    value: float | None = None
    message: str | None = None
    tags: dict[str, Any] = Field(default_factory=dict)