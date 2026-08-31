# Plan Estructurado de Telemetría — Book Manager

> Documento sintetizado a partir de `telemetry.ts`, `TELEMETRY-PLAN.md` y `TELEMETRY-SCHEMA.md`.

---

## 1. Visión General

Implementar un sistema de telemetría basado en **Event Envelope** que capture acciones de usuarios y eventos del sistema en los dominios de libros y autenticación.

**Principio fundamental: Toda la telemetría pasa por una única función `track()`**, tanto en frontend como en backend:

| Capa | Función | Ubicación |
|------|---------|-----------|
| **Frontend** | `track(event, context?, properties?)` | `frontend/lib/telemetry.ts` |
| **Backend** | `telemetry_service.track(event: EventEnvelope)` | `app/services/telemetry_service.py` |

El sistema es **bidireccional**: el frontend captura interacciones del usuario (vistas, clics) y el backend emite eventos del dominio (reservas, auth). Ambos convergen en el mismo endpoint de ingesta (`POST /telemetry/events`) y se almacenan en TinyDB.

**Stack**: FastAPI (backend), Next.js/React (frontend), TinyDB (sink inicial).

---

## 2. Arquitectura del Evento (Event Envelope)

### 2.1 Schema unificado

Basado en `TELEMETRY-SCHEMA.md` con ajustes desde `telemetry.ts`:

```jsonc
{
  "event_id": "evt_<uuid4>",                          // Deduplicación / idempotencia
  "event": "book.reserved",                            // namespace.accion (dot-case)
  "schema_version": "1.0",
  "timestamp": "2026-08-31T16:31:07.676Z",             // ISO 8601 UTC
  "user_id": "uuid" | null,                            // Del JWT (backend) o token (frontend)
  "anonymous_id": "anon_<uuid>" | null,                // localStorage, visitante anónimo
  "session_id": "s_<uuid>",                            // sessionStorage, una por pestaña/sesión
  "context": { ... },                                   // Referencias a entidades (book_id, role, etc.)
  "properties": { ... },                                // Métricas/atributos (nunca datos sensibles)
  "metadata": {                                         // Información técnica
    "source": "frontend-web" | "backend-api",
    "environment": "dev" | "staging" | "production",
    "app_version": "1.0.0"
  }
}
```

### 2.2 Controles de calidad desde `telemetry.ts` (5 Puntos de Verificación)

| # | Punto | Descripción |
|---|-------|-------------|
| 1 | **Consentimiento** | Verificar que el usuario haya aceptado tracking antes de enviar eventos. |
| 2 | **Sanitización** | Limpiar datos sensibles (passwords, tokens, PII) antes de construir el envelope. |
| 3 | **Whitelist de propiedades** | Solo enviar propiedades permitidas; descartar lo no listado. |
| 4 | **Sampling** | Seleccionar una muestra representativa en entornos de alta carga (ej. 1 de cada 10 eventos en prod). |
| 5 | **Entorno correcto** | Asegurar que los eventos se enruten al endpoint correspondiente (dev/staging/prod). |

---

## 3. Taxonomía de Eventos

| Evento | Origen | Disparador |
|--------|--------|------------|
| `book.viewed` | frontend | Vista de detalle `pages/books/[id].tsx` |
| `book.listed` | frontend | Home `pages/index.tsx` (al aplicar filtros) |
| `book.reserved` | backend | `BooksService.reserve_book` (éxito) |
| `book.reservation_failed` | backend | `BookUnavailableError` en reserve_book |
| `book.released` | backend | `BooksService.release_book` (éxito) |
| `user.registered` | backend | `UsersService.register_user` |
| `user.logged_in` | backend | Login exitoso en auth_service |
| `user.login_failed` | backend | Credenciales inválidas en auth_service |

**Eventos propuestos desde `telemetry.ts`** (a evaluar para futura expansión):
- Filtros aplicados (búsqueda/género)
- Click en "Reservar" (BookCard)
- Click en "Liberar libro" (reservations)
- Vistas de login/registro
- Errores capturados por ErrorBoundary (React)

---

## 4. Backend — Implementación

### 4.1 Configuración (Fase 0)

- **`app/config.py`**: Leer variable `TELEMETRY_ENABLED` (booleano, default `True`).
- **`app/db.py`**: Agregar `telemetry_events` a `DEFAULT_TABLES`.

### 4.2 Modelo Pydantic (`app/models/telemetry.py`)

