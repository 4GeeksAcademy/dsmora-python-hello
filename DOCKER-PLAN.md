# Plan de Dockerización — Library API + Frontend

> **Propósito:** Contenerizar la aplicación completa (backend FastAPI + frontend Next.js) usando Docker y Docker Compose para facilitar su ejecución, desarrollo y despliegue en cualquier entorno.

---

## 1. Diagnóstico completo del proyecto

### 1.1. Arquitectura general

```
┌─────────────────────────────────────────────────────┐
│                   dsmora-python-hello                │
│                                                      │
│   ┌──────────────────────┐  ┌──────────────────────┐ │
│   │      BACKEND         │  │      FRONTEND         │ │
│   │   (FastAPI + TinyDB) │  │   (Next.js + React)   │ │
│   │                      │  │                       │ │
│   │   Puerto: 8000       │  │   Puerto: 3000        │ │
│   │   Python 3.12        │  │   Node.js 22          │ │
│   │   Gestor: uv         │  │   Gestor: npm         │ │
│   └──────────┬───────────┘  └───────────┬───────────┘ │
│              │                          │              │
│              └──────────┬───────────────┘              │
│                         │ HTTP (API REST)              │
│                         ▼                              │
│              ┌──────────────────┐                      │
│              │   data/db.json   │                      │
│              │   (TinyDB)       │                      │
│              └──────────────────┘                      │
└─────────────────────────────────────────────────────┘
```

### 1.2. Tabla comparativa Backend vs Frontend

| Aspecto | Backend (FastAPI) | Frontend (Next.js) |
|---|---|---|
| **Lenguaje** | Python 3.12+ | TypeScript / JavaScript |
| **Framework** | FastAPI + Uvicorn | Next.js 16 + React 19 |
| **Base image recomendada** | `python:3.12-slim` | `node:22-alpine` |
| **Gestor de paquetes** | `uv` (rust, ultrarrápido) | `npm` |
| **Archivo de dependencias** | `pyproject.toml` + `uv.lock` | `package.json` + `package-lock.json` |
| **Archivo de bloqueo** | `uv.lock` | `package-lock.json` |
| **Puerto** | `8000` | `3000` |
| **Persistencia** | TinyDB en `data/db.json` (archivo) | Ninguna (solo consume API) |
| **Variables de entorno** | `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES` | `NEXT_PUBLIC_API_URL` |
| **Tipo de contenedor** | Servicio que corre toda la vida | Build de producción + servidor estático |

### 1.3. Árbol de dependencias del proyecto

```
dsmora-python-hello/
│
├── 🐍 BACKEND (Python)
│   ├── main.py                  ← Punto de entrada: uvicorn.run("main:app")
│   ├── seed.py                  ← Poblado inicial de datos
│   ├── pyproject.toml           ← Dependencias Python
│   ├── uv.lock                  ← Lockfile de uv
│   ├── app/
│   │   ├── __init__.py          ← create_app() → FastAPI app
│   │   ├── config.py            ← SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
│   │   ├── db.py                ← TinyDB initialization
│   │   ├── security.py          ← Hashing, JWT
│   │   ├── controllers/         ← Rutas (auth, books, profiles, users)
│   │   ├── services/            ← Lógica de negocio
│   │   ├── repositories/        ← Acceso a datos
│   │   ├── models/              ← Pydantic models
│   │   ├── views/               ← Respuestas HTTP
│   │   └── dependencies/        ← Inyección de dependencias
│   └── data/
│       └── db.json              ← Base de datos TinyDB (persistente)
│
└── ⚛️ FRONTEND (Next.js)
    ├── package.json             ← Dependencias npm
    ├── package-lock.json        ← Lockfile de npm
    ├── next.config.ts           ← Configuración de Next.js
    ├── tsconfig.json            ← TypeScript config
    ├── pages/                   ← Rutas (index, login, register, profile, books/[id], etc.)
    ├── components/              ← Componentes React (BookCard, Layout, etc.)
    ├── hooks/                   ← Custom hooks (useBook, useBooks, useAuthGuard)
    ├── lib/                     ← Utilidades (api.ts, auth.ts)
    ├── types/                   ← TypeScript types
    ├── public/                  ← Archivos estáticos
    └── styles/
        └── globals.css          ← Tailwind CSS
```

---

## 2. Conceptos fundamentales de Docker (para explicar en clase)

Antes de escribir código, entender estos conceptos es clave:

### 2.1. Imagen vs Contenedor

