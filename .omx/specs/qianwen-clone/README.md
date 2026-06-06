# Qianwen Clone Analysis For Student Chatbox

Date: 2026-05-27

Target URL:

```text
https://www.qianwen.com/?source=tongyigw&st=null&bizPassParams=source%3Dtongyigw%26x-platform%3DexternalH5
```

## Purpose

Analyze the Qianwen web app's layout, interaction model, and motion language,
then adapt the relevant chat-surface patterns to the NCHU student Chatbox.

## Tool Notes

- The Codex in-app browser backend was unavailable during initial setup
  (`agent.browsers.list()` returned an empty list).
- CLI Playwright was initially unavailable in the first shell probe, but a later
  check confirmed `node`, `npm`, and `npx` are available from `/opt/homebrew/bin`.
  The primary capture still used system Google Chrome headless because it was
  already sufficient for the required reference screenshots and DOM dump.
- System Google Chrome headless was available and used for primary URL
  screenshots and DOM dumps.

## Evidence Artifacts

- `output/playwright/qianwen-original-desktop.png`
- `output/playwright/qianwen-original-mobile-fixed.png`
- `output/playwright/qianwen-original-dom.html`

The earlier `output/playwright/qianwen-original-mobile.png` capture is
superseded and must not be used as implementation evidence. It was captured
before the mobile composer settled into the target proportions. The corrected
reference uses Playwright mobile device emulation and was copied to
`docs/design-references/qianwen/qianwen-original-mobile-fixed.png`.

## Planned Outputs

- `PAGE_TOPOLOGY.md`
- `BEHAVIORS.md`
- Component specs under `.omx/specs/qianwen-clone/components/`
- A reviewable prototype under `.omx/prototypes/`
- React implementation changes in `frontend/src/StudentChatboxPage.tsx` and
  `frontend/src/App.css`
