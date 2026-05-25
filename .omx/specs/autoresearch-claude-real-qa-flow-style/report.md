# Autoresearch Report: Claude Real QA Flow Style

Date: 2026-05-25 UTC

## Mission

Research Claude-style frontend cues for a compact, static "real QA flow" component that can replace the current homepage prompt area. The user changed direction from teaching breakdown to **Scheme A: Real QA Flow** and asked for no animation yet.

## Sources

- Claude official product overview: `https://claude.com/product/overview`
- Claude reference from `awesome-design-md`: `https://github.com/VoltAgent/awesome-design-md/blob/main/design-md/claude/DESIGN.md`
- Raw Claude reference: `https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/claude/DESIGN.md`
- Claude artifacts help: `https://support.claude.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them`
- `PRODUCT.md`
- `DESIGN.md`
- `docs/design/awesome-design-md.md`
- Prior local research: `.omx/specs/autoresearch-homepage-light-claude-tuning/report.md`

## Useful Claude Style Cues

1. **Warm canvas, not pure white**
   - Claude's design reference centers on `#faf9f5` canvas, warm ink, soft cream card surfaces, and hairline borders.
   - For NCHU, keep the existing warm page canvas and avoid bright white chat cards.

2. **Product chrome over abstract explanation**
   - The Claude design reference explicitly prefers product mockup cards and real interface fragments over generic illustrations.
   - For this component, show an actual mini conversation: submitted question, model status, response, handoff boundary.

3. **Small-radius controls**
   - Claude-style controls use restrained 6-8px radii for buttons and inputs, 12px for content cards.
   - This matches the current homepage prompt box direction better than the previous large teaching board.

4. **Quiet hierarchy**
   - Text should be warm black/gray with strong but not heavy labels.
   - NCHU blue remains the project accent for primary CTA and selected states; do not copy Claude coral as the main brand color.

5. **Conversation split**
   - Claude help materials describe artifacts as appearing in a dedicated right-side window when generated; the chat remains the conversational lane.
   - In this compact homepage version, do not add a right-side artifact pane. Use a single contained card that previews the conversation flow.

## Design Decision For This Task

Build a **static compact real QA flow** inside the homepage prompt area:

- Keep the existing hero layout and approximate prompt-box width.
- Replace the pure input-only card with a quiet Claude-style conversation preview.
- Show:
  1. user submitted question,
  2. model processing/status strip,
  3. assistant answer preview,
  4. clear human handoff / counselor boundary.
- No animation in this pass.
- No product file implantation yet unless the user approves the preview.

## Acceptance Criteria

- Desktop: component fits the left hero column and does not crowd the right visual panel.
- Mobile: component remains readable, no horizontal overflow, CTA remains accessible.
- Visual style: warm canvas, thin borders, restrained radius, product-like chat surface, not a teaching dashboard.
- Static: no new motion layer in this pass.

