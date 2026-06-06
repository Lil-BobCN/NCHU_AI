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
import type { StudentChatAttachmentPayload } from '@/lib/chat-attachments'
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
  onSessionExpired: (intent?: SessionExpiredIntent) => void
  session: {
    token: string
    user: {
      displayName: string
      role: string
    }
  } | null
}

type SessionExpiredIntent = {
  returnTo?: string
}

type ApiMessage = {
  id: string
  role: 'student' | 'assistant'
  content: string
  created_at: string
  attachments?: ApiMessageAttachment[]
}

type ApiMessageAttachment = {
  id?: string
  name?: string
  mime_type?: string | null
  mimeType?: string | null
  size?: number | null
  encoding?: string | null
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
  attachments?: StudentChatAttachmentPayload[]
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
const chatboxRoute = '/app/student/chatbox'
const pendingRetryStorageKey = 'nchu-ai-chatbox-pending-retry'
const pendingRetryTtlMs = 30 * 60 * 1000

type PendingChatRetry = {
  prompt: string
  conversationId: string | null
  attachments: StudentChatAttachmentPayload[]
  createdAt: number
}

export default function StudentChatboxPage({
  apiBase,
  onSessionExpired,
  session,
}: StudentChatboxPageProps) {
  const navigate = useNavigate()
  const [initialPendingRetry] = useState<PendingChatRetry | null>(() =>
    session?.token ? takePendingChatRetry() : null,
  )
  const abortRef = useRef<AbortController | null>(null)
  const initialHistoryLoadedRef = useRef(Boolean(initialPendingRetry))
  const [conversations, setConversations] = useState<ApiConversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    initialPendingRetry?.conversationId ?? null,
  )
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [status, setStatus] = useState<StreamStatus>(initialPendingRetry ? 'error' : 'idle')
  const [error, setError] = useState(
    initialPendingRetry ? '登录已恢复，刚才的问题已保留，可以点击重试继续发送。' : '',
  )
  const [lastPrompt, setLastPrompt] = useState(initialPendingRetry?.prompt ?? '')
  const [chatTheme, setChatTheme] = useState<ChatTheme>(getInitialChatTheme)
  const [webSearchEnabled, setWebSearchEnabled] = useState(false)
  const [reasoningEnabled, setReasoningEnabled] = useState(true)
  const [chatMode, setChatMode] = useState<StudentChatMode>('balanced')
  const [pendingAttachments, setPendingAttachments] = useState<StudentChatAttachmentPayload[]>(
    initialPendingRetry?.attachments ?? [],
  )
  const [lastAttachments, setLastAttachments] = useState<StudentChatAttachmentPayload[]>(
    initialPendingRetry?.attachments ?? [],
  )

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
  const messageAttachments = Object.fromEntries(
    messages.map((message) => [message.id, message.attachments ?? []]),
  ) as Record<string, StudentChatAttachmentPayload[]>
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
            preserveMessageSidecars(current, refreshed.messages.map(toChatMessage)),
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
    setLastAttachments([])
    setPendingAttachments([])
    setStatus('idle')
  }, [])

  const addPendingAttachments = useCallback((attachments: StudentChatAttachmentPayload[]) => {
    if (attachments.length === 0) {
      return
    }
    setPendingAttachments((current) => [...current, ...attachments].slice(0, 6))
  }, [])

  const removePendingAttachment = useCallback((attachmentId: string) => {
    setPendingAttachments((current) => current.filter((item) => item.id !== attachmentId))
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
    async (
      promptOverride: string,
      conversationOverride?: string | null,
      attachmentsOverride?: StudentChatAttachmentPayload[],
    ) => {
      const prompt = promptOverride.trim()
      if (!prompt || isBusy || !token) {
        return
      }
      const attachments = attachmentsOverride ?? pendingAttachments

      setMessages((current) => current.filter((message) => message.content.trim() !== ''))

      const controller = new AbortController()
      const stamp = Date.now()
      const studentId = `pending-student-${stamp}`
      const assistantId = `pending-assistant-${stamp}`
      const conversationId = conversationOverride ?? activeConversationId
      abortRef.current = controller
      setError('')
      setLastPrompt(prompt)
      setLastAttachments(attachments)
      setPendingAttachments([])
      setStatus('loading')
      setMessages((current) => [
        ...current,
        { id: studentId, role: 'student', content: prompt, attachments },
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
            reasoning: reasoningEnabled,
            profile: 'student',
            mode: chatMode,
            attachments: attachments.map(toRequestAttachment),
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

        const consumeStreamEvents = (events: StreamEvent[]) => {
          for (const event of events) {
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

        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            break
          }

          buffer += decoder.decode(value, { stream: true })
          const parsed = drainSseEvents(buffer)
          buffer = parsed.rest
          consumeStreamEvents(parsed.events)
        }

        buffer += decoder.decode()
        const finalParsed = drainSseEvents(buffer)
        consumeStreamEvents(finalParsed.events)
        if (finalParsed.rest.trim()) {
          consumeStreamEvents(parseSseEvent(finalParsed.rest))
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
          storePendingChatRetry({
            prompt,
            conversationId,
            attachments,
            createdAt: Date.now(),
          })
          onSessionExpired({ returnTo: chatboxRoute })
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
      reasoningEnabled,
      chatMode,
      pendingAttachments,
    ],
  )

  const stopStreaming = useCallback(async () => {
    abortRef.current?.abort()
  }, [])

  const retryLastPrompt = useCallback(async () => {
    if (!lastPrompt) {
      return
    }
    await sendMessage(lastPrompt, activeConversationId, lastAttachments)
  }, [activeConversationId, lastPrompt, lastAttachments, sendMessage])

  const runtime = useExternalStoreRuntime<ChatMessage>({
    messages,
    convertMessage: toAssistantMessage,
    isRunning: isBusy,
    isSendDisabled: !token || isBusy,
    suggestions: messages.length === 0 ? promptStarters.map((prompt) => ({ prompt })) : [],
    onNew: async (message) => {
      await sendMessage(getAppendMessageText(message), activeConversationId, pendingAttachments)
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
          onSessionExpired({ returnTo: chatboxRoute })
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
        <strong>Qwen 3.7</strong>
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
            messageAttachments={messageAttachments}
            messageContents={messageContents}
            messageRuns={messageRuns}
            mobileSidebarTrigger={mobileSidebar}
            onAttachmentsAdd={addPendingAttachments}
            onAttachmentRemove={removePendingAttachment}
            onChatModeChange={setChatMode}
            onReasoningChange={setReasoningEnabled}
            onRetry={() => void retryLastPrompt()}
            onWebSearchChange={setWebSearchEnabled}
            pendingAttachments={pendingAttachments}
            promptStarters={promptStarters}
            status={status}
            toolbar={threadToolbar}
            reasoningEnabled={reasoningEnabled}
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

function toRequestAttachment(attachment: StudentChatAttachmentPayload) {
  return {
    id: attachment.id,
    name: attachment.name,
    mimeType: attachment.mimeType,
    size: attachment.size,
    content: attachment.error ? undefined : attachment.content,
    encoding: attachment.encoding,
  }
}

function toChatMessage(message: ApiMessage): ChatMessage {
  return {
    id: message.id,
    role: message.role,
    content: message.content,
    attachments: toChatAttachments(message.attachments),
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

function toChatAttachments(
  attachments: ApiMessageAttachment[] | undefined,
): StudentChatAttachmentPayload[] | undefined {
  if (!attachments || attachments.length === 0) {
    return undefined
  }
  return attachments
    .filter((attachment) => attachment.id && attachment.name)
    .map((attachment) => ({
      id: attachment.id as string,
      name: attachment.name as string,
      mimeType: attachment.mimeType ?? attachment.mime_type ?? undefined,
      size: attachment.size ?? 0,
      encoding: attachment.encoding === 'base64' ? 'base64' : 'text',
    }))
}

function preserveMessageSidecars(current: ChatMessage[], next: ChatMessage[]): ChatMessage[] {
  const assistantSidecars = current
    .filter((message) => message.role === 'assistant' && (message.run || message.status))
    .map((message) => ({ run: message.run, status: message.status }))
  const studentSidecars = current
    .filter((message) => message.role === 'student' && message.attachments?.length)
    .map((message) => ({
      attachments: message.attachments,
      content: message.content,
      used: false,
    }))
  if (assistantSidecars.length === 0 && studentSidecars.length === 0) {
    return next
  }
  return next.map((message) => {
    if (message.role === 'student') {
      const sidecar = studentSidecars.find(
        (item) => !item.used && item.content === message.content,
      )
      if (!sidecar) {
        return message
      }
      sidecar.used = true
      return {
        ...message,
        attachments: sidecar.attachments,
      }
    }
    if (message.role !== 'assistant') {
      return message
    }
    const sidecar = assistantSidecars.shift()
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

function storePendingChatRetry(retry: PendingChatRetry) {
  const prompt = retry.prompt.trim()
  if (!prompt) {
    return
  }
  try {
    window.sessionStorage.setItem(
      pendingRetryStorageKey,
      JSON.stringify({
        prompt,
        conversationId: retry.conversationId,
        attachments: sanitizeRetryAttachments(retry.attachments),
        createdAt: retry.createdAt,
      } satisfies PendingChatRetry),
    )
  } catch {
    // Retry recovery is best-effort; login still proceeds if tab storage fails.
  }
}

function takePendingChatRetry(): PendingChatRetry | null {
  try {
    const raw = window.sessionStorage.getItem(pendingRetryStorageKey)
    window.sessionStorage.removeItem(pendingRetryStorageKey)
    if (!raw) {
      return null
    }
    const parsed = JSON.parse(raw) as unknown
    if (!isPendingChatRetry(parsed)) {
      return null
    }
    if (Date.now() - parsed.createdAt > pendingRetryTtlMs) {
      return null
    }
    return {
      ...parsed,
      attachments: sanitizeRetryAttachments(parsed.attachments),
    }
  } catch {
    return null
  }
}

function isPendingChatRetry(value: unknown): value is PendingChatRetry {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return false
  }
  const retry = value as Partial<PendingChatRetry>
  return (
    typeof retry.prompt === 'string' &&
    retry.prompt.trim().length > 0 &&
    (typeof retry.conversationId === 'string' || retry.conversationId === null) &&
    Array.isArray(retry.attachments) &&
    typeof retry.createdAt === 'number'
  )
}

function sanitizeRetryAttachments(
  attachments: StudentChatAttachmentPayload[] | undefined,
): StudentChatAttachmentPayload[] {
  if (!attachments?.length) {
    return []
  }
  return attachments
    .filter((attachment) => attachment.id && attachment.name)
    .slice(0, 6)
    .map((attachment) => ({
      id: attachment.id,
      name: attachment.name,
      mimeType: attachment.mimeType,
      size: Math.max(attachment.size, 0),
      content: attachment.error ? undefined : attachment.content,
      encoding: attachment.encoding === 'base64' ? 'base64' : 'text',
      error: attachment.error,
    }))
}

function getInitialChatTheme(): ChatTheme {
  const savedTheme = window.localStorage.getItem(chatThemeStorageKey)
  return savedTheme === 'dark' ? 'dark' : 'light'
}
