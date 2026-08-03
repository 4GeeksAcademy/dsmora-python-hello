# Library API

Small library management API built with FastAPI, TinyDB and Pydantic using a lightweight MVC structure.

## Stack

- FastAPI
- TinyDB
- Pydantic

No other direct project dependencies are declared.

## Project Structure

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
requirements.txt
```

## Install

```bash
pip install -r requirements.txt
```

## Seed Test Data

```bash
python seed.py
```

Running the seed multiple times does not duplicate the initial books.

## Run The API

```bash
python main.py
```

This starts the API with Uvicorn on port 8000.

## Endpoints

### Create a book

```http
POST /books
```

Body:

```json
{
	"title": "Dune",
	"author": "Frank Herbert",
	"genre": "sci-fi",
	"pages": 412,
	"status": "available"
}
```

### List books

```http
GET /books
GET /books?genre=sci-fi
GET /books?status=available
GET /books?genre=sci-fi&status=available
```

### Get one book

```http
GET /books/{id}
```

### Update status

```http
PATCH /books/{id}/status
```

Body:

```json
{
	"status": "checked_out"
}
```

### Delete a book

```http
DELETE /books/{id}
```

## Validation Rules

- `title`: required string
- `author`: required string
- `genre`: `fiction`, `non-fiction`, `mystery`, `sci-fi`
- `pages`: integer greater than 0
- `status`: `available`, `checked_out`
