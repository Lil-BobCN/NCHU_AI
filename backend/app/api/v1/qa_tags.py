from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.responses import ok
from app.db.models import Admin, QaPair, QaTag
from app.db.session import get_db
from app.services.qa_tag_service import normalize_qa_tag_key, normalize_qa_tag_name, sync_qa_tags_from_pairs


router = APIRouter(prefix="/qa-tags", tags=["qa-tags"])


class QaTagCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = normalize_qa_tag_name(value)
        if not name:
            raise ValueError("标签名称不能为空")
        return name


class QaTagUpdate(BaseModel):
    name: str | None = None
    status: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        name = normalize_qa_tag_name(value)
        if not name:
            raise ValueError("标签名称不能为空")
        return name

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if value not in {"enabled", "disabled"}:
            raise ValueError("标签状态不正确")
        return value


@router.get("")
async def list_qa_tags(
    keyword: str | None = None,
    include_disabled: bool = True,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    # 标签库功能上线前，已有 QA 记录可能已经带有 tags，但 qa_tags 表里没有对应记录。
    # 查询标签管理弹窗前先做一次回填，保证“文档解析自动生成的标签”也能被管理。
    await sync_qa_tags_from_pairs(db)
    await db.commit()
    filters = []
    if not include_disabled:
        filters.append(QaTag.status == "enabled")
    if keyword:
        filters.append(QaTag.name.ilike(f"%{normalize_qa_tag_name(keyword)}%"))
    rows = await db.execute(select(QaTag).where(*filters).order_by(QaTag.status.asc(), QaTag.name.asc()))
    tags = list(rows.scalars())
    usage_counts = await qa_tag_usage_counts(db)
    return ok([serialize_qa_tag(tag, usage_counts.get(tag.name, 0)) for tag in tags])


@router.post("")
async def create_qa_tag(
    payload: QaTagCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    normalized = normalize_qa_tag_key(payload.name)
    existing = await db.scalar(select(QaTag).where(QaTag.normalized_name == normalized))
    if existing:
        if existing.status == "disabled":
            # 用户重新新增一个已停用标签时，按“恢复启用”处理，避免同名标签重复。
            existing.status = "enabled"
            existing.updated_by = str(admin.id)
            existing.updated_at = datetime.now(timezone.utc)
            await db.commit()
            usage_counts = await qa_tag_usage_counts(db)
            return ok(serialize_qa_tag(existing, usage_counts.get(existing.name, 0)))
        raise HTTPException(status_code=409, detail="标签已存在")
    tag = QaTag(
        name=payload.name,
        normalized_name=normalized,
        status="enabled",
        created_by=str(admin.id),
        updated_by=str(admin.id),
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return ok(serialize_qa_tag(tag, 0))


@router.put("/{tag_id}")
async def update_qa_tag(
    tag_id: str,
    payload: QaTagUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    tag = await get_qa_tag(db, tag_id)
    old_name = tag.name
    values = payload.model_dump(exclude_unset=True)
    if "name" in values:
        new_name = normalize_qa_tag_name(values["name"])
        normalized = normalize_qa_tag_key(new_name)
        duplicate = await db.scalar(select(QaTag).where(QaTag.normalized_name == normalized, QaTag.id != tag_id))
        if duplicate:
            raise HTTPException(status_code=409, detail="标签已存在")
        # 标签重命名不仅更新标签库，也同步更新已关联 QA 对里的数组元素，
        # 否则列表筛选和聊天引用标签会继续显示旧名称。
        tag.name = new_name
        tag.normalized_name = normalized
        await rename_tag_in_qa_pairs(db, old_name, new_name)
    if "status" in values:
        tag.status = values["status"]
    tag.updated_by = str(admin.id)
    tag.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(tag)
    usage_counts = await qa_tag_usage_counts(db)
    return ok(serialize_qa_tag(tag, usage_counts.get(tag.name, 0)))


@router.patch("/{tag_id}/status")
async def update_qa_tag_status(
    tag_id: str,
    payload: QaTagUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    if payload.status not in {"enabled", "disabled"}:
        raise HTTPException(status_code=422, detail="标签状态不正确")
    tag = await get_qa_tag(db, tag_id)
    tag.status = payload.status
    tag.updated_by = str(admin.id)
    tag.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(tag)
    usage_counts = await qa_tag_usage_counts(db)
    return ok(serialize_qa_tag(tag, usage_counts.get(tag.name, 0)))


@router.delete("/{tag_id}")
async def delete_qa_tag(
    tag_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    tag = await get_qa_tag(db, tag_id)
    # 删除标签库记录时同步清理 QA 对上的标签引用，避免产生“库里没有但 QA 还挂着”的孤儿标签。
    await remove_tag_from_qa_pairs(db, tag.name)
    await db.delete(tag)
    await db.commit()
    return ok({"id": tag_id})


async def get_qa_tag(db: AsyncSession, tag_id: str) -> QaTag:
    tag = await db.scalar(select(QaTag).where(QaTag.id == tag_id))
    if tag is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    return tag


async def qa_tag_usage_counts(db: AsyncSession) -> dict[str, int]:
    # 使用次数按未删除 QA 对实时统计，保证标签重命名、删除和问答软删除后都能即时反映。
    rows = await db.execute(
        select(func.unnest(QaPair.tags).label("tag"), func.count().label("count"))
        .where(QaPair.deleted_at.is_(None), QaPair.tags.is_not(None))
        .group_by("tag")
    )
    return {str(row.tag): int(row.count or 0) for row in rows}


async def rename_tag_in_qa_pairs(db: AsyncSession, old_name: str, new_name: str) -> None:
    if old_name == new_name:
        return
    rows = await db.execute(
        select(QaPair).where(QaPair.deleted_at.is_(None), QaPair.tags.contains([old_name]))
    )
    for qa in rows.scalars():
        next_tags = []
        seen = set()
        for tag in qa.tags or []:
            value = new_name if tag == old_name else tag
            key = normalize_qa_tag_key(value)
            if not key or key in seen:
                continue
            next_tags.append(value)
            seen.add(key)
        qa.tags = next_tags


async def remove_tag_from_qa_pairs(db: AsyncSession, tag_name: str) -> None:
    rows = await db.execute(
        select(QaPair).where(QaPair.deleted_at.is_(None), QaPair.tags.contains([tag_name]))
    )
    for qa in rows.scalars():
        qa.tags = [tag for tag in qa.tags or [] if tag != tag_name]


def serialize_qa_tag(tag: QaTag, usage_count: int = 0) -> dict:
    return {
        "id": str(tag.id),
        "name": tag.name,
        "status": tag.status,
        "usage_count": usage_count,
        "created_at": tag.created_at.isoformat() if tag.created_at else None,
        "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
    }
