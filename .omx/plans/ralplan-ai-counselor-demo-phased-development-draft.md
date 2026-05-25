# RALPLAN Draft: AI Counselor Demo Phased Development

Date: 2026-05-17
Status: draft for product-manager review

## Evidence Base

- Current repository runtime is FastAPI under `backend/`.
- Existing technical stack: FastAPI, PostgreSQL, Redis, MinIO, Milvus, Docker Compose.
- Existing business API surface includes local/demo auth, student, admin, and counselor endpoints, but the business layer is currently in-memory.
- No tracked production frontend surface is present in the current file list.
- Existing governance rule: user is product manager; Codex is lead programmer; key technical choices, UI structure, database structure, and open-source component introduction require approval packages before implementation.

## RALPLAN-DR Summary

### Principles

1. Auditability before speed: every phase must produce interview notes, PRD/test-spec updates, branch/log evidence, risk register, rollback note, and acceptance evidence.
2. Real application chain over static fake screens: simulated data is allowed only when clearly labeled and routed through real app flows, APIs, persistence, and knowledge paths where implemented.
3. FastAPI remains the backend authority: external components may support the system but must not replace FastAPI as the business orchestration and API boundary.
4. Product-manager approval at decision gates: key technical selection, UI structure, database structure, and open-source component introduction stop at an approval package.
5. Small task nodes only: each phase is delivered through narrow, reversible nodes with explicit verification and rollback notes.

### Decision Drivers

1. Demo credibility: independent website, role-specific flows, desktop/mobile usability, and source-backed answers must feel like a formal product.
2. Delivery control: the work must remain small, auditable, and reversible because the user is approving as product manager.
3. Future compatibility: SSO, persistence, RAG, Docker deployment, and ECS sizing must be prepared without blocking the Demo on production dependencies.

### Viable Options

#### Option A: Strict Sequential Phase Gate

Complete Phase 0 through Phase 9 in order, requiring phase acceptance before the next phase starts.

Pros:
- Maximum auditability.
- Lowest risk of unapproved architecture/UI/database drift.
- Easiest rollback and phase-by-phase evidence review.

Cons:
- Slower feedback on later UI and RAG risks.
- More waiting at approval gates.

#### Option B: Gate-Based Mainline With Limited Parallel Discovery

Keep implementation sequential, but allow read-only `autoresearch`, UI exploration, and test-spec drafting for the next phase while the current phase is under review.

Pros:
- Preserves approval gates while reducing idle time.
- Surfaces open-source, UI, and database risks earlier.
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
- Not appropriate before UI, database, and component decisions are approved.

## Recommended Overall Route

Use Option B as the default route.

Implementation remains phase-gated and small-node based. While a phase is in approval or verification, Codex may prepare read-only research or draft approval packages for the next phase, but must not implement unapproved UI structures, database structures, technical selections, or open-source components.

Default phase lifecycle:

1. Phase intake and scope statement.
2. `$deep-interview` alignment.
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

Adopt a strict audit-gated, phase-by-phase delivery route with limited parallel read-only discovery.

### Drivers

- The Demo must become a formal standalone product experience, not a collection of static or disconnected pages.
- The product manager must approve key decisions before implementation.
- The current backend exists, but frontend, persistence hardening, and RAG integration still need controlled design and verification.

### Alternatives Considered

- Strict sequential only: safer but slower and may delay discovery of later RAG/UI risks.
- Broad team-parallel execution: faster but too risky before Phase 0 artifacts and approval packages are updated.

### Why Chosen

This route preserves auditability while allowing non-implementation research to reduce waiting and late surprises.

### Consequences

- Implementation can feel slower at first because Phase 0 must update PRD/test and approval structure.
- Phase logs become mandatory delivery artifacts, not optional notes.
- Team mode is reserved for approved, decomposable phases.

### Follow-Ups

- Phase 0 must produce the first approval packages and update PRD/test-spec before Phase 1 starts.
- Each phase must explicitly decide whether `ralph` or `team` is the better execution lane.

## Phase Plan

### Phase 0: Requirements/Test Update

Goal:
Update the product and verification baseline for the independent AI Counselor Demo.

Entry Conditions:
- Existing FastAPI Phase 1 docs and business endpoints are accepted as the current technical baseline.
- User confirms this plan direction or provides corrections.

