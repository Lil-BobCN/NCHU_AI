# Theme Switch Alignment Acceptance

Date: 2026-05-26

## Scope

- File changed: `.omx/prototypes/homepage-dark-hud-variants.html`
- Task: Center the theme switch icon pattern in the prototype navigation switch.
- Non-goals: No React implementation changes, no theme palette changes, no broader layout refactor.

## Change

- Kept the Uiverse-inspired filled moon shape.
- Adjusted the moon SVG viewBox from `0 0 24 24` to `-2.4 0 24 24` so the visible crescent is optically centered inside the circular dark-state knob.
- Preserved existing theme colors: light state remains blue, dark state remains brown.

## Verification

- Static page request: `200` from `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html`.
- Static server confirmed on port `5188`.
- `git diff --check -- .omx/prototypes/homepage-dark-hud-variants.html` passed.
- Desktop screenshots generated with Chrome headless reduced-motion mode:
  - Light crop: `/tmp/nchu-theme-switch-light-after.png`
  - Dark crop: `/tmp/nchu-theme-switch-dark-after.png`
- Additional 640px dark-state screenshot generated:
  - `/tmp/nchu-theme-dark-640-after.png`

Opened preview URL:

`http://172.20.10.2:5188/.omx/prototypes/homepage-dark-hud-variants.html`
