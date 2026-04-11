# FastAPI application package


def create_app() -> "FastAPI":
    """Application factory — implemented in main.py to avoid circular imports."""
    from app.main import lifespan
    from fastapi import FastAPI

    app = FastAPI(
        title="NCHU AI Counselor API",
        description="AI 心理辅导助手 API — FastAPI migration",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Register routers
    from app.api.v1.router import api_router
    app.include_router(api_router)

    return app
