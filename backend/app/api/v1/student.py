"""Student self-service routes for Q&A, resources, and conversations."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import current_user
from app.schemas.business import (
    ConversationCreate,
    ConversationMessageCreate,
    ConversationResponse,
    QuestionRequest,
    QuestionResponse,
    ResourceResponse,
)
from app.services.business import Conversation, User, store

router = APIRouter(prefix="/student", tags=["student"])


@router.post("/questions", response_model=QuestionResponse)
async def ask_question(
    payload: QuestionRequest,
    user: Annotated[User, Depends(current_user)],
) -> QuestionResponse:
    """Ask the counselor assistant a student-facing question."""
    message = store.answer_question(user.id, payload.question)
    return QuestionResponse(answer=message.content, resources=message.resources)


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
