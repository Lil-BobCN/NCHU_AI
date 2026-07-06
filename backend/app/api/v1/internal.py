from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import String, and_, cast, false, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user_from_sa_token
from app.core.config import get_settings
from app.core.responses import ok
from app.db.models import AnswerFeedback, Conversation, ConversationMessage, Document, DocumentJob
from app.db.session import get_db
from app.services.chat_service import ChatService
from app.services.conversation_title import normalize_conversation_title, validate_manual_conversation_title
from app.services.document_lifecycle_service import DocumentLifecycleService
from app.services.document_pipeline import supported_file
from app.services.task_queue_service import TaskQueueService


router = APIRouter(tags=["internal-rag"], dependencies=[Depends(get_current_user_from_sa_token)])


class UserContext(BaseModel):
    user_id: str = Field(min_length=1)
    dept_id: str | None = None
    role_codes: list[str] = Field(default_factory=list)
    data_scope: str | None = None


class AccessScope(BaseModel):
    scope_mode: str = Field(default="dept")
    allowed_dept_ids: list[str] = Field(default_factory=list)
    allowed_knowledge_ids: list[str] = Field(default_factory=list)
    allowed_attach_ids: list[int] = Field(default_factory=list)
    deny_attach_ids: list[int] = Field(default_factory=list)

    @field_validator("scope_mode")
    @classmethod
    def validate_scope_mode(cls, value: str) -> str:
        value = (value or "").strip()
        allowed = {"dept", "all_public", "custom", "admin_all"}
        if value not in allowed:
            raise ValueError(f"scope_mode 只能是 {', '.join(sorted(allowed))}")
        return value


class DocumentProcessRequest(BaseModel):
    attach_id: int = Field(gt=0)
    knowledge_id: str = Field(default="default", min_length=1, max_length=128)
    doc_id: str | None = Field(default=None, max_length=128)
    publish_dept_id: str | None = Field(default=None, max_length=128)
    owner_user_id: str | None = Field(default=None, max_length=128)
    visible_in_chat: bool = True
    publish_scope: str = Field(default="dept", max_length=32)
    allowed_dept_ids: list[str] = Field(default_factory=list)
    allowed_user_ids: list[str] = Field(default_factory=list)
    file_name: str = Field(min_length=1, max_length=255)
    file_ext: str | None = Field(default=None, max_length=32)
    mime_type: str | None = Field(default=None, max_length=128)
    file_size: int = Field(ge=0)
    file_hash: str = Field(min_length=1, max_length=128)
    bucket: str = Field(min_length=1, max_length=128)
    object_key: str = Field(min_length=1, max_length=512)
    operator_id: str | None = Field(default=None, max_length=128)
    auto_process: bool = True
    force: bool = False

    @field_validator("publish_scope")
    @classmethod
    def validate_publish_scope(cls, value: str) -> str:
        value = (value or "").strip() or "dept"
        allowed = {"public", "dept", "private", "custom"}
        if value not in allowed:
            raise ValueError(f"publish_scope 只能是 {', '.join(sorted(allowed))}")
        return value


class ReprocessRequest(BaseModel):
    operator_id: str | None = Field(default=None, max_length=128)
    force: bool = True


class RechunkRequest(BaseModel):
    operator_id: str | None = Field(default=None, max_length=128)
    chunk_config: dict | None = None


class DeleteDocumentRequest(BaseModel):
    operator_id: str | None = Field(default=None, max_length=128)
    reason: str = Field(default="document_deleted", max_length=128)


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    created_by: str | None = Field(default=None, max_length=128)


class ConversationUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class ChatOptions(BaseModel):
    top_k: int = Field(default=8, ge=1, le=50)
    rerank_top_k: int = Field(default=5, ge=1, le=20)
    enable_rewrite: bool = True
    enable_suggested_questions: bool = True


