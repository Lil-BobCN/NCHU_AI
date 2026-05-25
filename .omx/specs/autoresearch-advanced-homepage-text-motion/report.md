# Advanced Homepage Text Motion Research

Date: 2026-05-24
Status: prototype-ready

## Mission

Find a more advanced, higher-technology-feeling direction for the homepage left-side hero text motion, based on the product manager's choice of the previous `B` direction.

## Inputs

- Product manager selected the B direction: word/phrase-level reveal instead of whole-line reveal.
- Current need is a reviewable prototype, not a production homepage change.
- Skills used: `frontend-design`, `ui-ux-pro-max`, `gsap-core`, `gsap-timeline`, `gsap-plugins`, `gsap-performance`, `gsap-react` guidance for future React migration, and `karpathy-guidelines` to keep the prototype bounded.

## Research Synthesis

- Motion-driven hero sections work best when one signature animation carries the view instead of animating every element.
- Strong technology feel can be achieved with dark OLED/cinematic background, glass surfaces, restrained cyan/blue/violet highlights, and timeline-based reveal.
- Accessibility requires `prefers-reduced-motion` handling and avoiding excessive continuous motion.
- GSAP local package already includes `CustomEase`, `SplitText`, and `ScrambleTextPlugin`; no new runtime dependency is needed for the prototype or future React migration.

## Prototype Options

Prototype:

- `.omx/prototypes/homepage-tech-text-motion-lab.html`
- Preview URL: `http://127.0.0.1:5188/.omx/prototypes/homepage-tech-text-motion-lab.html`

Options:

1. `AI Decode`
   - Phrase-level reveal plus `ScrambleTextPlugin`.
   - Best when the product manager wants the AI identity to be explicit.
2. `Glass Scan`
   - Phrase-level mask reveal plus glass/light scan feeling.
   - Best balance for Apple-like glass + aviation technology feel.
3. `HUD Boot`
   - Line/layer boot sequence inspired by cockpit/HUD startup.
   - Best when the product manager wants stronger aviation/system-console identity.

## Recommendation

Use option 2, `Glass Scan`, as the default candidate if the product manager wants high-end technology without looking overly gimmicky.

Keep option 1 if AI decoding is the dominant story.
Keep option 3 if aviation cockpit language is the dominant story.

## Verification

- Prototype opened successfully via local static server.
- Playwright snapshot detected all three options.
- Clean Playwright console check: 0 errors, 0 warnings.
- Screenshot evidence: `output/playwright/homepage-tech-text-motion-lab.png`.

## Non-goals

- Do not change the formal React homepage yet.
- Do not add new dependencies.
- Do not introduce Three.js, Lottie, Rive, Lenis, real school materials, real student data, production SSO, database schema, or backend/RAG changes.
