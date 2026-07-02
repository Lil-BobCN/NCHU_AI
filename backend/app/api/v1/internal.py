from collections.abc import AsyncGenerator
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import and_, false, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_internal_service
from app.core.config import get_settings
from app.core.responses import ok
from app.db.models import Document, DocumentJob
from app.db.session import get_db
from app.services.chat_service import ChatService
from app.services.document_lifecycle_service import DocumentLifecycleService
from app.services.document_pipeline import supported_file
from app.services.task_queue_service import TaskQueueService

router = APIRouter(tags=["internal-rag"], dependencies=[Depends(require_internal_service)])

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

@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    return ok({"status": "ok", "name": settings.app_name})

@router.post("/documents/process")
async def process_document(payload: DocumentProcessRequest, db: AsyncSession = Depends(get_db)) -> dict:
    if not supported_file(payload.file_name):
        raise HTTPException(status_code=415, detail="不支持的文件类型")
    document = await _upsert_java_document(db, payload)
    jobs = []
    if payload.auto_process:
        task = await TaskQueueService().enqueue("document_full_pipeline", {"document_id": str(document.id), "attach_id": payload.attach_id})
        jobs.append({"job_id": task["id"], "status": "queued"})
    return ok({"attach_id": payload.attach_id, "rag_doc_id": str(document.id), "status": document.status, "jobs": jobs})

@router.post("/documents/{attach_id}/reparse")
async def reparse_document(attach_id: int, _: ReprocessRequest, db: AsyncSession = Depends(get_db)) -> dict:
    document = await _get_document_by_attach_id(db, attach_id)
    task = await TaskQueueService().enqueue("document_full_pipeline", {"document_id": str(document.id), "attach_id": attach_id})
    return ok({"attach_id": attach_id, "rag_doc_id": str(document.id), "job_id": task["id"], "status": "queued"})

@router.post("/documents/{attach_id}/rechunk")
async def rechunk_document(attach_id: int, _: RechunkRequest, db: AsyncSession = Depends(get_db)) -> dict:
    document = await _get_document_by_attach_id(db, attach_id)
    task = await TaskQueueService().enqueue("document_rechunk", {"document_id": str(document.id), "attach_id": attach_id})
    return ok({"attach_id": attach_id, "rag_doc_id": str(document.id), "job_id": task["id"], "status": "queued"})

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
    return ok({"job_id": str(job.id), "rag_doc_id": str(job.document_id), "job_type": job.job_type, "status": job.status, "progress": job.progress, "message": job.message, "error_message": job.error_message, "result": job.result})

@router.post("/chat/stream")
async def stream_chat(payload: InternalChatRequest, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    document_ids = await _allowed_document_ids(db, payload.access_scope, payload.user_context)
    conversation_id = _java_session_to_uuid(payload.session_id)
    service = ChatService()
    return StreamingResponse(_stream_with_java_boundary(service.stream_chat(db, payload.question, conversation_id, payload.options.enable_suggested_questions, payload.options.top_k, payload.options.rerank_top_k, document_ids, payload.options.enable_rewrite)), media_type="text/event-stream", headers={"Cache-Control": "no-cache, no-transform", "Connection": "keep-alive", "X-Accel-Buffering": "no"})

@router.post("/chat")
async def chat(payload: InternalChatRequest, db: AsyncSession = Depends(get_db)) -> dict:
    document_ids = await _allowed_document_ids(db, payload.access_scope, payload.user_context)
    conversation_id = _java_session_to_uuid(payload.session_id)
    result = await ChatService().chat_once(db, payload.question, conversation_id, payload.options.enable_suggested_questions, payload.options.top_k, payload.options.rerank_top_k, document_ids, payload.options.enable_rewrite)
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
    values = {"java_attach_id": payload.attach_id, "java_doc_id": payload.doc_id, "publish_dept_id": payload.publish_dept_id, "owner_user_id": payload.owner_user_id or payload.operator_id, "visible_in_chat": payload.visible_in_chat, "publish_scope": payload.publish_scope, "allowed_dept_ids": _clean_list(payload.allowed_dept_ids), "allowed_user_ids": _clean_list(payload.allowed_user_ids), "title": payload.file_name, "file_name": payload.file_name, "file_ext": ext, "mime_type": payload.mime_type, "file_size": payload.file_size, "file_hash": payload.file_hash, "storage_bucket": payload.bucket, "storage_object_key": payload.object_key, "knowledge_base": payload.knowledge_id, "status": status, "created_by": None, "deleted_at": None}
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

async def _get_document_by_attach_id(db: AsyncSession, attach_id: int) -> Document:
    document = await db.scalar(select(Document).where(Document.java_attach_id == attach_id, Document.deleted_at.is_(None)))
    if document is None:
        raise HTTPException(status_code=404, detail="RAG 文档不存在")
    return document

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
