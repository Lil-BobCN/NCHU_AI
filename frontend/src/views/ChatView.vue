<template>
  <AppShell>
    <div class="chat-layout">
      <section class="conversation-list">
        <div class="conversation-list-head">
          <div>
            <strong>历史对话</strong>
            <span>{{ conversations.length }} 条</span>
          </div>
          <button class="icon-button primary" title="新建对话" aria-label="新建对话" @click="chatStore.newConversation">
            <Plus :size="18" />
          </button>
        </div>

        <div class="conversation-scroll">
          <div
            v-for="item in conversations"
            :key="item.id"
            class="conversation-row"
            :class="{ active: item.id === conversationId }"
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

          <div v-if="!conversations.length" class="conversation-empty">暂无历史对话</div>
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

          <article v-for="message in messages" :key="message.id || message.localId" :class="['message', message.role]">
            <div class="bubble">
              <div
                v-if="message.content && message.role === 'assistant'"
                class="markdown-content"
                v-html="renderMarkdown(message.content)"
              />
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

              <div v-if="message.citations?.length" class="citations">
                <strong>参考来源</strong>
                <div v-for="(source, index) in message.citations" :key="index" class="citation-item">
                  <a :href="source.url" target="_blank">
                    {{ index + 1 }}. {{ source.document_title || source.document_name }}
                    <span v-if="source.page_start">，第 {{ source.page_start }} 页</span>
                    <span v-if="source.page_end && source.page_end !== source.page_start">-{{ source.page_end }} 页</span>
                    <span v-if="source.section_path">，{{ source.section_path }}</span>
                  </a>
                  <blockquote v-if="source.evidence" class="citation-evidence">
                    {{ source.evidence }}
                  </blockquote>
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
          <textarea
            v-model="question"
            rows="2"
            placeholder="输入问题，支持连续追问"
            @keydown.enter="handleComposerEnter"
          />
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
          <button v-else class="primary send-button" :disabled="!question.trim()" title="发送" aria-label="发送">
            <SendHorizontal :size="18" />
            <span>发送</span>
          </button>
        </form>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import AppShell from '../components/AppShell.vue'
import { Check, LoaderCircle, MessageSquareText, Pencil, Plus, SendHorizontal, Square, Trash2, Undo2, X } from 'lucide-vue-next'
import { useChatStreamStore, type Conversation, type Message } from '../stores/chatStream'

const chatStore = useChatStreamStore()
const {
  conversations,
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

onMounted(async () => {
  chatStore.attachScrollTarget(messagesEl.value)
  await chatStore.initialize()
})

onBeforeUnmount(() => {
  chatStore.attachScrollTarget(null)
})

watch(messagesEl, (element) => {
  chatStore.attachScrollTarget(element)
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

  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) {
      flushParagraph()
      flushList()
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
