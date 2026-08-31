# Plan de Implementación — Telemetría (Event Envelope)

Ver el schema completo en [TELEMETRY-SCHEMA.md](./TELEMETRY-SCHEMA.md).

## Fase 0 — Config

- Leer `TELEMETRY_ENABLED` en [app/config.py](app/config.py) (ya existe en `.env` pero no se usa).
- Añadir tabla `telemetry_events` a `DEFAULT_TABLES` en [app/db.py](app/db.py).

## Fase 1 — Backend: captura + almacenamiento

- Crear `app/models/telemetry.py` con el modelo `EventEnvelope` (Pydantic).
- Crear `TelemetryRepository` (TinyDB, append-only, tabla `telemetry_events`).
- Crear `TelemetryService.track(event: EventEnvelope)`. Si `TELEMETRY_ENABLED=false`, es no-op (evita overhead en tests/CI).
- Emitir eventos desde:
  - `BooksService.reserve_book` → `book.reserved` / `book.reservation_failed`
  - `BooksService.release_book` → `book.released`
  - `UsersService.register_user` → `user.registered`
  - login exitoso/fallido en `auth_service`/`auth_controller` → `user.logged_in` / `user.login_failed`
- Usar `BackgroundTasks` de FastAPI en los controllers para no bloquear la respuesta HTTP con la escritura del evento.

## Fase 2 — Endpoint de ingesta para frontend

- `POST /telemetry/events` que acepta una lista de envelopes (batch).
- Validaciones:
  - `schema_version` soportado.
  - Tamaño máximo del payload (anti-abuso/DoS).
  - `event` contra whitelist cerrada (enum de eventos permitidos).
  - Si hay JWT válido en el header, sobrescribe `user_id` con el `sub` del token (nunca confiar en el valor enviado por el cliente); si no hay JWT, se usa `anonymous_id`.
- Sin autenticación obligatoria (permite eventos anónimos como `book.viewed`), pero con rate-limiting básico por IP/`session_id`.

## Fase 3 — Frontend: helper + instrumentación

- Crear `frontend/lib/telemetry.ts`:
  - Genera y persiste `session_id` en `sessionStorage` (una vez por sesión de navegador).
  - Genera y persiste `anonymous_id` en `localStorage` (una vez por navegador/dispositivo, prefijo `anon_` + uuid4).
  - Arma el `EventEnvelope` (timestamp, user_id desde el token si existe, anonymous_id si no hay sesión, metadata).
  - Envía con `navigator.sendBeacon` (fire-and-forget, no bloquea la navegación); fallback a `fetch` con `keepalive: true` si `sendBeacon` no está disponible.
- Instrumentar:
  - Click en "Reservar" → [frontend/components/BookCard.tsx](frontend/components/BookCard.tsx)
  - Click en "Liberar libro" → [frontend/pages/reservations.tsx](frontend/pages/reservations.tsx)
  - Vista de detalle de libro → [frontend/pages/books/[id].tsx](frontend/pages/books/[id].tsx)

## Fase 4 — Consulta/observabilidad

- Endpoint admin `GET /telemetry/events?event=book.reserved&from=...` protegido con `require_roles({"admin"})`, para depuración y métricas básicas.

## Fase 5 — Escalar (futuro, opcional)

- Migrar el sink de TinyDB a la tabla Supabase ya configurada (`SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` en `.env`) para persistencia real y consultas SQL/agregaciones.

## Checklist de seguridad (OWASP)

- [ ] Nunca loguear `password`, `hashed_password` o tokens en `properties`.
- [ ] Límite de tamaño en `context`/`properties` para evitar payloads gigantes (DoS).
- [ ] `user_id` en eventos backend siempre desde el JWT verificado, nunca del input del cliente.
- [ ] `event` validado contra whitelist cerrada en el backend.
- [ ] Rate-limiting en `POST /telemetry/events`.
