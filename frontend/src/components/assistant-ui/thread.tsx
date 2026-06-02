import { useEffect, useMemo, useRef, useState } from "react"
import { AuiIf, ComposerPrimitive, MessagePartPrimitive, MessagePrimitive, ThreadPrimitive, useAuiState } from "@assistant-ui/react"
import { Actions, Sources, Think, ThoughtChain, XProvider } from "@ant-design/x"
import type { ThoughtChainItemType } from "@ant-design/x"
import {
  AlertCircle,
  BrainCircuit,
  Check,
  Circle,
  Copy,
  FileText,
  Globe2,
  Loader2,
  Paperclip,
  Plus,
  Search,
  SlidersHorizontal,
  StopCircle,
  SquareTerminal,
  X,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { MarkdownText } from "@/components/assistant-ui/markdown-text"
import type {
  ChatRunState,
  ChatRunTool,
  ChatRunToolStatus,
  ChatRunWorkflowArtifact,
  ChatRunWorkflowStatus,
  ChatRunWorkflowStep,
} from "@/lib/chat-run"
import type { StudentChatAttachmentPayload } from "@/lib/chat-attachments"
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
  messageAttachments: Record<string, StudentChatAttachmentPayload[]>
  messageContents: Record<string, string>
  messageRuns: Record<string, ChatRunState | undefined>
  mobileSidebarTrigger?: React.ReactNode
  onAttachmentsAdd: (attachments: StudentChatAttachmentPayload[]) => void
  onAttachmentRemove: (attachmentId: string) => void
  onChatModeChange: (mode: StudentChatMode) => void
  onReasoningChange: (enabled: boolean) => void
  onRetry: () => void
  onWebSearchChange: (enabled: boolean) => void
  pendingAttachments: StudentChatAttachmentPayload[]
  promptStarters: string[]
  reasoningEnabled: boolean
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
  messageAttachments,
  messageContents,
  messageRuns,
  mobileSidebarTrigger,
  onAttachmentsAdd,
  onAttachmentRemove,
  onChatModeChange,
  onReasoningChange,
  onRetry,
  onWebSearchChange,
  pendingAttachments,
  promptStarters,
  reasoningEnabled,
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
          <span className="aui-model-pill" aria-label="当前模型 Qwen 3.7">
            Qwen 3.7
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
                attachments={messageAttachments[message.id] ?? []}
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
            attachments={pendingAttachments}
            chatMode={chatMode}
            onAttachmentRemove={onAttachmentRemove}
            onAttachmentsAdd={onAttachmentsAdd}
            onChatModeChange={onChatModeChange}
            onReasoningChange={onReasoningChange}
            onWebSearchChange={onWebSearchChange}
            reasoningEnabled={reasoningEnabled}
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
      <h3>有什么可以帮你？</h3>
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
  attachments,
  content,
  onRetry,
  role,
  run,
}: {
  assistantName: string
  attachments: StudentChatAttachmentPayload[]
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
        {!isAssistant && attachments.length > 0 ? (
          <MessageAttachmentList attachments={attachments} />
        ) : null}
        <div className="aui-message-content">
          {isAssistant ? (
            <MarkdownText content={content} isStreaming={isRunning} smooth={false} />
          ) : (
            <MessagePrimitive.Parts
              components={{
                Text: () => (
                  <MessagePartPrimitive.Text
                    className="aui-user-message-text"
                    component="p"
                    smooth={false}
                  />
                ),
              }}
            />
          )}
        </div>
      </div>
    </MessagePrimitive.Root>
  )
}

