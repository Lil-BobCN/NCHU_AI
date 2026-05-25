# GitHub Auto Sync Workflow

## Purpose

Keep local project work aligned with GitHub `main` through a safe repeatable script path.

## Commands

- One-time sync:
  `powershell -ExecutionPolicy Bypass -File scripts/git-safe-sync.ps1`

- Start background sync loop:
  `powershell -ExecutionPolicy Bypass -File scripts/start-github-auto-sync.ps1 -IntervalSeconds 60`

- Stop background sync loop:
  `powershell -ExecutionPolicy Bypass -File scripts/stop-github-auto-sync.ps1`

## Safety Boundary

The sync script stages trackable files only, then blocks obvious local-only or sensitive paths:

- `.env` and `.env.*`
- dependency folders such as `node_modules`, `.venv`, and `venv`
- cache folders such as `.pytest_cache`, `.ruff_cache`, and `__pycache__`
- private key-like files and runtime `.log` / `.jsonl` files

The script also scans the staged snapshot for high-confidence secret patterns before committing.

## Operating Rule

Use this workflow for local-to-GitHub synchronization. If GitHub and local `main` diverge, the script stops instead of force-pushing.

## Auto-start Verification

The background sync loop was started locally on 2026-05-26. This note is used as a durable verification change for the first auto-sync pass.
