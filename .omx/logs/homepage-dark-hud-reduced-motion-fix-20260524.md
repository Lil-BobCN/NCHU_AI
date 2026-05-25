# Homepage Dark HUD Reduced-Motion Fix

Date: 2026-05-24
Scope: `.omx/prototypes/homepage-dark-hud-variants.html`
Status: verified

## Problem

Product-manager browser review showed the dark HUD prototype opening as a dimmed/covered page.

## Cause

The current browser environment reports `prefers-reduced-motion: reduce`. In that branch the prototype skipped the GSAP entrance timeline, but the full-screen boot curtain remained visible. The result looked like the page had no usable content or motion.

## Fix

- Added a reduced-motion display path that immediately reveals the active variant's nav, hero text, CTA, visual HUD, and scroll preview elements.
- Explicitly hides `[data-boot-curtain]` with `display: none`, `autoAlpha: 0`, `scaleY: 0`, and `pointerEvents: none`.
- Keeps atmosphere and sweep-only decorative motion hidden under reduced-motion mode.

## Verification

Playwright checked:

- `file:///C:/Users/liuqi/Desktop/agentproject/.omx/prototypes/homepage-dark-hud-variants.html` with reduced motion.
- `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html` with reduced motion.
- `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html` with normal motion.

Results:

- Console errors: `0`
- Console warnings: `0`
- Reduced-motion curtain state: `display: none`, `opacity: 0`, `visibility: hidden`
- Reduced-motion title opacity: `1`
- Reduced-motion nav opacity: `1`
- Normal-motion branch still completes with curtain opacity `0` and status `完成：A1 Obsidian Command`

Screenshots:

- `output/playwright/homepage-dark-hud-file-reduce-fixed-v2.png`
- `output/playwright/homepage-dark-hud-http-reduce-fixed-v2.png`
- `output/playwright/homepage-dark-hud-http-normal-fixed-v2.png`

## Boundary

This task only fixed the review prototype. It did not modify the formal React homepage, backend API, data contract, schema, RAG/provider path, or production login flow.
