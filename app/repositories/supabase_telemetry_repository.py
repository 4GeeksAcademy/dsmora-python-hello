"""
Repositorio de telemetría con Supabase como backend real (Fase 5).

Reemplaza TinyDB cuando SUPABASE_URL y SUPABASE_SERVICE_ROLE_KEY están configuradas.
Usa la REST API de Supabase para bulk insert y consultas.
"""

from datetime import datetime
from typing import Any

import httpx

from app.config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_TELEMETRY_TABLE, SUPABASE_URL


class SupabaseTelemetryRepository:
    """Repositorio de telemetría con Supabase como backend.

    Los eventos son inmutables (solo INSERT, nunca UPDATE/DELETE).
    """

    def __init__(self) -> None:
        self._base_url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TELEMETRY_TABLE}"
        self._headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        self._available = bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)

    def is_available(self) -> bool:
        return self._available

    def insert_bulk(self, rows: list[dict[str, Any]]) -> int:
        """Inserta múltiples filas en telemetry_events en una sola operación.

        Cada fila debe tener: timestamp, service, event_type, level, tags.
        """
        if not self._available or not rows:
            return 0

        try:
            response = httpx.post(self._base_url, headers=self._headers, json=rows, timeout=10)
            response.raise_for_status()
            return len(rows)
        except httpx.HTTPStatusError as e:
            print(f"Supabase insert error: {e.response.status_code} {e.response.text[:200]}")
            return 0
        except httpx.RequestError as e:
            print(f"Supabase connection error: {e}")
            return 0

    def query(
        self,
        event_type: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Consulta eventos con filtros opcionales."""
        if not self._available:
            return []

        params: list[tuple[str, str]] = []
        params.append(("limit", str(limit)))
        params.append(("offset", str(offset)))
        params.append(("order", "timestamp.desc"))

        if event_type:
            params.append(("event_type", f"eq.{event_type}"))
        if from_date:
            params.append(("timestamp", f"gte.{from_date.isoformat()}"))
        if to_date:
            params.append(("timestamp", f"lte.{to_date.isoformat()}"))

        try:
            response = httpx.get(
                self._base_url,
                headers=self._headers,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Supabase query error: {e}")
            return []

    def count(self, event_type: str | None = None) -> int:
        """Cuenta eventos (opcionalmente por tipo)."""
        if not self._available:
            return 0

        headers = {**self._headers, "Accept": "application/json"}
        params: list[tuple[str, str]] = [("select", "count")]

        if event_type:
            params.append(("event_type", f"eq.{event_type}"))

        try:
            response = httpx.get(
                self._base_url,
                headers=headers,
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            # Supabase devuelve el count en un header o en el body
            content_range = response.headers.get("content-range", "0-0/0")
            total = content_range.split("/")[-1]
            return int(total) if total.isdigit() else 0
        except Exception:
            return 0