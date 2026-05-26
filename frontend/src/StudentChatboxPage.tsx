import { useCallback, useEffect, useRef, useState } from 'react'
import type { AppendMessage, MessageStatus, ThreadMessageLike } from '@assistant-ui/react'
import {
  ActionBarPrimitive,
  AssistantRuntimeProvider,
  AuiIf,
  ComposerPrimitive,
  MessagePartPrimitive,
  MessagePrimitive,
  ThreadListItemPrimitive,
  ThreadListPrimitive,
  ThreadPrimitive,
  useAuiState,
  useExternalStoreRuntime,
} from '@assistant-ui/react'
import gsap from 'gsap'
import { useGSAP } from '@gsap/react'
import { Navigate, useNavigate } from 'react-router-dom'

type StudentChatboxPageProps = {
  apiBase: string
  session: {
    token: string
    user: {
      displayName: string
      role: string
    }
  } | null
}

type ApiMessage = {
  id: string
  role: 'student' | 'assistant'
  content: string
  created_at: string
}

type ApiConversation = {
  id: string
  title: string
  messages: ApiMessage[]
  updated_at: string
}

type ChatMessage = {
  id: string
  role: 'student' | 'assistant'
  content: string
  createdAt?: string
  status?: MessageStatus
}

type StreamStatus = 'idle' | 'loading' | 'streaming' | 'error' | 'stopped'

type StreamEvent = {
  event: string
  data: Record<string, string>
}

const promptStarters = [
  '我最近学习压力很大，应该怎么调整？',
  '我和室友发生矛盾，不知道怎么开口沟通。',
  '我错过了一次作业截止时间，应该怎么补救？',
]

const assistantDisplayName = 'AI 咨询助手'

