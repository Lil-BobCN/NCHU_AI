# Ralph Context: Homepage Top-Down Motion Repair

Date: 2026-05-25T18:56:55Z
Workspace: `C:\Users\liuqi\Desktop\agentproject`

## Task Statement

Repair `.omx/prototypes/homepage-dark-hud-variants.html` entrance motion. The user reports that the page appears fully loaded first, then elements animate one by one too quickly.

## Desired Outcome

- Initial viewport should not show the completed page before animation.
- First screen should enter progressively from top to bottom.
- Motion should be slower, coherent, and GSAP-driven.
- Reduced-motion users should still see immediate content.

## Constraints

- Keep the change focused to the prototype and supporting log/context files.
- Use local GSAP motion guidance, with Karpathy Guidelines for minimal changes.
- Use Ralph-style verify-and-record workflow.
- Do not redesign the page or change copy/content.

## Likely Touchpoints

- `.omx/prototypes/homepage-dark-hud-variants.html`
- `.omx/logs/homepage-claude-official-rebuild-20260525.md`

## Verification Plan

- Check inline JavaScript parses.
- Capture browser screenshots at early, mid, and resolved timings.
- Confirm early frame is not the fully completed hero.
