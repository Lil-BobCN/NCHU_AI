import { useCallback, useEffect, useRef, useState } from 'react'
import type { AppendMessage, MessageStatus, ThreadMessageLike } from '@assistant-ui/react'
import { AssistantRuntimeProvider, useExternalStoreRuntime } from '@assistant-ui/react'
import { Navigate, useNavigate } from 'react-router-dom'
import {
  AssistantMobileSidebar,
  AssistantSidebar,
} from '@/components/assistant-ui/assistant-sidebar'
import type { AssistantConversationMeta } from '@/components/assistant-ui/thread-list'
import { getRunPayload, readString, reduceChatRun } from '@/lib/chat-run'
import type { ChatRunState, RunEventData } from '@/lib/chat-run'
import {
  ArrowLeft,
  Moon,
  Plus,
  Sun,
} from '@/components/assistant-ui/chat-icons'
import {
  StudentAssistantThread,
  type StudentChatMode,
} from '@/components/assistant-ui/thread'

type StudentChatboxPageProps = {
  apiBase: string
  onSessionExpired: () => void
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
  run?: ChatRunState
  status?: MessageStatus
}

type StreamStatus = 'idle' | 'loading' | 'streaming' | 'error' | 'stopped'

type ChatTheme = 'light' | 'dark'

type StreamEvent = {
  event: string
  data: RunEventData
}

class ApiRequestError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

const expiredSessionMessage = '登录状态已失效，请重新登录后再发送。'

const promptStarters = [
  '我最近学习压力很大，应该怎么调整？',
  '我和室友发生矛盾，不知道怎么开口沟通。',
  '我错过了一次作业截止时间，应该怎么补救？',
]

const assistantDisplayName = 'AI 咨询助手'

const chatThemeStorageKey = 'nchu-ai-chat-theme'

