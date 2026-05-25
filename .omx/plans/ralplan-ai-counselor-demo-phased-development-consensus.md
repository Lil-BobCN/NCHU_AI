# RALPLAN Consensus: AI Counselor Demo Phased Development

Date: 2026-05-17
Status: consensus plan pending product-manager confirmation
Source draft: `.omx/plans/ralplan-ai-counselor-demo-phased-development-draft.md`

## Evidence Base

- Current repository runtime is FastAPI under `backend/`.
- Existing technical baseline mentions FastAPI, PostgreSQL, Redis, MinIO, Milvus, and Docker Compose.
- Existing business API surface includes local/demo auth, student, admin, and counselor endpoints, but the business layer is currently in-memory.
- No tracked production frontend surface is present in the current file list.
- Four older Phase 1 planning files remain in `.omx/plans/` and must be explicitly superseded or carried forward before new implementation work:
  - `.omx/plans/prd-ai-counselor-technical-phase1.md`
  - `.omx/plans/test-spec-ai-counselor-technical-phase1.md`
  - `.omx/plans/prd-ai-counselor-business-phase1.md`
  - `.omx/plans/test-spec-ai-counselor-business-phase1.md`
- Existing governance rule: user is product manager; Codex is lead programmer; key technical choices, UI structure, database structure, data contracts, and open-source component introduction require approval packages before implementation.

## RALPLAN-DR Summary

### Principles

1. Auditability before speed: every phase must produce interview notes, PRD/test-spec updates, approval evidence, branch/log evidence, risk register, rollback note, and acceptance evidence.
2. Demo honesty over artificial completeness: simulated data is allowed only when clearly labeled; Demo behavior must not imply real student records, production SSO, production RAG, or approved database schema before those gates.
3. Contract before UI/API build: role, knowledge, conversation, case, audit, and stats boundaries must be approved before frontend/API implementation can depend on them.
4. FastAPI remains the backend authority: external components may support the system but must not replace FastAPI as the business orchestration and API boundary.
5. Small task nodes only: each phase is delivered through narrow, reversible nodes with explicit verification and rollback notes.

### Decision Drivers

1. Demo credibility: independent website, role-specific flows, desktop/mobile usability, labeled Demo data, and source-backed answers must feel like a formal product without overstating production readiness.
2. Delivery control: work must remain small, auditable, and reversible because the user is approving as product manager.
3. Boundary discipline: UI/API, data contracts, schema, RAG, and open-source components must not drift into implementation before approval packages are accepted.

### Viable Options

#### Option A: Strict Sequential Phase Gate

Complete Phase 0 through Phase 9 in order, requiring phase acceptance before the next phase starts.

Pros:
- Maximum auditability.
- Lowest risk of unapproved architecture/UI/database drift.
- Easiest rollback and phase-by-phase evidence review.

Cons:
- Slower feedback on later UI and knowledge-answer risks.
- More waiting at approval gates.

#### Option B: Gate-Based Mainline With Limited Parallel Discovery

Keep implementation sequential, but allow read-only `autoresearch`, UI exploration, and test-spec drafting for later phases while the current phase is under review.

Pros:
- Preserves approval gates while reducing idle time.
- Surfaces frontend, contract, knowledge, and database risks earlier.
- Fits Codex-as-lead-programmer plus user-as-PM workflow.

Cons:
- Requires strict separation between research/drafting and implementation.
- Needs clear logs to avoid confusing approved work with exploratory work.

#### Option C: Team-Parallel Feature Build After Phase 0

Use `team` to split frontend, backend, tests, and docs across multiple agents once the global PRD/test spec is approved.

Pros:
- Faster after decisions are stable.
- Useful for wide phases with frontend/backend/test/doc slices.

Cons:
- Higher coordination cost.
- Higher risk of broad diffs and approval drift.
- Not appropriate before UI, contract, database, and component decisions are approved.

### Recommended Overall Route

Use Option B as the default route.

Implementation remains phase-gated and small-node based. While a phase is in approval or verification, Codex may prepare read-only research or draft approval packages for the next phase, but must not implement unapproved UI structures, API contracts, database structures, real schema, RAG/vector/provider integration, or open-source components.

Default phase lifecycle:

1. Phase intake and scope statement.
2. `$deep-interview` alignment when scope or product intent is ambiguous.
3. PRD update and test-spec update.
4. Approval package for key decisions.
5. Required `$autoresearch` where component/framework/practice selection is involved.
6. Branch creation: `phase/<number>-<slug>`.
7. Small task node implementation.
8. Targeted verification.
9. Log, acceptance evidence, risk register, and rollback note.
10. Phase acceptance summary.

