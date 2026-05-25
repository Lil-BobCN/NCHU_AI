# Homepage Claude Official Rebuild

Date: 2026-05-25
Status: completed prototype rebuild

## Scope

Rebuilt `.omx/prototypes/homepage-dark-hud-variants.html` as a new Claude-official-product-page-inspired homepage prototype for NCHU AI Counselor. The previous dark HUD variant is treated as obsolete for this review path.

## Inputs Used

- `PRODUCT.md`: NCHU AI Counselor product context, Chinese-first institutional support tone.
- `DESIGN.md`: external references may guide layout, hierarchy, tokens, and interactions, but must not replace project identity.
- `docs/design/awesome-design-md.md`: use selected external design references through adaptation, not brand copying.
- Claude official product overview: `https://claude.com/product/overview`.

## Skills Applied

- `autoresearch`: used to ground the implementation in the requested external reference and project documents.
- `ralph`: used to create a task context snapshot and continue through implementation plus verification.
- `karpathy-guidelines`: kept the change scoped to the requested prototype and defined concrete verification checks.
- `impeccable` / `frontend-design`: used for visual hierarchy, palette adaptation, typography, responsive layout, and avoiding generic AI-style output.
- `gsap-core`, `gsap-timeline`, `gsap-performance`: used for entrance sequencing, reveal rhythm, and transform/opacity-only animation discipline.

## Design Translation

- Claude-like structure:
  - Sticky top navigation with logo left, centered links, right login/sales/CTA cluster.
  - Secondary thin product bar.
  - Hero with large serif headline, supporting copy, prompt input, CTA button, and prompt pills.
  - Right abstract illustration and floating update card.
  - Scroll section with centered headline, grouped actions, left feature list, right network visual.
  - CTA band and usage tabs.
- Palette replacement:
  - Light mode: `#F5EFEA` background, `#122E8A` primary.
  - Dark mode: `#353538` background, `#C6BAA9` primary/text accent.
- Brand adaptation:
  - No Claude logo, assets, or exact brand illustration copied.
  - Copy remains NCHU AI Counselor Chinese product language.

## Verification Evidence

- Static inline JavaScript parse: passed.
- Local HTTP check:
  - `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html`
  - returned HTTP 200.
- Playwright browser verification:
  - GSAP loaded: `true`.
  - Console/page errors: `0`.
  - Light background: `rgb(245, 239, 234)`.
  - Dark background: `rgb(53, 53, 56)`.
  - Dark ink: `rgb(198, 186, 169)`.
  - Mobile viewport width check: `390`, layout width `362`.

## Screenshot Evidence

- `output/playwright/homepage-claude-official-rebuild/viewport-top-light.png`
- `output/playwright/homepage-claude-official-rebuild/viewport-platform-anchor-light.png`
- `output/playwright/homepage-claude-official-rebuild/viewport-platform-dark.png`
- `output/playwright/homepage-claude-official-rebuild/mobile-top-light.png`

## Notes

- The prototype uses GSAP from CDN and includes a native Web Animations fallback so the entrance/reveal motion still plays if the CDN is unavailable.
- This is still a review prototype, not the formal React homepage implementation.

## 2026-05-25 Dark Palette Revision

- Updated dark mode to the requested palette:
  - Hermès orange primary: `#FF8A00`.
  - Premium black background: `#0D131A`.
- Kept warm light text for readability while using orange for primary actions, lines, chips, SVG strokes, and emphasis.
- Verification:
  - Inline JavaScript parse passed.
  - Local HTTP returned 200.
  - Playwright console/page errors: `0`.
  - Browser-computed colors:
    - body background: `rgb(13, 19, 26)`.
    - primary button background: `rgb(255, 138, 0)`.
- Screenshot: `output/playwright/homepage-claude-official-rebuild/dark-hermes-orange.png`.

## 2026-05-25 Dark Palette Revision 2

- Updated dark mode again to the requested palette:
  - Red teak primary: `#AB5924`.
  - Premium black background: `#0D131A`.
- Browser-computed colors:
  - body background: `rgb(13, 19, 26)`.
  - primary button background: `rgb(171, 89, 36)`.
  - primary button text: `rgb(13, 19, 26)`.
- Verification:
  - Inline JavaScript parse passed.
  - Local HTTP returned 200.
  - Playwright console/page errors: `0`.
- Screenshot: `output/playwright/homepage-claude-official-rebuild/dark-red-teak.png`.

## 2026-05-25 Light Claude Tuning

- Re-tuned Light mode against `PRODUCT.md`, `DESIGN.md`, `docs/design/awesome-design-md.md`, and the Claude product overview reference.
- Moved content text to warm black/gray while keeping NCHU blue for CTAs, graphics, SVG strokes, and visual accents.
- Reduced display typography and forced the hero title into two intentional lines:
  - desktop H1 browser sample: `65.92px`;
  - mobile title text: `遇见你的\nAI 辅导员`.
- Shifted main nav links toward the action cluster with `justify-self: end`.
- Changed nav/action buttons toward Claude-like small-radius rectangles:
  - primary button radius: `6px`;
  - prompt container radius: `9px`;
  - Light/Dark toggle remains pill-shaped by request.
