# Event Envelope — Schema de Telemetría

Formato base acordado, extendido a partir del ejemplo de referencia (`lesson_completed`), aplicado al dominio de libros/reservas de este proyecto.

## Envelope

```jsonc
{
  "event_id": "evt_9f5a45c3-f0cb-4536-b66b-0a0d48d01113",  // uuid, para dedupe/idempotencia
  "event": "book.reserved",                                  // namespace.accion (dot-case)
  "schema_version": "1.0",
  "timestamp": "2026-08-31T16:31:07.676Z",                   // ISO 8601 UTC
  "user_id": "a7a6cef6-dd79-4f02-91b0-719529d74fea",         // null si tiene sesion iniciada; anonymous_id identifica al visitante
  "anonymous_id": "anon_9f5a45c3-f0cb-4536-b66b-0a0d48d01113", // persistido en localStorage, identifica al usuario anonimo
  "session_id": "s_xyz789",                                  // generado en frontend, persiste en sessionStorage
  "context": {                                                // referencias a entidades del dominio
    "book_id": 4,
    "genre": "fiction",
    "reservation_id": "7dea56ab-c85d-4a0a-a10e-b0060a380d26",
    "role": "user",
    "request_id": "req_abc123"                               // correlaciona con logs backend
  },
  "properties": {                                             // metricas/atributos propios del evento
    "previous_status": "available",
    "new_status": "checked_out"
  },
  "metadata": {                                               // info tecnica, no de negocio
    "source": "backend-api",                                  // backend-api | frontend-web
    "environment": "production",
    "app_version": "1.4.2"
  }
}
```

### Campos

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `event_id` | string | sí | prefijo `evt_` + uuid4, evita procesar duplicados |
| `event` | string | sí | debe pertenecer a la whitelist cerrada de eventos (ver taxonomía) |
| `schema_version` | string | sí | permite evolucionar el schema sin romper consumidores |
| `timestamp` | string (ISO 8601, UTC) | sí | generado en el momento del evento, no en la ingesta |
| `user_id` | string \| null | no | en backend se sobrescribe siempre con el `sub` del JWT verificado |
| `anonymous_id` | string \| null | no | persistido en localStorage, identifica al visitante anónimo; se reemplaza por `user_id` cuando inicia sesión |
| `session_id` | string | sí | identifica la sesión de navegación, no la sesión de auth |
| `context` | object | sí | referencias a entidades (ids), tamaño máximo limitado |
| `properties` | object | sí | atributos/métricas propias del evento, nunca datos sensibles |
| `metadata` | object | sí | `source`, `environment`, `app_version` |

## Taxonomía de eventos

| Evento | Origen | Se dispara en |
|---|---|---|
| `book.viewed` | frontend | `pages/books/[id].tsx` al montar |
| `book.listed` | frontend | `pages/index.tsx` al aplicar filtros |
| `book.reserved` | backend | `BooksService.reserve_book` (éxito) |
| `book.reservation_failed` | backend | `BookUnavailableError` en `reserve_book` |
| `book.released` | backend | `BooksService.release_book` (éxito) |
| `user.registered` | backend | `UsersService.register_user` |
| `user.logged_in` | backend | login exitoso |
| `user.login_failed` | backend | credenciales inválidas |

## Modelo Pydantic (backend)

```python
# app/models/telemetry.py
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4
from pydantic import BaseModel, Field

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
```

## Tipo TypeScript (frontend)

```typescript
// frontend/types/telemetry.ts
export interface EventEnvelope {
  event_id: string;
  event: string;
  schema_version: string;
  timestamp: string;
  user_id: string | null;
  anonymous_id: string | null;
  session_id: string;
  context: Record<string, unknown>;
  properties: Record<string, unknown>;
  metadata: { source: 'frontend-web'; environment?: string; app_version?: string };
}
}
```

## Consideraciones de seguridad (OWASP)

- Nunca loguear `password`, `hashed_password` o tokens en `properties`.
- Validar y limitar el tamaño de `context`/`properties` (evitar payloads gigantes → DoS).
- `user_id` en eventos generados por el backend siempre proviene del JWT verificado, nunca del input del cliente.
- `event` debe validarse contra un enum/whitelist cerrado en el backend, no strings libres enviados por el frontend.