## ADR

### Decision

Adopt a strict audit-gated, phase-by-phase delivery route with limited parallel read-only discovery and an explicit Contract/Data Boundary gate before UI/API implementation.

### Drivers

- The Demo must become a formal standalone product experience, not static or disconnected pages.
- The product manager must approve key decisions before implementation.
- Existing older Phase 1 PRD/Test Spec files contain useful technical/business intent but must be reconciled because this plan narrows the first Demo path.
- The current backend exists, but frontend, data contracts, persistence hardening, and retrieval integration still need controlled design and verification.

### Alternatives Considered

- Strict sequential only: safer but slower and may delay discovery of later UI and knowledge-answer risks.
- Broad team-parallel execution: faster but too risky before Phase 0 artifacts, contract boundaries, and approval packages are updated.
- Reuse old Phase 1 docs directly: rejected because they overstate first-Demo scope by mixing SSO, real schema, Milvus/embedding/provider, knowledge maintenance, counselor assistance, and full business acceptance into one phase.

### Why Chosen

This route preserves auditability while allowing non-implementation research to reduce waiting and late surprises. It also makes the old documents traceable instead of silently replacing them.

### Consequences

- Implementation can feel slower at first because Phase 0 must align old docs and Phase 1 must produce approved frontend planning artifacts before team execution.
- Phase logs and approval packages become mandatory delivery artifacts.
- Team mode is reserved for approved, decomposable phases with bounded write scopes.

### Follow-Ups

- Phase 0 must produce the old PRD/Test Spec alignment matrix before Phase 1 starts.
- Contract/Data Boundary Node must be approved before UI/API implementation.
- Each phase must explicitly decide whether `ralph`, `team`, or solo execution is the better lane.

## Approval Package Template

Every approval package must include:

- Decision title and phase/task node.
- Recommended option.
- Alternatives considered.
- Why recommended.
- Impacted files/resources.
- Data boundary impact, including Demo vs real data.
- API/UI/database/component impact.
- Risks and rollback.
- Acceptance method.
- Product-manager questions, if any.
- Explicit approval result and date.

## Phase Plan

### Phase 0: Requirements/Test Update

Goal:
Update the product and verification baseline for the independent AI Counselor Demo, and reconcile the four old Phase 1 PRD/Test Spec files before any Phase 1 work begins.

Entry Conditions:
- Existing FastAPI docs and business endpoints are accepted only as current baseline evidence, not as final Demo scope.
- No runtime code changes occur in this phase.

Key Approval Packages:
- Product scope approval: independent site, required pages, role flows, simulated-data labeling, SSO deferral.
- PRD structure approval.
- Test acceptance scope approval.
- Demo success path approval.
- Old PRD/Test Spec alignment approval.

Task Nodes:
- P0-N1: Evidence inventory and assumption cleanup.
- P0-N2: PRD delta draft.
- P0-N3: Test-spec delta draft.
- P0-N4: Approval package set for product scope, PRD structure, test scope, and Phase 1 frontend decision gates.
- P0-N5: Demo script acceptance path draft.
- P0-N6: Phase 0 log, risk register, and rollback note.
- P0-N7: Old PRD/Test Spec alignment matrix.

#### P0-N7: Old PRD/Test Spec Alignment Matrix

Goal:
Create a traceable matrix that states what happens to every old Phase 1 planning file before Phase 1 implementation.

Required Matrix Fields:
- Old file.
- Old clause.
- Disposition: keep, defer, delete, or convert to Demo label.
- Reason.
- Corresponding new PRD/Test Spec position.
- Whether this plan supersedes the old file.

Minimum Matrix:

| Old file | Old clause | Disposition | Reason | Corresponding new PRD/Test Spec position | Supersede old file? |
| --- | --- | --- | --- | --- | --- |
| `prd-ai-counselor-technical-phase1.md` | FastAPI as official backend boundary | Keep | Current repo backend and governance already treat FastAPI as the business/API authority | New PRD: backend authority and API boundary; Contract/Data Boundary Node | Yes, for Demo phase planning |
| `prd-ai-counselor-technical-phase1.md` | PostgreSQL/Redis/MinIO/Milvus Docker baseline | Defer by capability | Infrastructure remains target evidence, but Demo UI/API phases must not require Milvus or real persistence before approval | Phase 6 persistence, Phase 7 RAG; Phase 9 deployment smoke | Yes, for phased order |
| `prd-ai-counselor-technical-phase1.md` | Milvus as official vector store and Qdrant removal | Defer | Vector store choice belongs to Phase 7 RAG approval; no Phase 3 claim of RAG | Phase 7 RAG approval package | Yes |
| `prd-ai-counselor-technical-phase1.md` | MinIO original document storage | Defer | Original document storage is not required for deterministic Demo source adapter | Phase 7 or later storage/RAG package | Yes |
| `prd-ai-counselor-technical-phase1.md` | Smoke tests for FastAPI/PostgreSQL/Redis/MinIO/Milvus | Keep/defer split | Health/smoke discipline is kept; full infra smoke belongs to Phase 9 or component-specific phases | Phase 9 Docker smoke; phase verification sections | Yes |
| `test-spec-ai-counselor-technical-phase1.md` | FastAPI liveness and service readiness | Keep | Lightweight health/readiness remains valid verification pattern | Phase 2+ API verification; Phase 9 smoke | Yes |
| `test-spec-ai-counselor-technical-phase1.md` | PostgreSQL/Redis/MinIO/Milvus round-trip tests | Defer | These prove infrastructure, not initial Demo UI; each component needs approval before becoming required | Phase 6/7/9 acceptance evidence | Yes |
| `test-spec-ai-counselor-technical-phase1.md` | Qdrant exclusion | Keep | Old Qdrant path must not be accepted as new official path | Phase 7 RAG decision constraints | Yes |
| `test-spec-ai-counselor-technical-phase1.md` | Complete RAG question quality out of scope | Keep | Phase 3 must not claim RAG; deterministic adapter only | Phase 3 tightened acceptance | Yes |
| `prd-ai-counselor-business-phase1.md` | Student self-service Q&A with source/fallback | Convert to Demo label | Required for Demo, but source answer is deterministic and Demo-labeled until RAG is approved | Phase 3 Student Flow | Yes |
| `prd-ai-counselor-business-phase1.md` | SSO official login | Defer | Phase 2 uses local/Demo login; SSO adapter boundary only | Phase 2 SSO deferral and auth boundary | Yes |
| `prd-ai-counselor-business-phase1.md` | Knowledge maintenance | Narrow | Phase 4 only approves knowledge domain contract, admin UI/API behavior, Demo seed/reset | Phase 4 Admin Knowledge Flow | Yes |
| `prd-ai-counselor-business-phase1.md` | Counselor assistance | Keep as later Demo scope | Required for connected Demo story but after student/admin foundations | Phase 5 Counselor Flow | Yes |
| `prd-ai-counselor-business-phase1.md` | Audit, permission, statistics | Narrow | Audit events and stats snapshots are contract-bound; real persistence waits for Phase 6 | Contract/Data Boundary Node; Phase 6 persistence | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Login and role isolation tests | Keep/narrow | Demo accounts and role routing are Phase 2 scope; SSO callback tests are deferred | Phase 2 test spec | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Student Q&A, resource direct access, multi-turn conversation | Keep/narrow | Phase 3 covers deterministic answer-source adapter, fallback, source card, and conversation UI | Phase 3 test spec | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Knowledge upload/reindex/correction | Narrow/defer | Phase 4 Demo seed/reset and admin behavior only; reindex/vector behavior waits for Phase 7 | Phase 4; Phase 7 | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Audit trail and basic stats | Keep as contract, defer real persistence | AuditEvent and StatsSnapshot contracts are approved before UI/API; durable storage waits for Phase 6 | Contract/Data Boundary Node; Phase 6 | Yes |
| `test-spec-ai-counselor-business-phase1.md` | Counselor assistance tests | Keep as later Demo scope | Counselor workbench is Phase 5 and must remain advisory, not automated decisioning | Phase 5 test spec | Yes |

Phase 0 Acceptance Evidence:
- Updated PRD or PRD delta exists under `.omx/plans/`.
- Updated test spec or test-spec delta exists under `.omx/plans/`.
- Approval packages are present and reviewable.
- Demo success path is explicit: homepage -> login -> student Q&A -> counselor case -> admin knowledge/stats.
- P0-N7 alignment matrix exists and is accepted as a Phase 1 entry gate.
- Removed assumptions are listed, especially embedded-school-site UI, mandatory SSO, real student data, production RAG, real schema, and static fake screens.

Rollback:
- Revert Phase 0 artifact edits only.
- No runtime code changes should occur in this phase.

### Phase 1: Frontend Planning, IA, And Design-System Gate

Goal:
Produce and approve frontend stack, information architecture, design tokens, route map, and API integration points before any team-based frontend implementation.