Key Approval Packages:
- Product scope approval: independent site, required pages, role flows, simulated-data labeling, SSO deferral.
- PRD structure approval.
- Test acceptance scope approval.
- Demo success path approval.

Autoresearch Tasks:
- Optional only: review lightweight PRD/test-spec governance examples if the current artifact format proves insufficient.

Task Nodes:
- P0-N1: Evidence inventory and assumption cleanup.
- P0-N2: PRD delta draft.
- P0-N3: Test-spec delta draft.
- P0-N4: Approval package set for product scope, PRD structure, and test scope.
- P0-N5: Demo script acceptance path draft.
- P0-N6: Phase 0 log, risk register, and rollback note.

Acceptance Evidence:
- Updated PRD or PRD delta exists under `.omx/plans/`.
- Updated test spec or test-spec delta exists under `.omx/plans/`.
- Approval packages are present and reviewable.
- Demo success path is explicit: homepage -> login -> student Q&A -> counselor case -> admin knowledge/stats.
- Removed assumptions are listed, especially embedded-school-site UI, mandatory SSO, real student data, and static fake screens.

Rollback:
- Revert Phase 0 artifact edits only.
- No runtime code changes should occur in this phase.

### Phase 1: Frontend Skeleton & Design System

Goal:
Create the frontend foundation for homepage, login, student shell, counselor shell, and admin shell across desktop and mobile.

Entry Conditions:
- Phase 0 PRD/test updates accepted.
- UI information architecture and design-system approval package accepted.

Key Approval Packages:
- Frontend stack and build tool selection.
- UI information architecture.
- Design system direction.
- Desktop/mobile navigation patterns.
- Any component library introduction.

Autoresearch Tasks:
- Compare mature frontend stack/component options compatible with FastAPI and Docker deployment.
- Compare responsive app-shell patterns for role-based products.

Task Nodes:
- Create approved frontend project structure.
- Add routing skeleton for all required pages.
- Add responsive app shell and role-aware navigation placeholders.
- Add design tokens, layout primitives, empty/loading/error state patterns.
- Add smoke checks for build and responsive route rendering.

Acceptance Evidence:
- Homepage, login, student, counselor, and admin shells render on desktop and mobile.
- No page is a dead static fake; every shell has intended API/flow integration points documented.
- Simulated-data label placement is defined.
- Frontend build/lint smoke evidence is recorded.

Rollback:
- Revert frontend skeleton and related config additions on the phase branch.
- Backend remains untouched unless explicitly approved.

### Phase 2: Demo Login & Role Routing

Goal:
Implement local/Demo login and route protection for student, counselor, and admin roles.

Entry Conditions:
- Phase 1 shell accepted.
- Auth architecture and Demo account approval package accepted.

Key Approval Packages:
- Demo account model.
- Session/token approach.
- Route protection approach.
- Future SSO adapter boundary.
- Any auth library/component introduction.

Autoresearch Tasks:
- Compare FastAPI-compatible local auth/session approaches.
- Review safe Demo-account patterns without bringing real SSO into scope.

Task Nodes:
- Define Demo role/account data contract.
- Connect login page to backend auth endpoint.
- Implement client-side role routing.
- Implement backend/API role checks where required.
- Add unauthorized/expired-session states.

Acceptance Evidence:
- Student, counselor, and admin Demo accounts log in successfully.
- Each role lands in the correct workspace.
- Role mismatch is blocked or redirected.
- Tests cover login success, bad credentials, and role access denial.

Rollback:
- Revert auth/routing changes to the Phase 1 shell baseline.
- Preserve future SSO notes as documentation only.

### Phase 3: Student Flow

Goal:
Deliver the student Q&A flow with simulated but clearly labeled data and source/resource display.

Entry Conditions:
- Phase 2 login and role routing accepted.
- Student UI/API contract approval package accepted.

Key Approval Packages:
- Student page structure.
- Q&A API contract.
- Answer/source display behavior.
- Conversation history behavior.
- Mobile interaction pattern.

Autoresearch Tasks:
- Review mature chat/Q&A UX patterns.
- Review FastAPI/RAG-compatible answer-source contract patterns.

