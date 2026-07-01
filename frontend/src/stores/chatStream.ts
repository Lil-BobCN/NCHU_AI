import { defineStore } from 'pinia'
import { computed, nextTick, reactive, ref } from 'vue'
import { api, streamApiUrl, unwrap } from '../api/client'
import { createLocalId } from '../utils/id'

export type Message = {
  id?: string
  localId?: string
  role: 'user' | 'assistant'
  content: string
  citations?: any[]
  suggested_questions?: any[]
  feedback_status?: string
  feedback_error_type?: string
  status?: string
  retrieval?: string
  error?: string
}

export type Conversation = {
  id: string
  title: string
  summary?: string
  context_state?: Record<string, unknown>
  message_count?: number
  last_message_at?: string | null
  created_at?: string | null
  open_feedback_count?: number
  has_feedback?: boolean
}

type TypeState = {
  queue: string[]
  timer?: number
}

type ActiveTurn = {
  conversationId: string | null
  userMessage: Message
  assistantMessage: Message
  userMessageId?: string
  assistantMessageId?: string
  content: string
  startedAt: number
  aborted: boolean
  restoreDraft: boolean
  discarded: boolean
}

const TYPEWRITER_DELAY_MS = 15
const ACTIVE_CONVERSATION_STORAGE_KEY = 'rag_active_conversation_id'
let conversationSearchRequestId = 0

