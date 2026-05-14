"""FastAPI application entry point."""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    settings = get_settings()
    setup_logging(level=settings.log_level)
    logger.info("Starting NCHU AI Counselor API v%s", settings.app_version)

    from app.db.session import init_db

    await init_db(settings.database_url)
    logger.info("Application startup complete")

    yield

    logger.info("Shutting down NCHU AI Counselor API")
    from app.db.session import close_db

    await close_db()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="NCHU AI Counselor API technical Phase 1",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.parse_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestIDMiddleware)

    from app.api.v1.router import api_router

    app.include_router(api_router, prefix="/api/v1")
    return app


def main() -> None:
    """Run the application with uvicorn."""
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
