"""QA 向量服务：为标准问答生成 embedding 并同步到向量表。"""

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import QaPair
from app.services.hash_service import sha256_text
from app.services.model_service import ModelService


class QaEmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model_service = ModelService()

    async def sync_one(self, db: AsyncSession, qa_pair_id: str) -> int:
        qa = await db.scalar(select(QaPair).where(QaPair.id == qa_pair_id))
        if qa is None or qa.deleted_at is not None:
            return 0
        return await self.sync_pairs(db, [qa])

    async def sync_pairs(self, db: AsyncSession, qa_pairs: list[QaPair]) -> int:
        pairs = [
            item
            for item in qa_pairs
            if item.deleted_at is None and item.question.strip() and item.answer.strip()
        ]
        if not pairs:
            return 0

        contents = [self._embedding_content(item) for item in pairs]
        embeddings = await self.model_service.embed(contents)
        synced = 0
        for qa, content, embedding in zip(pairs, contents, embeddings, strict=True):
            vector_literal = "[" + ",".join(str(value) for value in embedding) + "]"
            await db.execute(
                text(
                    """
                    INSERT INTO qa_pair_embeddings (qa_pair_id, embedding, embedding_model, content_hash)
                    VALUES (:qa_pair_id, CAST(:embedding AS vector), :embedding_model, :content_hash)
                    ON CONFLICT (qa_pair_id) DO UPDATE SET
                      embedding = CAST(:embedding AS vector),
                      embedding_model = :embedding_model,
                      content_hash = :content_hash,
                      updated_at = now()
                    """
                ),
                {
                    "qa_pair_id": str(qa.id),
                    "embedding": vector_literal,
                    "embedding_model": self.settings.embedding_model,
                    "content_hash": sha256_text(content),
                },
            )
            synced += 1
        return synced

    def _embedding_content(self, qa: QaPair) -> str:
        return f"{qa.question.strip()}\n\n{qa.answer.strip()}"