```python
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

class EventSource(str, Enum):
    backend_api = "backend-api"
    frontend_web = "frontend-web"

class AllowedEvent(str, Enum):  # Whitelist cerrada
    book_viewed = "book.viewed"
    book_listed = "book.listed"
    book_reserved = "book.reserved"
    book_reservation_failed = "book.reservation_failed"
    book_released = "book.released"
    user_registered = "user.registered"
    user_logged_in = "user.logged_in"
    user_login_failed = "user.login_failed"

class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt_{uuid4()}")
    event: AllowedEvent
    schema_version: str = "1.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None
    anonymous_id: Optional[str] = None
    session_id: str
    context: dict[str, Any] = Field(default_factory=dict, max_length=2048)
    properties: dict[str, Any] = Field(default_factory=dict, max_length=2048)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

### 4.3 Repositorio (`app/repositories/telemetry_repository.py`)

- Append-only sobre tabla `telemetry_events` de TinyDB.
- Métodos:
  - `insert(event: EventEnvelope) -> None`
  - `find_by_event(event: str, from_date: datetime | None, to_date: datetime | None) -> list[EventEnvelope]`

### 4.4 Servicio — `track()` en backend (`app/services/telemetry_service.py`)

La función `track()` en backend es el único punto de entrada para registrar eventos de telemetría:

```python
# app/services/telemetry_service.py
class TelemetryService:
    def __init__(self, repository, enabled: bool = True):
        self._repository = repository
        self._enabled = enabled

    def track(self, event: EventEnvelope) -> None:
        """ÚNICA función para emitir telemetría en backend.
        
        Si TELEMETRY_ENABLED=false, es no-op (evita overhead en tests/CI).
        """
        if not self._enabled:
            return
        self._repository.insert(event)
```

**¿Quién llama a `track()`?**

| Evento | Lo emite | Quién llama a `track()` |
|--------|----------|-------------------------|
| `book.reserved` | backend | `BooksService.reserve_book` tras éxito → `telemetry_service.track(EventEnvelope)` |
| `book.reservation_failed` | backend | `BooksService.reserve_book` cuando `BookUnavailableError` → `telemetry_service.track(EventEnvelope)` |
| `book.released` | backend | `BooksService.release_book` tras éxito → `telemetry_service.track(EventEnvelope)` |
| `user.registered` | backend | `UsersService.register_user` tras éxito → `telemetry_service.track(EventEnvelope)` |
| `user.logged_in` | backend | `AuthService.login` tras éxito → `telemetry_service.track(EventEnvelope)` |
| `user.login_failed` | backend | `AuthService.login` cuando `InvalidCredentialsError` → `telemetry_service.track(EventEnvelope)` |

**Patrón**: Usar `BackgroundTasks` de FastAPI en los controllers para no bloquear la respuesta HTTP con la escritura del evento.  
Ejemplo:

```python
# app/controllers/books_controller.py
from fastapi import BackgroundTasks

@router.post("/{book_id}/reserve", response_model=BookResponse)
async def reserve_book(
    book_id: int,
    current_user: Annotated[UserModel, Depends(get_current_user)],
    background_tasks: BackgroundTasks,
) -> BookResponse:
    try:
        reserved_book = service.reserve_book(book_id, current_user.id)
        await FastAPICache.clear(namespace="books")
        # track() via BackgroundTasks — no bloquea la respuesta
        background_tasks.add_task(
            telemetry_service.track,
            EventEnvelope(
                event="book.reserved",
                user_id=current_user.id,
                session_id=f"srv_{current_user.id}",
                context={"book_id": book_id, "role": current_user.role.value},
                metadata={"source": "backend-api", "environment": TELEMETRY_ENV, "app_version": APP_VERSION},
            )
        )
        return reserved_book
    except BookNotFoundError as error:
        raise book_not_found_exception() from error
    except BookUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Book is not available") from error
```

### 4.5 Endpoint de ingesta (Fase 2)

```
POST /telemetry/events
Content-Type: application/json

[EventEnvelope, EventEnvelope, ...]
```

**Validaciones**:
- `schema_version` soportado (1.0).
- **Límite de payload**: 1 MB (anti-DoS). Ver `max_event_size` en config.
- **Whitelist**: `event` validado contra `AllowedEvent` enum.
- **Sobrescritura de `user_id`**: Si hay JWT válido → se usa `sub` del token. Si no → se respeta `anonymous_id`.
- Sin autenticación obligatoria (permite eventos anónimos), pero con **rate-limiting** básico por IP/session_id.

### 4.6 Endpoint de consulta admin (Fase 4)

```
GET /telemetry/events?event=book.reserved&from=2026-01-01&to=2026-08-31
Authorization: Bearer <admin_token>
```

- Protegido con `require_roles({"admin"})`.
- Para depuración y métricas básicas.

---

## 5. Frontend — `track()` como API única

La función `track()` en frontend es la **única interfaz pública** para emitir telemetría desde cualquier componente.

### 5.1 Helper de telemetría (`frontend/lib/telemetry.ts`)

Refactorizar el contenido actual de `telemetry.ts` (`/workspaces/dsmora-python-hello/frontend/telemetry.ts`) para que `lib/telemetry.ts` exponga **solo** la función `track()` como API pública:

```typescript
// frontend/lib/telemetry.ts — API pública: SOLO track()

