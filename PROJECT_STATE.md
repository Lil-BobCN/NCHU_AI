# Project State

Last updated: 2026-05-26

## Workflow Baseline

The mandatory project workflow baseline is now tracked in
`docs/development-process.md`.

Before any future implementation, review, planning, research, or verification
work, Codex and other AI agents must read that workflow document and use it as
the human-AI collaboration process for this repository. The operational entry
point for agents is `AGENTS.md`, which points back to the workflow baseline and
the required project context files.

Workflow changes require a new SDAR or explicit process revision record.

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

The business surface is in-memory for now. The full persistence-backed student
Q&A loop, admin UI, notifications, dashboards, and frontend delivery are still
future work.

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
