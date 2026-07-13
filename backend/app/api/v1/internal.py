"""
Java 后台专用 internal API。负责文档接入、权限范围过滤、任务查询、会话和问答，是 Java 联调的核心入口。
"""

from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import String, and_, cast, false, func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user_from_sa_token
from app.core.concurrency import release_chat_slot, try_acquire_chat_slot
from app.core.config import get_settings
from app.core.responses import ok
from app.db.models import AnswerFeedback, Conversation, ConversationMessage, Document, DocumentJob, RetrievalLog
from app.db.session import get_db
from app.services.chat_service import ChatService
from app.services.conversation_title import normalize_conversation_title, validate_manual_conversation_title
from app.services.document_lifecycle_service import DocumentLifecycleService
from app.services.document_pipeline import supported_file
from app.services.knowledge_base_service import (
    KnowledgeBaseService,
    normalize_knowledge_base_name,
    serialize_knowledge_base_option,
)
from app.services.task_queue_service import TaskQueueService


router = APIRouter(tags=["internal-rag"], dependencies=[Depends(get_current_user_from_sa_token)])

ALLOWED_FEEDBACK_ERROR_TYPES = {
    "answer_wrong",
    "citation_wrong",
    "off_topic",
    "incomplete",
    "other",
}
BATCH_ACTIONS = {
    "batch_reparse": ("BRP", "Batch reparse"),
    "batch_rechunk": ("BRC", "Batch rechunk"),
}
BATCH_JOB_STATUSES = {"pending", "running", "succeeded", "failed", "skipped", "canceled"}


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


class InternalDocumentBatchPayload(BaseModel):
    attach_ids: list[int] = Field(min_length=1, max_length=200)

    @field_validator("attach_ids")
    @classmethod
    def normalize_attach_ids(cls, value: list[int]) -> list[int]:
        normalized: list[int] = []
        seen: set[int] = set()
        for item in value:
            attach_id = int(item)
            if attach_id <= 0:
                raise ValueError("attach_ids must be positive")
            if attach_id in seen:
                continue
            seen.add(attach_id)
            normalized.append(attach_id)
        if not normalized:
            raise ValueError("attach_ids must not be empty")
        return normalized


class InternalDocumentBatchKnowledgePayload(InternalDocumentBatchPayload):
    knowledge_id: str = Field(min_length=1, max_length=128)

    @field_validator("knowledge_id")
    @classmethod
    def normalize_knowledge_id(cls, value: str) -> str:
        normalized = normalize_knowledge_base_name(value)
        if not normalized:
            raise ValueError("knowledge_id must not be empty")
        return normalized


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