```
┌─────────────────────────────────────────────────────────┐
│                    IMAGEN (blueprint)                    │
│                                                         │
│   Es un template de solo lectura.                       │
│   Contiene: SO base + dependencias + código fuente.     │
│   Se construye con `docker build`.                      │
│   Se reutiliza para crear múltiples contenedores.       │
│                                                         │
│   Ejemplo: python:3.12-slim (imagen base oficial)       │
└──────────────────────┬──────────────────────────────────┘
                       │ docker run / docker compose up
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   CONTENEDOR (instancia)                 │
│                                                         │
│   Es una instancia en ejecución de una imagen.          │
│   Tiene su propio sistema de archivos, red, procesos.   │
│   Es efímero: al borrarlo se pierde todo (¡excepto      │
│   lo que esté en volúmenes!).                           │
│                                                         │
│   Ejemplo: "library-api" (corriendo FastAPI)            │
└─────────────────────────────────────────────────────────┘
```

### 2.2. Capas (Layers) en una imagen Docker

```
┌──────────────────────────────┐
│  Capa 6: CMD                 │ ← Comando de arranque
├──────────────────────────────┤
│  Capa 5: EXPOSE              │ ← Puerto
├──────────────────────────────┤
│  Capa 4: COPY . .            │ ← Código fuente
├──────────────────────────────┤
│  Capa 3: RUN pip install     │ ← Dependencias
├──────────────────────────────┤
│  Capa 2: COPY requirements   │ ← Archivo de deps
├──────────────────────────────┤
│  Capa 1: FROM python:3.12    │ ← Base image
└──────────────────────────────┘
   Cada capa se cachea. Si cambia una, se reconstruyen
   las siguientes. Por eso ordenamos de lo menos cambiante
   (FROM) a lo más cambiante (código fuente).
```

### 2.3. Multi-stage build

```
┌─── STAGE 1: builder ──────────────────────────────┐
│  FROM python:3.12-slim AS builder                  │
│  COPY pyproject.toml uv.lock ./                     │
│  RUN uv sync --no-dev --frozen                      │
│  Resultado: .venv/ con todas las dependencias       │
└────────────────────┬───────────────────────────────┘
                     │ COPY --from=builder
                     ▼
┌─── STAGE 2: final ────────────────────────────────┐
│  FROM python:3.12-slim                              │
│  COPY --from=builder /app/.venv /app/.venv          │
│  COPY . .                                           │
│  Resultado: imagen más pequeña (sin herramientas     │
│  de build, solo lo necesario para correr)           │
└────────────────────────────────────────────────────┘
```

**Ventajas del multi-stage:**
- Imagen final más pequeña (menos MB)
- No incluye compiladores, gestores de paquetes ni código fuente de dependencias
- Mejor seguridad (menos superficie de ataque)
- Tiempos de descarga más rápidos

---

## 3. Estructura final de archivos Docker

```
dsmora-python-hello/
│
├── Dockerfile.backend          ← (NUEVO) Construye la imagen del backend
├── Dockerfile.frontend         ← (NUEVO) Construye la imagen del frontend
├── docker-compose.yml          ← (NUEVO) Orquestador de servicios
├── .dockerignore               ← (NUEVO) Archivos que NO van al contexto de build
├── .env                        ← (CREAR) Variables de entorno (NO versionar)
│
└── frontend/
    ├── .dockerignore           ← (NUEVO) Archivos que NO van al build del frontend
    └── ...
```

---

## 4. Archivo por archivo: explicación línea a línea

### 4.1. `.dockerignore` — Raíz del proyecto (backend)

Este archivo le dice a Docker: *"al construir la imagen, ignora estos archivos y no los copies al contexto de build"*.

```dockerignore
# Entorno virtual de Python (ocupa cientos de MB)
.venv/

# Caché de Python (archivos .pyc compilados)
__pycache__/
*.pyc

# Variables de entorno sensibles (NO deben estar en la imagen)
.env

# Carpeta de dependencias del frontend (está en frontend/node_modules)
node_modules/

# Build de Next.js (está en frontend/.next)
.next/

# Base de datos local (debe persistir fuera del contenedor, no dentro)
data/db.json

# Git (innecesario en producción)
.git/
.gitignore

# Logs
*.log

# IDE
.vscode/
.idea/
```

> **🔑 Dato clave:** El contexto de build es todo lo que se envía al daemon de Docker. Si no usas `.dockerignore`, terminas enviando `.venv/` (cientos de MB) innecesariamente, ralentizando el build.

---

### 4.2. `frontend/.dockerignore` — Para el build del frontend

```dockerignore
node_modules/
.next/
.git/
*.log
.env
.env.local
```

---

### 4.3. `Dockerfile.backend` — Explicación línea a línea

#### Etapa 1: Builder (instalación de dependencias)

