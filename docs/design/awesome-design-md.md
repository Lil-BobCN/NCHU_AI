# awesome-design-md Project Configuration

## Source

- Repository: https://github.com/VoltAgent/awesome-design-md
- License: MIT
- Purpose: curated `DESIGN.md` files inspired by public developer-focused websites and brands.
- Retrieved/confirmed: 2026-05-25

The source project describes `DESIGN.md` as a markdown design-system document that coding/design agents can read from a project root to generate consistent UI.

## How This Project Uses It

This repository does not vendor the full external collection by default. Instead:

- `PRODUCT.md` defines the NCHU AI Counselor product context.
- `DESIGN.md` is the project-level design entry point for agents.
- This file records how to select and apply individual `awesome-design-md` references.

This keeps the project identity stable while allowing fast exploration of specific visual directions.

## Agent Workflow

For frontend or design work:

1. Read `PRODUCT.md`.
2. Read root `DESIGN.md`.
3. If a specific reference is requested, fetch or inspect that reference from `https://getdesign.md/<name>/design-md` or the upstream repository.
4. Adapt tokens and interaction patterns to this product; do not copy brand identity, logos, or proprietary assets.
5. Implement within the existing frontend stack unless the user explicitly approves a stack change.
6. Verify with lint/build and browser screenshots when UI changes are made.

## Reference Selection Guide

Use these as starting points:

| Need | Candidate reference | Why |
| --- | --- | --- |
| Calm operational dashboards | Linear | Precise hierarchy, low visual noise, efficient workflows |
| Knowledge-base and resource pages | Mintlify | Reading-optimized layout and documentation clarity |
| Student support conversations | Intercom | Support-oriented interaction patterns and approachable tone |
| Technical admin surfaces | Vercel, Resend | Restrained developer-product UI with strong spacing discipline |
| Dark agent-console experiments | VoltAgent, OpenCode AI | Agent-native, technical dark surfaces |
| Data-heavy audit/stat screens | Sentry, Supabase | Dense operational data and clear status treatment |

## How To Use Manually

To ask an agent to use this configuration:

```text
Use PRODUCT.md and DESIGN.md. For this screen, adapt the Linear reference from awesome-design-md, but keep the NCHU AI Counselor product tone and Chinese-first labels.
```

For another reference:

```text
Use PRODUCT.md and DESIGN.md. Adapt the Mintlify reference from awesome-design-md for the knowledge-resource page. Do not copy the Mintlify brand; use it only for layout, hierarchy, spacing, and documentation-style clarity.
```

## Optional Full Reference Copy

If a task needs offline access to a specific upstream `DESIGN.md`, copy only that selected file into:

```text
docs/design/references/<reference-name>/DESIGN.md
```

Then mention it explicitly in the task prompt:

```text
Use docs/design/references/linear/DESIGN.md as the visual reference.
```

Avoid copying all upstream references into the repo unless there is a clear offline or review requirement.

## Update Procedure

1. Open the upstream collection: https://github.com/VoltAgent/awesome-design-md
2. Pick the exact reference needed for the task.
3. If vendoring a reference, add it under `docs/design/references/<reference-name>/DESIGN.md`.
4. Record the source URL and retrieval date near the top of the vendored file.
5. Review for proprietary assets or instructions that conflict with this project's `PRODUCT.md` and root `DESIGN.md`.

## Rollback

To remove this configuration:

1. Delete `DESIGN.md` if it is no longer wanted as the project-level design entry point.
2. Delete `PRODUCT.md` only if another product-context document replaces it.
3. Delete this file and any vendored `docs/design/references/*` files.

