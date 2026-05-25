# Homepage Story Back-Replay Removal

Date: 2026-05-25
Scope: `.omx/prototypes/homepage-dark-hud-variants.html`

## Change

Removed the story-section behavior that replayed the full section entrance when the user scrolled upward from the lower part of the page.

## Current Interaction Rule

- First entrance into the story section still plays header/card entrance animation.
- Clicking a left capability card still replays the corresponding right-side chapter animation.
- Scrolling upward through the story section no longer resets or replays the whole section.
- Leaving the story section upward past its top still resets the section, so a future downward re-entry can play normally.

## Verification

Playwright verified:

- Before first entrance: header/card opacity `0`.
- Early first entrance: header partially visible, cards still hidden.
- After first entrance: header/card opacity `1`.
- Scroll to bottom then wheel upward: header/card remain opacity `1`; no full-section reload.
- Clicking the fourth card activates card index `3` and panel index `3`.
- Console/page errors: none.

Screenshot artifact:

- `output/playwright/homepage-story-no-back-replay.png`
