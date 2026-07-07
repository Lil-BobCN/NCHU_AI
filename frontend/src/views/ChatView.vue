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

        <div class="conversation-scroll">
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
                @click.stop="requestConversationDelete(item)"
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

          <article
            v-for="message in messages"
            :key="message.localId || message.id"
            :data-message-key="messageKey(message)"
            :data-message-id="message.id || undefined"
            :class="[
              'message',
              message.role,
              {
                'feedback-open': message.role === 'assistant' && message.feedback_status === 'open',
                'has-quote': hasQuotedMessage(message)
              }
            ]"
          >
            <div class="message-stack">
              <div class="bubble">
              <!-- 带引用的用户消息需要在发送后仍能看出“这条问题基于哪条 AI 回复”。 -->
              <!-- 点击引用摘要会滚动回被引用的 AI 消息，方便用户核对上下文。 -->
              <button
                v-if="hasQuotedMessage(message)"
                type="button"
                class="message-quote-preview"
                title="定位引用消息"
                aria-label="定位引用消息"
                @click="locateMessageQuote(message)"
              >
                <Quote :size="15" />
                <span>{{ summarizeQuotedMessage(message.quoted_message_content || '') }}</span>
              </button>
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
              <p v-else-if="message.content">{{ displayMessageContent(message) }}</p>
              <p v-else-if="message.status" class="stream-status">{{ message.status }}</p>

              <div v-if="message.retrieval" class="retrieval-state">
                <span>{{ message.retrieval }}</span>
              </div>

              <div v-if="message.error" class="error">
                {{ message.error }}
              </div>

              <div v-if="qaCitationTags(message).length" class="citations qa-citation-section">
                <strong>标签</strong>
                <div class="qa-citation-tag-row" aria-label="问答引用标签">
                  <RouterLink
                    v-for="item in qaCitationTags(message)"
                    :key="item.key"
                    class="tag-chip qa-citation-tag"
                    :to="{ path: '/qa-pairs', query: { tag: item.tag } }"
                    :title="`查看标签“${item.tag}”对应的问答`"
                  >
                    {{ item.tag }}
                  </RouterLink>
                </div>
              </div>

              <div v-if="documentCitations(message).length" class="citations">
                <strong>参考来源</strong>
                <div v-for="(source, index) in documentCitations(message)" :key="index" class="citation-item">
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
              <div v-if="message.role === 'assistant'" class="message-actions-row assistant-actions" aria-label="AI 回复操作">
                <button
                  type="button"
                  class="message-action-button action-copy"
                  :disabled="messageActionDisabled(message)"
                  :data-message-action-key="messageActionKey(message, 'copy')"
                  aria-label="复制"
                  @mouseleave="clearMessageActionState(message, 'copy')"
                  @pointerleave="clearMessageActionState(message, 'copy')"
                  @blur="clearMessageActionState(message, 'copy')"
                  @click="copyMessage(message)"
                >
                  <Check v-if="isMessageActionConfirmed(message, 'copy')" :size="15" />
                  <Copy v-else :size="15" />
                  <span class="message-action-tooltip">复制</span>
                </button>
                <button
                  type="button"
                  class="message-action-button action-quote"
                  :disabled="messageActionDisabled(message)"
                  :data-message-action-key="messageActionKey(message, 'quote')"
                  aria-label="引用"
                  @mouseleave="clearMessageActionState(message, 'quote')"
                  @pointerleave="clearMessageActionState(message, 'quote')"
                  @blur="clearMessageActionState(message, 'quote')"
                  @click="quoteMessage(message)"
                >
                  <Check v-if="isMessageActionConfirmed(message, 'quote')" :size="15" />
                  <Quote v-else :size="15" />
                  <span class="message-action-tooltip">引用</span>
                </button>
                <button
                  type="button"
                  class="message-action-button action-feedback"
                  :class="{ active: message.feedback_status === 'open' }"
                  :disabled="messageFeedbackDisabled(message) || feedbackCancelSubmitting"
                  :aria-label="message.feedback_status === 'open' ? '取消异常反馈' : '回答有误'"
                  @click="handleFeedbackAction(message)"
                >
                  <Undo2 v-if="message.feedback_status === 'open'" :size="15" />
                  <CircleAlert v-else :size="15" />
                  <span class="message-action-tooltip">
                    {{ message.feedback_status === 'open' ? '取消异常反馈' : '回答有误' }}
                  </span>
                </button>
                <button
                  type="button"
                  class="message-action-button action-delete"
                  :disabled="messageDeleteDisabled(message)"
                  aria-label="删除"
                  @click="requestMessageDelete(message)"
                >
                  <LoaderCircle v-if="deletingMessageId === message.id" :size="15" class="spin" />
                  <Trash2 v-else :size="15" />
                  <span class="message-action-tooltip">删除</span>
                </button>
              </div>
              <div v-else class="message-actions-row user-actions" aria-label="用户消息操作">
                <button
                  type="button"
                  class="message-action-button action-copy"
                  :disabled="messageActionDisabled(message)"
                  :data-message-action-key="messageActionKey(message, 'copy')"
                  aria-label="复制"
                  @mouseleave="clearMessageActionState(message, 'copy')"
                  @pointerleave="clearMessageActionState(message, 'copy')"
                  @blur="clearMessageActionState(message, 'copy')"
                  @click="copyMessage(message)"
                >
                  <Check v-if="isMessageActionConfirmed(message, 'copy')" :size="15" />
                  <Copy v-else :size="15" />
                  <span class="message-action-tooltip">复制</span>
                </button>

                <button
                  type="button"
                  class="message-action-button action-delete"
                  :disabled="messageDeleteDisabled(message)"
                  aria-label="删除"
                  @click="requestMessageDelete(message)"
                >
                  <LoaderCircle v-if="deletingMessageId === message.id" :size="15" class="spin" />
                  <Trash2 v-else :size="15" />
                  <span class="message-action-tooltip">删除</span>
                </button>
              </div>
            </div>
          </article>
        </div>

        <form class="composer" @submit.prevent="submitComposer">
          <div class="composer-field">
            <div
              v-if="quotedMessage"
              class="composer-quote-card"
              role="button"
              tabindex="0"
              title="定位引用消息"
              aria-label="定位引用消息"
              @click="locateQuotedMessage"
              @keydown.enter.prevent="locateQuotedMessage"
              @keydown.space.prevent="locateQuotedMessage"
            >
              <Quote :size="15" />
              <span class="composer-quote-content">{{ quotedMessageSummary }}</span>
              <!-- 取消引用按钮使用 CSS 绘制红叉，避免图标字体加载或颜色继承导致圆形按钮空白。 -->
              <button
                type="button"
                class="composer-quote-close"
                aria-label="取消引用"
                @click.stop="chatStore.clearQuotedMessage()"
              >
                <span aria-hidden="true"></span>
              </button>
            </div>
            <textarea
              v-model="question"
              rows="2"
              :class="{ 'limit-reached': isComposerLimitReached }"
              :aria-invalid="isComposerOverLimit"
              aria-describedby="composer-limit-tip"
              @input="handleComposerInput"
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

      <div v-if="truncatedInputText" class="document-preview-modal" role="dialog" aria-modal="true">
        <section class="feedback-dialog input-limit-dialog">
          <header>
            <div>
              <strong>输入内容已达上限</strong>
              <span>输入框最多保留 {{ CHAT_MAX_QUESTION_CHARS }} 字，以下内容未被录入。</span>
            </div>
            <button type="button" class="icon-button" title="关闭" aria-label="关闭" @click="closeInputLimitDialog">
              <X :size="18" />
            </button>
          </header>

          <div class="input-limit-content">
            {{ truncatedInputText }}
          </div>

          <footer>
            <button type="button" class="primary" @click="closeInputLimitDialog">知道了</button>
          </footer>
        </section>
      </div>

      <ConfirmDialog
        v-if="conversationDeleteTarget"
        title="确认删除对话"
        :message="`将删除“${conversationDeleteTarget.title}”，删除后不可恢复。`"
        subject-label="1 个对话"
        detail="取消不会影响当前对话，确认删除后将刷新历史对话列表。"
        :busy="deletingConversationId === conversationDeleteTarget.id"
        @cancel="cancelConversationDelete"
        @confirm="confirmConversationDelete"
      />

      <ConfirmDialog
        v-if="messageDeleteTarget"
        title="确认删除消息"
        :message="messageDeleteMessage"
        :subject-label="messageDeleteSubject"
        detail="删除后当前页面将隐藏该消息，后台仍会保留删除人和删除时间用于审计追溯。"
        :busy="deletingMessageId === messageDeleteTarget.id"
        @cancel="cancelMessageDelete"
        @confirm="confirmMessageDelete"
      />

      <ConfirmDialog
        v-if="feedbackCancelTarget"
        title="取消异常反馈"
        message="将撤销本次“回答有误”标记，撤销后该反馈不再计入异常统计。"
        subject-label="1 条异常反馈"
        detail="系统仍会保留原反馈内容、撤销人和撤销时间用于审计追溯。"
        prompt="请确认是否取消异常反馈"
        confirm-text="确认取消反馈"
        :busy="feedbackCancelSubmitting"
        @cancel="cancelFeedbackCancel"
        @confirm="confirmCancelFeedback"
      />

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
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { Check, CircleAlert, Copy, LoaderCircle, MessageSquareText, Pencil, Plus, Quote, Search, SendHorizontal, Square, Trash2, Undo2, X } from 'lucide-vue-next'
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
  quotedMessage,
  loading,
  stoppingGeneration,
  deletingConversationId,
  deletingMessageId,
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
const feedbackCancelTarget = ref<Message | null>(null)
const feedbackCancelSubmitting = ref(false)
const feedbackError = ref('')
const feedbackToast = ref('')
const truncatedInputText = ref('')
const conversationDeleteTarget = ref<Conversation | null>(null)
const messageDeleteTarget = ref<Message | null>(null)
const confirmedMessageActionKeys = ref<Set<string>>(new Set())
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
const quotedMessageSummary = computed(() => summarizeQuotedMessage(quotedMessage.value?.content || ''))
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
const messageDeleteSubject = computed(() => {
  if (!messageDeleteTarget.value) return '1 条消息'
  return messageDeleteTarget.value.role === 'assistant' ? '1 条 AI 回复' : '1 条用户消息'
})
const messageDeleteMessage = computed(() => {
  if (!messageDeleteTarget.value) return ''
  return messageDeleteTarget.value.role === 'assistant'
    ? '将删除这条 AI 回复，删除后前端不再显示。'
    : '将删除这条用户消息，删除后前端不再显示。'
})

