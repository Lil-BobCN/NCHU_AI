# assistant-ui Chat Context Engineering

Date: 2026-05-27

## User Request

Implant this project context:

```text
## assistant-ui

This project uses assistant-ui for chat interfaces.

Documentation: https://www.assistant-ui.com/llms-full.txt

Key patterns:
- Use AssistantRuntimeProvider at the app root
- Thread component for full chat interface
- AssistantModal for floating chat widget
- useChatRuntime hook with AI SDK transport
```

## Current Project State

- `SDAR-0009` approved assistant-ui as the main frontend chat framework for the
  student Chatbox and future chat pages.
- `frontend/package.json` already includes `@assistant-ui/react`.
- `frontend/src/StudentChatboxPage.tsx` already uses:
  - `AssistantRuntimeProvider`
  - `ThreadPrimitive`
  - `ThreadListPrimitive`
  - `ThreadListItemPrimitive`
  - `ComposerPrimitive`
  - `MessagePrimitive`
  - `ActionBarPrimitive`
  - `useExternalStoreRuntime`
- The existing implementation keeps the approved FastAPI boundary:
  - `GET /api/v1/student/conversations`
  - `POST /api/v1/student/chat/stream`
- The browser does not call model providers directly and does not expose model
  API keys.

## Context Rules For Future Work

1. assistant-ui is the default chat UI/runtime context for project chat surfaces.
2. Read the official assistant-ui LLM documentation before substantial
   assistant-ui changes:

   ```text
   https://www.assistant-ui.com/llms-full.txt
   ```

3. Wrap assistant-ui surfaces with `AssistantRuntimeProvider` at the app root or
   at the chat feature root. The current student Chatbox uses the feature-root
   pattern inside `StudentChatboxPage`.
4. Use assistant-ui `Thread` or `ThreadPrimitive` patterns for full chat
   interfaces.
5. Use `AssistantModal` or `AssistantModalPrimitive` patterns for floating chat
   widgets.
6. For future AI SDK compatible backends, prefer the assistant-ui
   `useChatRuntime` pattern with an AI SDK transport such as
   `AssistantChatTransport`.
7. Treat an AI SDK transport switch as a separate implementation decision if it
   requires new dependencies or API contract changes.

## Approved Boundaries

The assistant-ui context does not approve:

- Browser-side model provider calls.
- Frontend model API keys.
- Unapproved model providers or model selectors.
- Web search.
- RAG/vector/embedding pipelines.
- Real school resources.
- Real student data.
- Attachments or file processing.
- Database persistence.
- Teacher/counselor Chatbox expansion.
- Shared multi-role Chat shell extraction.

Those changes still require product-manager approval under the project workflow.

## Acceptance Criteria For This Context Implant

- Agent entry instructions mention assistant-ui and point to the official docs.
- Project state records assistant-ui as the approved chat UI context.
- `.omx` contains an auditable context snapshot for future turns.
- No frontend runtime code, dependency, API, provider, or persistence change is
  made by this context-only task.
