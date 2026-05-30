"""Student self-service routes for Q&A, resources, and conversations."""
from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.v1.deps import chat_model_provider, current_user
from app.config import Settings, get_settings
from app.schemas.business import (
    ConversationCreate,
    ConversationMessageCreate,
    ConversationResponse,
    QuestionRequest,
    QuestionResponse,
    ResourceResponse,
    StudentChatRequest,
)
from app.services.business import Conversation, User, store
from app.services.chat_model import (
    ChatModelConfigurationError,
    ChatModelError,
    ChatModelMessage,
    ChatModelProvider,
)

router = APIRouter(prefix="/student", tags=["student"])


@router.post("/questions", response_model=QuestionResponse)
async def ask_question(
    payload: QuestionRequest,
    user: Annotated[User, Depends(current_user)],
) -> QuestionResponse:
    """Ask the counselor assistant a student-facing question."""
    message = store.answer_question(user.id, payload.question)
    return QuestionResponse(answer=message.content, resources=message.resources)


@router.post("/chat/stream")
async def stream_student_chat(
    payload: StudentChatRequest,
    user: Annotated[User, Depends(current_user)],
    provider: Annotated[ChatModelProvider, Depends(chat_model_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StreamingResponse:
    """Stream a real-model assistant reply for the isolated student Chatbox."""
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student chat is only available to student accounts",
        )
    if not provider.configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Qwen model configuration is missing. Set DASHSCOPE_API_KEY and "
                "DASHSCOPE_MODEL, or the legacy QWEN_API_KEY and QWEN_MODEL aliases."
            ),
        )

    conversation = _student_chat_conversation(payload, user)
    store.append_conversation_message(conversation, "student", payload.message)
    model_messages = _conversation_model_messages(
        conversation,
        limit=settings.chat_model_context_message_limit,
    )

    return StreamingResponse(
        _stream_chat_events(conversation, user, provider, model_messages),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/resources", response_model=list[ResourceResponse])
async def list_resources(
    query: str = "",
    category: str | None = None,
) -> list[ResourceResponse]:
    """List published support resources from the in-memory knowledge base."""
    return store.search_resources(query=query, category=category)


@router.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(resource_id: str) -> ResourceResponse:
    """Get a published support resource by id."""
    resource = next(
        (item for item in store.search_resources() if item.id == resource_id),
        None,
    )
    if resource is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return ResourceResponse.model_validate(resource)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    user: Annotated[User, Depends(current_user)],
) -> list[ConversationResponse]:
    """List conversations owned by the current student."""
    return [
        item
        for item in store.conversations.values()
        if item.student_id == user.id or user.role in {"counselor", "admin"}
    ]


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: ConversationCreate,
    user: Annotated[User, Depends(current_user)],
) -> ConversationResponse:
    """Create a student conversation, optionally seeded with a first message."""
    return store.create_conversation(user.id, payload.title, payload.message)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user: Annotated[User, Depends(current_user)],
) -> ConversationResponse:
    """Get one conversation visible to the current user."""
    return _visible_conversation(conversation_id, user)


@router.post("/conversations/{conversation_id}/messages", response_model=ConversationResponse)
async def add_conversation_message(
    conversation_id: str,
    payload: ConversationMessageCreate,
    user: Annotated[User, Depends(current_user)],
) -> ConversationResponse:
    """Append a student message and generated assistant reply."""
    conversation = _visible_conversation(conversation_id, user)
    if conversation.student_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owning student can add messages",
        )
    return store.add_student_message(conversation, payload.content)


def _visible_conversation(conversation_id: str, user: User) -> Conversation:
    conversation = store.conversations.get(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    if conversation.student_id != user.id and user.role not in {"counselor", "admin"}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


def _student_chat_conversation(payload: StudentChatRequest, user: User) -> Conversation:
    if payload.conversation_id:
        conversation = _visible_conversation(payload.conversation_id, user)
        if conversation.student_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owning student can use this conversation",
            )
        return conversation
    title = payload.message.strip().replace("\n", " ")[:32] or "New chat"
    return store.create_empty_conversation(user.id, title)


def _conversation_model_messages(
    conversation: Conversation,
    *,
    limit: int,
) -> list[ChatModelMessage]:
    role_map = {"student": "user", "assistant": "assistant"}
    messages = [
        ChatModelMessage(role=role_map[message.role], content=message.content)
        for message in conversation.messages
        if message.role in role_map and message.content.strip()
    ]
    return messages[-limit:]


async def _stream_chat_events(
    conversation: Conversation,
    user: User,
    provider: ChatModelProvider,
    model_messages: list[ChatModelMessage],
) -> AsyncIterator[str]:
    chunks: list[str] = []
    yield _sse("conversation", {"conversationId": conversation.id})
    try:
        async for chunk in provider.stream_reply(model_messages):
            chunks.append(chunk)
            yield _sse("delta", {"content": chunk})
    except ChatModelConfigurationError as exc:
        yield _sse("error", {"detail": str(exc)})
        return
    except ChatModelError as exc:
        store.record_audit(
            user.id,
            "student.chat.stream.failure",
            "conversation",
            conversation.id,
            result="failure",
            event_tags=["chat:model:qwen"],
            counter_key="student.chat.stream.failure.count",
        )
        yield _sse("error", {"detail": str(exc)})
        return
    except asyncio.CancelledError:
        partial_reply = "".join(chunks).strip()
        if partial_reply:
            store.append_conversation_message(conversation, "assistant", partial_reply)
        raise

    reply = "".join(chunks).strip()
    if reply:
        store.append_conversation_message(conversation, "assistant", reply)
    store.record_audit(
        user.id,
        "student.chat.stream.success",
        "conversation",
        conversation.id,
        event_tags=["chat:model:qwen"],
        counter_key="student.chat.stream.success.count",
    )
    yield _sse("done", {"conversationId": conversation.id})


def _sse(event: str, data: dict[str, str]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
