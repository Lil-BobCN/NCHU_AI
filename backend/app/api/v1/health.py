"""
健康检查接口。用于确认服务进程和基础 readiness 状态。
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import ok
from app.db.session import get_db
from app.services.minio_service import MinioService
from app.services.redis_service import RedisService


router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return ok({"api": "ok"})


@router.get("/readiness")
async def readiness(db: AsyncSession = Depends(get_db)):
    return await check_dependencies(db)


async def check_dependencies(db: AsyncSession):
    status = {"api": "ok", "postgres": "unknown", "redis": "unknown", "minio": "unknown"}
    try:
        await db.execute(text("SELECT 1"))
        status["postgres"] = "ok"
    except Exception as exc:
        status["postgres"] = f"error: {exc}"
    try:
        status["redis"] = "ok" if await RedisService().ping() else "error"
    except Exception as exc:
        status["redis"] = f"error: {exc}"
    try:
        MinioService().ensure_buckets()
        status["minio"] = "ok"
    except Exception as exc:
        status["minio"] = f"error: {exc}"
    return ok(status)
