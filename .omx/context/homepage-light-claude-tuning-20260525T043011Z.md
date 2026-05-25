# Homepage Light Claude Tuning Context

Date: 2026-05-25T04:30:11Z
Status: Ralph execution context

## Task

Tune `.omx/prototypes/homepage-dark-hud-variants.html` with emphasis on Light mode. Keep the current Claude-inspired page direction, but refine typography, navigation alignment, button shape, prompt input sizing, section gradients, and scroll transition motion.

## User Requirements

- Light text should not be mostly blue.
- Use black, gray, and Claude-like neutral tones for text.
- Keep product graphics and visual accents blue where Claude would keep orange illustration/accent elements.
- Navigation action buttons should be more Claude-like: rectangular first, small radius second. Theme toggle keeps its existing pill design.
- Main nav links (`认识产品`, `平台能力`, `角色场景`, `治理边界`, `资源`) should shift right instead of sitting too centered.
- Reduce oversized typography and create more breathing room.
- Light mode first and second sections should have a gradient/tonal transition like Claude, not a flat surface.
- Add a more mature scroll/page transition feel.
- Shrink and simplify the simulated question input component using Claude's rectangular-primary/small-radius button language.

## Reference Evidence

- Claude official page inspected with Playwright on 2026-05-25:
  - Body background: `rgb(250, 249, 245)`.
  - Body text: `rgb(20, 20, 19)`.
  - H1 color: `rgb(20, 20, 19)`.
  - H1 desktop sample size: `64px`.
  - Navigation buttons use small rounded rectangles around `4px` radius.
  - Hero uses black/neutral text and preserves the orange abstract illustration as a separate accent.
  - First/second section transition uses warm off-white/gray tonal bands.
- Project documents:
  - `PRODUCT.md`: calm, trustworthy, work-focused, Chinese-first.
  - `DESIGN.md`: restrained polished visual treatment, readable typography, responsive constraints.

## Constraints

- Do not alter the approved dark palette direction in this pass.
- Do not remove the Light/Dark pill toggle.
- Do not remove blue from illustration/accent graphics.
- Prototype only, no formal React implementation and no new dependency.

## Touchpoints

- `.omx/prototypes/homepage-dark-hud-variants.html`
- `.omx/logs/homepage-claude-official-rebuild-20260525.md`

## Verification Targets

- Inline scripts parse.
- Prototype returns HTTP 200.
- Playwright desktop Light screenshot shows black/gray text with blue graphics retained.
- Light/Dark toggle still works.
- Console/page errors are zero.
