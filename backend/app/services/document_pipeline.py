"""
文档处理流水线。串联 MinIO 读取、解析、切片、向量化、任务进度更新和文档状态流转。
"""

import asyncio
from datetime import datetime, timezone
import mimetypes
from pathlib import Path

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.json_utils import to_jsonable
from app.db.models import Document, DocumentChunk, DocumentJob, DocumentParseResult
from app.services.archive_import_service import ArchiveImportService
from app.services.chunk_service import ChunkService
from app.services.document_lifecycle_service import DocumentLifecycleService
from app.services.document_state import indexing_blocker, parse_terminal_message, parse_terminal_status
from app.services.hash_service import sha256_bytes, sha256_text
from app.services.minio_service import MinioService
from app.services.model_service import ModelService
from app.services.parse_service import ParseService
from app.services.privacy_service import PrivacyService
from app.services.redis_service import RedisService
from app.services.document_upload_service import (
    next_available_active_file_name,
    normalize_upload_file_name,
)


class DocumentPipeline:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.parse_service = ParseService()
        self.chunk_service = ChunkService()
        self.model_service = ModelService()
        self.minio_service = MinioService()
        self.redis_service = RedisService()
        self.archive_import_service = ArchiveImportService()
        self.lifecycle_service = DocumentLifecycleService()
        self.privacy_service = PrivacyService()

    async def run_full_pipeline_from_storage(
        self, db: AsyncSession, document_id: str, job_id: str | None = None
    ) -> None:
        document = await db.scalar(select(Document).where(Document.id == document_id))
        if document is None:
            raise ValueError("文档不存在")
        file_bytes = await asyncio.to_thread(
            self.minio_service.read_bytes,
            document.storage_bucket,
            document.storage_object_key,
        )
        await self.run_full_pipeline(db, document_id, file_bytes, job_id=job_id)

    async def run_full_pipeline(
        self, db: AsyncSession, document_id: str, file_bytes: bytes, job_id: str | None = None
    ) -> None:
        use_tracking_job = job_id is not None
        if use_tracking_job:
            parse_job_id = str(job_id)
        else:
            parse_job = await self._create_job(db, document_id, "parse")
            parse_job_id = str(parse_job.id)
        try:
            await self._set_job(db, parse_job_id, "running", 5, "开始解析")
            document = await db.scalar(select(Document).where(Document.id == document_id))
            if document is None:
                raise ValueError("文档不存在")

            # 第一阶段：解析原文并把解析产物保存到数据库和 MinIO。
            parsed = await asyncio.to_thread(self.parse_service.parse, document.file_name, file_bytes)
            # 隐私脱敏：对解析后的文本做正则兜底脱敏，从源头切断敏感信息入库
            privacy_result = self.privacy_service.mask(parsed.text)
            if privacy_result.masked_count > 0:
                parsed.text = privacy_result.text
                if parsed.markdown:
                    parsed.markdown = self.privacy_service.mask(parsed.markdown).text
            await self._store_parse_assets(document_id, parsed)
            quality = await asyncio.to_thread(self.parse_service.quality_score, parsed)
            object_key = f"parsed/{document_id}/content.md"
            await asyncio.to_thread(
                self.minio_service.upload_text,
                self.settings.minio_parsed_bucket,
                parsed.markdown or parsed.text,
                object_key,
            )
            await self._store_parse_result(db, document_id, parsed, quality, object_key)
            document_status = parse_terminal_status(parsed.meta)
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(
                    status=document_status,
                    parse_quality_score=quality,
                    error_message=None,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            if parsed.meta.get("skip_chunking"):
                await self._clear_indexed_content(db, document_id)
            await db.commit()
            if parsed.meta.get("skip_chunking"):
                # 旧 Office、压缩包等容器类文档可能只记录状态，不直接进入检索索引。
                await self._set_job(
                    db,
                    parse_job_id,
                    "succeeded",
                    100,
                    parse_terminal_message(parsed.meta),
                )
                return
            if use_tracking_job:
                await self._set_job(db, parse_job_id, "running", 35, "解析完成，开始切片")
            else:
                await self._set_job(db, parse_job_id, "succeeded", 100, "解析完成")
        except Exception as exc:
            await self._fail(db, document_id, parse_job_id, exc)
            return

        if use_tracking_job:
            chunk_job_id = str(job_id)
        else:
            chunk_job = await self._create_job(db, document_id, "chunk")
            chunk_job_id = str(chunk_job.id)
        try:
            # 第二阶段：根据解析文本重建 chunk，旧 chunk 和向量会在生命周期服务里清理。
            await self._set_job(db, chunk_job_id, "running", 40 if use_tracking_job else 5, "开始切片")
            chunk_count = await self._chunk_document(db, document_id)
            if chunk_count <= 0:
                raise ValueError("切片结果为空，未生成可向量化内容")
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(status="chunked", updated_at=datetime.now(timezone.utc))
            )
            await self.lifecycle_service.mark_knowledge_base_changed(
                db, document_id=document_id, reason="document_chunked"
            )
            await db.commit()
            if use_tracking_job:
                await self._set_job(db, chunk_job_id, "running", 65, "切片完成，开始向量化")
            else:
                await self._set_job(db, chunk_job_id, "succeeded", 100, "切片完成")
        except Exception as exc:
            await self._fail(db, document_id, chunk_job_id, exc)
            return

        if use_tracking_job:
            embed_job_id = str(job_id)
        else:
            embed_job = await self._create_job(db, document_id, "embed")
            embed_job_id = str(embed_job.id)
        try:
            # 第三阶段：为每个有效 chunk 生成 embedding，完成后文档才变为 indexed。
            await self._set_job(db, embed_job_id, "running", 70 if use_tracking_job else 5, "开始向量化")
            embedded_count = await self._embed_document(
                db,
                document_id,
                embed_job_id,
                progress_start=70 if use_tracking_job else 0,
            )
            if embedded_count <= 0:
                raise ValueError("没有可向量化的切片")
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(status="indexed", updated_at=datetime.now(timezone.utc))
            )
            await self.lifecycle_service.mark_knowledge_base_changed(
                db, document_id=document_id, reason="document_indexed"
            )
            await db.commit()
            await self._set_job(db, embed_job_id, "succeeded", 100, "向量化完成")
        except Exception as exc:
            await self._fail(db, document_id, embed_job_id, exc)

    async def run_chunk_and_embed(self, db: AsyncSession, document_id: str, job_id: str | None = None) -> None:
        use_tracking_job = job_id is not None
        if use_tracking_job:
            chunk_job_id = str(job_id)
        else:
            chunk_job = await self._create_job(db, document_id, "chunk")
            chunk_job_id = str(chunk_job.id)
        try:
            await self._set_job(db, chunk_job_id, "running", 5, "开始重新切片")
            blocker = await self._indexing_blocker(db, document_id)
            if blocker:
                await self._set_job(db, chunk_job_id, "skipped", 100, blocker)
                return
            chunk_count = await self._chunk_document(db, document_id)
            if chunk_count <= 0:
                raise ValueError("切片结果为空，未生成可向量化内容")
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(status="chunked", updated_at=datetime.now(timezone.utc))
            )
            await self.lifecycle_service.mark_knowledge_base_changed(
                db, document_id=document_id, reason="document_rechunked"
            )
            await db.commit()
            if use_tracking_job:
                await self._set_job(db, chunk_job_id, "running", 50, "重新切片完成，开始重新向量化")
            else:
                await self._set_job(db, chunk_job_id, "succeeded", 100, "重新切片完成")
        except Exception as exc:
            await self._fail(db, document_id, chunk_job_id, exc)
            return

        await self.run_embed_only(db, document_id, job_id=job_id)

    async def run_embed_only(self, db: AsyncSession, document_id: str, job_id: str | None = None) -> None:
        if job_id is not None:
            embed_job_id = str(job_id)
        else:
            embed_job = await self._create_job(db, document_id, "embed")
            embed_job_id = str(embed_job.id)
        try:
            await self._set_job(db, embed_job_id, "running", 55 if job_id is not None else 5, "开始重新向量化")
            blocker = await self._indexing_blocker(db, document_id)
            if blocker:
                await self._set_job(db, embed_job_id, "skipped", 100, blocker)
                return
            await self._ensure_parse_result(db, document_id)
            existing_chunk_count = await self._active_chunk_count(db, document_id)
            if existing_chunk_count <= 0:
                raise ValueError("当前文档没有可向量化的切片，请先重新解析或重新切片")
            await self.lifecycle_service.clear_embeddings(
                db,
                document_id,
                reason="document_reembed_started",
            )
            await db.commit()
            embedded_count = await self._embed_document(
                db,
                document_id,
                embed_job_id,
                progress_start=55 if job_id is not None else 0,
            )
            if embedded_count <= 0:
                raise ValueError("没有可向量化的切片")
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(status="indexed", updated_at=datetime.now(timezone.utc))
            )
            await self.lifecycle_service.mark_knowledge_base_changed(
                db, document_id=document_id, reason="document_reindexed"
            )
            await db.commit()
            await self._set_job(db, embed_job_id, "succeeded", 100, "重新向量化完成")
        except Exception as exc:
            await self._fail(db, document_id, embed_job_id, exc)

    async def run_convert_office(self, db: AsyncSession, document_id: str) -> None:
        job = await self._create_job(db, document_id, "convert_office")
        job_id = str(job.id)
        try:
            await self._set_job(db, job_id, "running", 5, "开始转换旧 Office 文件")
            document = await db.scalar(select(Document).where(Document.id == document_id))
            if document is None:
                raise ValueError("文档不存在")
            original_bytes = await asyncio.to_thread(
                self.minio_service.read_bytes,
                document.storage_bucket,
                document.storage_object_key,
            )
            converted_name, converted_bytes, convert_meta = await asyncio.to_thread(
                self.parse_service.convert_legacy_office_file,
                document.file_name,
                original_bytes,
            )
            await self._set_job(db, job_id, "running", 45, f"已转换为 {converted_name}")
            converted_document = await self._create_child_document(
                db,
                parent=document,
                file_name=converted_name,
                data=converted_bytes,
                title=f"{self._display_document_title(document)}（转换）",
            )
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(status="converted", error_message=None, updated_at=datetime.now(timezone.utc))
            )
            await self._set_job(
                db,
                job_id,
                "succeeded",
                100,
                "转换完成，已创建转换后的文档并开始入库",
                result={
                    "source_document_id": str(document.id),
                    "source_document_file_name": document.file_name,
                    "source_url": document.source_url,
                    "converted_document_id": str(converted_document.id),
                    "converted_file_name": converted_name,
                    "converted_preview_url": converted_document.preview_url,
                    **convert_meta,
                },
            )
            await self.run_full_pipeline(db, str(converted_document.id), converted_bytes)
        except Exception as exc:
            await self._fail(db, document_id, job_id, exc, document_status="needs_conversion")

    async def run_extract_archive(self, db: AsyncSession, document_id: str) -> None:
        job = await self._create_job(db, document_id, "extract_import")
        job_id = str(job.id)
        try:
            await self._set_job(db, job_id, "running", 5, "开始安全解压压缩包")
            document = await db.scalar(select(Document).where(Document.id == document_id))
            if document is None:
                raise ValueError("文档不存在")
            archive_bytes = await asyncio.to_thread(
                self.minio_service.read_bytes,
                document.storage_bucket,
                document.storage_object_key,
            )
            result = await asyncio.to_thread(
                self.archive_import_service.extract_supported_entries,
                document.file_name,
                archive_bytes,
            )
            if not result.entries:
                skipped_summary = "; ".join(
                    f"{item.get('name')}: {item.get('reason')}" for item in result.skipped[:5]
                )
                raise ValueError(f"压缩包内没有可导入文件。{skipped_summary}")

            imported_documents: list[tuple[Document, bytes, str]] = []
            total = len(result.entries)
            for index, entry in enumerate(result.entries, start=1):
                imported = await self._create_child_document(
                    db,
                    parent=document,
                    file_name=entry.file_name,
                    data=entry.data,
                    title=f"{self._display_document_title(document)} / {entry.name}",
                )
                imported_documents.append((imported, entry.data, entry.name))
                progress = min(80, 10 + int(index / total * 70))
                await self._set_job(db, job_id, "running", progress, f"已导入 {index}/{total} 个内部文件")

            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(status="extracted", error_message=None, updated_at=datetime.now(timezone.utc))
            )
            await self._set_job(
                db,
                job_id,
                "succeeded",
                100,
                f"解压导入完成，已创建 {len(imported_documents)} 个文档",
                result={
                    "archive_document_id": str(document.id),
                    "archive_file_name": document.file_name,
                    "archive_source_url": document.source_url,
                    "imported_documents": [
                        {
                            "document_id": str(item.id),
                            "file_name": item.file_name,
                            "title": item.title,
                            "file_size": item.file_size,
                            "preview_url": item.preview_url,
                            "archive_entry_name": entry_name,
                        }
                        for item, _, entry_name in imported_documents
                    ],
                    "imported_document_ids": [str(item.id) for item, _, _ in imported_documents],
                    "imported_count": len(imported_documents),
                    "skipped": result.skipped,
                },
            )
            for imported, data, _ in imported_documents:
                await self.run_full_pipeline(db, str(imported.id), data)
        except Exception as exc:
            await self._fail(db, document_id, job_id, exc)

    async def _chunk_document(self, db: AsyncSession, document_id: str) -> int:
        parse_result = await db.scalar(
            select(DocumentParseResult).where(DocumentParseResult.document_id == document_id)
        )
        if parse_result is None:
            raise ValueError("解析结果不存在")
        await self.lifecycle_service.clear_indexed_content(
            db,
            document_id,
            reason="document_chunks_rebuilt",
            bump_version=False,
        )
        chunks = await asyncio.to_thread(self.chunk_service.split, parse_result.content_text, parse_result.parse_meta)
        if not chunks:
            return 0
        for chunk in chunks:
            db.add(
                DocumentChunk(
                    document_id=document_id,
                    chunk_no=chunk.chunk_no,
                    chunk_type=chunk.chunk_type,
                    content=chunk.content,
                    content_hash=chunk.content_hash,
                    char_count=len(chunk.content),
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    section_path=chunk.section_path,
                    metadata_=chunk.metadata,
                )
            )
        await db.flush()
        # 父子切片：按 section_path 分组，同一章节的多个子切片生成一个父级摘要切片
        await self._build_parent_chunks(db, document_id)
        await db.execute(
            text(
                """
                UPDATE document_chunks
                SET search_vector = to_tsvector('simple', content)
                WHERE document_id = :document_id
                """
            ),
            {"document_id": document_id},
        )
        return len(chunks)

    async def _store_parse_result(
        self,
        db: AsyncSession,
        document_id: str,
        parsed,
        quality: float,
        object_key: str,
    ) -> None:
        existing = await db.scalar(
            select(DocumentParseResult).where(DocumentParseResult.document_id == document_id)
        )
        if existing:
            existing.parser_name = str(parsed.meta.get("parser", "unknown"))
            existing.content_text = parsed.text
            existing.content_md = parsed.markdown
            existing.content_object_key = object_key
            existing.page_count = parsed.page_count
            existing.quality_score = quality
            existing.parse_meta = parsed.meta
        else:
            db.add(
                DocumentParseResult(
                    document_id=document_id,
                    parser_name=str(parsed.meta.get("parser", "unknown")),
                    content_text=parsed.text,
                    content_md=parsed.markdown,
                    content_object_key=object_key,
                    page_count=parsed.page_count,
                    quality_score=quality,
                    parse_meta=parsed.meta,
                )
            )

    async def _store_parse_assets(self, document_id: str, parsed) -> None:
        assets = list(getattr(parsed, "assets", []) or [])
        if not assets:
            return
        stored_assets: list[dict] = []
        for asset in assets:
            image_id = str(asset.get("image_id") or "")
            data = asset.get("data")
            if not image_id or not isinstance(data, bytes) or not data:
                continue
            object_key, _ = await asyncio.to_thread(
                self.minio_service.upload_bytes,
                self.settings.minio_preview_bucket,
                data,
                str(asset.get("file_name") or f"{image_id}.png"),
                str(asset.get("content_type") or "application/octet-stream"),
            )
            bucket = self.settings.minio_preview_bucket
            parsed.text = parsed.text.replace(f"__RAG_IMAGE_BUCKET_{image_id}__", bucket)
            parsed.text = parsed.text.replace(f"__RAG_IMAGE_OBJECT_KEY_{image_id}__", object_key)
            parsed.markdown = (parsed.markdown or "").replace(f"__RAG_IMAGE_BUCKET_{image_id}__", bucket)
            parsed.markdown = parsed.markdown.replace(f"__RAG_IMAGE_OBJECT_KEY_{image_id}__", object_key)
            stored_assets.append(
                {
                    key: value
                    for key, value in asset.items()
                    if key != "data"
                }
                | {
                    "bucket": bucket,
                    "object_key": object_key,
                }
            )
        if stored_assets:
            parsed.meta = {
                **parsed.meta,
                "image_assets": stored_assets,
                "image_asset_count": len(stored_assets),
            }

    async def _build_parent_chunks(self, db: AsyncSession, document_id: str) -> None:
        rows = await db.execute(
            text(
                """
                SELECT id, chunk_no, content, page_start, page_end, section_path
                FROM document_chunks
                WHERE document_id = :document_id
                  AND is_active = true
                  AND parent_chunk_id IS NULL
                  AND section_path IS NOT NULL
                  AND section_path != ''
                ORDER BY section_path, chunk_no
                """
            ),
            {"document_id": document_id},
        )
        child_chunks = [dict(row._mapping) for row in rows]
        # 按 section_path 分组
        groups: dict[str, list[dict]] = {}
        for item in child_chunks:
            path = str(item["section_path"])
            groups.setdefault(path, []).append(item)
        for path, items in groups.items():
            if len(items) < 2:
                continue  # 只有一个切片的不需要父级
            # 生成父级内容：章节路径 + 各子切片摘要
            parts: list[str] = [f"章节：{path}"]
            for item in items:
                content = str(item["content"])
                summary = content[:200].strip()
                if len(content) > 200:
                    summary += "..."
                page_info = ""
                if item.get("page_start"):
                    page_info = f" (第{item['page_start']}页)"
                parts.append(f"- {summary}{page_info}")
            parent_content = "\n\n".join(parts)
            page_start = min((item.get("page_start") for item in items if item.get("page_start")), default=None)
            page_end = max((item.get("page_end") for item in items if item.get("page_end")), default=None)
            parent_chunk = DocumentChunk(
                document_id=document_id,
                chunk_no=0,
                chunk_type="parent",
                content=parent_content,
                content_hash=sha256_text(parent_content),
                char_count=len(parent_content),
                page_start=page_start,
                page_end=page_end,
                section_path=path,
                metadata_={"section": path, "child_count": len(items), "parent_summary": True},
            )
            db.add(parent_chunk)
            await db.flush()
            # 更新子切片的 parent_chunk_id
            child_ids = [str(item["id"]) for item in items]
            if child_ids:
                await db.execute(
                    text(
                        """
                        UPDATE document_chunks
                        SET parent_chunk_id = :parent_id
                        WHERE id = ANY(CAST(:child_ids AS uuid[]))
                        """
                    ),
                    {"parent_id": str(parent_chunk.id), "child_ids": child_ids},
                )
        await db.flush()

    async def _embed_document(
        self,
        db: AsyncSession,
        document_id: str,
        job_id: str,
        progress_start: int = 0,
        progress_end: int = 95,
    ) -> int:
        rows = await db.execute(
            text(
                """
                SELECT c.id, c.content, c.content_hash
                FROM document_chunks c
                LEFT JOIN chunk_embeddings e ON e.chunk_id = c.id
                WHERE c.document_id = :document_id AND e.id IS NULL
                ORDER BY c.chunk_no
                """
            ),
            {"document_id": document_id},
        )
        chunks = [dict(row._mapping) for row in rows]
        if not chunks:
            return 0
        embedded_count = 0
        batch_size = max(1, self.settings.embedding_batch_size)
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            embeddings = await self.model_service.embed([item["content"] for item in batch])
            insert_rows = []
            for item, embedding in zip(batch, embeddings, strict=True):
                vector_literal = "[" + ",".join(str(value) for value in embedding) + "]"
                insert_rows.append(
                    {
                        "chunk_id": item["id"],
                        "document_id": document_id,
                        "embedding": vector_literal,
                        "embedding_model": self.settings.embedding_model,
                        "content_hash": item["content_hash"],
                    }
                )
            if insert_rows:
                await db.execute(
                    text(
                        """
                        INSERT INTO chunk_embeddings (
                          chunk_id, document_id, embedding, embedding_model,
                          embedding_provider, content_hash
                        )
                        VALUES (
                          :chunk_id, :document_id, CAST(:embedding AS vector),
                          :embedding_model, 'api', :content_hash
                        )
                        ON CONFLICT (chunk_id) DO NOTHING
                        """
                    ),
                    insert_rows,
                )
                embedded_count += len(insert_rows)
            progress_range = max(1, progress_end - progress_start)
            progress = min(
                progress_end,
                progress_start + int(((start + len(batch)) / len(chunks)) * progress_range),
            )
            await db.commit()
            await self._set_job(db, job_id, "running", progress, f"已向量化 {start + len(batch)}/{len(chunks)}")
        return embedded_count

    async def _indexing_blocker(self, db: AsyncSession, document_id: str) -> str | None:
        document = await db.scalar(select(Document).where(Document.id == document_id))
        if document is None:
            raise ValueError("文档不存在")
        parse_result = await db.scalar(
            select(DocumentParseResult).where(DocumentParseResult.document_id == document_id)
        )
        parse_meta = parse_result.parse_meta if parse_result else None
        return indexing_blocker(document, parse_meta)

    async def _ensure_parse_result(self, db: AsyncSession, document_id: str) -> DocumentParseResult:
        parse_result = await db.scalar(
            select(DocumentParseResult).where(DocumentParseResult.document_id == document_id)
        )
        if parse_result is None:
            raise ValueError("解析结果不存在，请先重新解析")
        return parse_result

    async def _active_chunk_count(self, db: AsyncSession, document_id: str) -> int:
        count = await db.scalar(
            text(
                """
                SELECT count(*)
                FROM document_chunks
                WHERE document_id = :document_id AND is_active = true
                """
            ),
            {"document_id": document_id},
        )
        return int(count or 0)

    async def _clear_indexed_content(self, db: AsyncSession, document_id: str) -> None:
        await self.lifecycle_service.clear_indexed_content(
            db,
            document_id,
            reason="document_index_cleared",
        )

    async def _create_child_document(
        self,
        db: AsyncSession,
        parent: Document,
        file_name: str,
        data: bytes,
        title: str,
    ) -> Document:
        safe_file_name = await next_available_active_file_name(
            db, normalize_upload_file_name(file_name or "imported.bin")
        )
        content_type = mimetypes.guess_type(safe_file_name)[0] or "application/octet-stream"
        object_key, public_url = await asyncio.to_thread(
            self.minio_service.upload_bytes,
            self.settings.minio_documents_bucket,
            data,
            safe_file_name,
            content_type,
        )
        child = Document(
            title=title,
            file_name=safe_file_name,
            file_ext=Path(safe_file_name).suffix.lower(),
            mime_type=content_type,
            file_size=len(data),
            file_hash=await asyncio.to_thread(sha256_bytes, data),
            storage_bucket=self.settings.minio_documents_bucket,
            storage_object_key=object_key,
            source_url=None,
            preview_url=public_url,
            download_url=public_url,
            status="uploaded",
            created_by=str(parent.created_by) if parent.created_by else None,
        )
        db.add(child)
        await db.flush()
        await self.lifecycle_service.mark_knowledge_base_changed(
            db, document_id=str(child.id), reason="document_uploaded"
        )
        await db.commit()
        await db.refresh(child)
        return child

    async def _create_job(self, db: AsyncSession, document_id: str, job_type: str) -> DocumentJob:
        job = DocumentJob(document_id=document_id, job_type=job_type, status="pending", progress=0)
        db.add(job)
        await db.commit()
        await db.refresh(job)
        await self._cache_job(job)
        return job

    async def _set_job(
        self,
        db: AsyncSession,
        job_id: str,
        status: str,
        progress: int,
        message: str,
        error_message: str | None = None,
        result: dict | None = None,
    ) -> None:
        values = {
            "status": status,
            "progress": progress,
            "message": message,
            "error_message": error_message,
            "updated_at": datetime.now(timezone.utc),
        }
        if status == "running":
            values["started_at"] = datetime.now(timezone.utc)
        if status in {"succeeded", "failed", "canceled", "skipped"}:
            values["finished_at"] = datetime.now(timezone.utc)
        if result is not None:
            values["result"] = to_jsonable(result)
        await db.execute(update(DocumentJob).where(DocumentJob.id == job_id).values(**values))
        await db.commit()
        job = await db.scalar(select(DocumentJob).where(DocumentJob.id == job_id))
        if job:
            await self._cache_job(job)

    async def _fail(
        self,
        db: AsyncSession,
        document_id: str,
        job_id: str,
        exc: Exception,
        document_status: str = "failed",
    ) -> None:
        await db.rollback()
        message = str(exc)
        await db.execute(
            update(Document)
            .where(Document.id == document_id)
            .values(status=document_status, error_message=message, updated_at=datetime.now(timezone.utc))
        )
        await db.commit()
        await self._set_job(db, job_id, "failed", 100, "处理失败", message)

    async def _cache_job(self, job: DocumentJob) -> None:
        await self.redis_service.set_json(
            f"job:{job.id}:progress",
            to_jsonable(
                {
                    "id": job.id,
                    "document_id": job.document_id,
                    "job_type": job.job_type,
                    "status": job.status,
                    "progress": job.progress,
                    "message": job.message,
                    "error_message": job.error_message,
                    "result": job.result,
                }
            ),
            ttl=86400,
        )

    def _display_document_title(self, document: Document) -> str:
        title = document.title or ""
        if not title or title.count("?") >= max(2, len(title) // 2):
            return document.file_name
        return title


def supported_file(file_name: str) -> bool:
    return Path(file_name).suffix.lower() in {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".xlsm",
        ".txt",
        ".md",
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".zip",
        ".rar",
    }
