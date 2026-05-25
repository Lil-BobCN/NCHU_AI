# Deep Interview Spec: AI Counselor Demo Scope Realignment

Date: 2026-05-17
Context type: brownfield
Profile: standard
Final ambiguity: 13%
Threshold: 20%
Context snapshot: `.omx/context/ai-counselor-business-phase1-20260515T072709Z.md`
Transcript: `.omx/interviews/ai-counselor-demo-scope-realignment-20260517T000000Z.md`

## Intent

Build a credible Demo that presents the AI counselor system as an independent, formal-product-like website. The Demo should prove the product direction and user value before investing in real SSO, real student data, production hardening, and official school website integration.

## Desired Outcome

The school official website can link to the independent AI counselor site. A viewer can enter the site and experience:

- Homepage.
- Login page.
- Student side.
- Counselor side.
- Admin side.
- Desktop and mobile layouts.
- Synthetic data clearly labeled as demo/simulated.
- Real system flows where implemented, not static fake screens.

## In Scope

- Independent main website.
- Demo login with role-based accounts.
- Student Q&A and resource discovery.
- Counselor assistance/workbench.
- Admin knowledge/content management.
- Synthetic demo dataset.
- Clear simulated-data labeling.
- Desktop and mobile development together.
- Real API integration for the Demo flow.
- PostgreSQL persistence migration where needed for Demo credibility.
- MinIO/Milvus/RAG integration where needed for knowledge-driven answers.
- Basic role isolation and audit traces.
- Demo script and acceptance path.

## Out Of Scope / Non-Goals

- Real school SSO integration.
- Real student private data.
- Production-grade security audit.
- ICP filing/formal domain/HTTPS as Demo success prerequisites.
- Real school official website modification.
- Full production operations, backups, monitoring, and compliance.

## Decision Boundaries

Codex may decide:

- Information architecture.
- UI style.
- Desktop/mobile layout tradeoffs.
- Synthetic demo data.
- Demo script.
- Technical implementation details.
- File/module decomposition.
- Incremental delivery order.

Codex should ask before:

- Changing product positioning.
- Depending on real school resources.
- Integrating real SSO.
- Using real student data.
- Expanding production launch/security commitments.
- Requiring school official website modification.

## Acceptance Criteria

- The Demo has a formal standalone homepage, login page, student side, counselor side, and admin side.
- Student, counselor, and admin flows can be demonstrated as one connected product story.
- Synthetic/demo data is visibly labeled.
- Login works with Demo accounts and role-specific access.
- Student can ask a question and see an answer/resource path.
- Counselor can view assistance context and act on a simulated case.
- Admin can maintain knowledge/demo content or see knowledge management state.
- Desktop and mobile views are both usable.
- The system does not imply use of real student data.
- Real SSO is clearly positioned as future integration, not current Demo functionality.

## Development Plan Summary

Detailed plan: `.omx/plans/development-plan-ai-counselor-demo-scope-realignment.md`

Recommended handoff after this interview: update PRD/test spec first, then execute implementation with `$ralph` or `$team` depending on whether parallel frontend/backend work is desired.

