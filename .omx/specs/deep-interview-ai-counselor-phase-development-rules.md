# Deep Interview Spec: AI Counselor Phase Development Rules

Date: 2026-05-17
Context type: brownfield
Profile: standard
Final ambiguity: 12%
Threshold: 20%
Transcript: `.omx/interviews/ai-counselor-phase-development-rules-20260517T000000Z.md`
Related plan: `.omx/plans/development-plan-ai-counselor-demo-scope-realignment.md`

## Intent

Define a disciplined, repeatable, auditable development process for the AI counselor Demo. The process should support collaborative product-manager-style approval while still allowing Codex to execute implementation efficiently after decisions are approved.

## Development Governance Rule

Use strict auditable governance for every development phase.

Every phase must have:

- Phase alignment record.
- Phase PRD/scope note.
- Phase test specification.
- `$autoresearch` mature-solution report when technology/UI/database/component decisions are involved.
- Branch plan.
- Development log.
- Commit discipline.
- Acceptance evidence.
- Risk register.
- Rollback notes.
- Phase summary.

## Phase Opening Rule

Every phase begins with a small `$deep-interview` alignment.

The opening alignment must present:

- What this phase will build.
- Technical nodes.
- Technologies and components under consideration.
- Required cooperation or external resources.
- Code-level structure proposal.
- Technical explanation of the plan.
- Proposed small task nodes.
- Key decisions requiring approval.

The phase cannot begin implementation until the phase-level decision gates are resolved.

## Research Rule

After phase alignment, use `$autoresearch` where relevant to investigate mature approaches.

Research must preserve:

- FastAPI as the core backend framework.
- Preference for mature open-source components around FastAPI instead of hand-rolling common backend capabilities.
- Component introduction requires approval.
- Research output must compare recommended option and alternatives.
- Research must include implementation impact, risk, maintenance cost, and verification method.

## Small Task Node Rule

Work must be decomposed into small task nodes.

For each task node, Codex must identify whether it touches:

- Key technical selection.
- UI structure.
- Database structure.
- Open-source component.
- Product direction.
- External school resource.
- SSO.
- Production/public launch security boundary.

If yes, Codex must ask for approval using the approval package template before implementation.

If no, Codex may implement within the already approved scope and then provide verification evidence.

## Approval Package Template

Use this exact structure for key decisions:

1. Recommended option.
2. Alternative options.
3. Why this option is recommended.
4. Impact scope.
5. Risks.
6. Acceptance/verification method.
7. Questions requiring user confirmation.

## Branch And Log Rule

Each phase should use a dedicated branch when code changes begin.

Suggested branch format:

```text
phase/<phase-number>-<short-slug>
```

Each phase should maintain a development log under:

```text
.omx/logs/phase-<phase-number>-<short-slug>.md
```

The log should include:

- Date/time.
- Task node.
- Decision package links.
- User approval summary.
- Files changed.
- Tests run.
- Known risks.
- Rollback note.

## Commit Rule

Commits should follow the repository Lore Commit Protocol from `AGENTS.md`.

Commit messages must describe why the change was made and include relevant trailers such as:

- `Constraint:`
- `Rejected:`
- `Confidence:`
- `Scope-risk:`
- `Directive:`
- `Tested:`
- `Not-tested:`

## Verification Rule

Every task node must end with a verification note.

Verification can include:

- Unit tests.
- API tests.
- Frontend build/lint.
- Type checks.
- Responsive viewport checks.
- Docker Compose smoke tests.
- Manual Demo script dry run.

If a verification step cannot be run, record why and what the next-best evidence is.

## Rollback Rule

Every phase must include rollback notes:

- Files/modules affected.
- Data/schema migration risk.
- How to revert or disable the feature.
- Whether rollback requires data cleanup.

## Stop Conditions

Stop and ask the user when:

- A key decision requires approval.
- Scope expands beyond the approved phase.
- A new dependency/component is needed.
- Database schema changes are required.
- UI information architecture changes.
- A real school resource or SSO assumption is introduced.
- Production security/public launch boundaries change.

Continue without asking when:

- Work is within an approved task node.
- Changes are implementation details.
- Tests or small bug fixes are needed to satisfy approved acceptance criteria.
- Documentation/log updates are needed for the current phase.

## Recommended Next Step

Use this rules spec to update or create a phase-by-phase governance plan, then begin Phase 0: Requirements And Test Update.

