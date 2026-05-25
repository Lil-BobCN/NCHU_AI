# Autoresearch Report: Homepage Light Claude Tuning

Date: 2026-05-25
Status: completed for implementation

## Mission

Reference the current Claude product overview page and project design documents to tune the NCHU AI homepage prototype Light mode.

## Sources

- Claude official product overview: `https://claude.com/product/overview`
- `PRODUCT.md`
- `DESIGN.md`
- `docs/design/awesome-design-md.md`

## Findings

- Claude Light page uses warm neutral background and black/gray text. Browser sample:
  - body background: `rgb(250, 249, 245)`.
  - body text: `rgb(20, 20, 19)`.
  - H1 color: `rgb(20, 20, 19)`.
- Claude current product page font samples:
  - body: `"Anthropic Sans", Arial, sans-serif`.
  - H1: `"Anthropic Serif", Georgia, sans-serif`.
  - H1 weight: `500`.
  - H1 size: `60px`.
- Project `DESIGN.md` asks for clean sans-serif UI typography and Chinese/mixed labels that fit containers. Because Claude's proprietary fonts are not available and the Chinese Songti-style fallback felt too classical for this product, the prototype uses a clean system sans-serif stack for headings and body.
- Claude keeps accent color separate from the main text system. In our adaptation:
  - text should move to warm black/gray;
  - NCHU visual accents and abstract graphics can remain blue.
- Claude top actions are closer to rectangular buttons with small rounded corners, not large pills. The theme toggle may remain pill-shaped because it is a mode switch rather than a primary CTA.
- Claude first/second screen transition uses subtle warm tonal bands, not a flat same-color page.
- Claude prompt input is compact and quiet, with the primary CTA embedded as a small rectangular button.

## Implementation Decisions

- Light token split:
  - text: warm near-black and gray;
  - brand/accent: blue retained for symbols, CTAs, SVG strokes, and visual graphics.
- Reduce hero and section display type size to leave more space.
- Replace the previous Songti/Georgia heading stack with system Chinese/English sans-serif tokens.
- Shift centered nav links right by changing the nav grid proportions and link justification.
- Make CTA/action buttons rectangular with `6px` radius; keep the Light/Dark toggle pill.
- Force the hero title into two intentional lines so mobile does not break the final Chinese character onto an orphan line.
- Add Light-only section background bands and a thin transition veil at the second section.
- Add scroll reveal clip/opacity motion using existing GSAP fallback infrastructure.

## Evidence Artifacts

- `output/playwright/claude-reference/claude-overview-current-20260525-top.png`
- `output/playwright/claude-reference/claude-overview-current-20260525-second.png`
- `output/playwright/homepage-claude-official-rebuild/light-tuned-top-v3.png`
- `output/playwright/homepage-claude-official-rebuild/light-tuned-platform-v3.png`
- `output/playwright/homepage-claude-official-rebuild/light-tuned-mobile-v3.png`
