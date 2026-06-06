# assistant-ui Skills Install

Date: 2026-05-27

## Request

Install the assistant-ui skill set shown in the user-provided screenshot:

```text
npx skills add assistant-ui/skills
```

## Scope

- Local Codex skill installation only.
- No project runtime, frontend source, backend source, API, dependency, model,
  database, or persistence changes.

## Environment Note

The current shell does not have Node/npm/npx available:

```text
node not found
npm not found
npx not found
```

To achieve the same Codex skill installation result, the official Codex
`skill-installer` GitHub installer was used against the public repository:

```text
assistant-ui/skills
ref: main
method: git
```

## Installed Skills

- `/assistant-ui`
- `/setup`
- `/primitives`
- `/runtime`
- `/tools`
- `/streaming`
- `/cloud`
- `/thread-list`
- `/update`

## Destination

Installed into:

```text
/Users/Admin/.codex/skills/
```

Concrete paths:

```text
/Users/Admin/.codex/skills/assistant-ui
/Users/Admin/.codex/skills/setup
/Users/Admin/.codex/skills/primitives
/Users/Admin/.codex/skills/runtime
/Users/Admin/.codex/skills/tools
/Users/Admin/.codex/skills/streaming
/Users/Admin/.codex/skills/cloud
/Users/Admin/.codex/skills/thread-list
/Users/Admin/.codex/skills/update
```

## Verification

- Verified each installed directory contains `SKILL.md`.
- Verified each `SKILL.md` reports the expected `name` metadata:
  `assistant-ui`, `setup`, `primitives`, `runtime`, `tools`, `streaming`,
  `cloud`, `thread-list`, and `update`.

Restart Codex to pick up newly installed skills.