function MessageAttachmentList({ attachments }: { attachments: StudentChatAttachmentPayload[] }) {
  return (
    <div className="aui-message-attachments" aria-label="本轮引用文件">
      {attachments.map((attachment) => (
        <div
          className={cn("aui-message-attachment", attachment.error ? "error" : "ready")}
          key={attachment.id}
          title={attachment.error ?? attachment.name}
        >
          <FileText aria-hidden="true" />
          <span>{attachment.name}</span>
          <small>{formatBytes(attachment.size)}</small>
        </div>
      ))}
    </div>
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
  const workflowSteps = useProgressiveWorkflowSteps(
    run ? buildWorkflowSteps(run, isRunning) : [],
    run?.runId ?? run?.messageId ?? "current-run",
  )
  if (!run) {
    return null
  }
  const activeStep =
    workflowSteps.find((step) => step.status === "running") ??
    [...workflowSteps].reverse().find((step) => step.status !== "queued")
  const thoughtItems = workflowSteps.map((step) =>
    workflowStepToThoughtItem(
      step,
      run.workflowArtifacts.filter((artifact) => artifact.stepId === step.id),
    ),
  )
  const canCopy = text.trim().length > 0

  return (
    <XProvider>
      <div className="aui-run-panel" data-terminal-status={run.terminalStatus}>
        <div className="aui-run-header">
          <span>{formatRunHeader(run.terminalStatus)}</span>
          {activeStep ? (
            <small className="aui-current-step-pill">
              {formatCurrentStep(activeStep)}
            </small>
          ) : null}
        </div>

        {thoughtItems.length > 0 ? (
          <div className="aui-process-card" aria-label="回答过程时间线">
            <ThoughtChain
              className="aui-thought-chain"
              defaultExpandedKeys={defaultExpandedWorkflowKeys(workflowSteps, run.workflowArtifacts)}
              items={thoughtItems}
              line="solid"
            />
          </div>
        ) : null}

        {run.reasoning ? (
          <Think
            blink={isRunning && run.terminalStatus === "running"}
            className="aui-run-reasoning"
            defaultExpanded={false}
            loading={isRunning && run.terminalStatus === "running"}
            title={
              <span className="aui-run-reasoning-title">
                <span>思考摘要</span>
                <small>{isRunning && run.terminalStatus === "running" ? "更新中" : "已完成"}</small>
              </span>
            }
          >
            <p>{run.reasoning}</p>
          </Think>
        ) : null}

        {run.sources.length > 0 ? (
          <div className="aui-source-trust-block">
            <Sources
              className="aui-source-section"
              defaultExpanded={false}
              items={run.sources.map((source, index) => ({
                key: source.key || source.url || index,
                title: source.title,
                url: source.url,
                icon: <FileText aria-hidden="true" />,
                description: formatSourceDescription(source),
              }))}
              onClick={(source) => {
                if (source.url) {
                  window.open(source.url, "_blank", "noopener,noreferrer")
                }
              }}
              title={
                <span className="aui-source-title">
                  <Globe2 aria-hidden="true" />
                  公网来源
                </span>
              }
            />
            <p className="aui-source-trust-note">
              仅展示后端确认的公开 http(s) 来源；回答仍由 AI 生成，请以来源原文为准。
            </p>
          </div>
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

function useProgressiveWorkflowSteps(
  steps: ChatRunWorkflowStep[],
  runKey: string,
): ChatRunWorkflowStep[] {
  const displayableSteps = useMemo(() => {
    const activeSteps = steps.filter((step) => step.status !== "queued")
    return activeSteps.length > 0 ? activeSteps : steps.slice(0, 1)
  }, [steps])
  const [revealState, setRevealState] = useState({ runKey: "", visibleCount: 1 })
  const visibleCount =
    displayableSteps.length === 0
      ? 0
      : revealState.runKey === runKey
        ? Math.max(1, revealState.visibleCount)
        : 1

  useEffect(() => {
    if (visibleCount >= displayableSteps.length) {
      return
    }
    const timeout = window.setTimeout(() => {
      setRevealState((current) =>
        current.runKey === runKey
          ? {
              runKey,
              visibleCount: Math.min(current.visibleCount + 1, displayableSteps.length),
            }
          : {
              runKey,
              visibleCount: Math.min(2, displayableSteps.length),
            },
      )
    }, 420)
    return () => window.clearTimeout(timeout)
  }, [displayableSteps.length, runKey, visibleCount])

  return displayableSteps.slice(0, visibleCount)
}

function buildWorkflowSteps(run: ChatRunState, isRunning: boolean): ChatRunWorkflowStep[] {
  const steps =
    run.workflowSteps.length > 0
      ? [...run.workflowSteps]
      : [
          {
            id: "phase",
            kind: "plan",
            title: formatPhase(run.phase ?? (isRunning ? "connecting" : run.terminalStatus)),
            status: runStatusToWorkflowStatus(run.terminalStatus, isRunning),
            detail: run.error,
            artifactCount: undefined,
          },
        ]

  for (const tool of run.tools) {
    if (isSandboxToolCoveredByWorkflow(tool, steps)) {
      continue
    }
    if (steps.some((step) => step.id === tool.id || step.id === `tool-${tool.id}`)) {
      continue
    }
    steps.push({
      id: `tool-${tool.id}`,
      kind: tool.name.includes("search") ? "search" : "tool",
      title: tool.title,
      status: toolStatusToWorkflowStatus(tool.status),
      detail: tool.detail,
      artifactCount: tool.resultCount,
    })
  }

  return steps
}

function isSandboxToolCoveredByWorkflow(
  tool: ChatRunTool,
  steps: ChatRunWorkflowStep[],
): boolean {
  if (tool.name === "read_uploaded_files") {
    return steps.some((step) => step.id === "sandbox-read")
  }
  if (tool.name === "run_terminal") {
    return steps.some((step) => step.id === "sandbox-install" || step.id === "sandbox-run")
  }
  return false
}

function workflowStepToThoughtItem(
  step: ChatRunWorkflowStep,
  artifacts: ChatRunWorkflowArtifact[],
): ThoughtChainItemType {
  const description = step.summary ?? step.detail ?? formatWorkflowStatus(step.status)
  return {
    key: step.id,
    title: (
      <span className="aui-workflow-title">
        <span>{step.title}</span>
        {typeof step.artifactCount === "number" ? (
          <small>{step.artifactCount} 个结果</small>
        ) : null}
      </span>
    ),
    description,
    status: workflowStatusToThoughtStatus(step.status),
    icon: <WorkflowKindIcon kind={step.kind} status={step.status} />,
    collapsible: artifacts.length > 0,
    content: artifacts.length > 0 ? <WorkflowArtifactList artifacts={artifacts} /> : undefined,
    blink: step.status === "running",
  }
}

function WorkflowArtifactList({ artifacts }: { artifacts: ChatRunWorkflowArtifact[] }) {
  return (
    <div className="aui-workflow-artifacts">
      {artifacts.map((artifact) => (
        <details className="aui-workflow-artifact" key={artifact.id} open={artifacts.length === 1}>
          <summary>
            <span>{artifact.title}</span>
            <small>{formatArtifactKind(artifact.kind)}</small>
          </summary>
          <pre>{artifact.content}</pre>
        </details>
      ))}
    </div>
  )
}

function WorkflowKindIcon({
  kind,
  status,
}: {
  kind: string
  status: ChatRunWorkflowStatus
}) {
  if (status === "running") {
    return <Loader2 className="aui-workflow-spin" />
  }
  if (status === "error") {
    return <AlertCircle />
  }
  if (status === "aborted") {
    return <StopCircle />
  }
  if (status === "success") {
    return <Check />
  }
  if (kind === "read" || kind === "file") {
    return <FileText />
  }
  if (kind === "terminal") {
    return <SquareTerminal />
  }
  if (kind === "search") {
    return <Search />
  }
  if (kind === "workspace" || kind === "plan") {
    return <Circle />
  }
  return <Circle />
}

function defaultExpandedWorkflowKeys(
  steps: ChatRunWorkflowStep[],
  artifacts: ChatRunWorkflowArtifact[],
): string[] {
  const artifactStepIds = new Set(artifacts.map((artifact) => artifact.stepId))
  const running = steps.find((step) => step.status === "running")
  if (running) {
    return [running.id]
  }
  const latestWithArtifact = [...steps].reverse().find((step) => artifactStepIds.has(step.id))
  return latestWithArtifact ? [latestWithArtifact.id] : []
}

function runStatusToWorkflowStatus(
  terminalStatus: ChatRunState["terminalStatus"],
  isRunning: boolean,
): ChatRunWorkflowStatus {
  if (terminalStatus === "error") {
    return "error"
  }
  if (terminalStatus === "aborted") {
    return "aborted"
  }
  if (terminalStatus === "done") {
    return "success"
  }
  return isRunning ? "running" : "success"
}

function toolStatusToWorkflowStatus(status: ChatRunToolStatus): ChatRunWorkflowStatus {
  if (status === "error") {
    return "error"
  }
  if (status === "running") {
    return "running"
  }
  if (status === "disabled") {
    return "disabled"
  }
  if (status === "no_results") {
    return "skipped"
  }
  return "success"
}

function workflowStatusToThoughtStatus(
  status: ChatRunWorkflowStatus,
): ThoughtChainItemType["status"] {
  if (status === "running") {
    return "loading"
  }
  if (status === "error") {
    return "error"
  }
  if (status === "aborted") {
    return "abort"
  }
  if (status === "queued") {
    return undefined
  }
  return "success"
}

function formatRunHeader(status: ChatRunState["terminalStatus"]): string {
  if (status === "done") {
    return "AI 咨询助手 · 回答完成"
  }
  if (status === "error") {
    return "AI 咨询助手 · 需要重试"
  }
  if (status === "aborted") {
    return "AI 咨询助手 · 已停止"
  }
  return "AI 咨询助手 · 正在回答"
}

function formatCurrentStep(step: ChatRunWorkflowStep): string {
  if (step.status === "running") {
    return `正在${step.title}`
  }
  return `${step.title} · ${formatWorkflowStatus(step.status)}`
}

function formatWorkflowStatus(status: ChatRunWorkflowStatus): string {
  const labels: Record<ChatRunWorkflowStatus, string> = {
    aborted: "已停止",
    blocked: "已阻止",
    disabled: "未启用",
    error: "失败",
    queued: "等待中",
    running: "执行中",
    skipped: "已跳过",
    success: "已完成",
  }
  return labels[status]
}

function formatArtifactKind(kind: string): string {
  const labels: Record<string, string> = {
    file: "文件",
    summary: "摘要",
    terminal: "终端",
    workspace: "工作区",
  }
  return labels[kind] ?? kind
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

function StudentComposer({
  attachments,
  chatMode,
  onAttachmentRemove,
  onAttachmentsAdd,
  onChatModeChange,
  onReasoningChange,
  onWebSearchChange,
  reasoningEnabled,
  webSearchEnabled,
}: {
  attachments: StudentChatAttachmentPayload[]
  chatMode: StudentChatMode
  onAttachmentRemove: (attachmentId: string) => void
  onAttachmentsAdd: (attachments: StudentChatAttachmentPayload[]) => void
  onChatModeChange: (mode: StudentChatMode) => void
  onReasoningChange: (enabled: boolean) => void
  onWebSearchChange: (enabled: boolean) => void
  reasoningEnabled: boolean
  webSearchEnabled: boolean
}) {
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) {
      return
    }
    const nextAttachments = await Promise.all(Array.from(files).slice(0, 6).map(readAttachmentFile))
    onAttachmentsAdd(nextAttachments)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const uploadButton = (
    <button
      className="aui-composer-file-button"
      onClick={() => fileInputRef.current?.click()}
      title="上传作业或代码文件"
      type="button"
    >
      <Paperclip aria-hidden="true" />
      <span>{attachments.length > 0 ? `${attachments.length} 个附件` : "上传文件"}</span>
    </button>
  )

  return (
    <ComposerPrimitive.Root className="aui-composer" data-slot="aui-composer-root">
      {attachments.length > 0 ? (
        <div className="aui-composer-attachments" aria-label="待发送附件">
          {attachments.map((attachment) => (
            <span
              className={cn("aui-composer-attachment", attachment.error ? "error" : "ready")}
              key={attachment.id}
              title={attachment.error ?? attachment.name}
            >
              <FileText aria-hidden="true" />
              <span>{attachment.name}</span>
              <small>{formatBytes(attachment.size)}</small>
              {attachment.error ? <strong>未读取</strong> : null}
              <button
                aria-label={`移除 ${attachment.name}`}
                onClick={() => onAttachmentRemove(attachment.id)}
                type="button"
              >
                <X aria-hidden="true" />
              </button>
            </span>
          ))}
        </div>
      ) : null}
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
      <div className="aui-composer-toolbar" aria-label="聊天运行控制">
        <div className="aui-composer-controls">
          <button
            className="aui-composer-plus"
            onClick={() => fileInputRef.current?.click()}
            title="上传作业或代码文件"
            type="button"
          >
            <Plus aria-hidden="true" />
            <span className="sr-only">添加</span>
          </button>
          <label className="aui-composer-toggle">
            <input
              checked={reasoningEnabled}
              onChange={(event) => onReasoningChange(event.target.checked)}
              type="checkbox"
            />
            <BrainCircuit aria-hidden="true" />
            <span>思考</span>
            <strong>{reasoningEnabled ? "On" : "Off"}</strong>
          </label>
          <input
            accept=".py,.js,.ts,.tsx,.jsx,.json,.md,.txt,.css,.html,.csv,.yaml,.yml"
            className="sr-only"
            multiple
            onChange={(event) => void handleFiles(event.target.files)}
            ref={fileInputRef}
            type="file"
          />
          <label className="aui-composer-toggle">
            <input
              checked={webSearchEnabled}
              onChange={(event) => onWebSearchChange(event.target.checked)}
              type="checkbox"
            />
            <Search aria-hidden="true" />
            <span>Web search</span>
            <strong>{webSearchEnabled ? "Auto" : "Off"}</strong>
          </label>
          {reasoningEnabled ? (
            <label className="aui-composer-select">
              <SlidersHorizontal aria-hidden="true" />
              <select
                aria-label="聊天模式"
                onChange={(event) => onChatModeChange(event.target.value as StudentChatMode)}
                value={chatMode}
              >
                <option value="balanced">标准</option>
                <option value="focus">深度</option>
                <option value="fast">快速</option>
              </select>
            </label>
          ) : (
            uploadButton
          )}
          {reasoningEnabled ? uploadButton : null}
        </div>
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

const composerAttachmentByteLimit = 64 * 1024

async function readAttachmentFile(file: File): Promise<StudentChatAttachmentPayload> {
  const base = {
    id: makeAttachmentId(),
    name: file.name,
    mimeType: file.type || undefined,
    size: file.size,
    encoding: "text" as const,
  }
  if (file.size > composerAttachmentByteLimit) {
    return {
      ...base,
      error: "文件超过 64KB，本轮会交给后端跳过读取。",
    }
  }
  try {
    return {
      ...base,
      content: await file.text(),
    }
  } catch {
    return {
      ...base,
      error: "浏览器未能读取文件内容。",
    }
  }
}

function makeAttachmentId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID()
  }
  return `attachment-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`
  }
  return `${(value / 1024 / 1024).toFixed(1)} MB`
}