```dockerfile
# ---- STAGE 1: BUILDER ----
# 1. Imagen base oficial de Python 3.12 en versión slim (Debian recortado)
#    slim = ~50MB menos que la versión completa, tiene lo justo para correr Python
FROM python:3.12-slim AS builder

# 2. Directorio de trabajo dentro del contenedor
#    Todos los comandos siguientes se ejecutan en /app
WORKDIR /app

# 3. Copiar el binario 'uv' desde la imagen oficial de Astral (ghcr.io)
#    COPY --from= otra-imagen :ruta  →  extrae archivos de otra imagen
#    /uv y /uvx son los binarios compilados de uv (gestor de paquetes Python, escrito en Rust)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 4. Copiar SOLO los archivos de dependencias
#    ORDEN CRUCIAL: esto cambia poco, así que Docker cachea esta capa
#    Mientras no modifiques pyproject.toml o uv.lock, esta capa NO se reconstruye
COPY pyproject.toml uv.lock ./

# 5. Sincronizar dependencias sin las de desarrollo y congeladas (usa el lockfile exacto)
#    Crea un .venv/ dentro de /app con todas las dependencias instaladas
#    --no-dev: omite dependencias de desarrollo (más pequeño)
#    --frozen: usa uv.lock exactamente, no resuelve de nuevo (más rápido y reproducible)
RUN uv sync --no-dev --frozen
```

#### Etapa 2: Imagen final

```dockerfile
# ---- STAGE 2: IMAGEN FINAL ----
# 6. Nueva imagen base limpia (más pequeña)
FROM python:3.12-slim

# 7. Variables de entorno para Python en producción
#    PYTHONDONTWRITEBYTECODE: no genera archivos .pyc
#    PYTHONUNBUFFERED: output sin buffer (logs en tiempo real)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 8. Directorio de trabajo
WORKDIR /app

# 9. Crear usuario no-root para seguridad
#    Nunca correr la app como root dentro del contenedor
#    uid=1001, gid=1001 (usuario 'appuser')
RUN addgroup --system --gid 1001 appuser \
    && adduser --system --uid 1001 --gid 1001 appuser

# 10. Copiar el .venv desde la etapa builder
#     Solo traemos las dependencias, no las herramientas de build
COPY --chown=appuser:appuser --from=builder /app/.venv /app/.venv

# 11. Copiar el código fuente
#     COPY . .  →  copia todo lo que NO esté en .dockerignore
#     --chown: asigna los archivos al usuario no-root
COPY --chown=appuser:appuser . .

# 12. Puerto que expone la aplicación (solo es documentación)
#     No hace que el puerto sea accesible automáticamente,
#     hay que mapearlo con -p o ports: en compose
EXPOSE 8000

# 13. Cambiar al usuario no-root (deja de usar root)
USER appuser

# 14. Comando por defecto al arrancar el contenedor
#     Formato exec (JSON array) — RECOMENDADO sobre el formato shell
#     Señales: con formato exec, SIGTERM llega directo al proceso
#     /app/.venv/bin/uvicorn: usa el uvicorn instalado en el .venv
#     main:app → archivo main.py, variable app
#     --host 0.0.0.0 → acepta conexiones desde cualquier IP
#     --port 8000 → puerto donde escucha
#     NOTA: No usamos --reload en producción (solo para desarrollo)
CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Versión completa del `Dockerfile.backend`

```dockerfile
# ---- STAGE 1: BUILDER ----
FROM python:3.12-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# ---- STAGE 2: IMAGEN FINAL ----
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system --gid 1001 appuser \
    && adduser --system --uid 1001 --gid 1001 appuser

COPY --chown=appuser:appuser --from=builder /app/.venv /app/.venv
COPY --chown=appuser:appuser . .

EXPOSE 8000

USER appuser

CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### 4.4. `Dockerfile.frontend` — Explicación línea a línea

#### Etapa 1: Builder (compilación de Next.js)

```dockerfile
# ---- STAGE 1: BUILDER ----
# 1. Imagen base de Node.js 22 basada en Alpine Linux (~5MB de SO)
#    Alpine es mínima, pero ojo: usa musl libc en vez de glibc
FROM node:22-alpine AS builder

# 2. Directorio de trabajo
WORKDIR /app

# 3. Copiar SOLO los archivos de metadatos de npm
#    Esto aprovecha el cache de Docker: si package.json no cambia,
#    la capa RUN npm ci se reusa de la cache
COPY package.json package-lock.json ./

# 4. npm ci (clean install):
#    - Instala EXACTAMENTE lo que dice package-lock.json (reproducible)
#    - Borra node_modules/ si existe y reinstala desde cero
#    - Es más rápido y estricto que npm install
#    - FALLA si package-lock.json no coincide con package.json
RUN npm ci

# 5. Copiar TODO el código fuente del frontend
#    Esto cambia frecuentemente → última capa antes del build
COPY . .

# 6. Construir la aplicación Next.js para producción
#    Genera la carpeta .next/ con:
#    - HTML, CSS, JS estáticos optimizados
#    - Server Components (Next.js 16)
#    - Imágenes optimizadas, chunks de código
RUN npm run build
```

#### Etapa 2: Imagen final (solo lo necesario para servir)

