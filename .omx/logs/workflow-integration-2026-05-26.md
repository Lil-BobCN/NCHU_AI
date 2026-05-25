# Acceptance Log: Development Workflow Integration

日期：2026-05-26
状态：已完成

## 已变更

- Added `docs/development-process.md` as the tracked project workflow baseline.
- Added `AGENTS.md` as the mandatory AI agent entry point.
- Updated `README.md` to make the workflow contract visible from the project
  entry page.
- Updated `PROJECT_STATE.md` to record the current workflow baseline.
- Updated `.omx/notepad.md` so the workflow requirement is available in project
  working memory.

## 未变更

- No runtime code, API behavior, dependencies, or deployment configuration were
  changed.

## 验证证据

- Confirmed the source document was copied into `docs/development-process.md`.
- Confirmed repository entry documents now reference the workflow baseline.

## 已知风险

- Future tools or agents that ignore repository instructions may still need the
  workflow requirement restated manually.

## 回滚方式

- Remove `docs/development-process.md`, `AGENTS.md`, this log, and the workflow
  sections added to `README.md`, `PROJECT_STATE.md`, and `.omx/notepad.md`.

## 下一步

- For every future task, start by reading `docs/development-process.md` and the
  relevant `.omx` context before planning or implementing changes.
