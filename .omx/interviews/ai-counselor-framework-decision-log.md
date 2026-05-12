# AI Counselor Framework Decision Log

## 2026-05-12 Deep Interview Decision

Current development phase is aligned to the technical proposal's Phase 1.

In scope for the current phase:
- Docker-based local/private deployment baseline.
- FastAPI as the formal backend direction.
- PostgreSQL for structured data.
- Redis for cache/session/task state foundation.
- MinIO for original document/object storage.
- Milvus as the vector database.
- Basic service health/smoke validation for the infrastructure stack.

Acceptance gate:
- One command starts the local/private deployment stack.
- FastAPI exposes a basic liveness endpoint.
- FastAPI or an automated smoke command verifies real connectivity and round-trip behavior for PostgreSQL, Redis, MinIO, and Milvus.
- PostgreSQL smoke test must create or use a test table, insert, read, and clean up data.
- Redis smoke test must write, read, and validate expiry behavior.
- MinIO smoke test must create/use a bucket, upload, download, and delete a test object.
- Milvus smoke test must create/use a collection, insert a 1024-dimensional test vector, build/load an index as needed, and perform TopK search.
- Smoke failures must identify the failing service clearly enough for local deployment troubleshooting.

Deferred product roadmap:
- The requirements checklist's Phase 1 business features remain valid as future development direction.
- Deferred items include the full student-facing intelligent Q&A experience, resource direct retrieval, knowledge-base management UI, role/permission system, logs/audit/dashboard, notification/document generation, and multi-terminal access.
- These should be planned as later sub-phases after the technical Phase 1 foundation is stable.

Decision rationale:
- The current project is still at the infrastructure/framework stage.
- Mixing all requirements-checklist Phase 1 business features into the first technical phase would make the phase too broad for clean delivery and maintenance.
- The framework should first make deployment, storage, vector indexing, model integration boundaries, and operational ownership explicit.

Migration boundary:
- The formal backend direction is `backend/` FastAPI plus Milvus.
- The old Flask stack under `src/backend/` is retained only as prototype/reference material during the current phase.
- Existing Qdrant-based FastAPI artifacts are treated as migration targets, not the accepted final vector-store direction.
- Current-phase acceptance must not depend on the Flask stack or Qdrant stack passing.
- Cleanup/removal of legacy Flask/Qdrant paths should happen only after the FastAPI + Milvus infrastructure smoke gate is stable, so historical behavior remains inspectable during migration.
