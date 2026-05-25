# Git Main Sync Log

Date: 2026-05-26

## Goal

Move the current development state from `phase/02-demo-login-role-routing` into `main` and make durable project assets visible on GitHub.

## Tracking Boundary

Included:
- `.omx/context`, `.omx/decisions`, `.omx/interviews`, `.omx/logs/*.md`
- `.omx/plans`, `.omx/prototypes`, `.omx/references`, `.omx/reports`, `.omx/specs`
- `.omx/project-memory.json`

Excluded:
- `.env`, `.env.*`, `backend/.env`, `backend/.env.*`
- dependency installs such as `.venv` and `frontend/node_modules`
- caches and generated runtime files
- `.omx/state`, `.omx/tmp`, `.omx/team`, `.omx/logs/*.jsonl`, `.omx/logs/*.log`

## Verification

- staged file count: 147 before this log file was added
- no staged `.env`, `node_modules`, virtualenv, cache, jsonl, or log runtime files detected
- high-confidence secret pattern scan found no staged matches
- frontend build passed with Vite chunk-size warning only
- backend tests passed: 20 passed
