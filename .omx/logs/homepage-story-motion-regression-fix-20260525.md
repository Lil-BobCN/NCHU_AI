# Homepage Story Motion Regression Fix

Date: 2026-05-25
Scope: `.omx/prototypes/homepage-dark-hud-variants.html`

## User Feedback

- Story section header text animation disappeared.
- Four capability cards had no first-load entrance animation.
- When scrolling upward back through the story section, the whole section should reload/replay its entrance motion.
- Keep the newer interaction rule: click a left capability card to replay the corresponding right-side chapter panel. Do not return to scroll-driven chapter switching.

## Fix

- Restored hidden initial state for story header, cards, card internals, and right-side chapter panels.
- Reintroduced a story-section ScrollTrigger only for entrance playback.
- Added a separate bottom-zone ScrollTrigger so scrolling down near the story bottom arms replay, then scrolling upward resets and replays the story entrance.
- Prevented first active-card selection from overwriting the card entrance tween.

## Verification

Playwright verified against `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html`.

- Before entering story: header opacity `0`, first card opacity `0`.
- Early story entry: header partially animating, all four cards still hidden.
- After entrance: header opacity `1`, four cards opacity `1`, first chapter active.
- Clicking third card: left active card index `2`, right panel index `2`.
- After scrolling to page bottom and back upward: story resets to hidden, then replays to visible.
- Console/page errors: none.

Screenshot artifact:

- `output/playwright/homepage-story-motion-restored-2.png`

## Notes

This is prototype-only work. Formal React homepage files were not changed.
