# Project Agent Instructions

This file is the mandatory entry point for AI-assisted work in this repository.

## Required Workflow Baseline

Before starting any work, read and use `docs/development-process.md` as the
default human-AI collaboration workflow for this project.

Every task must begin from the workflow document's context-first approach:

- Identify the user request, current project phase, approved decisions, non-goals,
  risks, and acceptance criteria.
- Read the relevant project context, including `README.md`, `PROJECT_STATE.md`,
  and applicable `.omx/context`, `.omx/specs`, `.omx/plans`, and `.omx/logs`
  artifacts.
- If requirements, boundaries, or acceptance criteria are unclear, clarify before
  implementation.
- Keep implementation work small, reversible, and aligned with existing
  architecture.
- Provide verification evidence before calling work complete.

## Website Change Order

For website or frontend experience changes, update and verify the demo/prototype
version first. In this project that means starting from the relevant artifact
under `.omx/prototypes/`, such as
`.omx/prototypes/homepage-dark-hud-variants.html`, before changing the formal
React implementation under `frontend/src/`.

## assistant-ui Chat Context

This project uses assistant-ui for chat interfaces. Treat this as mandatory
context whenever planning, reviewing, or implementing chat UI.

- Documentation entry point:
  `https://www.assistant-ui.com/llms-full.txt`
- Approved decision boundary:
  `.omx/decisions/SDAR-0009-student-chatbox-product-polish.md`
- Current implementation:
  `frontend/src/StudentChatboxPage.tsx`
- Use `AssistantRuntimeProvider` at the app root or chat feature root so
  assistant-ui primitives and hooks share the same runtime context.
- Use assistant-ui `Thread` / `ThreadPrimitive` patterns for full chat
  interfaces.
- Use `AssistantModal` / `AssistantModalPrimitive` patterns for floating chat
  widgets.
- For future AI SDK compatible transports, use `useChatRuntime` with an AI SDK
  transport such as `AssistantChatTransport`, but do not add packages or change
  transport/API boundaries without product-manager approval.
- Preserve the approved security and product boundary: browser UI must not call
  model providers directly, expose API keys, imply unapproved models, enable web
  search, RAG, attachments, real school data, or persistence without separate
  approval.

## Approval Gates

Pause for product-manager approval before making decisions that affect long-term
product direction, architecture, dependencies, data contracts, API boundaries,
database schema, persistence, model providers, web search, RAG/vector/embedding
pipelines, real school resources, real student data, production SSO, deployment,
security boundaries, secret handling, audit/privacy policy, or broad refactors.

## Delivery Records

When a task changes project state, architecture, workflow, or acceptance status,
update the relevant `.omx` artifact or project document so the decision is not
stored only in chat history.

Changes to the workflow itself must be approved through a new SDAR or explicit
process revision record.
