# Deep Interview Spec: AI Counselor Technical Phase 1 Framework

Date: 2026-05-12
Owner context: QL group
Recommended next workflow: `$ralplan`

## Target Result

Create an execution-ready development framework for the AI counselor project's current phase. The framework must align the team on what is being built now, what is deferred, how services are deployed locally/private, and how future model integration, operations, and maintenance should be handled.

## Authoritative Current Phase

Current implementation should follow the technical proposal's Phase 1, not the full business scope of the requirements checklist's Phase 1.

The requirements checklist's Phase 1 remains a valid product roadmap and should guide later sub-phases after the technical foundation is stable.

## Current Formal Architecture Direction

- Backend: FastAPI under `backend/`.
- Legacy prototype: Flask under `src/backend/`, reference only.
- Vector database: Milvus.
- Existing Qdrant code: migration target/reference only.
- Structured database: PostgreSQL.
- Cache/session/task state: Redis.
- Object/original document storage: MinIO.
- Deployment: Docker-based local/private deployment baseline.

## Current Repository Gap

Evidence from the existing codebase:
- `docker-compose.yml` currently starts the legacy Flask + Nginx + Redis stack.
- `src/backend/` contains the legacy Flask implementation.
- `backend/` already contains a FastAPI skeleton.
- `backend/docker-compose.rag.yml` currently uses Qdrant instead of Milvus and does not include MinIO.
- `backend/app/config.py` has `qdrant_url` but no Milvus/MinIO settings.
- `backend/app/api/deps.py`, `backend/app/rag/retriever.py`, and `backend/scripts/ingest_documents.py` depend on Qdrant.
- `backend/app/api/v1/health.py` has a basic liveness endpoint but not a full infrastructure smoke/readiness gate.

## In Scope

- Define one formal FastAPI + Milvus backend path.
- Define Docker service topology for FastAPI, PostgreSQL, Redis, MinIO, and Milvus.
- Define service healthchecks and readiness behavior.
- Define env var naming and local/private deployment conventions.
- Define smoke verification for PostgreSQL, Redis, MinIO, and Milvus.
- Define how legacy Flask/Qdrant code is isolated during migration.
- Define documentation and maintenance rules so non-AI contributors can operate the project.

## Out of Scope

- Completing all student-facing product functions from the requirements checklist.
- Completing a knowledge-base admin UI.
- Completing permission/audit/dashboard/notification/document-generation features.
- Enterprise WeChat/公众号/multi-terminal rollout.
- Full frontend framework migration.
- Production SSO/security hardening beyond current-phase service boundaries.
- Removing legacy Flask/Qdrant code before the new FastAPI + Milvus smoke gate is stable.

## Acceptance Criteria

- One command starts the current-phase stack.
- FastAPI exposes a liveness endpoint.
- A smoke command or readiness endpoint verifies PostgreSQL, Redis, MinIO, and Milvus with real round-trip operations.
- PostgreSQL smoke: create/use test table, insert, read, cleanup.
- Redis smoke: write, read, validate expiry.
- MinIO smoke: create/use bucket, upload, download, delete test object.
- Milvus smoke: create/use collection, insert a 1024-dimensional vector, build/load index as needed, perform TopK search.
- Every smoke failure clearly names the failing service and the failed operation.
- The current-phase acceptance report does not require Flask or Qdrant to pass.

## Migration Boundary

The project should formally move to `backend/` FastAPI + Milvus now. During the current phase:
- Do not treat Flask as the formal backend.
- Do not treat Qdrant as the formal vector database.
- Keep Flask/Qdrant artifacts inspectable as migration references.
- Avoid destructive cleanup until the new FastAPI + Milvus infrastructure smoke gate is passing.

## Future Roadmap Captured From Requirements Checklist

After the technical foundation is stable, later sub-phases should cover:
- Student-facing 7x24 intelligent Q&A.
- Policy source citation and direct resource links.
- Knowledge-base management.
- Role/permission/log/audit/dashboard capabilities.
- Notification and document-generation assistance.
- Multi-terminal access.
- Official-site embedded student entry.

## Planning Tasks For `$ralplan`

The next planning pass should produce:
- PRD for technical-proposal Phase 1.
- Test specification for infrastructure smoke validation.
- File-level migration plan from Qdrant to Milvus.
- Docker topology and service ownership rules.
- Environment variable contract.
- Legacy isolation policy.
- Documentation structure for future operators and non-AI maintainers.
- Risk list and rollback/debugging procedure for local/private deployment.

## Stop Condition For Planning

Planning is complete when the repository has an approved PRD and test spec that are specific enough for implementation without asking another scope question.
