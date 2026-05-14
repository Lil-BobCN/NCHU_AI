# Project State

Last updated: 2026-05-13

## Current Runtime

The repository is scoped to the FastAPI technical Phase 1 backend in
`backend/`.

Accepted Phase 1 stack:

- FastAPI API container
- PostgreSQL
- Redis
- MinIO
- Milvus standalone with etcd and internal MinIO

The canonical startup command is:

```powershell
cd backend
docker compose -f docker-compose.phase1.yml up -d
```

## API Surface

Mounted endpoints:

- `GET /api/v1/health`
- `GET /api/v1/readiness`

The full student Q&A loop, auth, chat sessions, admin UI, notifications,
dashboards, and frontend delivery are intentionally outside the current phase.

## Legacy Cleanup

The old Flask backend, old static frontend, root Flask compose/Docker/nginx
files, Qdrant compose file, and Qdrant ingestion script were removed after the
FastAPI + Milvus + MinIO smoke gate stabilized.

Historical design rationale remains available in `.omx/` planning artifacts and
git history. Current tracked runtime files and Phase 1 docs supersede older
interview/planning notes when they conflict.

## Verification Commands

```powershell
cd backend
docker compose -f docker-compose.phase1.yml up -d
..\.venv\Scripts\python.exe scripts\smoke_phase1.py
..\.venv\Scripts\python.exe -m pytest
```

Use the project virtual environment. The machine's default `python` may point
to Anaconda and may not have the backend dependencies installed.