Entry Conditions:
- Phase 0 PRD/test updates accepted.
- P0-N7 old PRD/Test Spec alignment matrix accepted.

Key Approval Packages:
- Frontend stack and build tool selection.
- UI information architecture.
- Design system direction and design tokens.
- Route map for homepage, login, student, counselor, and admin.
- API integration point map.
- Desktop/mobile navigation patterns.
- Any component library introduction.

Execution Lane:
- Initial work is solo or `$ralph`, not `$team`.
- `$team` may be used only after the approval package is accepted.
- Any team split must bind scope to the approved frontend stack, IA, design tokens, route map, and API integration point documents.

Task Nodes:
- P1-N1: Frontend stack options and recommendation.
- P1-N2: Information architecture and route map.
- P1-N3: Design token draft and responsive layout rules.
- P1-N4: API integration point map, with placeholders only where contracts are not yet approved.
- P1-N5: Approval package and Phase 1 implementation handoff.
- P1-N6: Optional post-approval frontend skeleton implementation, if explicitly released from this gate.

Acceptance Evidence:
- Approved frontend stack document.
- Approved IA document.
- Approved design tokens.
- Approved route map.
- Approved API integration point map.
- Explicit note that no team frontend implementation starts before approval.

Rollback:
- Revert Phase 1 planning artifacts or post-approval skeleton changes on the phase branch.
- Backend remains untouched unless explicitly approved.

### Contract/Data Boundary Node: Product Data Contract Gate

Goal:
Approve the minimum product/domain contract before UI/API implementation for login, student Q&A, admin knowledge, counselor cases, audit, or stats.

Position:
- This node must be completed after Phase 1 planning and before Phase 2 UI/API implementation.
- If Phase 1 post-approval skeleton only renders inert routes, it may proceed without contract-backed data calls. Any API-connected UI must wait for this node.

Required Minimum Contracts:
- `User` / `Role`
- `KnowledgeResource`
- `Conversation`
- `CounselorCase`
- `AuditEvent`
- `StatsSnapshot`

Required Contract Fields:
- Field boundary: field names, data type intent, required/optional, public/private, role visibility.
- Demo/real-data label: Demo seed, user-entered Demo data, future real school data, or system-generated.
- API read/write responsibility: frontend read-only, frontend write request, backend authoritative write, backend derived read.
- Persistence state: in-memory Demo, browser/session only, planned PostgreSQL, planned object storage, planned vector index, or derived snapshot.
- Audit requirement: none, log-only, AuditEvent required, or future durable audit.

Minimum Approval Table:

| Contract | Field boundary | Demo/real-data label | API read/write responsibility | Persistence state | Audit requirement |
| --- | --- | --- | --- | --- | --- |
| `User` / `Role` | id, display name, role, Demo account marker, session state; no real student profile | Demo seed only until SSO phase | Auth API returns session/user; backend owns role check | In-memory/session in Phase 2; PostgreSQL candidate in Phase 6 | Login success/failure becomes AuditEvent contract; durable audit waits for Phase 6 |
| `KnowledgeResource` | id, title, category, summary, source label, resource URL/file marker, active flag | Demo seed/admin-entered Demo resource | Admin API writes approved Demo resources; student API reads source cards | In-memory/seed in Phase 4; storage/vector later | Create/update/delete/enable/disable require audit contract |
| `Conversation` | id, user id/role, turns, question, answer, fallback state, source ids | Demo conversation only | Student UI writes question; backend writes answer turn | In-memory in Phase 3; PostgreSQL candidate in Phase 6 | Question/answer event audit contract |
| `CounselorCase` | id, student label, case topic, status, summary, suggested action, linked conversations | Simulated case data only | Counselor UI reads/updates case status; backend owns state | In-memory/seed in Phase 5; PostgreSQL candidate in Phase 6 | Status/action updates require audit contract |
| `AuditEvent` | actor id/role, action, target type/id, timestamp, result, metadata summary | System-generated Demo audit | Backend authoritative write; UI read only if approved | Log/in-memory first; PostgreSQL durable audit in Phase 6 | Required for auth, knowledge writes, case status, admin reset |
| `StatsSnapshot` | consultation count, fallback count, knowledge hit count, top categories, timestamp | Derived Demo stats only | Backend derives; admin UI reads | Derived from in-memory/seed until Phase 6 | Snapshot reads optional; source events audited where applicable |

Acceptance Evidence:
- Contract approval package accepted by user.
- New PRD/Test Spec positions reference each contract and its boundary.
- Any implementation handoff states which approved contract version it uses.

Stop Rule:
- If implementation needs a field, API write, persistence behavior, or audit behavior outside this contract, stop and create a contract amendment approval package.

