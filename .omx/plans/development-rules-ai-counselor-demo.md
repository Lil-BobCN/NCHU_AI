# Development Rules: AI Counselor Demo

Date: 2026-05-17

## Operating Model

The user is the product manager.

Codex is the lead programmer.

The development process is strict, auditable, and interactive. Codex should not take on too many tasks at once. Work must be decomposed into small task nodes, and key decisions must be approved before implementation.

## Per-Phase Lifecycle

Each phase follows this lifecycle:

1. Phase intake.
2. `$deep-interview` alignment.
3. Approval of phase scope.
4. `$autoresearch` for mature open-source solutions when relevant.
5. Approval of key technical/UI/database/component choices.
6. Branch creation.
7. Small task node implementation.
8. Verification.
9. Development log update.
10. Risk and rollback note update.
11. Phase acceptance summary.

## Required Phase Artifacts

Each phase should produce or update:

- `.omx/interviews/<phase>-*.md`
- `.omx/specs/<phase>-*.md`
- `.omx/specs/autoresearch-<phase>/report.md` when research is needed
- `.omx/plans/<phase>-prd.md` or phase scope note
- `.omx/plans/<phase>-test-spec.md`
- `.omx/logs/phase-<phase>-<slug>.md`
- Acceptance evidence section
- Risk register section
- Rollback section

## Approval Gate Template

Use this template before key decisions:

```md
## Decision Package: <topic>

### Recommended Option
<one clear recommendation>

### Alternative Options
<viable alternatives>

### Why This Option
<reasoning and tradeoffs>

### Impact Scope
<files, modules, data, UI, tests, deployment>

### Risks
<known risks and mitigations>

### Acceptance / Verification
<how we prove it works>

### Questions For You
<specific confirmations needed>
```

## Key Decision Definition

Ask the user before continuing when a task involves:

- Key technical selection.
- UI structure.
- Database structure.
- Open-source component introduction.
- Product positioning.
- Real school resources.
- SSO.
- Real student data.
- Production security.
- Public launch or official deployment boundary.

## Small Task Node Template

```md
## Task Node: <name>

Goal:

Approved scope:

Decision gates:

Implementation steps:

Files likely affected:

Tests/verification:

Rollback note:
```

## Default Branch Rule

Use a branch per phase:

```text
phase/<phase-number>-<short-slug>
```

Examples:

```text
phase/00-requirements-test-update
phase/01-frontend-skeleton-design-system
phase/02-demo-login-role-routing
```

## Default Log Rule

Each phase maintains a log:

```text
.omx/logs/phase-<phase-number>-<short-slug>.md
```

Every log entry records:

- Time.
- Task node.
- Approval gate, if any.
- Files changed.
- Tests run.
- Result.
- Risks.
- Rollback note.

## Phase Rules

### Phase 0: Requirements And Test Update

Start with `$deep-interview`:

- Present exact requirement changes.
- Present updated test scope.
- Ask which old assumptions should be removed.

Use `$autoresearch` only if requirement/test governance format needs external examples.

Approval needed for:

- PRD structure.
- Test acceptance scope.
- Any change to product positioning.

### Phase 1: Frontend Skeleton And Design System

Start with `$deep-interview`:

- Present page map.
- Present desktop/mobile layout approach.
- Present design style options.
- Present frontend stack/component-library options.

Use `$autoresearch`:

- Compare mature frontend options and component libraries.
- Keep choices compatible with the existing repo and deployment path.

Approval needed for:

- UI information architecture.
- Design system direction.
- Component library introduction.
- Mobile navigation pattern.

### Phase 2: Demo Login And Role Routing

Start with `$deep-interview`:

- Present role model.
- Present login flow.
- Present session/token approach.
- Present route protection approach.

Use `$autoresearch`:

- Compare FastAPI-compatible auth/session approaches and mature libraries.
- Keep real SSO deferred.

Approval needed for:

- Auth architecture.
- Demo account model.
- Session/token storage.
- Open-source auth component introduction.

### Phase 3: Student Flow

Start with `$deep-interview`:

- Present student page flow.
- Present Q&A data contract.
- Present source/resource display.
- Present mobile-first interaction.

Use `$autoresearch`:

- Investigate mature chat/Q&A UX patterns and FastAPI/RAG integration patterns.

Approval needed for:

- Student UI structure.
- Q&A API contract.
- Knowledge answer behavior.

### Phase 4: Admin Knowledge Flow

Start with `$deep-interview`:

- Present knowledge model.
- Present admin operations.
- Present ingestion/indexing path.
- Present audit requirements.

Use `$autoresearch`:

- Compare mature admin CRUD, knowledge ingestion, and document storage patterns around FastAPI, PostgreSQL, MinIO, and Milvus.

Approval needed for:

- Database schema.
- Knowledge model.
- Open-source admin/CRUD component.
- Ingestion/indexing architecture.

### Phase 5: Counselor Flow

Start with `$deep-interview`:

- Present counselor case workflow.
- Present assistant output types.
- Present status model.
- Present relation to student Q&A.

Use `$autoresearch`:

- Investigate case-management/workbench patterns and AI-assisted workflow patterns.

Approval needed for:

- Counselor UI structure.
- Case/status data model.
- Assistant output contract.

### Phase 6: Persistence Hardening

Start with `$deep-interview`:

- Present schema migration plan.
- Present repository/service structure.
- Present rollback strategy.

Use `$autoresearch`:

- Compare FastAPI + SQLAlchemy/Alembic patterns, repository/service layering, and migration workflow.

Approval needed for:

- Database schema.
- Migration tooling.
- Data access structure.
- Any data migration risk.

### Phase 7: Knowledge/RAG Integration

Start with `$deep-interview`:

- Present RAG pipeline.
- Present embedding/model provider options.
- Present MinIO/Milvus structure.
- Present fallback behavior.

Use `$autoresearch`:

- Compare mature RAG frameworks/components that can work with FastAPI, MinIO, and Milvus.

Approval needed for:

- RAG framework/component.
- Embedding model/provider.
- Vector schema.
- Source citation behavior.

### Phase 8: Responsive QA And Product Polish

Start with `$deep-interview`:

- Present QA checklist.
- Present visual quality criteria.
- Present desktop/mobile viewport targets.

Use `$autoresearch` only if choosing new visual/test tooling.

Approval needed for:

- Major UI changes.
- New visual testing tools.
- Changes to product tone or information architecture.

### Phase 9: Docker/Deployment Smoke

Start with `$deep-interview`:

- Present deployment checklist.
- Present Docker/env changes.
- Present Alibaba Cloud assumptions.

Use `$autoresearch`:

- Investigate deployment hardening and common Docker Compose production-ish practices, without overbuilding full production.

Approval needed for:

- Deployment topology changes.
- New infrastructure components.
- Security/public exposure boundary.

## Implementation Permission Rule

After approval, Codex may implement within the approved small task node without asking for every line-level change.

Codex must pause and ask again if implementation reveals a new key decision.

