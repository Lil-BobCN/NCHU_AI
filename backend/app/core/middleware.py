"""Middleware components for the FastAPI application.

Includes CORS (handled via FastAPI built-in), request ID tracking,
and a rate limiter stub.
"""
from __future__ import annotations

import time
import uuid
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# In-memory rate limit store (stub — replace with Redis in production)
_rate_limit_store: dict[str, list[float]] = defaultdict(list)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Generate and attach a unique request ID to every request/response.

    The request ID is:
    - Generated as a UUID for each incoming request
    - Stored in request.state.request_id for downstream use
    - Returned in the X-Request-ID response header
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request with generated request ID.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware/handler in the chain.

        Returns:
            Response with X-Request-ID header.
        """
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter (stub for development).

    Tracks requests per client IP within sliding time windows.
    For production, replace with Redis-backed implementation.
    """

    def __init__(
        self,
        app: object,
        max_requests_per_minute: int = 60,
        max_requests_per_hour: int = 1000,
    ) -> None:
        """Initialize rate limiter.

        Args:
            app: ASGI application.
            max_requests_per_minute: Max requests allowed per minute.
            max_requests_per_hour: Max requests allowed per hour.
        """
        super().__init__(app)
        self.max_per_minute = max_requests_per_minute
        self.max_per_hour = max_requests_per_hour

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Check rate limit before processing request.

        Args:
            request: Incoming HTTP request.
            call_next: Next middleware/handler in the chain.

        Returns:
            Response or 429 Too Many Requests.
        """
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Clean old entries
        _rate_limit_store[client_ip] = [
            ts for ts in _rate_limit_store[client_ip] if now - ts < 3600
        ]

        timestamps = _rate_limit_store[client_ip]
        minute_count = sum(1 for ts in timestamps if now - ts < 60)
        hour_count = len(timestamps)

        if minute_count >= self.max_per_minute:
            return Response(
                content='{"error": "Rate limit exceeded (per minute)"}',
                status_code=429,
                media_type="application/json",
            )

        if hour_count >= self.max_per_hour:
            return Response(
                content='{"error": "Rate limit exceeded (per hour)"}',
                status_code=429,
                media_type="application/json",
            )

        timestamps.append(now)
        return await call_next(request)
