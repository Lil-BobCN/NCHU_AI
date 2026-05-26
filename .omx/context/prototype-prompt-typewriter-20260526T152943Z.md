# Prototype Prompt Typewriter

- Task statement: Move the left-to-right typewriter placeholder effect into the homepage static prototype prompt box shown in the screenshot.
- Desired outcome: `http://172.20.10.2:5188/.omx/prototypes/homepage-dark-hud-variants.html` shows the animated prompt text inside the hero consultation input area, not the React student chat page.
- Known facts/evidence:
  - Target file: `.omx/prototypes/homepage-dark-hud-variants.html`.
  - Target DOM: `.prompt-box [data-motion="prompt"]`, `.prompt-main input`, and the `hero.placeholder` i18n string.
  - The prototype already loads GSAP from CDN and has language/theme replay motion.
  - Previous React chatbox implementation is not the requested target.
- Constraints:
  - Use Karpathy guidelines: minimal, surgical changes to the static prototype.
  - Use Ralph workflow with verification and completion audit.
  - Preserve real input behavior: focus/input must hide the animated placeholder.
  - Preserve language switching: Chinese and English prompt text should animate from the current `hero.placeholder` translation.
- Unknowns/open questions:
  - Whether to loop forever or only run once. Choose a subtle loop after a short hold because the screenshot uses an empty prompt affordance.
- Likely codebase touchpoints:
  - `.omx/prototypes/homepage-dark-hud-variants.html`
