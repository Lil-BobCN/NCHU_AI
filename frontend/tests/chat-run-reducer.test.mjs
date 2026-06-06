import assert from "node:assert/strict"
import test from "node:test"

import { reduceChatRun } from "../src/lib/chat-run.ts"

test("chat run reducer merges workflow, source, citation, tool, notice, and usage events", () => {
  let run = reduceChatRun(undefined, "run_started", {
    schema_version: "chat.run.v1",
    type: "run_started",
    run_id: "run_1",
    message_id: "msg_1",
    seq: 1,
    payload: { conversationId: "conversation-1", messageId: "msg_1" },
  })

  run = reduceChatRun(run, "workflow_plan", {
    type: "workflow_plan",
    payload: {
      steps: [
        {
          step_id: "request-analyze",
          kind: "plan",
          title: "Understand request",
          status: "queued",
        },
      ],
    },
  })
  run = reduceChatRun(run, "workflow_step_started", {
    type: "workflow_step_started",
    payload: {
      step_id: "request-analyze",
      kind: "plan",
      title: "Understand request",
      status: "running",
      detail: "Checking public-source needs.",
    },
  })
  run = reduceChatRun(run, "tool_started", {
    type: "tool_started",
    payload: {
      toolCallId: "search-1",
      toolName: "web_search",
      title: "Provider web search",
    },
  })
  run = reduceChatRun(run, "source", {
    type: "source",
    payload: {
      sourceId: "source-1",
      dedupeKey: "https://example.edu/notice",
      displayTitle: "Public notice display",
      title: "Public notice",
      url: "https://example.edu/notice",
      snippet: "Public student support notice.",
    },
  })
  run = reduceChatRun(run, "source", {
    type: "source",
    payload: {
      key: "source-1-duplicate",
      dedupeKey: "https://example.edu/notice",
      title: "Duplicate public notice",
      url: "https://example.edu/notice#section",
    },
  })
  run = reduceChatRun(run, "citation", {
    type: "citation",
    payload: {
      citationId: "cite-1",
      marker: "[ref_1]",
      title: "Public notice",
      url: "https://example.edu/notice",
      sourceId: "source-1",
      sourceIndex: 1,
    },
  })
  run = reduceChatRun(run, "notice", {
    type: "notice",
    payload: {
      code: "provider_public_source",
      detail: "Source comes from provider web search.",
    },
  })
  run = reduceChatRun(run, "usage", {
    type: "usage",
    payload: {
      output_chars: 42,
      source_count: 1,
      tool_count: 1,
      elapsed_ms: 123,
    },
  })
  run = reduceChatRun(run, "done", {
    type: "done",
    payload: { conversationId: "conversation-1" },
  })

  assert.equal(run.terminalStatus, "done")
  assert.equal(run.conversationId, "conversation-1")
  assert.equal(run.workflowSteps[0].status, "running")
  assert.equal(run.tools[0].name, "web_search")
  assert.equal(run.sources.length, 1)
  assert.equal(run.sources[0].url, "https://example.edu/notice")
  assert.equal(run.sources[0].sourceId, "source-1")
  assert.equal(run.sources[0].displayTitle, "Public notice display")
  assert.equal(run.sources[0].dedupeKey, "https://example.edu/notice")
  assert.equal(run.citations[0].key, "cite-1")
  assert.equal(run.citations[0].sourceId, "source-1")
  assert.equal(run.citations[0].sourceIndex, 1)
  assert.equal(run.notices[0].code, "provider_public_source")
  assert.deepEqual(run.usage, {
    outputChars: 42,
    sourceCount: 1,
    toolCount: 1,
    elapsedMs: 123,
  })
})

test("chat run reducer keeps 401-style errors local to the run state", () => {
  const run = reduceChatRun(undefined, "error", {
    type: "error",
    payload: { detail: "登录状态已失效，请重新登录后再发送。" },
  })

  assert.equal(run.terminalStatus, "error")
  assert.equal(run.phase, "error")
  assert.equal(run.error, "登录状态已失效，请重新登录后再发送。")
})
