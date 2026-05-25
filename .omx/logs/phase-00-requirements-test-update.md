# Phase 00 Log: Requirements/Test Update

Date: 2026-05-17
Status: first approval package accepted by product manager

## Scope

Phase 0 updates planning and verification artifacts only. Runtime code, frontend implementation, backend schema, RAG, deployment, and server configuration are out of scope.

## Task Nodes Covered In This Batch

| Task node | Result | Files |
| --- | --- | --- |
| P0-N1 Evidence inventory and assumption cleanup | Completed as draft | `.omx/plans/prd-ai-counselor-demo-phase0.md` |
| P0-N4 First approval package | Completed as draft | `.omx/plans/approval-packages-ai-counselor-demo-phase0.md` |
| P0-N7 Old PRD/Test Spec alignment matrix | Completed as draft | `.omx/plans/prd-ai-counselor-demo-phase0.md` |
| Master plan merge | Completed as draft | `.omx/plans/overall-development-plan-ai-counselor-demo.md` |
| Phase 0 test acceptance baseline | Completed as draft | `.omx/plans/test-spec-ai-counselor-demo-phase0.md` |

## Evidence Inventory Summary

- `backend/` is the formal FastAPI backend path.
- `backend/docker-compose.phase1.yml` and docs show the current technical baseline: FastAPI, PostgreSQL, Redis, MinIO, Milvus.
- `backend/app/api/v1/router.py` aggregates health, auth, student, counselor, and admin routers.
- `backend/app/services/business.py` states the business service is in-memory.
- `backend/tests/test_business_phase1.py` covers current in-memory business API behavior.
- No tracked production frontend product surface exists in the current file list.
- The old technical/business PRD and test-spec files remain present and are reconciled through the new matrix.

## Assumptions Removed Or Narrowed

- Embedded official-site assistant is replaced by a standalone product website linked from the official site.
- Mandatory SSO is deferred; Demo/local login comes first.
- Real student data is out of scope.
- Production RAG/vector/provider work is deferred.
- Real schema/migrations are deferred until approved Phase 6 subsets.
- Static fake screens are not acceptable as final Demo flows.
- Mobile is in scope from the start.

## Approval Gates Open

- Product scope approval: accepted on 2026-05-17.
- PRD/test structure approval: accepted on 2026-05-17.
- Old-doc supersession approval: accepted on 2026-05-17.
- Permission to proceed to Phase 1 planning after Phase 0 acceptance: accepted on 2026-05-17.

Approval evidence: user stated "我同意".

## Risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| User expects implementation to begin immediately | Medium | Stop after Phase 0 artifacts and ask for explicit approval before Phase 1 planning/implementation. |
| Old docs conflict with new Demo route | High | Use alignment matrix and supersession statement. |
| Phase 3 gets interpreted as RAG | Medium | PRD and test spec state deterministic answer-source adapter only until Phase 7 approval. |
| Contract fields sprawl during implementation | High | Contract/Data Boundary Node is a hard gate before Phase 2+ API-connected UI. |

## Verification

Planned checks:

- Verify Phase 0 files exist.
- Verify PRD contains evidence inventory, assumption cleanup, and old-doc matrix.
- Verify approval package remains pending, not approved.
- Verify no runtime implementation is claimed.

## Rollback

Revert only:

- `.omx/plans/overall-development-plan-ai-counselor-demo.md`
- `.omx/plans/prd-ai-counselor-demo-phase0.md`
- `.omx/plans/test-spec-ai-counselor-demo-phase0.md`
- `.omx/plans/approval-packages-ai-counselor-demo-phase0.md`
- `.omx/logs/phase-00-requirements-test-update.md`

No runtime rollback is required because Phase 0 does not change app code.
