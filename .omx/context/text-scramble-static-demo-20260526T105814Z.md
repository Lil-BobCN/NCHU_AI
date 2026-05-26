# Ralph Context Snapshot

- task statement: In the static demo page at `.omx/prototypes/homepage-dark-hud-variants.html`, change the screenshot label "AI Counselor Demo, Phase 2" to use a TextScramble-style presentation.
- desired outcome: The demo site at `http://172.20.10.2:5188/.omx/prototypes/homepage-dark-hud-variants.html#top` shows the hero eyebrow text with a monospaced uppercase scramble effect similar to the provided React component.
- known facts/evidence: The exact target text is in `.omx/prototypes/homepage-dark-hud-variants.html` on the hero eyebrow element with `data-motion="hero-eyebrow"`. The page is static HTML with existing GSAP/native animation paths.
- constraints: Keep changes surgical, preserve existing static demo motion hooks, do not modify the formal React app for this request, and do not add dependencies.
- unknowns/open questions: No blocking unknowns after the user clarified the target is the demo page.
- likely codebase touchpoints: `.omx/prototypes/homepage-dark-hud-variants.html` only.
