"""Health check endpoint.

Provides a simple health check for monitoring and load balancers.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import get_settings
from app.models.common import APIResponse

router = APIRouter()


@router.get(
    "/health",
    summary="Health check",
    description="Returns the current health status of the API service.",
    response_model=APIResponse,
)
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Health status dictionary with service name, version, and timestamp.
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "ai-counselor-api",
        "version": settings.app_version,
    }
