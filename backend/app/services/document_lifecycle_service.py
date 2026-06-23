from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Document, DocumentChunk, DocumentJob, DocumentParseResult
from app.services.minio_service import MinioService


@dataclass(frozen=True)
class StoredObjectRef:
    bucket: str
    object_key: str | None


class DocumentLifecycleService:
    """Keeps document metadata, indexes, and cache version changes in one DB flow."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def storage_objects_for_document(
        self, db: AsyncSession, document: Document
    ) -> list[StoredObjectRef]:
        refs = [StoredObjectRef(document.storage_bucket, document.storage_object_key)]
        parse_result = await db.scalar(
            select(DocumentParseResult).where(DocumentParseResult.document_id == str(document.id))
        )
        if parse_result:
            refs.append(
                StoredObjectRef(self.settings.minio_parsed_bucket, parse_result.content_object_key)
            )
        return refs

    async def soft_delete_document(
        self, db: AsyncSession, document: Document, *, reason: str = "document_deleted"
    ) -> list[StoredObjectRef]:
        document_id = str(document.id)
        refs = await self.storage_objects_for_document(db, document)
        await self.clear_indexed_content(
            db,
            document_id,
            reason=reason,
            delete_parse_result=True,
            cancel_jobs=True,
            touch_document=False,
            bump_version=False,
        )
        now = datetime.now(timezone.utc)
        await db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(status="deleted", deleted_at=now, updated_at=now)
        )
        await self.mark_knowledge_base_changed(db, document_id=document_id, reason=reason)
        return refs

    async def prepare_document_replacement(
        self, db: AsyncSession, document: Document, *, reason: str = "document_replaced"
    ) -> list[StoredObjectRef]:
        refs = await self.storage_objects_for_document(db, document)
        await self.clear_indexed_content(
            db,
            str(document.id),
            reason=reason,
            delete_parse_result=True,
            cancel_jobs=True,
            touch_document=False,
            bump_version=False,
        )
        return refs

    async def clear_indexed_content(
        self,
        db: AsyncSession,
        document_id: str,
        *,
        reason: str,
        delete_parse_result: bool = False,
        cancel_jobs: bool = False,
        touch_document: bool = True,
        bump_version: bool = True,
    ) -> None:
        now = datetime.now(timezone.utc)
        await db.execute(
            text(
                """
                DELETE FROM chunk_embeddings
                WHERE document_id = :document_id
                """
            ),
            {"document_id": document_id},
        )
        await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        if delete_parse_result:
            await db.execute(
                delete(DocumentParseResult).where(DocumentParseResult.document_id == document_id)
            )
        if cancel_jobs:
            await self.cancel_active_jobs(
                db,
                document_id,
                message="文档已变更，旧任务已取消",
                now=now,
            )
        if touch_document:
            await db.execute(
                update(Document).where(Document.id == document_id).values(updated_at=now)
            )
        if bump_version:
            await self.mark_knowledge_base_changed(db, document_id=document_id, reason=reason)

    async def clear_embeddings(
        self,
        db: AsyncSession,
        document_id: str,
        *,
        reason: str,
        touch_document: bool = True,
        bump_version: bool = True,
    ) -> None:
        now = datetime.now(timezone.utc)
        await db.execute(
            text(
                """
                DELETE FROM chunk_embeddings
                WHERE document_id = :document_id
                """
            ),
            {"document_id": document_id},
        )
        if touch_document:
            await db.execute(
                update(Document).where(Document.id == document_id).values(updated_at=now)
            )
        if bump_version:
            await self.mark_knowledge_base_changed(db, document_id=document_id, reason=reason)

    async def cancel_active_jobs(
        self,
        db: AsyncSession,
        document_id: str,
        *,
        message: str,
        now: datetime | None = None,
    ) -> None:
        timestamp = now or datetime.now(timezone.utc)
        await db.execute(
            update(DocumentJob)
            .where(
                DocumentJob.document_id == document_id,
                DocumentJob.status.in_(["pending", "running"]),
            )
            .values(
                status="canceled",
                progress=100,
                message=message,
                error_message=None,
                finished_at=timestamp,
                updated_at=timestamp,
            )
        )

    async def mark_knowledge_base_changed(
        self, db: AsyncSession, *, document_id: str | None, reason: str
    ) -> None:
        await db.execute(
            text(
                """
                INSERT INTO knowledge_base_versions(scope, version, changed_at, reason, document_id)
                VALUES ('default', 1, now(), :reason, CAST(:document_id AS uuid))
                ON CONFLICT (scope) DO UPDATE
                SET version = knowledge_base_versions.version + 1,
                    changed_at = EXCLUDED.changed_at,
                    reason = EXCLUDED.reason,
                    document_id = EXCLUDED.document_id
                """
            ),
            {"reason": reason, "document_id": document_id},
        )

    def remove_storage_objects(
        self, refs: list[StoredObjectRef], minio_service: MinioService | None = None
    ) -> None:
        minio = minio_service or MinioService()
        seen: set[tuple[str, str]] = set()
        for ref in refs:
            if not ref.object_key:
                continue
            key = (ref.bucket, ref.object_key)
            if key in seen:
                continue
            seen.add(key)
            minio.remove_object(ref.bucket, ref.object_key)
