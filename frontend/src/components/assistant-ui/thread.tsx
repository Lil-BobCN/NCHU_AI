import { AuiIf, ComposerPrimitive, MessagePartPrimitive, MessagePrimitive, ThreadPrimitive, useAuiState } from "@assistant-ui/react"
import { Actions, Sources, Think, ThoughtChain, XProvider } from "@ant-design/x"
import type { ThoughtChainItemType } from "@ant-design/x"
import { Copy, Paperclip, Search, SlidersHorizontal } from "lucide-react"

import { Button } from "@/components/ui/button"
import { MarkdownText } from "@/components/assistant-ui/markdown-text"
import type { ChatRunState, ChatRunToolStatus } from "@/lib/chat-run"
import {
  ChevronDown,
  RefreshCcw,
  SendHorizontal,
  Square,
} from "@/components/assistant-ui/chat-icons"
import { cn } from "@/lib/utils"

export type StudentThreadStatus = "idle" | "loading" | "streaming" | "error" | "stopped"
export type StudentChatMode = "balanced" | "focus" | "fast"

type StudentAssistantThreadProps = {
  assistantName: string
  canRetry: boolean
  chatMode: StudentChatMode
  error: string
  messageContents: Record<string, string>
  messageRuns: Record<string, ChatRunState | undefined>
  mobileSidebarTrigger?: React.ReactNode
  onChatModeChange: (mode: StudentChatMode) => void
  onRetry: () => void
  onWebSearchChange: (enabled: boolean) => void
  promptStarters: string[]
  status: StudentThreadStatus
  toolbar?: React.ReactNode
  title: string
  webSearchEnabled: boolean
}

export function StudentAssistantThread({
  assistantName,
  canRetry,
  chatMode,
  error,
  messageContents,
  messageRuns,
  mobileSidebarTrigger,
  onChatModeChange,
  onRetry,
  onWebSearchChange,
  promptStarters,
  status,
  toolbar,
  title,
  webSearchEnabled,
}: StudentAssistantThreadProps) {
  const showStatus = status !== "idle"
  const showRetry = canRetry && (status === "error" || status === "stopped")

  return (
    <ThreadPrimitive.Root className="aui-thread-root" data-slot="aui-thread-root">
      <header className="aui-thread-header">
        <div className="aui-thread-title-row">
          {mobileSidebarTrigger}
          <div className="aui-thread-title-block">
            <span className="aui-thread-kicker">AI 咨询助手</span>
            <h2>{title}</h2>
          </div>
        </div>
        <div className="aui-thread-header-actions">
          {toolbar}
          <span className="aui-model-pill" aria-label="当前模型 Qwen">
            Qwen
          </span>
          {showStatus ? (
            <button
              aria-live="polite"
              className={cn("aui-status-pill", status)}
              type="button"
              disabled
            >
              {statusLabel(status)}
            </button>
          ) : null}
          {showRetry ? (
            <Button
              className="aui-retry-button"
              onClick={onRetry}
              type="button"
              variant="ghost"
            >
              <RefreshCcw data-icon="inline-start" />
              重试
            </Button>
          ) : null}
        </div>
      </header>

      {error ? (
        <div className="aui-thread-error" role="alert">
          <div>
            <strong>回复没有完成</strong>
            <span>{error}</span>
          </div>
          <Button disabled={!canRetry} onClick={onRetry} type="button" variant="outline">
            重新发送
          </Button>
        </div>
      ) : null}

      <ThreadPrimitive.Viewport
        autoScroll
        className="aui-thread-viewport"
        data-slot="aui-thread-viewport"
        scrollToBottomOnInitialize
        scrollToBottomOnRunStart
        scrollToBottomOnThreadSwitch
        turnAnchor="bottom"
      >
        <ThreadPrimitive.Empty>
          <StudentThreadEmpty promptStarters={promptStarters} />
        </ThreadPrimitive.Empty>

        <div className="aui-message-stack" aria-live="polite" data-slot="aui-message-stack">
          <ThreadPrimitive.Messages>
            {({ message }) => (
              <StudentMessage
                role={message.role}
                assistantName={assistantName}
                content={messageContents[message.id] ?? ""}
                onRetry={onRetry}
                run={messageRuns[message.id]}
              />
            )}
          </ThreadPrimitive.Messages>
        </div>

        <ThreadPrimitive.ScrollToBottom asChild>
          <Button className="aui-scroll-bottom" type="button" variant="secondary">
            <ChevronDown data-icon="inline-start" />
            回到底部
          </Button>
        </ThreadPrimitive.ScrollToBottom>

        <ThreadPrimitive.ViewportFooter className="aui-composer-anchor" data-slot="aui-composer-anchor">
          <StudentComposer
            chatMode={chatMode}
            onChatModeChange={onChatModeChange}
            onWebSearchChange={onWebSearchChange}
            webSearchEnabled={webSearchEnabled}
          />
        </ThreadPrimitive.ViewportFooter>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  )
}