- Made the prompt input component smaller and changed the secondary product strip to Chinese labels.
- Verification:
  - inline JavaScript parse passed;
  - local HTTP returned 200;
  - Playwright console/page errors: `0`;
  - desktop Light body background: `rgb(250, 249, 245)`;
  - desktop H1 color: `rgb(20, 20, 19)`;
  - graphic fill remains blue: `rgb(18, 46, 138)`;
  - mobile scroll width equals viewport width: `390 / 390`.
- Screenshots:
  - `output/playwright/homepage-claude-official-rebuild/light-tuned-top-v3.png`
  - `output/playwright/homepage-claude-official-rebuild/light-tuned-platform-v3.png`
  - `output/playwright/homepage-claude-official-rebuild/light-tuned-mobile-v3.png`

## 2026-05-25 Light Typography Alignment

- Rechecked Claude official product overview in browser:
  - body font sample: `"Anthropic Sans", Arial, sans-serif`;
  - H1 font sample: `"Anthropic Serif", Georgia, sans-serif`;
  - H1 weight sample: `500`;
  - H1 size sample: `60px`.
- Adjusted the prototype to avoid copying proprietary Claude fonts while matching the project typography guidance:
  - shared font tokens now use system Chinese/English sans-serif stack;
  - H1/H2/CTA title use the same clean display stack instead of Songti/Georgia;
  - H1 weight reduced to `500`;
  - desktop H1 size reduced to `56px`;
  - mobile H1 sample size is `35.88px`.
- Rationale:
  - `DESIGN.md` requires clean sans-serif UI typography and Chinese labels that fit containers;
  - the previous Songti-style hero heading looked too classical and visually heavy for the NCHU AI Counselor product tone.
- Verification:
  - inline JavaScript parse passed;
  - local HTTP returned 200;
  - desktop computed H1 font stack: `"PingFang SC", "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", Arial, system-ui, sans-serif`;
  - desktop computed H1 weight: `500`;
  - mobile scroll width equals viewport width: `390 / 390`.
- Screenshots:
  - `output/playwright/homepage-claude-official-rebuild/light-font-sans-top-v2.png`
  - `output/playwright/homepage-claude-official-rebuild/light-font-sans-mobile-v2.png`

## 2026-05-26 Light Hero Copy And Gradient Tuning

- Changed hero title layout from two display lines to one line on desktop:
  - browser text: `遇见你的 AI 辅导员`;
  - computed `white-space`: `nowrap`;
  - title span top values match, confirming same-line layout.
- Replaced hero support copy with:
  - `与NCHU AI同行，让校园信息触手可及`.
- Strengthened the Light mode first-to-second-screen gradient:
  - main transition band now uses stronger warm gray;
  - `#platform` now combines warm gray vertical gradient with a subtle NCHU blue radial tint.
- Verification:
  - inline JavaScript parse passed;
  - local HTTP returned 200;
  - Playwright console/page errors: `0`;
  - desktop scroll width equals viewport width: `1280 / 1280`.
- Screenshots:
  - `output/playwright/homepage-claude-official-rebuild/light-copy-gradient-top-v1.png`
  - `output/playwright/homepage-claude-official-rebuild/light-copy-gradient-platform-v1.png`
  - `output/playwright/homepage-claude-official-rebuild/light-copy-gradient-mobile-v1.png`

## 2026-05-26 Sticky Header Group

- Changed the top navigation and product overview strip into one sticky header group.
- Rationale:
  - match the Claude-style behavior where the main nav and product strip remain together during scroll;
  - avoid separate sticky offsets or scroll listeners.
- Implementation:
  - added `.sticky-header` as the sticky container;
  - moved `.top-nav` and `.product-bar` inside it;
  - kept the existing nav and product-strip visual treatment.
- Verification:
  - inline JavaScript parse passed;
  - local HTTP returned 200;
  - after scrolling to `760px`, browser metrics showed:
    - `.sticky-header` top: `0`, bottom: `114`;
    - `.top-nav` top: `0`, bottom: `65`;
    - `.product-bar` top: `65`, bottom: `114`;
    - desktop scroll width equals viewport width: `1280 / 1280`;
  - Playwright console/page errors: `0`.
- Screenshots:
  - `output/playwright/homepage-claude-official-rebuild/sticky-header-top-v1.png`
  - `output/playwright/homepage-claude-official-rebuild/sticky-header-platform-v1.png`
  - `output/playwright/homepage-claude-official-rebuild/sticky-header-mobile-platform-v1.png`

## 2026-05-25 Claude Motion Polish

- Used `PRODUCT.md`, `DESIGN.md`, `docs/design/awesome-design-md.md`, and fresh inspection of `https://claude.com/product/overview`.
- Claude evidence used:
  - GSAP 3.15, ScrollTrigger, SplitText, and `data-prevent-flicker`;
  - hero heading word reveal from `autoAlpha: 0`;
  - body/CTA/visual entrance with small `y` movement and `power2.out`;
  - nav/secondary nav entrance from `autoAlpha: 0, y: -20`;
  - scroll headings/cards reveal with stagger.
