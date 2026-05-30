import { AuiIf, ComposerPrimitive, MessagePartPrimitive, MessagePrimitive, ThreadPrimitive, useAuiState } from "@assistant-ui/react"

import { Button } from "@/components/ui/button"
import { MarkdownText } from "@/components/assistant-ui/markdown-text"
import {
  ChevronDown,
  RefreshCcw,
  SendHorizontal,
  Square,
} from "@/components/assistant-ui/chat-icons"
import { cn } from "@/lib/utils"

export type StudentThreadStatus = "idle" | "loading" | "streaming" | "error" | "stopped"

type StudentAssistantThreadProps = {
  assistantName: string
  canRetry: boolean
  error: string
  mobileSidebarTrigger?: React.ReactNode
  onRetry: () => void
  promptStarters: string[]
  status: StudentThreadStatus
  toolbar?: React.ReactNode
  title: string
}

export function StudentAssistantThread({
  assistantName,
  canRetry,
  error,
  mobileSidebarTrigger,
  onRetry,
  promptStarters,
  status,
  toolbar,
  title,
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
              <StudentMessage role={message.role} assistantName={assistantName} />
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
          <StudentComposer />
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
  role,
}: {
  assistantName: string
  role: "assistant" | "user" | "system"
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

function StudentComposer() {
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
