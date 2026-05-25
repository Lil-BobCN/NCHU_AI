# Ralph Context: Platform Replay Gate

Date: 2026-05-25T19:47:55Z
Workspace: `C:\Users\liuqi\Desktop\agentproject`

## Task Statement

Adjust the scroll replay behavior for the screenshot section in `.omx/prototypes/homepage-dark-hud-variants.html`.

## Desired Outcome

- The screenshot section is `#platform`:
  - heading/actions;
  - four feature rows;
  - right network card.
- This section should not reset/replay during small internal scroll movement.
- It should only be reset after the page has fully returned to the previous page above it.
- After that full previous-page transition, scrolling down into `#platform` should replay its reveal motion.

## Constraints

- Keep current design and copy unchanged.
- Keep global up/down replay behavior for other sections.
- Use GSAP transform/opacity logic and avoid layout-heavy animation.

## Verification Plan

- Parse inline scripts.
- Use browser automation:
  - play `#platform`;
  - scroll partially away inside/below and confirm it stays active;
  - scroll fully above the section and confirm it resets;
  - scroll down again and confirm it replays from below.
