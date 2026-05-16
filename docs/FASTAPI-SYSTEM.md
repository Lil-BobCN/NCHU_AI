# FastAPI Phase 1 System

## Purpose

`backend/` is the formal backend for the AI counselor system. In technical
Phase 1 it provides infrastructure readiness and smoke validation; the current
business Phase 1 layer adds a lightweight in-memory auth, student, admin, and
counselor API surface for acceptance testing.

## Stack

- FastAPI + Uvicorn
- PostgreSQL via `asyncpg`/SQLAlchemy
- Redis
- MinIO Python SDK
- Milvus via PyMilvus
- Docker Compose local/private deployment

## Files

| File | Purpose |
| --- | --- |
| `backend/docker-compose.phase1.yml` | Formal Phase 1 stack |
| `backend/.env.example` | Host-side environment template |
| `backend/app/config.py` | Pydantic settings for PostgreSQL, Redis, MinIO, Milvus |
| `backend/app/api/v1/health.py` | Liveness and readiness endpoints |
| `backend/app/api/v1/auth.py` | Local login and mock SSO auth routes |
| `backend/app/api/v1/student.py` | Student Q&A, resources, and conversations |
| `backend/app/api/v1/admin.py` | Knowledge maintenance, audit, and stats |
| `backend/app/api/v1/counselor.py` | Counselor assistance route |
| `backend/app/services/business.py` | In-memory business store and helper logic |
| `backend/app/schemas/business.py` | Request and response models for business routes |
| `backend/scripts/smoke_phase1.py` | Acceptance-grade infrastructure smoke script |

## Start, Verify, Stop

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

cd backend
docker compose -f docker-compose.phase1.yml up -d
..\.venv\Scripts\python.exe scripts\smoke_phase1.py
..\.venv\Scripts\python.exe -m pytest
```

When an environment with `backend/requirements.txt` is already active,
`python scripts/smoke_phase1.py` and `pytest` are equivalent.

Liveness:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/health
```

Readiness:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/readiness
```

Stop:

```powershell
cd backend
docker compose -f docker-compose.phase1.yml down
```

## Readiness Versus Smoke

Readiness is intentionally lightweight and checks connectivity only:

- PostgreSQL `SELECT 1`
- Redis `PING`
- MinIO bucket listing
- Milvus collection listing

The smoke script is the acceptance gate and performs real mutations:

- PostgreSQL create table, insert, select, cleanup.
- Redis set, get, TTL, delete.
- MinIO ensure bucket, put object, get object, delete object.
- Milvus create collection, insert 1024-dimensional vector, flush, create
  index, load, TopK search, drop smoke collection.

## API Boundary

The mounted Phase 1 API surface is intentionally small but now includes the
business acceptance layer:

- `GET /api/v1/health`
- `GET /api/v1/readiness`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/sso/callback`
- `GET /api/v1/auth/me`
- `POST /api/v1/student/questions`
- `GET /api/v1/student/resources`
- `GET /api/v1/student/conversations`
- `POST /api/v1/student/conversations`
- `GET /api/v1/student/conversations/{conversation_id}`
- `POST /api/v1/student/conversations/{conversation_id}/messages`
- `GET /api/v1/admin/knowledge`
- `POST /api/v1/admin/knowledge`
- `PUT /api/v1/admin/knowledge/{knowledge_id}`
- `DELETE /api/v1/admin/knowledge/{knowledge_id}`
- `GET /api/v1/admin/audit`
- `GET /api/v1/admin/stats`
- `POST /api/v1/counselor/assistance`

Generated documentation routes (`/docs`, `/redoc`, `/openapi.json`) are still
disabled in this phase. The business layer is in-memory and exists to validate
the acceptance contract before persistence-backed services are added.

## Configuration Notes

`backend/.env.example` uses host-side `localhost` values. The compose file
overrides the API container to use Docker service names:

- `postgres`
- `redis`
- `minio`
- `milvus`

This keeps the documented host smoke command consistent with the API container
runtime.

Published Docker ports bind to `127.0.0.1` by default:

- `API_BIND_HOST`
- `POSTGRES_BIND_HOST`
- `REDIS_BIND_HOST`
- `MINIO_BIND_HOST`
- `MILVUS_BIND_HOST`

For trusted private-network access, set the needed bind host to an internal
interface or `0.0.0.0` and replace default PostgreSQL/MinIO credentials before
starting the stack.

## Troubleshooting

Check service health:

```powershell
cd backend
docker compose -f docker-compose.phase1.yml ps
```

Inspect logs:

```powershell
docker compose -f docker-compose.phase1.yml logs api
docker compose -f docker-compose.phase1.yml logs postgres
docker compose -f docker-compose.phase1.yml logs redis
docker compose -f docker-compose.phase1.yml logs minio
docker compose -f docker-compose.phase1.yml logs milvus
```

Smoke failures are formatted with service and operation context:

```text
FAIL postgres operation=insert error="..."
FAIL redis operation=ttl error="..."
FAIL minio operation=get_object error="..."
FAIL milvus operation=search error="..."
```

The compose defaults avoid Docker Hub for MinIO and Milvus. If a configured
registry is unavailable in the local network, keep the compose file and
commands unchanged but override image variables in the shell, for example
`MILVUS_IMAGE`, `MINIO_IMAGE`, or `MILVUS_MINIO_IMAGE`.

## Legacy Boundary

Legacy Flask, Qdrant, and old static frontend code were removed from the current
runtime after the FastAPI + Milvus + MinIO smoke gate stabilized. They are not
Phase 1 acceptance conditions. Persistence-backed auth/chat/RAG services are
still future work; the current business routes are only the in-memory
acceptance surface.
