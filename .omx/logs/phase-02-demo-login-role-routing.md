# Phase 2 Log: Demo Login & Role Routing

Date: 2026-05-19
Status: in progress
Branch: `phase/02-demo-login-role-routing`

## Scope

Phase 2 covers Demo login, session behavior, role routing, unauthorized states, and SSO deferral.

Approved boundaries:

- Use Demo/local accounts only.
- FastAPI remains the authority for session and role checks.
- Keep all data Demo-labeled.
- Do not introduce production SSO.
- Do not create database schema or migrations.
- Do not introduce RAG/vector/provider behavior.

## Entry Evidence

- `SDAR-0006-product-data-contract-boundary.md` approved on 2026-05-19.
- Product manager instruction: "好的，进入Phase 2".
- Data contract allows API-connected UI and backend work inside approved fields.

## Task Nodes

### P2-N1: Backend Auth/Session Contract Alignment

Status: done

Files changed:

- `backend/app/schemas/business.py`
- `backend/app/services/business.py`
- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/deps.py`
- `backend/app/api/v1/counselor.py`
- `backend/tests/test_business_phase1.py`

Implemented:

- `UserPublic` now exposes approved Demo contract fields: `displayName`, `role`, `demoAccount`, and `sessionState`.
- Local Demo login remains available for student, counselor, and admin.
- SSO callback routes now expose the adapter boundary but return explicit deferred behavior.
- Login failure records structured audit events.
- Role permission denial records structured audit events.
- Counselor assistance audit action uses approved structured action naming.
- Audit events use `eventTags` and `counterKey`, not free-text summaries.

Verification:

- `..\.venv\Scripts\python.exe -m pytest tests/test_business_phase1.py -q`
  - Result: 12 passed
- `..\.venv\Scripts\python.exe -m pytest -q`
  - Result: 17 passed
- `..\.venv\Scripts\python.exe -m ruff check .`
  - Result: all checks passed

Rollback:

- Revert the changed backend files listed above.
- Restore old `UserPublic`, SSO mock callback, and audit `details` behavior only if the product contract is explicitly rolled back.

### P2-N2: Frontend React Login/Role Routing Skeleton

Status: done

Files changed:

- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/vite.config.ts`
- `frontend/src/App.tsx`
- `frontend/src/App.css`
- `frontend/src/index.css`
- `frontend/src/main.tsx`

Implemented:

- Created React + TypeScript + Vite frontend project.
- Added Ant Design and React Router.
- Built approved product-homepage style entry route at `/`.
- Built `/login` role selection and Demo account login path.
- Added student, counselor, and admin workspace routes.
- Added guarded role routing with local Demo session state.
- Added Vite `/api` proxy to FastAPI at `http://127.0.0.1:8000`.

Verification:

- `npm run build`
  - Result: passed
  - Note: Vite reported a bundle-size warning because Ant Design is included in the initial bundle; this is acceptable for skeleton and can be optimized later with route/code splitting.
- `npm run lint`
  - Result: passed
- Frontend smoke:
  - `http://127.0.0.1:5173/` returned HTTP 200.
  - `http://127.0.0.1:5173/login` returned HTTP 200.
- Backend smoke:
  - `POST http://127.0.0.1:8000/api/v1/auth/login` returned a Demo `UserPublic` with `displayName`, `role`, `demoAccount`, and `sessionState`.
- Frontend proxy smoke:
  - `POST http://127.0.0.1:5173/api/v1/auth/login` returned a Demo admin session through Vite proxy.

Running local services:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

Backend was started with `--lifespan off` for current Demo development so Phase 2 can use the in-memory business API before Phase 6 PostgreSQL hardening.

Rollback:

- Revert the frontend directory additions and backend contract changes from P2-N1/P2-N2.

## Current Next Node

P2-N3: Product-manager browser review and Phase 2 interaction polish.

Expected scope:

- Product manager opens `http://127.0.0.1:5173`.
- Confirm homepage -> login -> role workspace flow.
- Log visual or interaction adjustments.
- Keep any changes inside Phase 2 login/routing scope.

## P2-N3 Interaction Polish Log

### 2026-05-19 Topbar And Identity Adjustment

Status: first polish pass done, pending product-manager browser review.

Files changed:

- `frontend/src/App.tsx`
- `frontend/src/App.css`

Implemented:

- Changed the brand title from `AI 辅导员 Demo` to `NCHU AI`.
- Removed direct role workspace entries from the top navigation.
- Kept the login flow responsible for role detection and automatic routing after account login.
- Updated visible role language to `学生`、`老师`、`运维管理人员`.
- Added logged-in identity display so the topbar shows the detected role identity.
- Adjusted the right-side topbar action area toward the Linear-style pattern: lightweight text action plus rounded primary action.

Verification:

- `npm run lint`
  - Result: passed
- `npm run build`
  - Result: passed
  - Note: Vite still reports a bundle-size warning from the current Ant Design initial bundle; this is not caused by this topbar polish and remains a later optimization item.
- Local frontend smoke:
  - `http://127.0.0.1:5173` returned HTTP 200.

Rollback:

- Revert the two frontend files listed above to restore the previous topbar and role wording.

### 2026-05-19 Login Layout Fix

Status: done, pending product-manager browser review.

Files changed:

- `frontend/src/App.css`

Problem:

- The login page right-side panel was visually broken after clicking login.
- Root cause: `.login-hero .ant-card-body` matched both the outer login hero card body and the nested login panel card body, causing the nested panel to inherit the outer two-column grid layout.

Implemented:

- Narrowed the selector to `.login-hero > .ant-card-body` so only the outer card uses the two-column grid.
- Added explicit width and layout rules for `.login-panel`.
- Added responsive rules so the login panel stretches correctly on smaller viewports.

Verification:

- `npm run lint`
  - Result: passed
- `npm run build`
  - Result: passed
  - Note: Existing Vite bundle-size warning remains a later optimization item.

Rollback:

- Revert `frontend/src/App.css` to restore the prior login page layout rules.

### 2026-05-20 Topbar And Homepage Hero Polish

Status: done, pending product-manager visual review.

Files changed:

- `frontend/src/App.tsx`
- `frontend/src/App.css`

Implemented:

- Reworked the homepage topbar into a darker product-site navigation style while preserving `NCHU AI` branding and public-only navigation.
- Rebuilt the first homepage viewport as a formal product hero: strong product proposition, clear Demo CTA, trust/status metrics, and a right-side AI console preview.
- Used the existing `frontend/src/assets/hero.png` as a subtle layered product visual in the hero preview.
- Kept login and role-routing behavior unchanged: login still determines student, teacher, or operations identity through the approved Demo account/session contract.
- Added mobile-specific hero typography and metric compaction so the first viewport remains usable.

Verification:

- `npm run lint`
  - Result: passed
- `npm run build`
  - Result: passed
  - Note: Existing Vite bundle-size warning remains a later optimization item.
- Browser visual evidence:
  - Desktop screenshot: `output/playwright/home-hero-1440-v2.png`
  - Mobile screenshot: `output/playwright/home-hero-mobile-390-v2.png`
- Route smoke:
  - `http://127.0.0.1:5173/` loaded and screenshot capture succeeded.
  - `http://127.0.0.1:5173/login` returned HTTP 200.

Known follow-up:

- Mobile hero is usable, but the first viewport still prioritizes the full hero message over showing the next section. This is acceptable for the current desktop-first direction and can be tightened in later responsive polish.

Rollback:

- Revert `frontend/src/App.tsx` and `frontend/src/App.css` to restore the previous lighter homepage hero.
