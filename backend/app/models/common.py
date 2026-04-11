"""Shared API response models.

Implements the envelope pattern for all API responses:
    {"code": 200, "message": "success", "request_id": "...", "timestamp": "...", "data": {...}, "pagination": {...}}
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class Pagination(BaseModel):
    """Pagination metadata included in list responses.

    Attributes:
        total: Total number of items.
        page: Current page number (1-indexed).
        page_size: Number of items per page.
        total_pages: Total number of pages.
    """

    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0


class ErrorResponse(BaseModel):
    """Error response body.

    Attributes:
        code: Application-specific error code.
        message: Human-readable error description.
        details: Optional structured error details.
    """

    code: int = 5000
    message: str = "Internal server error"
    details: dict[str, Any] | None = None


class APIResponse(BaseModel):
    """Standard API response envelope.

    All endpoints return responses wrapped in this envelope for consistency.

    Attributes:
        code: HTTP-equivalent status code (200 = success).
        message: Human-readable status message.
        data: Response payload (null on error).
        pagination: Pagination metadata (null for non-list responses).
        error: Error details (null on success).
        request_id: Unique request identifier for tracing.
        timestamp: ISO 8601 response timestamp.
    """

    code: int = 200
    message: str = "success"
    data: dict[str, Any] | list[Any] | None = None
    pagination: Pagination | None = None
    error: ErrorResponse | None = None
    request_id: str = Field(
        default_factory=lambda: "",
        description="Unique request ID from X-Request-ID header",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 response timestamp",
    )

    @classmethod
    def success(
        cls,
        data: Any = None,
        message: str = "success",
        pagination: Pagination | None = None,
    ) -> "APIResponse":
        """Create a success response.

        Args:
            data: Response payload.
            message: Status message.
            pagination: Optional pagination metadata.

        Returns:
            APIResponse instance with success status.
        """
        return cls(code=200, message=message, data=data, pagination=pagination)

    @classmethod
    def error(
        cls,
        code: int = 5000,
        message: str = "error",
        details: dict[str, Any] | None = None,
    ) -> "APIResponse":
        """Create an error response.

        Args:
            code: Application error code.
            message: Error description.
            details: Optional structured error details.

        Returns:
            APIResponse instance with error status.
        """
        return cls(
            code=code,
            message=message,
            data=None,
            error=ErrorResponse(code=code, message=message, details=details),
        )