onMounted(async () => {
  chatStore.attachScrollTarget(messagesEl.value)
  window.addEventListener('pointermove', handleMessageActionPointerMove)
  window.addEventListener('mousemove', handleMessageActionPointerMove)
  await chatStore.initialize()
})

onBeforeUnmount(() => {
  if (conversationSearchTimer) window.clearTimeout(conversationSearchTimer)
  if (feedbackToastTimer) window.clearTimeout(feedbackToastTimer)
  window.removeEventListener('pointermove', handleMessageActionPointerMove)
  window.removeEventListener('mousemove', handleMessageActionPointerMove)
  chatStore.attachScrollTarget(null)
})

watch(messagesEl, (element) => {
  chatStore.attachScrollTarget(element)
})

watch(messages, () => {
  const validKeys = new Set(messages.value.map(messageKey))
  const next = new Set([...expandedAnswerKeys.value].filter((key) => validKeys.has(key)))
  if (next.size !== expandedAnswerKeys.value.size) expandedAnswerKeys.value = next
  const validActionKeys = new Set<string>()
  for (const message of messages.value) {
    validActionKeys.add(messageActionKey(message, 'copy'))
    if (message.role === 'assistant') validActionKeys.add(messageActionKey(message, 'quote'))
  }
  const nextActionKeys = new Set([...confirmedMessageActionKeys.value].filter((key) => validActionKeys.has(key)))
  if (nextActionKeys.size !== confirmedMessageActionKeys.value.size) confirmedMessageActionKeys.value = nextActionKeys
})

