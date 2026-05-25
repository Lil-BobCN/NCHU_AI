# Homepage Persistent Idle Motion Visible Pass

Date: 2026-05-25
Scope: `.omx/prototypes/homepage-dark-hud-variants.html`
Status: done

## Problem

The previous persistent idle motion existed in code, but it was still hard to perceive. The main root cause was that later `body[data-ambient-style]` rules also assigned `animation` to the same hero controls and visually overrode the `is-idle-playing` rules. The GSAP idle loop was also too subtle for the product manager's "looping video" expectation.

## Change

- Added a final `is-active.is-idle-playing` override layer so the idle state wins over A/B/C ambient debug styles.
- Strengthened the status pill, status dot, capability chips, CTA buttons, role cards, right HUD panel, radar, route lines, flight object, and HUD lines.
- Added stronger visible keyframes for glowing borders, hot sweep scans, panel aura, and status-dot pulse.
- Increased GSAP idle-loop movement amplitude while staying on transform/opacity-heavy animation for performance.

## Skills Used

- `frontend-design`
- `ui-ux-pro-max`
- `gsap-core`
- `gsap-timeline`
- `gsap-performance`
- `playwright`

## Verification

- Inline script syntax check: `4/4 scripts ok`.
- HTTP check: `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html` returned `200`.
- Browser console check: `0 errors / 0 warnings`.
- Runtime state: active hero class was `hero-variant is-active is-ambient-ready is-idle-playing`.
- Runtime state: `data-idle-motion="running"` and `window.__nchuIdleMotion.active=true`.
- Motion sampling over 0.85s showed visible transform/box-shadow changes in the status dot, CTA, chip, role card, visual frame, flight object, HUD panel, and HUD line.
- Screenshot evidence: `output/playwright/homepage-hero-idle-strong-20260525.png`.

## Notes

This remains prototype-only work. The formal React homepage and backend were not changed.
