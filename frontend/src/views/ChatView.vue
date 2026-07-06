<template>
  <AppShell>
    <div class="chat-layout">
      <section class="conversation-list">
        <div class="conversation-list-head">
          <div>
            <strong>历史对话</strong>
            <span>{{ conversationListSummary }}</span>
          </div>
          <button class="icon-button primary" title="新建对话" aria-label="新建对话" @click="chatStore.newConversation">
            <Plus :size="18" />
          </button>
        </div>

        <label class="conversation-search" aria-label="搜索历史对话">
          <Search :size="16" />
          <input
            v-model="conversationSearch"
            type="search"
            placeholder="搜索会话名称或对话内容"
            autocomplete="off"
          />
          <button
            v-if="conversationSearch"
            type="button"
            class="icon-button"
            title="清空搜索"
            aria-label="清空搜索"
            @click="conversationSearch = ''"
          >
            <X :size="14" />
          </button>
          <LoaderCircle v-else-if="searchingConversations" :size="15" class="spin search-loading" />
        </label>

        <div class="conversation-filter-row" aria-label="历史对话筛选">
          <button
            type="button"
            class="conversation-filter-button"
            :class="{ active: conversationFeedbackOnly }"
            :aria-pressed="conversationFeedbackOnly"
            @click="void chatStore.toggleFeedbackOnlyConversations()"
          >
            <CircleAlert :size="15" />
            <span>只看异常</span>
          </button>
        </div>

        <div class="conversation-scroll">
          <div
            v-for="item in conversations"
            :key="item.id"
            class="conversation-row"
            :class="{ active: item.id === conversationId, flagged: item.has_feedback }"
            role="button"
            tabindex="0"
            @click="chatStore.loadConversation(item.id)"
            @keydown.enter.prevent="chatStore.loadConversation(item.id)"
          >
            <form
              v-if="editingConversationId === item.id"
              class="conversation-title-form"
              @submit.prevent="saveConversationTitle(item)"
              @click.stop
              @keydown.stop
            >
              <input
                :ref="setTitleInputEl"
                v-model="editingConversationTitle"
                maxlength="50"
                aria-label="会话标题"
                @keydown.esc.prevent.stop="cancelConversationTitleEdit"
              />
              <button
                type="submit"
                class="icon-button primary"
                title="保存标题"
                aria-label="保存标题"
                :disabled="renamingConversationId === item.id"
              >
                <LoaderCircle v-if="renamingConversationId === item.id" :size="15" class="spin" />
                <Check v-else :size="15" />
              </button>
              <button
                type="button"
                class="icon-button"
                title="取消编辑"
                aria-label="取消编辑"
                :disabled="renamingConversationId === item.id"
                @click.stop="cancelConversationTitleEdit"
              >
                <X :size="15" />
              </button>
            </form>
            <template v-else>
              <div class="conversation-title">
                <MessageSquareText :size="16" />
                <span :title="item.title">{{ item.title }}</span>
              </div>
              <span v-if="item.has_feedback" class="conversation-feedback-badge">
                <CircleAlert :size="13" />
                异常 {{ item.open_feedback_count || 1 }}
              </span>
              <small>{{ formatConversationTime(item.last_message_at || item.created_at) }}</small>
              <button
                class="icon-button conversation-edit"
                title="编辑标题"
                aria-label="编辑标题"
                :disabled="renamingConversationId === item.id"
                @click.stop="startConversationTitleEdit(item)"
              >
                <LoaderCircle v-if="renamingConversationId === item.id" :size="15" class="spin" />
                <Pencil v-else :size="15" />
              </button>
              <button
                class="icon-button danger conversation-delete"
                title="删除会话"
                aria-label="删除会话"
                :disabled="deletingConversationId === item.id"
                @click.stop="chatStore.deleteConversation(item)"
              >
                <LoaderCircle v-if="deletingConversationId === item.id" :size="16" class="spin" />
                <Trash2 v-else :size="16" />
              </button>
            </template>
          </div>

          <div v-if="!conversations.length" class="conversation-empty">
            {{ conversationEmptyText }}
          </div>
        </div>
      </section>

      <section class="chat-panel">
        <header class="chat-toolbar">
          <div>
            <strong>{{ activeConversationTitle }}</strong>
            <span>{{ loading ? '生成中' : `${messages.length} 条消息` }}</span>
          </div>
        </header>

        <div ref="messagesEl" class="messages">
          <div v-if="!messages.length" class="chat-empty">
            <MessageSquareText :size="32" />
            <strong>暂无消息</strong>
          </div>

          <article v-for="message in messages" :key="message.localId || message.id" :class="['message', message.role]">
            <div class="bubble">
              <template v-if="message.content && message.role === 'assistant'">
                <div
                  class="markdown-content"
                  :class="{ collapsed: isAnswerCollapsed(message) }"
                  v-html="renderMarkdown(displayedAnswerContent(message))"
                />
                <div v-if="shouldCollapseAnswer(message)" class="answer-collapse-control">
                  <span v-if="isAnswerCollapsed(message)">已折叠长回答，约 {{ answerCharCount(message) }} 字，当前展示摘要</span>
                  <button
                    type="button"
                    :aria-expanded="!isAnswerCollapsed(message)"
                    :aria-label="isAnswerCollapsed(message) ? '展开长回答全文' : '收起长回答'"
                    @click="toggleAnswerCollapse(message)"
                  >
                    {{ isAnswerCollapsed(message) ? '展开全文' : '收起回答' }}
                  </button>
                </div>
              </template>
              <p v-else-if="message.content">{{ message.content }}</p>
              <p v-else-if="message.status" class="stream-status">{{ message.status }}</p>

              <div v-if="message.retrieval" class="retrieval-state">
                <span>{{ message.retrieval }}</span>
              </div>

              <div v-if="message.error" class="error">
                {{ message.error }}
              </div>

              <div v-if="chatStore.isActiveUserMessage(message)" class="message-actions">
                <button
                  type="button"
                  class="message-action"
                  :disabled="stoppingGeneration"
                  title="撤回并修改"
                  @click="void chatStore.retractActiveTurn()"
                >
                  <Undo2 :size="15" />
                  <span>撤回</span>
                </button>
              </div>

              <div v-if="canFeedback(message)" class="assistant-feedback">
                <button
                  type="button"
                  class="feedback-trigger"
                  :disabled="message.feedback_status === 'open'"
                  @click="openFeedbackDialog(message)"
                >
                  <CircleAlert :size="15" />
                  <span>{{ message.feedback_status === 'open' ? '已标记回答有误' : '回答有误' }}</span>
                </button>
              </div>

              <div v-if="visibleCitations(message).length" class="citations">
                <strong>参考来源</strong>
                <div v-for="(source, index) in visibleCitations(message)" :key="index" class="citation-item">
                  <a :href="source.url" target="_blank">
                    {{ index + 1 }}. {{ source.document_title || source.document_name }}
                  </a>
                  <span v-if="citationLocation(source)" class="citation-location">{{ citationLocation(source) }}</span>
                  <div v-if="source.images?.length" class="related-images">
                    <span>相关示意图</span>
                    <a
                      v-for="image in source.images"
                      :key="image.url"
                      class="related-image"
                      :href="image.url"
                      target="_blank"
                    >
                      <img :src="image.url" :alt="image.file_name || '相关示意图'" loading="lazy" />
                    </a>
                  </div>
                </div>
              </div>

              <div v-if="message.suggested_questions?.length" class="suggestions">
                <button v-for="item in message.suggested_questions" :key="item.question" @click="chatStore.ask(item.question)">
                  {{ item.question }}
                </button>
              </div>
            </div>
          </article>
        </div>

        <form class="composer" @submit.prevent="chatStore.ask(question)">
          <div class="composer-field">
            <textarea
              v-model="question"
              rows="2"
              :maxlength="CHAT_MAX_QUESTION_CHARS"
              :class="{ 'limit-reached': isComposerLimitReached }"
              :aria-invalid="isComposerOverLimit"
              aria-describedby="composer-limit-tip"
              placeholder="输入问题，支持连续追问"
              @keydown.enter="handleComposerEnter"
            />
            <p
              id="composer-limit-tip"
              class="composer-limit-tip"
              :class="{ warning: isComposerLimitReached }"
              aria-live="polite"
            >
              <span v-if="isComposerLimitReached">输出达到上限</span>
              <span v-else>{{ composerCharCount }}/{{ CHAT_MAX_QUESTION_CHARS }}</span>
            </p>
          </div>
          <button
            v-if="loading"
            type="button"
            class="stop-button"
            :disabled="stoppingGeneration"
            title="停止生成"
            aria-label="停止生成"
            @click="void chatStore.stopGeneration()"
          >
            <LoaderCircle v-if="stoppingGeneration" :size="18" class="spin" />
            <Square v-else :size="18" />
            <span>{{ stoppingGeneration ? '停止中' : '停止生成' }}</span>
          </button>
          <button v-else class="primary send-button" :disabled="!question.trim() || isComposerOverLimit" title="发送" aria-label="发送">
            <SendHorizontal :size="18" />
            <span>发送</span>
          </button>
        </form>
      </section>

      <div v-if="feedbackToast" class="feedback-toast" role="status" aria-live="polite">
        {{ feedbackToast }}
      </div>

      <div v-if="feedbackTarget" class="document-preview-modal" role="dialog" aria-modal="true">
        <form class="feedback-dialog" @submit.prevent="submitFeedback">
          <header>
            <div>
              <strong>回答有误</strong>
              <span>标记后会归集给运维人员排查知识库和回答链路。</span>
            </div>
            <button type="button" class="icon-button" title="关闭" aria-label="关闭" @click="closeFeedbackDialog">
              <X :size="18" />
            </button>
          </header>

          <div class="feedback-options">
            <label v-for="option in feedbackTypeOptions" :key="option.value">
              <input v-model="feedbackType" type="radio" name="feedbackType" :value="option.value" />
              <span>{{ option.label }}</span>
            </label>
          </div>

          <label class="feedback-description">
            <span>补充说明（选填）</span>
            <textarea
              v-model="feedbackDescription"
              rows="4"
              maxlength="1000"
              placeholder="可描述哪里不准确、期望答案或参考来源问题"
            />
          </label>

          <p v-if="feedbackError" class="error">{{ feedbackError }}</p>

          <footer>
            <button type="button" @click="closeFeedbackDialog">取消</button>
            <button type="submit" class="primary" :disabled="feedbackSubmitting">
              <LoaderCircle v-if="feedbackSubmitting" :size="16" class="spin" />
              <span>{{ feedbackSubmitting ? '提交中' : '提交反馈' }}</span>
            </button>
          </footer>
        </form>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import AppShell from '../components/AppShell.vue'
