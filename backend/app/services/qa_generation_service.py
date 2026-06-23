import json
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.json_utils import to_jsonable
from app.db.models import Document, DocumentJob, DocumentParseResult, QaPair
from app.services.document_state import indexing_blocker
from app.services.model_service import ModelService
from app.services.qa_embedding_service import QaEmbeddingService
from app.services.redis_service import RedisService


class QaGenerationService:
    def __init__(self) -> None:
        self.model_service = ModelService()
        self.redis_service = RedisService()

    async def generate_from_document(
        self,
        db: AsyncSession,
        document_id: str,
        count: int = 10,
        auto_enable: bool = True,
    ) -> None:
        job = DocumentJob(
            document_id=document_id,
            job_type="qa_generate",
            status="running",
            progress=5,
            message="开始生成 QA",
            started_at=datetime.now(timezone.utc),
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        try:
            document = await db.scalar(select(Document).where(Document.id == document_id))
            parse_result = await db.scalar(
                select(DocumentParseResult).where(DocumentParseResult.document_id == document_id)
            )
            if document is None or parse_result is None:
                raise ValueError("文档或解析结果不存在")
            blocker = indexing_blocker(document, parse_result.parse_meta)
            if blocker:
                await db.execute(
                    update(DocumentJob)
                    .where(DocumentJob.id == job.id)
                    .values(
                        status="skipped",
                        progress=100,
                        message=blocker,
                        finished_at=datetime.now(timezone.utc),
                    )
                )
                await db.commit()
                await self._cache_job(job.id, document_id, "skipped", 100, blocker)
                return
            content = parse_result.content_text[:12000]
            document_name = self._display_document_title(document)
            prompt = (
                f"请基于以下文档内容生成 {count} 组高质量问答对。"
                "只输出合法 JSON 数组，每项包含 question、answer、tags。"
                "问题要贴近用户真实会问的问题；答案必须基于文档原文，避免编造。"
                "如果涉及金额、日期、主体、条款，请在答案中写清楚。\n\n"
                f"文档名：{document_name}\n\n文档内容：\n{content}"
            )
            raw = await self.model_service.complete_text(
                [
                    {"role": "system", "content": "你是知识库 QA 生成助手，只输出合法 JSON。"},
                    {"role": "user", "content": prompt},
                ]
            )
            pairs = self._parse_pairs(raw)[:count]
            created_pairs: list[QaPair] = []
            for item in pairs:
                qa = QaPair(
                    question=item["question"],
                    answer=item["answer"],
                    status="enabled" if auto_enable else "draft",
                    source_document_id=document_id,
                    source_url=document.source_url or document.preview_url or document.download_url,
                    tags=item.get("tags") or [],
                )
                db.add(qa)
                created_pairs.append(qa)
            await db.flush()
            embedding_count = await QaEmbeddingService().sync_pairs(db, created_pairs)
            message = f"已生成 {len(pairs)} 组 QA"
            await db.execute(
                update(DocumentJob)
                .where(DocumentJob.id == job.id)
                .values(
                    status="succeeded",
                    progress=100,
                    message=message,
                    result={"qa_count": len(pairs), "embedding_count": embedding_count},
                    finished_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()
            await self._cache_job(job.id, document_id, "succeeded", 100, message)
        except Exception as exc:
            await db.rollback()
            await db.execute(
                update(DocumentJob)
                .where(DocumentJob.id == job.id)
                .values(
                    status="failed",
                    progress=100,
                    error_message=str(exc),
                    finished_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()
            await self._cache_job(job.id, document_id, "failed", 100, str(exc))

    def _parse_pairs(self, raw: str) -> list[dict]:
        start = raw.find("[")
        end = raw.rfind("]")
        if start >= 0 and end > start:
            raw = raw[start : end + 1]
        data = json.loads(raw)
        pairs: list[dict] = []
        for item in data if isinstance(data, list) else []:
            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()
            if question and answer:
                tags = item.get("tags") or []
                if isinstance(tags, str):
                    tags = [tags]
                pairs.append({"question": question, "answer": answer, "tags": tags})
        return pairs

    async def _cache_job(
        self, job_id: str, document_id: str, status: str, progress: int, message: str
    ) -> None:
        await self.redis_service.set_json(
            f"job:{job_id}:progress",
            to_jsonable(
                {
                    "id": job_id,
                    "document_id": document_id,
                    "job_type": "qa_generate",
                    "status": status,
                    "progress": progress,
                    "message": message,
                }
            ),
            ttl=86400,
        )

    def _display_document_title(self, document: Document) -> str:
        title = document.title or ""
        if not title or title.count("?") >= max(2, len(title) // 2):
            return document.file_name
        return title
