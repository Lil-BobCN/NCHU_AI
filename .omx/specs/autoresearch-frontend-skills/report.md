# Autoresearch Report: Frontend Skills Selection

Date: 2026-05-19
Status: completed

## Summary

Installed seven frontend-adjacent skills for the next design iteration:

1. `shadcn-component-discovery`
2. `shadcn-component-review`
3. `frontend-design`
4. `ui-ux-pro-max`
5. `playwright`
6. `screenshot`
7. `vercel-react-best-practices` (`react-best-practices` install directory)

The existing project-local `shadcn` skill remains installed and is still the primary shadcn/ui project-operation skill.

## Installed Skills

| Skill | Source | Why installed | Helps with |
| --- | --- | --- | --- |
| `shadcn-component-discovery` | `mattbx/shadcn-skills` | Finds shadcn-compatible components and registries before custom-building UI. | Selecting login pages, dashboards, cards, tables, dialogs, AI UI blocks. |
| `shadcn-component-review` | `mattbx/shadcn-skills` | Reviews custom components against shadcn patterns, token usage, spacing, accessibility, and composition. | Post-build review after page/component edits. |
| `frontend-design` | `vipulgupta2048/codex-skills` | Focused on avoiding generic AI-looking frontend output and improving production-grade visual direction. | Turning screenshots and style references into a coherent homepage/login/workspace look. |
| `ui-ux-pro-max` | `jMerta/codex-skills` | Provides searchable UI/UX style, palette, typography, layout, landing, chart, and React guidance. | Teaching design vocabulary, choosing style directions, refining pages. |
| `playwright` | `openai/skills` | Official Codex skill for browser automation and UI-flow debugging. | Verifying homepage/login/role flow, screenshots, responsive checks. |
| `screenshot` | `openai/skills` | Official Codex skill for desktop/system screenshots when browser/tool-specific capture is insufficient. | Capturing local visual evidence or user-provided page comparisons. |
| `vercel-react-best-practices` | `vercel-labs/agent-skills` | Adds React/Next.js performance rules maintained by Vercel Engineering. | Reviewing React component structure, re-render risks, bundle/import choices, client data fetching, and performance-sensitive code. Next.js-specific guidance is applied selectively because the current app is React + Vite. |

## Considered But Not Installed

| Candidate | Reason not installed now |
| --- | --- |
| OpenAI `figma`, `figma-use`, `figma-implement-design` | Current workflow is website screenshots and reference-site discussion, not Figma URLs or Figma MCP. Install later if product manager introduces Figma files. |
| `google-labs-code/stitch-skills` | High star count but tied to Stitch MCP workflow; not currently part of this project. |
| Large "awesome skills" repos | Useful for browsing, but not direct Codex frontend execution skills. |
| Broad third-party skill packs | Too much unrelated scope for the current frontend visual iteration. |

## Evidence

- `openai/skills` is the official Codex skills catalog and had about 19k GitHub stars at research time.
- `shadcn/ui` had about 114k GitHub stars and remains the strongest ecosystem anchor for shadcn-compatible UI.
- `mattbx/shadcn-skills` is low-star but directly targets shadcn component discovery/review and complements the existing shadcn skill.
- `jMerta/codex-skills` has a dedicated `ui-ux-pro-max` skill with data/search scripts for design guidance.
- `vipulgupta2048/codex-skills` has a dedicated `frontend-design` skill explicitly aimed at avoiding low-quality generic frontend output.
- `vercel-labs/agent-skills` provides `skills/react-best-practices`, whose metadata names the installed skill `vercel-react-best-practices` and focuses on React/Next.js performance practices.

## Installation Paths

Installed into user-level Codex skills:

```text
C:\Users\liuqi\.codex\skills\playwright
C:\Users\liuqi\.codex\skills\screenshot
C:\Users\liuqi\.codex\skills\shadcn-component-discovery
C:\Users\liuqi\.codex\skills\shadcn-component-review
C:\Users\liuqi\.codex\skills\frontend-design
C:\Users\liuqi\.codex\skills\ui-ux-pro-max
C:\Users\liuqi\.codex\skills\react-best-practices
```

## Operational Note

Codex normally discovers newly installed skills at session startup. Restart Codex before expecting these skills to appear in the automatic skill list. In the current session, the files are installed and can still be read manually if needed.

## Recommended Use In This Project

Next frontend iteration should use this order:

1. `frontend-design` / `ui-ux-pro-max`: turn user screenshots into style vocabulary and design direction.
2. `shadcn-component-discovery`: search existing shadcn-compatible blocks/components before custom-building.
3. Existing `shadcn`: apply shadcn/ui project operations where relevant.
4. `vercel-react-best-practices`: check React implementation quality, re-render behavior, bundle/import patterns, and performance-sensitive code.
5. `shadcn-component-review`: review the final components for token, spacing, accessibility, and composition quality.
6. `playwright` / existing visual QA tools: verify flows and capture evidence.
7. `screenshot`: capture OS-level screenshots only when browser-specific capture is insufficient.

## 2026-05-22 Animation Skills Addendum

Product manager approved adding animation-focused skills before the next homepage wing-hero prototype revision.

Installed into user-level Codex skills:

```text
C:\Users\liuqi\.codex\skills\gsap-core
C:\Users\liuqi\.codex\skills\gsap-timeline
C:\Users\liuqi\.codex\skills\gsap-plugins
C:\Users\liuqi\.codex\skills\gsap-react
C:\Users\liuqi\.codex\skills\gsap-performance
C:\Users\liuqi\.codex\skills\svg-animations
```

How they should be used:

| Skill | Use in this project |
| --- | --- |
| `svg-animations` | Rebuild the NCHU wing symbol as a cleaner SVG composition, with path/group structure suitable for staged motion. |
| `gsap-core` | Control basic transform, opacity, easing, and entrance motion for the wing components. |
| `gsap-timeline` | Sequence the required motion: component fly-in, final assembly lock, then unified idle float. |
| `gsap-react` | Later React implementation pattern if the accepted prototype is ported into `frontend/src`. |
| `gsap-plugins` | Evaluate optional plugin needs only if core GSAP is insufficient; do not add visual complexity by default. |
| `gsap-performance` | Keep the animation transform-based, avoid layout thrash, and respect reduced-motion constraints. |

Operational note: Codex normally discovers newly installed skills at session startup. Restart Codex to pick up new skills automatically; in the current session the files are installed and can still be read manually.