```dockerfile
# ---- STAGE 2: IMAGEN FINAL ----
# 7. Nueva imagen base limpia de Alpine
FROM node:22-alpine

# 8. Directorio de trabajo
WORKDIR /app

# 9. Copiar los artefactos de producción desde el builder
#    Solo lo mínimo indispensable para servir la app
#
#    .next/         → Build completo de Next.js (páginas, chunks, etc.)
#    public/        → Archivos estáticos (favicon, imágenes, etc.)
#    package.json   → Necesario para npm run start
#    node_modules/  → Dependencias ya instaladas (evita reinstalar)
#    next.config.ts → Configuración de Next.js
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/next.config.ts ./

# 10. Documentar el puerto
EXPOSE 3000

# 11. Usuario no-root para seguridad
#     node:22-alpine ya tiene un usuario 'node' creado
USER node

# 12. Comando de inicio en producción
#     npm run start → ejecuta "next start"
#     Next.js sirve las páginas ya compiladas en .next/
#     No es necesario --reload, esto ya es producción
CMD ["npm", "run", "start"]
```

#### Versión completa del `Dockerfile.frontend`

```dockerfile
# ---- STAGE 1: BUILDER ----
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- STAGE 2: IMAGEN FINAL ----
FROM node:22-alpine

WORKDIR /app

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/next.config.ts ./

EXPOSE 3000

USER node

CMD ["npm", "run", "start"]
```

---

### 4.5. `docker-compose.yml` — Explicación línea a línea

```yaml
# versions: docker compose (v2) ya NO requiere la clave 'version'
# El formato es el del schema más reciente automáticamente

services:
  # ──── SERVICIO BACKEND ────
  backend:
    # Construcción de la imagen
    build:
      context: .                        # Contexto de build = raíz del proyecto
      dockerfile: Dockerfile.backend     # Dockerfile específico para backend
    # Nombre del contenedor (útil para docker exec, logs, etc.)
    container_name: library-api
    # Mapeo de puertos: HOST:CONTENEDOR
    # Accedes al backend en http://localhost:8000
    ports:
      - "8000:8000"
    # Cargar variables de entorno desde un archivo .env
    # NO incluir .env en la imagen, solo se pasa en tiempo de ejecución
    env_file:
      - .env
    # Volúmenes: montar carpetas del HOST dentro del CONTENEDOR
    # ./data (host) → /app/data (contenedor)
    # PERMITE: persistir TinyDB aunque el contenedor se elimine
    # SIN VOLUMEN: cada vez que haces docker compose down se pierden los datos
    volumes:
      - ./data:/app/data
    # Red interna para comunicación entre servicios
    networks:
      - app-network
    # Política de reinicio: siempre reiniciar a menos que se detenga manualmente
    restart: unless-stopped
    # Health check: Docker verifica que el servicio responda
    # curl hace GET a /books, espera código 200
    # interval: cada 30s | timeout: 10s para responder | retries: 3 fallos seguidos
    # start_period: espera 40s antes del primer check (tiempo de arranque)
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/books"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # ──── SERVICIO FRONTEND ────
  frontend:
    build:
      context: ./frontend               # Contexto de build = carpeta frontend/
      dockerfile: ../Dockerfile.frontend # Dockerfile está en la raíz del proyecto
    container_name: library-frontend
    ports:
      - "3000:3000"
    # Variables de entorno inline (otra forma de pasarlas)
    # NEXT_PUBLIC_API_URL: le dice al frontend dónde está el backend
    # http://backend:8000 usa el nombre del servicio, NO localhost
    # Docker DNS interno resuelve 'backend' a la IP del contenedor backend
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    # depends_on: orden de arranque (frontend espera a que backend empiece)
    # NOTA: espera a que el contenedor exista, NO a que la app esté lista
    # Para esperar a que responda, se necesita healthcheck + wait-for-it
    depends_on:
      backend:
        condition: service_healthy   # Espera a que el healthcheck del backend pase
    networks:
      - app-network
    restart: unless-stopped

# ──── REDES ────
networks:
  app-network:
    driver: bridge                     # Red interna tipo puente
    # bridge: red aislada del host, los contenedores se ven entre sí
    # por nombre de servicio (DNS interno)
    # No expuestos al exterior a menos que se mapeen puertos
```

#### Versión completa del `docker-compose.yml`

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: library-api
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    networks:
      - app-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/books"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: ./frontend
      dockerfile: ../Dockerfile.frontend
    container_name: library-frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped

networks:
  app-network:
    driver: bridge
```

---

## 5. Variables de entorno: cuáles, dónde y por qué

### 5.1. Backend (archivo `.env` en la raíz)

```bash
# .env
# Clave secreta para firmar JWT. ¡Cambiar en producción! Mínimo 32 caracteres.
SECRET_KEY=mi-clave-secreta-super-segura-cambiar-en-produccion

