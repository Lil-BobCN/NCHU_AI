"""Pytest fixtures for async FastAPI testing.

Provides an async test client, test database, and application instance.
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app():
    """Create the FastAPI application instance for testing.

    Returns:
        FastAPI application.
    """
    return create_app()


@pytest.fixture
async def async_client(app):
    """Create an async HTTP client for testing.

    Args:
        app: FastAPI application fixture.

    Yields:
        AsyncClient configured for the test application.
    """
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_db():
    """Create and tear down a test database.

    Yields:
        Test database URL string.

    Note:
        TODO: Configure a test-specific PostgreSQL database.
        Consider using testcontainers or an in-memory SQLite for unit tests.
    """
    # TODO: Set up test database
    test_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_nchu_ai_counselor"
    yield test_url
    # TODO: Tear down test database
