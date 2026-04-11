"""FastAPI application entry point with lifespan context manager."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.core.middleware import RequestIDMiddleware
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown lifecycle.

    On startup:
    - Configure structured logging
    - Initialize database connection pool
    - Initialize Redis connection pool
    - Warm up caches if applicable

    On shutdown:
    - Close database connections
    - Close Redis connections
    """
    # Startup
    settings = get_settings()
    setup_logging(level=settings.log_level)
    logger.info("Starting NCHU AI Counselor API v%s", settings.app_version)

    # TODO: Initialize database engine
    from app.db.session import init_db, close_db
    await init_db(settings.database_url)

    # TODO: Initialize Redis connection
    # from app.core.cache import init_redis, close_redis
    # await init_redis(settings.redis_url)

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down NCHU AI Counselor API")

    # TODO: Close database connections
    from app.db.session import close_db
    await close_db()

    # TODO: Close Redis connections
    # await close_redis()

    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="NCHU AI 心理辅导助手 API",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS middleware — with explicit null origin support for file:// pages
    cors_origins = settings.parse_cors_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Handle file:// protocol: Starlette's CORSMiddleware doesn't properly
    # match "Origin: null" against allow_origins containing "null".
    # This middleware intercepts responses and fixes the CORS headers.
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response

    class NullOriginMiddleware(BaseHTTPMiddleware):
        """Fix CORS for file:// pages that send Origin: null."""
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            origin = request.headers.get("origin", "")
            if origin == "null":
                response.headers["Access-Control-Allow-Origin"] = "null"
                response.headers["Access-Control-Allow-Credentials"] = "true"
            return response

    app.add_middleware(NullOriginMiddleware)

    # Request ID middleware
    app.add_middleware(RequestIDMiddleware)

    # Register routers
    from app.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")

    return app


def main() -> None:
    """Entry point for running the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:create_app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        factory=True,
    )


if __name__ == "__main__":
    main()
