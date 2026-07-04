from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
import unicodedata

from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Document
from app.services.hash_service import sha256_bytes
from app.services.document_lifecycle_service import DocumentLifecycleService
from app.services.minio_service import MinioService


UploadDuplicatePolicy = Literal["reject", "overwrite", "keep_both"]
UPLOAD_DUPLICATE_POLICIES = {"reject", "overwrite", "keep_both"}
MAX_FILE_NAME_LENGTH = 255


@dataclass
class DuplicateMatch:
    document: Document
    same_name: bool
    same_hash: bool


@dataclass
class DuplicateCheck:
    requested_file_name: str
    file_hash: str | None
    matches: list[DuplicateMatch]

    @property
    def has_duplicate(self) -> bool:
        return bool(self.matches)

    @property
    def same_name(self) -> bool:
        return any(match.same_name for match in self.matches)

    @property
    def same_hash(self) -> bool:
        return any(match.same_hash for match in self.matches)


@dataclass
class DocumentUploadResult:
    document: Document
    duplicate_check: DuplicateCheck
    action: str


class DocumentDuplicateError(Exception):
    def __init__(self, duplicate_check: DuplicateCheck):
        self.duplicate_check = duplicate_check
        super().__init__("文档已存在")


class DocumentUploadPolicyError(ValueError):
    pass


def normalize_upload_file_name(file_name: str | None) -> str:
    name = Path(file_name or "").name.strip()
    if not name:
        name = "upload.bin"
    return _fit_file_name(name)


def file_name_key(file_name: str | None) -> str:
    return unicodedata.normalize("NFC", file_name or "").strip().casefold()


def make_copy_file_name(file_name: str, index: int) -> str:
    path = Path(file_name)
    suffix = path.suffix
    stem = file_name[: -len(suffix)] if suffix else file_name
    marker = f" ({index})"
    max_stem_length = max(1, MAX_FILE_NAME_LENGTH - len(marker) - len(suffix))
    return f"{stem[:max_stem_length]}{marker}{suffix}"


async def next_available_active_file_name(db: AsyncSession, file_name: str) -> str:
    candidate = normalize_upload_file_name(file_name)
    if not await active_file_name_exists(db, candidate):
        return candidate
    for index in range(2, 10000):
        candidate = make_copy_file_name(file_name, index)
        if not await active_file_name_exists(db, candidate):
            return candidate
    raise DocumentUploadPolicyError("同名副本过多，请先清理已有文档")


async def active_file_name_exists(db: AsyncSession, file_name: str) -> bool:
    existing_id = await db.scalar(
        select(Document.id)
        .where(
            Document.deleted_at.is_(None),
            func.lower(func.btrim(Document.file_name)) == file_name_key(file_name),
        )
        .limit(1)
    )
    return existing_id is not None


