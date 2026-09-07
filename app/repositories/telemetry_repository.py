from datetime import datetime
from typing import Any

from tinydb import Query

from app.db import get_db


class TelemetryRepository:
    """Repositorio append-only para eventos de telemetría en TinyDB."""

    def __init__(self) -> None:
        self.table = get_db().table("telemetry_events")

    def insert(self, event: dict[str, Any]) -> None:
        """Inserta un evento (ya serializado) en la tabla."""
        self.table.insert(event)

    def insert_bulk(self, events: list[dict[str, Any]]) -> int:
        """Inserta múltiples eventos en una sola operación.

        Returns:
            Número de eventos insertados.
        """
        for event in events:
            self.table.insert(event)
        return len(events)

    def find_by_event(
        self,
        event: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Busca eventos con filtros opcionales."""
        query = Query()
        conditions = []

        if event is not None:
            conditions.append(query.event == event)

        if from_date is not None:
            if from_date.tzinfo is None:
                from_date = from_date.replace(tzinfo=None)
            conditions.append(query.timestamp >= from_date.isoformat())

        if to_date is not None:
            if to_date.tzinfo is None:
                to_date = to_date.replace(tzinfo=None)
            conditions.append(query.timestamp <= to_date.isoformat())

        if conditions:
            combined = conditions[0]
            for cond in conditions[1:]:
                combined = combined & cond
            return self.table.search(combined)

        return self.table.all()

    def list_events(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Lista eventos con paginación."""
        all_events = self.table.all()
        return all_events[offset:offset + limit]

    def count(self) -> int:
        return len(self.table)