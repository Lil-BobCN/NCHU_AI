# Ralph Context: Homepage Scroll Replay Motion

Date: 2026-05-25T19:17:04Z
Workspace: `C:\Users\liuqi\Desktop\agentproject`

## Task Statement

Add repeated scroll reveal motion to `.omx/prototypes/homepage-dark-hud-variants.html`.

## Desired Outcome

- While scrolling down, page sections/cards/text animate into view.
- While scrolling back up, the same sections/cards/text also animate into view again.
- Off-screen reveal elements reset so they can replay on the next entry.
- Use GSAP as the primary animation engine and keep reduced-motion fallback intact.

## Current Evidence

- Existing GSAP reveal observer calls `revealObserver.unobserve(el)` after first reveal.
- Native fallback also unobserves after first reveal.
- This makes scroll reveals one-shot only.

## Constraints

- Do not redesign layout, colors, or copy.
- Keep the change surgical and limited to scroll reveal behavior.
- Use transform/opacity (`y`, `autoAlpha`) rather than layout-heavy properties.

## Verification Plan

- Parse inline scripts.
- Use browser automation to scroll down, then back up, and inspect reveal element opacity/transform states.
- Capture screenshots after down-scroll and up-scroll re-entry.