Rollback:
- Revert contract artifacts only.
- Do not modify business code in this node.

### Phase 2: Demo Login & Role Routing

Goal:
Implement local/Demo login and route protection for student, counselor, and admin roles using the approved `User` / `Role` contract.

Entry Conditions:
- Phase 1 frontend planning accepted.
- Contract/Data Boundary Node accepted.
- Auth architecture and Demo account approval package accepted.

Key Approval Packages:
- Demo account model.
- Session/token approach.
- Route protection approach.
- Future SSO adapter boundary.
- Any auth library/component introduction.

Task Nodes:
- Define Demo role/account data contract implementation against approved contract.
- Connect login page to backend auth endpoint.
- Implement client-side role routing.
- Implement backend/API role checks where required.
- Add unauthorized/expired-session states.

Acceptance Evidence:
- Student, counselor, and admin Demo accounts log in successfully.
- Each role lands in the correct workspace.
- Role mismatch is blocked or redirected.
- Tests cover login success, bad credentials, and role access denial.
- SSO is explicitly deferred; no production SSO claim is made.

Rollback:
- Revert auth/routing changes to the approved frontend baseline.
- Preserve future SSO notes as documentation only.

### Phase 3: Student Flow With Deterministic Answer-Source Adapter

Goal:
Deliver the student Q&A flow with clearly labeled Demo data, deterministic answer-source behavior, fallback, source card, and conversation UI.

Entry Conditions:
- Phase 2 login and role routing accepted.
- Student UI/API contract approval package accepted.
- Approved `KnowledgeResource` and `Conversation` contract boundaries exist.

Key Approval Packages:
- Student page structure.
- Deterministic answer-source adapter contract.
- Answer/source display behavior.
- Conversation history behavior.
- Mobile interaction pattern.

Explicit Non-Goals:
- Do not claim RAG.
- Do not introduce Milvus, embeddings, model provider, vector schema, or document ingestion.
- Do not require MinIO/object storage.

Task Nodes:
- Build student dashboard and Q&A input.
- Connect question submission to backend deterministic answer-source adapter.
- Seed a fixed set of Demo knowledge resources for predictable matches.
- Render answer, fallback state, source/resource cards, and conversation UI.
- Add clear simulated-data labeling.
- Add tests for fixed knowledge-resource hit, no-answer fallback, source card rendering, conversation UI, and mobile layout.

Acceptance Evidence:
- Student can log in, ask a known Demo question, receive the expected deterministic answer and source card.
- Student can ask an unsupported question and receive the approved fallback.
- Conversation UI shows current and prior turns within the approved Demo boundary.
- UI never implies simulated records are real student data.
- No acceptance claim mentions RAG, vector search, embeddings, Milvus, or model providers.

Rollback:
- Revert student frontend and deterministic adapter changes for this phase.
- Keep Phase 2 login intact.

### Phase 4: Admin Knowledge Domain, UI/API Behavior, And Demo Seed/Reset

Goal:
Approve and implement admin-facing Demo knowledge behavior without introducing real schema, production ingestion, or vector/RAG infrastructure.

Entry Conditions:
- Phase 3 student flow accepted.
- Admin knowledge domain contract and behavior approval package accepted.
- Approved `KnowledgeResource`, `AuditEvent`, and `StatsSnapshot` boundaries exist.

Key Approval Packages:
- Knowledge domain contract.
- Admin UI structure.
- Admin API behavior.
- Demo seed/reset behavior.
- Data validation behavior for Demo resources.

Explicit Non-Goals:
- No real database schema.
- No partial production schema.
- No Milvus/vector/embedding/provider integration.
- No document ingestion/reindex pipeline.
- No real school resource ingestion.

Task Nodes:
- Build admin knowledge/resource list.
- Build approved Demo add/edit/delete or enable/disable operations.
- Implement Demo seed/reset path.
- Connect admin stats/activity surfaces from Demo data only.
- Add role-protected API/frontend tests.

Acceptance Evidence:
- Admin can view and modify Demo knowledge/resources through real app flows.
- Admin can reset Demo seed data through approved behavior.
- Admin changes affect deterministic student answer-source behavior where in scope.
- Basic activity/stats are visible and clearly Demo-labeled.
- No schema/migration/vector/provider work is introduced.

Rollback:
- Revert admin UI/API changes and Demo seed/reset changes from the phase branch.
- Reset Demo data only through the approved reset path.

Phase 4 Stop Rule:
- Any need for real schema, migrations, durable audit, real resource ingestion, vector index, or provider configuration moves to a Phase 6 subset and triggers a database approval package.

