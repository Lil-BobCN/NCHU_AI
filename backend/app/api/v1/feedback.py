from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import String, cast, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.responses import ok
from app.db.models import Admin, AnswerFeedback, ConversationMessage, RetrievalLog
from app.db.session import get_db


router = APIRouter(prefix="/feedback", tags=["feedback"])

ALLOWED_ERROR_TYPES = {
    "answer_wrong",
    "citation_wrong",
    "off_topic",
    "incomplete",
    "other",
}


class AnswerFeedbackCreate(BaseModel):
    assistant_message_id: str = Field(min_length=1)
    error_type: str = Field(min_length=1)
    description: str = Field(default="", max_length=1000)

    @field_validator("error_type")
    @classmethod
    def validate_error_type(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in ALLOWED_ERROR_TYPES:
            raise ValueError("unsupported feedback error type")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        return value.strip()


@router.post("/answers")
async def submit_answer_feedback(
    payload: AnswerFeedbackCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    assistant_message = await db.scalar(
        select(ConversationMessage).where(
            ConversationMessage.id == payload.assistant_message_id,
            ConversationMessage.role == "assistant",
        )
    )
    if assistant_message is None:
        raise HTTPException(status_code=404, detail="assistant message not found")

    user_message = await db.scalar(
        select(ConversationMessage)
        .where(
            ConversationMessage.conversation_id == assistant_message.conversation_id,
            ConversationMessage.role == "user",
            ConversationMessage.created_at <= assistant_message.created_at,
        )
        .order_by(ConversationMessage.created_at.desc())
        .limit(1)
    )
    retrieval_log = await db.scalar(
        select(RetrievalLog)
        .where(
            RetrievalLog.conversation_id == assistant_message.conversation_id,
            RetrievalLog.message_id == (user_message.id if user_message else None),
        )
        .order_by(RetrievalLog.created_at.desc())
        .limit(1)
    )
    existing = await db.scalar(
        select(AnswerFeedback).where(
            AnswerFeedback.assistant_message_id == assistant_message.id,
            AnswerFeedback.status == "open",
        )
    )
    now = datetime.now(timezone.utc)
    values = {
        "conversation_id": assistant_message.conversation_id,
        "user_message_id": user_message.id if user_message else None,
        "assistant_message_id": assistant_message.id,
        "retrieval_log_id": retrieval_log.id if retrieval_log else None,
        "error_type": payload.error_type,
        "description": payload.description,
        "question_snapshot": (user_message.content if user_message else "") or "",
        "answer_snapshot": assistant_message.content or "",
        "citations_snapshot": assistant_message.citations or [],
        "status": "open",
        "created_by": str(admin.id),
        "updated_at": now,
    }
    if existing:
        await db.execute(
            update(AnswerFeedback)
            .where(AnswerFeedback.id == existing.id)
            .values(**values)
        )
        feedback_id = existing.id
        created_at = existing.created_at
    else:
        feedback = AnswerFeedback(**values)
        db.add(feedback)
        await db.flush()
        feedback_id = feedback.id
        created_at = feedback.created_at

    if retrieval_log is not None:
        quality = dict(retrieval_log.answer_quality or {})
        quality["feedback"] = {
            "has_error": True,
            "error_type": payload.error_type,
            "description": payload.description,
            "feedback_id": str(feedback_id),
            "updated_at": now.isoformat(),
        }
        await db.execute(
            update(RetrievalLog)
            .where(RetrievalLog.id == retrieval_log.id)
            .values(answer_quality=quality)
        )

    await db.commit()
    open_count = await db.scalar(
        select(func.count())
        .select_from(AnswerFeedback)
        .where(
            cast(AnswerFeedback.conversation_id, String) == str(assistant_message.conversation_id),
            AnswerFeedback.status == "open",
        )
    )
    return ok(
        {
            "id": str(feedback_id),
            "conversation_id": str(assistant_message.conversation_id),
            "assistant_message_id": str(assistant_message.id),
            "user_message_id": str(user_message.id) if user_message else None,
            "retrieval_log_id": str(retrieval_log.id) if retrieval_log else None,
            "error_type": payload.error_type,
            "description": payload.description,
            "status": "open",
            "created_at": created_at.isoformat() if created_at else None,
            "conversation_feedback_count": int(open_count or 0),
        }
    )