# Minutos de expiración del token de acceso JWT
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**¿Cómo las lee la app?**
- `app/config.py` usa `python-dotenv` → `os.getenv("SECRET_KEY")`
- Docker pasa el `.env` mediante `env_file: .env` en `docker-compose.yml`

**⚠️ Reglas de seguridad:**
- `.env` **NO** debe versionarse en Git (está en `.gitignore`)
- En producción, usa un gestor de secretos (Docker secrets, Vault, etc.)
- Nunca escribas `SECRET_KEY` directamente en `docker-compose.yml`

### 5.2. Frontend (variable inline)

```yaml
environment:
  - NEXT_PUBLIC_API_URL=http://backend:8000
```

**¿Por qué inline y no en .env?**
- `NEXT_PUBLIC_API_URL` no es secreta, es una URL
- Next.js en build necesita las variables con prefijo `NEXT_PUBLIC_`
- En el `Dockerfile.frontend` **no** se usa `NEXT_PUBLIC_API_URL` durante el build porque la imagen final ya tiene el `.next/` compilado y la variable se resuelve en el cliente

**¿Por qué `http://backend:8000` y no `http://localhost:8000`?**
- `backend` es el nombre del servicio en docker-compose.yml
- Docker tiene un DNS interno que resuelve los nombres de servicio a IPs de contenedor
- Si usas `localhost:8000` desde el frontend, estarías buscando en el contenedor del frontend, no en el backend

---

## 6. Flujo de datos entre contenedores (arquitectura de red)

```
┌──────────────────────────────────────────────────────────────┐
│                     TU MÁQUINA (HOST)                        │
│                                                              │
│   http://localhost:3000          http://localhost:8000       │
│          │                              │                    │
│          ▼                              ▼                    │
│   ┌──────────────┐             ┌──────────────┐             │
│   │   FRONTEND   │             │   BACKEND    │             │
│   │  :3000       │  HTTP API   │  :8000       │             │
│   │              │ ──────────► │              │             │
│   │  library-    │             │  library-    │             │
│   │  frontend    │  ◄───────── │  api         │             │
│   └──────────────┘    JSON     └──────┬───────┘             │
│                                       │                     │
│                                       ▼                     │
│                              ┌──────────────┐              │
│                              │   TinyDB      │              │
│                              │   db.json     │              │
│                              │  (volumen)    │              │
│                              └──────────────┘              │
│                                                              │
│   Red: app-network (bridge)                                   │
│   DNS interno: backend → 172.x.x.x, frontend → 172.x.x.y    │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. Comandos: clasificados por propósito

### 7.1. Build (construir imágenes)

| Comando | Explicación |
|---|---|
| `docker compose build` | Construye las imágenes sin arrancar los contenedores |
| `docker compose build --no-cache` | Reconstruye desde cero, ignorando la caché de Docker |
| `docker compose build backend` | Construye solo la imagen del backend |
| `docker build -t library-api -f Dockerfile.backend .` | Build manual sin compose |
| `docker build -t library-frontend -f Dockerfile.frontend ./frontend` | Build manual del frontend |

**Explicación del formato:**
- `-t library-api` → asigna el nombre (tag) `library-api` a la imagen
- `-f Dockerfile.backend` → especifica qué Dockerfile usar (por defecto busca `Dockerfile`)
- `.` → contexto de build (carpeta desde donde se copian los archivos)

### 7.2. Up (arrancar contenedores)

| Comando | Explicación |
|---|---|
| `docker compose up` | Arranca servicios y muestra logs en terminal (bloqueante) |
| `docker compose up -d` | Arranca en segundo plano (detached mode) |
| `docker compose up --build` | Reconstruye imágenes antes de arrancar |
| `docker compose up --build -d` | Reconstruye + arranca en background |
| `docker compose up backend` | Arranca solo el backend |
| `docker compose up --scale backend=3` | Escalar backend a 3 réplicas (no recomendado con TinyDB) |

### 7.3. Logs (monitoreo)

| Comando | Explicación |
|---|---|
| `docker compose logs -f` | Logs de todos los servicios en tiempo real (follow) |
| `docker compose logs -f backend` | Logs solo del backend |
| `docker compose logs --tail=50 backend` | Últimas 50 líneas del backend |
| `docker compose logs -f --no-color` | Logs sin colores (útil para pipes) |

### 7.4. Down (detener y limpiar)

| Comando | Explicación |
|---|---|
| `docker compose down` | Detiene y elimina contenedores, redes |
| `docker compose down -v` | Además elimina volúmenes (¡borra la base de datos!) |
| `docker compose down --rmi all` | Además elimina las imágenes |
| `docker compose stop` | Solo detiene (no elimina) los contenedores |
| `docker compose start` | Reanuda contenedores detenidos |

### 7.5. Ejecución de comandos dentro de contenedores

| Comando | Explicación |
|---|---|
| `docker compose run --rm backend /app/.venv/bin/python seed.py` | Ejecuta seed.py dentro de un contenedor temporal (--rm lo borra al terminar) |
| `docker compose exec backend /bin/bash` | Abre una shell interactiva en el contenedor en ejecución |
| `docker exec -it library-api /bin/bash` | Abre shell usando el container_name (alternativa) |
| `docker compose exec backend /app/.venv/bin/python -c "print('hola')"` | Ejecuta un comando Python inline |

**Diferencia entre `run` y `exec`:**
- `docker compose run` → crea un **nuevo** contenedor temporal para ejecutar el comando
- `docker compose exec` → ejecuta el comando en un contenedor **ya en ejecución**

### 7.6. Inspección (diagnóstico)

| Comando | Explicación |
|---|---|
| `docker ps` | Lista contenedores en ejecución |
| `docker ps -a` | Lista todos los contenedores (incluyendo detenidos) |
| `docker images` | Lista imágenes descargadas |
| `docker compose images` | Lista imágenes usadas por el compose |
| `docker inspect library-api` | Información detallada del contenedor (IP, volúmenes, etc.) |
| `docker stats` | Consumo de CPU/RAM de contenedores en vivo |
| `docker system df` | Espacio ocupado por imágenes, contenedores, volúmenes |
| `docker container prune` | Limpia contenedores detenidos |

### 7.7. Salud y debugging

| Comando | Explicación |
|---|---|
| `docker compose ps` | Estado de los servicios (running, exited, healthy) |
| `docker compose events` | Eventos en tiempo real de los contenedores |
| `docker logs --tail 100 library-api` | Últimas 100 líneas del contenedor (sin compose) |
| `curl http://localhost:8000/books` | Prueba manual del endpoint |