### Phase 5: Counselor Flow

Goal:
Deliver counselor workbench with simulated case list/detail, advisory AI-assistance-style output, and status/action handling.

Entry Conditions:
- Student and admin flows accepted enough to support a connected Demo story.
- Counselor workflow/data model approval package accepted.
- Approved `CounselorCase`, `Conversation`, and `AuditEvent` boundaries exist.

Key Approval Packages:
- Counselor UI structure.
- Case/status model.
- Assistant output contract.
- Relationship between student activity and counselor case context.

Task Nodes:
- Build counselor dashboard/case list.
- Build case detail view with simulated student context.
- Connect advisory summary/suggested response endpoint or deterministic Demo generator.
- Add case status/action updates.
- Add tests for role access, case state changes, advisory labeling, and mobile layout.

Acceptance Evidence:
- Counselor can open a simulated case, view advisory assistance, update status, and see context tied to the student Demo story.
- Assistant output is clearly advisory, not an automated decision.

Rollback:
- Revert counselor UI/API changes from this phase.
- Keep accepted student/admin surfaces intact.

### Phase 6: Persistence Hardening And Database Approval Subsets

Goal:
Move approved Demo-critical data from in-memory behavior to persistent PostgreSQL-backed storage with controlled migrations.

Entry Conditions:
- Role flows are accepted at the product level.
- Database schema and migration approval package accepted.
- Any schema subset requested by Phase 4 or later has its own approval package.

Key Approval Packages:
- Database schema.
- Migration tooling.
- Repository/service structure.
- Seed-data and reset strategy.
- Audit storage strategy.
- Rollback/downgrade strategy.

Task Nodes:
- Introduce approved migration tooling if not already present.
- Model only the approved subset of users/roles, knowledge resources, conversations, counselor cases, audit events, and stats snapshots.
- Replace in-memory services incrementally.
- Add seed/reset commands for Demo data.
- Add restart-survival tests.

Acceptance Evidence:
- Approved Demo records survive service restart.
- Backend tests cover persistence reads/writes for the approved subset.
- Migration upgrade and rollback/downgrade evidence is recorded.
- Schema work is traceable to an approval package.

Rollback:
- Use migration downgrade if available.
- Otherwise reset local Demo database volumes with explicit data-loss warning for Demo data only.

### Phase 7: Knowledge/RAG Integration

Goal:
Connect knowledge-backed answers to MinIO/Milvus or another approved RAG component while preserving fallback behavior and source citation.

Entry Conditions:
- Persistence baseline accepted.
- RAG architecture, vector schema, embedding/model provider, storage, and component choices approved.

Key Approval Packages:
- RAG framework/component selection.
- Embedding model/provider.
- Vector schema and metadata strategy.
- Object/document storage strategy.
- Source citation behavior.
- Fallback/no-answer policy.

Task Nodes:
- Define ingestion/indexing contract.
- Store original source documents or Demo resources through approved storage path.
- Index approved Demo knowledge into approved vector store.
- Connect student Q&A to retrieval path.
- Add fallback when no reliable source is found.

Acceptance Evidence:
- Student answer can cite a source/resource from the Demo knowledge base through the approved retrieval path.
- Index rebuild path is documented and smoke-tested.
- No-answer behavior is explicit and tested.
- Deterministic Phase 3 fallback can be restored by configuration.

Rollback:
- Disable RAG path behind configuration or fallback to deterministic answer-source adapter.
- Preserve original documents/resources for rebuild.

### Phase 8: Responsive QA/Product Polish

Goal:
Verify and polish the complete product experience across desktop and mobile.

Entry Conditions:
- Required functional flows are implemented and accepted enough for QA.
- Visual QA criteria approved.

Key Approval Packages:
- Viewport targets.
- Product tone and visual polish scope.
- Any new visual testing tool.
- Any major UI restructuring.

Task Nodes:
- Run responsive route checklist for homepage, login, student, counselor, and admin.
- Fix overflow, spacing, navigation, empty/loading/error states.
- Run Demo script end to end.
- Add product copy cleanup and simulated-data label consistency pass.
- Capture screenshots/evidence.

Acceptance Evidence:
- Required surfaces are usable on desktop and mobile.
- No critical text overflow or incoherent overlap.
- Demo script can be followed without manual database edits.
- Known polish gaps are logged with severity.

Rollback:
- Revert polish changes by task node.
- Preserve functional fixes separately from visual-only changes where possible.

### Phase 9: Docker/Deployment Smoke