class InternalAnswerFeedbackCreate(BaseModel):
    assistant_message_id: str = Field(min_length=1)
    error_type: str = Field(min_length=1)
    description: str = Field(default="", max_length=1000)

    @field_validator("error_type")
    @classmethod
    def validate_error_type(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in ALLOWED_FEEDBACK_ERROR_TYPES:
            raise ValueError("unsupported feedback error type")
        return normalized

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        return value.strip()


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    return ok({"status": "ok", "name": settings.app_name})


@router.get("/knowledge-bases")
async def list_knowledge_bases(db: AsyncSession = Depends(get_db)) -> dict:
    options = await KnowledgeBaseService().list_options(db)
    return ok(
        {
            "items": [serialize_knowledge_base_option(option) for option in options],
            "default": "default",
            "total": len(options),
        }
    )


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


@router.post("/documents/batch/reparse")
async def batch_reparse_documents(payload: InternalDocumentBatchPayload, db: AsyncSession = Depends(get_db)) -> dict:
    documents = await _get_documents_by_attach_ids(db, payload.attach_ids)
    batch = _new_batch("batch_reparse", len(documents))
    jobs = []
    for index, document in enumerate(documents, start=1):
        job = await _enqueue_document_job(
            db,
            document,
            "document_full_pipeline",
            {
                "document_id": str(document.id),
                "attach_id": document.java_attach_id,
                **_batch_task_params(batch, index),
            },
        )
        jobs.append(_batch_job_item(document, batch, index, "queued", job_id=str(job.id)))
    return ok({"batch": batch, "jobs": jobs, "count": len(jobs)})


@router.post("/documents/batch/rechunk")
async def batch_rechunk_documents(payload: InternalDocumentBatchPayload, db: AsyncSession = Depends(get_db)) -> dict:
    documents = await _get_documents_by_attach_ids(db, payload.attach_ids)
    batch = _new_batch("batch_rechunk", len(documents))
    jobs = []
    for index, document in enumerate(documents, start=1):
        job = await _enqueue_document_job(
            db,
            document,
            "document_rechunk",
            {
                "document_id": str(document.id),
                "attach_id": document.java_attach_id,
                **_batch_task_params(batch, index),
            },
        )
        jobs.append(_batch_job_item(document, batch, index, "queued", job_id=str(job.id)))
    return ok({"batch": batch, "jobs": jobs, "count": len(jobs)})


@router.post("/documents/batch/knowledge-base")
async def batch_update_knowledge_base(
    payload: InternalDocumentBatchKnowledgePayload,
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not await KnowledgeBaseService().exists(db, payload.knowledge_id):
        raise HTTPException(status_code=400, detail="knowledge_id not found")
    documents = await _get_documents_by_attach_ids(db, payload.attach_ids)
    ids = [str(document.id) for document in documents]
    await db.execute(
        update(Document)
        .where(Document.id.in_(ids), Document.deleted_at.is_(None))
        .values(knowledge_base=payload.knowledge_id)
    )
    for document_id in ids:
        await DocumentLifecycleService().mark_knowledge_base_changed(
            db,
            document_id=document_id,
            reason="internal_batch_knowledge_base_changed",
        )
    await db.commit()
    return ok(
        {
            "updated": [
                {"attach_id": document.java_attach_id, "rag_doc_id": str(document.id)}
                for document in documents
            ],
            "knowledge_base": payload.knowledge_id,
            "count": len(documents),
        }
    )


@router.post("/documents/batch/delete")
async def batch_delete_documents(payload: InternalDocumentBatchPayload, db: AsyncSession = Depends(get_db)) -> dict:
    documents = await _get_documents_by_attach_ids(db, payload.attach_ids)
    lifecycle = DocumentLifecycleService()
    storage_refs = []
    deleted = []
    for document in documents:
        storage_refs.extend(await lifecycle.soft_delete_document(db, document, reason="internal_batch_deleted"))
        deleted.append({"attach_id": document.java_attach_id, "rag_doc_id": str(document.id)})
    await db.commit()
    lifecycle.remove_storage_objects(storage_refs)
    return ok({"deleted": deleted, "count": len(deleted)})


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


@router.get("/jobs")
async def list_jobs(
    batch_id: str | None = None,
    attach_id: int | None = Query(default=None, gt=0),
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
) -> dict:
    page = max(1, int(page or 1))
    page_size = min(100, max(1, int(page_size or 20)))
    filters = []
    normalized_batch_id = normalize_batch_id(batch_id)
    normalized_status = normalize_batch_status(status)
    if normalized_batch_id:
        filters.append(DocumentJob.params["batch_id"].as_string() == normalized_batch_id)
    if normalized_status:
        filters.append(DocumentJob.status == normalized_status)
    if attach_id is not None:
        document = await _get_document_by_attach_id(db, attach_id)
        filters.append(DocumentJob.document_id == str(document.id))
    query = select(DocumentJob)
    count_query = select(func.count()).select_from(DocumentJob)
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)
    total = await db.scalar(count_query)
    rows = await db.execute(
        query.order_by(DocumentJob.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return ok(
        {
            "items": [_serialize_job(job) for job in rows.scalars()],
            "page": page,
            "page_size": page_size,
            "total": int(total or 0),
        }
    )


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
    if created_by and str(created_by) not in {current_user.user_id, current_user.login_id, current_user.id}:
        raise HTTPException(status_code=403, detail="无权查看其他用户会话")
    filters = _conversation_filters(
        q,
        feedback_only,
        created_by or current_user.user_id,
        _conversation_owner_id(current_user),
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
    if not _can_access_conversation(conversation, current_user):
        raise HTTPException(status_code=403, detail="无权访问此会话")
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


@router.post("/feedback/answers")
async def submit_answer_feedback(
    payload: InternalAnswerFeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_from_sa_token),
) -> dict:
    return ok(await _submit_answer_feedback(db, payload, current_user))


@router.post("/feedback/answers/{feedback_id}/cancel")
async def cancel_answer_feedback(
    feedback_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_from_sa_token),
) -> dict:
    return ok(await _cancel_answer_feedback(db, feedback_id, current_user))


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


# ============================================================
# Admin 接口：全量数据，不做用户级隔离，由 Java 后台做权限过滤
# ============================================================


@router.get("/admin/conversations")
async def list_admin_conversations(
    page: int = 1,
    page_size: int = 20,
    q: str | None = None,
    feedback_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_from_sa_token),
) -> dict:
    """全量会话列表（admin 专用），不做用户隔离，Java 后台自行做权限过滤。"""
    page = max(1, int(page or 1))
    page_size = min(100, max(1, int(page_size or 20)))
    filters = _conversation_filters(q, feedback_only, created_by=None, owner_id=None)
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


@router.get("/admin/conversations/{conversation_id}/messages")
async def list_admin_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_from_sa_token),
) -> dict:
    """全量会话消息列表（admin 专用），不做用户隔离。"""
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