export default function StudentChatboxPage({
  apiBase,
  onSessionExpired,
  session,
}: StudentChatboxPageProps) {
  const navigate = useNavigate()
  const abortRef = useRef<AbortController | null>(null)
  const initialHistoryLoadedRef = useRef(false)
  const [conversations, setConversations] = useState<ApiConversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [status, setStatus] = useState<StreamStatus>('idle')
  const [error, setError] = useState('')
  const [lastPrompt, setLastPrompt] = useState('')
  const [chatTheme, setChatTheme] = useState<ChatTheme>(getInitialChatTheme)
  const [webSearchEnabled, setWebSearchEnabled] = useState(false)
  const [chatMode, setChatMode] = useState<StudentChatMode>('balanced')

  const token = session?.token ?? ''
  const activeConversation = conversations.find((item) => item.id === activeConversationId)
  const isBusy = status === 'loading' || status === 'streaming'
  const canRetry = Boolean(lastPrompt) && !isBusy
  const messageRuns = Object.fromEntries(
    messages.map((message) => [message.id, message.run]),
  ) as Record<string, ChatRunState | undefined>
  const messageContents = Object.fromEntries(
    messages.map((message) => [message.id, message.content]),
  ) as Record<string, string>
  const conversationMeta: AssistantConversationMeta[] = conversations.map((conversation) => ({
    id: conversation.id,
    title: conversation.title || '未命名会话',
    messageCount: conversation.messages.length,
    updatedAt: conversation.updated_at,
  }))

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

  const applyRunEvent = useCallback(
    (messageId: string, eventName: string, data: RunEventData) => {
      setMessages((current) =>
        current.map((message) =>
          message.id === messageId
            ? {
                ...message,
                run: reduceChatRun(message.run, eventName, data),
              }
            : message,
        ),
      )
    },
    [],
  )

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
          setMessages((current) =>
            preserveAssistantRunState(current, refreshed.messages.map(toChatMessage)),
          )
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
            webSearch: webSearchEnabled,
            profile: 'student',
            mode: chatMode,
            attachments: [],
          }),
          signal: controller.signal,
        })

        if (!response.ok) {
          throw await requestError(response, '模型接口调用失败')
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
        let hasStandardRunEvents = false

        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            break
          }

          buffer += decoder.decode(value, { stream: true })
          const parsed = drainSseEvents(buffer)
          buffer = parsed.rest

          for (const event of parsed.events) {
            const payload = getRunPayload(event.data)
            const eventType = readString(event.data.type) ?? event.event
            const isStandardRunEvent = event.data.schema_version === 'chat.run.v1'
            if (isStandardRunEvent) {
              hasStandardRunEvents = true
            }
            const shouldConsumeEvent =
              isStandardRunEvent || !hasStandardRunEvents || event.event === 'conversation'
            if (shouldConsumeEvent) {
              applyRunEvent(assistantId, event.event, event.data)
            }
            if (
              event.event === 'conversation' ||
              eventType === 'run_started' ||
              eventType === 'done'
            ) {
              streamedConversationId =
                readString(payload.conversationId) ??
                readString(event.data.conversationId) ??
                streamedConversationId
              setActiveConversationId(streamedConversationId ?? null)
            }
            if (shouldConsumeEvent && (event.event === 'delta' || eventType === 'answer_delta')) {
              appendAssistantChunk(
                assistantId,
                readString(payload.content) ?? readString(event.data.content) ?? '',
              )
            }
            if (shouldConsumeEvent && eventType === 'error') {
              throw new Error(
                readString(payload.detail) ??
                  readString(event.data.detail) ??
                  '模型生成失败',
              )
            }
          }
        }

        markAssistantStatus(assistantId, { type: 'complete', reason: 'stop' })
        setStatus('idle')
        await refreshConversations(streamedConversationId ?? null)
      } catch (sendError) {
        if (sendError instanceof DOMException && sendError.name === 'AbortError') {
          applyRunEvent(assistantId, 'aborted', {
            type: 'aborted',
            payload: { detail: 'Generation stopped by user.' },
          })
          markAssistantStatus(assistantId, { type: 'incomplete', reason: 'cancelled' })
          setStatus('stopped')
          return
        }
        const message = isAuthError(sendError)
          ? expiredSessionMessage
          : sendError instanceof Error
            ? sendError.message
            : '模型生成失败'
        setStatus('error')
        setError(message)
        setMessages((current) =>
          current.map((item) =>
            item.id === assistantId
              ? {
                  ...item,
                  content: message,
                  run: reduceChatRun(item.run, 'error', {
                    type: 'error',
                    payload: { detail: message },
                  }),
                }
              : item,
          ),
        )
        markAssistantStatus(assistantId, {
          type: 'incomplete',
          reason: 'error',
          error: message,
        })
        if (isAuthError(sendError)) {
          onSessionExpired()
        }
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
      applyRunEvent,
      isBusy,
      markAssistantStatus,
      onSessionExpired,
      refreshConversations,
      token,
      webSearchEnabled,
      chatMode,
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
        const message = isAuthError(loadError)
          ? expiredSessionMessage
          : loadError instanceof Error
            ? loadError.message
            : '聊天记录读取失败'
        setError(message)
        setStatus('error')
        if (isAuthError(loadError)) {
          onSessionExpired()
        }
      })
    return () => {
      ignore = true
    }
  }, [apiBase, onSessionExpired, token])

  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  useEffect(() => {
    window.localStorage.setItem(chatThemeStorageKey, chatTheme)
  }, [chatTheme])

  if (!session) {
    return <Navigate to="/login" replace />
  }

  if (session.user.role !== 'student') {
    return <Navigate to="/app" replace />
  }

  const sidebarHeader = (
    <div className="aui-sidebar-header">
      <button className="aui-back-button" onClick={() => navigate('/app/student')} type="button">
        <ArrowLeft data-icon="inline-start" />
        学生工作台
      </button>
      <div className="aui-sidebar-brand">
        <div>
          <span className="aui-sidebar-eyebrow">学生端</span>
          <h1>{assistantDisplayName}</h1>
        </div>
      </div>
    </div>
  )

  const sidebarUtility = (
    <div className="aui-sidebar-utility">
      <div className="aui-model-card" aria-label="当前模型">
        <span>模型</span>
        <strong>Qwen</strong>
      </div>
      <label className="aui-theme-switch" aria-label="主题切换">
        <input
          aria-label={chatTheme === 'dark' ? '切换到浅色模式' : '切换到深色模式'}
          checked={chatTheme === 'dark'}
          onChange={(event) => setChatTheme(event.target.checked ? 'dark' : 'light')}
          role="switch"
          type="checkbox"
        />
        <span aria-hidden="true">
          <Sun />
          <Moon />
        </span>
      </label>
    </div>
  )

  const threadToolbar = (
    <div className="aui-thread-toolbar">
      <button className="aui-thread-new-button" onClick={startNewChat} type="button">
        <Plus data-icon="inline-start" />
        新会话
      </button>
    </div>
  )

  const mobileSidebar = (
    <AssistantMobileSidebar
      conversations={conversationMeta}
      header={sidebarHeader}
      theme={chatTheme}
      utility={sidebarUtility}
    />
  )

  return (
    <main className="student-chat-page" data-chat-theme={chatTheme}>
      <AssistantRuntimeProvider runtime={runtime}>
        <section className="aui-chat-shell" aria-label="学生 AI 咨询助手">
          <AssistantSidebar
            conversations={conversationMeta}
            header={sidebarHeader}
            utility={sidebarUtility}
          />
          <StudentAssistantThread
            assistantName={assistantDisplayName}
            canRetry={canRetry}
            chatMode={chatMode}
            error={error}
            messageContents={messageContents}
            messageRuns={messageRuns}
            mobileSidebarTrigger={mobileSidebar}
            onChatModeChange={setChatMode}
            onRetry={() => void retryLastPrompt()}
            onWebSearchChange={setWebSearchEnabled}
            promptStarters={promptStarters}
            status={status}
            toolbar={threadToolbar}
            webSearchEnabled={webSearchEnabled}
            title={activeConversation?.title ?? '新会话'}
          />
        </section>
      </AssistantRuntimeProvider>
    </main>
  )
}

