# NCHU AI Counselor

## Project Workflow Contract

All human-AI collaboration in this repository must follow
[`docs/development-process.md`](docs/development-process.md). Before any future
work starts, Codex or any other AI agent should read that document together with
[`AGENTS.md`](AGENTS.md), this README, `PROJECT_STATE.md`, and the relevant
`.omx` artifacts. The workflow document is the default baseline for context
engineering, clarification, SDAR approval, small task execution, verification
evidence, and acceptance logging.

Changes to this workflow require a new SDAR or explicit process revision record.

This repository is now scoped to the formal FastAPI backend plus a lightweight
in-memory business Phase 1 surface.

Project-level design context is defined in `PRODUCT.md` and `DESIGN.md`. The
design entry point is configured to use
[VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md)
as an optional reference library; usage notes live in
`docs/design/awesome-design-md.md`.

The technical Phase 1 foundation still covers FastAPI, PostgreSQL, Redis,
MinIO, Milvus, Docker local/private deployment, liveness, readiness, and the
automated smoke gate. On top of that, the repo now exposes in-memory business
routes for auth, student Q&A/resources/conversations, knowledge maintenance,
audit, stats, and counselor assistance.

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

Mounted Phase 1 routes include:

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

FastAPI's generated `/docs`, `/redoc`, and `/openapi.json` routes are disabled
in this phase. The business surface is intentionally in-memory so the endpoints
can be validated before persistence-backed services land.

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
