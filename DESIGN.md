# NCHU AI Counselor Design Guidance

## Design Source Configuration

This project is configured to use [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) as an optional external design reference library.

Use this file as the project-level design entry point. Do not replace the product's institutional identity with an external brand by default. When a user asks for a specific visual direction, pick a suitable `awesome-design-md` reference and adapt its principles to the NCHU AI Counselor product context.

Reference catalog and usage notes live in `docs/design/awesome-design-md.md`.

## Default Register

The default UI register for this project is an institutional operations product:

- quiet, structured, and task-focused;
- Chinese-first labels and copy where user-facing text is added;
- restrained but polished visual treatment;
- dense enough for repeated counselor/admin use without becoming cluttered;
- clear enough for student self-service without requiring explanation.

## Visual Principles

- Prefer full-width app surfaces, split panes, sidebars, tables, timelines, message panels, and dashboard bands over marketing cards.
- Use cards only for repeated entities, modals, and genuinely framed tools.
- Keep navigation predictable and stable across student, counselor, and admin surfaces.
- Use color semantically: primary action, success, warning, danger, neutral, and selected state.
- Keep motion subtle and functional: transitions should clarify state changes, not decorate the page.
- Use icons for tools and actions when an established icon exists; add concise tooltips for unfamiliar controls.

## Typography

- Favor clean sans-serif UI typography with strong numeric readability.
- Keep display-scale type for true page headers only.
- Use compact headings inside dashboards, tool panels, sidebars, and cards.
- Avoid negative letter spacing and viewport-scaled font sizing.
- Ensure Chinese and mixed Chinese/English labels fit their containers on desktop and mobile.

## Layout

- Build responsive constraints intentionally with grid tracks, min/max widths, stable toolbar dimensions, and fixed-format component sizing where useful.
- Keep repeated workflows close to their controls: filters near lists, actions near selected items, state indicators near affected content.
- Make loading, empty, error, and permission states first-class.
- Avoid overlapping text, floating decorative elements, and nested cards.

## Applying awesome-design-md

When using an external reference:

1. Read `PRODUCT.md`, this `DESIGN.md`, and `docs/design/awesome-design-md.md`.
2. Select one reference based on the task, audience, and surface type.
3. Import the reference's useful tokens and interaction ideas, not its brand identity.
4. State the selected reference and what was adapted before implementation.
5. Verify the result in browser screenshots for desktop and mobile when changing frontend UI.

Good default references to consider:

- `Linear` for calm issue/workflow dashboards.
- `Mintlify` for readable knowledge-base and documentation surfaces.
- `Intercom` for support conversation and handoff flows.
- `Vercel` or `Resend` for restrained developer/admin surfaces.
- `VoltAgent` only when a dark, agent-native technical surface is explicitly desired.

## Guardrails

- Do not copy logos, proprietary illustrations, or exact brand identity from external references.
- Do not make the application look like a public marketing site unless the user asks for a landing page.
- Do not introduce a new dependency just to match a reference style.
- Keep accessibility, responsive behavior, and the existing React/Vite/Ant Design stack constraints ahead of visual novelty.