export default function StudentChatboxPage({ apiBase, session }: StudentChatboxPageProps) {
  const navigate = useNavigate()
  const pageRef = useRef<HTMLElement | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const initialHistoryLoadedRef = useRef(false)
  const [conversations, setConversations] = useState<ApiConversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [status, setStatus] = useState<StreamStatus>('idle')
  const [error, setError] = useState('')
  const [lastPrompt, setLastPrompt] = useState('')

  const token = session?.token ?? ''
  const activeConversation = conversations.find((item) => item.id === activeConversationId)
  const isBusy = status === 'loading' || status === 'streaming'
  const canRetry = Boolean(lastPrompt) && !isBusy

  const appendAssistantChunk = useCallback((messageId: string, chunk: string) => {
    if (!chunk) {
      return
    }
    setMessages((current) =>
      current.map((message) =>
        message.id === messageId
          ? {
              ...message,
              content: `${message.content === '正在连接咨询助手...' ? '' : message.content}${chunk}`,
            }
          : message,
      ),
    )
  }, [])

  const markAssistantStatus = useCallback((messageId: string, nextStatus: MessageStatus) => {
    setMessages((current) =>
      current.map((message) =>
        message.id === messageId ? { ...message, status: nextStatus } : message,
      ),
    )
  }, [])

  const refreshConversations = useCallback(
    async (conversationId: string | null) => {
      if (!token) {
        return
      }
      const items = await loadConversations(apiBase, token)
      setConversations(items)
      if (conversationId) {
        const refreshed = items.find((item) => item.id === conversationId)
        if (refreshed) {
          setMessages(refreshed.messages.map(toChatMessage))
        }
      }
    },
    [apiBase, token],
  )

  const startNewChat = useCallback(() => {
    abortRef.current?.abort()
    setActiveConversationId(null)
    setMessages([])
    setError('')
    setLastPrompt('')
    setStatus('idle')
  }, [])

  const selectConversationById = useCallback(
    (conversationId: string) => {
      if (isBusy) {
        return
      }
      const conversation = conversations.find((item) => item.id === conversationId)
      if (!conversation) {
        return
      }
      setActiveConversationId(conversation.id)
      setMessages(conversation.messages.map(toChatMessage))
      setError('')
      setStatus('idle')
    },
    [conversations, isBusy],
  )

  const sendMessage = useCallback(
    async (promptOverride: string, conversationOverride?: string | null) => {
      const prompt = promptOverride.trim()
      if (!prompt || isBusy || !token) {
        return
      }

      setMessages((current) => current.filter((message) => message.content.trim() !== ''))

      const controller = new AbortController()
      const stamp = Date.now()
      const studentId = `pending-student-${stamp}`
      const assistantId = `pending-assistant-${stamp}`
      const conversationId = conversationOverride ?? activeConversationId
      abortRef.current = controller
      setError('')
      setLastPrompt(prompt)
      setStatus('loading')
      setMessages((current) => [
        ...current,
        { id: studentId, role: 'student', content: prompt },
        {
          id: assistantId,
          role: 'assistant',
          content: '正在连接咨询助手...',
          status: { type: 'running' },
        },
      ])

      try {
        const response = await fetch(`${apiBase}/api/v1/student/chat/stream`, {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            conversationId,
            message: prompt,
          }),
          signal: controller.signal,
        })

        if (!response.ok) {
          const detail = await response.json().catch(() => ({ detail: '模型接口调用失败' }))
          throw new Error(detail.detail ?? '模型接口调用失败')
        }

        if (!response.body) {
          throw new Error('当前浏览器不支持流式响应读取')
        }

        setStatus('streaming')
        setMessages((current) =>
          current.map((message) =>
            message.id === assistantId ? { ...message, content: '' } : message,
          ),
        )

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let streamedConversationId = conversationId

        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            break
          }

          buffer += decoder.decode(value, { stream: true })
          const parsed = drainSseEvents(buffer)
          buffer = parsed.rest

          for (const event of parsed.events) {
            if (event.event === 'conversation') {
              streamedConversationId = event.data.conversationId ?? streamedConversationId
              setActiveConversationId(streamedConversationId ?? null)
            }
            if (event.event === 'delta') {
              appendAssistantChunk(assistantId, event.data.content ?? '')
            }
            if (event.event === 'error') {
              throw new Error(event.data.detail ?? '模型生成失败')
            }
          }
        }

        markAssistantStatus(assistantId, { type: 'complete', reason: 'stop' })
        setStatus('idle')
        await refreshConversations(streamedConversationId ?? null)
      } catch (sendError) {
        if (sendError instanceof DOMException && sendError.name === 'AbortError') {
          markAssistantStatus(assistantId, { type: 'incomplete', reason: 'cancelled' })
          setStatus('stopped')
          return
        }
        const message = sendError instanceof Error ? sendError.message : '模型生成失败'
        setStatus('error')
        setError(message)
        markAssistantStatus(assistantId, {
          type: 'incomplete',
          reason: 'error',
          error: message,
        })
      } finally {
        if (abortRef.current === controller) {
          abortRef.current = null
        }
      }
    },
    [
      activeConversationId,
      apiBase,
      appendAssistantChunk,
      isBusy,
      markAssistantStatus,
      refreshConversations,
      token,
    ],
  )

  const stopStreaming = useCallback(async () => {
    abortRef.current?.abort()
  }, [])

  const retryLastPrompt = useCallback(async () => {
    if (!lastPrompt) {
      return
    }
    await sendMessage(lastPrompt, activeConversationId)
  }, [activeConversationId, lastPrompt, sendMessage])

  const runtime = useExternalStoreRuntime<ChatMessage>({
    messages,
    convertMessage: toAssistantMessage,
    isRunning: isBusy,
    isSendDisabled: !token || isBusy,
    suggestions: messages.length === 0 ? promptStarters.map((prompt) => ({ prompt })) : [],
    onNew: async (message) => {
      await sendMessage(getAppendMessageText(message), activeConversationId)
    },
    onCancel: stopStreaming,
    onReload: async () => {
      await retryLastPrompt()
    },
    adapters: {
      threadList: {
        threadId: activeConversationId ?? 'new',
        threads: conversations.map((conversation) => ({
          id: conversation.id,
          title: conversation.title || '未命名会话',
          status: 'regular' as const,
        })),
        onSwitchToNewThread: startNewChat,
        onSwitchToThread: selectConversationById,
      },
    },
  })

  useEffect(() => {
    if (!token) {
      initialHistoryLoadedRef.current = false
      return
    }
    let ignore = false
    void loadConversations(apiBase, token)
      .then((items) => {
        if (ignore) {
          return
        }
        setConversations(items)
        if (!initialHistoryLoadedRef.current && items.length > 0) {
          initialHistoryLoadedRef.current = true
          const first = items[0]
          setActiveConversationId(first.id)
          setMessages(first.messages.map(toChatMessage))
          return
        }
        initialHistoryLoadedRef.current = true
      })
      .catch((loadError: unknown) => {
        if (ignore) {
          return
        }
        const message = loadError instanceof Error ? loadError.message : '聊天记录读取失败'
        setError(message)
      })
    return () => {
      ignore = true
    }
  }, [apiBase, token])

  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  useGSAP(
    () => {
      const mm = gsap.matchMedia()
      mm.add(
        {
          reduceMotion: '(prefers-reduced-motion: reduce)',
        },
        (context) => {
          const { reduceMotion } = context.conditions as { reduceMotion: boolean }
          if (reduceMotion) {
            gsap.set('.conversation-rail, .chat-workspace, .chat-composer-panel', {
              clearProps: 'all',
            })
            return undefined
          }
          const timeline = gsap.timeline({ defaults: { duration: 0.36, ease: 'power3.out' } })
          timeline
            .from('.conversation-rail', { x: -18, autoAlpha: 0 })
            .from('.chat-workspace', { y: 16, autoAlpha: 0 }, '<0.08')
            .from('.chat-composer-panel', { y: 12, autoAlpha: 0 }, '<0.08')
          return undefined
        },
      )
      return () => mm.revert()
    },
    { scope: pageRef },
  )

  useGSAP(
    () => {
      const root = pageRef.current
      if (!root || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return
      }
      const items = root.querySelectorAll('.chat-message')
      const lastItem = items[items.length - 1]
      if (!lastItem) {
        return
      }
      gsap.fromTo(
        lastItem,
        { y: 10, autoAlpha: 0 },
        { y: 0, autoAlpha: 1, duration: 0.22, ease: 'power2.out' },
      )
    },
    { dependencies: [messages.length], scope: pageRef },
  )

  if (!session) {
    return <Navigate to="/login" replace />
  }

  if (session.user.role !== 'student') {
    return <Navigate to="/app" replace />
  }

  return (
    <main className="student-chat-page" ref={pageRef}>
      <AssistantRuntimeProvider runtime={runtime}>
        <section className="chat-shell" aria-label="学生 AI 咨询助手">
          <ThreadListPrimitive.Root className="conversation-rail" aria-label="会话记录">
            <div className="rail-header">
              <button className="rail-back-button" onClick={() => navigate('/app/student')} type="button">
                <span aria-hidden="true">←</span>
                学生工作台
              </button>
              <div>
                <span className="rail-eyebrow">会话记录</span>
                <h1>{assistantDisplayName}</h1>
              </div>
              <ThreadListPrimitive.New className="new-thread-button">
                <span aria-hidden="true">＋</span>
                新会话
              </ThreadListPrimitive.New>
            </div>

            <div className="rail-model-card" aria-label="当前模型">
              <span>当前模型</span>
              <strong>Qwen</strong>
            </div>

            <div className="conversation-list">
              {conversations.length === 0 ? (
                <div className="conversation-empty">还没有保存的会话，发送第一条消息后会自动出现在这里。</div>
              ) : (
                <ThreadListPrimitive.Items>
                  {({ threadListItem }) => {
                    const conversation = conversations.find((item) => item.id === threadListItem.id)
                    return (
                      <ThreadListItemPrimitive.Root className="conversation-item">
                        <ThreadListItemPrimitive.Trigger className="conversation-item-trigger">
                          <span className="conversation-item-title">
                            <ThreadListItemPrimitive.Title
                              fallback={conversation?.title || '未命名会话'}
                            />
                          </span>
                          <span className="conversation-item-meta">
                            {conversation ? `${conversation.messages.length} 条消息` : '继续会话'}
                          </span>
                        </ThreadListItemPrimitive.Trigger>
                      </ThreadListItemPrimitive.Root>
                    )
                  }}
                </ThreadListPrimitive.Items>
              )}
            </div>
          </ThreadListPrimitive.Root>

          <ThreadPrimitive.Root className="chat-workspace">
            <div className="chat-topbar">
              <div className="chat-title-block">
                <span className="chat-kicker">学生端咨询</span>
                <h2>{activeConversation?.title ?? '新会话'}</h2>
              </div>
              <div className="chat-topbar-actions">
                <span className={`chat-status-pill ${status}`}>{statusLabel(status)}</span>
                <button
                  className="chat-text-button"
                  disabled={!canRetry}
                  onClick={() => void retryLastPrompt()}
                  type="button"
                >
                  重试
                </button>
              </div>
            </div>

            {error ? (
              <div className="chat-error" role="alert">
                <div>
                  <strong>回复没有完成</strong>
                  <span>{error}</span>
                </div>
                <button disabled={!canRetry} onClick={() => void retryLastPrompt()} type="button">
                  重新发送
                </button>
              </div>
            ) : null}

            <ThreadPrimitive.Viewport className="message-list" turnAnchor="bottom">
              <ThreadPrimitive.Empty>
                <div className="chat-empty-state">
                  <span className="empty-mark" aria-hidden="true">
                    ✦
                  </span>
                  <h3>今天想先聊哪件事？</h3>
                  <p>
                    可以从学习压力、沟通困扰、作业安排或校园资源开始。回复由 AI 生成，重要事项请联系辅导员确认。
                  </p>
                  <div className="prompt-starters">
                    {promptStarters.map((prompt) => (
                      <ThreadPrimitive.Suggestion
                        className="prompt-starter"
                        key={prompt}
                        prompt={prompt}
                      />
                    ))}
                  </div>
                </div>
              </ThreadPrimitive.Empty>

              <div className="message-stack" aria-live="polite">
                <ThreadPrimitive.Messages>
                  {({ message }) => <ChatMessageItem role={message.role} />}
                </ThreadPrimitive.Messages>
              </div>

              <ThreadPrimitive.ScrollToBottom className="scroll-to-bottom-button">
                回到底部
              </ThreadPrimitive.ScrollToBottom>
            </ThreadPrimitive.Viewport>

            <div className="chat-composer-panel">
              <ComposerPrimitive.Root className="composer-form">
                <ComposerPrimitive.Input
                  addAttachmentOnPaste={false}
                  aria-label="输入咨询内容"
                  autoFocus
                  className="composer-input"
                  maxRows={6}
                  minRows={1}
                  placeholder="输入你想讨论的问题..."
                  submitMode="enter"
                  unstable_insertNewlineOnTouchEnter
                />
                <div className="composer-footer">
                  <span>Enter 发送，Shift + Enter 换行</span>
                  <div className="composer-actions">
                    <AuiIf condition={(state) => state.thread.isRunning}>
                      <ComposerPrimitive.Cancel className="composer-stop-button">
                        停止
                      </ComposerPrimitive.Cancel>
                    </AuiIf>
                    <AuiIf condition={(state) => !state.thread.isRunning}>
                      <ComposerPrimitive.Send className="composer-send-button">
                        发送
                      </ComposerPrimitive.Send>
                    </AuiIf>
                  </div>
                </div>
              </ComposerPrimitive.Root>
            </div>
          </ThreadPrimitive.Root>
        </section>
      </AssistantRuntimeProvider>
    </main>
  )
}

