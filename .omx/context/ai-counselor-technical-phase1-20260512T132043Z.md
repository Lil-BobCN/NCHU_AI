# AI Counselor Technical Phase 1 Context Snapshot

Task statement: Implement the technical Phase 1 engineering foundation for the AI counselor system in `C:\Users\liuqi\Desktop\agentproject`.

Desired outcome: A Docker-based FastAPI stack under `backend/` with PostgreSQL, Redis, MinIO, and Milvus; FastAPI liveness/readiness; a real infrastructure smoke script; and docs matching the actual commands.

Known facts/evidence:
- `backend/` is the formal FastAPI backend path.
- `src/backend/` is a legacy Flask prototype and is reference-only for this phase.
- Qdrant artifacts are migration/history references, not the accepted vector database.
- Existing PRD and test spec are present at `.omx/plans/prd-ai-counselor-technical-phase1.md` and `.omx/plans/test-spec-ai-counselor-technical-phase1.md`.
- `tmux` and `omx` are available in this environment.

Constraints:
- Do not delete old Flask/Qdrant code before FastAPI + Milvus + MinIO smoke is stable.
- Do not implement the full student Q&A, admin, permission/audit/dashboard/notification, or multi-terminal business loop.
- Use the phase-one command shape: `cd backend`, `docker compose -f docker-compose.phase1.yml up -d`, `python scripts/smoke_phase1.py`, `pytest`.

Unknowns/open questions:
- Whether Docker Desktop is currently running and whether phase-one ports are free.
- Whether all new Python client dependencies are already installed in the local Python environment before verification.

Likely codebase touchpoints:
- `backend/docker-compose.phase1.yml`
- `backend/.env.example`
- `backend/requirements.txt`
- `backend/pyproject.toml`
- `backend/app/config.py`
- `backend/app/api/v1/health.py`
- `backend/app/api/v1/router.py`
- `backend/scripts/smoke_phase1.py`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/FASTAPI-SYSTEM.md`
