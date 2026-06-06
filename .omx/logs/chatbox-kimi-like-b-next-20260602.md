# Acceptance Log: Chatbox Kimi-like B-next Boundary Review

Date: 2026-06-02
Team: implement-approved-b-next-chat
Worker: worker-4 (quality/security reviewer)
Status: boundary review completed for worker-4 snapshot; integration of worker-1/2/3 code lanes was still pending when this log was written.

## Scope Reviewed

B-next credible hardening must remain inside SDAR-0008 and SDAR-0010:

- Keep FastAPI as the model/key/security boundary.
- Keep assistant-ui as Thread / Composer / runtime owner.
- Keep Ant Design X limited to local advanced assistant-message renderers.
- Do not add or modify `StudentChatRequest` fields.
- Do not change sandbox trigger/default behavior.
- Do not introduce persistence, new provider/API family, real school resources, real student data, RAG/vector/embedding, Agent/task queue, production SSO, deployment/security boundary changes, or frontend model secrets.

## Key Files Read

Required shared context:

1. `docs/development-process.md`
2. `README.md`
3. `PROJECT_STATE.md`
4. `.omx/context/chatbox-kimi-like-b-plan-20260602T055134Z.md` (leader root)
5. `.omx/specs/autoresearch-kimi-chatbox-comparative-audit-20260602/report.md` (leader root)
6. `.omx/plans/prd-chatbox-kimi-like-b-next-20260602.md` (leader root)
7. `.omx/plans/test-spec-chatbox-kimi-like-b-next-20260602.md` (leader root)
8. `.omx/plans/ralplan-chatbox-kimi-like-b-next-20260602.md` (leader root)
9. `.omx/logs/chatbox-kimi-like-b-lite-implementation-20260601.md` (leader root)
10. `.omx/decisions/SDAR-0008-real-model-student-chatbox.md`
11. `.omx/decisions/SDAR-0010-assistant-ui-chatbox-component-boundaries.md` (leader root)

Additional boundary files:

- `backend/app/config.py`
- `backend/app/services/sandbox.py`
- `backend/app/schemas/business.py`
- `backend/app/api/v1/student.py`
- `backend/app/services/chat_model.py`
- `frontend/src/StudentChatboxPage.tsx`
- `frontend/src/components/assistant-ui/thread.tsx`
- `frontend/src/lib/chat-run.ts`

## Boundary Findings

PASS - Request contract preserved in this worker snapshot.

- `StudentChatRequest` fields remain: `message`, `conversation_id`, `web_search`, `reasoning_enabled`, `profile`, `mode`, `attachments`.
- The frontend request body still uses the approved semantic fields: `conversationId`, `message`, `webSearch`, `reasoning`, `profile`, `mode`, `attachments`.
- No `toolMode`, `sandboxConfirmation`, provider selector, persistence flag, real-resource selector, or Agent/task field was found.

PASS - Sandbox governance boundary preserved.

- Defaults remain:
  - `chat_sandbox_enabled=True`
  - `chat_sandbox_timeout_seconds=8.0`
  - `chat_sandbox_max_attachment_bytes=65536`
  - `chat_sandbox_max_files=6`
  - `chat_sandbox_dependency_install_enabled=False`
- Trigger behavior remains attachment-driven plus existing keyword matching: `运行`, `测试`, `pytest`, `npm test`, `node`, `python`.
- No implementation change was made to sandbox confirmation, dependency installation, resource limits, request fields, or trigger policy.

PASS - Provider/key boundary preserved.

- Model API key handling remains backend-only in `backend/app/config.py` and `backend/app/services/chat_model.py`.
- Frontend TypeScript/TSX search found no `DASHSCOPE_API_KEY`, `QWEN_API_KEY`, `CHAT_MODEL_API_KEY`, `sk-`, or `apiKey` secret material.
- The frontend still calls FastAPI `/api/v1/student/chat/stream` rather than a browser-direct provider endpoint.

PASS - Component boundary preserved.

- `frontend/src/components/assistant-ui/thread.tsx` still uses `ThreadPrimitive.Root` and `ComposerPrimitive.Root`.
- Ant Design X usage is limited to local renderers/actions (`ThoughtChain`, `Think`, `Sources`, `Actions`).
- No Ant Design X `Bubble`, `Sender`, or `Conversations` replacement of the assistant-ui main chat surfaces was found.

PASS - UI capability claims remain bounded in reviewed code.

- Frontend TypeScript/TSX search found no claims for school database access, internal school systems, RAG knowledge-base access, or real student records.
- Source/citation/tool UI is driven by `chat.run.v1` reducer state (`source`, `citation`, `tool_*`, `workflow_*`, `notice`, `usage`), not by hard-coded fake source/tool content in the reviewed frontend files.
- `backend/app/config.py` system prompt explicitly tells the model not to claim real school database, RAG knowledge base, or real student archive access.

