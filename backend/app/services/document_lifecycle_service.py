from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import (
    Document,
    DocumentChunk,
    DocumentJob,
    DocumentParseResult,
    QaPair,
    QaPairEmbedding,
)
from app.services.minio_service import MinioService


@dataclass(frozen=True)
class StoredObjectRef:
    bucket: str
    object_key: str | None


@dataclass
class IndexCleanupResult:
    document_id: str | None = None
    deleted_chunk_embeddings: int = 0
    deleted_chunks: int = 0
    deleted_parse_results: int = 0
    canceled_jobs: int = 0
    disabled_qa_pairs: int = 0
    deleted_qa_embeddings: int = 0
    touched_documents: int = 0

    @property
    def changed(self) -> bool:
        return any(
            (
                self.deleted_chunk_embeddings,
                self.deleted_chunks,
                self.deleted_parse_results,
                self.canceled_jobs,
                self.disabled_qa_pairs,
                self.deleted_qa_embeddings,
                self.touched_documents,
            )
        )

    def merge(self, other: "IndexCleanupResult") -> None:
        self.deleted_chunk_embeddings += other.deleted_chunk_embeddings
        self.deleted_chunks += other.deleted_chunks
        self.deleted_parse_results += other.deleted_parse_results
        self.canceled_jobs += other.canceled_jobs
        self.disabled_qa_pairs += other.disabled_qa_pairs
        self.deleted_qa_embeddings += other.deleted_qa_embeddings
        self.touched_documents += other.touched_documents

    def as_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "changed": self.changed,
            "deleted_chunk_embeddings": self.deleted_chunk_embeddings,
            "deleted_chunks": self.deleted_chunks,
            "deleted_parse_results": self.deleted_parse_results,
            "canceled_jobs": self.canceled_jobs,
            "disabled_qa_pairs": self.disabled_qa_pairs,
            "deleted_qa_embeddings": self.deleted_qa_embeddings,
            "touched_documents": self.touched_documents,
        }


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
            disable_source_qa=True,
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
            disable_source_qa=True,
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
        disable_source_qa: bool = False,
        touch_document: bool = True,
        bump_version: bool = True,
    ) -> IndexCleanupResult:
        now = datetime.now(timezone.utc)
        result = IndexCleanupResult(document_id=document_id)
        chunk_ids = await self._chunk_ids_for_document(db, document_id)
        if disable_source_qa:
            result.merge(await self._disable_document_qa_pairs(db, document_id, chunk_ids, now=now))

        chunk_embedding_result = await db.execute(
            text(
                """
                DELETE FROM chunk_embeddings
                WHERE document_id = :document_id
                   OR chunk_id = ANY(CAST(:chunk_ids AS uuid[]))
                """
            ),
            {"document_id": document_id, "chunk_ids": chunk_ids},
        )
        result.deleted_chunk_embeddings += self._rowcount(chunk_embedding_result)

        chunk_result = await db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        result.deleted_chunks += self._rowcount(chunk_result)

        if delete_parse_result:
            parse_result = await db.execute(
                delete(DocumentParseResult).where(DocumentParseResult.document_id == document_id)
            )
            result.deleted_parse_results += self._rowcount(parse_result)
        if cancel_jobs:
            result.canceled_jobs += await self.cancel_active_jobs(
                db,
                document_id,
                message="document changed; stale indexing job canceled",
                now=now,
            )
        if touch_document:
            touch_result = await db.execute(
                update(Document).where(Document.id == document_id).values(updated_at=now)
            )
            result.touched_documents += self._rowcount(touch_result)
        if bump_version and result.changed:
            await self.mark_knowledge_base_changed(db, document_id=document_id, reason=reason)
        return result

    async def clear_embeddings(
        self,
        db: AsyncSession,
        document_id: str,
        *,
        reason: str,
        touch_document: bool = True,
        bump_version: bool = True,
    ) -> IndexCleanupResult:
        now = datetime.now(timezone.utc)
        result = IndexCleanupResult(document_id=document_id)
        embedding_result = await db.execute(
            text(
                """
                DELETE FROM chunk_embeddings
                WHERE document_id = :document_id
                """
            ),
            {"document_id": document_id},
        )
        result.deleted_chunk_embeddings += self._rowcount(embedding_result)
        if touch_document:
            touch_result = await db.execute(
                update(Document).where(Document.id == document_id).values(updated_at=now)
            )
            result.touched_documents += self._rowcount(touch_result)
        if bump_version and result.changed:
            await self.mark_knowledge_base_changed(db, document_id=document_id, reason=reason)
        return result

    async def cleanup_deleted_document_artifacts(
        self,
        db: AsyncSession,
        *,
        document_id: str | None = None,
        reason: str = "cleanup_deleted_document_artifacts",
    ) -> IndexCleanupResult:
        query = select(Document.id).where(Document.deleted_at.is_not(None))
        if document_id:
            query = query.where(Document.id == document_id)
        rows = await db.execute(query.order_by(Document.deleted_at.desc()))
        deleted_document_ids = [str(item) for item in rows.scalars().all()]

        total = IndexCleanupResult(document_id=document_id)
        for deleted_document_id in deleted_document_ids:
            item = await self.clear_indexed_content(
                db,
                deleted_document_id,
                reason=reason,
                delete_parse_result=True,
                cancel_jobs=True,
                disable_source_qa=True,
                touch_document=False,
                bump_version=False,
            )
            total.merge(item)
        if total.changed:
            await self.mark_knowledge_base_changed(db, document_id=document_id, reason=reason)
        return total

    async def cancel_active_jobs(
        self,
        db: AsyncSession,
        document_id: str,
        *,
        message: str,
        now: datetime | None = None,
    ) -> int:
        timestamp = now or datetime.now(timezone.utc)
        result = await db.execute(
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
        return self._rowcount(result)

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

    async def _chunk_ids_for_document(self, db: AsyncSession, document_id: str) -> list[str]:
        rows = await db.execute(
            select(DocumentChunk.id).where(DocumentChunk.document_id == document_id)
        )
        return [str(item) for item in rows.scalars().all()]

    async def _disable_document_qa_pairs(
        self,
        db: AsyncSession,
        document_id: str,
        chunk_ids: list[str],
        *,
        now: datetime,
    ) -> IndexCleanupResult:
        result = IndexCleanupResult(document_id=document_id)
        qa_ids: set[str] = set()
        rows = await db.execute(select(QaPair.id).where(QaPair.source_document_id == document_id))
        qa_ids.update(str(item) for item in rows.scalars().all())

        if chunk_ids:
            rows = await db.execute(
                text(
                    """
                    SELECT id
                    FROM qa_pairs
                    WHERE source_chunk_ids IS NOT NULL
                      AND source_chunk_ids && CAST(:chunk_ids AS uuid[])
                    """
                ),
                {"chunk_ids": chunk_ids},
            )
            qa_ids.update(str(row[0]) for row in rows)

        if not qa_ids:
            return result

        qa_id_list = sorted(qa_ids)
        embedding_result = await db.execute(
            delete(QaPairEmbedding).where(QaPairEmbedding.qa_pair_id.in_(qa_id_list))
        )
        result.deleted_qa_embeddings += self._rowcount(embedding_result)

        qa_result = await db.execute(
            update(QaPair)
            .where(QaPair.id.in_(qa_id_list), QaPair.deleted_at.is_(None))
            .values(status="disabled", deleted_at=now, updated_at=now)
        )
        result.disabled_qa_pairs += self._rowcount(qa_result)
        return result

    def _rowcount(self, result) -> int:
        value = getattr(result, "rowcount", 0)
        return int(value or 0) if value and value > 0 else 0
