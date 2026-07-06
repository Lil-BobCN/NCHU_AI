from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document


DEFAULT_KNOWLEDGE_BASE = "default"
NORMAL_KNOWLEDGE_STATUS = "0"


@dataclass(frozen=True)
class KnowledgeBaseOption:
    value: str
    label: str
    id: str | None = None
    code: str | None = None
    status: str = NORMAL_KNOWLEDGE_STATUS
    source: str = "documents"
    sort_order: int = 0
    is_top: int = 0
    created_at: datetime | None = None


def normalize_knowledge_base_name(value: str | None) -> str:
    return " ".join(str(value or "").strip().split())[:64]


def serialize_knowledge_base_option(option: KnowledgeBaseOption) -> dict[str, Any]:
    return {
        "id": option.id,
        "code": option.code,
        "name": option.label,
        "value": option.value,
        "label": option.label,
        "status": option.status,
        "source": option.source,
        "sort_order": option.sort_order,
        "is_top": option.is_top,
        "created_at": option.created_at.isoformat() if option.created_at else None,
    }


class KnowledgeBaseService:
    async def list_options(self, db: AsyncSession) -> list[KnowledgeBaseOption]:
        options: list[KnowledgeBaseOption] = [
            KnowledgeBaseOption(value=DEFAULT_KNOWLEDGE_BASE, label=DEFAULT_KNOWLEDGE_BASE)
        ]
        options.extend(await self._fetch_business_knowledge_bases(db))
        options.extend(await self._fetch_document_knowledge_bases(db))
        return self._dedupe(options)

    async def exists(self, db: AsyncSession, value: str) -> bool:
        normalized = normalize_knowledge_base_name(value)
        if not normalized:
            return False
        options = await self.list_options(db)
        return normalized in {option.value for option in options}

    async def _fetch_business_knowledge_bases(self, db: AsyncSession) -> list[KnowledgeBaseOption]:
        sql = text(
            """
            SELECT id::text AS id,
                   kid::text AS code,
                   kname::text AS name,
                   status::text AS status,
                   sort_order,
                   is_top,
                   create_time
              FROM public.knowledge_info
             WHERE status = :normal_status
               AND btrim(coalesce(kname, '')) <> ''
             ORDER BY is_top DESC, sort_order ASC, create_time DESC NULLS LAST, kname ASC
            """
        )
        try:
            rows = (await db.execute(sql, {"normal_status": NORMAL_KNOWLEDGE_STATUS})).mappings()
        except SQLAlchemyError:
            await db.rollback()
            return []

        options: list[KnowledgeBaseOption] = []
        for row in rows:
            name = normalize_knowledge_base_name(row.get("name"))
            if not name:
                continue
            options.append(
                KnowledgeBaseOption(
                    id=str(row["id"]) if row.get("id") is not None else None,
                    code=str(row["code"]) if row.get("code") is not None else None,
                    value=name,
                    label=name,
                    status=str(row.get("status") or NORMAL_KNOWLEDGE_STATUS),
                    source="knowledge_info",
                    sort_order=int(row.get("sort_order") or 0),
                    is_top=int(row.get("is_top") or 0),
                    created_at=row.get("create_time"),
                )
            )
        return options

    async def _fetch_document_knowledge_bases(self, db: AsyncSession) -> list[KnowledgeBaseOption]:
        try:
            rows = await db.execute(
                select(Document.knowledge_base)
                .where(Document.deleted_at.is_(None))
                .group_by(Document.knowledge_base)
                .order_by(Document.knowledge_base.asc())
            )
        except SQLAlchemyError:
            await db.rollback()
            return []

        options: list[KnowledgeBaseOption] = []
        for value in rows.scalars():
            name = normalize_knowledge_base_name(value)
            if name:
                options.append(KnowledgeBaseOption(value=name, label=name))
        return options

    @staticmethod
    def _dedupe(options: list[KnowledgeBaseOption]) -> list[KnowledgeBaseOption]:
        seen: set[str] = set()
        deduped: list[KnowledgeBaseOption] = []
        for option in options:
            key = option.value
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(option)
        return deduped
