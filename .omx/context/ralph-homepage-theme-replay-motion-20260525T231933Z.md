# Ralph Context: Homepage Theme Replay Motion

Date: 2026-05-25T23:19:33Z
Workspace: `/Users/Admin/学校项目/NCHU_AI`

## Task Statement

Modify `.omx/prototypes/homepage-dark-hud-variants.html` so the page animations replay whenever the light/dark theme switch changes.

## Desired Outcome

- Toggling between light and dark updates `body[data-theme]` as before.
- After a real theme change, the top/hero intro animation replays.
- Current in-viewport reveal animations replay after the theme change.
- Off-screen reveal items are reset so they can animate again when they re-enter the viewport.
- Reduced-motion users still see the page immediately without forced motion.

## Known Facts / Evidence

- The page has a checkbox theme switch with id `homepage-theme-toggle`.
- GSAP is the primary animation path.
- The page also has a native `Element.animate` fallback path.
- Scroll reveal replay logic already exists and includes a special `#platform` page-gated replay scope.
- The file already has user/worktree edits that replaced the old text theme toggle with the current switch UI.

## Constraints

- Keep the change surgical and limited to `.omx/prototypes/homepage-dark-hud-variants.html`.
- Do not redesign layout, copy, colors, or the existing switch UI.
- Preserve existing GSAP and native fallback behavior.
- Do not overwrite unrelated user edits in the dirty worktree.

## Unknowns / Open Questions

- "整个页面的动画" could imply replaying all animation systems, not scrolling the user back to the top. The conservative implementation should replay visible animation and reset off-screen reveals without changing scroll position.

## Likely Codebase Touchpoints

- `.omx/prototypes/homepage-dark-hud-variants.html`
- Inline script section around theme switch setup and animation setup.

## Verification Plan

- Parse the HTML/inline JavaScript after editing.
- Open the static prototype in a browser automation session.
- Confirm theme toggling changes `body[data-theme]`.
- Confirm a hero token is reset/replayed after toggle.
- Confirm an in-viewport reveal item is reset/replayed after toggle.
