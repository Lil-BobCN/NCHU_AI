# Ralph Context: Preview 5188 Connection Refused

Date: 2026-05-26T10:32:19Z
Workspace: `/Users/Admin/学校项目/NCHU_AI`

## Task Statement

Investigate and fix the browser error for `http://172.20.10.2:5188/.omx/prototypes/homepage-dark-hud-variants.html#top`, which shows `ERR_CONNECTION_REFUSED`.

## Desired Outcome

- Identify the concrete cause of the connection refusal.
- Restore access to `.omx/prototypes/homepage-dark-hud-variants.html` on port `5188`.
- Verify the page is reachable through both `127.0.0.1:5188` and `172.20.10.2:5188`.

## Known Facts / Evidence

- `ifconfig` shows `172.20.10.2` is assigned locally.
- `lsof -nP -iTCP:5188 -sTCP:LISTEN` returned no listener.
- `curl -I http://127.0.0.1:5188/.omx/prototypes/homepage-dark-hud-variants.html` failed with connection refused.
- `curl -I http://172.20.10.2:5188/.omx/prototypes/homepage-dark-hud-variants.html` also failed with connection refused.

## Constraints

- Do not change the prototype HTML unless the investigation proves the page content is the cause.
- Prefer a simple static server bound to `0.0.0.0` so the LAN address works.
- Preserve unrelated dirty worktree changes.

## Unknowns / Open Questions

- The previous preview process may have been stopped or crashed.
- The existing log path `.omx/logs/static-prototype-preview-5188-2026-05-26.md` exists in the IDE but did not contain readable content during initial inspection.

## Likely Touchpoints

- Port `5188` preview process.
- `.omx/prototypes/homepage-dark-hud-variants.html`.
- `.omx/logs/static-prototype-preview-5188-2026-05-26.md` if a durable preview note is needed.

## Verification Plan

- Start a static server from repo root on `0.0.0.0:5188`.
- Check `lsof` confirms a listener on `*:5188`.
- Run `curl -I` against `127.0.0.1:5188` and `172.20.10.2:5188`.
- Optionally open with browser automation if the URL is reachable.