function StudentThreadEmpty({ promptStarters }: { promptStarters: string[] }) {
  return (
    <section className="aui-empty-state" data-slot="aui-thread-empty">
      <h3>今天想先聊哪件事？</h3>
      <p>
        可以从学习压力、沟通困扰、作业安排或校园资源开始。回复由 AI 生成，重要事项请联系辅导员确认。
      </p>
      <div className="aui-prompt-grid">
        {promptStarters.map((prompt) => (
          <ThreadPrimitive.Suggestion
            className="aui-prompt-card"
            key={prompt}
            prompt={prompt}
          >
            {prompt}
          </ThreadPrimitive.Suggestion>
        ))}
      </div>
    </section>
  )
}

function StudentMessage({
  assistantName,
  content,
  onRetry,
  role,
  run,
}: {
  assistantName: string
  content: string
  onRetry: () => void
  role: "assistant" | "user" | "system"
  run?: ChatRunState
}) {
  const isAssistant = role === "assistant"
  const isRunning = useAuiState((state) => state.message.status?.type === "running")

  if (role === "system") {
    return null
  }

  return (
    <MessagePrimitive.Root
      aria-label={isAssistant ? assistantName : "你"}
      className={cn("aui-message", isAssistant ? "assistant" : "student")}
      data-role={role}
      data-slot="aui-message"
    >
      <div className="aui-message-body">
        {isAssistant && isRunning ? (
          <div className="aui-message-label">
            <span>{assistantName}</span>
            <small className="aui-streaming-label">
              <span aria-hidden="true" />
              正在回复
            </small>
          </div>
        ) : null}
        {isAssistant ? (
          <AssistantRunPanel isRunning={isRunning} onRetry={onRetry} run={run} text={content} />
        ) : null}
        <div className="aui-message-content">
          <MessagePrimitive.Parts
            components={{
              Text: () =>
                isAssistant ? (
                  <MarkdownText smooth={false} />
                ) : (
                  <MessagePartPrimitive.Text
                    className="aui-user-message-text"
                    component="p"
                    smooth={false}
                  />
                ),
            }}
          />
        </div>
      </div>
    </MessagePrimitive.Root>
  )
}

