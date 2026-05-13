# NCHU AI Counselor

This repository currently contains two backend lines:

- `backend/`: the formal FastAPI backend for technical Phase 1.
- `src/backend/`: the legacy Flask prototype, retained only as reference material.

Technical Phase 1 acceptance is limited to the engineering foundation: FastAPI,
PostgreSQL, Redis, MinIO, Milvus, Docker local/private deployment, liveness,
readiness, and an automated smoke gate. It does not include the full student
Q&A product loop, admin UI, permission/audit, dashboard, notifications, document
generation, or multi-terminal rollout.

## Phase 1 Quick Start

Run these commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

cd backend
docker compose -f docker-compose.phase1.yml up -d
..\.venv\Scripts\python.exe scripts\smoke_phase1.py
..\.venv\Scripts\python.exe -m pytest
```

If the virtual environment is already activated and has `backend/requirements.txt`
installed, the shorter `python scripts/smoke_phase1.py` and `pytest` commands
are equivalent.

The compose file starts:

| Service | Container | Host port | Purpose |
| --- | --- | --- | --- |
| FastAPI | `nchu-phase1-api` | `8000` | Formal backend API |
| PostgreSQL | `nchu-phase1-postgres` | `5432` | Structured data |
| Redis | `nchu-phase1-redis` | `6379` | Cache/session/task state base |
| MinIO | `nchu-phase1-minio` | `9000`, `9001` | Original document/object storage |
| Milvus | `nchu-phase1-milvus` | `19530`, `9091` | Formal vector database |
| Milvus etcd | `nchu-phase1-milvus-etcd` | internal | Milvus dependency |
| Milvus MinIO | `nchu-phase1-milvus-minio` | internal | Milvus object-store dependency |

Stop the stack with:

```powershell
cd backend
docker compose -f docker-compose.phase1.yml down
```

Remove persisted local volumes only when you intentionally want a clean data
reset:

```powershell
cd backend
docker compose -f docker-compose.phase1.yml down -v
```

## Configuration

Use `backend/.env.example` as the host-side template:

```powershell
cd backend
copy .env.example .env
```

The template uses `localhost` defaults so host-run smoke commands work after the
Docker stack is up. `docker-compose.phase1.yml` overrides API-container service
URLs to Docker DNS names such as `postgres`, `redis`, `minio`, and `milvus`.

Important Phase 1 variables:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Host-side PostgreSQL URL for smoke/dev commands |
| `REDIS_URL` | Host-side Redis URL |
| `MINIO_ENDPOINT` | Host-side MinIO API endpoint |
| `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET` | Object storage credentials and bucket |
| `MILVUS_HOST`, `MILVUS_PORT`, `MILVUS_DB_NAME` | Milvus connection target |
| `MILVUS_COLLECTION`, `MILVUS_VECTOR_DIM`, `MILVUS_METRIC_TYPE` | Formal vector-store defaults |
| `DASHSCOPE_API_KEY`, `EMBEDDING_MODEL` | Future model integration settings |
| `JWT_SECRET_KEY` | FastAPI JWT signing secret |

## Health And Smoke

FastAPI liveness:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
```

FastAPI readiness:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/readiness
```

Full smoke gate:

```powershell
cd backend
..\.venv\Scripts\python.exe scripts\smoke_phase1.py
```

The smoke script performs real round trips:

- PostgreSQL: create/use test table, insert, select, cleanup.
- Redis: set, get, TTL check, delete.
- MinIO: create/reuse bucket, put object, get object, delete object.
- Milvus: create smoke collection, insert a 1024-dimensional vector, create
  index, load, TopK search, cleanup.

Failures name the service and failed operation, for example:

```text
FAIL milvus operation=search error="collection not loaded"
```

## Legacy Boundary

The root `docker-compose.yml` and `src/backend/` belong to the old Flask
prototype. They are not part of technical Phase 1 acceptance.

Older Qdrant code is retained only as migration/reference material until the
FastAPI + Milvus + MinIO smoke gate is stable. New Phase 1 validation uses
Milvus, not Qdrant.

## Troubleshooting

Check container state:

```powershell
cd backend
docker compose -f docker-compose.phase1.yml ps
```

View a failing service log:

```powershell
cd backend
docker compose -f docker-compose.phase1.yml logs api
docker compose -f docker-compose.phase1.yml logs milvus
docker compose -f docker-compose.phase1.yml logs minio
```

Common causes:

- Port conflict: change `POSTGRES_PORT`, `REDIS_PORT`, `MINIO_API_PORT`,
  `MINIO_CONSOLE_PORT`, `MILVUS_PORT`, `MILVUS_HEALTH_PORT`, or `API_PORT`.
- Registry access: the compose defaults avoid Docker Hub for MinIO and Milvus.
  If another registry is unavailable, override `MILVUS_IMAGE`, `MINIO_IMAGE`,
  or `MILVUS_MINIO_IMAGE` for the current shell and rerun the same command.
- Orphan Qdrant warning: an existing `nchu-counselor-qdrant` container can be
  ignored for Phase 1. Do not remove old Flask/Qdrant assets until the migration
  boundary is explicitly closed.
- API unhealthy: check `JWT_SECRET_KEY`, `DATABASE_URL`, and `api` logs.
- MinIO failure: verify `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`.
- Milvus slow start: wait for `milvus-etcd`, `milvus-minio`, and `milvus` to
  become healthy; first startup can take longer than other services.
