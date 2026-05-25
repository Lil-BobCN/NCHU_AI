# Test Spec Delta: AI Counselor Demo Phase 0

Date: 2026-05-17
Status: draft for product-manager approval
Corresponding PRD: `.omx/plans/prd-ai-counselor-demo-phase0.md`

## Test Goal

Verify that Phase 0 produces a clear, reviewable planning and acceptance baseline for the independent AI Counselor Demo. This test spec does not define executable product tests yet; it defines the evidence required before implementation phases begin.

## Scope

Phase 0 verifies artifacts and decision boundaries only:

- Overall development plan exists.
- Phase 0 PRD delta exists.
- Phase 0 test-spec delta exists.
- Old PRD/Test Spec alignment matrix exists and covers all four old files.
- First approval package exists and is reviewable.
- P0-N1 evidence inventory cites current repo evidence.
- Obsolete assumptions are explicitly removed or narrowed.
- No runtime implementation is performed.

## Required Artifact Checks

| Check ID | Check | Passing evidence |
| --- | --- | --- |
| P0-TC-001 | Overall plan exists | `.omx/plans/overall-development-plan-ai-counselor-demo.md` exists and names RALPLAN consensus as primary source |
| P0-TC-002 | PRD delta exists | `.omx/plans/prd-ai-counselor-demo-phase0.md` exists |
| P0-TC-003 | Test spec exists | `.omx/plans/test-spec-ai-counselor-demo-phase0.md` exists |
| P0-TC-004 | Approval package exists | `.omx/plans/approval-packages-ai-counselor-demo-phase0.md` exists |
| P0-TC-005 | Phase log exists | `.omx/logs/phase-00-requirements-test-update.md` exists |
| P0-TC-006 | Evidence inventory cites repo state | PRD or log cites FastAPI backend, Docker/infrastructure baseline, in-memory business layer, current routers/tests, and missing frontend product surface |
| P0-TC-007 | Assumption cleanup is explicit | PRD lists embedded-site removal, SSO deferral, simulated data, no production RAG, no real schema before Phase 6, mobile in scope |
| P0-TC-008 | Old-doc matrix is complete enough | Matrix covers technical PRD, technical test spec, business PRD, and business test spec with disposition, reason, new position, and supersession status |
| P0-TC-009 | Approval state is honest | Artifacts say draft/pending approval and do not mark Phase 0 accepted before user approval |
| P0-TC-010 | Runtime scope is untouched | No product code implementation is claimed in Phase 0 |

## Future Acceptance Shape

Later executable phases must derive tests from this baseline:

- Phase 1: route map, design tokens, desktop/mobile IA, frontend stack approval.
- Contract/Data Boundary Node: field/role/API/persistence/audit contracts.
- Phase 2: Demo login success, bad credentials, role routing, access denial, expired/unauthorized states.
- Phase 3: deterministic student Q&A hit, unsupported fallback, source card, conversation UI, mobile layout.
- Phase 4: admin Demo knowledge view/edit/enable-disable or add/delete as approved, seed/reset, stats/activity, role protection.
- Phase 5: counselor case list/detail, advisory assistance labeling, status/action update, role protection, mobile layout.
- Phase 6: persistence survival, migration upgrade/downgrade, repository/service tests.
- Phase 7: approved retrieval path, source citation, no-answer fallback, rebuild smoke, deterministic fallback switch.
- Phase 8: responsive QA for homepage, login, student, counselor, admin; overflow and label consistency checks.
- Phase 9: Docker Compose startup, health/readiness, backend tests, frontend build, Demo script against composed stack.

## Phase 0 Failure Conditions

Phase 0 is not ready for approval if:

- Any old Phase 1 doc is silently reused without disposition.
- The plan still assumes embedded official-site UI.
- The plan makes SSO mandatory for Demo login.
- The plan requires real student data.
- Phase 3 is described as RAG/vector/provider-backed.
- Phase 4 requires real schema or production ingestion.
- Mobile is treated as out of scope.
- Any implementation work begins before the relevant approval gates.

## Verification Commands Used For This Draft

Planning verification should use file checks and text checks, not app execution:

```powershell
Get-Item .omx/plans/overall-development-plan-ai-counselor-demo.md
Get-Item .omx/plans/prd-ai-counselor-demo-phase0.md
Get-Item .omx/plans/test-spec-ai-counselor-demo-phase0.md
Get-Item .omx/plans/approval-packages-ai-counselor-demo-phase0.md
Get-Item .omx/logs/phase-00-requirements-test-update.md
Select-String -Path .omx/plans/prd-ai-counselor-demo-phase0.md -Pattern "Old PRD/Test Spec Alignment Matrix"
```

## Rollback

Revert only Phase 0 artifacts. Runtime code, Docker files, and tests are not part of this phase.