import { Check, CircleAlert, LoaderCircle, MessageSquareText, Pencil, Plus, Search, SendHorizontal, Square, Trash2, Undo2, X } from 'lucide-vue-next'
import { apiErrorMessage } from '../api/client'
import { CHAT_MAX_QUESTION_CHARS, useChatStreamStore, type Conversation, type Message } from '../stores/chatStream'

const chatStore = useChatStreamStore()
const {
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
  activeConversationTitle
} = storeToRefs(chatStore)
const messagesEl = ref<HTMLElement | null>(null)
const titleInputEl = ref<HTMLInputElement | null>(null)
const editingConversationId = ref<string | null>(null)
const editingConversationTitle = ref('')
const expandedAnswerKeys = ref<Set<string>>(new Set())
let conversationSearchTimer: number | undefined
const feedbackTarget = ref<Message | null>(null)
const feedbackType = ref('answer_wrong')
const feedbackDescription = ref('')
const feedbackSubmitting = ref(false)
const feedbackError = ref('')
const feedbackToast = ref('')
let feedbackToastTimer: number | undefined
const feedbackTypeOptions = [
  { value: 'answer_wrong', label: '答案错误' },
  { value: 'citation_wrong', label: '参考来源错误' },
  { value: 'off_topic', label: '答非所问' },
  { value: 'incomplete', label: '回答不完整' },
  { value: 'other', label: '其他问题' }
]
const composerCharCount = computed(() => Array.from(question.value.trim()).length)
const isComposerLimitReached = computed(() => composerCharCount.value >= CHAT_MAX_QUESTION_CHARS)
const isComposerOverLimit = computed(() => composerCharCount.value > CHAT_MAX_QUESTION_CHARS)
const conversationListSummary = computed(() => {
  const countText = hasConversationSearch.value || hasConversationFeedbackFilter.value
    ? `匹配 ${conversations.value.length} 条`
    : `${conversations.value.length} 条`
  return hasConversationFeedbackFilter.value ? `${countText} · 异常反馈` : countText
})
const conversationEmptyText = computed(() => {
  if (hasConversationFeedbackFilter.value && hasConversationSearch.value) return '未找到匹配的异常会话'
  if (hasConversationFeedbackFilter.value) return '暂无异常反馈会话'
  if (hasConversationSearch.value) return '未找到匹配会话'
  return '暂无历史对话'
})

