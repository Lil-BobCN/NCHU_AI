# Phase 3R Log: Real Model Student Chatbox

Date: 2026-05-25
Status: ready for product review
Branch: `phase/02-demo-login-role-routing`

## Scope

Phase 3R revises the original deterministic-only Phase 3 student flow. The new product-manager direction is to use real model API replies for the student Chatbox while keeping FastAPI as the backend authority and API-key boundary.

Proposed boundaries:

- Build the student Chatbox as an isolated page first.
- Use backend-proxied real model streaming responses.
- Reuse the Qwen model API already configured in project files; do not add a second provider configuration family.
- Keep chat history in the current in-memory Demo runtime for this phase.
- Do not expose model API keys in the frontend.
- Do not introduce database persistence, RAG/vector/provider retrieval, document ingestion, production SSO, or real student data in this node.

## Task Nodes

### P3R-N1: Boundary Revision Approval Package

Status: done

Artifact:

- `.omx/decisions/SDAR-0008-real-model-student-chatbox.md`

Evidence:

- Product manager completed in-file review on 2026-05-25.
- Approved scheme: student-first isolated Chatbox, FastAPI-proxied real model API, runtime-only chat history, counselor/teacher Chatbox deferred until student Chat engine verification.
- Constraint: use the existing project-configured Qwen model API; do not add a new model API family.

### P3R-N2: Backend Real-Model Stream Proxy

Status: done

Scope:

- Located existing Qwen/DashScope configuration names in legacy project env files:
  - `.env.legacy-20260513T145513`: `QWEN_API_KEY`, `QWEN_MODEL`
  - `backend/.env.legacy-20260513T145513`: `DASHSCOPE_API_KEY`, `DASHSCOPE_API_BASE_URL`, `DASHSCOPE_MODEL`, `ENABLE_THINKING`
- Added backend Qwen/DashScope runtime settings using the existing configuration family and legacy aliases.
- Added student real-model SSE route: `POST /api/v1/student/chat/stream`.
- Added in-memory runtime conversation writes for streamed student and assistant turns.
- Added clear `503` failure when model provider configuration is missing.

Evidence:

- `python -m ruff check .` from `backend/`: passed.
- `python -m pytest` from `backend/`: 20 passed.

### P3R-N3: Isolated Student Chatbox Page

Status: done

Scope:

- Build a standalone student Chatbox route/page before merging into `/app/student`.
- Support streaming output, stop generation, retry/error state, new chat, and current in-memory chat history.
- Keep `/app/student` as the existing role workspace and add only an entry button to the isolated page.
- Add isolated route: `/app/student/chatbox`.

Evidence:

- `npm run lint` from `frontend/`: passed.
- `npm run build` from `frontend/`: passed with the pre-existing Vite chunk size warning.

### P3R-N4: Verification

Status: done

Scope:

- Backend targeted tests.
- Frontend lint/build.
- Browser smoke when local services are available.

Evidence:

- Backend: `python -m ruff check .` passed.
- Backend: `python -m pytest` passed, 20 tests.
- Frontend: `npm run lint` passed.
- Frontend: `npm run build` passed with the existing chunk size warning.
- Browser smoke:
  - Frontend verification server: `http://127.0.0.1:5180`.
  - Backend verification server: `http://127.0.0.1:8001` with `--lifespan off` because local PostgreSQL was not running.
  - Student Demo login reached `/app/student`.
  - `/app/student` entry opened `/app/student/chatbox`.
  - Real Qwen/DashScope streamed model reply appeared in the Chatbox.
  - Stop generation moved status to `已停止`.
  - New chat now keeps an empty new conversation state while preserving the runtime history rail.
  - Playwright console check: 0 errors / 0 warnings.
  - Screenshot: `output/playwright/p3r-student-chatbox-smoke.png`.

Known verification note:

- Normal backend lifespan startup requires PostgreSQL. The local browser smoke used `uvicorn --lifespan off` to validate the in-memory Phase 3R Chatbox path without database startup.
