# Deep Interview Transcript: AI Counselor Framework

Date: 2026-05-12
Profile: standard
Type: brownfield
Final ambiguity: ~8%
Status: crystallized for planning handoff

## Source Materials

Documents inserted into the project:
- `docs/AI辅导员助手 - 开发计划表.docx`
- `docs/AI 辅导员系统建设需求清单（2026.4第一版）(1).docx`
- `docs/南昌航空学校RAG智能问答系统技术方案(1).docx`

Context snapshot:
- `.omx/context/ai-counselor-framework-20260512T100333Z.md`

Decision log:
- `.omx/interviews/ai-counselor-framework-decision-log.md`

## Crystallized Intent

The current work is not to complete every product function listed in the requirements checklist's Phase 1. The current work is to build the technical proposal's Phase 1 foundation so later product functions can be developed, deployed, maintained, and operated consistently.

The formal direction is:
- Backend: FastAPI.
- Vector database: Milvus.
- Structured data: PostgreSQL.
- Cache/session/task state foundation: Redis.
- Object/original document storage: MinIO.
- Deployment baseline: Docker-based local/private deployment.

## Brownfield Evidence

Current repository state:
- Root `docker-compose.yml` is still the Flask + Nginx + Redis stack.
- `src/backend/` contains the legacy Flask prototype.
- `backend/` contains a FastAPI RAG skeleton.
- `backend/docker-compose.rag.yml` currently composes FastAPI + PostgreSQL + Qdrant + Redis.
- `backend/app/config.py`, `backend/app/api/deps.py`, `backend/app/rag/retriever.py`, and `backend/scripts/ingest_documents.py` currently reference Qdrant.
- `backend/app/api/v1/health.py` already exposes a basic FastAPI health endpoint.
- There is no accepted current-phase MinIO/Milvus stack yet.

## Interview Rounds

Round 1: Phase boundary
- Question: Should Phase 1 be judged by a student-usable minimum knowledge-base Q&A loop?
- Answer summary: User requested a detailed explanation of this loop.
- Effect: Exposed that product-facing scope and infrastructure scope were being mixed.

Round 2: Student entry point
- Question: If doing a minimum Q&A loop, which student entry should be preferred?
- Answer: Campus official-site embedded page.
- Effect: Useful future product direction, but later deferred from current technical Phase 1.

Round 3: Non-goals pressure
- Question: Should current Phase 1 be limited to embedded RAG Q&A + infrastructure + minimal ingestion, deferring admin, enterprise WeChat, notifications, dashboards, complex parsing, and student profile?
- Answer summary: User asked whether these were beyond the requirements checklist's first phase and whether the suggestion strictly followed the requirement document.
- Effect: Clarified the need to separate the requirements checklist roadmap from the technical proposal's current phase.

Round 4: Authoritative phase source
- Question: Should current Phase 1 strictly cover all requirements-checklist Phase 1 features, or follow technical-proposal Phase 1 first and record requirements-checklist Phase 1 as later direction?
- Answer: Follow the technical proposal's Phase 1; write requirements-checklist Phase 1 into the log as later development direction.
- Effect: Current scope became infrastructure/framework readiness.

Round 5: Acceptance gate
- Question: Confirm acceptance as one-command startup + FastAPI connectivity to PostgreSQL, Redis, MinIO, and Milvus with automated smoke tests.
- Answer: Yes.
- Effect: Acceptance criteria became concrete and testable.

Round 6: Migration boundary
- Question implied by prior recommendation: Should the formal route directly move to FastAPI + Milvus while retaining Flask/Qdrant only as reference until the new stack is stable?
- Answer: Yes.
- Effect: Legacy stacks are reference only and excluded from current acceptance.

## In Scope Now

- Create a Docker-based local/private deployment baseline.
- Make FastAPI the formal backend path.
- Replace the current Qdrant formal direction with Milvus.
- Add MinIO to the formal infrastructure baseline.
- Keep PostgreSQL and Redis in the formal infrastructure baseline.
- Provide a liveness endpoint and service-level readiness/smoke verification.
- Make failures identify the failing service clearly.
- Preserve the requirements-checklist Phase 1 product functions as roadmap items.

## Out of Scope Now

- Full student-facing AI Q&A experience.
- Complete knowledge-base management UI.
- Role/permission/audit/dashboard completion.
- Notification/document generation completion.
- Enterprise WeChat or multi-terminal delivery.
- Full frontend redesign or Vue3 migration.
- Immediate deletion of legacy Flask/Qdrant code before the new stack is stable.

## Acceptance Criteria

- One command starts the current-phase stack.
- FastAPI exposes a basic liveness endpoint.
- A smoke command or readiness endpoint verifies round-trip behavior for:
  - PostgreSQL: create/use test table, insert, read, cleanup.
  - Redis: write, read, validate expiry.
  - MinIO: create/use bucket, upload, download, delete object.
  - Milvus: create/use collection, insert a 1024-dimensional vector, build/load index as needed, TopK search.
- Smoke failures report the failing service and enough detail for local deployment troubleshooting.
- Flask and Qdrant are not required for current-phase acceptance.

## Pressure Pass Findings

- The phrase "Phase 1" was ambiguous because the requirements checklist and the technical proposal define different levels of Phase 1.
- Treating the requirements checklist's Phase 1 as the immediate implementation target would overload the first delivery.
- The safer delivery order is: infrastructure foundation first, then minimum student Q&A loop, then management/operations features.
- Keeping legacy code as reference reduces migration risk, but acceptance must not depend on legacy systems.

## Recommended Handoff

Use `$ralplan` next to produce:
- A PRD for technical-proposal Phase 1.
- A test specification for service readiness and smoke validation.
- A repository framework/migration plan that defines formal paths, legacy boundaries, environment variables, service ownership, and operational handoff rules.

Do not start implementation until that framework plan is written and reviewed.