onMounted(async () => {
  chatStore.attachScrollTarget(messagesEl.value)
  await chatStore.initialize()
})

onBeforeUnmount(() => {
  if (conversationSearchTimer) window.clearTimeout(conversationSearchTimer)
  if (feedbackToastTimer) window.clearTimeout(feedbackToastTimer)
  chatStore.attachScrollTarget(null)
})

watch(messagesEl, (element) => {
  chatStore.attachScrollTarget(element)
})

watch(messages, () => {
  const validKeys = new Set(messages.value.map(messageKey))
  const next = new Set([...expandedAnswerKeys.value].filter((key) => validKeys.has(key)))
  if (next.size !== expandedAnswerKeys.value.size) expandedAnswerKeys.value = next
})

watch(conversationSearch, (value) => {
  if (conversationSearchTimer) window.clearTimeout(conversationSearchTimer)
  conversationSearchTimer = window.setTimeout(() => {
    void chatStore.searchConversations(value)
  }, 220)
})

function handleComposerEnter(event: KeyboardEvent) {
  if (event.shiftKey || event.isComposing) return
  event.preventDefault()
  void chatStore.ask(question.value)
}

async function startConversationTitleEdit(item: Conversation) {
  editingConversationId.value = item.id
  editingConversationTitle.value = item.title
  await nextTick()
  titleInputEl.value?.focus()
  titleInputEl.value?.select()
}

