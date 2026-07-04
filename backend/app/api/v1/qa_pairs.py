from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.responses import ok
from app.db.models import Admin, Document, QaPair
from app.db.session import get_db
from app.services.task_queue_service import TaskQueueService


router = APIRouter(prefix="/qa-pairs", tags=["qa-pairs"])


class QaPairCreate(BaseModel):
    question: str
    answer: str
    status: str = "enabled"
    source_document_id: str | None = None
    source_chunk_ids: list[str] | None = None
    tags: list[str] | None = None


class QaPairUpdate(BaseModel):
    question: str | None = None
    answer: str | None = None
    status: str | None = None
    tags: list[str] | None = None


class QaStatusUpdate(BaseModel):
    status: str


@router.get("")
async def list_qa_pairs(
    keyword: str | None = None,
    status: str | None = None,
    document_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    query = select(QaPair).where(QaPair.deleted_at.is_(None))
    count_query = select(func.count()).select_from(QaPair).where(QaPair.deleted_at.is_(None))
    if keyword:
        condition = QaPair.question.ilike(f"%{keyword}%") | QaPair.answer.ilike(f"%{keyword}%")
        query = query.where(condition)
        count_query = count_query.where(condition)
    if status:
        query = query.where(QaPair.status == status)
        count_query = count_query.where(QaPair.status == status)
    if document_id:
        query = query.where(QaPair.source_document_id == document_id)
        count_query = count_query.where(QaPair.source_document_id == document_id)
    total = await db.scalar(count_query)
    rows = await db.execute(
        query.order_by(QaPair.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return ok(
        {
            "items": [serialize_qa(item) for item in rows.scalars()],
            "page": page,
            "page_size": page_size,
            "total": total or 0,
        }
    )


@router.post("")
async def create_qa_pair(
    payload: QaPairCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    source_url = None
    if payload.source_document_id:
        document = await db.scalar(select(Document).where(Document.id == payload.source_document_id))
        if document:
            source_url = document.source_url or document.preview_url or document.download_url
    qa = QaPair(
        question=payload.question,
        answer=payload.answer,
        status=payload.status,
        source_document_id=payload.source_document_id,
        source_chunk_ids=payload.source_chunk_ids,
        source_url=source_url,
        tags=payload.tags,
        created_by=str(admin.id),
        updated_by=str(admin.id),
    )
    db.add(qa)
    await db.commit()
    await db.refresh(qa)
    await _enqueue_qa_embedding_sync(str(qa.id))
    return ok(serialize_qa(qa))


@router.put("/{qa_pair_id}")
async def update_qa_pair(
    qa_pair_id: str,
    payload: QaPairUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    qa = await _get_qa(db, qa_pair_id)
    values = payload.model_dump(exclude_unset=True)
    values["version"] = qa.version + 1
    values["updated_by"] = str(admin.id)
    values["updated_at"] = datetime.now(timezone.utc)
    await db.execute(update(QaPair).where(QaPair.id == qa_pair_id).values(**values))
    await db.commit()
    qa = await _get_qa(db, qa_pair_id)
    await _enqueue_qa_embedding_sync(qa_pair_id)
    return ok(serialize_qa(qa))


@router.delete("/{qa_pair_id}")
async def delete_qa_pair(
    qa_pair_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    await _get_qa(db, qa_pair_id)
    await db.execute(
        update(QaPair)
        .where(QaPair.id == qa_pair_id)
        .values(deleted_at=datetime.now(timezone.utc), status="disabled")
    )
    await db.commit()
    return ok({"id": qa_pair_id})


@router.patch("/{qa_pair_id}/status")
async def update_qa_status(
    qa_pair_id: str,
    payload: QaStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    await _get_qa(db, qa_pair_id)
    await db.execute(
        update(QaPair).where(QaPair.id == qa_pair_id).values(status=payload.status)
    )
    await db.commit()
    qa = await _get_qa(db, qa_pair_id)
    return ok(serialize_qa(qa))


async def _get_qa(db: AsyncSession, qa_pair_id: str) -> QaPair:
    qa = await db.scalar(select(QaPair).where(QaPair.id == qa_pair_id, QaPair.deleted_at.is_(None)))
    if qa is None:
        raise HTTPException(status_code=404, detail="QA 不存在")
    return qa


async def _enqueue_qa_embedding_sync(qa_pair_id: str) -> dict:
    return await TaskQueueService().enqueue("qa_embedding_sync", {"qa_pair_id": qa_pair_id})


def serialize_qa(qa: QaPair) -> dict:
    return {
        "id": str(qa.id),
        "question": qa.question,
        "answer": qa.answer,
        "status": qa.status,
        "source_document_id": str(qa.source_document_id) if qa.source_document_id else None,
        "source_chunk_ids": [str(item) for item in qa.source_chunk_ids] if qa.source_chunk_ids else [],
        "source_url": qa.source_url,
        "tags": qa.tags or [],
        "version": qa.version,
        "updated_at": qa.updated_at.isoformat() if qa.updated_at else None,
    }