---

## 8. Flujo de trabajo completo: desarrollo a producción

### 8.1. Primera vez (setup inicial)

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd dsmora-python-hello

# 2. Crear archivo .env con SECRET_KEY (¡OBLIGATORIO!)
#    Sin esto, la app falla al arrancar (RuntimeError en config.py)
echo "SECRET_KEY=mi-clave-super-segura-123456" > .env

# 3. Construir las imágenes (puede tomar 1-2 minutos la primera vez)
docker compose build

# 4. Arrancar los servicios en segundo plano
docker compose up -d

# 5. Verificar que ambos contenedores estén corriendo
docker compose ps

# 6. Sembrar datos de prueba en la base de datos TinyDB
#    Crea libros de ejemplo en data/db.json
docker compose run --rm backend /app/.venv/bin/python seed.py

# 7. Probar la API
curl http://localhost:8000/books | python -m json.tool

# 8. Abrir el frontend en el navegador
#    http://localhost:3000
```

### 8.2. Día a día (desarrollo)

```bash
# Arrancar servicios (si ya están construidos)
docker compose up -d

# Ver logs en vivo
docker compose logs -f

# Si cambias código Python, reconstruir backend
docker compose up -d --build backend

# Si cambias código del frontend, reconstruir frontend
docker compose up -d --build frontend

# Ejecutar seed si es necesario
docker compose run --rm backend /app/.venv/bin/python seed.py

# Detener todo al finalizar
docker compose down
```

### 8.3. Limpieza total

```bash
# Detener y eliminar todo (contenedores, redes, volúmenes, imágenes)
docker compose down -v --rmi all

# O aún más a fondo (limpiar todo Docker)
docker system prune -a --volumes
```

> **⚠️ Advertencia:** `system prune -a` borra TODAS las imágenes no usadas, contenedores detenidos y volúmenes. ¡Cuidado!

---

## 9. Perfil de desarrollo: hot-reload

### 9.1. `docker-compose.override.yml`

Cuando existe, Docker Compose lo **fusiona automáticamente** con `docker-compose.yml`. Es ideal para configuraciones de desarrollo sin modificar el archivo principal.

```yaml
# docker-compose.override.yml (NO versionar en producción)
services:
  backend:
    # Activar hot-reload de Uvicorn
    # --reload: reinicia el servidor cuando detecta cambios en archivos .py
    command: ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    # Montar el código fuente como volumen (sobreescribe el COPY del Dockerfile)
    # Los cambios en ./app/ se reflejan al instante dentro del contenedor
    volumes:
      - .:/app
      - ./data:/app/data   # Mantener persistencia de datos

  frontend:
    # Modo desarrollo de Next.js (con hot-reload)
    command: ["npm", "run", "dev"]
    # Montar el código del frontend
    volumes:
      - ./frontend:/app
      - /app/node_modules     # Volumen anónimo para no sobrescribir node_modules
      - /app/.next            # Volumen anónimo para no sobrescribir .next