function cancelConversationTitleEdit() {
  editingConversationId.value = null
  editingConversationTitle.value = ''
}

function setTitleInputEl(element: unknown) {
  titleInputEl.value = element instanceof HTMLInputElement ? element : null
}

async function saveConversationTitle(item: Conversation) {
  if (editingConversationId.value !== item.id) return
  const nextTitle = editingConversationTitle.value.trim()
  if (!nextTitle || nextTitle === item.title) {
    cancelConversationTitleEdit()
    return
  }
  await chatStore.renameConversation(item, nextTitle)
  cancelConversationTitleEdit()
}

function canFeedback(message: Message) {
  return message.role === 'assistant' && Boolean(message.id) && Boolean(message.content) && !chatStore.isActiveAssistantMessage(message)
}

const ANSWER_COLLAPSE_THRESHOLD = 900
const ANSWER_COLLAPSE_PREVIEW = 560
const ANSWER_SUMMARY_MIN_LENGTH = 260

function messageKey(message: Message) {
  return message.localId || message.id || `${message.role}:${message.content.slice(0, 32)}`
}

function answerCharCount(message: Message) {
  return answerTextLength(message.content || '')
}

function shouldCollapseAnswer(message: Message) {
  return (
    message.role === 'assistant' &&
    !message.status &&
    !chatStore.isActiveAssistantMessage(message) &&
    answerCharCount(message) > ANSWER_COLLAPSE_THRESHOLD
  )
}

function isAnswerCollapsed(message: Message) {
  return shouldCollapseAnswer(message) && !expandedAnswerKeys.value.has(messageKey(message))
}

function displayedAnswerContent(message: Message) {
  if (!isAnswerCollapsed(message)) return message.content
  return `${summarizeAnswerContent(message.content)}\n\n...`
}

function toggleAnswerCollapse(message: Message) {
  const key = messageKey(message)
  const next = new Set(expandedAnswerKeys.value)
  if (next.has(key)) {
    next.delete(key)
  } else {
    next.add(key)
  }
  expandedAnswerKeys.value = next
}

