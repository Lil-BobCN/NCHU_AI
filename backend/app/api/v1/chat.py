"""Chat session endpoints.

Provides CRUD for chat sessions and message operations.
Endpoints: POST /chat/sessions, GET /chat/sessions, GET /chat/sessions/{id},
           POST /chat/sessions/{id}/messages
"""
from __future__ import annotations

from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.deps import get_rag_service, get_session_service
from app.core.auth import get_current_user
from app.models.chat import (
    ChatSession,
    CreateSessionRequest,
    Message,
    SendMessageRequest,
)
from app.models.common import APIResponse, Pagination
from app.services.rag_service import RAGService
from app.services.session_service import SessionService

router = APIRouter()


@router.post(
    "/sessions",
    response_model=APIResponse,
    summary="Create a new chat session",
)
async def create_session(
    request: CreateSessionRequest,
    session_service: SessionService = Depends(get_session_service),
) -> dict:
    """Create a new chat session.

    Args:
        request: Session creation parameters.
        session_service: Injected SessionService.

    Returns:
        Created chat session data.
    """
    session = await session_service.create_session(
        user_id=request.user_id,
        title=request.title,
        college=request.college,
    )
    return APIResponse.success(
        data=session.model_dump(),
        message="Session created",
    ).model_dump()


@router.get(
    "/sessions",
    response_model=APIResponse,
    summary="List chat sessions",
)
async def list_sessions(
    user_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    session_service: SessionService = Depends(get_session_service),
) -> dict:
    """List chat sessions with optional filtering.

    Args:
        user_id: Filter by user ID.
        page: Page number for pagination.
        page_size: Items per page.
        session_service: Injected SessionService.

    Returns:
        Paginated list of chat sessions.
    """
    sessions, total = await session_service.list_sessions(
        user_id=user_id,
        limit=page_size,
        page=page,
    )
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return APIResponse.success(
        data=[s.model_dump() for s in sessions],
        pagination=Pagination(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
    ).model_dump()


@router.get(
    "/sessions/{session_id}",
    response_model=APIResponse,
    summary="Get a chat session",
)
async def get_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
) -> dict:
    """Get a single chat session by ID.

    Args:
        session_id: Unique session identifier.
        session_service: Injected SessionService.

    Returns:
        Chat session data.
    """
    session = await session_service.get_session(session_id)
    if session is None:
        return APIResponse.error(
            code=4004,
            message=f"Session '{session_id}' not found",
        ).model_dump()

    # Get recent messages as well
    messages = await session_service.get_messages(session_id, limit=10)

    return APIResponse.success(
        data={
            "session": session.model_dump(),
            "messages": [m.model_dump() for m in messages],
        },
    ).model_dump()


@router.delete(
    "/sessions/{session_id}",
    response_model=APIResponse,
    summary="Delete a chat session",
)
async def delete_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service),
) -> dict:
    """Delete a chat session and its messages.

    Args:
        session_id: Session to delete.
        session_service: Injected SessionService.

    Returns:
        Success confirmation.
    """
    deleted = await session_service.delete_session(session_id)
    if deleted:
        return APIResponse.success(
            message="Session deleted",
        ).model_dump()
    return APIResponse.error(
        code=4004,
        message=f"Session '{session_id}' not found",
    ).model_dump()


@router.post(
    "/sessions/{session_id}/messages",
    response_model=APIResponse,
    summary="Send a message in a chat session",
)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    session_service: SessionService = Depends(get_session_service),
    rag_service: RAGService = Depends(get_rag_service),
    current_user: str = Depends(get_current_user),
) -> dict:
    """Send a message and get an AI response.

    Args:
        session_id: Target chat session ID.
        request: Message content and optional metadata.
        session_service: Injected SessionService.
        rag_service: Injected RAGService.

    Returns:
        Assistant response message.
    """
    # Verify session exists
    session = await session_service.get_session(session_id)
    if session is None:
        return APIResponse.error(
            code=4004,
            message=f"Session '{session_id}' not found",
        ).model_dump()

    # Save user message
    await session_service.add_message(
        session_id=session_id,
        role="user",
        content=request.content,
    )

    # Get conversation history for context
    history = await session_service.get_messages(session_id, limit=10)
    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in history
    ]

    # Execute RAG pipeline
    rag_response = await rag_service.query(
        query=request.content,
        conversation_history=conversation_history,
    )

    # Build source metadata for the assistant message
    source_metadata = None
    if rag_response.sources:
        source_metadata = [
            {"content": s.content, "source": s.source, "score": s.score}
            for s in rag_response.sources
        ]

    # Save assistant response
    assistant_msg = await session_service.add_message(
        session_id=session_id,
        role="assistant",
        content=rag_response.context,
        metadata={"sources": source_metadata} if source_metadata else None,
    )

    return APIResponse.success(
        data=assistant_msg.model_dump(),
        message="Message sent",
    ).model_dump()


@router.post(
    "/sessions/{session_id}/messages/stream",
    summary="Send a message with streaming response (SSE)",
)
async def send_message_stream(
    session_id: str,
    request: SendMessageRequest,
    session_service: SessionService = Depends(get_session_service),
    rag_service: RAGService = Depends(get_rag_service),
    current_user: str = Depends(get_current_user),
) -> StreamingResponse:
    """Send a message and receive a streaming SSE response.

    Args:
        session_id: Target chat session ID.
        request: Message content.
        session_service: Injected SessionService.
        rag_service: Injected RAGService.

    Returns:
        StreamingResponse with SSE-formatted chunks.
    """
    session = await session_service.get_session(session_id)
    if session is None:
        # Return error as SSE
        async def error_stream() -> AsyncGenerator[str, None]:
            yield f'data: {{"error": "Session not found"}}\n\n'

        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
        )

    # Save user message
    await session_service.add_message(
        session_id=session_id,
        role="user",
        content=request.content,
    )

    # Get conversation history
    history = await session_service.get_messages(session_id, limit=10)
    conversation_history = [
        {"role": m.role, "content": m.content}
        for m in history
    ]

    async def generate() -> AsyncGenerator[str, None]:
        full_response = ""
        try:
            async for chunk in rag_service.stream_query(
                query=request.content,
                conversation_history=conversation_history,
            ):
                full_response += chunk
                yield chunk
        except Exception as exc:
            import json

            yield f'data: {json.dumps({"error": str(exc)})}\n\n'

        # Save the complete assistant response
        if full_response:
            try:
                await session_service.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                )
            except Exception:
                import logging
                logging.getLogger(__name__).warning(
                    "Failed to save assistant response for session %s",
                    session_id,
                )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )
