import csv
import io
from datetime import datetime
from uuid import UUID
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.config import get_settings
from app.core.responses import ok
from app.db.models import Admin, Document, DocumentChunk, DocumentJob, DocumentParseResult
from app.db.session import get_db
from app.services.document_state import ARCHIVE_EXTENSIONS, LEGACY_OFFICE_EXTENSIONS, indexing_blocker
from app.services.document_pipeline import supported_file
from app.services.document_lifecycle_service import DocumentLifecycleService
from app.services.knowledge_base_service import KnowledgeBaseService, normalize_knowledge_base_name
from app.services.minio_service import MinioService
from app.services.task_queue_service import TaskQueueService
from app.services.document_upload_service import (
    DocumentDuplicateError,
    DocumentUploadPolicyError,
    DocumentUploadService,
    normalize_upload_file_name,
)


router = APIRouter(prefix="/documents", tags=["documents"])


BATCH_ACTIONS = {
    "batch_reparse": ("BRP", "批量重解析"),
    "batch_rechunk": ("BRC", "批量重切片"),
}
BATCH_JOB_STATUSES = {"pending", "running", "succeeded", "failed", "skipped", "canceled"}


class DocumentBatchPayload(BaseModel):
    document_ids: list[str] = Field(min_length=1, max_length=200)

    @field_validator("document_ids")
    @classmethod
    def normalize_document_ids(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            try:
                document_id = str(UUID(str(item)))
            except ValueError as exc:
                raise ValueError("document_id 格式不正确") from exc
            if document_id in seen:
                continue
            seen.add(document_id)
            normalized.append(document_id)
        if not normalized:
            raise ValueError("document_ids 不能为空")
        return normalized


class DocumentBatchKnowledgeBasePayload(DocumentBatchPayload):
    knowledge_base: str = Field(min_length=1, max_length=64)

    @field_validator("knowledge_base")
    @classmethod
    def normalize_knowledge_base(cls, value: str) -> str:
        normalized = normalize_knowledge_base(value)
        if not normalized:
            raise ValueError("knowledge_base 不能为空")
        return normalized


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    source_url: str | None = Form(default=None),
    auto_process: bool = Form(default=True),
    duplicate_policy: str = Form(default="reject"),
    overwrite_document_id: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    settings = get_settings()
    if not supported_file(file.filename or ""):
        raise HTTPException(status_code=415, detail="不支持的文件类型")
    data = await file.read()
    if len(data) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件超过 100MB")
    try:
        result = await DocumentUploadService().save_upload(
            db,
            file_name=file.filename,
            content_type=file.content_type,
            data=data,
            title=title,
            source_url=source_url,
            created_by=str(admin.id),
            duplicate_policy=duplicate_policy,
            overwrite_document_id=overwrite_document_id,
        )
    except DocumentDuplicateError as exc:
        raise HTTPException(
            status_code=409,
            detail=serialize_duplicate_check(exc.duplicate_check, message="文档已存在，请选择覆盖、保留副本或取消"),
        ) from exc
    except DocumentUploadPolicyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    document = result.document
    jobs = []
    if auto_process:
        task = await _enqueue_document_task(
            "document_full_pipeline",
            str(document.id),
            task_action="initial_parse",
            task_label="初次解析",
        )
        jobs.append({"job_type": "parse", "status": "queued", "task_id": task["id"]})
    return ok(
        {
            "document": serialize_document(document),
            "jobs": jobs,
            "action": result.action,
            "duplicate": serialize_duplicate_check(result.duplicate_check),
        }
    )


@router.get("/upload/check")
async def check_upload_duplicate(
    file_name: str = Query(..., min_length=1),
    file_hash: str | None = Query(default=None),
    file_size: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    settings = get_settings()
    safe_file_name = normalize_upload_file_name(file_name)
    if not supported_file(safe_file_name):
        raise HTTPException(status_code=415, detail="不支持的文件类型")
    if file_size is not None and file_size > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件超过 100MB")
    duplicate_check = await DocumentUploadService().check_duplicates(db, safe_file_name, file_hash)
    return ok(serialize_duplicate_check(duplicate_check))


@router.get("")
async def list_documents(
    keyword: str | None = None,
    status: str | None = None,
    knowledge_base: str | None = None,
    batch_id: str | None = None,
    batch_status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    query = select(Document).where(Document.deleted_at.is_(None))
    count_query = select(func.count()).select_from(Document).where(Document.deleted_at.is_(None))
    if keyword:
        condition = Document.title.ilike(f"%{keyword}%") | Document.file_name.ilike(f"%{keyword}%")
        query = query.where(condition)
        count_query = count_query.where(condition)
    if status:
        query = query.where(Document.status == status)
        count_query = count_query.where(Document.status == status)
    normalized_knowledge_base = normalize_knowledge_base(knowledge_base)
    if normalized_knowledge_base:
        query = query.where(Document.knowledge_base == normalized_knowledge_base)
        count_query = count_query.where(Document.knowledge_base == normalized_knowledge_base)
    batch_document_ids = _batch_document_ids_query(batch_id, batch_status)
    if batch_document_ids is not None:
        query = query.where(Document.id.in_(batch_document_ids))
        count_query = count_query.where(Document.id.in_(batch_document_ids))
    total = await db.scalar(count_query)
    rows = await db.execute(
        query.order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return ok(
        {
            "items": [serialize_document(row) for row in rows.scalars()],
            "page": page,
            "page_size": page_size,
            "total": total or 0,
        }
    )


@router.get("/export")
async def export_documents(
    keyword: str | None = None,
    status: str | None = None,
    knowledge_base: str | None = None,
    batch_id: str | None = None,
    batch_status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    query = select(Document).where(Document.deleted_at.is_(None))
    if keyword:
        condition = Document.title.ilike(f"%{keyword}%") | Document.file_name.ilike(f"%{keyword}%")
        query = query.where(condition)
    if status:
        query = query.where(Document.status == status)
    normalized_knowledge_base = normalize_knowledge_base(knowledge_base)
    if normalized_knowledge_base:
        query = query.where(Document.knowledge_base == normalized_knowledge_base)
    batch_document_ids = _batch_document_ids_query(batch_id, batch_status)
    if batch_document_ids is not None:
        query = query.where(Document.id.in_(batch_document_ids))
    rows = await db.execute(query.order_by(Document.created_at.desc()))
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(["名称", "文件名", "大小(B)", "上传时间", "所属知识库", "状态", "质量"])
    for document in rows.scalars():
        writer.writerow(
            [
                _display_document_title(document),
                document.file_name,
                document.file_size,
                document.created_at.isoformat() if document.created_at else "",
                document.knowledge_base or "default",
                document.status,
                float(document.parse_quality_score or 0),
            ]
        )
    filename = f"documents-{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    return Response(
        content="\ufeff" + buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/batch/delete")
async def batch_delete_documents(
    payload: DocumentBatchPayload,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    documents = await _get_documents(db, payload.document_ids)
    lifecycle = DocumentLifecycleService()
    storage_refs = []
    deleted_ids: list[str] = []
    for document in documents:
        storage_refs.extend(await lifecycle.soft_delete_document(db, document, reason="documents_batch_deleted"))
        deleted_ids.append(str(document.id))
    await db.commit()
    lifecycle.remove_storage_objects(storage_refs)
    return ok({"deleted": deleted_ids, "count": len(deleted_ids)})


@router.post("/batch/knowledge-base")
async def batch_update_knowledge_base(
    payload: DocumentBatchKnowledgeBasePayload,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    if not await KnowledgeBaseService().exists(db, payload.knowledge_base):
        raise HTTPException(status_code=400, detail="知识库不存在或已停用")
    documents = await _get_documents(db, payload.document_ids)
    ids = [str(document.id) for document in documents]
    await db.execute(
        update(Document)
        .where(Document.id.in_(ids), Document.deleted_at.is_(None))
        .values(knowledge_base=payload.knowledge_base)
    )
    for document_id in ids:
        await DocumentLifecycleService().mark_knowledge_base_changed(
            db,
            document_id=document_id,
            reason="documents_batch_knowledge_base_changed",
        )
    await db.commit()
    return ok({"updated": ids, "knowledge_base": payload.knowledge_base, "count": len(ids)})


@router.post("/batch/reparse")
async def batch_reparse_documents(
    payload: DocumentBatchPayload,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    documents = await _get_documents(db, payload.document_ids)
    batch = _new_batch("batch_reparse", [str(document.id) for document in documents])
    jobs = []
    for index, document in enumerate(documents, start=1):
        task = await _enqueue_document_task(
            "document_full_pipeline",
            str(document.id),
            **_batch_task_params(batch, index),
        )
        jobs.append(_batch_job_item(document, batch, "queued", task_id=task["id"], message="等待后台调度"))
    return ok({"batch": batch, "jobs": jobs, "count": len(jobs)})


@router.post("/batch/rechunk")
async def batch_rechunk_documents(
    payload: DocumentBatchPayload,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    documents = await _get_documents(db, payload.document_ids)
    batch = _new_batch("batch_rechunk", [str(document.id) for document in documents])
    jobs = []
    skipped = []
    for index, document in enumerate(documents, start=1):
        skip = await _indexing_skip_payload(db, document, "chunk")
        if skip:
            item = _batch_job_item(document, batch, "skipped", message=skip.get("message") or "已跳过")
            skipped.append(skip)
            jobs.append(item)
            continue
        task = await _enqueue_document_task(
            "document_rechunk",
            str(document.id),
            **_batch_task_params(batch, index),
        )
        jobs.append(_batch_job_item(document, batch, "queued", task_id=task["id"], message="等待后台调度"))
    return ok({"batch": batch, "jobs": jobs, "skipped": skipped, "count": len(jobs)})


@router.post("/cleanup-deleted-artifacts")
async def cleanup_deleted_document_artifacts(
    document_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    normalized_document_id = _normalize_document_id(document_id) if document_id else None
    result = await DocumentLifecycleService().cleanup_deleted_document_artifacts(
        db,
        document_id=normalized_document_id,
    )
    await db.commit()
    return ok(result.as_dict())


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    document = await _get_document(db, document_id)
    document_id = str(document.id)
    chunk_count = await db.scalar(
        select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == document_id)
    )
    jobs = await db.execute(
        select(DocumentJob).where(DocumentJob.document_id == document_id).order_by(DocumentJob.created_at.desc()).limit(5)
    )
    data = serialize_document(document)
    data["stats"] = {"chunk_count": chunk_count or 0}
    data["latest_jobs"] = [serialize_job(job) for job in jobs.scalars()]
    return ok(data)


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    document = await _get_document(db, document_id)
    lifecycle = DocumentLifecycleService()
    refs = await lifecycle.soft_delete_document(db, document)
    await db.commit()
    lifecycle.remove_storage_objects(refs)
    return ok({"id": document_id, "status": "deleted"})


@router.post("/{document_id}/reparse")
async def reparse_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    document = await _get_document(db, document_id)
    task = await _enqueue_document_task(
        "document_full_pipeline",
        str(document.id),
        task_action="manual_reparse",
        task_label="重解析",
    )
    return ok({"document_id": document_id, "status": "queued", "task_id": task["id"]})


@router.post("/{document_id}/rechunk")
async def rechunk_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    document = await _get_document(db, document_id)
    skip = await _indexing_skip_payload(db, document, "chunk")
    if skip:
        return ok(skip)
    task = await _enqueue_document_task(
        "document_rechunk",
        str(document.id),
        task_action="manual_rechunk",
        task_label="重切片",
    )
    return ok({"document_id": str(document.id), "status": "queued", "task_id": task["id"]})


@router.post("/{document_id}/reembed")
async def reembed_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    document = await _get_document(db, document_id)
    skip = await _indexing_skip_payload(db, document, "embed")
    if skip:
        return ok(skip)
    task = await _enqueue_document_task(
        "document_reembed",
        str(document.id),
        task_action="manual_reembed",
        task_label="重向量化",
    )
    return ok({"document_id": str(document.id), "status": "queued", "task_id": task["id"]})


@router.post("/{document_id}/convert-office")
async def convert_office_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    document = await _get_document(db, document_id)
    if str(document.file_ext or "").lower() not in LEGACY_OFFICE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="当前文档不是可转换的旧 Office 文件")
    task = await _enqueue_document_task("document_convert_office", str(document.id))
    return ok({"document_id": str(document.id), "job_type": "convert_office", "status": "queued", "task_id": task["id"]})


@router.post("/{document_id}/extract-archive")
async def extract_archive_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    document = await _get_document(db, document_id)
    if str(document.file_ext or "").lower() not in ARCHIVE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="当前文档不是可解压导入的压缩包")
    task = await _enqueue_document_task("document_extract_archive", str(document.id))
    return ok({"document_id": str(document.id), "job_type": "extract_import", "status": "queued", "task_id": task["id"]})


@router.post("/{document_id}/qa-pairs/generate")
async def generate_qa_pairs(
    document_id: str,
    count: int = 10,
    auto_enable: bool = True,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    document = await _get_document(db, document_id)
    skip = await _indexing_skip_payload(db, document, "qa_generate")
    if skip:
        return ok(skip)
    task = await TaskQueueService().enqueue(
        "document_qa_generate",
        {"document_id": str(document.id), "count": count, "auto_enable": auto_enable},
    )
    return ok({"document_id": str(document.id), "job_type": "qa_generate", "status": "queued", "task_id": task["id"]})


@router.get("/{document_id}/parse-result")
async def parse_result(
    document_id: str,
    format: str = "markdown",
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    document_id = _normalize_document_id(document_id)
    result = await db.scalar(
        select(DocumentParseResult).where(DocumentParseResult.document_id == document_id)
    )
    if result is None:
        raise HTTPException(status_code=404, detail="解析结果不存在")
    return ok(
        {
            "document_id": document_id,
            "format": format,
            "content": result.content_md if format == "markdown" else result.content_text,
            "quality_score": float(result.quality_score or 0),
            "parse_meta": result.parse_meta,
        }
    )


@router.get("/{document_id}/chunks")
async def list_chunks(
    document_id: str,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    document_id = _normalize_document_id(document_id)
    query = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
    count_query = select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == document_id)
    if keyword:
        query = query.where(DocumentChunk.content.ilike(f"%{keyword}%"))
        count_query = count_query.where(DocumentChunk.content.ilike(f"%{keyword}%"))
    total = await db.scalar(count_query)
    rows = await db.execute(
        query.order_by(DocumentChunk.chunk_no).offset((page - 1) * page_size).limit(page_size)
    )
    return ok(
        {
            "items": [
                {
                    "id": str(chunk.id),
                    "chunk_no": chunk.chunk_no,
                    "chunk_type": chunk.chunk_type,
                    "content": chunk.content,
                    "char_count": chunk.char_count,
                    "token_count": chunk.token_count,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "section_path": chunk.section_path,
                    "metadata": chunk.metadata_,
                    "is_active": chunk.is_active,
                }
                for chunk in rows.scalars()
            ],
            "page": page,
            "page_size": page_size,
            "total": total or 0,
        }
    )


async def _get_document(db: AsyncSession, document_id: str) -> Document:
    document_id = _normalize_document_id(document_id)
    document = await db.scalar(
        select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
    )
    if document is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    return document


async def _get_documents(db: AsyncSession, document_ids: list[str]) -> list[Document]:
    normalized_ids = [_normalize_document_id(item) for item in document_ids]
    rows = await db.execute(
        select(Document).where(Document.id.in_(normalized_ids), Document.deleted_at.is_(None))
    )
    documents = list(rows.scalars())
    found_ids = {str(document.id) for document in documents}
    missing = [document_id for document_id in normalized_ids if document_id not in found_ids]
    if missing:
        raise HTTPException(status_code=404, detail=f"文档不存在：{', '.join(missing[:3])}")
    return documents


async def _indexing_skip_payload(db: AsyncSession, document: Document, job_type: str) -> dict | None:
    parse_result = await db.scalar(
        select(DocumentParseResult).where(DocumentParseResult.document_id == str(document.id))
    )
    message = indexing_blocker(document, parse_result.parse_meta if parse_result else None)
    if message is None:
        return None
    return {
        "document_id": str(document.id),
        "job_type": job_type,
        "status": "skipped",
        "message": message,
    }


async def _enqueue_document_task(task_type: str, document_id: str, **params) -> dict:
    payload = {"document_id": document_id, **{key: value for key, value in params.items() if value is not None}}
    return await TaskQueueService().enqueue(task_type, payload)


def _new_batch(action: str, document_ids: list[str]) -> dict:
    prefix, label = BATCH_ACTIONS[action]
    batch_id = f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:6].upper()}"
    return {
        "id": batch_id,
        "action": action,
        "label": label,
        "total": len(document_ids),
        "document_ids": document_ids,
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
    }


def _batch_task_params(batch: dict, index: int) -> dict:
    return {
        "task_action": batch["action"],
        "task_label": batch["label"],
        "batch_id": batch["id"],
        "batch_action": batch["action"],
        "batch_label": batch["label"],
        "batch_size": batch["total"],
        "batch_index": index,
    }


def _batch_job_item(
    document: Document,
    batch: dict,
    status: str,
    *,
    task_id: str | None = None,
    message: str | None = None,
) -> dict:
    return {
        "document_id": str(document.id),
        "title": _display_document_title(document),
        "file_name": document.file_name,
        "status": status,
        "message": message,
        "task_id": task_id,
        "batch_id": batch["id"],
        "batch_action": batch["action"],
        "batch_label": batch["label"],
    }


def _batch_document_ids_query(batch_id: str | None, batch_status: str | None = None):
    normalized_batch_id = normalize_batch_id(batch_id)
    if not normalized_batch_id:
        return None
    query = select(DocumentJob.document_id).where(
        DocumentJob.params["batch_id"].astext == normalized_batch_id
    )
    normalized_status = normalize_batch_status(batch_status)
    if normalized_status:
        query = query.where(DocumentJob.status == normalized_status)
    return query


def _normalize_document_id(document_id: str) -> str:
    try:
        return str(UUID(document_id))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="document_id 格式不正确") from exc


def serialize_document(document: Document) -> dict:
    return {
        "id": str(document.id),
        "title": _display_document_title(document),
        "file_name": document.file_name,
        "file_ext": document.file_ext,
        "file_size": document.file_size,
        "knowledge_base": document.knowledge_base or "default",
        "status": document.status,
        "source_url": document.source_url,
        "preview_url": _document_access_url(document),
        "download_url": _document_access_url(document, download=True),
        "parse_quality_score": float(document.parse_quality_score or 0),
        "error_message": document.error_message,
        "created_at": document.created_at.isoformat() if document.created_at else None,
        "updated_at": document.updated_at.isoformat() if document.updated_at else None,
    }


def normalize_knowledge_base(value: str | None) -> str:
    return normalize_knowledge_base_name(value)


def normalize_batch_id(value: str | None) -> str:
    return str(value or "").strip()[:96]


def normalize_batch_status(value: str | None) -> str:
    status = str(value or "").strip()
    return status if status in BATCH_JOB_STATUSES else ""


def serialize_duplicate_check(duplicate_check, message: str | None = None) -> dict:
    matches = [
        {
            "same_name": match.same_name,
            "same_hash": match.same_hash,
            "reason": _duplicate_reason(match.same_name, match.same_hash),
            "document": serialize_document(match.document),
        }
        for match in duplicate_check.matches
    ]
    recommended_action = "none"
    if duplicate_check.same_hash:
        recommended_action = "use_existing"
    elif duplicate_check.same_name:
        recommended_action = "overwrite"
    payload = {
        "requested_file_name": duplicate_check.requested_file_name,
        "file_hash": duplicate_check.file_hash,
        "has_duplicate": duplicate_check.has_duplicate,
        "same_name": duplicate_check.same_name,
        "same_hash": duplicate_check.same_hash,
        "recommended_action": recommended_action,
        "matches": matches,
    }
    if message:
        payload["message"] = message
    return payload


def serialize_job(job: DocumentJob) -> dict:
    return {
        "id": str(job.id),
        "document_id": str(job.document_id),
        "job_type": job.job_type,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "error_message": job.error_message,
        "params": job.params,
        "result": job.result,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


def _display_document_title(document: Document) -> str:
    title = document.title or ""
    if not title or title.count("?") >= max(2, len(title) // 2):
        return document.file_name
    return title


def _document_access_url(document: Document, download: bool = False) -> str | None:
    if document.source_url and not download:
        return document.source_url
    try:
        return MinioService().proxy_url(
            document.storage_bucket,
            document.storage_object_key,
            download_name=document.file_name if download else None,
        )
    except Exception:
        return document.preview_url or document.download_url


def _duplicate_reason(same_name: bool, same_hash: bool) -> str:
    if same_name and same_hash:
        return "same_name_and_content"
    if same_name:
        return "same_name"
    if same_hash:
        return "same_content"
    return "unknown"