@router.post("/chat/stream")
async def stream_chat(
    payload: InternalChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user_from_sa_token),
) -> StreamingResponse:
    document_filter = await _allowed_document_filter(db, payload.access_scope, payload.user_context)
    if not await try_acquire_chat_slot():
        raise HTTPException(status_code=429, detail="当前问答请求较多，请稍后再试")
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
                enable_rewrite=payload.options.enable_rewrite,
                created_by=_conversation_owner_id(current_user),
                context_created_by=current_user.user_id,
                document_filter=document_filter,
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
    document_filter = await _allowed_document_filter(db, payload.access_scope, payload.user_context)
    if not await try_acquire_chat_slot():
        raise HTTPException(status_code=429, detail="当前问答请求较多，请稍后再试")
    conversation_id = _java_session_to_uuid(payload.session_id)
    try:
        result = await ChatService().chat_once(
            db=db,
            question=payload.question,
            conversation_id=conversation_id,
            enable_suggested_questions=payload.options.enable_suggested_questions,
            top_k=payload.options.top_k,
            rerank_top_k=payload.options.rerank_top_k,
            enable_rewrite=payload.options.enable_rewrite,
            created_by=_conversation_owner_id(current_user),
            context_created_by=current_user.user_id,
            document_filter=document_filter,
        )
        return ok(result)
    finally:
        release_chat_slot()


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
    try:
        async for chunk in generator:
            yield chunk
    finally:
        release_chat_slot()


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
    task_payload = dict(payload)
    job = DocumentJob(
        document_id=str(document.id),
        job_type=job_type,
        status="pending",
        progress=0,
        message="已加入处理队列",
        params={"source": "java_internal", **task_payload},
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    await TaskQueueService().enqueue(job_type, {**task_payload, "job_id": str(job.id)})
    return job


async def _get_document_by_attach_id(db: AsyncSession, attach_id: int) -> Document:
    document = await db.scalar(select(Document).where(Document.java_attach_id == attach_id, Document.deleted_at.is_(None)))
    if document is None:
        raise HTTPException(status_code=404, detail="RAG 文档不存在")
    return document


async def _get_documents_by_attach_ids(db: AsyncSession, attach_ids: list[int]) -> list[Document]:
    rows = await db.execute(
        select(Document).where(Document.java_attach_id.in_(attach_ids), Document.deleted_at.is_(None))
    )
    by_attach_id = {
        int(document.java_attach_id): document
        for document in rows.scalars()
        if document.java_attach_id is not None
    }
    missing = [str(attach_id) for attach_id in attach_ids if attach_id not in by_attach_id]
    if missing:
        raise HTTPException(status_code=404, detail=f"RAG documents not found: {', '.join(missing[:5])}")
    return [by_attach_id[attach_id] for attach_id in attach_ids]


def _new_batch(action: str, total: int) -> dict:
    prefix, label = BATCH_ACTIONS[action]
    now = datetime.now(timezone.utc)
    return {
        "batch_id": f"{prefix}-{now.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}",
        "action": action,
        "label": label,
        "total": total,
        "created_at": now.isoformat(),
    }


def _batch_task_params(batch: dict, index: int) -> dict:
    return {
        "batch_id": batch["batch_id"],
        "batch_index": index,
        "batch_label": batch["label"],
        "batch_total": batch["total"],
    }


def _batch_job_item(
    document: Document,
    batch: dict,
    index: int,
    status: str,
    *,
    job_id: str | None = None,
    message: str | None = None,
) -> dict:
    return {
        "batch_id": batch["batch_id"],
        "batch_index": index,
        "batch_label": batch["label"],
        "attach_id": document.java_attach_id,
        "rag_doc_id": str(document.id),
        "file_name": document.file_name,
        "status": status,
        "job_id": job_id,
        "message": message,
    }


def normalize_batch_id(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())[:64]


def normalize_batch_status(value: str | None) -> str:
    normalized = " ".join(str(value or "").strip().split())[:32]
    if normalized and normalized not in BATCH_JOB_STATUSES:
        raise HTTPException(status_code=422, detail="status is unsupported")
    return normalized


async def _get_conversation(db: AsyncSession, conversation_id: str) -> Conversation:
    conversation = await db.scalar(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.deleted_at.is_(None))
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conversation


async def _allowed_document_filter(db: AsyncSession, scope: AccessScope, user: UserContext) -> dict:
    sql, params, cache_key = _document_access_sql(scope, user)
    exists_row = await db.scalar(
        text(f"SELECT 1 FROM documents d WHERE ({sql}) LIMIT 1"),
        params,
    )
    if not exists_row:
        raise HTTPException(status_code=403, detail="当前用户没有可检索的知识库资料")
    return {
        "document_sql": sql,
        "qa_sql": f"q.source_document_id IS NOT NULL AND ({sql})",
        "params": params,
        "cache_key": cache_key,
    }


def _document_access_sql(scope: AccessScope, user: UserContext) -> tuple[str, dict, dict]:
    params: dict = {"user_id": str(user.user_id)}
    clauses = [
        "d.deleted_at IS NULL",
        "d.visible_in_chat = true",
        "d.status = 'indexed'",
    ]

    allowed_dept_ids = _clean_list(scope.allowed_dept_ids)
    allowed_knowledge_ids = _clean_list(scope.allowed_knowledge_ids)
    allowed_attach_ids = list(scope.allowed_attach_ids or [])
    deny_attach_ids = list(scope.deny_attach_ids or [])
    dept_conditions: list[str] = []

    if allowed_dept_ids:
        params["allowed_dept_ids"] = allowed_dept_ids
        dept_conditions.extend(
            [
                "d.publish_dept_id = ANY(CAST(:allowed_dept_ids AS text[]))",
                "d.allowed_dept_ids && CAST(:allowed_dept_ids AS text[])",
            ]
        )

    if scope.scope_mode == "admin_all":
        pass
    elif scope.scope_mode == "all_public":
        clauses.append("d.publish_scope = 'public'")
    elif scope.scope_mode == "dept":
        if not allowed_dept_ids:
            raise HTTPException(status_code=403, detail="部门权限范围为空，拒绝检索")
        clauses.append(_document_access_sql_condition(dept_conditions, user_id_param="CAST(:user_id AS text)"))
    elif scope.scope_mode == "custom":
        if not allowed_dept_ids and not allowed_knowledge_ids and not allowed_attach_ids:
            raise HTTPException(status_code=403, detail="自定义权限范围为空，拒绝检索")
        clauses.append(
            _custom_document_access_sql_condition(
                dept_conditions,
                explicit_attach=bool(allowed_attach_ids),
                explicit_knowledge=bool(allowed_knowledge_ids),
            )
        )

    if allowed_knowledge_ids:
        params["allowed_knowledge_ids"] = allowed_knowledge_ids
        if scope.scope_mode != "custom":
            clauses.append("d.knowledge_base = ANY(CAST(:allowed_knowledge_ids AS text[]))")
    if allowed_attach_ids:
        params["allowed_attach_ids"] = allowed_attach_ids
        if scope.scope_mode != "custom":
            clauses.append("d.java_attach_id = ANY(CAST(:allowed_attach_ids AS bigint[]))")
    if deny_attach_ids:
        params["deny_attach_ids"] = deny_attach_ids
        clauses.append(
            "(d.java_attach_id IS NULL OR NOT (d.java_attach_id = ANY(CAST(:deny_attach_ids AS bigint[]))))"
        )

    cache_key = {
        "scope_mode": scope.scope_mode,
        "allowed_dept_ids": allowed_dept_ids,
        "allowed_knowledge_ids": allowed_knowledge_ids,
        "allowed_attach_ids": allowed_attach_ids,
        "deny_attach_ids": deny_attach_ids,
        "user_id": str(user.user_id),
    }
    return " AND ".join(f"({clause})" for clause in clauses), params, cache_key


def _document_access_sql_condition(
    dept_conditions: list[str],
    *,
    user_id_param: str,
    explicit_attach: bool = False,
) -> str:
    parts = ["d.publish_scope = 'public'"]
    if explicit_attach:
        parts.append("d.java_attach_id = ANY(CAST(:allowed_attach_ids AS bigint[]))")
    if dept_conditions:
        parts.append(f"(d.publish_scope = 'dept' AND ({' OR '.join(dept_conditions)}))")
    parts.append(f"(d.publish_scope = 'private' AND d.owner_user_id = {user_id_param})")
    custom_parts = [
        f"d.owner_user_id = {user_id_param}",
        f"{user_id_param} = ANY(d.allowed_user_ids)",
    ]
    custom_parts.extend(dept_conditions)
    parts.append(f"(d.publish_scope = 'custom' AND ({' OR '.join(custom_parts)}))")
    return "(" + " OR ".join(parts) + ")"


def _custom_document_access_sql_condition(
    dept_conditions: list[str],
    *,
    explicit_attach: bool = False,
    explicit_knowledge: bool = False,
) -> str:
    parts: list[str] = []
    if explicit_attach:
        parts.append("d.java_attach_id = ANY(CAST(:allowed_attach_ids AS bigint[]))")
    if explicit_knowledge:
        parts.append("d.knowledge_base = ANY(CAST(:allowed_knowledge_ids AS text[]))")
    if dept_conditions:
        parts.append(f"({' OR '.join(dept_conditions)})")
    if not parts:
        raise HTTPException(status_code=403, detail="自定义权限范围为空，拒绝检索")
    return "(" + " OR ".join(parts) + ")"


async def _allowed_document_ids(db: AsyncSession, scope: AccessScope, user: UserContext) -> list[str]:
    # Java 先算业务权限，Python 再做检索前二次过滤，确保无权限文档不会进入模型上下文。
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
        query = query.where(_custom_document_access_condition(scope))
    if scope.allowed_knowledge_ids:
        if scope.scope_mode != "custom":
            query = query.where(Document.knowledge_base.in_(scope.allowed_knowledge_ids))
    if scope.allowed_attach_ids and scope.scope_mode != "custom":
        query = query.where(Document.java_attach_id.in_(scope.allowed_attach_ids))
    if scope.deny_attach_ids:
        # deny 优先级最高，即使前面允许了附件，也会在这里排除。
        query = query.where(~Document.java_attach_id.in_(scope.deny_attach_ids))
    rows = await db.execute(query)
    ids = [str(item) for item in rows.scalars()]
    if not ids:
        raise HTTPException(status_code=403, detail="当前用户没有可检索的知识库资料")
    return ids


def _document_access_condition(user: UserContext, scope: AccessScope, allow_explicit_attach: bool):
    # 文档可见性由公开、部门、私有、自定义四类规则组成。
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


def _custom_document_access_condition(scope: AccessScope):
    conditions = []
    allowed_dept_ids = _clean_list(scope.allowed_dept_ids)
    if scope.allowed_attach_ids:
        conditions.append(Document.java_attach_id.in_(scope.allowed_attach_ids))
    if scope.allowed_knowledge_ids:
        conditions.append(Document.knowledge_base.in_(scope.allowed_knowledge_ids))
    if allowed_dept_ids:
        conditions.extend(
            [
                Document.publish_dept_id.in_(allowed_dept_ids),
                Document.allowed_dept_ids.overlap(allowed_dept_ids),
            ]
        )
    return or_(*(conditions or [false()]))


def _conversation_filters(
    search: str | None = None,
    feedback_only: bool = False,
    created_by: str | None = None,
    owner_id: str | None = None,
) -> list:
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


async def _submit_answer_feedback(
    db: AsyncSession,
    payload: InternalAnswerFeedbackCreate,
    current_user: CurrentUser,
) -> dict:
    assistant_message_id = _normalize_uuid(payload.assistant_message_id, "assistant_message_id")
    assistant_message = await db.scalar(
        select(ConversationMessage).where(
            cast(ConversationMessage.id, String) == assistant_message_id,
            ConversationMessage.role == "assistant",
        )
    )
    if assistant_message is None:
        raise HTTPException(status_code=404, detail="assistant message not found")

    conversation = await _get_conversation(db, str(assistant_message.conversation_id))
    if not _can_access_conversation(conversation, current_user):
        raise HTTPException(status_code=403, detail="no permission for this conversation")

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
        "created_by": current_user.id,
        "updated_at": now,
    }
    if existing:
        await db.execute(update(AnswerFeedback).where(_feedback_id_filter(existing.id)).values(**values))
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
            "updated_by": current_user.user_id,
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
            _feedback_conversation_id() == str(assistant_message.conversation_id),
            AnswerFeedback.status == "open",
        )
    )
    return {
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


async def _cancel_answer_feedback(
    db: AsyncSession,
    feedback_id: str,
    current_user: CurrentUser,
) -> dict:
    feedback_id = _normalize_uuid(feedback_id, "feedback_id")
    feedback = await db.scalar(
        select(AnswerFeedback).where(
            _feedback_id_filter(feedback_id),
            AnswerFeedback.status == "open",
        )
    )
    if feedback is None:
        raise HTTPException(status_code=404, detail="open feedback not found")

    conversation = await _get_conversation(db, str(feedback.conversation_id))
    if not _can_access_conversation(conversation, current_user):
        raise HTTPException(status_code=403, detail="no permission for this conversation")

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
                    "canceled_by": current_user.user_id,
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
            _feedback_conversation_id() == str(feedback.conversation_id),
            AnswerFeedback.status == "open",
        )
    )
    return {
        "id": str(feedback.id),
        "conversation_id": str(feedback.conversation_id),
        "assistant_message_id": str(feedback.assistant_message_id),
        "status": "canceled",
        "conversation_feedback_count": int(open_count or 0),
    }


def _feedback_id_filter(feedback_id: str):
    return cast(AnswerFeedback.id, String) == str(feedback_id)


def _feedback_assistant_message_id_filter(assistant_message_id: str):
    return cast(AnswerFeedback.assistant_message_id, String) == str(assistant_message_id)


def _retrieval_log_id_filter(retrieval_log_id: str):
    return cast(RetrievalLog.id, String) == str(retrieval_log_id)


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
    params = dict(job.params or {})
    return {
        "job_id": str(job.id),
        "rag_doc_id": str(job.document_id),
        "job_type": job.job_type,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "error_message": job.error_message,
        "params": params,
        "batch_id": params.get("batch_id"),
        "batch_index": params.get("batch_index"),
        "batch_label": params.get("batch_label"),
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
