import json
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status

from app.config import APP_VERSION, MAX_EVENT_BATCH_SIZE, TELEMETRY_ENV
from app.dependencies.auth import get_current_user, get_optional_current_user, require_roles
from app.models.telemetry import AllowedEvent, EventEnvelope
from app.models.user import UserModel
from app.repositories.telemetry_repository import TelemetryRepository
from app.services.telemetry_service import telemetry_service
from app.views.auth_view import unauthorized_exception
from app.telemetry_analysis import (
    metric_auth_failure_rate,
    metric_error_rate_by_type,
    metric_events_per_day,
    metric_reservation_success_rate,
)


router = APIRouter(prefix="/telemetry", tags=["telemetry"])
repository = TelemetryRepository()


# --- Simple in-memory rate limiter (IP-based) ---
_rate_limit_store: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW_SEC = 10
RATE_LIMIT_MAX = 30


def _check_rate_limit(client_id: str) -> bool:
    """Returns True if request is allowed, False if rate-limited."""
    now = datetime.now(timezone.utc).timestamp()
    window_start = now - RATE_LIMIT_WINDOW_SEC

    timestamps = _rate_limit_store.get(client_id, [])
    # Keep only timestamps within the window
    timestamps = [t for t in timestamps if t > window_start]
    timestamps.append(now)
    _rate_limit_store[client_id] = timestamps

    return len(timestamps) <= RATE_LIMIT_MAX


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/events")
async def ingest_events(
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Annotated[UserModel | None, Depends(get_optional_current_user)] = None,
) -> dict:
    """Endpoint de ingesta para telemetría (frontend y externos).

    Acepta un batch de eventos. Realiza validación por evento (parseo laxo).
    Los eventos inválidos se rechazan individualmente sin cancelar el lote.

    Rate-limiting por IP/session_id.
    """
    # Rate limiting
    client_ip = _get_client_ip(request)
    if not _check_rate_limit(client_ip):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    # Parse body
    try:
        body = await request.json()
    except (json.JSONDecodeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body")

    raw_events = body.get("events", []) if isinstance(body, dict) else body

    if not isinstance(raw_events, list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Body must contain an events array")

    # Anti-abuse: limit batch size
    if len(raw_events) > MAX_EVENT_BATCH_SIZE * 2:
        raw_events = raw_events[:MAX_EVENT_BATCH_SIZE]

    total = len(raw_events)
    stored = 0
    rejected = 0
    valid_events: list[EventEnvelope] = []

    for raw in raw_events:
        if not isinstance(raw, dict):
            rejected += 1
            continue

        try:
            event = EventEnvelope.model_validate(raw)
        except Exception:
            rejected += 1
            continue

        # Validar event contra whitelist cerrada
        try:
            AllowedEvent(event.event)
        except ValueError:
            rejected += 1
            continue

        # Seguridad: si hay JWT válido, sobrescribir user_id con el sub del token
        if current_user is not None:
            event.user_id = current_user.id
            event.anonymous_id = None  # Si hay sesión autenticada, no hay anónimo
        elif event.anonymous_id:
            event.user_id = None  # Anónimo, sin user_id
        else:
            rejected += 1
            continue  # Sin JWT ni anonymous_id, no podemos identificar

        # Validar tamaño del payload
        try:
            payload_size = len(json.dumps(event.model_dump(mode="json"), default=str))
            if payload_size > 10240:  # 10KB max por evento
                rejected += 1
                continue
        except Exception:
            rejected += 1
            continue

        # Sanitizar properties y context (eliminar campos sensibles)
        event.properties = _sanitize_properties(event.properties)
        event.context = _sanitize_properties(event.context)

        valid_events.append(event)

    # Encolar en BackgroundTasks para no bloquear la respuesta
    if valid_events:
        background_tasks.add_task(_store_batch, valid_events)

    return {
        "received": total,
        "stored": len(valid_events),
        "rejected": rejected,
    }


def _sanitize_properties(data: dict) -> dict:
    """Elimina campos sensibles."""
    sensitive = {"password", "hashed_password", "token", "access_token", "secret"}
    return {k: v for k, v in data.items() if k.lower() not in sensitive}


def _store_batch(events: list[EventEnvelope]) -> None:
    """Almacena un batch de eventos en TinyDB."""
    for event in events:
        telemetry_service.track(event)


# --- Endpoint admin de consulta (Fase 4) ---

@router.get("/events", response_model=list[dict])
def query_events(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    event: str | None = Query(None, description="Filtrar por tipo de evento"),
    from_date: str | None = Query(None, description="Fecha inicio (ISO 8601)"),
    to_date: str | None = Query(None, description="Fecha fin (ISO 8601)"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    """Consulta eventos de telemetría. Solo admin."""
    require_roles(current_user, {"admin"})

    parsed_from = None
    parsed_to = None
    if from_date:
        parsed_from = datetime.fromisoformat(from_date)
    if to_date:
        parsed_to = datetime.fromisoformat(to_date)

    return repository.find_by_event(event=event, from_date=parsed_from, to_date=parsed_to)[offset:offset + limit]


@router.get("/count")
def count_events(
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> dict:
    """Cuenta total de eventos. Solo admin."""
    require_roles(current_user, {"admin"})
    return {"count": repository.count()}


# ── Simple in-memory cache for report ──
_report_cache: dict[str, tuple[float, dict]] = {}
REPORT_CACHE_TTL_SEC = 60


def _get_cached_or_compute(cache_key: str, compute_fn) -> dict:
    import time
    now = time.time()
    cached = _report_cache.get(cache_key)
    if cached and (now - cached[0]) < REPORT_CACHE_TTL_SEC:
        return cached[1]
    result = compute_fn()
    _report_cache[cache_key] = (now, result)
    return result


@router.get("/report")
def get_telemetry_report(
    current_user: Annotated[UserModel, Depends(get_current_user)],
    start_date: str | None = Query(None, description="Fecha inicio (ISO 8601)"),
    end_date: str | None = Query(None, description="Fecha fin (ISO 8601)"),
) -> dict:
    """Reporte de métricas operacionales de telemetría. Solo admin."""
    require_roles(current_user, {"admin"})

    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)

    # Resolver el período una sola vez
    if start_date:
        period_from = datetime.fromisoformat(start_date)
        if period_from.tzinfo is None:
            period_from = period_from.replace(tzinfo=timezone.utc)
    else:
        period_from = now - timedelta(days=7)

    if end_date:
        period_to = datetime.fromisoformat(end_date)
        if period_to.tzinfo is None:
            period_to = period_to.replace(tzinfo=timezone.utc)
    else:
        period_to = now

    # Cache key incluye los parámetros
    cache_key = f"report_{period_from.isoformat()}_{period_to.isoformat()}"

    def compute_report():
        return {
            "period": {
                "from": period_from.isoformat(),
                "to": period_to.isoformat(),
            },
            "metrics": {
                "events_per_day": metric_events_per_day(period_from, period_to),
                "error_rate_by_type": metric_error_rate_by_type(period_from, period_to),
                "auth_failure_rate": metric_auth_failure_rate(period_from, period_to),
                "reservation_success_rate": metric_reservation_success_rate(period_from, period_to),
            },
        }

    return _get_cached_or_compute(cache_key, compute_report)