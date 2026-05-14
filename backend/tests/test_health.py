"""Tests for the health check endpoint."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(async_client: AsyncClient) -> None:
    """Health endpoint returns 200 with expected fields."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-counselor-api"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_has_request_id(async_client: AsyncClient) -> None:
    """Health response includes X-Request-ID header."""
    response = await async_client.get("/api/v1/health")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


@pytest.mark.asyncio
async def test_health_content_type(async_client: AsyncClient) -> None:
    """Health endpoint returns JSON content type."""
    response = await async_client.get("/api/v1/health")
    assert "application/json" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_readiness_returns_checks(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Readiness endpoint returns dependency check details."""
    from app.api.v1 import health

    async def fake_checks(_settings):
        return {
            "postgres": {"status": "ready", "operation": "select_1"},
            "redis": {"status": "ready", "operation": "ping"},
            "minio": {"status": "ready", "operation": "list_buckets"},
            "milvus": {"status": "ready", "operation": "list_collections"},
        }

    monkeypatch.setattr(health, "_run_readiness_checks", fake_checks)
    response = await async_client.get("/api/v1/readiness")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert set(data["checks"]) == {"postgres", "redis", "minio", "milvus"}


@pytest.mark.asyncio
async def test_phase1_does_not_expose_business_routes(async_client: AsyncClient) -> None:
    """Phase 1 should not expose incomplete auth/chat/RAG business endpoints."""
    for path in (
        "/api/v1/auth/me",
        "/api/v1/chat/sessions",
        "/api/v1/rag/retrieval",
    ):
        response = await async_client.get(path)
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_phase1_does_not_expose_docs_routes(async_client: AsyncClient) -> None:
    """Phase 1 should expose only health/readiness HTTP routes."""
    for path in ("/docs", "/redoc", "/openapi.json"):
        response = await async_client.get(path)
        assert response.status_code == 404
