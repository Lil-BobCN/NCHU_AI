# Homepage Toolbar Ambient Chinese Repair

Date: 2026-05-25
Scope: `.omx/prototypes/homepage-dark-hud-variants.html`
Status: done

## Problem

Product review found three issues in the dark HUD prototype:

- The top review/debug toolbar was crowded and hard to read.
- A/B/C ambient motion choices were not perceptible enough.
- Runtime prototype content had regressed to English.

## Fix

- Reworked the review toolbar into grouped controls: homepage variant, playback, ambient motion, and playback status.
- Restored the runtime-visible UI copy to Chinese through a post-render repair layer, avoiding direct reliance on the older corrupted static body markup.
- Strengthened ambient motion:
  - A: breathing glow and subtle floating on buttons/cards.
  - B: scanning edge sweep on buttons/cards/panels.
  - C: signal flicker on buttons/cards/panels.
- Kept the change scoped to the review prototype. No formal React homepage change was made.

## Verification

Playwright checked `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html`.

- Console/page errors: 0.
- Horizontal overflow: 0 on desktop and mobile.
- Runtime DOM clean marker: `cleanReady=true`.
- Visible runtime text is Chinese; old English review labels are not visible.
- Broken visible tag pattern `?/span>` etc.: false.
- Toolbar desktop: 1380x66 at 1440px viewport.
- Toolbar mobile: 366x255 at 390px viewport.
- Ambient A active state: `A 呼吸光`, `ambient-micro-float`, `ambient-aura`.
- Ambient B active state: `B 扫描边`, `ambient-edge-sweep`, `ambient-panel-sweep`.
- Ambient C active state: `C 信号闪`, `ambient-signal-flicker`.

Screenshots:

- `output/playwright/homepage-toolbar-cn-a.png`
- `output/playwright/homepage-toolbar-cn-b.png`
- `output/playwright/homepage-toolbar-cn-c.png`
- `output/playwright/homepage-toolbar-cn-mobile.png`

## Notes

The physical HTML file still contains an older corrupted static body block before the script. Runtime immediately replaces the body via `renderCleanPrototype()` and then applies the Chinese repair layer. Future cleanup should remove the stale static block in a dedicated cleanup pass, because deleting it inside this repair could widen the diff.
