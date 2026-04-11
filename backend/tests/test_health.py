"""Tests for the health check endpoint."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(async_client: AsyncClient) -> None:
    """Health endpoint returns 200 with expected fields."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-counselor-api"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_has_request_id(async_client: AsyncClient) -> None:
    """Health response includes X-Request-ID header."""
    response = await async_client.get("/health")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


@pytest.mark.asyncio
async def test_health_content_type(async_client: AsyncClient) -> None:
    """Health endpoint returns JSON content type."""
    response = await async_client.get("/health")
    assert "application/json" in response.headers["content-type"]
