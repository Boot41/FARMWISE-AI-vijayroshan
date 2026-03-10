from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from starlette.responses import JSONResponse

from app.api.router import root_router
from app.core.logging import setup_logging
from app.db.session import get_sessionmaker
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.schemas.common import ErrorResponse


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    get_sessionmaker()
    logger.info("Application started")
    yield
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(title="FarmWise AI Backend", version="1.0.0", lifespan=lifespan)

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: FastAPI, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(message=message).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: FastAPI, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(message="Validation failed", errors=exc.errors()).model_dump(),
        )

    app.include_router(root_router)
    return app


app = create_app()
