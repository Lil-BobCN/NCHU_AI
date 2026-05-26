# Prototype Prompt Questions Rotation

- Task statement: Enhance the homepage prototype prompt-box typewriter to rotate through 10 service-goal-aligned questions, slow the typing speed, and keep the input empty until the prompt field finishes loading.
- Desired outcome: The target static prototype at `http://172.20.10.2:5188/.omx/prototypes/homepage-dark-hud-variants.html` shows no prompt text before the prompt container enters, then slowly types and rotates through 10 NCHU AI Counselor questions.
- Known facts/evidence:
  - Target file: `.omx/prototypes/homepage-dark-hud-variants.html`.
  - Existing typewriter code uses `playPromptTypewriter`, `promptTypewriterTimeline`, `promptCursorTween`, and starts after the prompt intro in GSAP/native paths.
  - Design guidance: `PRODUCT.md`, `DESIGN.md`, and `docs/design/awesome-design-md.md` call for calm, trustworthy, Chinese-first institutional support UI.
- Constraints:
  - Use GSAP as the main animation driver.
  - Follow Karpathy guidelines: surgical changes, avoid unrelated refactors.
  - Ralph workflow requires context snapshot, verification, scoped deslop scan, and completion audit.
  - Preserve focus/input behavior: animation hides when the user interacts with the real input.
- Unknowns/open questions:
  - User included trailing `23:` without clear meaning; no action is inferred from it.
- Likely codebase touchpoints:
  - `.omx/prototypes/homepage-dark-hud-variants.html`
