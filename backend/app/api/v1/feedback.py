from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select, update
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


def answer_feedback_cancel_filters(assistant_message_id: str, conversation_id: str | None = None) -> list:
    # 客户端传入会话时，取消操作必须按会话收窄范围。
    # 即使旧弹窗仍停留在页面上，同一个消息编号也不能取消其他会话里的有效反馈记录。
    filters = [
        AnswerFeedback.assistant_message_id == assistant_message_id,
        AnswerFeedback.status == "open",
    ]
    if conversation_id:
        filters.append(AnswerFeedback.conversation_id == conversation_id)
    return filters


class AnswerFeedbackCreate(BaseModel):
    # 反馈属于按会话划分的审计链路，请求必须携带当前会话编号，不能只依赖消息编号。
    conversation_id: str = Field(min_length=1)
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
    # 写入反馈前先确认目标回答属于本次提交的会话，
    # 避免前端旧状态把其他会话里的消息标记为“回答有误”。
    assistant_message = await db.scalar(
        select(ConversationMessage).where(
            ConversationMessage.id == payload.assistant_message_id,
            ConversationMessage.conversation_id == payload.conversation_id,
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
    # 重复提交有效反馈时只编辑当前有效记录。
    # 已取消记录刻意保持不变，以便审计历史保留每一次提交/取消动作。
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
        # 回答质量里的反馈字段仅镜像当前有效反馈状态，供检索/调试视图查看。
        # 持久审计来源仍然是回答反馈表，已取消记录会保留在那里。
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
            AnswerFeedback.conversation_id == assistant_message.conversation_id,
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


@router.patch("/answers/{assistant_message_id}/cancel")
async def cancel_answer_feedback(
    assistant_message_id: str,
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    # 只取消同一回答、同一会话下的有效反馈。
    # 这样反馈状态可以反向切换，同时不会物理删除原始回答反馈行。
    feedback = await db.scalar(
        select(AnswerFeedback).where(*answer_feedback_cancel_filters(assistant_message_id, conversation_id))
    )
    if feedback is None:
        raise HTTPException(status_code=404, detail="open feedback not found")

    now = datetime.now(timezone.utc)
    # 为满足审计要求采用软取消：前端不再把它视为有效反馈，
    # 后端仍记录取消人和取消时间。
    feedback.status = "canceled"
    feedback.canceled_at = now
    feedback.canceled_by = str(admin.id)
    feedback.updated_at = now

    if feedback.retrieval_log_id:
        retrieval_log = await db.scalar(select(RetrievalLog).where(RetrievalLog.id == feedback.retrieval_log_id))
        if retrieval_log is not None:
            quality = dict(retrieval_log.answer_quality or {})
            previous = dict(quality.get("feedback") or {})
            previous.update(
                {
                    "has_error": False,
                    "status": "canceled",
                    "feedback_id": str(feedback.id),
                    "canceled_at": now.isoformat(),
                    "canceled_by": str(admin.id),
                }
            )
            quality["feedback"] = previous
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
            AnswerFeedback.conversation_id == feedback.conversation_id,
            AnswerFeedback.status == "open",
        )
    )
    return ok(
        {
            "id": str(feedback.id),
            "conversation_id": str(feedback.conversation_id),
            "assistant_message_id": str(feedback.assistant_message_id),
            "error_type": feedback.error_type,
            "description": feedback.description,
            "status": "canceled",
            "canceled_at": now.isoformat(),
            "canceled_by": str(admin.id),
            "conversation_feedback_count": int(open_count or 0),
        }
    )
