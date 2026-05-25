# Claude Motion Polish Context

Date: 2026-05-25T18:26:26Z
Status: Ralph execution context

## Task Statement

Polish `.omx/prototypes/homepage-dark-hud-variants.html` motion using the project Claude-style direction from `PRODUCT.md`, `DESIGN.md`, `docs/design/awesome-design-md.md`, and fresh official Claude product overview inspection.

## Desired Outcome

- Keep NCHU AI Counselor Chinese product language and approved palette direction.
- Make the homepage motion feel closer to Claude's product page: calm, editorial, restrained, functional, and visibly staged.
- Use GSAP as the primary motion implementation surface.
- Do not copy Claude brand assets, logos, or proprietary illustrations.

## Known Facts / Evidence

- `PRODUCT.md` requires calm, trustworthy, work-focused, Chinese-first UI.
- `DESIGN.md` requires subtle functional motion that clarifies state changes.
- `docs/design/awesome-design-md.md` says external references should be adapted for tokens and interaction patterns, not copied as brand identity.
- Claude official page inspection found Webflow + GSAP 3.15 usage, `data-prevent-flicker`, `ScrollTrigger`, `SplitText`, hero heading word reveal, nav fade/slide, and secondary text/CTA/visual entrance using `autoAlpha`, small `y` movement, `power2.out`, and stagger.
- Current prototype already uses GSAP 3.12.5, `motion-prep`, `reveal`, SVG line drawing, and IntersectionObserver.

## Constraints

- Prototype path only: `.omx/prototypes/homepage-dark-hud-variants.html`.
- Use transform/opacity-heavy animation and keep reduced-motion fallback.
- Keep review URL served under `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html`.
- Avoid adding runtime dependencies just to match Claude.

## Unknowns / Open Questions

- Exact Claude easing curves and proprietary SplitText implementation details are not fully available.
- Current implementation can reproduce Claude-like motion class, not exact proprietary motion timing.

## Likely Code Touchpoints

- CSS initial states for `.motion-prep`, `.reveal`, and text reveal tokens.
- GSAP intro timeline.
- Section reveal observer behavior.
- Native/reduced-motion fallback.

## Verification Targets

- HTML parses and loads.
- GSAP branch runs without console errors.
- Hero title visibly reveals in token/word-like sequence.
- Prompt, visual panel, chips, and latest card enter in a synchronized Claude-like timeline.
- Scroll sections reveal with stronger text/card staging.
- Reduced-motion branch immediately reveals content.