class InternalChatRequest(BaseModel):
    session_id: str | None = None
    message_id: str | None = None
    question: str = Field(min_length=1)
    user_context: UserContext
    access_scope: AccessScope
    options: ChatOptions = Field(default_factory=ChatOptions)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        settings = get_settings()
        value = value.strip()
        if len(value) > settings.chat_max_question_chars:
            raise ValueError(f"问题长度不能超过 {settings.chat_max_question_chars} 字符")
        return value


class InternalChatRetractRequest(BaseModel):
    session_id: str | None = None
    conversation_id: str | None = None
    user_message_id: str = Field(min_length=1)
    assistant_message_id: str = Field(min_length=1)


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    return ok({"status": "ok", "name": settings.app_name})


@router.get("/documents/{attach_id}")
async def get_document_status(attach_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    document = await _get_document_by_attach_id(db, attach_id)
    return ok(
        {
            "attach_id": attach_id,
            "rag_doc_id": str(document.id),
            "status": document.status,
            "file_name": document.file_name,
            "knowledge_base": document.knowledge_base,
            "error_message": document.error_message,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
        }
    )


@router.post("/documents/process")
async def process_document(payload: DocumentProcessRequest, db: AsyncSession = Depends(get_db)) -> dict:
    if not supported_file(payload.file_name):
        raise HTTPException(status_code=415, detail="不支持的文件类型")
    document = await _upsert_java_document(db, payload)
    jobs = []
    if payload.auto_process:
        job = await _enqueue_document_job(
            db,
            document,
            "document_full_pipeline",
            {"document_id": str(document.id), "attach_id": payload.attach_id},
        )
        jobs.append({"job_id": str(job.id), "status": job.status})
    return ok({"attach_id": payload.attach_id, "rag_doc_id": str(document.id), "status": document.status, "jobs": jobs})


@router.post("/documents/{attach_id}/reparse")
async def reparse_document(attach_id: int, _: ReprocessRequest, db: AsyncSession = Depends(get_db)) -> dict:
    document = await _get_document_by_attach_id(db, attach_id)
    job = await _enqueue_document_job(
        db,
        document,
        "document_full_pipeline",
        {"document_id": str(document.id), "attach_id": attach_id},
    )
    return ok({"attach_id": attach_id, "rag_doc_id": str(document.id), "job_id": str(job.id), "status": job.status})


@router.post("/documents/{attach_id}/rechunk")
async def rechunk_document(attach_id: int, _: RechunkRequest, db: AsyncSession = Depends(get_db)) -> dict:
    document = await _get_document_by_attach_id(db, attach_id)
    job = await _enqueue_document_job(
        db,
        document,
        "document_rechunk",
        {"document_id": str(document.id), "attach_id": attach_id},
    )
    return ok({"attach_id": attach_id, "rag_doc_id": str(document.id), "job_id": str(job.id), "status": job.status})


@router.delete("/documents/{attach_id}")
async def delete_document_index(attach_id: int, payload: DeleteDocumentRequest, db: AsyncSession = Depends(get_db)) -> dict:
    document = await _get_document_by_attach_id(db, attach_id)
    await DocumentLifecycleService().soft_delete_document(db, document, reason=payload.reason)
    await db.commit()
    return ok({"attach_id": attach_id, "rag_doc_id": str(document.id), "status": "deleted"})


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    job_id = _normalize_uuid(job_id, "job_id")
    job = await db.scalar(select(DocumentJob).where(DocumentJob.id == job_id))
    if job is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return ok(_serialize_job(job))


@router.post("/conversations")
async def create_conversation(
    payload: ConversationCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_from_sa_token),
) -> dict:
    # 优先使用请求体中的 created_by，否则取当前登录用户
    created_by = payload.created_by or current_user.user_id
    owner_id = _conversation_owner_id(current_user)
    conversation = Conversation(
        title=normalize_conversation_title(payload.title),
        created_by=owner_id,
        context_state={"created_by": created_by, "owner_id": owner_id},
        message_count=0,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return ok(_serialize_conversation(conversation))


@router.get("/conversations")
async def list_conversations(
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    feedback_only: bool = False,
    created_by: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_from_sa_token),
) -> dict:
    page = max(1, int(page or 1))
    page_size = min(100, max(1, int(page_size or 20)))
    # /internal/rag/ 内部接口，由 Java 后端调用，Java 层已负责用户身份与权限控制
    # 此处仅根据 Java 传入的 created_by 参数做数据过滤，不再重复校验用户所有权
    # 不传 created_by 时，不做用户级过滤（后管需要返回全部数据）
    filters = _conversation_filters(
        q,
        feedback_only,
        created_by,                                                           # 仅当显式传入时才过滤
        _conversation_owner_id(current_user) if created_by else None,          # 仅当显式传入时才过滤
    )
    total = await db.scalar(select(func.count()).select_from(Conversation).where(*filters))
    rows = await db.execute(
        select(Conversation)
        .where(*filters)
        .order_by(Conversation.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    conversations = list(rows.scalars())
    feedback_counts = await _open_feedback_counts(db, [str(item.id) for item in conversations])
    return ok(
        {
            "total": int(total or 0),
            "page": page,
            "page_size": page_size,
            "items": [
                _serialize_conversation(item, feedback_counts.get(str(item.id), 0))
                for item in conversations
            ],
        }
    )


@router.get("/conversations/{conversation_id}/messages")
async def list_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_from_sa_token),
) -> dict:
    conversation_id = _normalize_uuid(conversation_id, "conversation_id")
    conversation = await _get_conversation(db, conversation_id)
    feedback_rows = await db.execute(
        select(AnswerFeedback).where(
            _feedback_conversation_id() == str(conversation_id),
            AnswerFeedback.status == "open",
        )
    )
    feedback_by_message = {str(item.assistant_message_id): item for item in feedback_rows.scalars()}
    rows = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.asc())
    )
    return ok([_serialize_message(item, feedback_by_message.get(str(item.id))) for item in rows.scalars()])


