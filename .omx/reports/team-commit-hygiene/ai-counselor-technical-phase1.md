# Team Commit Hygiene Finalization Guide

- team: ai-counselor-technical-phase1
- generated_at: 2026-05-12T14:09:57.904Z
- lore_commit_protocol_required: true
- runtime_commits_are_scaffolding: true

## Suggested Leader Finalization Prompt

```text
Team "ai-counselor-technical-phase1" is ready for commit finalization. Treat runtime-originated commits (auto-checkpoints, merge/cherry-picks, cross-rebases, worker clean rebase scaffolds, leader integration signals, shutdown checkpoints) as temporary scaffolding rather than final history. Do not reuse operational commit subjects verbatim. Use the completed task descriptions and resulting diffs to infer semantic commit boundaries. Rewrite or squash the operational history into clean Lore-format final commit(s) with intent-first subjects and relevant trailers. Use task subjects/results and shutdown diff reports to choose semantic commit boundaries and rationale.
```

## Commit Hygiene Vocabulary

### Operational commit kinds

- `auto_checkpoint` (auto-checkpoint) — A worker-local checkpoint commit created by the team runtime to preserve dirty worktree changes.
- `integration_merge` (integration merge) — A leader-side runtime merge commit that integrates a worker branch or checkpoint into the team branch.
- `integration_cherry_pick` (integration cherry-pick) — A leader-side runtime cherry-pick used when the normal worker merge path cannot be used cleanly.
- `cross_rebase` (cross-rebase) — A runtime rebase operation that moves worker work across the current leader branch baseline.
- `worker_clean_rebase` (worker clean rebase) — A runtime rebase that refreshes a clean worker branch onto the current leader branch baseline.
- `leader_integration_attempt` (leader integration attempt) — A leader-side integration attempt recorded for auditability even when it does not create a final semantic commit.
- `shutdown_checkpoint` (shutdown checkpoint) — A shutdown-time checkpoint commit that preserves remaining worker worktree changes before cleanup.
- `shutdown_merge` (shutdown merge) — A shutdown-time runtime merge that preserves worker changes on the leader branch before teardown.

### Operational commit statuses

- `applied` (applied) — The runtime operation changed repository history or preserved worker changes as intended.
- `noop` (no-op) — The runtime operation was unnecessary because there was no relevant change to preserve or integrate.
- `conflict` (conflict) — The runtime operation encountered conflicts that require human or leader-side reconciliation.
- `skipped` (skipped) — The runtime intentionally skipped the operation because prerequisites or safety checks were not met.

## Task Summary

- task-1 | status=pending | owner=worker-1 | subject=AI counselor technical phase1 support. Worker 1: inspect backend Docker/env/conf
  - description: AI counselor technical phase1 support. Worker 1: inspect backend Docker/env/config/readiness/smoke requirements and report implementation risks. Worker 2: inspect README/docs/test expectations and report documentation/test risks. Do not edit files or commit
- task-2 | status=pending | owner=worker-1 | subject=read-only support only. Leader is implementing in main workspace.
  - description: read-only support only. Leader is implementing in main workspace.

## Runtime Operational Ledger

- [2026-05-12T14:09:57.897Z] shutdown_merge | worker=worker-1 | status=noop | task=1 | source_commit=96748b73841d345ebaf65f083a8ea07a6bd7fabf | leader_before=96748b73841d345ebaf65f083a8ea07a6bd7fabf | leader_after=96748b73841d345ebaf65f083a8ea07a6bd7fabf | report_path=C:\Users\liuqi\Desktop\agentproject\.omx\team\ai-counselor-technical-phase1\worktrees\worker-1\.omx\diff.md | detail=source already reachable from leader HEAD
- [2026-05-12T14:09:57.897Z] shutdown_merge | worker=worker-2 | status=noop | source_commit=96748b73841d345ebaf65f083a8ea07a6bd7fabf | leader_before=96748b73841d345ebaf65f083a8ea07a6bd7fabf | leader_after=96748b73841d345ebaf65f083a8ea07a6bd7fabf | report_path=C:\Users\liuqi\Desktop\agentproject\.omx\team\ai-counselor-technical-phase1\worktrees\worker-2\.omx\diff.md | detail=source already reachable from leader HEAD

## Finalization Guidance

1. Treat `omx(team): ...` runtime commits as temporary scaffolding, not as the final PR history.
2. Reconcile checkpoint, merge/cherry-pick, cross-rebase, and shutdown checkpoint activity into semantic Lore-format final commit(s).
3. Use task outcomes, code diffs, and shutdown diff reports to name and scope the final commits.

## Recommended Next Steps

1. Inspect the current branch diff/log and identify which runtime-originated commits should be squashed or rewritten.
2. Derive semantic commit boundaries from completed task subjects, code diffs, and shutdown reports rather than from omx(team) operational commit subjects.
3. Create final commit messages in Lore format with intent-first subjects and only the trailers that add decision context.
