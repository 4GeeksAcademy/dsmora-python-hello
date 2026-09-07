"""
Pipeline de análisis de telemetría con Pandas.

Cada función de métrica es independiente y libre de efectos secundarios.
Sigue el orden: cargar (SQL) → refinar (Pandas) → convertir tipos → agrupar → agregar → servir.

Las funciones cargan desde Supabase (si está configurado) o desde TinyDB como fallback.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
from dateutil import parser as dateparser

from app.config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_TELEMETRY_TABLE, SUPABASE_URL
from app.repositories.telemetry_repository import TelemetryRepository


def _get_events_supabase(
    event_types: list[str] | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> pd.DataFrame:
    """Carga eventos desde Supabase (filtrados por SQL)."""
    from app.repositories.supabase_telemetry_repository import SupabaseTelemetryRepository

    repo = SupabaseTelemetryRepository()
    if not repo.is_available():
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    # Cargar por cada tipo si hay filtro, o todos si no
    if event_types:
        for evt in event_types:
            rows.extend(repo.query(event_type=evt, from_date=start_date, to_date=end_date, limit=5000))
    else:
        rows.extend(repo.query(from_date=start_date, to_date=end_date, limit=5000))

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _get_events_tinydb(
    event_types: list[str] | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> pd.DataFrame:
    """Carga eventos desde TinyDB (fallback cuando Supabase no está disponible)."""
    repo = TelemetryRepository()
    all_events: list[dict[str, Any]] = repo.find_by_event(from_date=start_date, to_date=end_date)

    if not all_events:
        return pd.DataFrame()

    df = pd.DataFrame(all_events)

    # Si hay columna 'event', filtrar por tipo
    if event_types and "event" in df.columns:
        df = df[df["event"].isin(event_types)]

    return df


def _load_events(
    event_types: list[str] | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> pd.DataFrame:
    """Carga eventos desde Supabase o TinyDB según disponibilidad."""
    # Intentar Supabase primero
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        df = _get_events_supabase(event_types, start_date, end_date)
        if not df.empty:
            return df

    # Fallback a TinyDB
    df = _get_events_tinydb(event_types, start_date, end_date)
    return df


def _normalize_timestamp(df: pd.DataFrame, col: str = "timestamp") -> pd.DataFrame:
    """Convierte columna timestamp a datetime y extrae fecha."""
    if col not in df.columns:
        return df

    # Convertir a datetime (maneja strings ISO 8601 y timestamps nativos)
    try:
        df[col] = pd.to_datetime(df[col], utc=True)
    except Exception:
        try:
            df[col] = df[col].apply(lambda x: dateparser.parse(str(x)))
        except Exception:
            pass

    # Extraer fecha para agrupación diaria
    if "date" not in df.columns:
        df["date"] = df[col].dt.date
    df["date"] = pd.to_datetime(df["date"])

    return df


# ── Métricas (Fase 1 del pipeline) ──────────────────────────────────


def metric_events_per_day(
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    """Volumen de eventos por tipo y por día.

    Responde: ¿qué eventos ocurren, con qué frecuencia?
    """
    df = _load_events(start_date=start_date, end_date=end_date)
    if df.empty:
        return []

    df = _normalize_timestamp(df)

    # Determinar columna de tipo de evento
    event_col = "event_type" if "event_type" in df.columns else "event" if "event" in df.columns else None
    if event_col is None:
        return []

    # Agrupar por fecha y tipo de evento
    grouped = df.groupby(["date", event_col]).size().reset_index(name="count")
    grouped = grouped.sort_values(["date", event_col])

    return grouped.reset_index(drop=True).to_dict(orient="records")


def metric_error_rate_by_type(
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    """Tasa de error por día.

    Calcula eventos de fallo (book.reservation_failed, user.login_failed)
    como proporción del total de eventos de su categoría.

    Responde: ¿qué proporción de operaciones fallan?
    """
    error_types = ["book.reservation_failed", "user.login_failed"]
    total_types = [
        "book.reservation_failed", "book.reserved",
        "user.login_failed", "user.logged_in",
    ]

    df = _load_events(event_types=total_types, start_date=start_date, end_date=end_date)
    if df.empty:
        return []

    df = _normalize_timestamp(df)
    event_col = "event_type" if "event_type" in df.columns else "event" if "event" in df.columns else None
    if event_col is None:
        return []

    # Clasificar errores
    df["is_error"] = df[event_col].isin(error_types)

    # Agrupar por fecha: total eventos y total errores
    grouped = df.groupby("date").agg(
        total_events=pd.NamedAgg(column=event_col, aggfunc="count"),
        error_count=pd.NamedAgg(column="is_error", aggfunc="sum"),
    ).reset_index()

    # Calcular tasa
    grouped["error_rate"] = (grouped["error_count"] / grouped["total_events"]).round(4)
    grouped = grouped.sort_values("date")

    return grouped.reset_index(drop=True).to_dict(orient="records")


def metric_auth_failure_rate(
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    """Tasa diaria de fallos de autenticación.

    Calcula user.login_failed / (user.login_failed + user.logged_in) por día.

    Responde: ¿qué proporción de intentos de login fallan?
    """
    auth_types = ["user.login_failed", "user.logged_in"]

    df = _load_events(event_types=auth_types, start_date=start_date, end_date=end_date)
    if df.empty:
        return []

    df = _normalize_timestamp(df)
    event_col = "event_type" if "event_type" in df.columns else "event" if "event" in df.columns else None
    if event_col is None:
        return []

    # Contar por fecha y tipo
    grouped = df.groupby(["date", event_col]).size().reset_index(name="count")

    # Pivot: una fila por fecha, columnas para cada tipo
    pivot = grouped.pivot_table(
        index="date",
        columns=event_col,
        values="count",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    # Asegurar que ambas columnas existan
    failed_col = "user.login_failed"
    success_col = "user.logged_in"

    total_col = "total_attempts"
    if failed_col in pivot.columns and success_col in pivot.columns:
        pivot[total_col] = pivot[failed_col] + pivot[success_col]
        pivot["failure_rate"] = (pivot[failed_col] / pivot[total_col]).round(4)
    elif failed_col in pivot.columns:
        pivot[total_col] = pivot[failed_col]
        pivot["failure_rate"] = 1.0
    elif success_col in pivot.columns:
        pivot[total_col] = pivot[success_col]
        pivot["failure_rate"] = 0.0
    else:
        return []

    pivot = pivot.sort_values("date")
    return pivot.reset_index(drop=True).to_dict(orient="records")


def metric_reservation_success_rate(
    start_date: datetime,
    end_date: datetime,
) -> list[dict[str, Any]]:
    """Tasa diaria de éxito en reservas.

    Calcula book.reserved / (book.reserved + book.reservation_failed) por día.

    Responde: ¿qué proporción de intentos de reserva son exitosos?
    """
    reserve_types = ["book.reserved", "book.reservation_failed"]

    df = _load_events(event_types=reserve_types, start_date=start_date, end_date=end_date)
    if df.empty:
        return []

    df = _normalize_timestamp(df)
    event_col = "event_type" if "event_type" in df.columns else "event" if "event" in df.columns else None
    if event_col is None:
        return []

    grouped = df.groupby(["date", event_col]).size().reset_index(name="count")

    pivot = grouped.pivot_table(
        index="date",
        columns=event_col,
        values="count",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    success_col = "book.reserved"
    fail_col = "book.reservation_failed"

    total_col = "total_attempts"
    if success_col in pivot.columns and fail_col in pivot.columns:
        pivot[total_col] = pivot[success_col] + pivot[fail_col]
        pivot["success_rate"] = (pivot[success_col] / pivot[total_col]).round(4)
    elif success_col in pivot.columns:
        pivot[total_col] = pivot[success_col]
        pivot["success_rate"] = 1.0
    elif fail_col in pivot.columns:
        pivot[total_col] = pivot[fail_col]
        pivot["success_rate"] = 0.0
    else:
        return []

    pivot = pivot.sort_values("date")
    return pivot.reset_index(drop=True).to_dict(orient="records")