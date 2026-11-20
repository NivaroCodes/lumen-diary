"""Точка входа FastAPI. Запуск: uvicorn app.main:app --reload (из папки backend/)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import Settings, load_settings
from .errors import ApiError
from .routes_days import media_router, router as days_router
from .storage import Storage

logger = logging.getLogger("lumen")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    storage = Storage(settings.data_dir)  # папки и БД создаются при первом обращении

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        storage.cleanup_tmp()
        yield

    app = FastAPI(title="Lumen Diary API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.storage = storage

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ApiError)
    async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(exc.body(), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        loc = [str(p) for p in first.get("loc", ()) if p not in ("query", "path", "body")]
        body = {"error": "validation_error", "field": ".".join(loc) or "request",
                "message": "Некорректное значение"}
        return JSONResponse(body, status_code=400)

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        codes = {404: "not_found", 405: "method_not_allowed"}
        return JSONResponse({"error": codes.get(exc.status_code, "http_error")}, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unexpected error", exc_info=exc)
        return JSONResponse({"error": "internal_error"}, status_code=500)

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(days_router, prefix="/api")
    app.include_router(media_router)
    return app


app = create_app()
