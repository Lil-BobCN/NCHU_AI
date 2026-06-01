export type ChatRunTerminalStatus = "running" | "done" | "error" | "aborted"

export type ChatRunSource = {
  key: string
  title: string
  url: string
  snippet?: string
  siteName?: string
  publishedAt?: string
}

export type ChatRunToolStatus = "running" | "success" | "error" | "no_results" | "disabled"

export type ChatRunTool = {
  id: string
  name: string
  title: string
  status: ChatRunToolStatus
  detail?: string
  resultCount?: number
}

export type ChatRunNotice = {
  code: string
  detail: string
}

export type ChatRunCitation = {
  key: string
  marker?: string
  title?: string
  url?: string
  sourceIndex?: number
}

export type ChatRunUsage = {
  outputChars?: number
  sourceCount?: number
  toolCount?: number
  elapsedMs?: number
}

export type ChatRunState = {
  runId?: string
  messageId?: string
  conversationId?: string
  seq?: number
  phase?: string
  terminalStatus: ChatRunTerminalStatus
  reasoning: string
  sources: ChatRunSource[]
  citations: ChatRunCitation[]
  tools: ChatRunTool[]
  notices: ChatRunNotice[]
  usage?: ChatRunUsage
  error?: string
}

export type RunEventData = Record<string, unknown> & {
  conversationId?: string
  content?: string
  detail?: string
  payload?: unknown
  type?: string
}

export function reduceChatRun(
  current: ChatRunState | undefined,
  eventName: string,
  data: RunEventData,
): ChatRunState {
  const payload = getRunPayload(data)
  const eventType = readString(data.type) ?? legacyEventType(eventName)
  const next: ChatRunState = {
    terminalStatus: current?.terminalStatus ?? "running",
    reasoning: current?.reasoning ?? "",
    sources: current?.sources ?? [],
    citations: current?.citations ?? [],
    tools: current?.tools ?? [],
    notices: current?.notices ?? [],
    ...current,
    runId: readString(data.run_id) ?? current?.runId,
    messageId: readString(data.message_id) ?? current?.messageId,
    conversationId: readString(data.conversation_id) ?? current?.conversationId,
    seq: readNumber(data.seq) ?? current?.seq,
  }

  if (eventType === "run_started") {
    return {
      ...next,
      conversationId: readString(payload.conversationId) ?? next.conversationId,
      messageId: readString(payload.messageId) ?? next.messageId,
      terminalStatus: "running",
    }
  }

  if (eventType === "phase") {
    return {
      ...next,
      phase: readString(payload.phase) ?? next.phase,
      terminalStatus: next.terminalStatus === "running" ? "running" : next.terminalStatus,
    }
  }

  if (
    eventType === "reasoning_summary_delta" ||
    eventType === "reasoning_summary" ||
    eventType === "reasoning"
  ) {
    const content = readString(payload.content)
    return content ? { ...next, reasoning: `${next.reasoning}${content}` } : next
  }

  if (eventType === "source") {
    const source = sourceFromPayload(payload)
    if (!source || next.sources.some((item) => item.url === source.url)) {
      return next
    }
    return { ...next, sources: [...next.sources, source] }
  }

  if (eventType === "citation") {
    const citation = citationFromPayload(payload)
    if (!citation || next.citations.some((item) => item.key === citation.key)) {
      return next
    }
    return { ...next, citations: [...next.citations, citation] }
  }

  if (eventType === "tool_started") {
    const tool = toolFromPayload(payload, "running")
    return tool ? { ...next, tools: upsertTool(next.tools, tool) } : next
  }

  if (eventType === "tool_delta") {
    const tool = toolFromPayload(payload, "running")
    return tool ? { ...next, tools: upsertTool(next.tools, tool, true) } : next
  }

  if (eventType === "tool_done") {
    const tool = toolFromPayload(payload, normalizeToolStatus(readString(payload.status)))
    return tool ? { ...next, tools: upsertTool(next.tools, tool) } : next
  }

  if (eventType === "notice") {
    const notice = noticeFromPayload(payload)
    if (!notice) {
      return next
    }
    const exists = next.notices.some(
      (item) => item.code === notice.code && item.detail === notice.detail,
    )
    return exists ? next : { ...next, notices: [...next.notices, notice] }
  }

  if (eventType === "error") {
    return {
      ...next,
      terminalStatus: "error",
      phase: "error",
      error: readString(payload.detail) ?? next.error,
    }
  }

  if (eventType === "usage") {
    return {
      ...next,
      usage: {
        outputChars: readNumber(payload.output_chars),
        sourceCount: readNumber(payload.source_count),
        toolCount: readNumber(payload.tool_count),
        elapsedMs: readNumber(payload.elapsed_ms),
      },
    }
  }

  if (eventType === "aborted") {
    return {
      ...next,
      terminalStatus: "aborted",
      phase: "aborted",
      error: readString(payload.detail) ?? next.error,
    }
  }

  if (eventType === "done") {
    return {
      ...next,
      terminalStatus: "done",
      phase: "done",
      conversationId: readString(payload.conversationId) ?? next.conversationId,
    }
  }

  return next
}

