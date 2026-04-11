"""Custom exception hierarchy for the AI Counselor API.

Defines domain-specific exceptions that map to appropriate HTTP status codes
and user-friendly error messages.
"""
from __future__ import annotations


class BusinessException(Exception):
    """Base exception for all business logic errors.

    Attributes:
        message: Human-readable error description.
        code: Application-specific error code.
        status_code: HTTP status code for the response.
    """

    def __init__(
        self,
        message: str = "Business error occurred",
        code: int = 4000,
        status_code: int = 400,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)


class RetrievalError(BusinessException):
    """Raised when RAG retrieval fails (vector store errors, embedding failures).

    Attributes:
        message: Error description.
    """

    def __init__(self, message: str = "Retrieval failed") -> None:
        super().__init__(message=message, code=5001, status_code=500)


class LLMError(BusinessException):
    """Raised when LLM API call fails (rate limit, timeout, API error).

    Attributes:
        message: Error description.
    """

    def __init__(self, message: str = "LLM service unavailable") -> None:
        super().__init__(message=message, code=5002, status_code=502)


class ValidationError(BusinessException):
    """Raised when input validation fails.

    Attributes:
        message: Error description.
        field: Optional field name that failed validation.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        field: str | None = None,
    ) -> None:
        self.field = field
        super().__init__(message=message, code=4001, status_code=422)


class ResourceNotFoundError(BusinessException):
    """Raised when a requested resource does not exist.

    Attributes:
        resource_type: Type of the missing resource (e.g., 'chat_session').
        resource_id: Identifier of the missing resource.
    """

    def __init__(
        self,
        resource_type: str = "resource",
        resource_id: str | None = None,
    ) -> None:
        detail = f"{resource_type}"
        if resource_id:
            detail += f" '{resource_id}'"
        message = f"{detail} not found"
        super().__init__(message=message, code=4004, status_code=404)