watch(conversationId, () => {
  // 反馈弹窗持有具体消息引用。切换会话时关闭弹窗，
  // 避免旧弹窗对新会话提交或取消反馈。
  if (!feedbackSubmitting.value) feedbackTarget.value = null
  if (!feedbackCancelSubmitting.value) feedbackCancelTarget.value = null
  feedbackError.value = ''
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
  void submitComposer()
}

async function submitComposer() {
  if (!question.value.trim()) {
    if (quotedMessage.value) showFeedbackToast('请输入追加内容后再发送')
    return
  }
  await chatStore.ask(question.value)
}

function handleComposerInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  const chars = Array.from(target.value)
  if (chars.length <= CHAT_MAX_QUESTION_CHARS) {
    question.value = target.value
    return
  }

  const keptText = chars.slice(0, CHAT_MAX_QUESTION_CHARS).join('')
  const discardedText = chars.slice(CHAT_MAX_QUESTION_CHARS).join('')
  question.value = keptText
  target.value = keptText
  if (discardedText) truncatedInputText.value = discardedText
}

function closeInputLimitDialog() {
  truncatedInputText.value = ''
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

function requestConversationDelete(item: Conversation) {
  if (deletingConversationId.value) return
  conversationDeleteTarget.value = item
}

function cancelConversationDelete() {
  if (deletingConversationId.value) return
  conversationDeleteTarget.value = null
}

async function confirmConversationDelete() {
  const target = conversationDeleteTarget.value
  if (!target) return
  await chatStore.deleteConversation(target)
  conversationDeleteTarget.value = null
}

function requestMessageDelete(message: Message) {
  if (messageDeleteDisabled(message) || deletingMessageId.value) return
  messageDeleteTarget.value = message
}

function cancelMessageDelete() {
  if (deletingMessageId.value) return
  messageDeleteTarget.value = null
}

async function confirmMessageDelete() {
  const target = messageDeleteTarget.value
  if (!target || deletingMessageId.value) return
  try {
    await chatStore.deleteMessage(target)
    showFeedbackToast('消息已删除')
    messageDeleteTarget.value = null
  } catch (error) {
    showFeedbackToast(apiErrorMessage(error, '删除失败，请稍后重试'))
  }
}

function messageActionDisabled(message: Message) {
  // 非删除操作只在消息未完成或无法持久化时禁用。
  // 流式生成期间，历史气泡仍可复制和引用。
  return (
    chatStore.isActiveAssistantMessage(message) ||
    !message.id ||
    !message.content
  )
}

function messageFeedbackDisabled(message: Message) {
  // 反馈操作只要求 AI 消息已经入库；即使回答内容为空，也允许用户标记异常。
  // 这样刷新或切换会话留下的空 AI 气泡仍能被反馈，不会被普通复制/引用的内容校验误伤。
  return message.role !== 'assistant' || chatStore.isActiveAssistantMessage(message) || !message.id
}

function messageDeleteDisabled(message: Message) {
  // 删除会改变持久化历史，因此在回答生成或停止生成期间全局禁用；
  // 即使其他气泡操作可用，也不能删除消息。
  // 删除只要求消息已经入库；空内容脏气泡也必须允许删除，避免用户无法清理历史脏记录。
  return (
    loading.value ||
    stoppingGeneration.value ||
    deletingMessageId.value === message.id ||
    chatStore.isActiveAssistantMessage(message) ||
    !message.id
  )
}

function messageActionKey(message: Message, action: 'copy' | 'quote') {
  return `${messageKey(message)}:${action}`
}

function isMessageActionConfirmed(message: Message, action: 'copy' | 'quote') {
  return confirmedMessageActionKeys.value.has(messageActionKey(message, action))
}

function setMessageActionConfirmed(message: Message, action: 'copy' | 'quote') {
  const next = new Set(confirmedMessageActionKeys.value)
  next.add(messageActionKey(message, action))
  confirmedMessageActionKeys.value = next
}

function clearMessageActionState(message: Message, action: 'copy' | 'quote') {
  const key = messageActionKey(message, action)
  if (!confirmedMessageActionKeys.value.has(key)) return
  const next = new Set(confirmedMessageActionKeys.value)
  next.delete(key)
  confirmedMessageActionKeys.value = next
}

function handleMessageActionPointerMove(event: MouseEvent | PointerEvent) {
  if (!confirmedMessageActionKeys.value.size) return
  const target = event.target instanceof Element ? event.target : null
  const actionButton = target?.closest('[data-message-action-key]') as HTMLElement | null
  const hoveredKey = actionButton?.dataset.messageActionKey
  const next = new Set([...confirmedMessageActionKeys.value].filter((key) => key === hoveredKey))
  if (next.size !== confirmedMessageActionKeys.value.size) confirmedMessageActionKeys.value = next
}

async function copyMessage(message: Message) {
  if (messageActionDisabled(message)) return
  setMessageActionConfirmed(message, 'copy')
  try {
    await writeClipboardText(displayMessageContent(message))
    showFeedbackToast('复制成功')
  } catch (error) {
    showFeedbackToast(apiErrorMessage(error, '复制失败，请手动选择文本复制'))
  }
}

function quoteMessage(message: Message) {
  // 引用按钮只对已完成的 AI 回复生效；正在生成的回复没有稳定内容，不允许引用。
  if (message.role !== 'assistant' || messageActionDisabled(message)) return
  chatStore.quoteMessage(message)
  setMessageActionConfirmed(message, 'quote')
  showFeedbackToast('已添加引用')
}

function summarizeQuotedMessage(content: string) {
  // 引用卡片只展示摘要，完整文本保存在 store/后端字段里参与提问上下文。
  // 使用 Array.from 按字符截断，避免中文或 emoji 被半截切开。
  const normalized = content.replace(/\s+/g, ' ').trim()
  const chars = Array.from(normalized)
  if (chars.length <= 56) return normalized
  return `${chars.slice(0, 56).join('')}...`
}

function locateQuotedMessage() {
  // 输入框里的引用卡片定位当前页面中的被引用 AI 回复。
  // 未入库的乐观消息依赖 localId，已入库消息依赖后端 id。
  const key = quotedMessage.value?.key
  if (!key || !messagesEl.value) return
  const target = messagesEl.value.querySelector(`[data-message-key="${cssEscape(key)}"]`) as HTMLElement | null
  if (!target) return
  target.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function hasQuotedMessage(message: Message) {
  // 历史消息从后端拿 quoted_message_content；乐观消息发送时也会填这个字段。
  // 只在用户消息上展示引用预览，AI 回复自己的引用关系不在气泡内展示。
  return message.role === 'user' && Boolean(message.quoted_message_content?.trim())
}

function displayMessageContent(message: Message) {
  if (!hasQuotedMessage(message)) return message.content
  const marker = '用户追加问题：'
  const content = message.content || ''
  const markerIndex = content.lastIndexOf(marker)
  if (!content.startsWith('引用内容：') || markerIndex < 0) return content
  return content.slice(markerIndex + marker.length).trim()
}

function locateMessageQuote(message: Message) {
  // 用户消息气泡内的引用预览只拿后端消息 id 定位。
  // 如果被引用消息已被删除或旧数据没有引用 id，则保持静默，不打断用户阅读。
  const messageId = message.quoted_message_id
  if (!messageId || !messagesEl.value) return
  const target = messagesEl.value.querySelector(`[data-message-id="${cssEscape(messageId)}"]`) as HTMLElement | null
  if (!target) return
  target.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function cssEscape(value: string) {
  // data 属性查询需要转义消息 id/localId，避免特殊字符破坏 CSS selector。
  if (window.CSS?.escape) return window.CSS.escape(value)
  return value.replace(/["\\]/g, '\\$&')
}
async function writeClipboardText(text: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', 'true')
  textarea.style.position = 'fixed'
  textarea.style.left = '-9999px'
  document.body.appendChild(textarea)
  textarea.select()
  const copied = document.execCommand('copy')
  document.body.removeChild(textarea)
  if (!copied) throw new Error('copy command failed')
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

function handleFeedbackAction(message: Message) {
  if (messageFeedbackDisabled(message) || feedbackCancelSubmitting.value) return
  // 反馈按钮是双状态控件：已有有效反馈时进入取消确认，
  // 否则打开可编辑、可预填的提交表单。
  if (message.feedback_status === 'open') {
    feedbackCancelTarget.value = message
    return
  }
  openFeedbackDialog(message)
}

function openFeedbackDialog(message: Message) {
  feedbackTarget.value = message
  feedbackType.value = message.feedback_error_type || 'answer_wrong'
  feedbackDescription.value = message.feedback_description || ''
  feedbackError.value = ''
}

function cancelFeedbackCancel() {
  if (feedbackCancelSubmitting.value) return
  feedbackCancelTarget.value = null
}

async function confirmCancelFeedback() {
  if (!feedbackCancelTarget.value || feedbackCancelSubmitting.value) return
  feedbackCancelSubmitting.value = true
  try {
    await chatStore.cancelAnswerFeedback(feedbackCancelTarget.value)
    feedbackCancelTarget.value = null
    showFeedbackToast('已取消异常反馈')
  } catch (error) {
    showFeedbackToast(apiErrorMessage(error, '取消反馈失败，请稍后重试'))
  } finally {
    feedbackCancelSubmitting.value = false
  }
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
    // 补充说明为选填项，提交前仅做去空格规整，允许空字符串正常入库。
    await chatStore.submitAnswerFeedback(
      feedbackTarget.value,
      feedbackType.value,
      feedbackDescription.value.trim()
    )
    feedbackSubmitting.value = false
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

function citationTags(source: any) {
  if (!Array.isArray(source?.tags)) return []
  return source.tags.map((tag: unknown) => String(tag).trim()).filter(Boolean)
}

function qaCitationTags(message: Message) {
  const tags = new Map<string, { key: string; tag: string }>()
  for (const source of message.citations || []) {
    const sourceTags = citationTags(source)
    if (!source.qa_pair_id || !sourceTags.length) continue
    for (const tag of sourceTags) {
      // 问答命中不再混入普通“参考来源”行，标签本身作为可跳转引用入口，避免无文档来源时显示“暂未找到明确资料”。
      const key = `${source.qa_pair_id}:${tag}`
      if (!tags.has(key)) tags.set(key, { key, tag })
    }
  }
  return [...tags.values()]
}

function documentCitations(message: Message) {
  return (message.citations || []).filter((source) => {
    // 带问答记录编号且有标签的引用代表单条问答命中，按需求展示到“标签”区域；普通文档仍保留参考来源模板。
    return !(source.qa_pair_id && citationTags(source).length)
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
