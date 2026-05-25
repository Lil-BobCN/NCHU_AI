# Ralph Context: GitHub Safe Auto Sync

## Task Statement

Continue the GitHub synchronization task until the project can keep local development work aligned with GitHub `main`.

## Desired Outcome

- Current workspace remains on `main`.
- Durable project assets are committed and pushed to GitHub.
- Future local development changes have a safe repeatable sync path.
- Secrets, dependencies, caches, runtime logs, and machine state stay local.

## Known Facts / Evidence

- `origin` points to `git@github.com:Lil-BobCN/NCHU_AI.git`.
- `main` was already pushed to GitHub at commit `7ec38d1`.
- Frontend build and backend tests passed after that push.
- `.omx` durable docs/prototypes should be trackable, while `.omx/state`, `.omx/tmp`, `.omx/*.log`, and `.omx/*.jsonl` should remain local.

## Constraints

- Do not push secrets or runtime-only files.
- Do not use destructive Git commands.
- Keep the local working state on `main`.
- Use Lore-format commit messages.

## Unknowns / Open Questions

- Whether the user wants a long-running local background sync process permanently, or just a scriptable safe sync entrypoint.

## Likely Touchpoints

- `scripts/git-safe-sync.ps1`
- `scripts/start-github-auto-sync.ps1`
- `scripts/stop-github-auto-sync.ps1`
- `.omx/logs/github-auto-sync-20260526.md`