export const useChatStreamStore = defineStore('chatStream', () => {
  const conversations = ref<Conversation[]>([])
  const conversationSearch = ref('')
  const conversationFeedbackOnly = ref(false)
  const searchingConversations = ref(false)
  const conversationId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const question = ref('')
  const loading = ref(false)
  const stoppingGeneration = ref(false)
  const deletingConversationId = ref<string | null>(null)
  const renamingConversationId = ref<string | null>(null)
  const activeAbortController = ref<AbortController | null>(null)
  const activeTurn = ref<ActiveTurn | null>(null)
  const scrollTarget = ref<HTMLElement | null>(null)
  const typeStates = new WeakMap<Message, TypeState>()

  const activeConversationTitle = computed(() => {
    const current = conversations.value.find((item) => item.id === conversationId.value)
    return current?.title || '智能对话'
  })
  const hasConversationSearch = computed(() => Boolean(conversationSearch.value.trim()))
  const hasConversationFeedbackFilter = computed(() => conversationFeedbackOnly.value)

  async function initialize() {
    await loadConversations()
    await restoreActiveConversation()
  }

  function attachScrollTarget(target: HTMLElement | null) {
    scrollTarget.value = target
    void scrollToBottom()
  }

  async function loadConversations(search = conversationSearch.value) {
    const keyword = search.trim()
    const requestId = ++conversationSearchRequestId
    searchingConversations.value = Boolean(keyword)
    try {
      const data = unwrap<any>(
        await api.get('/conversations', {
          params: {
            q: keyword || undefined,
            feedback_only: conversationFeedbackOnly.value || undefined,
            page_size: keyword ? 50 : 20
          }
        })
      )
      if (requestId === conversationSearchRequestId) conversations.value = data.items
    } finally {
      if (requestId === conversationSearchRequestId) searchingConversations.value = false
    }
  }

  async function searchConversations(keyword: string) {
    conversationSearch.value = keyword
    await loadConversations(keyword)
  }

  async function clearConversationSearch() {
    if (!conversationSearch.value) return
    conversationSearch.value = ''
    await loadConversations('')
  }

  async function toggleFeedbackOnlyConversations() {
    conversationFeedbackOnly.value = !conversationFeedbackOnly.value
    await loadConversations()
  }

  async function restoreActiveConversation() {
    if (conversationId.value) return
    const active = activeTurn.value
    if (active?.conversationId) {
      conversationId.value = active.conversationId
      localStorage.setItem(ACTIVE_CONVERSATION_STORAGE_KEY, active.conversationId)
      await scrollToBottom()
      return
    }
    const storedId = localStorage.getItem(ACTIVE_CONVERSATION_STORAGE_KEY)
    const stored = conversations.value.find((item) => item.id === storedId)
    if (stored?.id) {
      await loadConversation(stored.id)
      return
    }
    if (conversations.value[0]?.id) await loadConversation(conversations.value[0].id)
  }

  async function newConversation() {
    if (activeTurn.value) {
      activeTurn.value.aborted = true
      activeTurn.value.restoreDraft = false
      clearTypeQueue(activeTurn.value.assistantMessage)
      activeAbortController.value?.abort()
      activeTurn.value = null
      activeAbortController.value = null
    }
    loading.value = false
    stoppingGeneration.value = false
    const data = unwrap<any>(await api.post('/conversations', { title: '新的对话' }))
    conversationId.value = data.id
    localStorage.setItem(ACTIVE_CONVERSATION_STORAGE_KEY, data.id)
    messages.value = []
    await loadConversations()
  }

  async function renameConversation(item: Conversation, title: string) {
    const nextTitle = title.trim()
    if (!nextTitle || renamingConversationId.value) return
    if (nextTitle === item.title) return
    renamingConversationId.value = item.id
    try {
      const updated = unwrap<Conversation>(await api.patch(`/conversations/${item.id}`, { title: nextTitle }))
      upsertConversation(updated)
    } finally {
      renamingConversationId.value = null
    }
  }

  async function loadConversation(id: string) {
    conversationId.value = id
    localStorage.setItem(ACTIVE_CONVERSATION_STORAGE_KEY, id)
    const active = activeTurn.value
    if (active && active.conversationId === id) {
      ensureActiveTurnVisible(active)
      await scrollToBottom()
      return
    }
    messages.value = unwrap<any>(await api.get(`/conversations/${id}/messages`))
    await scrollToBottom()
  }

  async function deleteConversation(item: any) {
    if (deletingConversationId.value) return
    const confirmed = window.confirm(`确认删除“${item.title}”？`)
    if (!confirmed) return
    deletingConversationId.value = item.id
    try {
      await api.delete(`/conversations/${item.id}`)
      if (conversationId.value === item.id) {
        conversationId.value = null
        messages.value = []
        localStorage.removeItem(ACTIVE_CONVERSATION_STORAGE_KEY)
      }
      await loadConversations()
    } finally {
      deletingConversationId.value = null
    }
  }

  async function submitAnswerFeedback(message: Message, errorType: string, description: string) {
    if (!message.id || message.role !== 'assistant') throw new Error('无法定位要反馈的回答')
    const data = unwrap<any>(
      await api.post('/feedback/answers', {
        assistant_message_id: message.id,
        error_type: errorType,
        description
      })
    )
    message.feedback_status = data.status || 'open'
    message.feedback_error_type = data.error_type || errorType
    if (data.conversation_id) {
      upsertConversation({
        id: data.conversation_id,
        open_feedback_count: data.conversation_feedback_count,
        has_feedback: Number(data.conversation_feedback_count || 0) > 0
      })
    }
    await loadConversations()
    return data
  }

  async function ask(text: string) {
    const content = text.trim()
    if (!content || loading.value) return
    question.value = ''

    const userMessage = reactive<Message>({
      localId: createLocalId(),
      role: 'user',
      content
    })
    const assistant = reactive<Message>({
      localId: createLocalId(),
      role: 'assistant',
      content: '',
      citations: [],
      suggested_questions: [],
      status: '准备检索资料'
    })
    messages.value.push(userMessage)
    messages.value.push(assistant)
    await scrollToBottom()

    const controller = new AbortController()
    const turn: ActiveTurn = {
      conversationId: conversationId.value,
      userMessage,
      assistantMessage: assistant,
      content,
      startedAt: Date.now(),
      aborted: false,
      restoreDraft: false,
      discarded: false
    }
    activeAbortController.value = controller
    activeTurn.value = turn
    loading.value = true
    try {
      const response = await fetch(streamApiUrl('/chat/stream'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`
        },
        body: JSON.stringify({
          conversation_id: conversationId.value,
          question: content,
          enable_suggested_questions: false
        }),
        signal: controller.signal
      })
      if (!response.ok || !response.body) {
        throw new Error(`请求失败：${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const events = buffer.split('\n\n')
        buffer = events.pop() || ''
        for (const event of events) {
          handleEvent(event, assistant, turn)
        }
      }
      if (buffer.trim()) handleEvent(buffer, assistant, turn)
      await drainTypeQueue(assistant)
      if (!turn.aborted && !assistant.content && !assistant.error) {
        assistant.error = '没有收到模型输出'
      }
    } catch (error) {
      if (turn.aborted || isAbortError(error)) {
        await discardActiveTurn(turn)
      } else {
        assistant.error = error instanceof Error ? error.message : '发送失败'
      }
    } finally {
      if (turn.aborted && !turn.discarded) {
        await discardActiveTurn(turn)
      }
      assistant.status = ''
      if (activeTurn.value === turn) activeTurn.value = null
      if (activeAbortController.value === controller) activeAbortController.value = null
      loading.value = false
      stoppingGeneration.value = false
      await loadConversations()
      await scrollToBottom()
    }
  }

  function handleEvent(raw: string, assistant: Message, turn?: ActiveTurn) {
    const event = raw.match(/^event: (.+)$/m)?.[1]
    const dataRaw = raw.match(/^data: (.+)$/m)?.[1]
    if (!event || !dataRaw) return
    const data = JSON.parse(dataRaw)
    if (event === 'message_start') {
      conversationId.value = data.conversation_id
      localStorage.setItem(ACTIVE_CONVERSATION_STORAGE_KEY, data.conversation_id)
      upsertConversation({
        id: data.conversation_id,
        title: data.conversation_title || activeConversationTitle.value,
        message_count: data.message_count,
        last_message_at: data.last_message_at
      })
      if (turn) {
        turn.conversationId = data.conversation_id
        turn.userMessageId = data.user_message_id
        turn.assistantMessageId = data.assistant_message_id
        turn.userMessage.id = data.user_message_id
        turn.assistantMessage.id = data.assistant_message_id
      }
      const memoryParts = []
      if (data.has_summary) memoryParts.push('会话摘要')
      if (data.history_count) memoryParts.push(`${data.history_count} 条历史消息`)
      assistant.status = memoryParts.length ? `已读取 ${memoryParts.join(' + ')}` : '开始检索资料'
    }
    if (event === 'retrieval_start') {
      assistant.retrieval = data.uses_history ? '结合历史对话检索资料' : '检索相关资料'
      assistant.status = '检索资料中'
    }
    if (event === 'retrieval') {
      assistant.retrieval = '正在筛选相关资料'
      assistant.status = '生成回答中'
    }
    if (event === 'retrieval_done') {
      assistant.retrieval = data.citation_count ? '已找到相关资料' : '暂未找到明确资料'
      assistant.status = '生成回答中'
    }
    if (event === 'delta') {
      assistant.status = ''
      enqueueDelta(assistant, data.content || '')
    }
    if (event === 'citations') assistant.citations = data.citations
    if (event === 'suggested_questions') assistant.suggested_questions = data.questions
    if (event === 'error') {
      assistant.error = data.message || '生成失败'
      assistant.status = ''
    }
    if (event === 'message_end') {
      assistant.status = ''
    }
  }

  async function stopGeneration() {
    const turn = activeTurn.value
    if (!turn || stoppingGeneration.value) return
    turn.aborted = true
    turn.restoreDraft = false
    stoppingGeneration.value = true
    clearTypeQueue(turn.assistantMessage)
    removeTurnMessages(turn)
    activeAbortController.value?.abort()
    await scrollToBottom()
  }

  async function retractActiveTurn() {
    const turn = activeTurn.value
    if (!turn || stoppingGeneration.value) return
    turn.aborted = true
    turn.restoreDraft = true
    stoppingGeneration.value = true
    question.value = turn.content
    clearTypeQueue(turn.assistantMessage)
    removeTurnMessages(turn)
    activeAbortController.value?.abort()
    await scrollToBottom()
  }

  async function discardActiveTurn(turn: ActiveTurn) {
    turn.discarded = true
    clearTypeQueue(turn.assistantMessage)
    removeTurnMessages(turn)
    if (turn.restoreDraft) question.value = turn.content
    if (!turn.conversationId || !turn.userMessageId || !turn.assistantMessageId) return
    try {
      const result = unwrap<any>(
        await api.post('/chat/retract', {
          conversation_id: turn.conversationId,
          user_message_id: turn.userMessageId,
          assistant_message_id: turn.assistantMessageId
        })
      )
      if (result.deleted_conversation && conversationId.value === turn.conversationId) {
        conversationId.value = null
        localStorage.removeItem(ACTIVE_CONVERSATION_STORAGE_KEY)
      }
    } catch (error) {
      console.warn('Failed to retract cancelled chat turn', error)
    }
  }

  function isActiveUserMessage(message: Message) {
    const turn = activeTurn.value
    return Boolean(turn && loading.value && !stoppingGeneration.value && turn.userMessage === message)
  }

  function isActiveAssistantMessage(message: Message) {
    const turn = activeTurn.value
    return Boolean(turn && loading.value && !stoppingGeneration.value && turn.assistantMessage === message)
  }

  function ensureActiveTurnVisible(turn: ActiveTurn) {
    const containsUser = messages.value.some((message) => isSameMessage(message, turn.userMessage))
    const containsAssistant = messages.value.some((message) => isSameMessage(message, turn.assistantMessage))
    if (!containsUser) messages.value.push(turn.userMessage)
    if (!containsAssistant) messages.value.push(turn.assistantMessage)
  }

  function isSameMessage(left: Message, right: Message) {
    if (left.id && right.id) return left.id === right.id
    return Boolean(left.localId && right.localId && left.localId === right.localId)
  }

  function upsertConversation(next: Partial<Conversation> & { id: string }) {
    const patch = Object.fromEntries(
      Object.entries(next).filter(([, value]) => value !== undefined)
    ) as Partial<Conversation> & { id: string }
    const index = conversations.value.findIndex((item) => item.id === next.id)
    if (index >= 0) {
      conversations.value[index] = { ...conversations.value[index], ...patch }
      return
    }
    conversations.value.unshift({
      id: patch.id,
      title: patch.title || '新的对话',
      summary: patch.summary,
      context_state: patch.context_state,
      message_count: patch.message_count,
      last_message_at: patch.last_message_at || null,
      created_at: patch.created_at || null,
      open_feedback_count: patch.open_feedback_count,
      has_feedback: patch.has_feedback
    })
  }

  function removeTurnMessages(turn: ActiveTurn) {
    const ids = new Set([turn.userMessage.id, turn.assistantMessage.id].filter(Boolean))
    const localIds = new Set([turn.userMessage.localId, turn.assistantMessage.localId].filter(Boolean))
    messages.value = messages.value.filter((message) => {
      if (message.id && ids.has(message.id)) return false
      return !(message.localId && localIds.has(message.localId))
    })
  }

  function clearTypeQueue(assistant: Message) {
    const state = typeStates.get(assistant)
    if (!state) return
    state.queue = []
    if (state.timer) {
      window.clearInterval(state.timer)
      state.timer = undefined
    }
  }

  function isAbortError(error: unknown) {
    return error instanceof DOMException && error.name === 'AbortError'
  }

  function enqueueDelta(assistant: Message, content: string) {
    if (!content) return
    let state = typeStates.get(assistant)
    if (!state) {
      state = { queue: [] }
      typeStates.set(assistant, state)
    }
    state.queue.push(...Array.from(content))
    if (state.timer) return
    state.timer = window.setInterval(() => {
      const next = state?.queue.shift()
      if (next) {
        assistant.content += next
        void scrollToBottom()
        return
      }
      if (state?.timer) {
        window.clearInterval(state.timer)
        state.timer = undefined
      }
    }, TYPEWRITER_DELAY_MS)
  }

  async function drainTypeQueue(assistant: Message) {
    const state = typeStates.get(assistant)
    if (!state) return
    while (state.queue.length || state.timer) {
      await new Promise((resolve) => window.setTimeout(resolve, 20))
    }
  }

  async function scrollToBottom() {
    await nextTick()
    if (scrollTarget.value) {
      scrollTarget.value.scrollTop = scrollTarget.value.scrollHeight
    }
  }

  return {
    conversations,
    conversationSearch,
    conversationFeedbackOnly,
    searchingConversations,
    hasConversationSearch,
    hasConversationFeedbackFilter,
    conversationId,
    messages,
    question,
    loading,
    stoppingGeneration,
    deletingConversationId,
    renamingConversationId,
    activeConversationTitle,
    initialize,
    attachScrollTarget,
    loadConversations,
    searchConversations,
    clearConversationSearch,
    toggleFeedbackOnlyConversations,
    restoreActiveConversation,
    newConversation,
    loadConversation,
    deleteConversation,
    renameConversation,
    submitAnswerFeedback,
    ask,
    stopGeneration,
    retractActiveTurn,
    isActiveUserMessage,
    isActiveAssistantMessage,
    scrollToBottom
  }
})
