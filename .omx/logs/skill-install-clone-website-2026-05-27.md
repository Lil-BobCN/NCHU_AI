# Clone Website Skill Install

Date: 2026-05-27

## Request

Install the Codex skill from `JCodesMore/ai-website-cloner-template`.

## Scope

- No project runtime, architecture, dependency, API, database, or frontend source changes.
- Installed a local Codex skill under the user's Codex home.

## Result

Installed the skill from:

```text
JCodesMore/ai-website-cloner-template
path: .codex/skills/clone-website
ref: master
```

Destination:

```text
/Users/Admin/.codex/skills/clone-website
```

The first installer attempt using direct download failed with a transient TLS EOF
error from the GitHub zip request. Re-running the official installer with
`--method git` completed successfully.

## Verification

- `SKILL.md` exists at `/Users/Admin/.codex/skills/clone-website/SKILL.md`.
- Installed skill metadata reports `name: clone-website`.
- Installed skill metadata reports `user-invocable: true`.

Restart Codex to pick up newly installed skills.
