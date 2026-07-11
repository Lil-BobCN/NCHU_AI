"""
普通问答接口。提供流式问答、非流式问答和撤回一轮问答的 HTTP 入口。
"""

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.concurrency import release_chat_slot, try_acquire_chat_slot
from app.core.config import get_settings
from app.core.responses import ok
from app.db.models import Admin
from app.db.session import get_db
from app.services.chat_service import ChatService


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    question: str = Field(min_length=1)
    top_k: int = Field(default=8, ge=1)
    rerank_top_k: int = Field(default=5, ge=1)
    document_ids: list[str] | None = None
    enable_rewrite: bool = True
    enable_suggested_questions: bool = True

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        settings = get_settings()
        value = value.strip()
        if len(value) > settings.chat_max_question_chars:
            raise ValueError(f"问题长度不能超过 {settings.chat_max_question_chars} 字符")
        return value

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, value: int) -> int:
        settings = get_settings()
        if value > settings.chat_max_top_k:
            raise ValueError(f"top_k 不能超过 {settings.chat_max_top_k}")
        return value

    @field_validator("rerank_top_k")
    @classmethod
    def validate_rerank_top_k(cls, value: int) -> int:
        settings = get_settings()
        if value > settings.chat_max_rerank_top_k:
            raise ValueError(f"rerank_top_k 不能超过 {settings.chat_max_rerank_top_k}")
        return value


class ChatRetractRequest(BaseModel):
    conversation_id: str = Field(min_length=1)
    user_message_id: str = Field(min_length=1)
    assistant_message_id: str = Field(min_length=1)


async def _limited_stream(generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    try:
        async for chunk in generator:
            yield chunk
    finally:
        release_chat_slot()


@router.post("/stream")
async def stream_chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    if not await try_acquire_chat_slot():
        raise HTTPException(status_code=429, detail="当前问答请求较多，请稍后再试")
    service = ChatService()
    return StreamingResponse(
        _limited_stream(
            service.stream_chat(
                db,
                payload.question,
                payload.conversation_id,
                payload.enable_suggested_questions,
                payload.top_k,
                payload.rerank_top_k,
                payload.document_ids,
                payload.enable_rewrite,
            )
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/retract")
async def retract_chat_turn(
    payload: ChatRetractRequest,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    result = await ChatService().retract_turn(
        db,
        payload.conversation_id,
        payload.user_message_id,
        payload.assistant_message_id,
    )
    return ok(result)


@router.post("")
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    if not await try_acquire_chat_slot():
        raise HTTPException(status_code=429, detail="当前问答请求较多，请稍后再试")
    try:
        result = await ChatService().chat_once(
            db,
            payload.question,
            payload.conversation_id,
            payload.enable_suggested_questions,
            payload.top_k,
            payload.rerank_top_k,
            payload.document_ids,
            payload.enable_rewrite,
        )
        return ok(result)
    finally:
        release_chat_slot()
