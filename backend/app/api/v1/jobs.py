from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_current_admin
from app.core.responses import ok
from app.db.models import Admin, DocumentJob
from app.db.session import get_db
from app.services.redis_service import RedisService


router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    cached = await RedisService().get_json(f"job:{job_id}:progress")
    if cached:
        return ok(cached)
    job = await db.scalar(select(DocumentJob).where(DocumentJob.id == job_id))
    if job is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return ok(
        {
            "id": str(job.id),
            "document_id": str(job.document_id),
            "job_type": job.job_type,
            "status": job.status,
            "progress": job.progress,
            "message": job.message,
            "error_message": job.error_message,
            "params": job.params,
            "result": job.result,
        }
    )


@router.get("/documents/{document_id}/jobs")
async def list_document_jobs(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    document_id = _normalize_uuid(document_id, "document_id")
    rows = await db.execute(
        select(DocumentJob).where(DocumentJob.document_id == document_id).order_by(DocumentJob.created_at.desc())
    )
    return ok(
        [
            {
                "id": str(job.id),
                "job_type": job.job_type,
                "status": job.status,
                "progress": job.progress,
                "message": job.message,
                "error_message": job.error_message,
                "params": job.params,
                "result": job.result,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            }
            for job in rows.scalars()
        ]
    )


def _normalize_uuid(value: str, field_name: str) -> str:
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{field_name} 格式不正确") from exc