function ChatMessageItem({ role }: { role: 'assistant' | 'user' | 'system' }) {
  const isAssistant = role === 'assistant'
  const isRunning = useAuiState((state) => state.message.status?.type === 'running')

  if (role === 'system') {
    return null
  }

  return (
    <MessagePrimitive.Root className={`chat-message ${isAssistant ? 'assistant' : 'student'}`}>
      <div className="message-avatar" aria-hidden="true">
        {isAssistant ? 'AI' : '我'}
      </div>
      <div className="message-content">
        <div className="message-heading">
          <span>{isAssistant ? assistantDisplayName : '你'}</span>
          {isRunning ? <small>正在回复</small> : null}
        </div>
        <div className="message-bubble">
          <MessagePrimitive.Parts
            components={{
              Text: () => (
                <MessagePartPrimitive.Text
                  className="message-text"
                  component="p"
                  smooth={isAssistant}
                />
              ),
            }}
          />
          <ActionBarPrimitive.Root
            autohide="not-last"
            className="message-actions"
            hideWhenRunning
          >
            <ActionBarPrimitive.Copy className="message-action-button">
              复制
            </ActionBarPrimitive.Copy>
            <ActionBarPrimitive.Reload className="message-action-button">
              重试
            </ActionBarPrimitive.Reload>
          </ActionBarPrimitive.Root>
        </div>
      </div>
    </MessagePrimitive.Root>
  )
}

