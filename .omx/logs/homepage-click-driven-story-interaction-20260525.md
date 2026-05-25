# Homepage Story Interaction Update

Date: 2026-05-25
Scope: `.omx/prototypes/homepage-dark-hud-variants.html`

## Decision

The feature/story section now uses click-driven chapter playback instead of scroll-driven chapter sequencing.

## Changes

- Renamed the section intent from scroll narrative preview to interactive chapter preview.
- Left-side cards are now clickable and keyboard-operable with `role="button"`, `tabindex="0"`, and `aria-pressed`.
- Clicking any feature card replays the corresponding right-side chapter animation.
- Scroll no longer advances through cards automatically.
- Returning upward to the homepage no longer replays the hero animation.
- The section remains a visible ability matrix; users decide which card to inspect.

## Verification

Playwright checked:

- Scroll through the story section does not auto-switch from the active card.
- Mouse click switches to the selected card and replays the right panel.
- Keyboard `Enter` on a card switches and replays the right panel.
- Returning to the homepage does not restart the hero playback.
- Browser console warnings/errors: 0.

Screenshot:

- `output/playwright/homepage-click-driven-story.png`
