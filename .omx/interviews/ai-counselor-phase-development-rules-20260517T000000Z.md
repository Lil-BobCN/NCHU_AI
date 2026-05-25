# Deep Interview: Phase Development Rules

Date: 2026-05-17
Profile: standard
Final ambiguity: 12%
Status: complete

## Outcome

This interview defined how future AI counselor Demo development should be governed.

The user wants a strict, auditable, product-manager-led process. Codex should act as lead programmer: propose plans, explain technology, implement, test, and document evidence, while the user approves key product and technical decisions.

## Key Decisions

- Governance level: strict auditable.
- Each phase must begin with alignment before implementation.
- Each phase must use `$deep-interview` for structured clarification.
- Each phase must use `$autoresearch` to investigate mature open-source approaches/components where relevant.
- FastAPI remains the core backend framework.
- Mature open-source components may be integrated around FastAPI, but component introduction requires approval.
- Work must be decomposed into small task nodes.
- Codex should not execute many large tasks at once.
- Each key task node should include interaction and approval when it touches technical choices, UI structure, database structure, or open-source components.

## Mandatory Approval Areas

User approval is required before continuing when a task changes or introduces:

- Key technical selection.
- UI structure.
- Database structure.
- Open-source component.
- Product direction.
- Real school resource assumptions.
- SSO integration.
- Production security/public launch boundary.

## Approval Package Template

Every key decision package should include:

1. Recommended option.
2. Alternative options.
3. Why this option is recommended.
4. Impact scope.
5. Risks.
6. Acceptance/verification method.
7. Questions requiring user confirmation.

## Working Style

The user acts as product manager.

Codex acts as lead programmer:

- Decompose work into small task nodes.
- Present technical details clearly before key implementation.
- Ask for approval at decision gates.
- Continue implementation within approved boundaries.
- Keep logs, evidence, and rollback notes.

