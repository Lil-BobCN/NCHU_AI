# Deep Interview Context: Homepage Linear-like Left Text Motion

Task statement:
- Clarify the homepage left-side entrance motion before any code changes.

Desired outcome:
- Product manager wants the left hero text motion to feel like Linear's initial landing-page entrance motion.
- Current implementation appears static or the motion is not perceptible in the user's browser.
- No code changes should be made until the motion effect is clearly specified.

Known facts/evidence:
- Screenshot shows the current left hero content: eyebrow pill, H1 lines, paragraph, CTA buttons, and three metric cards.
- Current page uses React + TypeScript + Vite + Ant Design.
- Current homepage implementation has GSAP code, but the product manager did not perceive any visible animation.
- User explicitly wants relevant skills used: karpathy-guidelines, autoresearch, ui-ux-pro-max, gsap-react, gsap-core, gsap-plugins, gsap-timeline, gsap-performance.

Constraints:
- Do not edit code in this step.
- Clarify the intended effect through deep-interview first.
- Motion should reference Linear's initial entrance feel, not copy Linear branding.
- Existing SDAR-0007 constraints still apply unless superseded: no Three.js, no Lottie/Rive/Lenis, no real school assets, no login/API changes.

Unknowns/open questions:
- Whether the desired text entrance is whole-block fade/slide, line-by-line reveal, word/character mask reveal, or mixed stagger.
- Whether the navigation and right-side motion layer should animate before, during, or after left text.
- Whether repeat behavior is one-time on first page load only or also on route revisit/scroll reset.
- Whether current "no effect" is caused by animation being too subtle, too fast, already completed before visible load, browser reduced-motion preference, selector/scope issue, or Vite hot reload state.

Likely codebase touchpoints later:
- frontend/src/App.tsx
- frontend/src/App.css
- .omx/logs/development-path-structure-ai-counselor-demo.md
- .omx/logs/current-assets-progress-ai-counselor-demo-20260519.md

Prompt-safe initial-context summary status:
- not_needed
