# Homepage Claude-Style Restyle Snapshot

Timestamp: 2026-05-25T02:01:35Z

## Task Statement

Restyle `.omx/prototypes/homepage-dark-hud-variants.html` using `PRODUCT.md`, `DESIGN.md`, and the Claude-style reference from `awesome-design-md`.

## Desired Outcome

- Keep the AI counselor system in a Chinese-first institutional product tone.
- Adapt Claude-like qualities: calm editorial hierarchy, warm readable surface, precise navigation, restrained motion, and product preview clarity.
- Avoid copying Claude's orange/coral identity; use the project-compatible blue-green, graphite, and aviation-tech palette instead.
- Keep the prototype review controls, first-screen motion, and click-to-preview feature section usable.

## Known Facts / Evidence

- `PRODUCT.md` defines NCHU AI Counselor as a student support and counselor workflow product.
- `DESIGN.md` requires Chinese-first labels, operational clarity, restrained polish, visible state, and no external brand identity copying.
- `docs/design/awesome-design-md.md` allows fetching the selected upstream reference when a specific visual direction is requested.
- Current target HTML contains an old garbled static body and a later script-rendered body, causing inconsistent visible output and text encoding artifacts.

## Constraints

- Scope is prototype-only unless the user asks to modify the formal React homepage.
- Use `impeccable`, `karpathy-guidelines`, and `ralph`.
- Avoid new dependencies.
- Preserve GSAP-based motion, but make it functional and readable rather than HUD-heavy.
- Do not use Claude orange as the accent.

## Unknowns / Open Questions

- Exact final brand palette is not locked beyond avoiding orange; choose a conservative non-orange direction from the existing project color family.
- The final hero video/wing animation asset remains future technical debt.

## Likely Touchpoints

- `.omx/prototypes/homepage-dark-hud-variants.html`
- `.omx/logs/`
- `output/playwright/` for verification screenshots if browser checks succeed.
