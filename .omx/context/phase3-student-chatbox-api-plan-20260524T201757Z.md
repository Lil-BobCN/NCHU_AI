# Context Snapshot: Phase 3 Student Chatbox/API Plan

Task statement:
- Evaluate whether Phase 3 can start with an isolated student Chatbox page, then merge into the main frontend later.
- Evaluate whether Phase 3 should connect the Chatbox to a configured model/API with web-search behavior instead of Demo deterministic data.
- Reframe all Phase 3 work around the user's preferred development line if feasible.

Desired outcome:
- Provide product-manager-readable options, tradeoffs, recommendation, risks, rollback, and a task sequence.
- Keep the answer grounded in existing project files and approved phase gates.

Known evidence:
- Phase 3 is defined as student Q&A with deterministic answer-source adapter, fallback, source cards, and conversation UI.
- Phase 3 explicitly excludes RAG, Milvus, embeddings, model provider, vector schema, and document ingestion.
- Current backend has student routes for questions, resources, and conversations.
- Current frontend `WorkspacePage` is still a generic role workspace skeleton.
- Local backend config currently contains PostgreSQL, Redis, MinIO, Milvus, and CORS settings, but no LLM/model provider or web-search API configuration.

Constraints:
- No implementation in this planning turn.
- Do not claim RAG or live model/search capability unless separately approved and configured.
- Any new model/provider/web-search integration changes the approved Phase 3 boundary and needs an approval amendment or later-phase lane.
- Frontend may be built in an isolated route/component/lab first if integration contracts remain explicit.

Unknowns:
- Which exact model/provider the product manager believes is already configured.
- Whether the desired first model connection is a temporary developer preview, a Phase 3 scope amendment, or a Phase 7/RAG-boundary experiment.
- Whether the isolated page should be inside the Vite app route tree or outside `frontend/src/App.tsx` as a standalone prototype.

Likely touchpoints:
- `.omx/plans/ralplan-ai-counselor-demo-phased-development-consensus.md`
- `.omx/plans/overall-development-plan-ai-counselor-demo.md`
- `.omx/decisions/SDAR-0006-product-data-contract-boundary.md`
- `frontend/src/App.tsx`
- `frontend/src/App.css`
- `backend/app/api/v1/student.py`
- `backend/app/services/business.py`
- `backend/app/schemas/business.py`
- `backend/app/config.py`
- `backend/.env.example`
