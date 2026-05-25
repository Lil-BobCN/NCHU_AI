# Autoresearch Report: Frontend Visual Design Systems For SDAR-0004

Date: 2026-05-18
Status: completed for SDAR-0004 revision

## Research Goal

Support SDAR-0004 with mature design-system evidence and product-manager-readable explanations for:

- visual style: modern and technical, but still formal and credible;
- homepage interaction structure;
- student-side interaction structure;
- why CSS variables/design tokens are needed;
- radius, density, spacing, and style boundaries.

## Sources Reviewed

- Ant Design Customize Theme: https://ant.design/docs/react/customize-theme/
- shadcn/ui Theming: https://ui.shadcn.com/docs/theming
- Atlassian Design Tokens: https://atlassian.design/foundations/tokens/design-tokens/
- Atlassian Spacing: https://atlassian.design/foundations/spacing/
- Carbon Design System Spacing: https://carbondesignsystem.com/elements/spacing/overview/
- Material Design Color Overview: https://m3.material.io/styles/color/overview

## Design-System Findings

### Ant Design

Ant Design is a strong fit for counselor and management workspaces because it supports mature enterprise UI patterns and theme customization through design tokens.

Important evidence:

- Ant Design can modify global theme through `theme.token`.
- Ant Design uses `Seed Token`, `Map Token`, and `Alias Token`.
- Ant Design can generate palettes and rounded-corner styles from seed tokens.
- Ant Design default base `borderRadius` is `6`.

Implication for our project:

- Workbench areas should lean on Ant Design.
- Our initial workbench radius can be `6px`.
- We can use `8px` only for larger product cards where a more modern feel is needed.

### shadcn/ui

shadcn/ui is a good fit for homepage, login, and student-facing pages because it is flexible and product-looking.

Important evidence:

- shadcn/ui recommends CSS variables for theming.
- It uses semantic tokens like `background`, `foreground`, `primary`, `card`, `border`, `sidebar`, and chart tokens.
- Changing CSS variables changes the app look without rewriting all component classes.

Implication for our project:

- Homepage and student UI can use shadcn/ui or custom components.
- CSS variables should be the shared source for color, radius, spacing, and typography.

### Atlassian

Atlassian's design system is useful as a mature reference for product consistency and density.

Important evidence:

- Atlassian describes design tokens as a single source of truth for visual decisions.
- Atlassian spacing uses an 8px base unit.
- It explicitly connects spacing systems with future customizable density.

Implication for our project:

- Use an 8px spacing rhythm as the default.
- Use smaller spacing for dense workbench details and larger spacing for homepage/student readability.

### Carbon Design System

Carbon is useful as a mature enterprise-product reference.

Important evidence:

- Carbon uses spacing tokens to remove guesswork and create clear functional layouts.
- Its scale includes 2px, 4px, 8px, 12px, 16px, 24px, 32px, and larger values.
- Carbon ties spacing to product density.

Implication for our project:

- Our spacing scale of 4/8/12/16/24/32/48 is reasonable.
- Workbench pages can be denser without becoming visually chaotic.

### Material Design

Material Design is useful as a reference for mobile navigation, color roles, elevation, and interaction states.

Implication for our project:

- Use Material as a secondary reference for mobile navigation and touch-friendly states.
- Do not copy Material wholesale; our React stack is Ant Design + shadcn/ui.

## Recommended Style Direction

Use:

- Formal enough for a school and counselor product.
- Modern enough to feel like an AI product.
- Technical enough to look credible, but not dark, overdecorated, or sci-fi.

Avoid:

- large dark-blue/purple gradient backgrounds;
- decorative glowing orbs;
- over-rounded cards;
- marketing-page bloat;
- dense admin styling on the student page.

## Homepage User Interaction Description

### User Journey

1. User enters from the school website link or direct Demo URL.
2. User sees a clean product homepage with:
   - product name;
   - Demo/simulated-data label;
   - one concise value statement;
   - two clear role cards: `我是老师/辅导员`, `我是学生`.
3. User clicks a role card.
4. The system goes to the login page with the chosen role intent preserved.
5. After Demo login:
   - teacher/counselor goes to `/counselor`;
   - student goes to `/student`.
6. Management is not shown on the homepage. Management users use an independent link such as `/admin`.

### Why This Meets User Needs

