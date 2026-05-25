# AutoResearch Report: Homepage Dark HUD Component Directions

Date: 2026-05-24
Status: implemented as local prototype candidates

## Product-Manager Decision Interpreted

The selected direction is:

- **A style**: restrained, premium, legible, less flashy than AI-decode/glitch.
- **C interaction**: layered HUD boot sequence: eyebrow, title, body, CTA, status cards, visual module and bottom HUD rail enter in a controlled sequence.
- **Palette requirement**: darker and more premium, with deeper black/slate base and restrained aviation/AI accents.

## External Reference Findings

### 21st.dev Community Components

Reference URL: `https://21st.dev/community/components`

Observed useful component categories:

- `Heroes`
- `Features`
- `Cards`
- `Navigation Menus`
- `Texts`
- `Shaders`
- `AI Chats`
- `Buttons`
- `Badges`

Reusable pattern:

- Use mature landing-page blocks rather than one-off decoration.
- Compose the homepage from a glass navbar, hero copy, CTA cluster, product preview, feature cards, and text reveal components.
- Use "Text Components" patterns for reveal/morph/sparkle inspiration, but avoid over-decorating the production hero.

### MotionSites

Reference URL: `https://motionsites.ai/`

Observed useful pattern names and categories:

- `AI Workflow Hero`
- `Liquid Glass Agency`
- `SkyElite Private Jets`
- `NOVA Space Systems`
- `Cinematic Landing Page`
- `Weblex Dark Hero`
- `Dark Portfolio Hero`
- `Space Voyage`

Reusable pattern:

- Use a cinematic first viewport with dark background, large clear headline, product story, and a visual object on the right.
- Use a prompt-library style grid as inspiration for variant review, not as runtime dependency.
- Aviation/space references support a darker cockpit/HUD tone, but the product must remain a school AI counselor product rather than a sci-fi prop.

## Local UI/UX Pro Max Findings

Useful style directions:

- `Dark Mode (OLED)`: deep black, dark grey, midnight blue, minimal glow, high readability.
- `Glassmorphism`: frosted glass, translucent surfaces, subtle borders, depth.
- `HUD / Sci-Fi FUI`: data, transparency, scanlines, fine-line drawing, but must avoid thin-line accessibility issues.
- `Space Tech / Aerospace`: deep space black, star white, metallic accents.
- `Bento Box Grid`: modular cards and feature tiles for mature product explanation.

Useful landing pattern:

- `Video-First Hero`: reserve a visual/video area with dark overlay and white text.
- `Hero + Features + CTA`: hero, value props, feature cards, bottom CTA.

Typography guidance:

- Prefer system font stack for local reliability in China mainland network context.
- If later introducing web fonts, choose Chinese-safe modern sans (`Noto Sans SC`) plus a technical Latin display font only after approval.

## Prototype Decision

Create one review page with three local candidate variants:

1. **Obsidian Command**
   - Closest to Linear/Apple restraint.
   - Dark graphite, cyan/blue light, clean bento cards.

2. **Aero Glass**
   - Stronger aviation/cockpit feel.
   - Dark navy, warm runway amber, glass instrument surfaces.

3. **Liquid Intelligence**
   - More Apple liquid-glass and AI feel.
   - Deep black, muted cyan, soft violet, restrained internal glow.

All three share:

- A-style restrained visual hierarchy.
- C-style HUD boot sequence.
- Local GSAP timeline motion.
- No new dependencies.
- No real school logo or real student data.

## Output Artifact

- `.omx/prototypes/homepage-dark-hud-variants.html`

## Verification

Completed checks on 2026-05-24:

- Browser opens via local static server:
  - `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html`
- Playwright verification:
  - Console messages: `0 errors / 0 warnings`.
  - A1 headline sampled from hidden state to visible state.
  - A2 and A3 variant buttons switch to visible variants.
  - Screenshot evidence:
    - `output/playwright/homepage-dark-hud-variants-1280-v2.png`
    - `output/playwright/homepage-dark-hud-variants-verify.png`
- Scope check:
  - Prototype only.
  - Formal React homepage files were not modified.
  - No new runtime dependencies were introduced.

## Motion Enhancement Pass

Completed after product-manager feedback that many animations were still missing:

- Added stronger boot sequence: startup curtain, nav glint, background grid drift, and atmosphere streaks.
- Added more visible Linear-like copy motion: masked headline reveal plus row shine.
- Added product-flow tags under the body copy so the left side has a second staged motion layer.
- Added right-side HUD motion: radar scan, flight trails, wing keyframes, route drawing, HUD bars, and log row reveal.
- Added scroll narrative stage: left chapter cards and right sticky chapter screen update with scroll progress.
- Changed default playback to `1x` while preserving `0.5x` for slow review.
- Added an entry link from `.omx/prototypes/homepage-linear-text-motion-demo.html` to this dark HUD review prototype.

Latest verification:

- Browser URL: `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html`
- Playwright browser script: `0 errors / 0 warnings`.
- Hero sampled after playback:
  - title opacity: `1`
  - copy sequence opacity: `1`
  - copy sequence active: `true`
  - radar opacity: `0.4799`
  - flight opacity: `1`
  - nav booted: `true`
- Scroll sampled after moving into story section:
  - active card: `知识运维`
  - active panel: `CHAPTER 03 / ADMIN`
- Variant switching sampled:
  - active variant after clicking A2: `aero`
  - active button after clicking A2: `aero`
- Screenshot evidence:
  - `output/playwright/homepage-dark-hud-variants-final-t0700.png`
  - `output/playwright/homepage-dark-hud-variants-final-t2800.png`
  - `output/playwright/homepage-dark-hud-variants-enhanced-browser-hero.png`
  - `output/playwright/homepage-dark-hud-variants-enhanced-browser-story.png`
  - `output/playwright/homepage-linear-demo-with-dark-link.png`
