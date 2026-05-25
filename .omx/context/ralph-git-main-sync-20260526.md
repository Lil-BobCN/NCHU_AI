# Ralph Context: GitHub Main Sync

Date: 2026-05-26
Workspace: `C:\Users\liuqi\Desktop\agentproject`

## Task Statement

Ensure current project development assets are tracked by Git, upload them to GitHub, and move the active development state from `phase/02-demo-login-role-routing` to `main`.

## Desired Outcome

- Durable project files, especially planning/prototype assets under `.omx/`, are available on GitHub.
- Local `main` contains the current development branch work.
- `origin/main` is updated.
- Local working tree does not accidentally upload secrets, dependency directories, generated caches, or machine runtime state.

## Known Facts / Evidence

- Current branch: `phase/02-demo-login-role-routing`.
- Remote branch: `origin/phase/02-demo-login-role-routing`.
- `origin/main` is ahead of local `main`.
- `.git/info/exclude` locally ignores `.omx/` and `AGENTS.md`.
- `.gitignore` already ignores `.env`, `.env.*`, `backend/.env`, dependency/runtime directories, logs, and caches.

## Constraints

- Do not upload secrets such as `.env` or legacy env snapshots.
- Do not upload dependency installs such as `.venv` or `frontend/node_modules`.
- Do not upload caches/logs such as `.pytest_cache`, `.ruff_cache`, `.playwright-cli`, `logs`, and `output/logs`.
- Keep Git operations non-destructive; do not reset or discard unrelated changes.

## Likely Touchpoints

- `.gitignore`
- `.git/info/exclude`
- `.omx/plans`, `.omx/decisions`, `.omx/context`, `.omx/prototypes`, `.omx/specs`, `.omx/logs`, `.omx/references`, `.omx/reports`
- `main`
- `origin/main`
