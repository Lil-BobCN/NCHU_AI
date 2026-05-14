# Architecture

## Current Phase

Technical Phase 1 establishes the local/private engineering foundation. The
formal backend direction is:

```text
FastAPI (`backend/`)
  |-- PostgreSQL: structured application data foundation
  |-- Redis: cache, session, and task-state foundation
  |-- MinIO: original documents and object storage
  `-- Milvus: formal vector database
```

Legacy Flask, Qdrant, and old static frontend code were removed after the
FastAPI + Milvus + MinIO smoke gate became stable. They are no longer runtime
surfaces for this repository.

## Docker Topology

Recommended entrypoint:

```powershell
cd backend
docker compose -f docker-compose.phase1.yml up -d
```

Service layout:

```text
Host
  |-- 127.0.0.1:8000  -> api / FastAPI
  |-- 127.0.0.1:5432  -> postgres / PostgreSQL + pgvector image
  |-- 127.0.0.1:6379  -> redis / Redis
  |-- 127.0.0.1:9000  -> minio / object storage API
  |-- 127.0.0.1:9001  -> minio / console
  |-- 127.0.0.1:19530 -> milvus / vector database API
  `-- 127.0.0.1:9091  -> milvus / health endpoint

Internal Milvus dependencies
  |-- milvus-etcd
  `-- milvus-minio
```

The business MinIO service is named `minio`. Milvus uses a separate internal
`milvus-minio` service so original document storage is not confused with Milvus
internal object storage.

Published ports are localhost-bound by default. Private-network exposure is an
explicit deployment choice through `*_BIND_HOST` variables and should be paired
with non-default PostgreSQL and MinIO credentials.

## API Boundary

- `GET /api/v1/health` is liveness only. It proves the FastAPI process can
  respond.
- `GET /api/v1/readiness` checks lightweight connectivity to PostgreSQL, Redis,
  MinIO, and Milvus.
- Generated FastAPI documentation routes are disabled in this phase.
- `python scripts/smoke_phase1.py` is the acceptance-grade smoke gate. It
  performs writes, reads, searches, and cleanup.

No auth, chat, RAG question-answering, admin, dashboard, notification, or
frontend endpoints are exposed in Phase 1.

## Data Boundaries

PostgreSQL stores structured data and metadata. It is not the accepted vector
database for Phase 1, even though the image includes pgvector for historical
compatibility.

Milvus is the formal vector database. The configured default collection uses
1024-dimensional embeddings and a configurable metric/index pair.

MinIO stores original uploaded/source documents so future ingestion can rebuild
indexes and preserve auditability.

Redis is reserved for cache, session, and task-state foundations. The current
smoke gate verifies key/value and TTL behavior only.

## Legacy Boundary

The old Flask/Qdrant/static prototype code is intentionally absent from the
current runtime. Use git history or `.omx/` planning artifacts only when a
historical reference is needed.
