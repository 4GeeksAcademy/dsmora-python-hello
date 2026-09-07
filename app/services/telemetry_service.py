import json
from datetime import datetime

from app.config import APP_VERSION, TELEMETRY_ENABLED, TELEMETRY_ENV, MAX_CONTEXT_SIZE_BYTES
from app.models.telemetry import AllowedEvent, EventEnvelope
from app.repositories.telemetry_repository import TelemetryRepository


SENSITIVE_FIELDS = {"password", "hashed_password", "token", "access_token", "secret"}


class TelemetryService:
    """Servicio central de telemetría.

    ÚNICA función para emitir eventos en backend.
    Si TELEMETRY_ENABLED=false, track() es no-op.
    """

    def __init__(self, repository: TelemetryRepository | None = None, enabled: bool = TELEMETRY_ENABLED):
        self._repository = repository or TelemetryRepository()
        self._enabled = enabled

    def track(self, event: EventEnvelope) -> None:
        """Emite un evento de telemetría.

        Si TELEMETRY_ENABLED=false, es no-op (evita overhead en tests/CI).
        """
        if not self._enabled:
            return

        # Seguridad: validar contra whitelist
        try:
            AllowedEvent(event.event)
        except ValueError:
            # Evento no permitido — lo rechazamos silenciosamente
            return

        # Seguridad: sanitizar properties
        sanitized = self._sanitize(event.properties)
        event.properties = sanitized

        # Seguridad: sanitizar context
        event.context = self._sanitize(event.context)

        # Validar tamaño del payload
        payload_size = len(json.dumps(event.model_dump(mode="json"), default=str))
        if payload_size > MAX_CONTEXT_SIZE_BYTES:
            event.properties["_truncated"] = True
            # Truncar context y properties si exceden
            while len(json.dumps(event.model_dump(mode="json"), default=str)) > MAX_CONTEXT_SIZE_BYTES:
                event.context = dict(list(event.context.items())[:len(event.context) // 2])
                event.properties = dict(list(event.properties.items())[:len(event.properties) // 2])

        self._repository.insert(event.model_dump(mode="json"))

    def track_bulk(self, events: list[EventEnvelope]) -> tuple[int, int, int]:
        """Inserta múltiples eventos válidos en bulk.

        Returns:
            (received, stored, rejected)
        """
        if not self._enabled:
            return len(events), 0, len(events)

        valid: list[dict] = []
        rejected = 0

        for event in events:
            # Validar contra whitelist
            try:
                AllowedEvent(event.event)
            except ValueError:
                rejected += 1
                continue

            # Sanitizar
            event.properties = self._sanitize(event.properties)
            event.context = self._sanitize(event.context)

            # Validar tamaño
            payload_size = len(json.dumps(event.model_dump(mode="json"), default=str))
            if payload_size > MAX_CONTEXT_SIZE_BYTES:
                rejected += 1
                continue

            valid.append(event.model_dump(mode="json"))

        stored = self._repository.insert_bulk(valid)
        return len(events), stored, rejected

    def _sanitize(self, data: dict) -> dict:
        """Elimina campos sensibles del payload."""
        return {k: v for k, v in data.items() if k.lower() not in SENSITIVE_FIELDS}


# Instancia singleton para usar en toda la app
telemetry_service = TelemetryService()