function summarizeAnswerContent(content: string) {
  const normalized = content.replace(/\r\n/g, '\n').trim()
  if (!normalized) return ''
  const paragraphs = normalized
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)
  let summary = ''
  for (const paragraph of paragraphs) {
    const candidate = summary ? `${summary}\n\n${paragraph}` : paragraph
    if (answerTextLength(candidate) > ANSWER_COLLAPSE_PREVIEW) {
      if (!summary) return trimAnswerToBoundary(paragraph, ANSWER_COLLAPSE_PREVIEW)
      break
    }
    summary = candidate
    if (answerTextLength(summary) >= ANSWER_SUMMARY_MIN_LENGTH) break
  }
  return trimAnswerToBoundary(summary || normalized, ANSWER_COLLAPSE_PREVIEW)
}

function trimAnswerToBoundary(text: string, maxLength: number) {
  const clipped = sliceAnswerText(text, maxLength)
  if (answerTextLength(clipped) === answerTextLength(text)) return clipped
  const boundary = findLastSentenceBoundary(clipped)
  if (boundary >= ANSWER_SUMMARY_MIN_LENGTH) return clipped.slice(0, boundary).trimEnd()
  return clipped
}

function sliceAnswerText(text: string, maxLength: number) {
  const chars = Array.from(text)
  if (chars.length <= maxLength) return text.trimEnd()
  return chars.slice(0, maxLength).join('').trimEnd()
}

function answerTextLength(text: string) {
  return Array.from(text).length
}

function findLastSentenceBoundary(text: string) {
  const pattern = /[。！？!?；;.!?]\s*/g
  let boundary = -1
  let match: RegExpExecArray | null
  while ((match = pattern.exec(text)) !== null) {
    boundary = match.index + match[0].length
  }
  return boundary
}

function openFeedbackDialog(message: Message) {
  if (message.feedback_status === 'open') return
  feedbackTarget.value = message
  feedbackType.value = 'answer_wrong'
  feedbackDescription.value = ''
  feedbackError.value = ''
}

function closeFeedbackDialog() {
  if (feedbackSubmitting.value) return
  feedbackTarget.value = null
  feedbackError.value = ''
}

async function submitFeedback() {
  if (!feedbackTarget.value || feedbackSubmitting.value) return
  feedbackSubmitting.value = true
  feedbackError.value = ''
  try {
    await chatStore.submitAnswerFeedback(
      feedbackTarget.value,
      feedbackType.value,
      feedbackDescription.value.trim()
    )
    closeFeedbackDialog()
    showFeedbackToast('反馈提交成功，我们将尽快优化知识库')
  } catch (error) {
    feedbackError.value = apiErrorMessage(error, '反馈提交失败，请稍后重试')
  } finally {
    feedbackSubmitting.value = false
  }
}

function showFeedbackToast(message: string) {
  if (feedbackToastTimer) window.clearTimeout(feedbackToastTimer)
  feedbackToast.value = message
  feedbackToastTimer = window.setTimeout(() => {
    feedbackToast.value = ''
    feedbackToastTimer = undefined
  }, 2600)
}

