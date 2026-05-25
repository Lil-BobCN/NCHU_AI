# Homepage Story Left/Right Motion Sync

Date: 2026-05-25
Scope: `.omx/prototypes/homepage-dark-hud-variants.html`

## User Feedback

The story section had a timing mismatch:

- Left four capability cards rendered and animated first.
- Right chapter panel stayed black briefly, then appeared later.
- Desired behavior: left cards and right chapter preview should animate in synchronously.

## Fix

- Moved the first `setStoryIndex()` call in `playStoryIntro()` from `0.92s` to `0.12s`.
- Moved right chapter panel internal animation offsets earlier:
  - device starts at `0.04s`
  - device lines start at `0.16s`
  - text starts at `0.12s`
- Preserved the click-driven interaction: clicking a left card still replays the matching right chapter panel.

## Verification

Playwright verified against `http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html`.

Sampled story entrance:

- `180ms`: first card opacity `0.1284`, right panel opacity `0.085869`, right panel visibility `visible`.
- `300ms`: first card opacity `0.5503`, right panel opacity `0.405239`.
- `520ms`: first card opacity `0.9388`, right panel opacity `0.892553`, right title opacity `0.8379`.
- `950ms`: first card opacity `1`, right panel opacity `0.999392`, right title opacity `1`.

Interaction:

- Clicking the second card activates card index `1` and panel index `1`.
- Console/page errors: none.

Screenshot artifact:

- `output/playwright/homepage-story-sync-panel-final.png`