// --- Estado interno (no exportado) ---
let eventQueue: EventEnvelope[] = [];
let sessionId: string | null = null;
let anonymousId: string | null = null;
let flushTimer: ReturnType<typeof setInterval> | null = null;

// --- Configuración ---
const MAX_EVENTS = 10;
const FLUSH_INTERVAL_MS = 60000; // 60s TTL
const MAX_RETRY = 3;
const TELEMETRY_ENDPOINT = '/api/telemetry';

// --- IDs persistentes ---
function getSessionId(): string { /* sessionStorage */ }
function getAnonymousId(): string { /* localStorage, prefijo anon_ */ }

// --- track(): LA ÚNICA FUNCIÓN PÚBLICA ---
export function track(
  event: string,
  context?: Record<string, unknown>,
  properties?: Record<string, unknown>,
): void {
  // 1. Verificar consentimiento
  if (!hasConsent()) return;
  
  // 2. Sanitizar — eliminar datos sensibles
  const safeContext = sanitize(context ?? {});
  const safeProperties = sanitize(properties ?? {});
  
  // 3. Whitelist — solo eventos permitidos
  if (!isAllowedEvent(event)) return;
  
  // 4. Sampling — si aplica
  if (!shouldSample()) return;

  const envelope: EventEnvelope = {
    event_id: `evt_${crypto.randomUUID()}`,
    event,
    schema_version: '1.0',
    timestamp: new Date().toISOString(),
    user_id: getUserIdFromToken(),  // null si no hay sesión
    anonymous_id: getAnonymousId(),
    session_id: getSessionId(),
    context: safeContext,
    properties: safeProperties,
    metadata: {
      source: 'frontend-web',
      environment: getEnvironment(),
      app_version: '1.0.0',
    },
  };

  eventQueue.push(envelope);
  
  // 5. Enviar si se alcanzó el tamaño máximo del batch
  if (eventQueue.length >= MAX_EVENTS) {
    flush();
  }
}

// --- flush() — envía el batch y limpia la cola ---
function flush(): void { /* sendBeacon → fetch fallback → limpiar */ }

// --- init() — llamada desde _app.tsx ---
export function initTelemetry(): void {
  /* Inicia el timer de flush automático */
}

// --- Funciones internas ---
function hasConsent(): boolean { /* localStorage.getItem('telemetry_consent') */ }
function sanitize(obj: Record<string, unknown>): Record<string, unknown> { /* eliminar passwords, tokens */ }
function isAllowedEvent(event: string): boolean { /* whitelist */ }
function shouldSample(): boolean { /* 1 de cada N en prod */ }
function getUserIdFromToken(): string | null { /* decode JWT de localStorage */ }
function getEnvironment(): string { /* process.env.NODE_ENV */ }
```

### 5.2 Inicialización (`frontend/pages/_app.tsx`)

```typescript
import { useEffect } from 'react';
import { initTelemetry } from '@/lib/telemetry';
import "@/styles/globals.css";
import type { AppProps } from "next/app";

export default function App({ Component, pageProps }: AppProps) {
  useEffect(() => {
    initTelemetry();  // Inicia el flush automático (cada 60s)
  }, []);
  
  return <Component {...pageProps} />;
}
```

### 5.3 Instrumentación de componentes — SOLO llaman a `track()`

Cada componente importa `track` desde `@/lib/telemetry` y la invoca en el momento adecuado:

| Componente | Evento | Código |
|------------|--------|--------|
| `pages/books/[id].tsx` | `book.viewed` | `useEffect(() => { track('book.viewed', { book_id }); }, [bookId]);` |
| `pages/index.tsx` | `book.listed` | En `setFilters`: `track('book.listed', { genre: filters.genre, status: filters.status });` |
| `components/BookCard.tsx` | `book.reserved` | En `handleReserve` tras éxito: `track('book.reserved', { book_id: book.id, book_title: book.title });` |
| `pages/reservations.tsx` | `book.released` | En `handleRelease` tras éxito: `track('book.released', { book_id: reservation.book_id });` |
| `pages/login.tsx` | `user.logged_in` / `user.login_failed` | En `handleSubmit`: tras éxito → `track('user.logged_in', { email })`; en catch → `track('user.login_failed', { email })` |
| `pages/register.tsx` | `user.registered` | En `handleSubmit` tras éxito: `track('user.registered', { email: formData.email });` |

---

## 6. Flujo de datos completo

```
Frontend (React/Next.js)
  │
  │  Interacción del usuario
  │  → track(event, context, properties)   ← ÚNICA función
  │  → Se construye EventEnvelope internamente
  │  → Se acumula en cola local (batch)
  │
  ├── flush() cada 60s o al llegar a 10 eventos
  │   └── sendBeacon / fetch keepalive ──→ POST /api/telemetry
  │
