"""
评测接口。维护评测用例、启动评测运行，并查询评测结果。
"""

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.json_utils import to_jsonable
from app.core.responses import ok
from app.db.models import Admin, EvaluationCase, EvaluationResult, EvaluationRun
from app.db.session import AsyncSessionLocal, get_db
from app.services.chat_service import ChatService
from app.services.task_queue_service import TaskQueueService


router = APIRouter(prefix="/evaluation", tags=["evaluation"])


class EvaluationCaseCreate(BaseModel):
    question: str
    expected_answer: str | None = None
    expected_document_ids: list[str] | None = None
    expected_chunk_ids: list[str] | None = None
    tags: list[str] | None = None
    difficulty: str | None = None


class EvaluationRunCreate(BaseModel):
    name: str
    case_ids: list[str] | None = None
    config: dict = Field(default_factory=dict)


@router.get("/cases")
async def list_cases(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    total = await db.scalar(select(func.count()).select_from(EvaluationCase))
    rows = await db.execute(
        select(EvaluationCase)
        .order_by(EvaluationCase.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return ok(
        {
            "items": [serialize_case(item) for item in rows.scalars()],
            "page": page,
            "page_size": page_size,
            "total": total or 0,
        }
    )


@router.post("/cases")
async def create_case(
    payload: EvaluationCaseCreate,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    item = EvaluationCase(**payload.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return ok(serialize_case(item))


@router.post("/runs")
async def create_run(
    payload: EvaluationRunCreate,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    run = EvaluationRun(
        name=payload.name,
        config={"case_ids": payload.case_ids or [], **payload.config},
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    task = await TaskQueueService().enqueue(
        "evaluation_run",
        {"run_id": str(run.id), "case_ids": payload.case_ids},
    )
    return ok({"run_id": str(run.id), "status": "queued", "task_id": task["id"]})


@router.get("/runs/{run_id}")
async def get_run(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    run = await db.scalar(select(EvaluationRun).where(EvaluationRun.id == run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="评测批次不存在")
    rows = await db.execute(select(EvaluationResult).where(EvaluationResult.run_id == run_id))
    return ok(
        {
            "id": str(run.id),
            "name": run.name,
            "status": run.status,
            "metrics": run.metrics,
            "results": [
                {
                    "id": str(item.id),
                    "case_id": str(item.case_id),
                    "answer": item.answer,
                    "hit_top3": item.hit_top3,
                    "hit_top5": item.hit_top5,
                    "answer_score": float(item.answer_score) if item.answer_score is not None else None,
                    "citation_score": float(item.citation_score) if item.citation_score is not None else None,
                    "suggested_question_score": (
                        float(item.suggested_question_score)
                        if item.suggested_question_score is not None
                        else None
                    ),
                    "failure_reason": item.failure_reason,
                    "trace": item.trace,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
                for item in rows.scalars()
            ],
        }
    )


async def _run_evaluation(run_id: str, case_ids: list[str] | None) -> None:
    async with AsyncSessionLocal() as db:
        try:
            query = select(EvaluationCase).where(EvaluationCase.is_active.is_(True))
            if case_ids:
                query = query.where(EvaluationCase.id.in_(case_ids))
            rows = await db.execute(query)
            cases = list(rows.scalars())

            chat_service = ChatService()
            top3_hits = 0
            top5_hits = 0
            source_case_count = 0
            answer_scores: list[float] = []
            citation_scores: list[float] = []
            suggestion_scores: list[float] = []

            for case in cases:
                answer = ""
                citations: list[dict] = []
                suggested_questions: list[dict] = []
                trace: dict = {}
                error_message: str | None = None
                try:
                    result = await chat_service.chat_once(
                        db,
                        case.question,
                        conversation_id=None,
                        enable_suggested_questions=True,
                        rerank_top_k=5,
                        enable_rewrite=False,
                    )
                    answer = str(result.get("answer") or "")
                    citations = list(result.get("citations") or [])
                    suggested_questions = list(result.get("suggested_questions") or [])
                    trace = dict(result.get("retrieval_trace") or {})
                except Exception as exc:
                    await db.rollback()
                    error_message = str(exc)

                rerank_results = trace.get("rerank_results") or []
                doc_ids = [str(item.get("document_id")) for item in rerank_results if item.get("document_id")]
                chunk_ids = [str(item.get("chunk_id")) for item in rerank_results if item.get("chunk_id")]
                expected_docs = [str(item) for item in case.expected_document_ids or []]
                expected_chunks = [str(item) for item in case.expected_chunk_ids or []]
                has_expected_sources = bool(expected_docs or expected_chunks)
                hit_top3 = (
                    _has_expected_hit(doc_ids[:3], chunk_ids[:3], expected_docs, expected_chunks)
                    if has_expected_sources
                    else None
                )
                hit_top5 = (
                    _has_expected_hit(doc_ids[:5], chunk_ids[:5], expected_docs, expected_chunks)
                    if has_expected_sources
                    else None
                )
                if has_expected_sources:
                    source_case_count += 1
                    top3_hits += int(bool(hit_top3))
                    top5_hits += int(bool(hit_top5))

                answer_score = _answer_keyword_score(answer, case.expected_answer)
                citation_score = _citation_score(citations, trace, expected_docs, expected_chunks)
                suggested_question_score = _suggested_question_score(suggested_questions)
                if answer_score is not None:
                    answer_scores.append(answer_score)
                if citation_score is not None:
                    citation_scores.append(citation_score)
                suggestion_scores.append(suggested_question_score)

                db.add(
                    EvaluationResult(
                        run_id=run_id,
                        case_id=case.id,
                        answer=answer,
                        hit_top3=hit_top3,
                        hit_top5=hit_top5,
                        answer_score=answer_score,
                        citation_score=citation_score,
                        suggested_question_score=suggested_question_score,
                        failure_reason=_failure_reason(
                            error_message,
                            answer,
                            hit_top5,
                            answer_score,
                            citation_score,
                            suggested_question_score,
                        ),
                        trace=to_jsonable(
                            {
                                **trace,
                                "error_message": error_message,
                                "citations": citations,
                                "suggested_questions": suggested_questions,
                                "expected_document_ids": expected_docs,
                                "expected_chunk_ids": expected_chunks,
                                "expected_answer": case.expected_answer,
                            }
                        ),
                    )
                )
                await db.commit()

            source_total = source_case_count or 0
            metrics = {
                "case_count": len(cases),
                "source_case_count": source_case_count,
                "top3_hit_rate": round(top3_hits / source_total, 4) if source_total else None,
                "top5_hit_rate": round(top5_hits / source_total, 4) if source_total else None,
                "answer_score_avg": _average(answer_scores),
                "citation_score_avg": _average(citation_scores),
                "suggested_question_score_avg": _average(suggestion_scores),
            }
            await db.execute(
                update(EvaluationRun)
                .where(EvaluationRun.id == run_id)
                .values(status="succeeded", metrics=metrics, finished_at=datetime.now(timezone.utc))
            )
            await db.commit()
        except Exception as exc:
            await db.rollback()
            await db.execute(
                update(EvaluationRun)
                .where(EvaluationRun.id == run_id)
                .values(
                    status="failed",
                    metrics={"error": str(exc)},
                    finished_at=datetime.now(timezone.utc),
                )
            )
            await db.commit()


def serialize_case(item: EvaluationCase) -> dict:
    return {
        "id": str(item.id),
        "question": item.question,
        "expected_answer": item.expected_answer,
        "expected_document_ids": [str(x) for x in item.expected_document_ids or []],
        "expected_chunk_ids": [str(x) for x in item.expected_chunk_ids or []],
        "tags": item.tags or [],
        "difficulty": item.difficulty,
        "is_active": item.is_active,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def _has_expected_hit(
    doc_ids: list[str],
    chunk_ids: list[str],
    expected_docs: list[str],
    expected_chunks: list[str],
) -> bool:
    doc_hit = bool(expected_docs and set(doc_ids) & set(expected_docs))
    chunk_hit = bool(expected_chunks and set(chunk_ids) & set(expected_chunks))
    return doc_hit or chunk_hit


def _answer_keyword_score(answer: str, expected_answer: str | None) -> float | None:
    if not expected_answer or not expected_answer.strip():
        return None
    keywords = _extract_keywords(expected_answer)
    if not keywords:
        return None
    normalized_answer = _normalize_text(answer)
    hits = sum(1 for keyword in keywords if _normalize_text(keyword) in normalized_answer)
    return round(hits / len(keywords), 4)


def _citation_score(
    citations: list[dict],
    trace: dict,
    expected_docs: list[str],
    expected_chunks: list[str],
) -> float | None:
    if not expected_docs and not expected_chunks:
        return None
    citation_doc_ids = {
        str(item.get("document_id"))
        for item in citations
        if item.get("document_id")
    }
    citation_chunk_ids = {
        str(item.get("chunk_id"))
        for item in citations
        if item.get("chunk_id")
    }
    context_items = trace.get("final_context") or []
    citation_doc_ids.update(
        str(item.get("document_id"))
        for item in context_items
        if item.get("document_id")
    )
    citation_chunk_ids.update(
        str(item.get("chunk_id"))
        for item in context_items
        if item.get("chunk_id")
    )
    expected_total = max(1, len(expected_docs) + len(expected_chunks))
    hits = len(citation_doc_ids & set(expected_docs)) + len(citation_chunk_ids & set(expected_chunks))
    return round(min(1.0, hits / expected_total), 4)


def _suggested_question_score(suggested_questions: list[dict]) -> float:
    count = sum(1 for item in suggested_questions if str(item.get("question") or "").strip())
    return round(min(1.0, count / 3), 4)


def _failure_reason(
    error_message: str | None,
    answer: str,
    hit_top5: bool | None,
    answer_score: float | None,
    citation_score: float | None,
    suggested_question_score: float,
) -> str | None:
    if error_message:
        return "answer_error"
    if not answer.strip():
        return "empty_answer"
    if hit_top5 is False:
        return "retrieval_miss"
    if answer_score is not None and answer_score < 0.5:
        return "answer_low_score"
    if citation_score is not None and citation_score <= 0:
        return "citation_miss"
    if suggested_question_score <= 0:
        return "suggestion_missing"
    return None


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _extract_keywords(text: str) -> list[str]:
    parts = [item.strip() for item in re.split(r"[,，;；、\n\r]+", text) if item.strip()]
    if len(parts) >= 2:
        return _dedupe_keywords(parts)
    tokens = re.findall(r"[A-Za-z0-9_.%+-]+|[\u4e00-\u9fff]{2,}", text)
    if tokens:
        return _dedupe_keywords(tokens)
    stripped = text.strip()
    return [stripped] if stripped else []


def _dedupe_keywords(keywords: list[str]) -> list[str]:
    result: list[str] = []
    for keyword in keywords:
        normalized = _normalize_text(keyword)
        if not normalized:
            continue
        if any(normalized == _normalize_text(existing) for existing in result):
            continue
        result.append(keyword)
    return result


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()
