# Ralph Context: Platform Feature Item Jitter Fix

Date: 2026-05-25T20:21:32Z
Workspace: `C:\Users\liuqi\Desktop\agentproject`

## Task Statement

Fix rapid repeated animation on the fourth `#platform` feature row, "人工协同", in `.omx/prototypes/homepage-dark-hud-variants.html`.

## Desired Outcome

- The `#platform` feature list and network card should not repeatedly replay when the fourth row is near the viewport edge.
- `#platform` should animate as a section-level group.
- The previous-page replay gate remains: only after fully returning to the previous page should `#platform` be armed for another replay.

## Current Evidence

- `#platform` has `data-replay-scope="previous-page-gated"`.
- Its child `.reveal` elements are still observed individually.
- The fourth feature row can sit near the viewport threshold, causing visible repeated edge-trigger motion.

## Verification Plan

- Parse inline JavaScript.
- Use browser automation to hold the viewport around the fourth feature row and perform small scroll jitters.
- Confirm the fourth row stays active/visible and does not flip active state repeatedly.
- Confirm full previous-page return still resets and replays the section.
