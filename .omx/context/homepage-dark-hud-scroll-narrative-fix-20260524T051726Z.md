# Ralph Context: Homepage Dark HUD Scroll Narrative Fix

## Task Statement

Fix the review prototype at `.omx/prototypes/homepage-dark-hud-variants.html` so the homepage and scroll narrative feel like real motion, not just a static page that shifts position.

## Desired Outcome

- First screen should play a visible entrance sequence on load.
- Scroll-down chapters should have stronger entry motion and better chapter transitions.
- Scroll-up / return-to-top should replay or reset the relevant animation states.
- The horizontal progress line in the story section should stay fixed in its starting position and not overlap content while scrolling.
- Keep the fix inside the prototype unless the product manager asks for formal React changes.

## Known Facts / Evidence

- Current page loads visibly but in the user's browser the top status shows `reduced motion`, so the current reduced-motion path can appear static.
- `showReducedMotionVariant()` currently sets most elements directly to visible state with no entrance sequence.
- The story section uses `ScrollTrigger.batch(..., { once: true })`, which means cards only animate in once.
- The story section also uses a single `ScrollTrigger.create(... onUpdate ...)` that only maps progress to active index and chapter-screen offset.
- `.chapter-progress` is `position: sticky`, which can make the line feel like it moves with the page and overlap content.

## Constraints

- Keep changes surgical and reversible.
- Do not modify the formal React homepage unless explicitly approved.
- Preserve performance and use GSAP-friendly transform/opacity animation.
- Respect the existing dark cinematic style.

## Unknowns / Open Questions

- Whether the browser is actually running with system `prefers-reduced-motion`, or whether the prototype should override it more visibly for review purposes.
- How much motion should remain in reduced-motion mode versus full-motion mode.
- Whether the story section should animate by progress scrubbing or by discrete chapter enter/leave states.

## Likely Touchpoints

- `.omx/prototypes/homepage-dark-hud-variants.html`
- `frontend/src/App.tsx` and `frontend/src/App.css` only if the product manager later approves formal homepage changes
- `.omx/logs/development-path-structure-ai-counselor-demo.md`
- `.omx/logs/current-assets-progress-ai-counselor-demo-20260519.md`
