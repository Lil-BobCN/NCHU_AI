"""Liveness and readiness endpoints for the FastAPI service."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Response, status

from app.config import Settings, get_settings

router = APIRouter()


@router.get(
    "/health",
    summary="Liveness check",
    description="Returns API process liveness without checking infrastructure.",
)
async def health_check() -> dict[str, Any]:
    """Return API liveness status."""
    settings = get_settings()
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "ai-counselor-api",
        "version": settings.app_version,
    }


@router.get(
    "/readiness",
    summary="Readiness check",
    description="Checks lightweight connectivity to Phase 1 infrastructure.",
)
async def readiness_check(response: Response) -> dict[str, Any]:
    """Return dependency readiness without performing destructive smoke writes."""
    settings = get_settings()
    checks = await _run_readiness_checks(settings)
    ready = all(item["status"] == "ready" for item in checks.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if ready else "not_ready",
        "timestamp": datetime.now(UTC).isoformat(),
        "service": "ai-counselor-api",
        "version": settings.app_version,
        "checks": checks,
    }


async def _run_readiness_checks(settings: Settings) -> dict[str, dict[str, Any]]:
    """Run readiness checks concurrently."""
    names = ("postgres", "redis", "minio", "milvus")
    results = await asyncio.gather(
        _check_postgres(settings),
        _check_redis(settings),
        _check_minio(settings),
        _check_milvus(settings),
        return_exceptions=True,
    )
    return {
        name: _format_check_result(result)
        for name, result in zip(names, results, strict=True)
    }


async def _check_postgres(settings: Settings) -> dict[str, Any]:
    """Check PostgreSQL connectivity with SELECT 1."""
    operation = "select_1"
    try:
        import asyncpg

        conn = await asyncpg.connect(dsn=_asyncpg_dsn(settings.database_url))
        try:
            value = await conn.fetchval("SELECT 1")
        finally:
            await conn.close()
        if value != 1:
            raise RuntimeError(f"unexpected SELECT 1 result: {value!r}")
        return {"status": "ready", "operation": operation}
    except Exception as exc:
        return _failed("postgres", operation, exc)


async def _check_redis(settings: Settings) -> dict[str, Any]:
    """Check Redis connectivity with PING."""
    operation = "ping"
    try:
        import redis.asyncio as redis

        client = redis.from_url(settings.redis_url, socket_connect_timeout=3)
        try:
            pong = await client.ping()
        finally:
            await client.aclose()
        if pong is not True:
            raise RuntimeError(f"unexpected PING result: {pong!r}")
        return {"status": "ready", "operation": operation}
    except Exception as exc:
        return _failed("redis", operation, exc)


async def _check_minio(settings: Settings) -> dict[str, Any]:
    """Check MinIO credentials and API reachability."""
    operation = "list_buckets"
    try:
        from minio import Minio

        endpoint, secure = _normalize_minio_endpoint(
            settings.minio_endpoint,
            settings.minio_secure,
        )
        client = Minio(
            endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=secure,
        )
        buckets = await asyncio.to_thread(client.list_buckets)
        return {
            "status": "ready",
            "operation": operation,
            "bucket_count": len(buckets),
        }
    except Exception as exc:
        return _failed("minio", operation, exc)


async def _check_milvus(settings: Settings) -> dict[str, Any]:
    """Check Milvus connectivity by listing collections."""
    operation = "list_collections"
    try:
        from pymilvus import MilvusClient

        kwargs: dict[str, Any] = {
            "uri": f"http://{settings.milvus_host}:{settings.milvus_port}",
            "db_name": settings.milvus_db_name,
        }
        if settings.milvus_token:
            kwargs["token"] = settings.milvus_token
        client = MilvusClient(**kwargs)
        try:
            collections = await asyncio.to_thread(client.list_collections)
        finally:
            close = getattr(client, "close", None)
            if close is not None:
                await asyncio.to_thread(close)
        return {
            "status": "ready",
            "operation": operation,
            "collection_count": len(collections),
        }
    except Exception as exc:
        return _failed("milvus", operation, exc)


def _format_check_result(result: Any) -> dict[str, Any]:
    """Normalize readiness check results."""
    if isinstance(result, Exception):
        return {
            "status": "not_ready",
            "operation": "unknown",
            "error": f"{type(result).__name__}: {result}",
        }
    return result


def _failed(service: str, operation: str, exc: Exception) -> dict[str, Any]:
    """Build a dependency failure payload."""
    return {
        "status": "not_ready",
        "service": service,
        "operation": operation,
        "error": f"{type(exc).__name__}: {exc}",
    }


def _asyncpg_dsn(database_url: str) -> str:
    """Convert SQLAlchemy asyncpg URLs to asyncpg DSNs."""
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


def _normalize_minio_endpoint(endpoint: str, secure: bool) -> tuple[str, bool]:
    """Return a MinIO SDK endpoint without URL scheme."""
    if endpoint.startswith("https://"):
        return endpoint.removeprefix("https://"), True
    if endpoint.startswith("http://"):
        return endpoint.removeprefix("http://"), False
    return endpoint, secure
