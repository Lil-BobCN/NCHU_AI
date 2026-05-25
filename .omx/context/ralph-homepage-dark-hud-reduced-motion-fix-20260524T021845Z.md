# Ralph Context: Homepage Dark HUD Reduced Motion Fix

## Task Statement

Product manager opened `.omx/prototypes/homepage-dark-hud-variants.html` through `file:///...` and saw a nearly black page with status `A2 Aero Glass / reduced motion`.

## Desired Outcome

The review prototype must render visibly when the browser or OS prefers reduced motion. Reduced-motion mode should skip/flatten animation, not leave a dark overlay or hidden text.

## Known Facts / Evidence

- Screenshot shows the page is loaded, toolbar is visible, and status text says `reduced motion`.
- Current `playVariant()` reduced-motion branch sets `[data-boot-curtain]` to `autoAlpha: 1`.
- `.boot-curtain` is a full-screen fixed overlay with high z-index and dark gradient.
- Therefore reduced-motion mode leaves the boot overlay visible and dims the entire page.

## Constraints

- Fix only the prototype unless the product manager approves formal React changes.
- No new dependencies.
- Keep the fix surgical and reversible.
- Preserve normal animation mode.

## Unknowns / Open Questions

- The product manager may have OS/browser reduced motion enabled, or the in-app browser may emulate it.
- Need verify both normal mode and reduced-motion mode after the fix.

## Likely Touchpoints

- `.omx/prototypes/homepage-dark-hud-variants.html`
- `.omx/logs/current-assets-progress-ai-counselor-demo-20260519.md`
- `.omx/logs/development-path-structure-ai-counselor-demo.md`