## Files Changed By Worker 4

- `.omx/logs/chatbox-kimi-like-b-next-20260602.md` - added this boundary review / acceptance log.

No product code files were changed by worker-4.

## Verification Evidence

Static guard checks run from worker-4 worktree:

```text
StudentChatRequest fields: ['message', 'conversation_id', 'web_search', 'reasoning_enabled', 'profile', 'mode', 'attachments']
StudentChatRequest field-set guard: PASS
chat_sandbox_enabled ... default=True PASS
chat_sandbox_timeout_seconds ... default=8.0 PASS
chat_sandbox_max_attachment_bytes ... default=65536 PASS
chat_sandbox_max_files ... default=6 PASS
chat_sandbox_dependency_install_enabled ... default=False PASS
Sandbox keywords: ['运行', '测试', 'pytest', 'npm test', 'node', 'python']
Sandbox keyword trigger guard: PASS
Sandbox attachment trigger guard: PASS
Frontend secret exposure guard: PASS []
Frontend unapproved-claim guard: PASS []
Assistant UI ThreadPrimitive present: PASS
Assistant UI ComposerPrimitive present: PASS
Ant Design X local renderers only: PASS
```

Diff guard:

```text
git diff -- backend/app/schemas/business.py backend/app/services/sandbox.py backend/app/config.py frontend/src/StudentChatboxPage.tsx frontend/src/components/assistant-ui/thread.tsx frontend/src/lib/chat-run.ts
# no output; worker-4 did not change these boundary-critical files
```

Search evidence:

- `rg DASHSCOPE_API_KEY|QWEN_API_KEY|CHAT_MODEL_API_KEY|sk-|apiKey frontend/src -S` - no frontend secret-key hits in TS/TSX guard script.
- `rg 真实学校数据库|学校内部系统|RAG 知识库|真实学生档案|school database|real student record frontend/src -S` - no unapproved frontend capability claims in TS/TSX guard script.
- Backend hits for provider env names are expected and remain in backend-only config/provider code.

Project verification attempts from worker-4:

- `frontend> npm ci` -> PASS; installed 660 packages, 0 vulnerabilities. npm emitted EBADENGINE warnings because current Node is `v23.11.1` while several ESLint packages declare `^20.19.0 || ^22.13.0 || >=24`.
- `frontend> npm run lint` -> PASS; `eslint .` completed with exit code 0.
- `frontend> npm run build` -> PASS; `tsc -b && vite build` completed with exit code 0. Vite emitted the known large-chunk warning.
- `backend> python -m pip install -r requirements.txt` -> BLOCKED; timed out twice (304s and 604s) before installing required modules.
- `backend> python -m ruff check .` -> BLOCKED by environment; `No module named ruff`.
- `backend> python -m pytest` -> BLOCKED by environment; `No module named pytest`.
- `git diff --check -- .omx/logs/chatbox-kimi-like-b-next-20260602.md` -> PASS.
- Log structure check -> PASS for `## Boundary Findings`, `## Verification Evidence`, `## Not-tested`, and `## Rollback`.

## Not-tested

- Worker-4 did not run a live Qwen/DashScope provider smoke; this remains credential/provider-availability gated.
- Worker-4 did not run browser screenshots; worker-2/worker-3 own UI/prototype/browser smoke evidence.
- Worker-4 review snapshot was taken while worker-1, worker-2, and worker-3 tasks were still `in_progress`; final integrated branch should re-run this boundary guard after their commits are merged.

## Rollback

- Revert `.omx/logs/chatbox-kimi-like-b-next-20260602.md` to remove this review log if the team chooses to replace it with an integrated final acceptance log.
- If a later integrated diff crosses a stop line, revert the offending worker commit and open a new SDAR before reattempting request-field, sandbox-policy, provider, persistence, real-resource/RAG/vector, or Agent/task-queue work.

## Integrated Leader Closure Addendum

Date: 2026-06-02 16:40 Asia/Shanghai
Leader status: integrated closure completed after worker-4 snapshot.

### Integrated Scope

- Backend credible hardening is present in `backend/app/api/v1/student.py` and `backend/app/services/chat_model.py`:
  public-source normalization, duplicate source counting, source/citation payload preservation, and denser `workflow_*` stream events.
- Frontend credible UI is present in `frontend/src/lib/chat-run.ts`, `frontend/src/components/assistant-ui/thread.tsx`, and `frontend/src/App.css`:
  source/citation reducer state, deduped sources, Ant Design X local `Sources`/`Think`/`ThoughtChain`/`Actions` renderers, and no replacement of assistant-ui `Thread`/`Composer`/runtime.
- Prototype-first record is present in `.omx/prototypes/student-chatbox-kimi-like-chat-page-20260601.html` as the B-next credible-hardening addendum.
- Test evidence is present in `.omx/logs/chatbox-kimi-like-b-next-worker-3-test-evidence-20260602.md`.

