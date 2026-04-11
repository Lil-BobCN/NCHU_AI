"""API v1 router aggregation.

Imports and combines all v1 endpoint routers into a single APIRouter
that is mounted at /api/v1 in main.py.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.health import router as health_router
from app.api.v1.rag import router as rag_router

api_router = APIRouter()

# Register health at root level (not under /api/v1 prefix)
api_router.include_router(health_router)

# Register auth endpoints
api_router.include_router(auth_router, tags=["auth"])

# Register feature routers under v1 prefix
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(rag_router, prefix="/rag", tags=["rag"])
