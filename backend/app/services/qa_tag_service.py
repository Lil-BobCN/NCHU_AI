from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import QaPair, QaTag


def normalize_qa_tag_name(value: str) -> str:
    # 标签库名称需要统一裁剪空白并限制长度，避免“同一标签因为空格不同而重复入库”。
    return " ".join(str(value or "").strip().split())[:64]


def normalize_qa_tag_key(value: str) -> str:
    # normalized_name 用于唯一约束，casefold 比 lower 更适合处理中英文混合与特殊大小写字符。
    return normalize_qa_tag_name(value).casefold()


def normalize_qa_tag_list(values: list[str] | None) -> list[str]:
    # 前端、AI 生成和历史数据都可能传入重复标签；这里按规范化 key 去重，同时保留首次出现的展示名。
    tags: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        tag = normalize_qa_tag_name(value)
        key = normalize_qa_tag_key(tag)
        if not tag or key in seen:
            continue
        tags.append(tag)
        seen.add(key)
    return tags


async def ensure_qa_tags(db: AsyncSession, values: list[str] | None, admin_id: str | None = None) -> list[str]:
    # 所有 QA 入库路径都应先调用这里：既返回清洗后的 QA 标签数组，也把新标签补进标签库。
    tags = normalize_qa_tag_list(values)
    if tags:
        # 这里不用“先查再插”的写法，因为标签管理页和问答列表可能并发触发历史回填。
        # 直接交给数据库唯一约束兜底，可以避免两个请求同时补同名标签时抛唯一键冲突。
        await db.execute(
            pg_insert(QaTag)
            .values(
                [
                    {
                        "name": tag,
                        "normalized_name": normalize_qa_tag_key(tag),
                        "status": "enabled",
                        "created_by": admin_id,
                        "updated_by": admin_id,
                    }
                    for tag in tags
                ]
            )
            .on_conflict_do_nothing(index_elements=["normalized_name"])
        )
    return tags


async def sync_qa_tags_from_pairs(db: AsyncSession, admin_id: str | None = None) -> list[str]:
    # 兼容标签库上线前、以及历史后台任务直接写 qa_pairs.tags 造成的存量数据缺口。
    # GET 标签列表/可选标签时会先执行一次轻量回填，确保已有 QA 标签也能出现在标签管理和选择器中。
    rows = await db.execute(
        select(func.unnest(QaPair.tags).label("tag")).where(
            QaPair.deleted_at.is_(None),
            QaPair.tags.is_not(None),
        )
    )
    return await ensure_qa_tags(db, [str(row.tag) for row in rows if row.tag], admin_id)


async def list_enabled_qa_tag_names(db: AsyncSession) -> list[str]:
    # 可选标签只展示启用状态；停用标签仍可保留在旧 QA 对上，但不再作为新选择项出现。
    rows = await db.execute(select(QaTag.name).where(QaTag.status == "enabled").order_by(QaTag.name.asc()))
    return list(rows.scalars())
