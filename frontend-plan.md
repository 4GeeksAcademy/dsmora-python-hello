# Frontend Plan — Next.js + Tailwind + TypeScript

## 1. Crear aplicación Next.js

- Next.js con **Pages Router** (sin `/src`)
- **TypeScript**
- **Tailwind CSS** para estilos
- Diseño **mobile-first responsive** (grid adaptativo en home, layouts flexibles)

---

## 2. Estructura del proyecto

```
frontend/
├── pages/
│   ├── index.tsx          # Home: listado de libros con filtros
│   └── books/
│       └── [id].tsx       # Detalle de libro individual
├── components/
│   ├── Layout.tsx          # Layout general (header, main container, footer)
│   ├── BookCard.tsx        # Tarjeta de libro para la lista
│   ├── BookFilters.tsx     # Filtros de género y estado
│   ├── BookDetail.tsx      # Vista de detalle del libro
│   ├── LoadingSpinner.tsx  # Indicador de carga
│   ├── ErrorMessage.tsx    # Mensaje de error
│   └── EmptyState.tsx      # Estado vacío (sin resultados)
├── hooks/
│   ├── useBooks.ts         # Hook: listar libros (con filtros)
│   └── useBook.ts          # Hook: obtener libro por ID
├── lib/
│   └── api.ts              # Cliente fetch base (base URL, manejo de errores)
├── types/
│   └── book.ts             # Interfaces Book, BookGenre, BookStatus
└── styles/
    └── globals.css         # Estilos globales + directivas Tailwind
```

---

## 3. Endpoints a consumir (sin autenticación)

Del backend, solo se implementan las rutas **públicas**:

| Método | Endpoint            | Descripción                        | Parámetros                           |
|--------|---------------------|------------------------------------|--------------------------------------|
| GET    | `/books`            | Listar libros (con filtros)        | `?genre=fiction&status=available`    |
| GET    | `/books/{id}`       | Obtener detalle de un libro        | `id` (int)                           |

> Los endpoints `POST /books`, `GET /books/reserved` requieren autenticación y quedan fuera del alcance del frontend inicial.

---

## 4. Páginas

### 4.1 Home (`/`) — Listado de libros

- **Header** con título de la app
- **Barra de filtros**:
  - Selector de **género**: `fiction`, `non-fiction`, `mystery`, `sci-fi` (múltiple o todos)
  - Selector de **estado**: `available`, `checked_out` (múltiple o todos)
- **Grid responsive** de tarjetas (`BookCard`):
  - Desktop: 3-4 columnas
  - Tablet: 2 columnas
  - Mobile: 1 columna
- Cada `BookCard` muestra: título, autor, género (badge), estado (badge), nº de páginas
- Al hacer clic → navega a `/books/{id}`
- **Estados**:
  - **Loading**: spinner mientras carga
  - **Error**: mensaje de error con posibilidad de reintentar
  - **Empty**: mensaje "No se encontraron libros" cuando no hay resultados
  - **Success**: grid de tarjetas

### 4.2 Detalle (`/books/[id]`) — Ficha del libro

- Muestra toda la información del libro:
  - Título
  - Autor
  - Género (badge)
  - Estado (badge con color: verde = available, naranja = checked_out)
  - Número de páginas
- **Botonera**:
  - "Volver al listado" → navega a `/`
- **Estados**:
  - **Loading**: spinner
  - **Error (404)**: mensaje "Libro no encontrado"
  - **Error (genérico)**: mensaje con opción de reintentar

---

## 5. Componentes

### `Layout.tsx`
- Header con nombre de la app y navegación simple
- `<main>` con padding responsive
- Footer minimalista

### `BookCard.tsx`
- Props: `book: BookResponse`
- Muestra tarjeta con sombra suave, hover effect
- Badge de género con color por tipo
- Badge de estado (disponible / prestado)
- Enlace a `/books/{id}`

### `BookFilters.tsx`
- Props: `onFilterChange(filters: BookFilters)`
- Select múltiple de género
- Select de estado (todos / available / checked_out)
- Botón "Limpiar filtros"
- Se oculta/muestra responsive

### `BookDetail.tsx`
- Props: `book: BookResponse`
- Layout de detalle con información completa

### `LoadingSpinner.tsx`
- Spinner animado con Tailwind

### `ErrorMessage.tsx`
- Props: `message: string`, `onRetry?: () => void`
- Icono de error, mensaje y botón "Reintentar"

### `EmptyState.tsx`
- Props: `message?: string`
- Icono de libro vacío y mensaje personalizable

---

## 6. Hooks personalizados

### `useBooks(filters?: BookFilters)`
- Llama a `GET /books` con filtros opcionales
- Retorna `{ books, isLoading, error, refetch }`
- Manejo de errores con try/catch