Task Nodes:
- Build student dashboard and Q&A input.
- Connect question submission to backend.
- Render answer, confidence/fallback state, source/resource cards, and conversation history.
- Add clear simulated-data labeling.
- Add tests for happy path, no-answer fallback, and mobile layout.

Acceptance Evidence:
- Student can log in, ask a question, receive an answer/resource, and view context/history.
- UI never implies simulated records are real student data.
- Tests or manual evidence capture desktop and mobile behavior.

Rollback:
- Revert student frontend and API-contract changes for this phase.
- Keep Phase 2 login intact.

### Phase 4: Admin Knowledge Flow

Goal:
Allow admin users to maintain Demo knowledge/resources and inspect basic activity/stats.

Entry Conditions:
- Phase 3 student flow accepted.
- Admin knowledge model and database/component choices approved.

Key Approval Packages:
- Knowledge model.
- Admin UI structure.
- CRUD/data validation approach.
- Database schema if persistence is introduced here.
- Any admin CRUD/open-source component introduction.

Autoresearch Tasks:
- Compare FastAPI admin CRUD patterns.
- Review knowledge ingestion/document metadata patterns with PostgreSQL, MinIO, and Milvus boundaries.

Task Nodes:
- Build admin knowledge/resource list.
- Build add/edit/delete or enable/disable operations approved for Demo.
- Connect admin stats/activity surfaces.
- Add synthetic seed-data management path.
- Add role-protected API/frontend tests.

Acceptance Evidence:
- Admin can view and modify Demo knowledge/resources through real app flows.
- Admin actions are reflected in student answer/resource behavior where in scope.
- Basic activity/stats are visible and clearly Demo-labeled.

Rollback:
- Revert admin UI/API changes and seed-data changes from the phase branch.
- If schema changes occurred, include migration downgrade or documented data reset.

### Phase 5: Counselor Flow

Goal:
Deliver counselor workbench with case list/detail, AI assistance output, and status/action handling.

Entry Conditions:
- Student and admin flows accepted enough to support a connected Demo story.
- Counselor workflow/data model approval package accepted.

Key Approval Packages:
- Counselor UI structure.
- Case/status model.
- Assistant output contract.
- Relationship between student activity and counselor case context.

Autoresearch Tasks:
- Review case-management workbench patterns.
- Review AI-assisted staff workflow patterns and safe assistant-output labeling.

Task Nodes:
- Build counselor dashboard/case list.
- Build case detail view with simulated student context.
- Connect AI-assisted summary/suggested response endpoint.
- Add case status/action updates.
- Add tests for role access, case state changes, and mobile layout.

Acceptance Evidence:
- Counselor can open a simulated case, view AI assistance, update status, and see context tied to the student Demo story.
- Assistant output is clearly advisory, not an automated decision.

Rollback:
- Revert counselor UI/API changes from this phase.
- Keep accepted student/admin surfaces intact.

### Phase 6: Persistence Hardening

Goal:
Move Demo-critical data from in-memory behavior to persistent PostgreSQL-backed storage with controlled migrations.

Entry Conditions:
- The role flows are accepted at the product level.
- Database schema and migration approval package accepted.

Key Approval Packages:
- Database schema.
- Migration tooling.
- Repository/service structure.
- Seed-data and reset strategy.
- Rollback/downgrade strategy.

Autoresearch Tasks:
- Compare FastAPI + SQLAlchemy/Alembic patterns.
- Review repository/service layering and migration workflows.

Task Nodes:
- Introduce approved migration tooling if not already present.
- Model users/roles, knowledge entries, conversations, counselor cases, audit events, and stats.
- Replace in-memory services incrementally.
- Add seed/reset commands for Demo data.
- Add restart-survival tests.

Acceptance Evidence:
- Core Demo records survive service restart.
- Backend tests cover persistence reads/writes for auth, Q&A, knowledge, counselor, and audit where applicable.
- Migration upgrade and rollback/downgrade evidence is recorded.

Rollback:
- Use migration downgrade if available.
- Otherwise reset local Demo database volumes with explicit data-loss warning for Demo data only.

### Phase 7: Knowledge/RAG Integration

Goal:
Connect knowledge-backed answers to MinIO/Milvus or an approved RAG component while preserving fallback behavior and source citation.

Entry Conditions:
- Persistence baseline accepted.
- RAG architecture, vector schema, embedding/model provider, and component choices approved.