Goal:
Prepare and smoke-test local/private deployment path for the Demo with ECS 4 vCPU / 16 GiB as the target assumption.

Entry Conditions:
- Product Demo is functionally accepted.
- Deployment topology and public exposure boundary approval package accepted.

Key Approval Packages:
- Docker/deployment topology.
- Environment variable and secret boundary.
- Infrastructure component additions.
- Public exposure/security boundary.

Task Nodes:
- Update Docker/compose/env examples for the approved Demo stack.
- Add deployment smoke checklist.
- Run backend tests, frontend build, and compose smoke.
- Verify service health/readiness and Demo script path.
- Update deployment notes and rollback instructions.

Acceptance Evidence:
- Docker Compose stack starts locally.
- Health/readiness checks pass.
- Backend tests and frontend build pass.
- Demo script completes against the composed stack.
- Server assumptions and known production gaps are documented.

Rollback:
- Revert Docker/env changes on the phase branch.
- Use compose down for local services; remove volumes only with explicit Demo-data reset intent.

## Ralph vs Team Guidance

### Best Fit For `ralph`

- Phase 0: artifact update loop, old-doc alignment matrix, and acceptance criteria tightening.
- Phase 1: initial frontend stack/IA/design-token/route-map/API-integration planning before approval.
- Contract/Data Boundary Node: contract drafting and amendment loop.
- Phase 2: login/routing completion and verification loop.
- Phase 3: deterministic student flow end-to-end completion.
- Phase 6: persistence hardening, because it needs careful sequential migration and verification.
- Phase 7: RAG integration, because retrieval correctness and fallback behavior need persistent owner iteration.
- Phase 9: deployment smoke, because it needs one owner to chase failures to closure.

### Best Fit For `team`

- Phase 1 post-approval skeleton only: split by approved frontend shell, design tokens, route map, and tests/docs.
- Phase 4: admin knowledge flow, after contract/behavior approval; split into admin UI, backend API, Demo seed/reset, tests.
- Phase 5: counselor flow, after workflow approval; split into counselor UI, backend case/advisory contract, tests, Demo script updates.
- Phase 8: responsive QA/product polish; split into visual QA, mobile fixes, copy/labels, regression checks.

### Use Solo Execution Instead

- Any single approval package draft.
- Any one PRD/test-spec edit.
- Any narrow bug fix discovered during verification.
- Any contract amendment that affects only one contract and has no implementation.

## Phase 0 First Batch Small Task Nodes

### P0-N1: Evidence Inventory And Assumption Cleanup

Goal:
Create a short inventory of current repo state and remove obsolete assumptions from the next PRD/test baseline.

Approved Scope:
- Read existing `.omx/`, `README.md`, `PROJECT_STATE.md`, docs, and backend API files.
- No code edits.

Decision Gates:
- Product positioning changes require approval.

Files Likely Affected:
- `.omx/plans/prd-ai-counselor-demo-phase0.md`
- `.omx/plans/test-spec-ai-counselor-demo-phase0.md`
- `.omx/logs/phase-00-requirements-test-update.md`

Tests/Verification:
- Evidence list cites current runtime and existing API boundary.
- Obsolete assumptions are explicitly listed.

Rollback Note:
- Revert Phase 0 artifact files only.

### P0-N2: PRD Delta Draft

Goal:
Draft PRD changes for independent site, required pages, role flows, mobile scope, simulated-data labeling, SSO deferral, deterministic Demo answer-source behavior, and contract gates.

Approved Scope:
- Requirements artifact only.
- No UI or backend implementation.

Decision Gates:
- Any product positioning change requires an approval package.

Files Likely Affected:
- `.omx/plans/prd-ai-counselor-demo-phase0.md`

Tests/Verification:
- PRD includes homepage, login, student, counselor, admin, desktop/mobile, simulated-data label, non-goals, Demo script, old-doc supersession, and contract gate.

Rollback Note:
- Revert the PRD delta file.

### P0-N3: Test-Spec Delta Draft

Goal:
Draft acceptance tests and evidence requirements for the full Demo.

Approved Scope:
- Test planning artifact only.
- No executable tests yet unless separately approved in a later implementation phase.

Decision Gates:
- Test scope that changes product obligations requires approval.

Files Likely Affected:
- `.omx/plans/test-spec-ai-counselor-demo-phase0.md`

Tests/Verification:
- Test spec covers route presence, login/routing, contract gate, deterministic student Q&A, admin knowledge seed/reset, counselor case, persistence, RAG fallback/source citation when later approved, responsive QA, and Docker smoke.

