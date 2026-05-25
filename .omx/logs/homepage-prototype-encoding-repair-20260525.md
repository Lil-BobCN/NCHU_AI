# Homepage Prototype Encoding Repair

Date: 2026-05-25
Scope: `.omx/prototypes/homepage-dark-hud-variants.html`
Status: repaired

## Problem

The prototype rendered broken visible text such as `?/span>`, `?/h3>`, and corrupted Chinese strings. The visual result looked like overlapping layout and malformed headings.

## Root Cause

The static body HTML in the prototype had already been damaged by an encoding/tag corruption issue. Browser parsing turned malformed closing tags into visible text and distorted the DOM structure. The ambient motion CSS was not the primary cause.

## Fix

Added `renderCleanPrototype()` before GSAP initialization. It clears `document.body` and rebuilds the review prototype DOM with clean ASCII text, preserving the existing CSS class names and `data-*` hooks used by the animation code.

Also repaired corrupted playback status strings to stable ASCII labels.

## Verification

Playwright verification against:
`http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html#features`

Results:

- Console errors: none.
- Visible broken tags: false.
- Hero variants: 3.
- Story cards: 4.
- Chapter panels: 4.
- Ambient A: `ambient-micro-float`, `ambient-aura` active.
- Ambient B: `ambient-edge-sweep` active.
- Ambient C: `ambient-signal-flicker` active.
- Story click test: card `03 / ADMIN` activates panel `CHAPTER 03 / ADMIN`.
- Desktop overflow: false.

Screenshots:

- `output/playwright/homepage-clean-top.png`
- `output/playwright/homepage-clean-features.png`

## Note

This is a prototype repair only. It does not modify the formal React homepage.
