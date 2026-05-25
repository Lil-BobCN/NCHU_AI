# Development Plan: AI Counselor Demo Scope Realignment

Date: 2026-05-17

## Goal

Build a formal-product-like independent AI counselor Demo site that supports homepage, login, student side, counselor side, and admin side across desktop and mobile. Use clearly labeled simulated data while keeping the system flow real enough to prove product feasibility.

## Plan Format

Each module is written as:

- Function
- Development approach
- Why this approach
- Acceptance check

## 1. Independent Main Website

Function:
Create an independent main website that can be linked from the school official website.

Development approach:
Build a homepage with product identity, value summary, role-oriented entry points, login entry, and visible simulated-data/Demo labeling. The homepage should be the first screen of the product, not a temporary landing page.

Why this approach:
The product is no longer embedded in the school official website. The independent site must establish trust, explain the service, and route users to the correct role flow.

Acceptance check:
Desktop and mobile homepage are usable. A visitor can understand what the system is and enter login within one obvious action.

## 2. Login System

Function:
Support Demo login for student, counselor, and admin roles.

Development approach:
Use the current local/demo login direction. Provide controlled Demo accounts for three roles. Keep a future SSO entry/adapter boundary but do not require real SSO.

Why this approach:
Real SSO depends on school IT, protocol details, test accounts, callback configuration, and joint debugging. Demo should not be blocked by those external dependencies.

Acceptance check:
Demo accounts can log in. Each role lands on its own workspace. Unauthorized role switching is blocked or redirected.

## 3. Role-Based Navigation

Function:
Give each role a clear workspace and prevent users from seeing unrelated capabilities.

Development approach:
Implement a shared app shell with role-aware navigation. Student, counselor, and admin should have separate route groups and permission checks.

Why this approach:
The Demo must show three connected roles without confusing viewers. A shared shell reduces duplication while preserving role boundaries.

Acceptance check:
Student cannot access admin/counselor tools. Counselor and admin see their own workspaces. Mobile navigation remains usable.

## 4. Student Side

Function:
Let a student ask a question, receive guidance, view resources, and see conversation context.

Development approach:
Build a student dashboard centered on a Q&A input, answer panel, source/resource cards, and conversation history. Use simulated student profile and questions, clearly labeled.

Why this approach:
Student Q&A is the clearest value demonstration and should be the most polished user flow.

Acceptance check:
A student can complete this flow: log in -> ask question -> receive answer/resource -> see history or follow-up context.

## 5. Counselor Side

Function:
Let a counselor view simulated student consultation context and receive assistance.

Development approach:
Build a counselor workbench with case list, case detail, AI-assisted summary, suggested response/action, and status updates. Keep the flow lightweight and avoid complex approval systems.

Why this approach:
This proves the system supports counselor work rather than only student self-service.

Acceptance check:
Counselor can open a simulated case, view AI assistance, update status, and see context tied to student-side activity.

## 6. Admin Side

Function:
Let an admin maintain Demo knowledge/content and inspect basic system state.

Development approach:
Build admin screens for knowledge entries/resources, basic statistics, and audit/activity traces. Prioritize operations that support the Demo story.

Why this approach:
Admin capability proves the system can be operated and updated, not just used as a fixed chatbot.

Acceptance check:
Admin can view/add/edit knowledge/resource entries or Demo content. Basic stats/activity reflect the Demo flow.

## 7. Synthetic Demo Data

Function:
Provide realistic but non-private data for student profiles, questions, knowledge resources, counselor cases, and stats.

Development approach:
Create a seed dataset with fictional students, fictional cases, and school-affairs-style knowledge entries. Label all synthetic data in the UI and documentation.

Why this approach:
It allows a credible Demo without using real student private data or triggering privacy/compliance blockers.

Acceptance check:
No UI implies real student data. Demo records are coherent across student, counselor, and admin views.

## 8. Knowledge And Q&A Flow

Function:
Make student answers traceable to knowledge/resources.

Development approach:
Use the existing FastAPI direction and connect Q&A to knowledge records. If full RAG is not ready in the first increment, start with deterministic knowledge lookup but keep the API boundary compatible with Milvus/RAG.

Why this approach:
The Demo needs credible source-backed answers, but implementation should avoid overbuilding before persistence and ingestion are stable.

Acceptance check:
Answers include source/resource information or a clear fallback when no reliable answer exists.

## 9. Persistence

Function:
Move Demo-critical data from in-memory behavior toward persistent storage.

Development approach:
Prioritize PostgreSQL-backed persistence for users/roles, knowledge entries, conversations, counselor cases, audit events, and basic stats. Keep schema focused on Demo needs.

Why this approach:
The current business layer is in-memory. A formal Demo should survive service restarts and support connected cross-role flows.

Acceptance check:
Core Demo records survive restart. Student/counselor/admin flows read and write persistent data.

## 10. Mobile Development

Function:
Support mobile and desktop together.

Development approach:
Design responsive layouts from the start. Student side should be mobile-first. Counselor/admin can use compact cards, detail pages, filters, and stacked layouts instead of dense desktop tables on small screens.

