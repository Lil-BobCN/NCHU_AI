import { defineStore } from 'pinia'
import { computed, nextTick, reactive, ref } from 'vue'
import { api, apiErrorMessage, streamApiUrl, unwrap } from '../api/client'
import { createLocalId } from '../utils/id'

export type Message = {
  id?: string
  localId?: string
  // 后端按会话管理反馈和删除。每条消息保留会话编号后，
  // 操作处理器就能在会话切换后拒绝旧消息。
  conversation_id?: string
  role: 'user' | 'assistant'
  content: string
  // 用户消息引用 AI 回复时，这两个字段用于历史展示和定位原回复。
  // content 始终只保存用户自己的追加输入，避免把引用文本混进用户消息正文。
  quoted_message_id?: string | null
  quoted_message_content?: string
  citations?: any[]
  suggested_questions?: any[]
  feedback_status?: string
  feedback_error_type?: string
  feedback_description?: string
  status?: string
  retrieval?: string
  error?: string
  deleted_at?: string | null
  deleted_by?: string | null
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

type ScrollToBottomOptions = {
  force?: boolean
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

export type QuotedMessage = {
  // key 用于前端当前页面滚动定位；id/localId 分别兼容已入库消息和乐观渲染消息。
  key: string
  id?: string
  localId?: string
  // 保存完整引用文本，发送时传给后端作为本轮上下文，而不是直接插入输入框。
  content: string
}

const TYPEWRITER_DELAY_MS = 15
const SCROLL_BOTTOM_EPSILON_PX = 1
// 与后端聊天问题最大字符数配置保持一致，先在前端拦截超长输入，避免用户看到泛化的请求失败。
export const CHAT_MAX_QUESTION_CHARS = 2000
const ACTIVE_CONVERSATION_STORAGE_KEY = 'rag_active_conversation_id'
let conversationSearchRequestId = 0

function sliceChars(value: string, maxLength: number) {
  return Array.from(value).slice(0, Math.max(0, maxLength)).join('')
}

function buildQuotedRequestQuestion(userQuestion: string, quoteContent: string) {
  const quote = quoteContent.trim()
  if (!quote) return userQuestion

  // 发给模型的问题按产品语义拼成“引用内容 + 用户追加问题”。
  // 后端 question 字段有 2000 字限制，因此优先完整保留用户追加问题，引用过长时只截断引用文本。
  const header = '引用内容：\n'
  const separator = '\n\n用户追加问题：\n'
  const fixedText = `${header}${separator}${userQuestion}`
  const maxQuoteLength = CHAT_MAX_QUESTION_CHARS - Array.from(fixedText).length
  if (maxQuoteLength <= 0) return userQuestion

  const quoteChars = Array.from(quote)
  const clippedQuote =
    quoteChars.length > maxQuoteLength
      ? `${sliceChars(quote, Math.max(0, maxQuoteLength - 3))}...`
      : quote
  return `${header}${clippedQuote}${separator}${userQuestion}`
}

export const useChatStreamStore = defineStore('chatStream', () => {
  const conversations = ref<Conversation[]>([])
  const conversationSearch = ref('')
  const conversationFeedbackOnly = ref(false)
  const searchingConversations = ref(false)
  const conversationId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const question = ref('')
  const quotedMessage = ref<QuotedMessage | null>(null)
  const loading = ref(false)
  const stoppingGeneration = ref(false)
  const deletingConversationId = ref<string | null>(null)
  const deletingMessageId = ref<string | null>(null)
  const renamingConversationId = ref<string | null>(null)
  const activeAbortController = ref<AbortController | null>(null)
  const activeTurn = ref<ActiveTurn | null>(null)
  const scrollTarget = ref<HTMLElement | null>(null)
  const autoFollowOutput = ref(true)
  const typeStates = new WeakMap<Message, TypeState>()
  let lastMessagesScrollTop = 0

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
    scrollTarget.value?.removeEventListener('scroll', handleMessagesScroll)
    scrollTarget.value = target
    autoFollowOutput.value = true
    lastMessagesScrollTop = target?.scrollTop || 0
    scrollTarget.value?.addEventListener('scroll', handleMessagesScroll, { passive: true })
    void scrollToBottom({ force: true })
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
      await scrollToBottom({ force: true })
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
    question.value = ''
    quotedMessage.value = null
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
    question.value = ''
    quotedMessage.value = null
    const active = activeTurn.value
    if (active && active.conversationId === id) {
      ensureActiveTurnVisible(active)
      await scrollToBottom({ force: true })
      return
    }
    messages.value = unwrap<any>(await api.get(`/conversations/${id}/messages`))
    await scrollToBottom({ force: true })
  }

  async function deleteConversation(item: any) {
    if (deletingConversationId.value) return
    deletingConversationId.value = item.id
    try {
      await api.delete(`/conversations/${item.id}`)
      if (conversationId.value === item.id) {
        conversationId.value = null
        quotedMessage.value = null
        messages.value = []
        localStorage.removeItem(ACTIVE_CONVERSATION_STORAGE_KEY)
      }
      await loadConversations()
    } finally {
      deletingConversationId.value = null
    }
  }

  async function submitAnswerFeedback(message: Message, errorType: string, description: string) {
    // 反馈弹窗可能在快速切换会话后仍未关闭。
    // 提交前必须比较消息归属会话和当前会话。
    if (!message.id || message.role !== 'assistant') throw new Error('无法定位要反馈的回答')
    const targetConversationId = message.conversation_id || conversationId.value
    if (!targetConversationId || targetConversationId !== conversationId.value) {
      throw new Error('反馈消息不属于当前会话，请刷新后重试')
    }
    let data: any
    try {
      data = unwrap<any>(
        await api.post('/feedback/answers', {
          conversation_id: targetConversationId,
          assistant_message_id: message.id,
          error_type: errorType,
          // 补充说明允许为空，后端会保存为空字符串而不是阻断提交。
          description: description.trim()
        })
      )
    } catch (error) {
      throw new Error(apiErrorMessage(error, '反馈提交失败，请检查网络后重试'))
    }
    message.feedback_status = data.status || 'open'
    message.feedback_error_type = data.error_type || errorType
    message.feedback_description = data.description ?? description
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

  async function cancelAnswerFeedback(message: Message) {
    // 取消反馈和提交反馈使用同一套归属校验，
    // 否则旧的“已标记”状态可能会取消另一个会话里的反馈。
    if (!message.id || message.role !== 'assistant') throw new Error('无法定位要取消的反馈')
    const targetConversationId = message.conversation_id || conversationId.value
    if (!targetConversationId || targetConversationId !== conversationId.value) {
      throw new Error('反馈消息不属于当前会话，请刷新后重试')
    }
    let data: any
    try {
      data = unwrap<any>(
        await api.patch(`/feedback/answers/${message.id}/cancel`, null, {
          params: { conversation_id: targetConversationId }
        })
      )
    } catch (error) {
      throw new Error(apiErrorMessage(error, '取消反馈失败，请稍后重试'))
    }
    message.feedback_status = undefined
    message.feedback_error_type = data.error_type || message.feedback_error_type
    message.feedback_description = data.description ?? message.feedback_description ?? ''
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

  function storeMessageKey(message: Message) {
    // store 不能依赖 ChatView 内部的 messageKey，因此保留一份轻量 key 生成逻辑。
    // 优先使用 localId，能让刚生成但尚未拿到后端 id 的消息也可以被定位。
    return message.localId || message.id || `${message.role}:${message.content.slice(0, 32)}`
  }

  function quoteMessage(message: Message) {
    // 只有 AI 回复允许被引用；用户消息不再提供引用入口。
    // 点击新的 AI 引用会直接替换旧引用，满足“同一时间只引用一条消息”的交互规则。
    if (message.role !== 'assistant' || !message.content) return
    quotedMessage.value = {
      key: storeMessageKey(message),
      id: message.id,
      localId: message.localId,
      content: message.content
    }
  }

  function clearQuotedMessage() {
    // 取消引用只清空引用卡片，不影响输入框里已有草稿。
    quotedMessage.value = null
  }

  async function deleteMessage(message: Message) {
    if (!conversationId.value || !message.id || deletingMessageId.value) {
      return
    }
    deletingMessageId.value = message.id
    try {
      const data = unwrap<any>(await api.delete(`/conversations/${conversationId.value}/messages/${message.id}`))
      messages.value = messages.value.filter((item) => item.id !== message.id)
      upsertConversation({
        id: data.conversation_id || conversationId.value,
        message_count: data.message_count,
        last_message_at: data.last_message_at || null
      })
      await loadConversations()
      await scrollToBottom()
    } finally {
      deletingMessageId.value = null
    }
  }

  async function ask(text: string) {
    const content = text.trim()
    if (!content || loading.value) return
    if (Array.from(content).length > CHAT_MAX_QUESTION_CHARS) return
    // 先捕获当前引用，再清空输入区状态；后续乐观消息和请求体都使用这份快照。
    // 这样即使用户发送后马上切换引用，也不会影响已经发出的这一轮。
    const quote = quotedMessage.value
    const requestQuestion = buildQuotedRequestQuestion(content, quote?.content || '')
    question.value = ''
    quotedMessage.value = null

    const userMessage = reactive<Message>({
      localId: createLocalId(),
      role: 'user',
      content,
      // 乐观渲染阶段就展示引用摘要，不必等后端 message_start 或刷新历史。
      quoted_message_id: quote?.id || null,
      quoted_message_content: quote?.content || ''
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
    await scrollToBottom({ force: true })

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
          question: requestQuestion,
          // 引用编号用于入库和历史定位；引用全文用于后端构造本轮上下文。
          quoted_message_id: quote?.id,
          quoted_content: quote?.content,
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
        // 流式输出一开始就把后端编号写回两条乐观消息。
        // 后续复制、引用、删除、反馈等操作才能绑定真实会话，
        // 而不是绑定临时的本地轮次。
        turn.conversationId = data.conversation_id
        turn.userMessageId = data.user_message_id
        turn.assistantMessageId = data.assistant_message_id
        turn.userMessage.id = data.user_message_id
        turn.userMessage.conversation_id = data.conversation_id
        turn.assistantMessage.id = data.assistant_message_id
        turn.assistantMessage.conversation_id = data.conversation_id
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
      // 最终是否“找到资料”只能由引用事件里的真实引用决定；这里清空检索过程文案，避免把候选召回误说成已找到依据。
      assistant.retrieval = ''
      assistant.status = '生成回答中'
    }
    if (event === 'delta') {
      assistant.status = ''
      enqueueDelta(assistant, data.content || '')
    }
    if (event === 'citations') {
      assistant.citations = data.citations
      // 不再显示“已找到相关资料”这类状态文案；有真实引用时由参考来源/标签区域直接展示。
      assistant.retrieval = ''
    }
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
    // 只有正在流式生成的回答才视为活跃消息。
    // 生成期间历史消息仍可操作，未完成的回答则禁止反馈、复制、引用等动作。
    const turn = activeTurn.value
    return Boolean(turn && loading.value && turn.assistantMessage === message)
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

  function handleMessagesScroll() {
    const target = scrollTarget.value
    if (!target) return
    const isAtBottom = isScrollAtBottom()
    const isScrollingUp = target.scrollTop < lastMessagesScrollTop
    // 模型输出期间用户只要向上滚动查看历史内容，就暂停自动跟随，避免后续增量内容抢回滚动条。
    if (loading.value && isScrollingUp && !isAtBottom) {
      autoFollowOutput.value = false
    } else if (isAtBottom) {
      autoFollowOutput.value = true
    }
    lastMessagesScrollTop = target.scrollTop
  }

  function isScrollAtBottom() {
    const target = scrollTarget.value
    if (!target) return true
    const distanceToBottom = target.scrollHeight - target.scrollTop - target.clientHeight
    return distanceToBottom <= SCROLL_BOTTOM_EPSILON_PX
  }

  async function scrollToBottom(options: ScrollToBottomOptions = {}) {
    await nextTick()
    const target = scrollTarget.value
    if (!target || (!options.force && !autoFollowOutput.value)) return
    target.scrollTop = target.scrollHeight
    lastMessagesScrollTop = target.scrollTop
    autoFollowOutput.value = true
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
    quotedMessage,
    loading,
    stoppingGeneration,
    deletingConversationId,
    deletingMessageId,
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
    cancelAnswerFeedback,
    quoteMessage,
    clearQuotedMessage,
    deleteMessage,
    ask,
    stopGeneration,
    retractActiveTurn,
    isActiveUserMessage,
    isActiveAssistantMessage,
    scrollToBottom
  }
})
