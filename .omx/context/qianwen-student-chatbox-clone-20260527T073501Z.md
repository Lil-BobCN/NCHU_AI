# Qianwen Student Chatbox Clone Context

Timestamp: 2026-05-27T07:35:01Z

## Task Statement

Use `$ralph` to complete a verified frontend implementation. Use
`$clone-website` to analyze the target URL:

```text
https://www.qianwen.com/?source=tongyigw&st=null&bizPassParams=source%3Dtongyigw%26x-platform%3DexternalH5
```

Focus analysis on layout, interaction logic, and motion. Then use
`$assistant-ui` and the project assistant-ui context to clone the website's
chat-oriented experience as the student chat page. Use frontend design skills
for buttons/icons/content, GSAP skills for interaction/motion, and
`$karpathy-guidelines` while coding.

## Desired Outcome

- A documented analysis of the Qianwen page's layout, interaction model, and
  motion behavior.
- A reviewable `.omx/prototypes/` demo first, following the project website
  change order.
- The formal React student Chatbox at `frontend/src/StudentChatboxPage.tsx`
  restyled/restructured toward the Qianwen chat-page interaction language while
  retaining assistant-ui primitives and existing backend streaming behavior.
- Fresh verification evidence: lint/build, browser smoke, responsive screenshots,
  console check, and delivery log.

## Known Facts / Evidence

- Project workflow requires context-first development and verification evidence.
- Website/frontend experience changes should update and verify prototype first
  before touching `frontend/src/`.
- `SDAR-0009` approved assistant-ui as the main student Chatbox frontend
  framework.
- `frontend/package.json` already includes `@assistant-ui/react`, `gsap`, and
  `@gsap/react`.
- Current student Chatbox already uses `AssistantRuntimeProvider`,
  assistant-ui primitives, and `useExternalStoreRuntime`.
- Current approved backend boundary remains:
  - `GET /api/v1/student/conversations`
  - `POST /api/v1/student/chat/stream`
- Browser UI must not call model providers directly or expose API keys.
- The first mobile screenshot,
  `output/playwright/qianwen-original-mobile.png`, is superseded and should not
  be used for implementation reference.
- Corrected mobile reference:
  `output/playwright/qianwen-original-mobile-fixed.png`, copied to
  `docs/design-references/qianwen/qianwen-original-mobile-fixed.png`.

## Constraints

- Do not add new dependencies without product-manager approval.
- Do not modify FastAPI API contracts.
- Do not switch model providers.
- Do not enable web search, RAG, attachments, real school resources, real
  student data, persistence, teacher/counselor Chatbox, or multi-role shared
  Chat shell extraction.
- Keep edits small, reversible, and scoped to the student Chatbox surface unless
  the prototype or documentation artifacts require support files.
- Preserve Chinese-first student-support copy and institutional trust.
- Use GSAP with scoped refs/useGSAP cleanup and animate transform/opacity where
  possible.

## Unknowns / Open Questions

- Whether the Qianwen target page can be fully accessed from this environment.
- Which UI states are visible without login.
- Whether remote assets, fonts, videos, and scripts can be inspected or saved.
- Exact responsive breakpoints and animation timings of the live page.

## Likely Codebase Touchpoints

- `.omx/prototypes/`
- `.omx/context/`
- `.omx/specs/`
- `.omx/logs/`
- `frontend/src/StudentChatboxPage.tsx`
- `frontend/src/App.css`
- `frontend/package.json` only for verification, not expected to change.

## Ralph Success Criteria

- Qianwen analysis artifacts exist and cite concrete browser observations.
- Prototype exists and can be opened locally.
- React student Chatbox builds and preserves existing assistant-ui runtime and
  FastAPI streaming boundary.
- Desktop and mobile browser screenshots show the cloned interaction language.
- Lint/build pass or any blocker is explicitly documented with exact output.