function formatConversationTime(value?: string | null) {
  if (!value) return '尚无消息'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '尚无消息'
  const now = Date.now()
  const diff = now - date.getTime()
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

function citationLocation(source: any) {
  const parts: string[] = []
  const pageNumbers = Array.isArray(source.page_numbers)
    ? source.page_numbers.filter((page: unknown) => Number.isInteger(page) && Number(page) > 0)
    : []
  if (pageNumbers.length) {
    parts.push(`第 ${formatNumberRanges(pageNumbers)} 页`)
  } else if (source.page_start) {
    const end = source.page_end && source.page_end !== source.page_start ? `-${source.page_end}` : ''
    parts.push(`第 ${source.page_start}${end} 页`)
  }
  if (Array.isArray(source.table_numbers) && source.table_numbers.length) {
    parts.push(source.table_numbers.slice(0, 5).join('、'))
  } else if (source.section_path && /^表格?\s*[0-9一二三四五六七八九十]+/.test(String(source.section_path))) {
    parts.push(source.section_path)
  }
  return parts.join('，')
}

function visibleCitations(message: Message) {
  return (message.citations || []).filter((source: any) => {
    const title = String(source?.document_title || source?.document_name || '').trim()
    const url = String(source?.url || '').trim()
    return Boolean(title && url)
  })
}

function formatNumberRanges(values: number[]) {
  const numbers = [...new Set(values.map(Number).filter((value) => value > 0))].sort((a, b) => a - b)
  const ranges: string[] = []
  let start = numbers[0]
  let previous = numbers[0]
  for (const number of numbers.slice(1)) {
    if (number === previous + 1) {
      previous = number
      continue
    }
    ranges.push(start === previous ? `${start}` : `${start}-${previous}`)
    start = previous = number
  }
  if (start) ranges.push(start === previous ? `${start}` : `${start}-${previous}`)
  return ranges.join('、')
}

function renderMarkdown(content: string): string {
  const lines = content.replace(/\r\n/g, '\n').split('\n')
  const html: string[] = []
  let paragraph: string[] = []
  let listType: 'ul' | 'ol' | null = null
  let listItems: string[] = []
  let orderedListStart: number | null = null

  const flushParagraph = () => {
    const text = paragraph.join('\n').trim()
    if (text) html.push(`<p>${renderInlineMarkdown(text)}</p>`)
    paragraph = []
  }

  const flushList = () => {
    if (listType && listItems.length) {
      const startAttr =
        listType === 'ol' && orderedListStart !== null && orderedListStart !== 1
          ? ` start="${orderedListStart}"`
          : ''
      html.push(`<${listType}${startAttr}>${listItems.join('')}</${listType}>`)
    }
    listType = null
    listItems = []
    orderedListStart = null
  }

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index]
    const trimmed = line.trim()
    if (!trimmed) {
      flushParagraph()
      flushList()
      continue
    }

    if (isMarkdownTableStart(lines, index)) {
      flushParagraph()
      flushList()
      const table = collectMarkdownTable(lines, index)
      html.push(renderMarkdownTable(table.rows))
      index = table.endIndex
      continue
    }

    const heading = trimmed.match(/^(#{1,3})\s+(.+)$/)
    if (heading) {
      flushParagraph()
      flushList()
      const level = heading[1].length + 1
      html.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`)
      continue
    }

    const unordered = trimmed.match(/^[-*]\s+(.+)$/)
    const ordered = parseOrderedListItem(trimmed)
    if (unordered || ordered) {
      flushParagraph()
      const nextType = unordered ? 'ul' : 'ol'
      if (listType && listType !== nextType) flushList()
      listType = nextType
      if (ordered && orderedListStart === null) orderedListStart = ordered.value
      const valueAttr = ordered ? ` value="${ordered.value}"` : ''
      const itemText = unordered?.[1] || ordered?.text || ''
      listItems.push(`<li${valueAttr}>${renderInlineMarkdown(itemText)}</li>`)
      continue
    }

    flushList()
    paragraph.push(line)
  }

  flushParagraph()
  flushList()
  return html.join('')
}

function isMarkdownTableStart(lines: string[], index: number): boolean {
  const header = lines[index]?.trim() || ''
  const separator = lines[index + 1]?.trim() || ''
  const firstBodyRow = lines[index + 1]?.trim() || ''
  return (
    isMarkdownTableRow(header) &&
    (isMarkdownTableSeparator(separator) || isLooseMarkdownTableStart(header, firstBodyRow))
  )
}

function collectMarkdownTable(lines: string[], startIndex: number): { rows: string[][]; endIndex: number } {
  const rows: string[][] = [splitMarkdownTableRow(lines[startIndex])]
  const hasSeparator = isMarkdownTableSeparator(lines[startIndex + 1]?.trim() || '')
  let endIndex = hasSeparator ? startIndex + 1 : startIndex
  const bodyStartIndex = hasSeparator ? startIndex + 2 : startIndex + 1
  for (let index = bodyStartIndex; index < lines.length; index += 1) {
    const line = lines[index].trim()
    if (!isMarkdownTableRow(line) || isMarkdownTableSeparator(line)) break
    rows.push(splitMarkdownTableRow(line))
    endIndex = index
  }
  const columnCount = Math.max(...rows.map((row) => row.length))
  return {
    rows: rows.map((row) => normalizeTableRow(row, columnCount)),
    endIndex
  }
}

function isMarkdownTableRow(line: string): boolean {
  const cells = splitMarkdownTableRow(line)
  return line.includes('|') && cells.length >= 2 && cells.some(Boolean)
}

function isMarkdownTableSeparator(line: string): boolean {
  if (!line || !line.includes('|')) return false
  const cells = splitMarkdownTableRow(line)
  return cells.length >= 2 && cells.every((cell) => /^:?-{2,}:?$/.test(cell.replace(/\s+/g, '')))
}

function isLooseMarkdownTableStart(header: string, firstBodyRow: string): boolean {
  if (!isMarkdownTableRow(firstBodyRow)) return false
  const headerCells = splitMarkdownTableRow(header)
  const bodyCells = splitMarkdownTableRow(firstBodyRow)
  return headerCells.length === bodyCells.length && headerCells.every(Boolean)
}

function splitMarkdownTableRow(line: string): string[] {
  const trimmed = line.trim().replace(/^\|/, '').replace(/\|$/, '')
  const cells: string[] = []
  let current = ''
  let escaped = false
  for (const char of trimmed) {
    if (char === '|' && !escaped) {
      cells.push(current.trim().replace(/\\\|/g, '|'))
      current = ''
    } else {
      current += char
    }
    escaped = char === '\\' && !escaped
  }
  cells.push(current.trim().replace(/\\\|/g, '|'))
  return cells
}

function normalizeTableRow(row: string[], columnCount: number): string[] {
  const normalized = [...row]
  while (normalized.length < columnCount) normalized.push('')
  return normalized.slice(0, columnCount)
}

function renderMarkdownTable(rows: string[][]): string {
  if (!rows.length) return ''
  const [header, ...body] = rows
  const head = header
    .map((cell) => `<th>${renderInlineMarkdown(cell)}</th>`)
    .join('')
  const bodyRows = body
    .map((row) => (
      `<tr>${row.map((cell, index) => `<td class="${tableCellClass(cell, index, header)}">${renderInlineMarkdown(cell)}</td>`).join('')}</tr>`
    ))
    .join('')
  return `<div class="markdown-table-wrap"><table class="markdown-table"><thead><tr>${head}</tr></thead><tbody>${bodyRows}</tbody></table></div>`
}

function tableCellClass(cell: string, cellIndex: number, header: string[]): string {
  const classes: string[] = []
  if (isTableLabelCell(cell, cellIndex, header)) classes.push('table-cell-label')
  if (isImportantTableCell(cell, cellIndex)) classes.push('table-cell-important')
  return classes.join(' ')
}

function isTableLabelCell(cell: string, cellIndex: number, header: string[]): boolean {
  if (cellIndex !== 0 || !cell.trim()) return false
  const firstHeader = header[0]?.replace(/\s+/g, '')
  return /^(项目|字段|类别|事项|名称|类型|条目|问题)$/.test(firstHeader || '') || header.length === 2
}

function isImportantTableCell(cell: string, cellIndex: number): boolean {
  const compact = cell.replace(/\s+/g, '')
  if (!compact) return false
  if (cellIndex === 0) return false
  if (/\d+(?:\.\d+)?\s*(?:%|元|万元|天|日|月|年|小时|个工作日)/.test(compact)) return true
  if (/(?:\d{3,4}-)?\d{7,8}/.test(compact)) return true
  if (/[A-Z]\d{2,4}/i.test(compact)) return true
  return /(时间|日期|金额|费用|比例|条件|材料|流程|地点|期限|要求|对象|状态|办理|申请|提交|审核|公示|备案|报销|票据|归口|咨询电话)/.test(compact)
}

function parseOrderedListItem(text: string): { value: number; text: string } | null {
  const match = text.match(/^(\d+)(?:\.\s+|、\s*)(.+)$/)
  if (!match) return null
  const value = Number(match[1])
  if (!Number.isSafeInteger(value)) return null
  return { value, text: match[2] }
}

function renderInlineMarkdown(text: string): string {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}
</script>
