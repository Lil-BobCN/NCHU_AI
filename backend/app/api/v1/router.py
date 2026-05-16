"""API v1 router aggregation for the technical Phase 1 surface."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.counselor import router as counselor_router
from app.api.v1.health import router as health_router
from app.api.v1.student import router as student_router

api_router = APIRouter()

# Phase 1 exposes infrastructure and in-memory business routes.
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(student_router)
api_router.include_router(counselor_router)
api_router.include_router(admin_router)
