from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from app.controllers.auth_controller import router as auth_router
from app.controllers.books_controller import router as books_router
from app.controllers.profiles_controller import router as profiles_router
from app.controllers.telemetry_controller import router as telemetry_router
from app.controllers.users_controller import router as users_router
from app.db import init_tables

## fastapi_cache.backends.redis
@asynccontextmanager
async def lifespan(app: FastAPI):
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    yield


def create_app() -> FastAPI:
    init_tables()
    app = FastAPI(title="Library API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(books_router)
    app.include_router(users_router)
    app.include_router(profiles_router)
    app.include_router(telemetry_router)
    return app