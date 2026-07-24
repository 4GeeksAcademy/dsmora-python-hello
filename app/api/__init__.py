from fastapi import FastAPI

from app.adapters import PostgreSQLDummyRepository
from app.api.routes import register_routes


def create_app(repository: PostgreSQLDummyRepository | None = None) -> FastAPI:
    app = FastAPI(title="Shopping List API", version="1.0.0")
    repo = repository or PostgreSQLDummyRepository()
    register_routes(app, repo)
    return app


app = create_app()