- Reduces confusion: ordinary users only see the two roles they understand.
- Avoids accidental management access: management is not a public homepage card.
- Supports Demo explanation: stakeholder can clearly demonstrate teacher and student flows.
- Preserves future backend integration: role intent can later feed into auth routing.

### Pros

- Simple first screen.
- Formal product feel.
- Easy to explain during Demo.
- Keeps management boundary cleaner.

### Cons

- Management entry must be documented separately.
- If evaluators expect an admin demo, someone must know the independent management URL.
- Role cards are not real security; actual access still depends on login and backend permissions.

## Student UI Interaction Description

### User Journey

1. Student logs in and enters `/student`.
2. Student sees:
   - a central question input;
   - recent or suggested questions;
   - Demo data label;
   - quick access to resources/history.
3. Student asks a question.
4. The answer area appears:
   - answer text;
   - source/resource card;
   - fallback message if no supported Demo answer exists.
5. Student can open source/resource details.
6. Student can switch to history to continue or review previous conversations.

### Why This Meets User Needs

- Student's main goal is asking a question, not managing data.
- Source cards build trust and teach the user where information came from.
- History helps multi-turn use without making the page feel like an admin dashboard.

### Pros

- Simple and focused.
- Modern AI assistant feel.
- Supports Phase 3 deterministic answer-source adapter.
- Leaves room for later RAG/source citation without redesigning the page.

### Cons

- If too minimal, it may hide useful resources.
- If too dense, it becomes a workbench and loses student friendliness.
- Requires careful empty/loading/fallback states later.

## Design Token Explanation For Product Manager

### Plain-Language Explanation

Design tokens are the product's shared visual rules.

Think of them like a school uniform standard:

- button blue is always the same blue;
- card corners have the same radius;
- page spacing follows the same rhythm;
- warning colors mean the same thing everywhere.

Without tokens, each page may look slightly different. One page may look like Ant Design, another like shadcn/ui, and the whole product will feel stitched together.

### What Need Creates This Requirement

We are using two UI sources:

- Ant Design for workbench pages.
- shadcn/ui/custom styling for homepage/student pages.

That gives us speed and beauty, but creates a risk: inconsistent visual language.

Tokens solve this by making both libraries follow the same visual source.

### Options

| Option | Meaning | Pros | Cons |
| --- | --- | --- | --- |
| No shared token | Style each page independently | Fast at first | Product feels inconsistent; hard to maintain |
| Ant Design theme only | Let Ant Design control most styling | Good for workbench | Homepage/student may become too admin-like |
| CSS variables as shared source | One visual rule set maps into Ant Design and shadcn/ui | Consistent, flexible, fits both libraries | Requires discipline during implementation |

Recommendation:

Use CSS variables as the shared source.

## Radius, Density, And Spacing Recommendation

### Radius

Use:

- `6px` for Ant Design workbench controls and tables.
- `8px` for homepage/student cards and larger panels.
- Avoid large 16px+ rounded cards as the default.

Reason:

- Ant Design default base radius is `6`.
- `8px` still feels modern without becoming playful or childish.

### Density

Use:

- Workbench: medium-high density.
- Homepage: spacious.
- Student: medium, readable, not admin-dense.

Reason:

- Counselor/admin users scan lists and operate repeatedly.
- Students need a clear, low-friction question-answer experience.

### Spacing

Use an 8px-based rhythm:

- 4px/8px for compact details.
- 12px/16px/24px for cards and forms.
- 32px/48px for page sections.

Reason:

- Atlassian and Carbon both support tokenized spacing systems based around small predictable increments.
- Predictable spacing makes UI faster to build and easier to review.

## SDAR-0004 Revision Recommendations

1. Keep the visual direction, but change wording to include “现代科技感”.
2. Add a product-manager-readable explanation of design tokens.
3. Mark homepage and student interaction descriptions as required design inputs.
4. Change radius guidance from “not over 8px” to:
   - workbench default 6px;
   - homepage/student large cards up to 8px;
   - larger radii require explicit design reason.
5. Mark mobile polish as Phase 8 technical debt.
6. Keep SDAR-0004 as `revision-required` until the product manager accepts the new explanations.

## Completion Verdict

This research is sufficient to revise SDAR-0004 because it:

- uses mature official design-system references;
- explains tokens in non-technical language;
- provides homepage and student user interaction descriptions;
- gives actionable style constraints for radius, density, and spacing.
