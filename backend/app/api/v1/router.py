"""API v1 router aggregation for the technical Phase 1 surface."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health import router as health_router

api_router = APIRouter()

# Phase 1 only exposes infrastructure liveness/readiness.
api_router.include_router(health_router)
