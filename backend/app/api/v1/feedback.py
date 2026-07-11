"""
回答反馈接口。记录用户对回答的纠错、问题类型、引用快照和处理状态。
"""

from datetime import datetime, timezone
from uuid import uuid4

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
            cast(ConversationMessage.id, String) == payload.assistant_message_id,
            ConversationMessage.role == "assistant",
        )
    )
    if assistant_message is None:
        raise HTTPException(status_code=404, detail="assistant message not found")

    user_message = await db.scalar(
        select(ConversationMessage)
        .where(
            cast(ConversationMessage.conversation_id, String) == str(assistant_message.conversation_id),
            ConversationMessage.role == "user",
            ConversationMessage.created_at <= assistant_message.created_at,
        )
        .order_by(ConversationMessage.created_at.desc())
        .limit(1)
    )
    retrieval_filters = [
        cast(RetrievalLog.conversation_id, String) == str(assistant_message.conversation_id),
    ]
    if user_message is not None:
        retrieval_filters.append(cast(RetrievalLog.message_id, String) == str(user_message.id))
    else:
        retrieval_filters.append(RetrievalLog.message_id.is_(None))
    retrieval_log = await db.scalar(
        select(RetrievalLog)
        .where(*retrieval_filters)
        .order_by(RetrievalLog.created_at.desc())
        .limit(1)
    )
    existing = await db.scalar(
        select(AnswerFeedback).where(
            _feedback_assistant_message_id_filter(assistant_message.id),
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
            .where(_feedback_id_filter(existing.id))
            .values(**values)
        )
        feedback_id = existing.id
        created_at = existing.created_at
    else:
        feedback = AnswerFeedback(id=str(uuid4()), **values)
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
            .where(_retrieval_log_id_filter(retrieval_log.id))
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


@router.post("/answers/{feedback_id}/cancel")
async def cancel_answer_feedback(
    feedback_id: str,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    feedback = await db.scalar(
        select(AnswerFeedback).where(
            _feedback_id_filter(feedback_id),
            AnswerFeedback.status == "open",
        )
    )
    if feedback is None:
        raise HTTPException(status_code=404, detail="open feedback not found")

    now = datetime.now(timezone.utc)
    await db.execute(
        update(AnswerFeedback)
        .where(_feedback_id_filter(feedback.id))
        .values(status="canceled", updated_at=now)
    )
    if feedback.retrieval_log_id:
        retrieval_log = await db.scalar(select(RetrievalLog).where(_retrieval_log_id_filter(feedback.retrieval_log_id)))
        if retrieval_log is not None:
            quality = dict(retrieval_log.answer_quality or {})
            existing_feedback = dict(quality.get("feedback") or {})
            existing_feedback.update(
                {
                    "has_error": False,
                    "status": "canceled",
                    "feedback_id": str(feedback.id),
                    "canceled_at": now.isoformat(),
                    "canceled_by": str(admin.id),
                }
            )
            quality["feedback"] = existing_feedback
            await db.execute(
                update(RetrievalLog)
                .where(_retrieval_log_id_filter(retrieval_log.id))
                .values(answer_quality=quality)
            )

    await db.commit()
    open_count = await db.scalar(
        select(func.count())
        .select_from(AnswerFeedback)
        .where(
            cast(AnswerFeedback.conversation_id, String) == str(feedback.conversation_id),
            AnswerFeedback.status == "open",
        )
    )
    return ok(
        {
            "id": str(feedback.id),
            "conversation_id": str(feedback.conversation_id),
            "assistant_message_id": str(feedback.assistant_message_id),
            "status": "canceled",
            "conversation_feedback_count": int(open_count or 0),
        }
    )


def _feedback_id_filter(feedback_id: str):
    return cast(AnswerFeedback.id, String) == str(feedback_id)


def _feedback_assistant_message_id_filter(assistant_message_id: str):
    return cast(AnswerFeedback.assistant_message_id, String) == str(assistant_message_id)


def _retrieval_log_id_filter(retrieval_log_id: str):
    return cast(RetrievalLog.id, String) == str(retrieval_log_id)