export function getRunPayload(data: RunEventData): RunEventData {
  return isRecord(data.payload) ? data.payload : data
}

export function readString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined
}

function readNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined
}

function legacyEventType(eventName: string): string {
  if (eventName === "delta") {
    return "answer_delta"
  }
  if (eventName === "reasoning") {
    return "reasoning_summary_delta"
  }
  return eventName
}

function sourceFromPayload(payload: RunEventData): ChatRunSource | undefined {
  const url = readString(payload.url)
  if (!url) {
    return undefined
  }
  return {
    key: readString(payload.sourceId) ?? readString(payload.source_id) ?? readString(payload.key) ?? url,
    title: readString(payload.title) ?? url,
    url,
    snippet: readString(payload.snippet),
    siteName: readString(payload.siteName),
    publishedAt: readString(payload.publishedAt),
  }
}

function citationFromPayload(payload: RunEventData): ChatRunCitation | undefined {
  const marker = readString(payload.marker)
  const url = readString(payload.url)
  const sourceIndex = readNumber(payload.sourceIndex) ?? readNumber(payload.source_index)
  const key =
    readString(payload.citationId) ??
    readString(payload.citation_id) ??
    marker ??
    url ??
    (sourceIndex !== undefined ? `source-${sourceIndex}` : undefined)
  if (!key) {
    return undefined
  }
  return {
    key,
    marker,
    title: readString(payload.title),
    url,
    sourceIndex,
  }
}

function toolFromPayload(
  payload: RunEventData,
  status: ChatRunToolStatus,
): ChatRunTool | undefined {
  const id = readString(payload.toolCallId) ?? readString(payload.tool_call_id)
  const name = readString(payload.toolName) ?? readString(payload.tool_name)
  if (!id || !name) {
    return undefined
  }
  return {
    id,
    name,
    title: readString(payload.title) ?? formatToken(name),
    status,
    detail: readString(payload.detail),
    resultCount: readNumber(payload.resultCount),
  }
}

function noticeFromPayload(payload: RunEventData): ChatRunNotice | undefined {
  const code = readString(payload.code)
  const detail = readString(payload.detail)
  return code && detail ? { code, detail } : undefined
}

function upsertTool(
  tools: ChatRunTool[],
  tool: ChatRunTool,
  appendDetail = false,
): ChatRunTool[] {
  const index = tools.findIndex((item) => item.id === tool.id)
  if (index === -1) {
    return [...tools, tool]
  }
  const existing = tools[index]
  const nextDetail =
    appendDetail && existing.detail && tool.detail
      ? `${existing.detail}\n${tool.detail}`
      : tool.detail ?? existing.detail
  return tools.map((item) =>
    item.id === tool.id
      ? {
          ...item,
          ...tool,
          detail: nextDetail,
        }
      : item,
  )
}

function normalizeToolStatus(status: string | undefined): ChatRunToolStatus {
  if (status === "success" || status === "error" || status === "disabled") {
    return status
  }
  if (status === "no_results") {
    return status
  }
  return "success"
}

function formatToken(value: string): string {
  return value
    .split(/[_-]/)
    .filter(Boolean)
    .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1)}`)
    .join(" ")
}

function isRecord(value: unknown): value is RunEventData {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}
