from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
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

    @field_validator("question", "answer")
    @classmethod
    def validate_required_text(cls, value: str, info):
        value = value.strip()
        if not value:
            label = "问题" if info.field_name == "question" else "答案"
            raise ValueError(f"{label}不能为空")
        return value


class QaPairUpdate(BaseModel):
    question: str | None = None
    answer: str | None = None
    status: str | None = None
    tags: list[str] | None = None

    @field_validator("question", "answer")
    @classmethod
    def validate_optional_required_text(cls, value: str | None, info):
        if value is None:
            return value
        value = value.strip()
        if not value:
            label = "问题" if info.field_name == "question" else "答案"
            raise ValueError(f"{label}不能为空")
        return value


class QaStatusUpdate(BaseModel):
    status: str


@router.get("")
async def list_qa_pairs(
    keyword: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    document_id: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    filters = qa_pair_list_filters(keyword=keyword, status=status, tag=tag, document_id=document_id)
    query = select(QaPair).where(*filters)
    count_query = select(func.count()).select_from(QaPair).where(*filters)
    total = await db.scalar(count_query)
    rows = await db.execute(
        query.order_by(QaPair.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    # 标签筛选下拉要覆盖当前查询范围内的全部标签，不能只从当前页聚合，否则分页后会漏选项。
    available_tags = await list_available_qa_tags(db, keyword=keyword, status=status, document_id=document_id)
    return ok(
        {
            "items": [serialize_qa(item) for item in rows.scalars()],
            "page": page,
            "page_size": page_size,
            "total": total or 0,
            "available_tags": available_tags,
        }
    )


@router.post("")
async def create_qa_pair(
    payload: QaPairCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    duplicate_id = await db.scalar(select(QaPair.id).where(*qa_pair_duplicate_question_filters(payload.question)))
    if duplicate_id:
        # 新增问答只按“问题字符串完全一致”判重，不做模糊匹配，避免把相似但语义不同的问题误拦截。
        raise HTTPException(status_code=409, detail="当前已经存在该问答")
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


def qa_pair_list_filters(
    keyword: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    document_id: str | None = None,
) -> list:
    filters = [QaPair.deleted_at.is_(None)]
    if keyword:
        condition = QaPair.question.ilike(f"%{keyword}%") | QaPair.answer.ilike(f"%{keyword}%")
        filters.append(condition)
    if status:
        filters.append(QaPair.status == status)
    if tag:
        clean_tag = tag.strip()
        if clean_tag:
            # 标签筛选使用数组包含，保持按完整标签精确匹配，避免模糊匹配误命中相近分类。
            filters.append(QaPair.tags.contains([clean_tag]))
    if document_id:
        filters.append(QaPair.source_document_id == document_id)
    return filters


def qa_pair_duplicate_question_filters(question: str):
    # 完全一致判重只排除软删除记录；大小写、标点、空格都按入库后的标准字符串精确比较。
    return [QaPair.deleted_at.is_(None), QaPair.question == question]


async def list_available_qa_tags(
    db: AsyncSession,
    keyword: str | None = None,
    status: str | None = None,
    document_id: str | None = None,
) -> list[str]:
    filters = qa_pair_list_filters(keyword=keyword, status=status, document_id=document_id)
    filters.append(QaPair.tags.is_not(None))
    rows = await db.execute(select(QaPair.tags).where(*filters))
    tags: set[str] = set()
    for value in rows.scalars():
        for tag in value or []:
            clean_tag = str(tag).strip()
            if clean_tag:
                tags.add(clean_tag)
    return sorted(tags, key=lambda item: item.casefold())


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
