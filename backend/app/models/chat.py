"""Chat domain models.

Pydantic models for chat sessions, messages, and request/response schemas.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatSession(BaseModel):
    """A chat session between a user and the AI counselor.

    Attributes:
        session_id: Unique session identifier (UUID).
        user_id: Associated user identifier.
        title: Session display title.
        college: Optional college affiliation for contextual responses.
        created_at: Session creation timestamp (ISO 8601).
        updated_at: Last activity timestamp (ISO 8601).
        metadata: Optional session-level metadata.
    """

    session_id: str
    user_id: str = "anonymous"
    title: str = "New Session"
    college: str | None = None
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """A single message within a chat session.

    Attributes:
        message_id: Unique message identifier.
        role: Message role ('user', 'assistant', or 'system').
        content: Message text content.
        sources: Optional RAG source references for assistant messages.
        created_at: Message creation timestamp (ISO 8601).
    """

    message_id: str
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str
    sources: list[dict[str, Any]] | None = None
    created_at: str


class CreateSessionRequest(BaseModel):
    """Request body for creating a new chat session.

    Attributes:
        user_id: Optional user identifier.
        title: Optional session title.
        college: Optional college for contextual responses.
    """

    user_id: str | None = None
    title: str | None = None
    college: str | None = None


class SendMessageRequest(BaseModel):
    """Request body for sending a message in a chat session.

    Attributes:
        content: Message text.
        stream: Whether to stream the response (SSE).
    """

    content: str = Field(..., min_length=1, max_length=4000)
    stream: bool = False