```

**Importante:** El override **NO** se incluye en producción. En servidores, solo usas `docker-compose.yml`.

### 9.2. Perfiles de Compose

Otra alternativa más explícita es usar perfiles:

```yaml
# docker-compose.yml (añadir perfil)
services:
  backend:
    # ... configuración normal ...
    profiles:
      - prod       # Incluido en el perfil "prod"

  backend-dev:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: library-api-dev
    command: ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    volumes:
      - .:/app
      - ./data:/app/data
    env_file:
      - .env
    ports:
      - "8000:8000"
    profiles:
      - dev        # Solo se activa con --profile dev
    networks:
      - app-network
```

```bash
# Producción
docker compose --profile prod up

# Desarrollo
docker compose --profile dev up
```

---

## 10. Estrategia de caché de Docker (optimización de builds)

### 10.1. Orden óptimo de capas

```
  [MÁS ESTABLE]                             [MENOS ESTABLE]
  FROM → RUN apt-get → COPY deps → RUN deps → COPY código → CMD
  (nunca cambia)   (raro)        (a veces)     (siempre)
```

### 10.2. Cómo aprovechar el caché

En el `Dockerfile.backend`:

```dockerfile
# ❌ MAL: Copiar todo primero, luego instalar dependencias
#     Si cambias 1 línea de código, se invalidan las dependencias
COPY . .
RUN uv sync --no-dev --frozen   # Se reinstala cada vez que cambia el código

# ✅ BIEN: Dependencias primero, código después
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen   # Cacheado mientras no cambien las deps
COPY . .                         # Solo esta capa se reconstruye
```

### 10.3. Comandos de utilidad para caché

```bash
# Ver historial de capas de una imagen
docker history library-api

# Ver tamaño de cada capa
docker history --no-trunc library-api

# Limpiar caché de build
docker builder prune

# Forzar rebuild sin caché
docker compose build --no-cache
```

---

## 11. Seguridad en contenedores

### 11.1. Buenas prácticas implementadas

| Práctica | Backend | Frontend |
|---|---|---|
| **Usuario no-root** | `USER appuser` | `USER node` |
| **No exponer .env** | `env_file` en compose, no en imagen | Solo vars inline |
| **Base slim/alpine** | `python:3.12-slim` | `node:22-alpine` |
| **No incluir tools de build** | Multi-stage: builder separado | Multi-stage: builder separado |
| **Healthcheck** | Sí, para detectar caídas | No |

### 11.2. Por qué no usar root

```bash
# Si un atacante explota tu app y el contenedor corre como root:
# Puede instalar software, modificar archivos del host (volúmenes), etc.

# Con usuario no-root:
# Solo puede modificar archivos que el usuario tenga permisos (app/)
# No puede hacer apt-get, no puede escalar privilegios fácilmente
```

### 11.3. Escaneo de vulnerabilidades

```bash
# Escanear imagen en busca de vulnerabilidades conocidas
docker scout library-api

# También con herramientas externas:
# trivy image library-api
# grype library-api
```

---

## 12. Healthchecks y monitoreo

### 12.1. Cómo funciona el healthcheck

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/books"]
  interval: 30s    # Cada 30 segundos hace la prueba
  timeout: 10s     # Espera 10s por respuesta
  retries: 3       # 3 fallos seguidos = unhealthy
  start_period: 40s # Espera 40s antes del primer check (arranque)
```

### 12.2. Ver el estado de salud

```bash
# Ver columna STATUS con "healthy" o "unhealthy"
docker compose ps

# Inspeccionar healthchecks
docker inspect --format='{{json .State.Health}}' library-api

# Traer el healthcheck "a la fuerza"
docker compose exec backend curl -f http://localhost:8000/books
```

### 12.3. ¿Por qué el frontend espera al backend?

```yaml
depends_on:
  backend:
    condition: service_healthy
```

Sin esto, el frontend podría arrancar antes de que el backend esté listo, causando errores de conexión. `condition: service_healthy` asegura que el frontend espere hasta que el healthcheck del backend pase.

---

## 13. Solución de problemas (troubleshooting)

### 13.1. El contenedor no arranca

```bash
# Ver el estado
docker compose ps

# Ver logs
docker compose logs backend

# Ver si el error es de Python
# RuntimeError: SECRET_KEY is required → crear .env
```

### 13.2. Puerto ocupado

```bash
# Error: port is already allocated
# Solución: cambiar el mapeo en docker-compose.yml
ports:
  - "8001:8000"   # Acceder en localhost:8001
```

### 13.3. TinyDB no persiste datos

```bash
# Verificar que el volumen está montado
docker inspect library-api | grep -A 5 Mounts

# Si no hay volumen, los datos se pierden al hacer down
# Solución: asegurar volumes: ./data:/app/data en docker-compose.yml
```

### 13.4. Frontend no conecta con backend

