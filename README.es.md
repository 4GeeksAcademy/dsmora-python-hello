# API de Librería

API pequeña para gestionar libros, construida con FastAPI, TinyDB y Pydantic, usando una estructura MVC ligera.

## Stack

- FastAPI
- TinyDB
- Pydantic

No se declaran más dependencias directas del proyecto.

## Estructura

```text
app/
	controllers/
	models/
	repositories/
	services/
	views/
data/
main.py
seed.py
pyproject.toml
uv.lock
```

## Instalación

```bash
uv sync
```

Este proyecto usa `uv` para gestionar dependencias. No uses `pip install` ni `pipenv`.

## Seed de prueba

```bash
uv run python seed.py
```

Si ejecutas el seed más de una vez, no duplicará los libros iniciales.

## Ejecutar la API

```bash
uv run python main.py
```

Esto levanta la API con Uvicorn en el puerto 8000.

## Endpoints

### Crear un libro

```http
POST /books
```

Cuerpo:

```json
{
	"title": "Dune",
	"author": "Frank Herbert",
	"genre": "sci-fi",
	"pages": 412,
	"status": "available"
}
```

### Listar libros

```http
GET /books
GET /books?genre=sci-fi
GET /books?status=available
GET /books?genre=sci-fi&status=available
```

### Obtener un libro por id

```http
GET /books/{id}
```

### Actualizar estado

```http
PATCH /books/{id}/status
```

Cuerpo:

```json
{
	"status": "checked_out"
}
```

### Eliminar un libro

```http
DELETE /books/{id}
```

## Reglas de validación

- `title`: string obligatorio
- `author`: string obligatorio
- `genre`: `fiction`, `non-fiction`, `mystery`, `sci-fi`
- `pages`: entero mayor que 0
- `status`: `available`, `checked_out`