Why this approach:
Students are likely to use phones, and a mobile-capable Demo feels more realistic.

Acceptance check:
Homepage, login, student side, counselor side, and admin side are usable on mobile and desktop.

## 11. Visual/Product Quality

Function:
Make the Demo look like a formal product.

Development approach:
Use a consistent design system: restrained colors, clear hierarchy, role-specific workspaces, icons, empty states, loading states, and error states. Avoid temporary placeholder screens.

Why this approach:
A Demo can fail by looking unfinished even when the backend works. Product trust matters here.

Acceptance check:
No major screen looks like a debug page. Text fits on mobile and desktop. UI states are handled.

## 12. Basic Security And Audit

Function:
Provide minimum role isolation and traceability.

Development approach:
Implement role checks, protect privileged routes, avoid exposing internal service ports publicly, record key Demo actions where practical.

Why this approach:
Production-grade security is out of scope, but the Demo should not teach the wrong architecture.

Acceptance check:
Student cannot use admin APIs. Key actions have at least basic activity/audit records.

## 13. Deployment Readiness

Function:
Prepare the app for later Alibaba Cloud ECS deployment.

Development approach:
Keep Docker Compose as the deployment baseline. Add `.dockerignore`, server-safe `.env` examples, and deployment notes. Target the accepted 4 vCPU / 16 GiB configuration.

Why this approach:
The server discussion is deferred, but code should not block future deployment.

Acceptance check:
Local Docker Compose continues to work. Deployment-sensitive secrets and caches are not baked into images.

## 14. Demo Script

Function:
Provide a repeatable demonstration path.

Development approach:
Write a scripted flow: homepage -> login as student -> ask question -> view answer/source -> switch to counselor -> review case/assist -> switch to admin -> update knowledge/view stats.

Why this approach:
The Demo should be reproducible under time pressure and understandable to teachers/evaluators.

Acceptance check:
The script can be followed from start to finish without manual database edits.

## Delivery Phases

### Phase 0: Requirements And Test Update

- Update PRD and test spec to reflect independent main website, mobile in scope, synthetic data, SSO deferred.
- Define Demo acceptance path.
- Define non-goals and decision boundaries.

Exit condition:
Updated requirement/test artifacts are clear enough for implementation.

### Phase 1: Frontend Skeleton And Design System

- Create or update frontend app structure.
- Build homepage, login page, and role shell.
- Establish responsive layout tokens and navigation.

Exit condition:
Desktop/mobile skeleton exists for all required surfaces.

### Phase 2: Demo Login And Role Routing

- Implement Demo accounts.
- Connect login to role-specific routes.
- Add basic access control.

Exit condition:
Student/counselor/admin can log in and see correct workspace.

### Phase 3: Student Flow

- Build Q&A UI.
- Connect to backend endpoints.
- Show source/resource cards and history.

Exit condition:
Student Demo flow works end to end.

### Phase 4: Admin Knowledge Flow

- Build admin knowledge/resource screens.
- Add synthetic data seed/management path.
- Show basic stats/activity where available.

Exit condition:
Admin can support or modify the Demo knowledge content.

### Phase 5: Counselor Flow

- Build case list/detail.
- Show AI/counselor assistance output.
- Add status/action handling.

Exit condition:
Counselor flow is connected to the student Demo story.

### Phase 6: Persistence Hardening

- Move Demo-critical in-memory data to PostgreSQL.
- Keep audit/activity records.
- Ensure restart survival.

Exit condition:
Core Demo data survives service restart.

### Phase 7: Knowledge/RAG Integration

- Integrate MinIO/Milvus where needed.
- Preserve fallback behavior when no source is found.
- Keep source-backed answer contract.

Exit condition:
Knowledge-backed answers are demonstrable and traceable.

### Phase 8: Responsive QA And Product Polish

- Test desktop and mobile viewports.
- Fix layout overflow, unclear states, and role navigation issues.
- Add loading/error/empty states.

Exit condition:
All required surfaces are usable and look product-like.

### Phase 9: Docker/Deployment Smoke

- Add `.dockerignore` and deployment-safe env examples.
- Run backend tests, frontend build, and Docker Compose smoke.
- Preserve Alibaba Cloud ECS 4 vCPU / 16 GiB as target deployment assumption.

Exit condition:
Local verification passes and server deployment path is not blocked by obvious packaging mistakes.

## Verification Plan

- Backend unit/API tests for role login, permissions, Q&A, knowledge, counselor, admin, persistence.
- Frontend build and lint if frontend tooling exists.
- Responsive checks for homepage, login, student, counselor, admin.
- Docker Compose health/readiness/smoke checks.
- Demo script dry run.

## Stop Conditions

The Demo scope is complete when:

- Formal-product-like homepage, login, student, counselor, and admin surfaces exist.
- Desktop and mobile are both usable.
- Demo accounts work.
- Synthetic data is clearly labeled.
- Student/counselor/admin flow can be demonstrated end to end.
- Core records persist where required.
- Verification checks pass or any remaining gaps are explicitly documented.