class DocumentUploadService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.minio_service = MinioService()
        self.lifecycle_service = DocumentLifecycleService()

    async def check_duplicates(
        self, db: AsyncSession, file_name: str, file_hash: str | None = None
    ) -> DuplicateCheck:
        safe_file_name = normalize_upload_file_name(file_name)
        normalized_hash = _normalize_file_hash(file_hash)
        conditions = [func.lower(func.btrim(Document.file_name)) == file_name_key(safe_file_name)]
        if normalized_hash:
            conditions.append(Document.file_hash == normalized_hash)

        rows = await db.execute(
            select(Document)
            .where(Document.deleted_at.is_(None), or_(*conditions))
            .order_by(Document.updated_at.desc(), Document.created_at.desc())
        )
        matches: list[DuplicateMatch] = []
        seen: set[str] = set()
        for document in rows.scalars():
            document_id = str(document.id)
            if document_id in seen:
                continue
            seen.add(document_id)
            same_name = file_name_key(document.file_name) == file_name_key(safe_file_name)
            same_hash = bool(normalized_hash and document.file_hash == normalized_hash)
            if same_name or same_hash:
                matches.append(
                    DuplicateMatch(document=document, same_name=same_name, same_hash=same_hash)
                )
        matches.sort(key=lambda item: (not item.same_name, not item.same_hash))
        return DuplicateCheck(
            requested_file_name=safe_file_name,
            file_hash=normalized_hash,
            matches=matches,
        )

    async def save_upload(
        self,
        db: AsyncSession,
        *,
        file_name: str | None,
        content_type: str | None,
        data: bytes,
        title: str | None,
        source_url: str | None,
        created_by: str | None,
        duplicate_policy: str = "reject",
        overwrite_document_id: str | None = None,
    ) -> DocumentUploadResult:
        policy = _normalize_duplicate_policy(duplicate_policy)
        safe_file_name = normalize_upload_file_name(file_name)
        file_hash = await asyncio.to_thread(sha256_bytes, data)

        await self._acquire_file_name_lock(db, safe_file_name)
        duplicate_check = await self.check_duplicates(db, safe_file_name, file_hash)

        if duplicate_check.has_duplicate and policy == "reject":
            raise DocumentDuplicateError(duplicate_check)

        if policy == "overwrite" and duplicate_check.has_duplicate:
            target = _overwrite_target(duplicate_check, overwrite_document_id)
            document = await self._overwrite_document(
                db,
                target,
                safe_file_name=safe_file_name,
                content_type=content_type,
                data=data,
                file_hash=file_hash,
                title=title,
                source_url=source_url,
                created_by=created_by,
            )
            return DocumentUploadResult(document, duplicate_check, "overwritten")

        if policy == "overwrite" and not duplicate_check.has_duplicate:
            policy = "reject"

        final_file_name = safe_file_name
        if policy == "keep_both":
            final_file_name = await next_available_active_file_name(db, safe_file_name)

        document = await self._create_document(
            db,
            safe_file_name=final_file_name,
            content_type=content_type,
            data=data,
            file_hash=file_hash,
            title=title,
            source_url=source_url,
            created_by=created_by,
        )
        action = "copied" if final_file_name != safe_file_name else "created"
        return DocumentUploadResult(document, duplicate_check, action)

    async def _create_document(
        self,
        db: AsyncSession,
        *,
        safe_file_name: str,
        content_type: str | None,
        data: bytes,
        file_hash: str,
        title: str | None,
        source_url: str | None,
        created_by: str | None,
    ) -> Document:
        object_key: str | None = None
        try:
            object_key, _ = await asyncio.to_thread(
                self.minio_service.upload_bytes,
                self.settings.minio_documents_bucket,
                data,
                safe_file_name,
                content_type,
            )
            document = Document(
                title=title or safe_file_name,
                file_name=safe_file_name,
                file_ext=Path(safe_file_name).suffix.lower(),
                mime_type=content_type,
                file_size=len(data),
                file_hash=file_hash,
                storage_bucket=self.settings.minio_documents_bucket,
                storage_object_key=object_key,
                source_url=source_url,
                preview_url=None,
                download_url=None,
                status="uploaded",
                created_by=created_by,
            )
            db.add(document)
            await db.flush()
            await self.lifecycle_service.mark_knowledge_base_changed(
                db, document_id=str(document.id), reason="document_uploaded"
            )
            await db.commit()
            await db.refresh(document)
            return document
        except IntegrityError as exc:
            await db.rollback()
            self._remove_object(self.settings.minio_documents_bucket, object_key)
            raise DocumentDuplicateError(await self.check_duplicates(db, safe_file_name, file_hash)) from exc
        except Exception:
            await db.rollback()
            self._remove_object(self.settings.minio_documents_bucket, object_key)
            raise

    async def _overwrite_document(
        self,
        db: AsyncSession,
        target: Document,
        *,
        safe_file_name: str,
        content_type: str | None,
        data: bytes,
        file_hash: str,
        title: str | None,
        source_url: str | None,
        created_by: str | None,
    ) -> Document:
        document_id = str(target.id)

        object_key: str | None = None
        old_objects = await self.lifecycle_service.storage_objects_for_document(db, target)
        try:
            object_key, _ = await asyncio.to_thread(
                self.minio_service.upload_bytes,
                self.settings.minio_documents_bucket,
                data,
                safe_file_name,
                content_type,
            )
            await self.lifecycle_service.prepare_document_replacement(db, target)
            now = datetime.now(timezone.utc)
            target.title = title or safe_file_name
            target.file_name = safe_file_name
            target.file_ext = Path(safe_file_name).suffix.lower()
            target.mime_type = content_type
            target.file_size = len(data)
            target.file_hash = file_hash
            target.storage_bucket = self.settings.minio_documents_bucket
            target.storage_object_key = object_key
            target.source_url = source_url
            target.preview_url = None
            target.download_url = None
            target.status = "uploaded"
            target.parse_quality_score = None
            target.error_message = None
            target.created_by = created_by
            target.deleted_at = None
            target.updated_at = now
            await self.lifecycle_service.mark_knowledge_base_changed(
                db, document_id=document_id, reason="document_replaced"
            )
            await db.commit()
            await db.refresh(target)
        except IntegrityError as exc:
            await db.rollback()
            self._remove_object(self.settings.minio_documents_bucket, object_key)
            raise DocumentDuplicateError(await self.check_duplicates(db, safe_file_name, file_hash)) from exc
        except Exception:
            await db.rollback()
            self._remove_object(self.settings.minio_documents_bucket, object_key)
            raise

        self.lifecycle_service.remove_storage_objects(
            [ref for ref in old_objects if ref.object_key != object_key],
            self.minio_service,
        )
        return target

    async def _acquire_file_name_lock(self, db: AsyncSession, file_name: str) -> None:
        bind = db.get_bind()
        if bind.dialect.name != "postgresql":
            return
        await db.execute(
            text(
                """
                SELECT pg_advisory_xact_lock(
                  hashtextextended(CAST(:lock_key AS text), 0)
                )
                """
            ),
            {"lock_key": f"document-upload:{file_name_key(file_name)}"},
        )

    def _remove_object(self, bucket: str, object_key: str | None) -> None:
        if not object_key:
            return
        self.minio_service.remove_object(bucket, object_key)


def _fit_file_name(file_name: str) -> str:
    if len(file_name) <= MAX_FILE_NAME_LENGTH:
        return file_name
    path = Path(file_name)
    suffix = path.suffix
    stem = file_name[: -len(suffix)] if suffix else file_name
    max_stem_length = max(1, MAX_FILE_NAME_LENGTH - len(suffix))
    return f"{stem[:max_stem_length]}{suffix}"


def _normalize_file_hash(file_hash: str | None) -> str | None:
    normalized = str(file_hash or "").strip().lower()
    return normalized or None


def _normalize_duplicate_policy(policy: str) -> UploadDuplicatePolicy:
    normalized = str(policy or "reject").strip().lower()
    if normalized not in UPLOAD_DUPLICATE_POLICIES:
        raise DocumentUploadPolicyError("duplicate_policy 只能是 reject、overwrite 或 keep_both")
    return normalized  # type: ignore[return-value]


def _overwrite_target(
    duplicate_check: DuplicateCheck, overwrite_document_id: str | None
) -> Document:
    if overwrite_document_id:
        for match in duplicate_check.matches:
            if str(match.document.id) == str(overwrite_document_id) and match.same_name:
                return match.document
        raise DocumentUploadPolicyError("只能覆盖同名的已有文档")
    for match in duplicate_check.matches:
        if match.same_name:
            return match.document
    raise DocumentUploadPolicyError("未找到可覆盖的同名文档")