### Integrated Verification

- `.\.venv\Scripts\python.exe -m pytest backend\tests\test_business_phase1.py` -> PASS, 49 tests.
- `.\.venv\Scripts\python.exe -m ruff check backend\app backend\tests` -> PASS.
- `node --test frontend\tests\chat-run-reducer.test.mjs` -> PASS, 2 tests.
- `cd frontend; npm run lint` -> PASS.
- `cd frontend; npm run build` -> PASS; Vite reported the known large-chunk warning only.
- `git diff --check` -> PASS.

### Browser Smoke

- Static preview attempts:
  - `http://127.0.0.1:4177/` returned HTTP 200 via PowerShell before Playwright opened.
  - `http://127.0.0.1:4178/` and `http://127.0.0.1:4179/` returned HTTP 200 via PowerShell immediately after Vite preview startup.
- Playwright CLI still captured Chromium `ERR_CONNECTION_REFUSED` pages:
  - `.playwright-cli/page-2026-06-02T08-27-01-800Z.png`
  - `.playwright-cli/page-2026-06-02T08-33-46-079Z.png`
  - `.playwright-cli/page-2026-06-02T08-34-59-344Z.png`
- Conclusion: integrated browser smoke is not counted as passed. The validated evidence for this closure is backend/frontend tests, lint/build, reducer tests, static boundary review, and existing earlier UI smoke artifacts.

### Final Boundary Statement

No new SDAR stop line was crossed in the integrated branch:

- no `StudentChatRequest` field addition/removal;
- no sandbox trigger/default behavior change;
- no persistence/provider/API-key handling change;
- no real school resources, real student data, RAG/vector/embedding, Agent/task queue, production SSO, deployment, or broad security-boundary change;
- frontend source/citation/tool UI remains driven by backend `chat.run.v1` events and local reducer state.

## Ralph Closure Addendum

Date: 2026-06-02 19:20 Asia/Shanghai
Leader status: remaining B-next P0 closure completed after local smoke recovery.

### Additional Scope Closed

- Login recovery now preserves the pending Chatbox prompt across a stream-time 401 and returns the user to `/app/student/chatbox` for one-click retry.
- Source governance now carries `sourceId`, `displayTitle`, and `dedupeKey` through backend events and the frontend reducer.
- Source display now shows Top 3 public sources by default, folds additional sources, and renders citation chips as clickable links only when they match returned source metadata.
- Composer control text was tightened to Chinese Kimi-like labels without replacing assistant-ui Thread/Composer/runtime ownership.
- Obsolete route-based Playwright smoke attempts were removed after proving that static CLI route bodies truncate multiline SSE.

### Additional Verification

- `backend> ..\.venv\Scripts\python.exe -m pytest` -> PASS, 56 tests.
- `backend> ..\.venv\Scripts\python.exe -m ruff check app tests` -> PASS.
- `frontend> node --test tests\chat-run-reducer.test.mjs` -> PASS, 2 tests.
- `frontend> npm run lint` -> PASS.
- `frontend> npm run build` -> PASS; Vite large-chunk warning only.
- Browser smoke with local HTTP/SSE mock:
  - `bash /mnt/c/Users/liuqi/Desktop/agentproject/output/playwright/run-chatbox-b-next-smoke-local-api-20260602.sh` -> PASS.
  - Final URL: `http://127.0.0.1:5300/app/student/chatbox`.
  - `hasPublicSources=1`, `hasFoldNote=1`, `hasCitationSource=1`.
  - The only browser console error is the expected first `401 Unauthorized` from the recovery test leg.
- Screenshot evidence:
  - `output/playwright/chatbox-b-next-401-recovery-sources-desktop-20260602.png`
  - `output/playwright/chatbox-b-next-401-recovery-sources-mobile-20260602.png`

### Additional Not-tested

- Live provider smoke against real DashScope/Moonshot credentials was not run.
- Direct local FastAPI server smoke remains environment-gated because the default backend startup path expects local PostgreSQL availability on this machine.
- The known Vite large-chunk warning is not addressed in this B-next P0 closure.

### Additional Rollback

- Revert the Ralph-owned frontend files: `frontend/src/App.tsx`, `frontend/src/StudentChatboxPage.tsx`, `frontend/src/lib/chat-run.ts`, `frontend/src/components/assistant-ui/thread.tsx`, `frontend/src/App.css`.
- Revert the Ralph-owned backend files: `backend/app/api/v1/student.py`, `backend/app/services/chat_model.py`.
- Revert the added/updated tests: `backend/tests/test_business_phase1.py`, `frontend/tests/chat-run-reducer.test.mjs`.
- Remove local smoke artifacts under `output/playwright/chatbox-b-next-*` if the closure evidence needs to be regenerated.