Backend (FastAPI)
  │
  │  Controllers (books, auth, users)
  │  → telemetry_service.track(EventEnvelope)   ← ÚNICA función
  │  → Se escribe en TinyDB (tabla telemetry_events)
  │
  └── POST /telemetry/events (ingesta externa desde frontend)
       → Validación (whitelist, schema_version, tamaño)
       → Sobrescritura de user_id desde JWT
       → telemetry_service.track(EventEnvelope)   ← misma función
```

---

## 7. Seguridad (OWASP Checklist)

- [ ] **Nunca loguear** `password`, `hashed_password` o tokens en `properties`.
- [ ] **Límite de tamaño** en `context`/`properties` (max 2048 bytes cada uno) → anti-DoS.
- [ ] `user_id` en eventos **backend** siempre desde JWT verificado, nunca del input cliente.
- [ ] `event` validado contra **whitelist cerrada** (`AllowedEvent` enum) en backend.
- [ ] **Rate-limiting** en `POST /telemetry/events` (por IP / session_id).
- [ ] **Payload máximo** en endpoint de ingesta (ej. 1 MB por request).

---

## 8. Fases de implementación (resumen ejecutivo)

| Fase | Qué | Archivos afectados | `track()` |
|------|-----|--------------------|-----------|
| **0** | Config + DB | `app/config.py`, `app/db.py` | — |
| **1** | Backend: modelo + repo + servicio `track()` | `app/models/telemetry.py`, `repositories/telemetry_repository.py`, `services/telemetry_service.py` | `telemetry_service.track()` |
| **2** | Emisión desde controllers via BackgroundTasks | `controllers/books_controller.py`, `controllers/users_controller.py`, `controllers/auth_controller.py` | Se invoca `telemetry_service.track()` |
| **3** | Endpoint ingesta `POST /telemetry/events` + validaciones | `controllers/telemetry_controller.py` (nuevo), `dependencies/telemetry.py` | Se invoca `telemetry_service.track()` internamente |
| **4** | Frontend: `track()` + helper + instrumentación | `frontend/lib/telemetry.ts` (nuevo), `frontend/types/telemetry.ts` (nuevo), `_app.tsx`, `BookCard.tsx`, `reservations.tsx`, `books/[id].tsx`, `index.tsx`, `login.tsx`, `register.tsx` | Componentes llaman a `track()` de lib/telemetry |
| **5** | Endpoint admin consulta `GET /telemetry/events` | `controllers/telemetry_controller.py` | — |
| **6** | Escalar a Supabase (futuro) | Migrar sink de TinyDB a Supabase | Sin cambios en API |

---

## 9. Próximos pasos inmediatos

1. ✅ Crear `app/models/telemetry.py` con modelo Pydantic + enum `AllowedEvent`.
2. ✅ Crear `app/repositories/telemetry_repository.py`.
3. ✅ Crear `app/services/telemetry_service.py` con su método `track()`.
4. ✅ Agregar `TELEMETRY_ENABLED` a config y `telemetry_events` a db.py.
5. ✅ Emitir eventos desde controllers: `books_controller.py`, `auth_controller.py`, `users_controller.py` → `telemetry_service.track()` via `BackgroundTasks`.
6. ✅ Crear endpoint `POST /telemetry/events` que valida y llama a `telemetry_service.track()`.
7. ✅ Crear `frontend/types/telemetry.ts` con interfaz `EventEnvelope`.
8. ✅ Refactorizar `frontend/telemetry.ts` → `frontend/lib/telemetry.ts` exponiendo solo `track()`, `initTelemetry()`.
9. ✅ Inicializar `initTelemetry()` en `_app.tsx`.
10. ✅ Instrumentar componentes frontend llamando a `track()` desde:
    - `pages/books/[id].tsx` → `book.viewed`
    - `pages/index.tsx` → `book.listed`
    - `components/BookCard.tsx` → `book.reserved`
    - `pages/reservations.tsx` → `book.released`
    - `pages/login.tsx` → `user.logged_in`, `user.login_failed`
    - `pages/register.tsx` → `user.registered`
11. ✅ Crear endpoint admin `GET /telemetry/events` protegido.