@router.patch("/conversations/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_from_sa_token),
) -> dict:
    conversation_id = _normalize_uuid(conversation_id, "conversation_id")
    try:
        title = validate_manual_conversation_title(payload.title)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    conversation = await _get_conversation(db, conversation_id)
    if not _can_access_conversation(conversation, current_user):
        raise HTTPException(status_code=403, detail="无权修改此会话")
    now = datetime.now(timezone.utc)
    await db.execute(update(Conversation).where(Conversation.id == conversation_id).values(title=title, updated_at=now))
    await db.commit()
    conversation.title = title
    conversation.updated_at = now
    return ok({"id": str(conversation.id), "title": conversation.title, "updated_at": now.isoformat()})


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_from_sa_token),
) -> dict:
    conversation_id = _normalize_uuid(conversation_id, "conversation_id")
    conversation = await _get_conversation(db, conversation_id)
    if not _can_access_conversation(conversation, current_user):
        raise HTTPException(status_code=403, detail="无权删除此会话")
    await db.execute(
        update(Conversation)
        .where(Conversation.id == conversation_id)
        .values(deleted_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return ok({"id": conversation_id, "status": "deleted"})


@router.post("/chat/stream")
async def stream_chat(
    payload: InternalChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_from_sa_token),
) -> StreamingResponse:
    document_ids = await _allowed_document_ids(db, payload.access_scope, payload.user_context)
    conversation_id = _java_session_to_uuid(payload.session_id)
    service = ChatService()
    return StreamingResponse(
        _stream_with_java_boundary(
            service.stream_chat(
                db=db,
                question=payload.question,
                conversation_id=conversation_id,
                enable_suggested_questions=payload.options.enable_suggested_questions,
                top_k=payload.options.top_k,
                rerank_top_k=payload.options.rerank_top_k,
                document_ids=document_ids,
                enable_rewrite=payload.options.enable_rewrite,
                created_by=_conversation_owner_id(current_user),
                context_created_by=current_user.user_id,
            )
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache, no-transform", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.post("/chat")
async def chat(
    payload: InternalChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_from_sa_token),
) -> dict:
    document_ids = await _allowed_document_ids(db, payload.access_scope, payload.user_context)
    conversation_id = _java_session_to_uuid(payload.session_id)
    result = await ChatService().chat_once(
        db=db,
        question=payload.question,
        conversation_id=conversation_id,
        enable_suggested_questions=payload.options.enable_suggested_questions,
        top_k=payload.options.top_k,
        rerank_top_k=payload.options.rerank_top_k,
        document_ids=document_ids,
        enable_rewrite=payload.options.enable_rewrite,
        created_by=_conversation_owner_id(current_user),
        context_created_by=current_user.user_id,
    )
    return ok(result)


@router.post("/chat/retract")
async def retract_chat_turn(payload: InternalChatRetractRequest, db: AsyncSession = Depends(get_db)) -> dict:
    conversation_id = payload.conversation_id or _java_session_to_uuid(payload.session_id)
    if not conversation_id:
        raise HTTPException(status_code=422, detail="conversation_id 或 session_id 不能为空")
    conversation_id = _normalize_uuid(conversation_id, "conversation_id")
    result = await ChatService().retract_turn(
        db,
        conversation_id,
        payload.user_message_id,
        payload.assistant_message_id,
    )
    return ok(result)


async def _stream_with_java_boundary(generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    async for chunk in generator:
        yield chunk


async def _upsert_java_document(db: AsyncSession, payload: DocumentProcessRequest) -> Document:
    existing = await db.scalar(select(Document).where(Document.java_attach_id == payload.attach_id))
    ext = (payload.file_ext or Path(payload.file_name).suffix or "").lower()
    status = "uploaded"
    if existing is not None and not payload.auto_process:
        content_changed = any(
            [
                existing.file_hash != payload.file_hash,
                existing.storage_bucket != payload.bucket,
                existing.storage_object_key != payload.object_key,
                existing.file_name != payload.file_name,
                existing.file_size != payload.file_size,
            ]
        )
        status = "uploaded" if content_changed else existing.status
    values = {
        "java_attach_id": payload.attach_id,
        "java_doc_id": payload.doc_id,
        "publish_dept_id": payload.publish_dept_id,
        "owner_user_id": payload.owner_user_id or payload.operator_id,
        "visible_in_chat": payload.visible_in_chat,
        "publish_scope": payload.publish_scope,
        "allowed_dept_ids": _clean_list(payload.allowed_dept_ids),
        "allowed_user_ids": _clean_list(payload.allowed_user_ids),
        "title": payload.file_name,
        "file_name": payload.file_name,
        "file_ext": ext,
        "mime_type": payload.mime_type,
        "file_size": payload.file_size,
        "file_hash": payload.file_hash,
        "storage_bucket": payload.bucket,
        "storage_object_key": payload.object_key,
        "knowledge_base": payload.knowledge_id,
        "status": status,
        "created_by": None,
        "deleted_at": None,
    }
    if existing:
        await db.execute(update(Document).where(Document.id == existing.id).values(**values))
        await db.commit()
        refreshed = await db.scalar(select(Document).where(Document.id == existing.id))
        if refreshed is None:
            raise HTTPException(status_code=500, detail="文档更新失败")
        return refreshed
    document = Document(**values)
    db.add(document)
    await db.commit()
    await db.refresh(document)
    return document


async def _enqueue_document_job(db: AsyncSession, document: Document, job_type: str, payload: dict) -> DocumentJob:
    job = DocumentJob(
        document_id=str(document.id),
        job_type=job_type,
        status="pending",
        progress=0,
        message="已加入处理队列",
        params={"source": "java_internal", **payload},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    await TaskQueueService().enqueue(job_type, {**payload, "job_id": str(job.id)})
    return job


async def _get_document_by_attach_id(db: AsyncSession, attach_id: int) -> Document:
    document = await db.scalar(select(Document).where(Document.java_attach_id == attach_id, Document.deleted_at.is_(None)))
    if document is None:
        raise HTTPException(status_code=404, detail="RAG 文档不存在")
    return document


async def _get_conversation(db: AsyncSession, conversation_id: str) -> Conversation:
    conversation = await db.scalar(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.deleted_at.is_(None))
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conversation


async def _allowed_document_ids(db: AsyncSession, scope: AccessScope, user: UserContext) -> list[str]:
    query = select(Document.id).where(Document.deleted_at.is_(None), Document.visible_in_chat.is_(True), Document.status == "indexed")
    if scope.scope_mode == "admin_all":
        pass
    elif scope.scope_mode == "all_public":
        query = query.where(Document.publish_scope == "public")
    elif scope.scope_mode == "dept":
        if not scope.allowed_dept_ids:
            raise HTTPException(status_code=403, detail="部门权限范围为空，拒绝检索")
        query = query.where(_document_access_condition(user, scope, allow_explicit_attach=False))
    elif scope.scope_mode == "custom":
        if not scope.allowed_dept_ids and not scope.allowed_knowledge_ids and not scope.allowed_attach_ids:
            raise HTTPException(status_code=403, detail="自定义权限范围为空，拒绝检索")
        query = query.where(_document_access_condition(user, scope, allow_explicit_attach=True))
    if scope.allowed_knowledge_ids:
        query = query.where(Document.knowledge_base.in_(scope.allowed_knowledge_ids))
    if scope.allowed_attach_ids and scope.scope_mode != "custom":
        query = query.where(Document.java_attach_id.in_(scope.allowed_attach_ids))
    if scope.deny_attach_ids:
        query = query.where(~Document.java_attach_id.in_(scope.deny_attach_ids))
    rows = await db.execute(query)
    ids = [str(item) for item in rows.scalars()]
    if not ids:
        raise HTTPException(status_code=403, detail="当前用户没有可检索的知识库资料")
    return ids


def _document_access_condition(user: UserContext, scope: AccessScope, allow_explicit_attach: bool):
    user_id = str(user.user_id)
    allowed_dept_ids = _clean_list(scope.allowed_dept_ids)
    allowed_attach_ids = list(scope.allowed_attach_ids or [])
    dept_conditions = []
    if allowed_dept_ids:
        dept_conditions.extend(
            [
                Document.publish_dept_id.in_(allowed_dept_ids),
                Document.allowed_dept_ids.overlap(allowed_dept_ids),
            ]
        )
    explicit_attach_condition = (
        Document.java_attach_id.in_(allowed_attach_ids)
        if allow_explicit_attach and allowed_attach_ids
        else false()
    )
    return or_(
        Document.publish_scope == "public",
        explicit_attach_condition,
        and_(Document.publish_scope == "dept", or_(*dept_conditions)) if dept_conditions else false(),
        and_(Document.publish_scope == "private", Document.owner_user_id == user_id),
        and_(
            Document.publish_scope == "custom",
            or_(
                Document.owner_user_id == user_id,
                Document.allowed_user_ids.any(user_id),
                *(dept_conditions or [false()]),
            ),
        ),
    )


def _conversation_filters(
    search: str | None = None,
    feedback_only: bool = False,
    created_by: str | None = None,
    owner_id: str | None = None,
) -> list:
    """构建会话列表查询过滤条件。

    不做用户级强制过滤：
    - 后管（Java admin controller）不传 created_by / owner_id，返回全部数据。
    - 前端 Chat 页面显式传入 created_by（current_user.user_id），实现数据隔离。
    """
    filters = [Conversation.deleted_at.is_(None)]
    owner_filters = []
    if created_by:
        owner_filters.append(Conversation.context_state["created_by"].as_string() == str(created_by))
        try:
            owner_filters.append(Conversation.created_by == str(UUID(str(created_by))))
        except ValueError:
            pass
    if owner_id:
        owner_filters.extend(
            [
                Conversation.created_by == owner_id,
                Conversation.context_state["owner_id"].as_string() == owner_id,
            ]
        )
    if owner_filters:
        filters.append(or_(*owner_filters))
    if feedback_only:
        filters.append(
            select(AnswerFeedback.id)
            .where(
                _feedback_conversation_id() == cast(Conversation.id, String),
                AnswerFeedback.status == "open",
            )
            .exists()
        )
    keyword = " ".join(str(search or "").strip().split())[:100]
    if keyword:
        pattern = f"%{keyword}%"
        filters.append(
            or_(
                Conversation.title.ilike(pattern),
                Conversation.summary.ilike(pattern),
                select(ConversationMessage.id)
                .where(ConversationMessage.conversation_id == Conversation.id, ConversationMessage.content.ilike(pattern))
                .exists(),
            )
        )
    return filters


async def _open_feedback_counts(db: AsyncSession, conversation_ids: list[str]) -> dict[str, int]:
    if not conversation_ids:
        return {}
    rows = await db.execute(
        select(AnswerFeedback.conversation_id, func.count().label("count"))
        .where(_feedback_conversation_id().in_([str(item) for item in conversation_ids]), AnswerFeedback.status == "open")
        .group_by(AnswerFeedback.conversation_id)
    )
    return {str(row.conversation_id): int(row.count or 0) for row in rows}


def _feedback_conversation_id():
    return cast(AnswerFeedback.conversation_id, String)


def _can_access_conversation(conversation: Conversation, current_user: CurrentUser) -> bool:
    owner_id = _conversation_owner_id(current_user)
    if not conversation.created_by or conversation.created_by == owner_id:
        return True
    context_state = conversation.context_state or {}
    return context_state.get("owner_id") == owner_id or context_state.get("created_by") in {
        current_user.user_id,
        current_user.login_id,
        owner_id,
    }


def _conversation_owner_id(current_user: CurrentUser) -> str:
    return current_user.id


def _serialize_conversation(item: Conversation, open_feedback_count: int = 0) -> dict:
    return {
        "id": str(item.id),
        "title": item.title,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        "message_count": item.message_count,
        "last_message_at": item.last_message_at.isoformat() if item.last_message_at else None,
        "has_feedback": open_feedback_count > 0,
        "open_feedback_count": open_feedback_count,
    }


def _serialize_message(item: ConversationMessage, feedback: AnswerFeedback | None = None) -> dict:
    return {
        "id": str(item.id),
        "conversation_id": str(item.conversation_id),
        "role": item.role,
        "content": item.content,
        "rewritten_query": item.rewritten_query,
        "retrieval_trace": item.retrieval_trace,
        "citations": item.citations,
        "suggested_questions": item.suggested_questions,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "feedback": _serialize_feedback(feedback) if item.role == "assistant" and feedback else None,
    }


def _serialize_feedback(item: AnswerFeedback | None) -> dict | None:
    if item is None:
        return None
    return {
        "id": str(item.id),
        "error_type": item.error_type,
        "description": item.description,
        "status": item.status,
    }


def _serialize_job(job: DocumentJob) -> dict:
    return {
        "job_id": str(job.id),
        "rag_doc_id": str(job.document_id),
        "job_type": job.job_type,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "error_message": job.error_message,
        "result": job.result,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


def _clean_list(values: list[str] | None) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        item = str(value).strip()
        if item and item not in seen:
            cleaned.append(item)
            seen.add(item)
    return cleaned


def _normalize_uuid(value: str, field_name: str) -> str:
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{field_name} 格式不正确") from exc


def _java_session_to_uuid(session_id: str | None) -> str | None:
    if not session_id:
        return None
    try:
        return str(UUID(str(session_id)))
    except ValueError:
        return str(uuid5(NAMESPACE_URL, f"java-chat-session:{session_id}"))
