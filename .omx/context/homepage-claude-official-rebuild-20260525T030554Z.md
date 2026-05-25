# Homepage Claude Official Rebuild Context

Date: 2026-05-25T03:05:54Z
Status: Ralph execution context

## Task

Rebuild `.omx/prototypes/homepage-dark-hud-variants.html` as a new homepage prototype for NCHU AI Counselor. The previous HUD/animation prototype may be treated as obsolete.

## Desired Outcome

- Closely reference the official Claude product overview page at `https://claude.com/product/overview`.
- Follow Claude's page structure, layout proportions, button grouping, entrance motion, and scroll reveal rhythm.
- Keep NCHU AI Counselor product language, Chinese-first copy, and institutional trust tone.
- Provide both light and dark modes:
  - Light: deep sea blue `#122E8A` plus soft milk white `#F5EFEA`.
  - Dark: smoke ink `#353538` plus tea white `#C6BAA9`.
- Replace Claude's black/orange pairing with the approved palettes.

## Evidence And References

- `PRODUCT.md`: NCHU AI Counselor is a Phase 1 student-support/counselor operations product. Tone is calm, trustworthy, work-focused, Chinese-first.
- `DESIGN.md`: use external references as layout/token/interaction guidance, do not copy brand identity.
- `docs/design/awesome-design-md.md`: selected reference may be adapted from awesome-design-md, with implementation verified by browser screenshots.
- Claude official page inspected on 2026-05-25:
  - Top nav: logo left, centered nav links, login/sales/CTA right.
  - Secondary product bar below nav.
  - Hero: large serif headline, supporting copy, prompt input and CTA, pill prompts, right abstract illustration, floating update card.
  - Scroll section: centered large headline, subtitle, grouped buttons, left feature list, right large network/abstract visual.
  - Later section: large CTA banner and usage tabs.

## Constraints

- Do not copy Claude brand assets, logo, or proprietary illustration.
- Implement as a standalone HTML prototype without adding dependencies.
- Use GSAP from CDN for timeline/scroll-style entrance motion.
- Animate transform and opacity only where possible.
- Chinese labels must fit on desktop and mobile.
- Verify with desktop and mobile screenshots.

## Likely Touchpoints

- `.omx/prototypes/homepage-dark-hud-variants.html`
- `.omx/logs/homepage-claude-official-rebuild-20260525.md`

## Verification Targets

- HTML loads over `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html`.
- No browser console errors.
- Light/dark toggle works and changes palettes.
- Entrance and scroll reveal animations are visible.
- Desktop and mobile screenshots saved under `output/playwright/homepage-claude-official-rebuild/`.