async function loadConversations(apiBase: string, token: string): Promise<ApiConversation[]> {
  const response = await fetch(`${apiBase}/api/v1/student/conversations`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })
  if (!response.ok) {
    throw await requestError(response, '聊天记录读取失败')
  }
  return response.json() as Promise<ApiConversation[]>
}

async function requestError(response: Response, fallback: string): Promise<ApiRequestError> {
  const detail = await response.json().catch(() => ({ detail: fallback }))
  return new ApiRequestError(detail.detail ?? fallback, response.status)
}

function isAuthError(error: unknown): boolean {
  return error instanceof ApiRequestError && error.status === 401
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

function preserveAssistantRunState(current: ChatMessage[], next: ChatMessage[]): ChatMessage[] {
  const sidecars = current
    .filter((message) => message.role === 'assistant' && (message.run || message.status))
    .map((message) => ({ run: message.run, status: message.status }))
  if (sidecars.length === 0) {
    return next
  }
  return next.map((message) => {
    if (message.role !== 'assistant') {
      return message
    }
    const sidecar = sidecars.shift()
    return sidecar
      ? {
          ...message,
          run: sidecar.run,
          status: sidecar.status ?? message.status,
        }
      : message
  })
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
    const data = JSON.parse(dataLines.join('\n')) as unknown
    return isRunEventData(data) ? [{ event, data }] : []
  } catch {
    return []
  }
}

function isRunEventData(value: unknown): value is RunEventData {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

function getInitialChatTheme(): ChatTheme {
  const savedTheme = window.localStorage.getItem(chatThemeStorageKey)
  return savedTheme === 'dark' ? 'dark' : 'light'
}
