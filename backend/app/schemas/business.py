"""Phase 1 business API schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str = Field(serialization_alias="displayName")
    role: str
    demo_account: bool = Field(serialization_alias="demoAccount")
    session_state: str = Field(serialization_alias="sessionState")


class LoginRequest(BaseModel):
    username: str
    password: str


class SSOCallbackRequest(BaseModel):
    provider: str = "campus-sso"
    code: str
    email: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    provider: str
    issued_at: datetime
    user: UserPublic


class ResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    summary: str
    category: str
    tags: list[str]
    source_knowledge_id: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    created_at: datetime
    resources: list[ResourceResponse] = Field(default_factory=list)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1)


class QuestionResponse(BaseModel):
    answer: str
    resources: list[ResourceResponse]


class ConversationCreate(BaseModel):
    title: str = "New conversation"
    message: str | None = None


class ConversationMessageCreate(BaseModel):
    content: str = Field(min_length=1)


class StudentChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("conversation_id", "conversationId"),
    )


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_id: str
    title: str
    messages: list[MessageResponse]
    created_at: datetime
    updated_at: datetime


class KnowledgeUpsert(BaseModel):
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    category: str = "general"
    tags: list[str] = Field(default_factory=list)
    status: str = "draft"


class KnowledgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    content: str
    category: str
    tags: list[str]
    status: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: str = Field(serialization_alias="actorId")
    actor_role: str = Field(serialization_alias="actorRole")
    action: str
    target_type: str = Field(serialization_alias="targetType")
    target_id: str = Field(serialization_alias="targetId")
    result: str
    event_tags: list[str] = Field(default_factory=list, serialization_alias="eventTags")
    counter_key: str | None = Field(default=None, serialization_alias="counterKey")
    created_at: datetime = Field(serialization_alias="createdAt")


class StatsResponse(BaseModel):
    users: int
    knowledge_items: int
    published_knowledge_items: int
    conversations: int
    messages: int
    audit_events: int


class CounselorAssistRequest(BaseModel):
    student_id: str | None = None
    concern: str = Field(min_length=1)
    context: str | None = None


class CounselorAssistResponse(BaseModel):
    suggested_response: str
    risk_level: str
    resources: list[ResourceResponse]
