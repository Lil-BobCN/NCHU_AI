from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import exists, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.responses import ok
from app.db.models import Admin, AnswerFeedback, Conversation, ConversationMessage
from app.db.session import get_db
from app.services.conversation_title import (
    DEFAULT_CONVERSATION_TITLE,
    auto_title_from_question,
    is_default_conversation_title,
    normalize_conversation_title,
    validate_manual_conversation_title,
)


router = APIRouter(prefix="/conversations", tags=["conversations"])


class ConversationCreate(BaseModel):
    title: str = DEFAULT_CONVERSATION_TITLE


class ConversationUpdate(BaseModel):
    title: str


@router.post("")
async def create_conversation(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    conversation = Conversation(title=normalize_conversation_title(payload.title), created_by=str(admin.id))
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return ok(serialize_conversation(conversation))


@router.get("")
async def list_conversations(
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    feedback_only: bool = False,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    filters = conversation_list_filters(q, feedback_only)
    total = await db.scalar(select(func.count()).select_from(Conversation).where(*filters))
    rows = await db.execute(
        select(Conversation)
        .where(*filters)
        .order_by(Conversation.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    conversations = list(rows.scalars())
    await backfill_default_conversation_titles(db, conversations)
    feedback_counts = await open_feedback_counts(db, [str(item.id) for item in conversations])
    return ok(
        {
            "items": [serialize_conversation(item, feedback_counts.get(str(item.id), 0)) for item in conversations],
            "page": page,
            "page_size": page_size,
            "total": total or 0,
        }
    )


@router.get("/{conversation_id}/messages")
async def list_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    # 加载当前会话的完整反馈历史，让消息列表可以用用户上次提交的内容预填反馈表单。
    # 只有有效反馈记录才表示该消息当前处于“已标记有误”的有效状态。
    feedback_history_rows = await db.execute(
        select(AnswerFeedback)
        .where(AnswerFeedback.conversation_id == conversation_id)
        .order_by(AnswerFeedback.created_at.asc(), AnswerFeedback.updated_at.asc())
    )
    feedback_by_message = {}
    for feedback in feedback_history_rows.scalars():
        message_feedback = {
            "feedback_error_type": feedback.error_type,
            "feedback_description": feedback.description,
        }
        if feedback.status == "open":
            message_feedback["feedback_status"] = feedback.status
        feedback_by_message[str(feedback.assistant_message_id)] = message_feedback
    rows = await db.execute(
        select(ConversationMessage)
        .where(*conversation_message_list_filters(conversation_id))
        .order_by(ConversationMessage.created_at.asc())
    )
    return ok([serialize_message(item, feedback_by_message.get(str(item.id))) for item in rows.scalars()])


@router.delete("/{conversation_id}/messages/{message_id}")
async def delete_message(
    conversation_id: str,
    message_id: str,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    conversation = await db.scalar(
        select(Conversation.id).where(Conversation.id == conversation_id, Conversation.deleted_at.is_(None))
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    message = await db.scalar(
        select(ConversationMessage).where(*conversation_message_delete_filters(conversation_id, message_id))
    )
    if message is None:
        raise HTTPException(status_code=404, detail="消息不存在或不支持删除")

    now = datetime.now(timezone.utc)
    # 对消息执行软删除：普通会话接口会隐藏它，但数据库行保留删除时间和删除人，
    # 后台审计视图仍可查看这次删除动作。
    message.deleted_at = now
    message.deleted_by = str(admin.id)
    await db.flush()

    # 会话计数只描述前端可见的聊天时间线。
    # 软删除后重新计算，确保侧边栏数量与页面展示保持一致。
    visible_count = await db.scalar(
        select(func.count())
        .select_from(ConversationMessage)
        .where(*conversation_message_list_filters(conversation_id))
    )
    last_message_at = await db.scalar(
        select(func.max(ConversationMessage.created_at)).where(*conversation_message_list_filters(conversation_id))
    )
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id, Conversation.deleted_at.is_(None))
        .values(
            message_count=int(visible_count or 0),
            last_message_at=last_message_at,
            updated_at=now,
        )
    )
    await db.commit()
    return ok(
        {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "deleted_at": now.isoformat(),
            "deleted_by": str(admin.id),
            "message_count": int(visible_count or 0),
            "last_message_at": last_message_at.isoformat() if last_message_at else None,
        }
    )


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    try:
        title = validate_manual_conversation_title(payload.title)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    conversation = await db.scalar(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.deleted_at.is_(None))
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    now = datetime.now(timezone.utc)
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(title=title, updated_at=now)
    )
    await db.commit()
    conversation.title = title
    conversation.updated_at = now
    return ok(serialize_conversation(conversation))


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    conversation = await db.scalar(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.deleted_at.is_(None))
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(deleted_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return ok({"id": conversation_id})


def serialize_conversation(item: Conversation, open_feedback_count: int = 0) -> dict:
    return {
        "id": str(item.id),
        "title": item.title,
        "summary": item.summary,
        "context_state": item.context_state,
        "message_count": item.message_count,
        "last_message_at": item.last_message_at.isoformat() if item.last_message_at else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "open_feedback_count": open_feedback_count,
        "has_feedback": open_feedback_count > 0,
    }


async def open_feedback_counts(db: AsyncSession, conversation_ids: list[str]) -> dict[str, int]:
    if not conversation_ids:
        return {}
    rows = await db.execute(
        select(AnswerFeedback.conversation_id, func.count().label("count"))
        .where(
            AnswerFeedback.conversation_id.in_(conversation_ids),
            AnswerFeedback.status == "open",
        )
        .group_by(AnswerFeedback.conversation_id)
    )
    return {str(row.conversation_id): int(row.count or 0) for row in rows}


def conversation_list_filters(search: str | None = None, feedback_only: bool = False) -> list:
    filters = [Conversation.deleted_at.is_(None)]
    if feedback_only:
        filters.append(
            exists(
                select(AnswerFeedback.id).where(
                    AnswerFeedback.conversation_id == Conversation.id,
                    AnswerFeedback.status == "open",
                )
            )
        )
    keyword = normalize_conversation_search_query(search)
    if not keyword:
        return filters
    pattern = f"%{keyword}%"
    filters.append(
        or_(
            Conversation.title.ilike(pattern),
            Conversation.summary.ilike(pattern),
            exists(
                select(ConversationMessage.id).where(
                    ConversationMessage.conversation_id == Conversation.id,
                    ConversationMessage.deleted_at.is_(None),
                    ConversationMessage.content.ilike(pattern),
                )
            ),
        )
    )
    return filters


def conversation_message_list_filters(conversation_id: str) -> list:
    # 普通聊天历史隐藏软删除消息；数据库行仍保留删除时间和删除人，
    # 供后台审计检查。
    return [
        ConversationMessage.conversation_id == conversation_id,
        ConversationMessage.deleted_at.is_(None),
    ]


def conversation_message_delete_filters(conversation_id: str, message_id: str) -> list:
    return [
        ConversationMessage.id == message_id,
        ConversationMessage.conversation_id == conversation_id,
        ConversationMessage.role.in_(("user", "assistant")),
        ConversationMessage.deleted_at.is_(None),
    ]


def normalize_conversation_search_query(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())[:100]


async def backfill_default_conversation_titles(db: AsyncSession, conversations: list[Conversation]) -> None:
    changed = False
    for conversation in conversations:
        if not is_default_conversation_title(conversation.title):
            continue
        first_question = await db.scalar(
            select(ConversationMessage.content)
            .where(
                ConversationMessage.conversation_id == conversation.id,
                ConversationMessage.role == "user",
                ConversationMessage.deleted_at.is_(None),
            )
            .order_by(ConversationMessage.created_at.asc())
            .limit(1)
        )
        title = auto_title_from_question(first_question or "")
        if title == DEFAULT_CONVERSATION_TITLE:
            continue
        conversation.title = title
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation.id)
            .values(title=title)
        )
        changed = True
    if changed:
        await db.commit()


def serialize_message(item: ConversationMessage, feedback: dict | None = None) -> dict:
    data = {
        "id": str(item.id),
        "conversation_id": str(item.conversation_id),
        "role": item.role,
        "content": item.content,
        # 用户消息如果带引用，需要把引用编号和快照一并返回，前端才能在历史气泡里还原引用卡片。
        "quoted_message_id": str(item.quoted_message_id) if item.quoted_message_id else None,
        "quoted_message_content": item.quoted_message_content or "",
        "rewritten_query": item.rewritten_query,
        "retrieval_trace": item.retrieval_trace,
        "citations": item.citations,
        "suggested_questions": item.suggested_questions,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "deleted_at": item.deleted_at.isoformat() if item.deleted_at else None,
        "deleted_by": str(item.deleted_by) if item.deleted_by else None,
    }
    if feedback:
        data.update(feedback)
    return data
