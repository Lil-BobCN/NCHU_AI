# Approval Packages: AI Counselor Demo Phase 0

Date: 2026-05-17
Status: approved by product manager

## Package 1: Phase 0 Product Scope, PRD/Test Structure, And Old-Doc Supersession

### Decision Title

Adopt the independent AI Counselor Demo Phase 0 baseline and supersede older Phase 1 planning files for Demo planning.

### Recommended Option

Approve `.omx/plans/overall-development-plan-ai-counselor-demo.md`, `.omx/plans/prd-ai-counselor-demo-phase0.md`, and `.omx/plans/test-spec-ai-counselor-demo-phase0.md` as the current Demo planning baseline.

Use the RALPLAN consensus as the detailed governance source and keep old Phase 1 PRD/Test Spec files as historical references only.

### Alternatives Considered

| Alternative | Reason not recommended |
| --- | --- |
| Continue using old technical and business Phase 1 docs directly | They mix infrastructure, SSO, real schema, RAG/vector work, knowledge ingestion, and business acceptance into one broad phase. |
| Delete old planning files | Deleting loses useful historical context and makes scope changes less auditable. |
| Start Phase 1 frontend implementation immediately | Frontend stack, IA, design tokens, route map, API integration points, and contract boundary are not approved yet. |
| Build backend schema/RAG first | This delays the formal Demo experience and contradicts the approved staged route. |

### Why Recommended

This option keeps planning traceable while aligning the next work with the updated product direction:

- Standalone product website linked from the school official website.
- Demo/local login first; SSO later.
- Homepage, login, student, counselor, and admin surfaces required.
- Desktop and mobile both in scope.
- Simulated data allowed only with explicit labeling.
- Contract gates before API-connected UI and persistence work.

### Impacted Files/Resources

New or updated planning/log artifacts:

- `.omx/plans/overall-development-plan-ai-counselor-demo.md`
- `.omx/plans/prd-ai-counselor-demo-phase0.md`
- `.omx/plans/test-spec-ai-counselor-demo-phase0.md`
- `.omx/plans/approval-packages-ai-counselor-demo-phase0.md`
- `.omx/logs/phase-00-requirements-test-update.md`

Historical references:

- `.omx/plans/prd-ai-counselor-technical-phase1.md`
- `.omx/plans/test-spec-ai-counselor-technical-phase1.md`
- `.omx/plans/prd-ai-counselor-business-phase1.md`
- `.omx/plans/test-spec-ai-counselor-business-phase1.md`

Runtime code:

- No runtime code changes in this package.

### Data Boundary Impact

- Real student data remains out of scope.
- Simulated Demo data is allowed only when visibly labeled.
- SSO real identity data is deferred.
- No new database schema is approved by this package.
- No RAG/vector/provider data path is approved by this package.

### API/UI/Database/Component Impact

- API impact: none in Phase 0.
- UI impact: defines required pages and future Phase 1 planning gates, but does not approve implementation.
- Database impact: none; schema approval is deferred to Contract/Data Boundary Node and Phase 6.
- Component impact: none; frontend stack and component-library choices require Phase 1 approval.

### Risks

| Risk | Mitigation |
| --- | --- |
| Old documents continue to cause scope drift | The alignment matrix marks each old clause as keep/narrow/defer/delete/convert. |
| Planning becomes too slow | Use small task nodes and allow read-only research during review. |
| Demo is mistaken for production readiness | Require simulated-data labels and explicit non-goals. |
| Frontend starts before contracts | Contract/Data Boundary Node is a hard gate before API-connected UI. |

### Rollback

Revert the Phase 0 artifacts listed above. Old files remain unchanged.

### Acceptance / Verification

Package is accepted when the product manager confirms:

- The overall Demo route is correct.
- The Phase 0 PRD/test baseline is acceptable.
- The old PRD/Test Spec matrix can supersede old files for Demo planning.
- Phase 1 may proceed only as planning until its own approval package is accepted.

### Questions For You

1. Do you approve this Phase 0 baseline as the current source of truth for Demo planning?
2. Do you approve that the four old Phase 1 PRD/Test Spec files remain historical references and are superseded for the Demo route by the new Phase 0 artifacts?
3. Do you approve moving next to Phase 1 planning only, not implementation, after Phase 0 is accepted?

### Approval Result

Approved by product manager.

Approval date: 2026-05-17.

Approval evidence: user stated "我同意".
