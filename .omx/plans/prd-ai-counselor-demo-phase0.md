# PRD Delta: AI Counselor Demo Phase 0

Date: 2026-05-17
Status: draft for product-manager approval
Parent plan: `.omx/plans/overall-development-plan-ai-counselor-demo.md`

## Phase 0 Goal

Create the requirements baseline for the independent AI Counselor Demo and reconcile older Phase 1 planning files before any new implementation work begins.

No runtime code changes are in scope for Phase 0.

## P0-N1 Evidence Inventory

### Repository Evidence

| Evidence | Current finding | Source |
| --- | --- | --- |
| Backend authority | `backend/` is the formal FastAPI backend path. | `README.md`, `PROJECT_STATE.md`, `backend/app/main.py` |
| Infrastructure baseline | Docker Compose baseline includes FastAPI, PostgreSQL, Redis, MinIO, and Milvus. | `backend/docker-compose.phase1.yml`, `README.md` |
| Health/smoke baseline | FastAPI liveness/readiness and infrastructure smoke script exist. | `backend/app/api/v1/health.py`, `backend/scripts/smoke_phase1.py`, `backend/tests/test_health.py` |
| Business API surface | Auth, student, counselor, and admin routers are present. | `backend/app/api/v1/router.py`, `backend/app/api/v1/auth.py`, `student.py`, `counselor.py`, `admin.py` |
| Current business storage | Business services are in-memory. | `backend/app/services/business.py`, `backend/tests/conftest.py`, `README.md` |
| Role/API tests | Tests cover local login, SSO callback shape, student Q&A, resources, conversations, admin knowledge, audit/stats, counselor assistance, and role denial. | `backend/tests/test_business_phase1.py` |
| Frontend product surface | No tracked production frontend product surface is present in the current file list. | `rg --files` result |
| Old planning files | Four older Phase 1 PRD/Test Spec files remain and need explicit disposition. | `.omx/plans/prd-ai-counselor-technical-phase1.md`, `.omx/plans/test-spec-ai-counselor-technical-phase1.md`, `.omx/plans/prd-ai-counselor-business-phase1.md`, `.omx/plans/test-spec-ai-counselor-business-phase1.md` |

### Product Evidence From Recent Decisions

- The frontend direction changed from embedded school-site assistant to standalone product website linked from the school official website.
- The Demo must include homepage, login, student workspace, counselor workspace, and administrator workspace.
- Desktop and mobile are both in scope.
- SSO is deferred. Phase 2 uses Demo/local login and preserves a future SSO adapter boundary.
- Simulated data is allowed, but every simulated-data touchpoint must be clearly labeled.
- Alibaba Cloud ECS 4 vCPU / 16 GiB is the later target deployment assumption, not Phase 0 implementation work.

## Assumption Cleanup

The following assumptions are removed or narrowed for the Demo route:

| Old or risky assumption | New Phase 0 position |
| --- | --- |
| The product is embedded directly into the school official website. | Replaced by a standalone main website linked from the official website. |
| SSO is mandatory before Demo login works. | SSO is deferred; Demo/local login is implemented first. |
| Real student data is needed for Demo credibility. | Rejected; use clearly labeled simulated data only. |
| Phase 3 student Q&A should be production RAG. | Rejected; Phase 3 uses deterministic answer-source adapter only. |
| Milvus/vector/embedding/provider work is required before student UI. | Deferred to Phase 7 after approval packages. |
| Real database schema is needed before admin/counselor Demo screens. | Deferred to Phase 6; earlier phases use approved in-memory/Demo boundaries. |
| Static fake screens are acceptable for the Demo. | Rejected; implemented flows must use real app paths inside the approved phase scope. |
| Mobile can be postponed. | Rejected; desktop and mobile are developed together. |
| Old Phase 1 docs can directly drive implementation. | Rejected; they are superseded for Demo planning by this Phase 0 baseline after approval. |

## Updated Demo Scope

### Required Product Surfaces

- Homepage: formal product entry and role-oriented explanation.
- Login page: Demo/local login for student, counselor, and admin.
- Student workspace: Q&A, source/resource card, fallback, and conversation context.
- Counselor workspace: simulated cases, advisory assistance, and status/action handling.
- Admin workspace: Demo knowledge/resources, seed/reset, stats/activity.

### Required Data Boundary

- All student/case/resource/stat records are simulated until a later explicit real-data approval.
- Simulated records must be visibly labeled in UI and acceptance evidence.
- Any real school resource, real student record, official SSO credential, or public deployment change requires a new approval package.

### Required Demo Success Path

Homepage -> login as student -> ask Demo question -> view answer/source -> login as counselor -> review simulated case/advisory assistance -> login as admin -> inspect/update Demo knowledge or stats.

