# Architecture

## Current Phase

Technical Phase 1 establishes the local/private engineering foundation. The
formal backend direction is:

```text
FastAPI (`backend/`)
  |-- PostgreSQL: structured application data
  |-- Redis: cache, session, and task-state foundation
  |-- MinIO: original documents and object storage
  `-- Milvus: formal vector database
```

The legacy Flask prototype under `src/backend/` remains inspectable but is not
part of the current acceptance gate. Qdrant artifacts are migration references
only and are not the formal vector-store path for Phase 1.

## Phase 1 Docker Topology

Recommended entrypoint:

```powershell
cd backend
docker compose -f docker-compose.phase1.yml up -d
```

Service layout:

```text
Host
  |-- :8000  -> api / FastAPI
  |-- :5432  -> postgres / PostgreSQL + pgvector image
  |-- :6379  -> redis / Redis
  |-- :9000  -> minio / business object storage API
  |-- :9001  -> minio / console
  |-- :19530 -> milvus / vector database API
  `-- :9091  -> milvus / health endpoint

Internal Milvus dependencies
  |-- milvus-etcd
  `-- milvus-minio
```

The business MinIO service is named `minio`. Milvus uses a separate internal
`milvus-minio` service so original document storage is not confused with Milvus
internal object storage.

## API Health Boundary

- `GET /api/v1/health` is liveness only. It proves the FastAPI process can
  respond.
- `GET /api/v1/readiness` checks lightweight connectivity to PostgreSQL, Redis,
  MinIO, and Milvus.
- `python scripts/smoke_phase1.py` is the acceptance-grade smoke gate. It
  performs writes, reads, searches, and cleanup.

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

The root `docker-compose.yml` starts the old Flask-oriented stack. Keep it
available for prototype comparison, but do not use it to decide Phase 1
completion.

Do not remove `src/backend/` or old Qdrant migration-reference files until the
FastAPI + Milvus + MinIO smoke gate is stable.
