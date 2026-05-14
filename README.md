# NCHU AI Counselor

This repository is now scoped to the formal FastAPI technical Phase 1 backend.

Technical Phase 1 acceptance covers the engineering foundation only:
FastAPI, PostgreSQL, Redis, MinIO, Milvus, Docker local/private deployment,
liveness, readiness, and an automated smoke gate. It does not include the full
student Q&A loop, admin UI, permission/audit, dashboard, notifications,
document generation, or multi-terminal rollout.

Legacy Flask, old static frontend, and Qdrant prototype code were removed after
the FastAPI + Milvus + MinIO smoke gate became stable. Historical rationale
remains in `.omx/` planning artifacts and git history, but the tracked Phase 1
runtime and the documentation in this file supersede older interview notes when
they conflict.

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

If the virtual environment is already activated and has
`backend/requirements.txt` installed, the shorter `python scripts/smoke_phase1.py`
and `pytest` commands are equivalent.

The compose file starts:

| Service | Container | Default host bind | Purpose |
| --- | --- | --- | --- |
| FastAPI | `nchu-phase1-api` | `127.0.0.1:8000` | Formal backend API |
| PostgreSQL | `nchu-phase1-postgres` | `127.0.0.1:5432` | Structured data |
| Redis | `nchu-phase1-redis` | `127.0.0.1:6379` | Cache/session/task state base |
| MinIO | `nchu-phase1-minio` | `127.0.0.1:9000`, `127.0.0.1:9001` | Original document/object storage |
| Milvus | `nchu-phase1-milvus` | `127.0.0.1:19530`, `127.0.0.1:9091` | Formal vector database |
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
Published ports bind to `127.0.0.1` by default. For trusted private-network
access, set the relevant `*_BIND_HOST` value to an internal interface or
`0.0.0.0` and replace default PostgreSQL/MinIO credentials before starting.

Important Phase 1 variables:

| Variable | Purpose |
| --- | --- |
| `API_BIND_HOST`, `POSTGRES_BIND_HOST`, `REDIS_BIND_HOST`, `MINIO_BIND_HOST`, `MILVUS_BIND_HOST` | Host interface for published Docker ports |
| `DATABASE_URL` | Host-side PostgreSQL URL for smoke/dev commands |
| `REDIS_URL` | Host-side Redis URL |
| `MINIO_ENDPOINT` | Host-side MinIO API endpoint |
| `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET` | Object storage credentials and bucket |
| `MILVUS_HOST`, `MILVUS_PORT`, `MILVUS_DB_NAME` | Milvus connection target |
| `MILVUS_COLLECTION`, `MILVUS_VECTOR_DIM`, `MILVUS_METRIC_TYPE` | Formal vector-store defaults |

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

## API Boundary

Phase 1 exposes only:

- `GET /api/v1/health`
- `GET /api/v1/readiness`

FastAPI's generated `/docs`, `/redoc`, and `/openapi.json` routes are disabled
in this phase to keep the HTTP surface limited to the two infrastructure
endpoints above.

Auth, chat, RAG question answering, admin management, dashboards, notifications,
and frontend pages are deliberately not exposed in this phase.

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
- Remote private-network access: change the relevant `*_BIND_HOST` from
  `127.0.0.1` to the target internal interface and replace default credentials.
- Registry access: the compose defaults avoid Docker Hub for MinIO and Milvus.
  If another registry is unavailable, override `MILVUS_IMAGE`, `MINIO_IMAGE`,
  or `MILVUS_MINIO_IMAGE` for the current shell and rerun the same command.
- API unhealthy: check `DATABASE_URL` and `api` logs.
- MinIO failure: verify `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`.
- Milvus slow start: wait for `milvus-etcd`, `milvus-minio`, and `milvus` to
  become healthy; first startup can take longer than other services.
