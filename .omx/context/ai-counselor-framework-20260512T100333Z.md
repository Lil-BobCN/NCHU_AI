# Deep Interview Context Snapshot: AI Counselor Framework

Task statement: Clarify requirements and align thinking before creating the development framework for the AI counselor system.

Desired outcome: A requirements-backed framework that governs implementation, maintenance, model integration, local deployment, and non-AI operational needs.

Stated solution: Use Milvus as the vector database and migrate the backend directly to FastAPI.

Probable intent hypothesis: The user wants to avoid continuing the current split Flask/Qdrant prototype path and instead establish a maintainable first-phase foundation aligned with the formal requirement and technical documents.

Known facts/evidence:
- Requirements document: `AI 辅导员系统建设需求清单（2026.4第一版）(1).docx`.
- Technical方案 document: `南昌航空学校RAG智能问答系统技术方案(1).docx`.
- Current repository has Flask prototype plus FastAPI RAG skeleton.
- Current FastAPI skeleton uses Qdrant, while the user and technical方案 require Milvus.
- Current technical方案 phase 1 delivery is Docker environment, PostgreSQL, Redis, MinIO, and Milvus.
- Requirements document phase 1 business outcome is a lightweight system: 7x24 intelligent Q&A, policy-source citation, resource direct links, knowledge-base management, permissions/logs/dashboard, notification assistance, and multi-terminal access.

Constraints:
- Deep-interview mode only; no implementation during this phase.
- One interview question per round.
- Current session is outside tmux; use native/plain question path.
- Framework must support later operations, maintenance, model integration, and local/private deployment.
- User has declared Milvus and direct FastAPI migration as decisions.

Unknowns/open questions:
- Whether phase 1 should deliver only infrastructure readiness or also the full business-facing lightweight AI counselor features.
- Which legacy Flask UI/logic should be preserved, migrated, or discarded.
- What non-goals should be explicit for phase 1.
- Which decisions the agent may make autonomously in the framework design.
- Which deployment target is authoritative: local dev, school intranet pilot, or production-ready private deployment.

Decision-boundary unknowns:
- Whether to treat the existing website embedding/NCHU_XGC page as a required phase-1 access channel.
- Whether front-end migration to Vue3 is in phase 1 or later.
- Whether Qdrant code should be removed immediately or abstracted during migration.
- Whether document parsing is part of current phase or only interface scaffolding for the QM group.

Likely codebase touchpoints:
- `backend/docker-compose.rag.yml`
- `backend/app/config.py`
- `backend/app/rag/retriever.py`
- `backend/scripts/ingest_documents.py`
- `backend/app/api/deps.py`
- `backend/app/main.py`
- `nginx.conf`
- `static/rag-chat.html`
- `src/backend/`

Prompt-safe initial-context summary status: not_needed