Rollback Note:
- Revert the test-spec delta file.

### P0-N4: Approval Package Set

Goal:
Prepare approval packages for product scope, PRD structure, test scope, Phase 1 frontend decision gates, and the Contract/Data Boundary Node.

Approved Scope:
- Approval package drafting only.

Decision Gates:
- User approval required before Phase 1 implementation and before any UI/API implementation bound to contracts.

Files Likely Affected:
- `.omx/plans/approval-packages-ai-counselor-demo-phase0.md`

Tests/Verification:
- Each package uses the approval template in this plan.

Rollback Note:
- Revert the approval package artifact.

### P0-N5: Demo Script Acceptance Path

Goal:
Define the minimum repeatable Demo path for future QA and stakeholder demonstrations.

Approved Scope:
- Script artifact only.

Decision Gates:
- Use of real school resources or real student data is out of scope and requires approval.

Files Likely Affected:
- `.omx/plans/demo-script-ai-counselor-demo.md`

Tests/Verification:
- Script path is executable conceptually from homepage through all three roles.
- Every simulated-data touchpoint is marked.

Rollback Note:
- Revert the demo script artifact.

### P0-N6: Phase 0 Log, Risk Register, And Rollback Note

Goal:
Create the audit trail for Phase 0.

Approved Scope:
- Logs and risk documentation only.

Decision Gates:
- None unless new scope is discovered.

Files Likely Affected:
- `.omx/logs/phase-00-requirements-test-update.md`

Tests/Verification:
- Log records task nodes, approvals needed, evidence, risks, and rollback instructions.

Rollback Note:
- Revert the Phase 0 log.

### P0-N7: Old PRD/Test Spec Alignment Matrix

Goal:
Create and approve the matrix defined in Phase 0 before Phase 1 starts.

Approved Scope:
- Planning artifact only.
- No code edits.

Decision Gates:
- User approval required because it supersedes the old Phase 1 planning files for this Demo route.

Files Likely Affected:
- `.omx/plans/prd-ai-counselor-demo-phase0.md`
- `.omx/plans/test-spec-ai-counselor-demo-phase0.md`
- `.omx/plans/approval-packages-ai-counselor-demo-phase0.md`

Tests/Verification:
- Matrix covers all four old files and all required fields.
- Matrix states whether this plan supersedes each old file.

Rollback Note:
- Revert matrix edits only; old files remain unchanged.

## Global Risks

- Frontend stack is not yet approved; Phase 1 must not start implementation before approval.
- Old Phase 1 docs are broader than this Demo route; failure to supersede them will cause scope drift.
- Contract boundaries can sprawl; stop when a field/API/persistence/audit need falls outside the approved contract.
- Existing business layer is in-memory; Demo credibility depends on clear labeling until Phase 6 persistence hardening.
- Phase 3 can be misread as RAG; acceptance must say deterministic answer-source adapter only.
- Phase 4 can accidentally introduce real schema; real schema belongs only to Phase 6 subsets with database approval.
- Mobile scope can become broad; Phase 8 should prioritize required flows over decorative polish.
- ECS 4 vCPU / 16 GiB is a target assumption, not production capacity proof.

## Stop Rules

- Stop implementation when a task reveals a new key technical, UI, data contract, database, RAG/provider, or component decision not covered by an approval package.
- Stop Phase 1 implementation until frontend stack, IA, design tokens, route map, and API integration points are approved.
- Stop UI/API implementation until the Contract/Data Boundary Node is approved.
- Stop Phase 3 if work requires vector search, embeddings, Milvus, model provider, MinIO, or ingestion.
- Stop Phase 4 if work requires real schema, migrations, durable audit, real school resources, vector index, or provider configuration.
- Stop phase progression when acceptance evidence is missing.
- Stop public/deployment expansion when security, SSO, real school resource, or real student data boundaries are crossed.

## Consensus Checklist

- Critic point 1 handled: Phase 0 includes P0-N7 old PRD/Test Spec alignment matrix with required fields and four old files.
- Critic point 2 handled: independent Contract/Data Boundary Node added before UI/API implementation.
- Critic point 3 handled: Phase 1 starts solo/`ralph` for frontend stack, IA, design tokens, route map, and API integration points; `team` is post-approval only and bound to approved files.
- Critic point 4 handled: Phase 3 uses deterministic answer-source adapter and forbids premature RAG/Milvus/embedding/provider claims.
- Critic point 5 handled: Phase 4 forbids real schema and limits scope to knowledge domain contract, admin UI/API behavior, and Demo seed/reset; real schema moves to Phase 6 subset with database approval package.