### `useBook(id: number)`
- Llama a `GET /books/{id}`
- Retorna `{ book, isLoading, error, refetch }`
- Manejo de errores con try/catch

---

## 7. Capa de API (`lib/api.ts`)

- `BASE_URL` configurable (por defecto `http://localhost:8000`)
- Función `fetchApi<T>(path, options?)` que:
  - Construye la URL completa
 - Aplica `Content-Type: application/json`
  - Lanza errores con mensajes descriptivos
  - Parsea JSON tipado

---

## 8. Tipos compartidos (`types/book.ts`)

```typescript
export type BookGenre = 'fiction' | 'non-fiction' | 'mystery' | 'sci-fi';
export type BookStatus = 'available' | 'checked_out';

export interface BookResponse {
  id: number;
  title: string;
  author: string;
  genre: BookGenre;
  pages: number;
  status: BookStatus;
}

export interface BookFilters {
  genre?: BookGenre;
  status?: BookStatus;
}
```

---

## 9. Plan de implementación (orden sugerido)

| Paso | Descripción |
|------|-------------|
| 1 | `npx create-next-app` con TypeScript + Tailwind, Pages Router, sin `/src` |
| 2 | Crear `types/book.ts` con interfaces |
| 3 | Crear `lib/api.ts` con cliente fetch base |
| 4 | Crear `hooks/useBooks.ts` y `hooks/useBook.ts` |
| 5 | Crear componentes atómicos: `LoadingSpinner`, `ErrorMessage`, `EmptyState` |
| 6 | Crear `BookCard.tsx` |
| 7 | Crear `BookFilters.tsx` |
| 8 | Crear `Layout.tsx` |
| 9 | Implementar página Home (`pages/index.tsx`) componiendo todo |
| 10 | Crear `BookDetail.tsx` |
| 11 | Implementar página Detalle (`pages/books/[id].tsx`) |
| 12 | Ajustes responsive finales y pruebas |

--------
FASE 2
Autenticación 
--------

## Objetivo
Implementar autenticación completa con control de acceso por rol y consumo de endpoints privados.

## Decisiones cerradas
- Persistencia del token: localStorage.
- Ruta tras login exitoso: perfil (/profile).
- Reserva de libro: usar PATCH /books/{id}/status con status=checked_out.
- Manejo global de 401 en rutas privadas: limpiar token y redirigir a /login.
- Roles disponibles en registro (UI): user, manager y admin.

## Funcionalidad a implementar
### 1) Registro
- Crear formulario de registro con: email, password, name, phone, address y role.
- Validaciones mínimas de cliente:
  - email válido
  - password con mínimo 8 caracteres
  - campos de perfil no vacíos

### 2) Login
- Crear formulario de login con email y password.
- En respuesta 200:
  - guardar access_token en localStorage
  - redirigir a /profile

### 3) Sesión y autorización
- Implementar logout cliente:
  - eliminar token de localStorage
  - redirigir a /
- Crear guard de rutas privadas (por ejemplo /profile, /reservations, /admin/books/new):
  - sin token: redirigir a /login y limpiar localStorage
  - con 401 del backend: redirigir a /login y limpiar localStorage
- Crear guard por rol para rutas de administrador/manager:
  - si backend responde 403: redirigir a /
  - no limpiar token en caso de 403

### 4) Página de perfil
- Crear /profile como pantalla privada.
- Mostrar datos del usuario autenticado (email + perfil) y acciones básicas de sesión.

### 5) Endpoints privados de libros
- Crear libro (solo admin/manager): POST /books.
- Reservar libro (usuario autenticado): PATCH /books/{id}/status con status=checked_out.
- Listado de reservas del usuario: GET /books/reserved.

### 6) Vistas por rol
- Vista user:
  - reservar libros
  - ver sus reservas
- Vista admin/manager:
  - crear libro
  - acceso a secciones de gestión (y futura extensión para editar/eliminar)

## Casos de uso (CAU)
CAU1. Usuario sin token en página privada
    Redirigir a /login
    Limpiar localStorage

CAU2. Login exitoso (200)
    Guardar token
    Redirigir a /profile

CAU3. Usuario cierra sesión
    Limpiar localStorage
    Redirigir a /

CAU4. Usuario con token válido pero rol incorrecto (403)
    Redirigir a /
    No limpiar token

CAU5. Usuario con token expirado/inválido (401) en endpoint privado
    Limpiar localStorage
    Redirigir a /login

## Flecos detectados a resolver
- El backend actual de registro no expone role en el payload de creación de usuario. Para cumplir este requisito, hay que extender el endpoint de registro para aceptar role de forma explícita y segura.
- El endpoint /auth/me devuelve email + profile; para UI basada en rol, el frontend tomará el role del JWT o se añadirá role al response de /auth/me.

