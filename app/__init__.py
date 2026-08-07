from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.auth_controller import router as auth_router
from app.controllers.books_controller import router as books_router
from app.controllers.profiles_controller import router as profiles_router
from app.controllers.users_controller import router as users_router
from app.db import init_tables


def create_app() -> FastAPI:
    init_tables()
    app = FastAPI(title="Library API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://silver-guide-7vgxwxwq9pjg2x49x-3000.app.github.dev"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(books_router)
    app.include_router(users_router)
    app.include_router(profiles_router)
    return app