- Prototype changes:
  - added local text tokenization for hero and section heading reveal;
  - rebuilt the hero GSAP intro timeline around nav, product bar, heading tokens, copy, prompt, visual, SVG lines, chips, and latest card;
  - made section headings reveal by token and feature/card/button groups reveal with child staggers;
  - kept reduced-motion immediate reveal.
- Verification:
  - local URL returned HTTP `200`;
  - hero motion screenshot at `450ms`: `output/playwright/homepage-claude-motion-polish-t0450-v2.png`;
  - resolved hero screenshot at `1900ms`: `output/playwright/homepage-claude-motion-polish-t1900-v2.png`;
  - platform section screenshot: `output/playwright/homepage-claude-motion-polish-platform.png`.
- Research artifact:
  - `.omx/specs/autoresearch-claude-motion-polish/report.md`

## 2026-05-25 Top-Down Entrance Motion Repair

- User issue:
  - the first viewport felt fully loaded before animation;
  - entrance motion was too fast and appeared as separate elements moving after render.
- Repair:
  - added an early `motion-boot` class before CSS render so the first viewport cannot expose the completed hero before motion setup;
  - split the sticky header wrapper from the animated top nav and product bar so the top strip can enter in order;
  - rebuilt the GSAP intro timeline as a slower top-down sequence: nav -> product bar -> eyebrow/title -> copy/prompt -> right visual/cards;
  - moved persistent floating motion until after the intro completes so it no longer fights the entrance timeline.
- Verification:
  - inline JavaScript parse passed;
  - local HTTP returned `200`;
  - file URL screenshot also shows no completed hero at `100ms`;
  - screenshot checkpoints:
    - `output/playwright/homepage-topdown-motion/t0100.png`
    - `output/playwright/homepage-topdown-motion/t0900.png`
    - `output/playwright/homepage-topdown-motion/t3000.png`
    - `output/playwright/homepage-topdown-motion/file-t0100.png`

## 2026-05-25 Scroll Replay Motion

- User issue:
  - section/card reveal motion only played while scrolling down the first time;
  - scrolling back upward should also show reveal motion again.
- Repair:
  - changed the GSAP section reveal observer from one-shot behavior to replay behavior;
  - removed the final `unobserve` path and added explicit reset-on-exit state;
  - tracked real scroll direction so elements entering while scrolling down start from below, and elements entering while scrolling up start from above;
  - reset child text/card details, network lines, and orbit labels so repeated reveals are visible rather than only moving the parent block.
- Verification:
  - inline JavaScript parse passed;
  - local HTTP returned `200`;
  - Playwright browser automation confirmed:
    - down-scroll entry active with positive `y`;
    - leave-top state reset to hidden;
    - up-scroll entry active with negative `y`;
    - completed replay opacity returned to `1`;
    - console/page errors: `0`;
  - screenshot checkpoints:
    - `output/playwright/homepage-scroll-replay-down-entry.png`
    - `output/playwright/homepage-scroll-replay-up-entry.png`

## 2026-05-25 Platform Replay Gate

- User issue:
  - the `#platform` section shown in the screenshot should not participate in replay just because individual rows/cards leave the viewport during local scrolling;
  - it should replay only after the page has fully returned to the previous page, then enters `#platform` again while scrolling down.
- Repair:
  - marked `#platform` with `data-replay-scope="previous-page-gated"`;
  - kept global replay behavior for other `.reveal` elements;
  - special-cased `#platform` reveal items so they do not reset on normal element exit;
  - added a previous-page gate: reset/re-arm only when `#platform` is below roughly the last 10% of the viewport, accounting for the sticky header and real browser layout;
  - mirrored the same gate in the native fallback path.
- Verification:
  - inline JavaScript parse passed;
  - local HTTP returned `200`;
  - Playwright browser automation confirmed:
    - `#platform` plays and remains active after scrolling past it;
    - partial upward return before the previous page does not reset it;
    - full return to the previous page resets and arms it;
    - scrolling down again replays it from below;
    - console/page errors: `0`;
  - screenshot checkpoint:
    - `output/playwright/homepage-platform-gated-replay-return.png`

## 2026-05-26 Platform Item 04 Jitter Guard

- User issue:
  - the lower-left `人工协同` row in `#platform` could visually feel like it was rapidly replaying near the viewport edge.
- Repair:
  - kept `#platform` reveal items excluded from the normal per-element replay observer;
  - added an explicit GSAP timeline latch for the whole `#platform` replay group;
  - kill and reset that section timeline only after the page has fully returned to the previous page;
  - left all other section scroll-replay behavior unchanged.
- Verification:
  - inline JavaScript parse passed;
  - local HTTP returned `200`;
  - Playwright jitter simulation around the `人工协同` row passed:
    - 10 edge-scroll samples;
    - unstable samples: `0`;
    - `人工协同` stayed `active=true`, `opacity=1`, `visibility=visible`;
    - full previous-page return still re-armed the section;
    - re-entering `#platform` replayed the section group;
    - console/page errors: `0`.
