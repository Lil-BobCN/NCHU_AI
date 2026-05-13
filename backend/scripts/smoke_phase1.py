"""Phase 1 infrastructure smoke test.

Validates the accepted technical Phase 1 stack:
FastAPI liveness, PostgreSQL, Redis, MinIO, and Milvus.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv

SERVICE_ALIASES = {"postgres", "redis", "minio", "milvus"}


class SmokeError(Exception):
    """Failure with service and operation context."""

    def __init__(self, service: str, operation: str, error: object) -> None:
        self.service = service
        self.operation = operation
        self.error = str(error)
        super().__init__(self.error)


@dataclass(frozen=True)
class Phase1Settings:
    """Smoke-test settings loaded from environment."""

    database_url: str
    redis_url: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    minio_secure: bool
    milvus_host: str
    milvus_port: int
    milvus_db_name: str
    milvus_collection: str
    milvus_vector_dim: int
    milvus_metric_type: str
    milvus_index_type: str
    milvus_index_nlist: int
    milvus_token: str
    fastapi_health_url: str


def load_settings() -> Phase1Settings:
    """Load `.env` and return smoke-test settings."""
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    return Phase1Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://counselor:counselor_pass@localhost:5432/counselor_db",
        ),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/1"),
        minio_endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        minio_access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        minio_secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        minio_bucket=os.getenv("MINIO_BUCKET", "nchu-counselor-documents"),
        minio_secure=_bool_env("MINIO_SECURE", False),
        milvus_host=os.getenv("MILVUS_HOST", "localhost"),
        milvus_port=int(os.getenv("MILVUS_PORT", "19530")),
        milvus_db_name=os.getenv("MILVUS_DB_NAME", "default"),
        milvus_collection=os.getenv("MILVUS_COLLECTION", "nchu_counselor_documents"),
        milvus_vector_dim=int(os.getenv("MILVUS_VECTOR_DIM", "1024")),
        milvus_metric_type=os.getenv("MILVUS_METRIC_TYPE", "COSINE").upper(),
        milvus_index_type=os.getenv("MILVUS_INDEX_TYPE", "IVF_FLAT").upper(),
        milvus_index_nlist=int(os.getenv("MILVUS_INDEX_NLIST", "1024")),
        milvus_token=os.getenv("MILVUS_TOKEN", ""),
        fastapi_health_url=os.getenv(
            "FASTAPI_HEALTH_URL",
            "http://localhost:8000/api/v1/health",
        ),
    )


async def smoke_fastapi(settings: Phase1Settings) -> str:
    """Validate FastAPI liveness."""
    operation = "health"
    try:
        import httpx

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(settings.fastapi_health_url)
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "healthy":
            raise RuntimeError(f"unexpected health payload: {payload}")
        return "PASS fastapi health"
    except Exception as exc:
        raise SmokeError("fastapi", operation, exc) from exc


async def smoke_postgres(settings: Phase1Settings) -> str:
    """Validate PostgreSQL create/insert/select/cleanup."""
    operation = "connect"
    engine = None
    test_id = str(uuid.uuid4())
    payload = f"phase1-smoke-{test_id}"
    try:
        from sqlalchemy import text
        from sqlalchemy.engine import make_url
        from sqlalchemy.ext.asyncio import create_async_engine

        url = _host_url_for_local_smoke(make_url(settings.database_url))
        engine = create_async_engine(url, pool_pre_ping=True)

        async with engine.begin() as conn:
            operation = "create_table"
            await conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS phase1_smoke (
                        id TEXT PRIMARY KEY,
                        payload TEXT NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                )
            )

            operation = "insert"
            await conn.execute(
                text("INSERT INTO phase1_smoke (id, payload) VALUES (:id, :payload)"),
                {"id": test_id, "payload": payload},
            )

            operation = "select"
            selected = await conn.scalar(
                text("SELECT payload FROM phase1_smoke WHERE id = :id"),
                {"id": test_id},
            )
            if selected != payload:
                raise RuntimeError(f"selected payload mismatch: {selected!r}")

            operation = "cleanup"
            await conn.execute(
                text("DELETE FROM phase1_smoke WHERE id = :id"),
                {"id": test_id},
            )

        return "PASS postgres connect/create_table/insert/select/cleanup"
    except Exception as exc:
        raise SmokeError("postgres", operation, exc) from exc
    finally:
        if engine is not None:
            await engine.dispose()


async def smoke_redis(settings: Phase1Settings) -> str:
    """Validate Redis set/get/TTL/delete."""
    operation = "connect"
    key = f"phase1:smoke:{uuid.uuid4()}"
    value = "ok"
    client = None
    try:
        import redis.asyncio as redis

        redis_url = _host_url_for_local_smoke(settings.redis_url)
        client = redis.from_url(redis_url, socket_connect_timeout=5)
        operation = "set"
        await client.set(key, value, ex=30)

        operation = "get"
        selected = await client.get(key)
        if selected != value.encode():
            raise RuntimeError(f"selected value mismatch: {selected!r}")

        operation = "ttl"
        ttl = await client.ttl(key)
        if ttl <= 0:
            raise RuntimeError(f"expected positive TTL, got {ttl}")

        operation = "delete"
        await client.delete(key)
        return "PASS redis set/get/ttl/delete"
    except Exception as exc:
        raise SmokeError("redis", operation, exc) from exc
    finally:
        if client is not None:
            await client.aclose()


async def smoke_minio(settings: Phase1Settings) -> str:
    """Validate MinIO bucket/object round trip."""
    operation = "connect"
    object_name = f"phase1-smoke/{uuid.uuid4()}.txt"
    content = b"phase1 minio smoke"
    try:
        from minio import Minio

        endpoint, secure = _normalize_minio_endpoint(
            _host_endpoint_for_local_smoke(settings.minio_endpoint),
            settings.minio_secure,
        )
        client = Minio(
            endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=secure,
        )

        operation = "ensure_bucket"
        if not await asyncio.to_thread(client.bucket_exists, settings.minio_bucket):
            await asyncio.to_thread(client.make_bucket, settings.minio_bucket)

        operation = "put_object"
        await asyncio.to_thread(
            client.put_object,
            settings.minio_bucket,
            object_name,
            BytesIO(content),
            len(content),
        )

        operation = "get_object"
        response = await asyncio.to_thread(
            client.get_object,
            settings.minio_bucket,
            object_name,
        )
        try:
            downloaded = await asyncio.to_thread(response.read)
        finally:
            response.close()
            response.release_conn()
        if downloaded != content:
            raise RuntimeError("downloaded object content mismatch")

        operation = "delete_object"
        await asyncio.to_thread(client.remove_object, settings.minio_bucket, object_name)
        return "PASS minio bucket/put/get/delete"
    except Exception as exc:
        raise SmokeError("minio", operation, exc) from exc


async def smoke_milvus(settings: Phase1Settings) -> str:
    """Validate Milvus collection/vector/index/search/cleanup."""
    operation = "connect"
    collection = _smoke_collection_name(settings.milvus_collection)
    client = None
    try:
        from pymilvus import DataType, MilvusClient

        kwargs = {
            "uri": f"http://{_host_for_local_smoke(settings.milvus_host)}:{settings.milvus_port}",
            "db_name": settings.milvus_db_name,
        }
        if settings.milvus_token:
            kwargs["token"] = settings.milvus_token
        client = MilvusClient(**kwargs)

        operation = "create_collection"
        if await asyncio.to_thread(client.has_collection, collection):
            await asyncio.to_thread(client.drop_collection, collection)

        schema = MilvusClient.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
        schema.add_field(
            field_name="vector",
            datatype=DataType.FLOAT_VECTOR,
            dim=settings.milvus_vector_dim,
        )
        schema.add_field(
            field_name="content",
            datatype=DataType.VARCHAR,
            max_length=256,
        )
        await asyncio.to_thread(
            client.create_collection,
            collection_name=collection,
            schema=schema,
        )

        operation = "insert"
        vector = _test_vector(settings.milvus_vector_dim)
        await asyncio.to_thread(
            client.insert,
            collection_name=collection,
            data=[{"id": 1, "vector": vector, "content": "phase1 smoke"}],
        )

        operation = "flush"
        await asyncio.to_thread(client.flush, collection_name=collection)

        operation = "create_index"
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type=settings.milvus_index_type,
            metric_type=settings.milvus_metric_type,
            params={"nlist": settings.milvus_index_nlist},
        )
        await asyncio.to_thread(
            client.create_index,
            collection_name=collection,
            index_params=index_params,
            sync=True,
        )

        operation = "load"
        await asyncio.to_thread(client.load_collection, collection, replica_number=1)

        operation = "search"
        results = await asyncio.to_thread(
            client.search,
            collection_name=collection,
            data=[vector],
            anns_field="vector",
            search_params={
                "metric_type": settings.milvus_metric_type,
                "params": {"nprobe": 8},
            },
            limit=1,
            output_fields=["content"],
        )
        if not results or not results[0]:
            raise RuntimeError("search returned no results")
        hit = results[0][0]
        hit_id = hit.get("id") if isinstance(hit, dict) else getattr(hit, "id", None)
        if hit_id not in (1, "1"):
            raise RuntimeError(f"top hit id mismatch: {hit_id!r}")

        operation = "cleanup"
        await asyncio.to_thread(client.drop_collection, collection)
        return "PASS milvus collection/insert/index/load/search/cleanup"
    except Exception as exc:
        raise SmokeError("milvus", operation, exc) from exc
    finally:
        if client is not None:
            try:
                if await asyncio.to_thread(client.has_collection, collection):
                    await asyncio.to_thread(client.drop_collection, collection)
            except Exception:
                pass
            close = getattr(client, "close", None)
            if close is not None:
                await asyncio.to_thread(close)


async def main() -> int:
    """Run all smoke checks and return a process exit code."""
    settings = load_settings()
    checks = (
        smoke_fastapi,
        smoke_postgres,
        smoke_redis,
        smoke_minio,
        smoke_milvus,
    )
    failures: list[SmokeError] = []

    for check in checks:
        try:
            print(await check(settings))
        except SmokeError as exc:
            failures.append(exc)
            print(f'FAIL {exc.service} operation={exc.operation} error="{_escape(exc.error)}"')

    if failures:
        print(f"FAIL phase1 smoke failed_services={','.join(f.service for f in failures)}")
        return 1

    print("PASS phase1 smoke")
    return 0


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _host_for_local_smoke(host: str) -> str:
    """Map Docker service DNS names to localhost for host-run smoke commands."""
    if _inside_container():
        return host
    return "localhost" if host in SERVICE_ALIASES else host


def _host_endpoint_for_local_smoke(endpoint: str) -> str:
    scheme = ""
    remainder = endpoint
    if "://" in endpoint:
        scheme, remainder = endpoint.split("://", 1)
        scheme = f"{scheme}://"
    host, separator, port = remainder.partition(":")
    host = _host_for_local_smoke(host)
    return f"{scheme}{host}{separator}{port}" if separator else f"{scheme}{host}"


def _host_url_for_local_smoke(url):
    """Map Docker service DNS names inside SQLAlchemy or Redis URLs."""
    if hasattr(url, "host"):
        return url.set(host=_host_for_local_smoke(url.host or "localhost"))

    parts = urlsplit(url)
    host = parts.hostname or ""
    if not host:
        return url
    host = _host_for_local_smoke(host)
    netloc = host
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    if parts.username:
        auth = parts.username
        if parts.password:
            auth = f"{auth}:{parts.password}"
        netloc = f"{auth}@{netloc}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _normalize_minio_endpoint(endpoint: str, secure: bool) -> tuple[str, bool]:
    if endpoint.startswith("https://"):
        return endpoint.removeprefix("https://"), True
    if endpoint.startswith("http://"):
        return endpoint.removeprefix("http://"), False
    return endpoint, secure


def _smoke_collection_name(base_name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in base_name)
    return f"{safe}_smoke"


def _test_vector(dim: int) -> list[float]:
    return [float((index % 17) + 1) / 17.0 for index in range(dim)]


def _inside_container() -> bool:
    return Path("/.dockerenv").exists() or os.getenv("RUNNING_IN_CONTAINER") == "1"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