## Old PRD/Test Spec Alignment Matrix

Disposition values:

- Keep: carry forward as an active Demo requirement or constraint.
- Narrow: carry forward in a reduced Demo form.
- Defer: valid future work but not required in the current early Demo phase.
- Convert to Demo label: keep the product idea but require simulated-data labeling.
- Delete: remove from the Demo route.

| Old file | Old clause | Disposition | Reason | New position | Supersede old file? |
| --- | --- | --- | --- | --- | --- |
| `prd-ai-counselor-technical-phase1.md` | `backend/` FastAPI as formal backend path | Keep | Current repo and docs already use FastAPI as the formal backend authority. | Global technical baseline; Phase 2+ API boundary | Yes, for Demo planning |
| `prd-ai-counselor-technical-phase1.md` | FastAPI + PostgreSQL + Redis + MinIO + Milvus local/private infrastructure | Keep/defer split | Infrastructure exists and remains the target baseline; early UI/API phases must not require all components. | Phase 6 persistence, Phase 7 RAG, Phase 9 deployment smoke | Yes |
| `prd-ai-counselor-technical-phase1.md` | Qdrant/Flask are excluded from formal acceptance | Keep | Current README says legacy Flask/static frontend/Qdrant were removed after the FastAPI/Milvus/MinIO gate stabilized. | Global technical constraint | Yes |
| `prd-ai-counselor-technical-phase1.md` | Milvus as official vector store | Defer | Vector search belongs to Phase 7 and needs RAG approval package. | Phase 7 RAG/component approval | Yes |
| `prd-ai-counselor-technical-phase1.md` | MinIO original document storage | Defer | Original documents are not needed for deterministic Phase 3 adapter. | Phase 7 storage/RAG or later ingestion package | Yes |
| `prd-ai-counselor-technical-phase1.md` | Smoke tests for PostgreSQL, Redis, MinIO, Milvus | Keep/defer split | Smoke discipline stays; full infrastructure smoke is Phase 9 or component-specific acceptance. | Phase 9 Docker/deployment smoke | Yes |
| `prd-ai-counselor-technical-phase1.md` | Readiness endpoint over infrastructure services | Keep | Useful for later deployment and health evidence. | Phase 9 smoke; backend verification | Yes |
| `prd-ai-counselor-technical-phase1.md` | Complete RAG backend foundation before business flow | Defer | The Demo should first prove role product flows, then add RAG after approval. | Phase 7 | Yes |
| `prd-ai-counselor-technical-phase1.md` | Do not complete full student Q&A/admin/permissions in technical Phase 1 | Keep as historical boundary | It explains why current backend is not the final product. | Phase 0 evidence; Phase 2-5 roadmap | Yes |
| `test-spec-ai-counselor-technical-phase1.md` | FastAPI liveness | Keep | Still valid backend readiness evidence. | Phase 2+ API verification; Phase 9 smoke | Yes |
| `test-spec-ai-counselor-technical-phase1.md` | PostgreSQL round-trip | Defer | Real persistence begins only after schema approval. | Phase 6 | Yes |
| `test-spec-ai-counselor-technical-phase1.md` | Redis round-trip and TTL | Defer | Useful for sessions/cache later, but not required for Phase 0-3 acceptance unless auth/session approval requires it. | Phase 2 auth decision or Phase 9 smoke | Yes |
| `test-spec-ai-counselor-technical-phase1.md` | MinIO object round-trip | Defer | Not required before approved document/RAG storage. | Phase 7 or Phase 9 | Yes |
| `test-spec-ai-counselor-technical-phase1.md` | Milvus vector round-trip | Defer | No vector claims before RAG approval. | Phase 7 | Yes |
| `test-spec-ai-counselor-technical-phase1.md` | Qdrant/Flask excluded from acceptance | Keep | Prevents regression to old prototype stack. | Global technical constraint | Yes |
| `test-spec-ai-counselor-technical-phase1.md` | Complete RAG answer quality out of scope | Keep | Phase 3 must not claim RAG. | Phase 3 explicit non-goal | Yes |
| `test-spec-ai-counselor-technical-phase1.md` | Failure output must identify service/operation | Keep | Good verification practice for later smoke and QA. | Phase 9 smoke and phase logs | Yes |
| `prd-ai-counselor-business-phase1.md` | School knowledge-base-driven student affairs Q&A plus counselor assistance platform | Narrow | Correct product direction, but initial Demo is smaller and staged. | Overall product target; Phases 3 and 5 | Yes |
| `prd-ai-counselor-business-phase1.md` | Student is first-priority user | Keep | Student Q&A remains core Demo proof. | Phase 3 | Yes |
| `prd-ai-counselor-business-phase1.md` | Counselor and admin are next-priority users | Keep | Required by current Demo scope. | Phases 4 and 5 | Yes |
| `prd-ai-counselor-business-phase1.md` | SSO official login | Defer | Depends on school IT and credentials; Demo uses local login. | Phase 2 SSO deferral boundary | Yes |
| `prd-ai-counselor-business-phase1.md` | Local/mock login | Keep/narrow | Becomes current Demo login model. | Phase 2 | Yes |
| `prd-ai-counselor-business-phase1.md` | User/role/org/college/class business model | Narrow/defer | Demo needs only `User/Role`; org/class profile waits for real-data/schema approval. | Contract/Data Boundary Node; Phase 6 | Yes |
| `prd-ai-counselor-business-phase1.md` | Knowledge/document/Q&A/session/log domain skeleton | Narrow | Keep minimal contracts; avoid real schema/RAG before approval. | Contract/Data Boundary Node | Yes |
| `prd-ai-counselor-business-phase1.md` | Student Q&A with source or fallback | Convert to Demo label | Required, but deterministic and simulated until RAG is approved. | Phase 3 | Yes |
| `prd-ai-counselor-business-phase1.md` | Resource direct access | Convert to Demo label | Keep as source/resource cards with Demo data. | Phase 3 | Yes |
| `prd-ai-counselor-business-phase1.md` | Multi-turn conversation/history | Narrow | Phase 3 supports Demo conversation UI within approved in-memory boundary. | Phase 3 | Yes |
| `prd-ai-counselor-business-phase1.md` | Knowledge upload/parse/index/reindex/correction | Narrow/defer | Phase 4 handles Demo resource management and seed/reset; ingestion/reindex waits for Phase 7. | Phase 4; Phase 7 | Yes |
| `prd-ai-counselor-business-phase1.md` | Counselor documents, interview outline, summary, ledger drafts, high-frequency analysis | Narrow | Phase 5 uses advisory simulated case assistance only; no broad document automation. | Phase 5 | Yes |
| `prd-ai-counselor-business-phase1.md` | Audit, permissions, statistics | Narrow | Keep role isolation and audit/stat contracts; durable persistence waits. | Contract gate; Phases 2, 4, 6 | Yes |
| `prd-ai-counselor-business-phase1.md` | Psychology diagnosis, sanctions, funding final decision, risk early warning | Delete from Demo route | High-risk and explicitly out of scope. | Non-goals | Yes |
| `prd-ai-counselor-business-phase1.md` | Enterprise WeChat/public account/multi-terminal full access | Defer | Current scope is web Demo with mobile responsiveness. | Later roadmap | Yes |
| `test-spec-ai-counselor-business-phase1.md` | SSO/local login tests | Narrow | Test Demo/local login now; SSO callback is only boundary/future adapter. | Phase 2 test spec | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Student Q&A source/fallback tests | Keep/narrow | Must test deterministic hit and unsupported fallback. | Phase 3 test spec | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Resource direct access tests | Keep/narrow | Test Demo source/resource cards. | Phase 3 test spec | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Multi-turn conversation tests | Keep/narrow | Test current/prior turns inside Demo boundary. | Phase 3 test spec | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Knowledge maintenance tests | Narrow/defer | Demo seed/reset and admin CRUD-like operations first; upload/reindex later. | Phase 4; Phase 7 | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Role isolation tests | Keep | Required for Demo credibility. | Phase 2 and cross-phase regression | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Audit trail tests | Keep as contract, defer durable storage | Key actions should be captured as audit events; durable DB waits for Phase 6. | Contract gate; Phase 6 | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Counselor assistance tests | Keep/narrow | Phase 5 tests advisory assistance only. | Phase 5 | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Basic stats tests | Keep/narrow | Admin sees derived Demo stats. | Phase 4; Phase 6 persistence hardening | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Psychology/risk/full multi-terminal exclusions | Keep | These remain explicit non-goals. | Phase 0 non-goals | Yes |

## Phase 0 PRD Acceptance Criteria

- This document exists and references current evidence.
- The standalone website, required pages, role flows, desktop/mobile scope, simulated-data labeling, SSO deferral, deterministic answer-source boundary, and contract gate are explicit.
- The old PRD/Test Spec alignment matrix covers all four old files.
- User accepts that this Phase 0 baseline supersedes the old Phase 1 docs for Demo planning.

## Phase 0 Non-Goals

- No frontend implementation.
- No backend implementation.
- No database schema/migration work.
- No RAG/vector/provider/storage integration.
- No real SSO integration.
- No real student data.
- No public server deployment.

## Rollback

Revert this Phase 0 artifact and related Phase 0 plan/log artifacts only. No runtime code should be affected.

