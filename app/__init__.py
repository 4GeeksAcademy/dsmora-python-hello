from fastapi import FastAPI

from app.controllers.books_controller import router as books_router


def create_app() -> FastAPI:
    app = FastAPI(title="Library API")
    app.include_router(books_router)
    return app