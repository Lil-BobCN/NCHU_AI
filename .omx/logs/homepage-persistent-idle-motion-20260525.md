# Homepage Persistent Idle Motion Repair

Date: 2026-05-25
Scope: `.omx/prototypes/homepage-dark-hud-variants.html`
Status: done

## Problem

The previous ambient effect was too weak and behaved like static styling. The product manager clarified that after the homepage entrance animation finishes, the selected hero areas should keep moving like a looping video.

## Change

- Added an explicit post-entrance idle state: `is-idle-playing`.
- Added a dedicated GSAP `idleTimeline` with cleanup through `stopIdleMotion()`.
- Started idle motion from the hero entrance `onComplete`.
- Added persistent visible motion for CTA buttons, sequence chips, signal cards, visual panel, scan sweep, wing object, trails, radar, nodes, route paths, HUD lines, HUD logs, and HUD metrics.
- Added CSS loop effects for glints, panel scans, video scan line, and soft aura.

## Verification

- Script syntax check: all inline scripts parsed successfully.
- Browser console check through Playwright CLI: 0 errors, 0 warnings.
- Runtime state check: active hero had `data-idle-motion="running"` and class `is-idle-playing`.
- Status text check: `常驻动效运行中：A1 黑曜指挥舱 / A 呼吸光`.
- Motion sampling:
  - Flight transform changed from `matrix(0.93358, -0.358368, 0.358368, 0.93358, 0, 0)` to `matrix(0.990887, -0.331602, 0.331602, 0.990887, 8.9896, -6.9919)`.
  - CTA transform sampled as `matrix(1.012, 0, 0, 1.012, 0, -4)`.
  - HUD line transform sampled as `matrix(0.959, 0, 0, 1, 0, 0)`.
- Horizontal overflow check: `0`.
- Screenshot evidence: `output/playwright/homepage-persistent-idle-after.png`.

## Notes

This remains prototype-only work. The formal React homepage was not changed in this repair.
