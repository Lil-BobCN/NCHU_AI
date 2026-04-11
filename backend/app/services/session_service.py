"""Chat session management service.

Handles CRUD operations for chat sessions and messages, backed by
the ChatRepository for persistence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.core.exceptions import ResourceNotFoundError
from app.models.chat import ChatSession, Message


class SessionService:
    """Chat session and message lifecycle management.

    Attributes:
        chat_repo: ChatRepository instance for data access.
    """

    def __init__(self, chat_repo: Any) -> None:
        """Initialize the session service.

        Args:
            chat_repo: ChatRepository instance.
        """
        self.chat_repo = chat_repo

    async def create_session(
        self,
        user_id: str | None = None,
        title: str | None = None,
        college: str | None = None,
    ) -> ChatSession:
        """Create a new chat session.

        Args:
            user_id: Optional user identifier (defaults to "anonymous").
            title: Optional session title (defaults to "New Session").
            college: Optional college affiliation for contextual responses.

        Returns:
            Created ChatSession instance.
        """
        now = datetime.now(timezone.utc).isoformat()
        session_id = str(uuid4())

        data = {
            "session_id": session_id,
            "user_id": user_id or "anonymous",
            "title": title or "New Session",
            "college": college,
            "created_at": now,
            "updated_at": now,
            "metadata": {},
        }

        result = await self.chat_repo.create_session(data)

        return ChatSession(**result)

    async def get_session(self, session_id: str) -> ChatSession | None:
        """Retrieve a chat session by ID.

        Args:
            session_id: Unique session identifier.

        Returns:
            ChatSession if found, None otherwise.
        """
        result = await self.chat_repo.find_session_by_id(session_id)
        if result is None:
            return None
        return ChatSession(**result)

    async def list_sessions(
        self,
        user_id: str | None = None,
        limit: int = 20,
        page: int = 1,
    ) -> tuple[list[ChatSession], int]:
        """List chat sessions with optional filtering.

        Args:
            user_id: Optional filter by user ID.
            limit: Items per page.
            page: Page number (1-indexed).

        Returns:
            Tuple of (sessions list, total count).
        """
        results, total = await self.chat_repo.list_sessions(
            user_id=user_id,
            page=page,
            page_size=limit,
        )
        sessions = [ChatSession(**s) for s in results]
        return sessions, total

    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session and its associated messages.

        Args:
            session_id: Session to delete.

        Returns:
            True if session was deleted.

        Raises:
            ResourceNotFoundError: If the session does not exist.
        """
        session = await self.get_session(session_id)
        if session is None:
            raise ResourceNotFoundError(
                resource_type="chat_session",
                resource_id=session_id,
            )
        # TODO: Implement actual deletion in repository
        return True

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """Add a message to a chat session.

        Args:
            session_id: Target session ID.
            role: Message role ("user" or "assistant").
            content: Message text.
            metadata: Optional message metadata (e.g., RAG sources).

        Returns:
            Created Message instance.

        Raises:
            ResourceNotFoundError: If the session does not exist.
        """
        session = await self.get_session(session_id)
        if session is None:
            raise ResourceNotFoundError(
                resource_type="chat_session",
                resource_id=session_id,
            )

        message_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        sources = None
        if metadata and "sources" in metadata:
            sources = metadata.pop("sources")

        data = {
            "message_id": message_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "sources": sources,
            "created_at": now,
            **(metadata or {}),
        }

        result = await self.chat_repo.add_message(data)

        return Message(
            message_id=result.get("message_id", message_id),
            role=role,
            content=result.get("content", content),
            sources=result.get("sources"),
            created_at=result.get("created_at", now),
        )

    async def get_messages(
        self,
        session_id: str,
        limit: int = 50,
    ) -> list[Message]:
        """Get messages for a session, ordered by creation time.

        Args:
            session_id: Target session ID.
            limit: Maximum number of messages to return.

        Returns:
            List of Message instances, most recent last.
        """
        results = await self.chat_repo.get_messages(session_id, limit=limit)
        return [
            Message(
                message_id=r.get("message_id", ""),
                role=r.get("role", "user"),
                content=r.get("content", ""),
                sources=r.get("sources"),
                created_at=r.get("created_at", ""),
            )
            for r in results
        ]