function AssistantRunPanel({
  isRunning,
  onRetry,
  run,
  text,
}: {
  isRunning: boolean
  onRetry: () => void
  run?: ChatRunState
  text: string
}) {
  if (!run) {
    return null
  }

  const thoughtItems = buildThoughtItems(run, isRunning)
  const sourceItems = run.sources.map((source, index) => ({
    key: source.key || source.url || index,
    title: source.title,
    url: source.url,
    description: source.snippet ?? source.siteName,
  }))
  const canCopy = text.trim().length > 0

  return (
    <XProvider>
      <div className="aui-run-panel" data-terminal-status={run.terminalStatus}>
      {thoughtItems.length > 0 ? (
        <ThoughtChain
          className="aui-run-chain"
          defaultExpandedKeys={thoughtItems.map((item) => item.key).filter(isString)}
          items={thoughtItems}
          line="dashed"
        />
      ) : null}
      {run.reasoning ? (
        <Think
          className="aui-run-think"
          defaultExpanded={false}
          loading={isRunning && run.terminalStatus === "running"}
          title="思考摘要"
        >
          <p>{run.reasoning}</p>
        </Think>
      ) : null}
      {sourceItems.length > 0 ? (
        <Sources
          className="aui-run-sources"
          defaultExpanded={sourceItems.length <= 2}
          items={sourceItems}
          onClick={(item) => {
            if (item.url) {
              window.open(item.url, "_blank", "noopener,noreferrer")
            }
          }}
          title="来源"
        />
      ) : null}
      {run.citations.length > 0 ? (
        <ul className="aui-run-citations" aria-label="引用">
          {run.citations.map((citation) => (
            <li key={citation.key}>
              <span>{citation.marker ?? "引用"}</span>
              {citation.title ?? citation.url ?? `来源 ${citation.sourceIndex ?? ""}`}
            </li>
          ))}
        </ul>
      ) : null}
      {run.notices.length > 0 ? (
        <ul className="aui-run-notices">
          {run.notices.map((notice) => (
            <li key={`${notice.code}-${notice.detail}`}>{formatNotice(notice.code, notice.detail)}</li>
          ))}
        </ul>
      ) : null}
      {canCopy ? (
        <Actions
          className="aui-run-actions"
          items={[
            {
              key: "copy",
              icon: <Copy aria-hidden="true" />,
              label: "复制",
              onItemClick: () => {
                void navigator.clipboard?.writeText(text)
              },
            },
            {
              key: "retry",
              icon: <RefreshCcw aria-hidden="true" />,
              label: "重试",
              onItemClick: onRetry,
            },
          ]}
        />
      ) : null}
      </div>
    </XProvider>
  )
}

function buildThoughtItems(run: ChatRunState, isRunning: boolean): ThoughtChainItemType[] {
  const status = runStatusToThoughtStatus(run.terminalStatus, isRunning)
  const items: ThoughtChainItemType[] = [
    {
      key: "phase",
      title: formatPhase(run.phase ?? "connecting"),
      description: run.error,
      status,
      blink: isRunning && run.terminalStatus === "running",
    },
  ]

  for (const tool of run.tools) {
    items.push({
      key: tool.id,
      title: tool.title,
      description: tool.detail ?? formatToolStatus(tool.status),
      footer:
        typeof tool.resultCount === "number"
          ? `${tool.resultCount} source${tool.resultCount === 1 ? "" : "s"}`
          : undefined,
      status: toolStatusToThoughtStatus(tool.status),
      collapsible: Boolean(tool.detail),
    })
  }

  return items
}

function runStatusToThoughtStatus(
  terminalStatus: ChatRunState["terminalStatus"],
  isRunning: boolean,
): ThoughtChainItemType["status"] {
  if (terminalStatus === "error") {
    return "error"
  }
  if (terminalStatus === "aborted") {
    return "abort"
  }
  if (terminalStatus === "done") {
    return "success"
  }
  return isRunning ? "loading" : "success"
}

function toolStatusToThoughtStatus(status: ChatRunToolStatus): ThoughtChainItemType["status"] {
  if (status === "error") {
    return "error"
  }
  if (status === "running") {
    return "loading"
  }
  return "success"
}

function formatToolStatus(status: ChatRunToolStatus): string {
  if (status === "no_results") {
    return "已完成，未返回来源"
  }
  return formatPhase(status)
}

