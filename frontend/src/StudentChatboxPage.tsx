import { useEffect, useRef, useState } from 'react'
import {
  ArrowLeftOutlined,
  ClockCircleOutlined,
  MessageOutlined,
  PlusOutlined,
  ReloadOutlined,
  RobotOutlined,
  SendOutlined,
  StopOutlined,
  UserOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { Alert, Button, Empty, Input, Space, Tag, Typography } from 'antd'
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
  streaming?: boolean
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

export default function StudentChatboxPage({ apiBase, session }: StudentChatboxPageProps) {
  const navigate = useNavigate()
  const abortRef = useRef<AbortController | null>(null)
  const initialHistoryLoadedRef = useRef(false)
  const [conversations, setConversations] = useState<ApiConversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [draft, setDraft] = useState('')
  const [status, setStatus] = useState<StreamStatus>('idle')
  const [error, setError] = useState('')
  const [lastPrompt, setLastPrompt] = useState('')

  const token = session?.token ?? ''

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

  if (!session) {
    return <Navigate to="/login" replace />
  }

  if (session.user.role !== 'student') {
    return <Navigate to="/app" replace />
  }

  const activeConversation = conversations.find((item) => item.id === activeConversationId)
  const isBusy = status === 'loading' || status === 'streaming'
  const canRetry = Boolean(lastPrompt) && !isBusy

  const refreshConversations = async (conversationId: string | null) => {
    const items = await loadConversations(apiBase, token)
    setConversations(items)
    if (conversationId) {
      const refreshed = items.find((item) => item.id === conversationId)
      if (refreshed) {
        setMessages(refreshed.messages.map(toChatMessage))
      }
    }
  }

  const startNewChat = () => {
    abortRef.current?.abort()
    setActiveConversationId(null)
    setMessages([])
    setDraft('')
    setError('')
    setLastPrompt('')
    setStatus('idle')
  }

  const selectConversation = (conversation: ApiConversation) => {
    if (isBusy) {
      return
    }
    setActiveConversationId(conversation.id)
    setMessages(conversation.messages.map(toChatMessage))
    setError('')
    setStatus('idle')
  }

  const sendMessage = async (promptOverride?: string, conversationOverride?: string | null) => {
    const prompt = (promptOverride ?? draft).trim()
    if (!prompt || isBusy) {
      return
    }

    const controller = new AbortController()
    const studentId = `pending-student-${messages.length + 1}`
    const assistantId = `pending-assistant-${messages.length + 2}`
    const conversationId = conversationOverride ?? activeConversationId
    abortRef.current = controller
    setDraft('')
    setError('')
    setLastPrompt(prompt)
    setStatus('loading')
    setMessages((current) => [
      ...current,
      { id: studentId, role: 'student', content: prompt },
      { id: assistantId, role: 'assistant', content: '', streaming: true },
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

      markAssistantComplete(assistantId)
      setStatus('idle')
      await refreshConversations(streamedConversationId ?? null)
    } catch (sendError) {
      if (sendError instanceof DOMException && sendError.name === 'AbortError') {
        markAssistantComplete(assistantId)
        setStatus('stopped')
        return
      }
      const message = sendError instanceof Error ? sendError.message : '模型生成失败'
      setStatus('error')
      setError(message)
      markAssistantComplete(assistantId)
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null
      }
    }
  }

  const stopStreaming = () => {
    abortRef.current?.abort()
  }

  const retryLastPrompt = () => {
    void sendMessage(lastPrompt, activeConversationId)
  }

  const appendAssistantChunk = (messageId: string, chunk: string) => {
    if (!chunk) {
      return
    }
    setMessages((current) =>
      current.map((message) =>
        message.id === messageId ? { ...message, content: `${message.content}${chunk}` } : message,
      ),
    )
  }

  const markAssistantComplete = (messageId: string) => {
    setMessages((current) =>
      current.map((message) =>
        message.id === messageId ? { ...message, streaming: false } : message,
      ),
    )
  }

  return (
    <main className="student-chat-page">
      <section className="chat-header">
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/app/student')}>
          学生工作台
        </Button>
        <div className="chat-header-title">
          <Tag color="blue">Phase 3R</Tag>
          <Typography.Title level={2}>学生 Chatbox</Typography.Title>
          <Typography.Paragraph>
            当前页面独立于学生工作台，回答由后端 Qwen/DashScope 流式代理生成。
          </Typography.Paragraph>
        </div>
        <Space wrap>
          <Button icon={<ReloadOutlined />} disabled={!canRetry} onClick={retryLastPrompt}>
            重试
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={startNewChat}>
            新会话
          </Button>
        </Space>
      </section>

      <section className="chat-shell" aria-label="学生 Chatbox">
        <aside className="conversation-rail">
          <div className="rail-title">
            <MessageOutlined />
            <span>当前运行期记录</span>
          </div>
          <div className="conversation-list">
            {conversations.length === 0 ? (
              <div className="conversation-empty">暂无会话</div>
            ) : (
              conversations.map((conversation) => (
                <button
                  className={`conversation-item ${
                    conversation.id === activeConversationId ? 'active' : ''
                  }`}
                  key={conversation.id}
                  onClick={() => selectConversation(conversation)}
                  type="button"
                >
                  <span>{conversation.title}</span>
                  <small>
                    <ClockCircleOutlined />
                    {conversation.messages.length} 条消息
                  </small>
                </button>
              ))
            )}
          </div>
        </aside>

        <section className="chat-workspace">
          <div className="chat-status-line">
            <div>
              <strong>{activeConversation?.title ?? '新会话'}</strong>
              <span>{session.user.displayName}</span>
            </div>
            <Tag color={status === 'error' ? 'red' : status === 'streaming' ? 'green' : 'blue'}>
              {statusLabel(status)}
            </Tag>
          </div>

          {error ? (
            <Alert
              type="error"
              showIcon
              icon={<WarningOutlined />}
              message={error}
              action={
                canRetry ? (
                  <Button size="small" onClick={retryLastPrompt}>
                    重试
                  </Button>
                ) : null
              }
            />
          ) : null}

          <div className="message-list" aria-live="polite">
            {messages.length === 0 ? (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="开始一个学生端咨询会话"
              >
                <div className="prompt-starters">
                  {promptStarters.map((prompt) => (
                    <Button key={prompt} onClick={() => void sendMessage(prompt, null)}>
                      {prompt}
                    </Button>
                  ))}
                </div>
              </Empty>
            ) : (
              messages.map((message) => (
                <article className={`chat-message ${message.role}`} key={message.id}>
                  <div className="message-avatar">
                    {message.role === 'student' ? <UserOutlined /> : <RobotOutlined />}
                  </div>
                  <div className="message-bubble">
                    <div className="message-role">
                      {message.role === 'student' ? '学生' : 'AI 辅导员'}
                      {message.streaming ? <span>生成中</span> : null}
                    </div>
                    <p>{message.content || '正在连接模型...'}</p>
                  </div>
                </article>
              ))
            )}
          </div>

          <div className="chat-composer">
            <Input.TextArea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onPressEnter={(event) => {
                if (!event.shiftKey) {
                  event.preventDefault()
                  void sendMessage()
                }
              }}
              disabled={isBusy}
              autoSize={{ minRows: 2, maxRows: 5 }}
              placeholder="输入你想讨论的问题"
            />
            <div className="composer-actions">
              {isBusy ? (
                <Button danger icon={<StopOutlined />} onClick={stopStreaming}>
                  停止
                </Button>
              ) : (
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  disabled={!draft.trim()}
                  onClick={() => void sendMessage()}
                >
                  发送
                </Button>
              )}
            </div>
          </div>
        </section>
      </section>
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
  }
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
    return '流式输出'
  }
  if (status === 'error') {
    return '错误'
  }
  if (status === 'stopped') {
    return '已停止'
  }
  return '就绪'
}
