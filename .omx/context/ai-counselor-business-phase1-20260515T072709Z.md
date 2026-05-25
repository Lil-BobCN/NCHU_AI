# Business Phase 1 Context Snapshot: AI Counselor System

Task statement: Create the next execution plan for the AI counselor project after the technical foundation and system positioning have been agreed.

Desired outcome: A product-facing P0/P1 plan that prioritizes student self-service Q&A and school resource retrieval, while keeping a counselor workbench, knowledge-base operations, authentication, and auditability in scope for the next build phase.

Stated solution:
- FastAPI remains the formal backend.
- The school SSO should be integrated via a FastAPI-side adapter.
- The main product shape is student self-service Q&A + knowledge-base backend + counselor assistance.

Known facts/evidence:
- Technical Phase 1 foundation already exists in the repository plan set.
- `backend/` is the formal FastAPI backend path.
- PostgreSQL, Redis, MinIO, and Milvus are the formal infrastructure stack.
- Legacy Flask/Qdrant code is reference-only for migration.
- Public NCHU SSO research indicates a custom SSO flow is more realistic than standard OIDC/CAS.
- Local project docs already define the technical stack, smoke gate, and legacy boundary.
- The requirements doc and implementation plan both emphasize school knowledge-base RAG, resource links, maintenance, and multi-stage growth.

Constraints:
- Do not re-open broad requirements interviews.
- Keep the plan aligned with the already accepted product positioning.
- Do not start implementation in this step.
- The plan must distinguish what is P0/P1 now versus later P2/P3 capabilities.
- The plan should remain suitable for a mainland-China / Linux / Aliyun / private-deployment path.

Unknowns/open questions:
- Exact boundaries between P0 and P1 for knowledge-base operations and counselor workbench.
- Whether the first business release needs a public student entry only, or also a counselor-first operating console.
- Which features must be included in the first test spec versus deferred to later phases.

Likely codebase touchpoints:
- `.omx/plans/`
- `.omx/state/`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/FASTAPI-SYSTEM.md`
- `backend/`

Prompt-safe initial-context summary status: not_needed