function formatPhase(value: string): string {
  const labels: Record<string, string> = {
    aborted: "已停止",
    analyzing: "正在分析",
    connecting: "正在连接",
    disabled: "未接入",
    done: "已完成",
    error: "出错",
    finalizing: "正在收尾",
    generating: "正在生成",
    reading: "正在阅读来源",
    running: "执行中",
    searching: "正在检索",
    success: "已完成",
    thinking: "正在整理",
    web_search: "联网搜索",
  }
  if (labels[value]) {
    return labels[value]
  }
  return value
    .split(/[_-]/)
    .filter(Boolean)
    .map((part) => `${part.slice(0, 1).toUpperCase()}${part.slice(1)}`)
    .join(" ")
}

function formatNotice(code: string, detail: string): string {
  const labels: Record<string, string> = {
    attachments_disabled: "附件读取暂未接入，本轮没有读取文件。",
    no_external_sources: "本轮没有返回外部来源。",
    no_external_tools: "本轮没有执行外部工具。",
  }
  return labels[code] ?? detail
}

function isString(value: unknown): value is string {
  return typeof value === "string"
}

function StudentComposer({
  chatMode,
  onChatModeChange,
  onWebSearchChange,
  webSearchEnabled,
}: {
  chatMode: StudentChatMode
  onChatModeChange: (mode: StudentChatMode) => void
  onWebSearchChange: (enabled: boolean) => void
  webSearchEnabled: boolean
}) {
  return (
    <ComposerPrimitive.Root className="aui-composer" data-slot="aui-composer-root">
      <div className="aui-composer-input-wrap">
        <ComposerPrimitive.Input
          addAttachmentOnPaste={false}
          aria-label="输入咨询内容"
          autoFocus
          className="aui-composer-input"
          maxRows={6}
          minRows={1}
          placeholder="发消息给 AI 咨询助手"
          submitMode="enter"
          unstable_insertNewlineOnTouchEnter
        />
      </div>
      <div className="aui-composer-controls" aria-label="聊天运行控制">
        <label className="aui-composer-toggle">
          <input
            checked={webSearchEnabled}
            onChange={(event) => onWebSearchChange(event.target.checked)}
            type="checkbox"
          />
          <Search aria-hidden="true" />
          <span>联网</span>
        </label>
        <label className="aui-composer-select">
          <SlidersHorizontal aria-hidden="true" />
          <span>模式</span>
          <select
            aria-label="聊天模式"
            onChange={(event) => onChatModeChange(event.target.value as StudentChatMode)}
            value={chatMode}
          >
            <option value="balanced">平衡</option>
            <option value="focus">专注</option>
            <option value="fast">快速</option>
          </select>
        </label>
        <button className="aui-composer-disabled-tool" disabled title="附件读取待接入" type="button">
          <Paperclip aria-hidden="true" />
          <span>附件待接入</span>
        </button>
      </div>
      <div className="aui-composer-footer">
        <span>AI 生成内容仅供参考</span>
        <div className="aui-composer-actions">
          <AuiIf condition={(state) => state.thread.isRunning}>
            <ComposerPrimitive.Cancel asChild>
              <Button
                aria-label="停止生成"
                className="aui-composer-stop"
                size="icon"
                type="button"
                variant="destructive"
              >
                <Square data-icon="inline-start" />
              </Button>
            </ComposerPrimitive.Cancel>
          </AuiIf>
          <AuiIf condition={(state) => !state.thread.isRunning}>
            <ComposerPrimitive.Send asChild>
              <Button aria-label="发送" className="aui-composer-send" size="icon" type="button">
                <SendHorizontal data-icon="inline-start" />
              </Button>
            </ComposerPrimitive.Send>
          </AuiIf>
        </div>
      </div>
    </ComposerPrimitive.Root>
  )
}

function statusLabel(status: StudentThreadStatus): string {
  if (status === "loading") {
    return "连接中"
  }
  if (status === "streaming") {
    return "正在回复"
  }
  if (status === "error") {
    return "需要重试"
  }
  if (status === "stopped") {
    return "已停止"
  }
  return "就绪"
}