async function loadConversations(apiBase: string, token: string): Promise<ApiConversation[]> {
  const response = await fetch(`${apiBase}/api/v1/student/conversations`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: '聊天记录读取失败' }))
    throw new Error(detail.detail ?? '聊天记录读取失败')
  }
  return response.json() as Promise<ApiConversation[]>
}

function toChatMessage(message: ApiMessage): ChatMessage {
  return {
    id: message.id,
    role: message.role,
    content: message.content,
    createdAt: message.created_at,
    status:
      message.role === 'assistant'
        ? {
            type: 'complete',
            reason: 'stop',
          }
        : undefined,
  }
}

function toAssistantMessage(message: ChatMessage): ThreadMessageLike {
  return {
    id: message.id,
    role: message.role === 'student' ? 'user' : 'assistant',
    content:
      message.role === 'assistant'
        ? [{ type: 'text', text: message.content || '正在回复...' }]
        : message.content,
    createdAt: message.createdAt ? new Date(message.createdAt) : undefined,
    status: message.role === 'assistant' ? message.status ?? { type: 'complete', reason: 'stop' } : undefined,
  }
}

function getAppendMessageText(message: AppendMessage): string {
  return message.content
    .filter((part): part is { type: 'text'; text: string } => part.type === 'text')
    .map((part) => part.text)
    .join('\n\n')
    .trim()
}

function drainSseEvents(buffer: string): { events: StreamEvent[]; rest: string } {
  const normalized = buffer.replace(/\r\n/g, '\n')
  const parts = normalized.split('\n\n')
  const rest = parts.pop() ?? ''
  const events = parts.flatMap(parseSseEvent)
  return { events, rest }
}

function parseSseEvent(block: string): StreamEvent[] {
  const lines = block.split('\n')
  let event = 'message'
  const dataLines: string[] = []

  for (const line of lines) {
    if (line.startsWith('event:')) {
      event = line.slice(6).trim()
    }
    if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim())
    }
  }

  if (dataLines.length === 0) {
    return []
  }

  try {
    return [{ event, data: JSON.parse(dataLines.join('\n')) as Record<string, string> }]
  } catch {
    return []
  }
}

function statusLabel(status: StreamStatus): string {
  if (status === 'loading') {
    return '连接中'
  }
  if (status === 'streaming') {
    return '正在回复'
  }
  if (status === 'error') {
    return '需要重试'
  }
  if (status === 'stopped') {
    return '已停止'
  }
  return '就绪'
}
