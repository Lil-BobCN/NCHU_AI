"""
检索调试接口。用于手动触发检索和查看检索日志，方便排查召回质量。
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.config import get_settings
from app.core.responses import ok
from app.db.models import Admin, RetrievalLog
from app.db.session import get_db
from app.services.retrieval_service import RetrievalService


router = APIRouter(prefix="/retrieval", tags=["retrieval"])


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=30, ge=1)
    rerank_top_k: int = Field(default=5, ge=1)
    document_ids: list[str] | None = None
    enable_rewrite: bool = True
    enable_qa_recall: bool = True
    enable_keyword_recall: bool = True
    enable_vector_recall: bool = True

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        settings = get_settings()
        value = value.strip()
        if len(value) > settings.retrieval_max_query_chars:
            raise ValueError(f"检索问题长度不能超过 {settings.retrieval_max_query_chars} 字符")
        return value

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, value: int) -> int:
        settings = get_settings()
        if value > settings.retrieval_max_top_k:
            raise ValueError(f"top_k 不能超过 {settings.retrieval_max_top_k}")
        return value

    @field_validator("rerank_top_k")
    @classmethod
    def validate_rerank_top_k(cls, value: int) -> int:
        settings = get_settings()
        if value > settings.retrieval_max_rerank_top_k:
            raise ValueError(f"rerank_top_k 不能超过 {settings.retrieval_max_rerank_top_k}")
        return value


@router.post("/search")
async def search(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    result = await RetrievalService().search(
        db,
        payload.query,
        top_k=payload.top_k,
        rerank_top_k=payload.rerank_top_k,
        document_ids=payload.document_ids,
        enable_vector_recall=payload.enable_vector_recall,
        enable_keyword_recall=payload.enable_keyword_recall,
        enable_qa_recall=payload.enable_qa_recall,
    )
    return ok(result)


@router.get("/logs")
async def list_logs(
    keyword: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    query = select(RetrievalLog)
    count_query = select(func.count()).select_from(RetrievalLog)
    if keyword:
        query = query.where(RetrievalLog.raw_query.ilike(f"%{keyword}%"))
        count_query = count_query.where(RetrievalLog.raw_query.ilike(f"%{keyword}%"))
    total = await db.scalar(count_query)
    rows = await db.execute(
        query.order_by(RetrievalLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    return ok(
        {
            "items": [
                {
                    "id": str(item.id),
                    "raw_query": item.raw_query,
                    "rewritten_query": item.rewritten_query,
                    "latency_ms": item.latency_ms,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in rows.scalars()
            ],
            "page": page,
            "page_size": page_size,
            "total": total or 0,
        }
    )


@router.get("/logs/{log_id}")
async def get_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    item = await db.scalar(select(RetrievalLog).where(RetrievalLog.id == log_id))
    if item is None:
        return ok(None)
    return ok(
        {
            "id": str(item.id),
            "raw_query": item.raw_query,
            "rewritten_query": item.rewritten_query,
            "recall_results": item.recall_results,
            "rerank_results": item.rerank_results,
            "final_context": item.final_context,
            "citations": item.citations,
            "suggested_questions": item.suggested_questions,
            "answer": item.answer,
            "latency_ms": item.latency_ms,
        }
    )
