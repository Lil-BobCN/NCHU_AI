# Ralph Context: Homepage Persistent Idle Motion

Timestamp: 2026-05-25T04:45:00Z
Scope: `.omx/prototypes/homepage-dark-hud-variants.html`

## Task Statement

The product manager clarified that "ambient motion" means persistent idle animation after the homepage entrance animation completes. The page should not feel frozen after load. The selected hero buttons/cards/HUD areas should keep moving like a looping video.

## Desired Outcome

- After the hero entrance finishes, visible persistent motion continues on:
  - CTA buttons.
  - left-side small sequence/card elements.
  - right-side visual/HUD/radar/flight elements.
- This must be obvious without clicking A/B/C.
- A/B/C can remain as review modes, but the default should already show persistent motion.
- Keep changes scoped to the prototype; do not change the formal React app.

## Constraints

- Use Ralph and Karpathy-guidelines.
- Use frontend/animation skill guidance.
- Keep the patch surgical.
- Prefer transform/opacity and CSS variables over layout animation.

## Likely Touchpoints

- CSS keyframes and `.is-ambient-ready` selectors.
- `playVariant()` completion handler.
- Potential GSAP idle timeline after entrance animation.

## Verification

- Browser opens without console/page errors.
- After entrance completion, computed animations are active on CTA/card/HUD/radar/flight elements.
- Screenshots show no layout overflow.
