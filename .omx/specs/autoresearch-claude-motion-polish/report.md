# Autoresearch Report: Claude Motion Polish

Date: 2026-05-25
Target: `.omx/prototypes/homepage-dark-hud-variants.html`

## Sources

- Project product guidance: `PRODUCT.md`
- Project design guidance: `DESIGN.md`
- Reference workflow guide: `docs/design/awesome-design-md.md`
- Official Claude product overview inspected on 2026-05-25: `https://claude.com/product/overview`

## Project Guidance Used

- `PRODUCT.md` sets the product tone as calm, trustworthy, work-focused, and Chinese-first.
- `DESIGN.md` says motion should be subtle and functional, clarifying state changes rather than decorating the page.
- `docs/design/awesome-design-md.md` says reference styles should be adapted as tokens and interaction patterns, not copied as brand identity.

## Claude Motion Findings

Official page inspection found:

- Webflow page uses GSAP 3.15 plus ScrollTrigger, SplitText, TextPlugin, Flip, Draggable, and InertiaPlugin.
- Page includes flicker prevention for global GSAP animations using `data-prevent-flicker`.
- Hero heading is pre-split with SplitText and animated word-by-word from `autoAlpha: 0`.
- Hero body text, CTA, and visual enter with small `y` movement, `autoAlpha`, `duration: 0.75`, and `power2.out`.
- Navigation and secondary nav enter from `autoAlpha: 0, y: -20`.
- Scroll headings use SplitText and ScrollTrigger; card groups enter from `autoAlpha: 0, y: 20` with stagger.

## Implementation Translation

Because this prototype should not add dependencies only to imitate Claude, the implementation keeps the existing GSAP CDN and adds a small local tokenizer instead of importing SplitText.

Changes made:

- Added runtime text tokenization for hero title and section headings.
- Changed hero title from block-level reveal to token-level reveal.
- Rebuilt the hero entrance timeline around Claude-like timing: nav, product bar, eyebrow, heading tokens, copy, visual, prompt, SVG lines, chips, and latest card.
- Reworked section reveal logic so headings reveal by tokens while cards/buttons reveal by grouped child elements.
- Kept reduced-motion fallback by immediately revealing `.motion-token` content.
- Stayed on transform/opacity-heavy animation with light clip-path reveal.

## Verification Artifacts

- Official reference screenshots:
  - `output/playwright/claude-motion-20260526/top-t300.png`
  - `output/playwright/claude-motion-20260526/top-t1800.png`
- Prototype screenshots:
  - `output/playwright/homepage-claude-motion-polish-t0450-v2.png`
  - `output/playwright/homepage-claude-motion-polish-t1900-v2.png`
  - `output/playwright/homepage-claude-motion-polish-platform.png`

## Verification Result

- Local prototype URL returned HTTP `200`.
- Playwright screenshots show the hero beginning in a partially revealed state around `450ms` and resolving to the full hero by `1900ms`.
- Platform section loads and displays the updated section reveal target.

## Limits

- Exact Claude proprietary motion timing and SplitText implementation were not copied.
- Playwright Test runner was not available as `@playwright/test` or `playwright/test` in the current transient CLI environment, so validation used Playwright CLI screenshots and HTTP smoke checks instead of a formal test spec.