```bash
# 1. Verificar que NEXT_PUBLIC_API_URL apunte al nombre del servicio
#    Debe ser: http://backend:8000 NO http://localhost:8000

# 2. Verificar que ambos estén en la misma red
docker network inspect dsmora-python-hello_app-network

# 3. Probar conectividad desde el frontend
docker compose exec frontend wget -qO- http://backend:8000/books
```

### 13.5. Error de permisos en data/db.json

```bash
# Si ves "Permission denied" al escribir en db.json
# Solución: dar permisos adecuados
sudo chown 1001:1001 data/db.json   # 1001 = uid del usuario appuser
# O simplemente borrar y regenerar:
rm data/db.json
docker compose run --rm backend /app/.venv/bin/python seed.py
```

### 13.6. La imagen es demasiado grande

```bash
# Ver tamaño
docker images library-api

# Backend con multi-stage debería pesar ~150-200MB
# Frontend con multi-stage debería pesar ~200-300MB

# Si es más grande:
# - Revisar .dockerignore (¿está excluyendo .venv? ¿node_modules?)
# - Revisar que uv sync use --no-dev
```

---

## 14. Tabla comparativa: comandos Docker vs Docker Compose

| Acción | Docker puro | Docker Compose |
|---|---|---|
| Construir | `docker build -t api -f Dockerfile.backend .` | `docker compose build` |
| Arrancar | `docker run -p 8000:8000 --env-file .env api` | `docker compose up -d` |
| Detener | `docker stop library-api` | `docker compose down` |
| Logs | `docker logs -f library-api` | `docker compose logs -f backend` |
| Shell | `docker exec -it library-api bash` | `docker compose exec backend bash` |
| Red | Crear red manual con `docker network create` | Se crea automáticamente |
| Volumen | `docker volume create` o `-v` | Se define en `volumes:` |

---

## 15. Posibles extensiones futuras

### 15.1. Base de datos PostgreSQL en lugar de TinyDB

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: library
      POSTGRES_USER: library
      POSTGRES_PASSWORD: secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

volumes:
  postgres_data:
```

### 15.2. Nginx como reverse proxy

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend
      - frontend
    networks:
      - app-network
```

### 15.3. Variables de build (ARG)

Útil para versionar imágenes:

```dockerfile
ARG APP_VERSION=1.0.0
LABEL version=${APP_VERSION}
```

```yaml
build:
  context: .
  args:
    APP_VERSION: 1.2.3
```

---

## 16. Glosario completo de términos Docker

| Término | Definición |
|---|---|
| **Imagen** | Plantilla inmodificable con SO + app + dependencias para crear contenedores |
| **Contenedor** | Proceso aislado ejecutando una imagen |
| **Dockerfile** | Receta con instrucciones para construir una imagen |
| **Capa (layer)** | Cada instrucción en un Dockerfile se guarda como una capa cacheable |
| **Contexto de build** | Carpeta que se envía al daemon de Docker para construir la imagen |
| **Multi-stage** | Varias etapas en un Dockerfile para separar build de ejecución |
| **Volumen** | Almacenamiento persistente externo al contenedor |
| **Bind mount** | Montar una carpeta del host directamente en el contenedor |
| **Red bridge** | Red virtual aislada donde los contenedores se comunican entre sí |
| **Port mapping** | Redirigir un puerto del host a un puerto del contenedor (`-p 8000:8000`) |
| **docker-compose.yml** | Archivo YAML que define y orquesta múltiples contenedores |
| **Service** | Definición de un contenedor dentro de docker-compose.yml |
| **Healthcheck** | Prueba periódica para verificar que un contenedor funciona correctamente |
| **Tag** | Etiqueta para identificar versiones de una imagen (`library-api:latest`) |
| **Registry** | Repositorio de imágenes (Docker Hub, GHCR, etc.) |
| **Entrypoint vs CMD** | Entrypoint es el ejecutable, CMD son los argumentos por defecto |
| **Docker daemon** | Proceso en segundo plano que gestiona contenedores, imágenes, redes |
| **Docker client** | CLI (`docker`) que se comunica con el daemon |

---

## 17. Resumen de archivos a crear (checklist)

| # | Archivo | Contenido breve |
|---|---|---|
| 1 | `.dockerignore` | Excluir `.venv/`, `__pycache__/`, `.env`, `node_modules/`, `.next/`, `data/db.json` |
| 2 | `frontend/.dockerignore` | Excluir `node_modules/`, `.next/`, `.env` |
| 3 | `Dockerfile.backend` | Multi-stage: builder con `uv sync`, final con `.venv` + código + usuario no-root |
| 4 | `Dockerfile.frontend` | Multi-stage: builder con `npm ci` + `npm run build`, final con `.next` + `node` |
| 5 | `docker-compose.yml` | 2 servicios (backend, frontend), red bridge, healthcheck, volúmenes |
| 6 | `.env` | `SECRET_KEY=...` (¡no versionar!) |