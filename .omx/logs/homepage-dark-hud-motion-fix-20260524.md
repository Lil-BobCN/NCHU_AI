# Homepage Dark HUD Motion Fix

Date: 2026-05-24
Scope: `.omx/prototypes/homepage-dark-hud-variants.html`

## Problem

The prototype did not reliably communicate motion intent:

- Hero playback could feel delayed after reload.
- Reloading from a scrolled position could leave story cards visible before the user entered the story section.
- Story section content could scroll out of view while the chapter state was still changing.
- Returning upward needed to reset the story state so the animation could replay.
- The chapter progress line should stay in normal layout flow instead of sticking over content.

## Changes

- Added a reusable story reset hook used by hero replay and variant switching.
- Killed outstanding story tweens during reset so old animations cannot restore visible cards after reset.
- Reduced initial hero replay delay and kept reload at `scrollY = 0`.
- Made the desktop story stage sticky while keeping the chapter progress line non-sticky.
- Left the formal React homepage untouched; this change is prototype-only.

## Verification

Playwright checks were run against:

`http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html`

Evidence:

- Console warnings/errors: 0.
- Early hero sample starts with title/visual hidden, then reveals.
- Story entry animates header/cards/panel from hidden state.
- Story mid-scroll keeps the story stage visible in the viewport.
- Upward return to top hides story header/cards and resets progress width to `0px`.
- Reloading from a scrolled position returns to `scrollY = 0` and leaves story cards hidden until entry.

Screenshots:

- `output/playwright/homepage-dark-hud-verify4-story-mid.png`
- `output/playwright/homepage-dark-hud-verify3-no-preference-reload.png`