Key Approval Packages:
- RAG framework/component selection.
- Embedding model/provider.
- Vector schema and metadata strategy.
- Source citation behavior.
- Fallback/no-answer policy.

Autoresearch Tasks:
- Compare mature RAG components compatible with FastAPI, MinIO, and Milvus.
- Review source citation and rebuild-index patterns.

Task Nodes:
- Define ingestion/indexing contract.
- Store original source documents or Demo resources through approved storage path.
- Index approved Demo knowledge into Milvus.
- Connect student Q&A to retrieval path.
- Add fallback when no reliable source is found.

Acceptance Evidence:
- Student answer can cite a source/resource from the Demo knowledge base.
- Index rebuild path is documented and smoke-tested.
- No-answer behavior is explicit and tested.

Rollback:
- Disable RAG path behind configuration or fallback to deterministic knowledge lookup.
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

Autoresearch Tasks:
- Optional: only if introducing new visual/accessibility testing tooling.

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

Autoresearch Tasks:
- Review Docker Compose production-ish hardening practices for FastAPI, PostgreSQL, Redis, MinIO, and Milvus.
- Review Alibaba Cloud ECS operational assumptions without turning Demo into full production launch.

Task Nodes:
- Update Docker/compose/env examples for full Demo stack.
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

- Phase 0: artifact update loop and acceptance criteria tightening.
- Phase 2: login/routing completion and verification loop.
- Phase 3: student flow end-to-end completion.
- Phase 6: persistence hardening, because it needs careful sequential migration and verification.
- Phase 7: RAG integration, because retrieval correctness and fallback behavior need persistent owner iteration.
- Phase 9: deployment smoke, because it needs one owner to chase failures to closure.

### Best Fit For `team`

- Phase 1: frontend skeleton/design system, after UI/stack approval; split into frontend shell, design tokens, route map, and tests/docs.
- Phase 4: admin knowledge flow, after schema/component approval; split into admin UI, backend API, seed data, tests.
- Phase 5: counselor flow, after workflow approval; split into counselor UI, backend case/assistant contract, tests, Demo script updates.
- Phase 8: responsive QA/product polish; split into visual QA, mobile fixes, copy/labels, regression checks.

### Use Solo Execution Instead

- Any single approval package draft.
- Any one PRD/test-spec edit.
- Any narrow bug fix discovered during verification.

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
Draft the PRD changes for independent site, required pages, role flows, mobile scope, simulated-data labeling, and SSO deferral.

Approved Scope:
- Requirements artifact only.
- No UI or backend implementation.

Decision Gates:
- Any product positioning change requires an approval package.

Files Likely Affected:
- `.omx/plans/prd-ai-counselor-demo-phase0.md`

Tests/Verification:
- PRD includes homepage, login, student, counselor, admin, desktop/mobile, simulated-data label, non-goals, and Demo script.

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
- Test spec covers route presence, login/routing, student Q&A, admin knowledge, counselor case, persistence, RAG fallback/source citation, responsive QA, Docker smoke.

Rollback Note:
- Revert the test-spec delta file.

### P0-N4: Approval Package Set

Goal:
Prepare approval packages for product scope, PRD structure, test scope, and Phase 1 frontend decision gates.

Approved Scope:
- Approval package drafting only.

Decision Gates:
- User approval required before Phase 1 implementation.

Files Likely Affected:
- `.omx/plans/approval-packages-ai-counselor-demo-phase0.md`

Tests/Verification:
- Each package uses: recommended option, alternatives, why recommended, impact scope, risks, acceptance method, questions.

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

## Global Risks

- Frontend stack is not yet approved; Phase 1 must not start implementation before approval.
- Existing business layer is in-memory; Demo credibility depends on Phase 6 persistence hardening.
- RAG can expand quickly; Phase 7 must keep source citation and fallback behavior as the acceptance boundary.
- Mobile scope can become broad; Phase 8 should prioritize required flows over decorative polish.
- ECS 4 vCPU / 16 GiB is a target assumption, not production capacity proof.

## Stop Rules

- Stop implementation when a task reveals a new key technical, UI, database, or component decision not covered by an approval package.
- Stop phase progression when acceptance evidence is missing.
- Stop public/deployment expansion when security, SSO, real school resource, or real student data boundaries are crossed.

