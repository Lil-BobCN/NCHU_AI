# Ralph Context: Homepage Prototype Toolbar And Ambient Motion Repair

Timestamp: 2026-05-25T00:00:00Z
Scope: `.omx/prototypes/homepage-dark-hud-variants.html`

## Task Statement

Fix the homepage prototype after user reported:

1. The top review/debug toolbar layout is broken.
2. The A/B/C ambient motion options are not clearly perceptible.
3. The whole page became English and should return to Chinese.

## Desired Outcome

- Review toolbar is compact and does not overlap or stretch awkwardly.
- A/B/C options are visibly different and active across the page after hero entrance finishes.
- Main content is Chinese again.
- Prototype remains review-only; no formal React page changes.
- Browser verification confirms no console errors and no horizontal overflow.

## Known Evidence

- Screenshot shows the toolbar compressed into one line with text/button crowding.
- Previous repair inserted a clean DOM with ASCII/English text to avoid corrupted static HTML; this solved bad `?/span>` text but caused the language regression.
- Current implementation uses `body[data-ambient-style]` and `.is-ambient-ready` to scope effects.

## Constraints

- Use frontend-related skills.
- User explicitly invoked karpathy-guidelines and ralph.
- Keep changes surgical to the prototype.
- Avoid reintroducing static Chinese text in raw HTML body if encoding corruption risk remains; use JS Unicode escapes or programmatic text insertion if needed.

## Likely Touchpoints

- `.review-toolbar`, `.toolbar-title`, `.toolbar-controls`, `.playback` CSS.
- `renderCleanPrototype()` HTML template.
- ambient CSS keyframes and selectors.
- Playwright verification script.

## Success Criteria

- Toolbar visible as compact review controls without crowding/intercept issues at 1440px and mobile width.
- Body text includes Chinese labels and does not include broken visible closing tags.
- A/B/C computed animation names differ and screenshots are generated.
- No console errors.
- No horizontal overflow.
