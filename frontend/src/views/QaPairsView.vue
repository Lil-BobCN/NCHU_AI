<template>
  <AppShell>
    <div class="page two-column">
      <section class="panel workspace-panel">
        <header class="panel-header">
          <div>
            <h1>QA 问答对</h1>
            <p>维护高频标准问答，作为检索召回的补充来源。</p>
          </div>
          <button class="primary qa-create-button" @click="save">新增问答</button>
        </header>

        <div class="form-grid">
          <label>
            问题
            <textarea v-model="form.question" rows="3" placeholder="请输入标准问题" />
          </label>
          <label>
            答案
            <textarea v-model="form.answer" rows="6" placeholder="请输入标准答案" />
          </label>
          <section class="qa-tag-field" aria-label="问答标签选择">
            <div class="qa-tag-field-head">
              <strong>标签</strong>
              <button type="button" @click="openTagManager">管理标签</button>
            </div>
            <TagSelector
              :selected-tags="selectedTags"
              :tag-options="tagLibrary"
              empty-text="暂无已选标签"
              @toggle="toggleCreateTag"
              @remove="removeCreateTag"
            />
          </section>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
      </section>

      <section class="panel qa-list-panel">
        <header class="panel-header">
          <div>
            <h2>问答列表</h2>
            <p>{{ items.length }} 条</p>
          </div>
          <div class="qa-toolbar">
            <div class="qa-filter-field">
              <span class="qa-filter-label">标签筛选</span>
              <div class="qa-filter-select" @keydown.esc="tagFilterOpen = false">
                <button
                  type="button"
                  class="qa-filter-trigger"
                  :aria-expanded="tagFilterOpen"
                  aria-haspopup="listbox"
                  @click="tagFilterOpen = !tagFilterOpen"
                >
                  <span>{{ selectedTag || '全部标签' }}</span>
                  <span class="qa-filter-caret" aria-hidden="true"></span>
                </button>
                <div v-if="tagFilterOpen" class="qa-filter-menu" role="listbox">
                  <button
                    type="button"
                    class="qa-filter-option"
                    :class="{ active: !selectedTag }"
                    role="option"
                    :aria-selected="!selectedTag"
                    @click="selectTagFilter('')"
                  >
                    全部标签
                  </button>
                  <button
                    v-for="tag in availableTags"
                    :key="tag"
                    type="button"
                    class="qa-filter-option"
                    :class="{ active: selectedTag === tag }"
                    role="option"
                    :aria-selected="selectedTag === tag"
                    @click="selectTagFilter(tag)"
                  >
                    {{ tag }}
                  </button>
                </div>
              </div>
            </div>
            <button type="button" class="qa-toolbar-manage" @click="openTagManager">标签管理</button>
          </div>
        </header>

        <article v-for="item in items" :key="item.id" class="qa-item">
          <div class="qa-item-content">
            <h3 class="qa-title">{{ item.question }}</h3>
            <p class="qa-answer">{{ item.answer }}</p>
            <div v-if="item.tags?.length" class="tag-list" aria-label="问答标签">
              <span v-for="tag in item.tags" :key="tag" class="tag-chip">{{ tag }}</span>
            </div>
          </div>
          <div class="qa-actions">
            <button
              class="qa-state-action"
              :class="{ enabled: item.status === 'enabled', disabled: item.status !== 'enabled' }"
              @click="toggle(item)"
            >
              {{ item.status === 'enabled' ? '停用' : '启用' }}
            </button>
            <button class="qa-edit-action" @click="openEditDialog(item)">编辑</button>
            <button class="danger" @click="requestRemove(item)">删除</button>
          </div>
        </article>

        <p v-if="!items.length" class="empty-state">暂无问答对</p>
      </section>

      <ConfirmDialog
        v-if="deleteTarget"
        title="确认删除问答对"
        :message="`将删除“${deleteTarget.question}”，删除后不可恢复。`"
        subject-label="1 个问答对"
        detail="取消不会影响当前问答对，确认删除后将刷新问答列表。"
        @cancel="cancelRemove"
        @confirm="confirmRemove"
      />

      <ConfirmDialog
        v-if="requiredDialog"
        title="请完善必填内容"
        :message="requiredDialog.message"
        :subject-label="requiredDialog.subject"
        detail="标签字段可以为空，补充必填内容后即可保存问答对。"
        prompt="以下字段不能为空"
        cancel-text="知道了"
        confirm-text="去填写"
        @cancel="closeRequiredDialog"
        @confirm="closeRequiredDialog"
      />

      <ConfirmDialog
        v-if="duplicateQuestionDialog"
        title="当前已经存在该问答"
        message="当前已经存在该问答"
        subject-label="重复问答"
        detail="问题字符串完全一致时不能重复新增；如需调整内容，请在右侧列表中编辑已有问答。"
        prompt="已拦截重复新增"
        cancel-text="知道了"
        confirm-text="去查看"
        @cancel="closeDuplicateQuestionDialog"
        @confirm="closeDuplicateQuestionDialog"
      />

      <div v-if="editDialog" class="document-preview-modal" role="dialog" aria-modal="true">
        <form class="qa-edit-dialog" @submit.prevent="saveEditDialog">
          <header class="duplicate-upload-head">
            <div>
              <strong>编辑问答对</strong>
              <p>修改当前问答记录的信息，标签可为空。</p>
            </div>
            <button type="button" class="icon-button" title="关闭" aria-label="关闭" @click="closeEditDialog">×</button>
          </header>

          <div class="duplicate-upload-body qa-edit-body">
            <label>
              问题
              <textarea v-model="editDialog.question" rows="3" placeholder="请输入标准问题" />
            </label>
            <label>
              答案
              <textarea v-model="editDialog.answer" rows="6" placeholder="请输入标准答案" />
            </label>
            <section class="qa-tag-field" aria-label="编辑问答标签">
              <div class="qa-tag-field-head">
                <strong>标签</strong>
                <button type="button" @click="openTagManager">管理标签</button>
              </div>
              <TagSelector
                :selected-tags="editDialog.selectedTags"
                :tag-options="tagLibrary"
                empty-text="暂无已选标签"
                @toggle="toggleEditTag"
                @remove="removeEditTag"
              />
            </section>
            <label>
              状态
              <select v-model="editDialog.status">
                <option value="enabled">启用</option>
                <option value="disabled">停用</option>
              </select>
            </label>
            <p v-if="editError" class="error">{{ editError }}</p>
          </div>

          <footer class="duplicate-upload-actions">
            <button type="button" @click="closeEditDialog">取消</button>
            <button class="primary" type="submit">确认保存</button>
          </footer>
        </form>
      </div>

      <div v-if="tagManagerOpen" class="document-preview-modal" role="dialog" aria-modal="true">
        <section class="qa-tag-manager">
          <header class="duplicate-upload-head">
            <div>
              <strong>标签管理</strong>
              <p>维护 QA 问答对可选的标准问题分类标签。</p>
            </div>
            <button type="button" class="icon-button" title="关闭" aria-label="关闭" @click="closeTagManager">×</button>
          </header>

          <div class="duplicate-upload-body qa-tag-manager-body">
            <div class="qa-tag-manager-tools">
              <input
                v-model="tagSearchDraft"
                placeholder="搜索标签"
                @keyup.enter="applyTagManagerSearch"
              />
              <button type="button" class="qa-tag-manager-search" @click="applyTagManagerSearch">搜索</button>
              <form class="qa-tag-create" @submit.prevent="createTag">
                <input v-model="newTagName" placeholder="新增标签" />
                <button class="primary" type="submit" :disabled="tagSaving">新增标签</button>
              </form>
            </div>

            <p v-if="tagManagerError" class="error">{{ tagManagerError }}</p>
            <div class="qa-tag-batch-bar">
              <span>已选 {{ selectedManagedTagCount }} 个标签</span>
              <button type="button" :disabled="!selectedManagedTagCount || tagSaving" @click="requestBatchRemoveTags">
                批量删除
              </button>
              <button type="button" :disabled="!selectedManagedTagCount || tagSaving" @click="clearManagedTagSelection">
                清空选择
              </button>
            </div>

            <div class="qa-tag-table" role="table" aria-label="标签管理列表">
              <div class="qa-tag-table-head" role="row">
                <span class="qa-tag-select-cell">
                  <input
                    type="checkbox"
                    :checked="allFilteredTagsSelected"
                    :disabled="!filteredTagLibrary.length || tagSaving"
                    aria-label="选择当前筛选结果中的全部标签"
                    @change="toggleAllFilteredTags"
                  />
                </span>
                <span>标签名称</span>
                <button type="button" class="qa-sort-title" @click="toggleUsageSort">
                  使用次数 <span>{{ usageSortArrow }}</span>
                </button>
                <button type="button" class="qa-sort-title" @click="toggleTimeSort">
                  创建时间 <span>{{ timeSortArrow }}</span>
                </button>
                <span>操作</span>
              </div>
              <div v-for="tag in filteredTagLibrary" :key="tag.id" class="qa-tag-table-row" role="row">
                <span class="qa-tag-select-cell">
                  <input
                    type="checkbox"
                    :checked="isManagedTagSelected(tag.id)"
                    :disabled="tagSaving"
                    :aria-label="`选择标签 ${tag.name}`"
                    @change="toggleManagedTagSelection(tag.id)"
                  />
                </span>
                <span>
                  <input
                    v-if="editingTagId === tag.id"
                    v-model="editingTagName"
                    class="qa-tag-edit-input"
                    aria-label="编辑标签名称"
                  />
                  <strong v-else>{{ tag.name }}</strong>
                </span>
                <span>{{ tag.usage_count }}</span>
                <span>{{ formatTagTime(tag.created_at) }}</span>
                <span class="qa-tag-row-actions">
                  <template v-if="editingTagId === tag.id">
                    <button type="button" :disabled="tagSaving" @click="saveTagName(tag)">保存</button>
                    <button type="button" :disabled="tagSaving" @click="cancelTagEdit">取消</button>
                  </template>
                  <template v-else>
                    <button type="button" class="success" @click="startTagEdit(tag)">编辑</button>
                    <button type="button" class="danger" :disabled="tagSaving" @click="requestRemoveTag(tag)">
                      删除
                    </button>
                  </template>
                </span>
              </div>
            </div>
            <p v-if="!filteredTagLibrary.length" class="empty-state">暂无标签</p>
          </div>
        </section>
      </div>

      <ConfirmDialog
        v-if="tagDeleteTarget"
        title="确认删除标签"
        :message="`将删除标签“${tagDeleteTarget.name}”，并从已有问答对中移除该标签。`"
        subject-label="1 个标签"
        detail="取消不会影响当前标签；确认删除后，标签库记录会被删除，已关联问答对上的该标签也会同步移除。"
        :busy="tagSaving"
        @cancel="cancelRemoveTag"
        @confirm="confirmRemoveTag"
      />

      <ConfirmDialog
        v-if="tagBatchDeleteConfirm"
        title="确认批量删除标签"
        :message="`将删除已选 ${selectedManagedTagCount} 个标签，并从已有问答对中同步移除这些标签。`"
        :subject-label="`${selectedManagedTagCount} 个标签`"
        :detail="batchDeleteTagDetail"
        prompt="请确认是否继续批量删除"
        confirm-text="确认批量删除"
        :busy="tagSaving"
        @cancel="cancelBatchRemoveTags"
        @confirm="confirmBatchRemoveTags"
      />
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, reactive, ref, watch } from 'vue'
import type { PropType } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '../components/AppShell.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { api, apiErrorMessage, unwrap } from '../api/client'

type QaTag = {
  id: string
  name: string
  status: 'enabled' | 'disabled'
  usage_count: number
  created_at?: string | null
  updated_at?: string | null
}

type SortDirection = 'asc' | 'desc'

type EditDialogState = {
  id: string
  question: string
  answer: string
  status: string
  selectedTags: string[]
}

const TagSelector = defineComponent({
  name: 'TagSelector',
  props: {
    selectedTags: { type: Array as PropType<string[]>, required: true },
    tagOptions: { type: Array as PropType<QaTag[]>, required: true },
    emptyText: { type: String, default: '暂无已选标签' }
  },
  emits: ['toggle', 'remove'],
  setup(props, { emit }) {
    // 搜索框输入先进入草稿值，点击搜索或回车后才真正过滤，避免用户打字时列表频繁跳动。
    const searchDraft = ref('')
    const optionKeyword = ref('')
    // 用规范化后的标签名判断选中状态，避免前后空格导致同名标签无法取消或重复选中。
    const selectedSet = computed(() => new Set(props.selectedTags.map((tag) => normalizeTagName(tag))))
    const optionNames = computed(() => new Set(props.tagOptions.map((tag) => normalizeTagName(tag.name))))
    // 可选项以启用标签库为主；如果历史记录里已有库外标签，只保留在已选区用于展示和移除。
    const selectableTags = computed(() => [
      ...props.tagOptions.filter((tag) => tag.status === 'enabled'),
      ...props.selectedTags
        .filter((tag) => !optionNames.value.has(normalizeTagName(tag)))
        .map((tag) => ({ id: `selected-${tag}`, name: tag, status: 'disabled' as const, usage_count: 0 }))
    ])
    const filteredSelectableTags = computed(() => {
      // 全部标签区域的搜索只做前端本地过滤，不改变后端标签库和当前已选标签。
      const keyword = normalizeTagName(optionKeyword.value)
      if (!keyword) return selectableTags.value
      return selectableTags.value.filter((tag) => normalizeTagName(tag.name).includes(keyword))
    })
    const applySearch = () => {
      optionKeyword.value = searchDraft.value
    }

    return () =>
      h('div', { class: 'qa-tag-selector' }, [
        h('div', { class: 'qa-tag-selected-block' }, [
          h('strong', '已选标签'),
          props.selectedTags.length
            ? h(
                'div',
                { class: 'tag-list' },
                props.selectedTags.map((tag) =>
                  h('span', { class: 'tag-chip tag-preview-chip', key: tag }, [
                    h('span', { class: 'tag-preview-label' }, tag),
                    h('button', {
                      type: 'button',
                      class: 'tag-remove-button',
                      title: `取消选择 ${tag}`,
                      'aria-label': `取消选择 ${tag}`,
                      onClick: () => emit('remove', tag)
                    })
                  ])
                )
              )
            : h('span', { class: 'tag-preview-empty' }, props.emptyText)
        ]),
        h('div', { class: 'qa-tag-option-block' }, [
          h('strong', '全部标签'),
          h('div', { class: 'qa-tag-option-search' }, [
            h('input', {
              value: searchDraft.value,
              placeholder: '搜索标签',
              'aria-label': '搜索全部标签',
              onInput: (event: Event) => {
                searchDraft.value = (event.target as HTMLInputElement).value
              },
              onKeydown: (event: KeyboardEvent) => {
                if (event.key === 'Enter') applySearch()
              }
            }),
            h('button', { type: 'button', onClick: applySearch }, '搜索')
          ]),
          filteredSelectableTags.value.length
            ? h(
                'div',
                { class: 'qa-tag-checkbox-grid' },
                filteredSelectableTags.value.map((tag) =>
                  h('label', { key: tag.id || tag.name, class: 'qa-tag-checkbox' }, [
                    h('input', {
                      type: 'checkbox',
                      checked: selectedSet.value.has(normalizeTagName(tag.name)),
                      disabled: tag.status !== 'enabled' && !selectedSet.value.has(normalizeTagName(tag.name)),
                      onChange: () => emit('toggle', tag.name)
                    }),
                    h('span', tag.name)
                  ])
                )
              )
            : h('span', { class: 'tag-preview-empty' }, optionKeyword.value ? '没有匹配的标签' : '暂无可选标签')
        ])
      ])
  }
})

const route = useRoute()
const router = useRouter()
const items = ref<any[]>([])
const availableTags = ref<string[]>([])
const selectedTags = ref<string[]>([])
const tagLibrary = ref<QaTag[]>([])
const form = reactive({ question: '', answer: '', status: 'enabled' })
const error = ref('')
const editError = ref('')
const selectedTag = ref(routeTagFilter())
const tagFilterOpen = ref(false)
const deleteTarget = ref<any | null>(null)
const requiredDialog = ref<{ message: string; subject: string } | null>(null)
const duplicateQuestionDialog = ref(false)
const editDialog = ref<EditDialogState | null>(null)
const tagManagerOpen = ref(false)
const tagSearch = ref('')
const tagSearchDraft = ref('')
const newTagName = ref('')
const tagManagerError = ref('')
const tagSaving = ref(false)
const editingTagId = ref('')
const editingTagName = ref('')
const tagDeleteTarget = ref<QaTag | null>(null)
const selectedManagedTagIds = ref<Set<string>>(new Set())
const tagBatchDeleteConfirm = ref(false)
const usageSortDirection = ref<SortDirection>('asc')
const timeSortDirection = ref<SortDirection>('desc')

const usageSortArrow = computed(() => (usageSortDirection.value === 'asc' ? '↑' : '↓'))
const timeSortArrow = computed(() => (timeSortDirection.value === 'asc' ? '↑' : '↓'))
const selectedManagedTagCount = computed(() => selectedManagedTagIds.value.size)
const selectedManagedTags = computed(() =>
  tagLibrary.value.filter((tag) => selectedManagedTagIds.value.has(tag.id))
)
const allFilteredTagsSelected = computed(
  () =>
    filteredTagLibrary.value.length > 0 &&
    filteredTagLibrary.value.every((tag) => selectedManagedTagIds.value.has(tag.id))
)
const batchDeleteTagDetail = computed(() => {
  const names = selectedManagedTags.value.map((tag) => tag.name)
  if (!names.length) return '取消不会影响当前标签；确认删除后，标签库和已关联问答对会同步更新。'
  const preview = names.slice(0, 8).join('、')
  const suffix = names.length > 8 ? ` 等 ${names.length} 个标签` : ''
  return `将删除：${preview}${suffix}。取消不会影响当前标签；确认删除后不可恢复。`
})

const filteredTagLibrary = computed(() => {
  // 标签管理弹窗先按搜索关键字过滤，再执行“使用次数 + 创建时间”的组合排序。
  const keyword = normalizeTagName(tagSearch.value)
  const filtered = keyword
    ? tagLibrary.value.filter((tag) => normalizeTagName(tag.name).includes(keyword))
    : [...tagLibrary.value]
  const usageDirection = usageSortDirection.value === 'asc' ? 1 : -1
  const timeDirection = timeSortDirection.value === 'asc' ? 1 : -1
  return filtered.sort((left, right) => {
    // 两个排序条件不互斥：先比较使用次数，次数相同再比较创建时间，最后按中文名称兜底保证顺序稳定。
    return (
      compareNumber(left.usage_count, right.usage_count, usageDirection) ||
      compareNumber(tagTimeValue(left.created_at), tagTimeValue(right.created_at), timeDirection) ||
      left.name.localeCompare(right.name, 'zh-Hans-CN')
    )
  })
})

onMounted(async () => {
  await Promise.all([load(), loadTagLibrary()])
})

watch(
  () => route.query.tag,
  () => {
    const nextTag = routeTagFilter()
    if (selectedTag.value === nextTag) return
    selectedTag.value = nextTag
    void load()
  }
)

function routeTagFilter() {
  const rawTag = route.query.tag
  // 智能对话里的标签块会通过问答列表地址携带标签参数跳转过来；这里做一次规整，确保刷新页面和同页跳转都能直接进入对应筛选结果。
  if (Array.isArray(rawTag)) return rawTag[0] || ''
  return typeof rawTag === 'string' ? rawTag : ''
}

async function applyTagFilter() {
  // 用户在问答列表里手动切换标签时同步地址栏，保证聊天标签跳转、刷新页面和下拉筛选三条路径使用同一套筛选入口。
  const { tag: _tag, ...queryWithoutTag } = route.query
  const query = selectedTag.value ? { ...queryWithoutTag, tag: selectedTag.value } : queryWithoutTag
  await router.replace({ path: '/qa-pairs', query })
  await load()
}

async function selectTagFilter(tag: string) {
  selectedTag.value = tag
  tagFilterOpen.value = false
  await applyTagFilter()
}

async function load() {
  try {
    const params = selectedTag.value ? { tag: selectedTag.value } : undefined
    const data = unwrap<any>(await api.get('/qa-pairs', { params }))
    items.value = data.items
    availableTags.value = data.available_tags || []
  } catch (err) {
    error.value = apiErrorMessage(err, '加载问答对失败')
  }
}

async function loadTagLibrary() {
  try {
    tagLibrary.value = unwrap<QaTag[]>(await api.get('/qa-tags'))
    reconcileManagedTagSelection()
  } catch (err) {
    tagManagerError.value = apiErrorMessage(err, '加载标签失败')
  }
}

function normalizeTagName(value: string) {
  // 前端先做一次轻量规范化，和后端标签清洗规则保持一致，减少重复标签和空标签提交。
  return String(value || '').trim().replace(/\s+/g, ' ')
}

function normalizeSelectedTags(values: string[]) {
  // 已选标签在进入请求体前统一去重，保留用户首次看到的展示名称。
  const result: string[] = []
  const seen = new Set<string>()
  for (const value of values) {
    const tag = normalizeTagName(value)
    const key = tag.toLocaleLowerCase()
    if (!tag || seen.has(key)) continue
    result.push(tag)
    seen.add(key)
  }
  return result
}

function compareNumber(left: number, right: number, direction: number) {
  if (left === right) return 0
  return left > right ? direction : -direction
}

function tagTimeValue(value?: string | null) {
  if (!value) return 0
  const time = new Date(value).getTime()
  return Number.isFinite(time) ? time : 0
}

function formatTagTime(value?: string | null) {
  // 后端返回 ISO 时间；界面展示为本地中文时间，解析失败时降级为短横线。
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function toggleUsageSort() {
  // 只切换使用次数方向，不重置创建时间方向，避免两个排序条件互相覆盖。
  usageSortDirection.value = usageSortDirection.value === 'asc' ? 'desc' : 'asc'
}

function toggleTimeSort() {
  // 只切换创建时间方向；默认 desc 表示越接近当前时间越靠上。
  timeSortDirection.value = timeSortDirection.value === 'asc' ? 'desc' : 'asc'
}

function toggleTag(list: string[], tag: string) {
  // checkbox 勾选和 chip 删除共用同一套切换逻辑，保证新增/编辑弹窗行为一致。
  const cleanTag = normalizeTagName(tag)
  const key = cleanTag.toLocaleLowerCase()
  const exists = list.some((item) => normalizeTagName(item).toLocaleLowerCase() === key)
  return exists ? list.filter((item) => normalizeTagName(item).toLocaleLowerCase() !== key) : [...list, cleanTag]
}

function toggleCreateTag(tag: string) {
  selectedTags.value = normalizeSelectedTags(toggleTag(selectedTags.value, tag))
}

function removeCreateTag(tag: string) {
  selectedTags.value = normalizeSelectedTags(toggleTag(selectedTags.value, tag))
}

function toggleEditTag(tag: string) {
  if (!editDialog.value) return
  editDialog.value.selectedTags = normalizeSelectedTags(toggleTag(editDialog.value.selectedTags, tag))
}

function removeEditTag(tag: string) {
  if (!editDialog.value) return
  editDialog.value.selectedTags = normalizeSelectedTags(toggleTag(editDialog.value.selectedTags, tag))
}

async function save() {
  error.value = ''
  const question = form.question.trim()
  const answer = form.answer.trim()
  if (!question || !answer) {
    const missing = [
      !question ? '问题' : '',
      !answer ? '答案' : ''
    ].filter(Boolean)
    requiredDialog.value = {
      message: `请填写${missing.join('、')}后再保存。`,
      subject: missing.join('、')
    }
    return
  }
  if (items.value.some((item) => item.question === question)) {
    openDuplicateQuestionDialog()
    return
  }
  const payload = {
    question,
    answer,
    status: form.status,
    tags: normalizeSelectedTags(selectedTags.value)
  }
  try {
    await api.post('/qa-pairs', payload)
    form.question = ''
    form.answer = ''
    selectedTags.value = []
    await Promise.all([load(), loadTagLibrary()])
  } catch (err) {
    const message = apiErrorMessage(err, '保存问答对失败')
    if (message === '当前已经存在该问答') {
      openDuplicateQuestionDialog()
      return
    }
    error.value = message
  }
}

async function toggle(item: any) {
  error.value = ''
  try {
    await api.patch(`/qa-pairs/${item.id}/status`, { status: item.status === 'enabled' ? 'disabled' : 'enabled' })
    await load()
  } catch (err) {
    error.value = apiErrorMessage(err, '更新问答状态失败')
  }
}

function requestRemove(item: any) {
  deleteTarget.value = item
}

function cancelRemove() {
  deleteTarget.value = null
}

function closeRequiredDialog() {
  requiredDialog.value = null
}

function openDuplicateQuestionDialog() {
  duplicateQuestionDialog.value = true
}

function closeDuplicateQuestionDialog() {
  duplicateQuestionDialog.value = false
}

function openEditDialog(item: any) {
  editError.value = ''
  editDialog.value = {
    id: item.id,
    question: item.question || '',
    answer: item.answer || '',
    status: item.status || 'enabled',
    selectedTags: normalizeSelectedTags(item.tags || [])
  }
}

function closeEditDialog() {
  editDialog.value = null
  editError.value = ''
}

async function saveEditDialog() {
  if (!editDialog.value) return
  editError.value = ''
  const question = editDialog.value.question.trim()
  const answer = editDialog.value.answer.trim()
  if (!question || !answer) {
    const missing = [
      !question ? '问题' : '',
      !answer ? '答案' : ''
    ].filter(Boolean)
    editError.value = `请填写${missing.join('、')}后再保存。`
    return
  }
  try {
    await api.put(`/qa-pairs/${editDialog.value.id}`, {
      question,
      answer,
      status: editDialog.value.status,
      tags: normalizeSelectedTags(editDialog.value.selectedTags)
    })
    closeEditDialog()
    await Promise.all([load(), loadTagLibrary()])
  } catch (err) {
    editError.value = apiErrorMessage(err, '保存问答对失败')
  }
}

async function confirmRemove() {
  const target = deleteTarget.value
  if (!target) return
  deleteTarget.value = null
  error.value = ''
  try {
    await api.delete(`/qa-pairs/${target.id}`)
    await Promise.all([load(), loadTagLibrary()])
  } catch (err) {
    error.value = apiErrorMessage(err, '删除问答对失败')
  }
}

function openTagManager() {
  tagManagerOpen.value = true
  tagManagerError.value = ''
  void loadTagLibrary()
}

function closeTagManager() {
  tagManagerOpen.value = false
  tagSearch.value = ''
  tagSearchDraft.value = ''
  newTagName.value = ''
  tagManagerError.value = ''
  clearManagedTagSelection()
  tagBatchDeleteConfirm.value = false
  cancelTagEdit()
}

function applyTagManagerSearch() {
  // 标签管理搜索采用显式按钮触发，避免表格在输入过程中不断重新排序和跳动。
  tagSearch.value = tagSearchDraft.value
}

async function createTag() {
  const name = normalizeTagName(newTagName.value)
  if (!name || tagSaving.value) return
  tagSaving.value = true
  tagManagerError.value = ''
  try {
    await api.post('/qa-tags', { name })
    newTagName.value = ''
    await refreshTagsAfterManagerChange()
  } catch (err) {
    tagManagerError.value = apiErrorMessage(err, '新增标签失败')
  } finally {
    tagSaving.value = false
  }
}

function startTagEdit(tag: QaTag) {
  editingTagId.value = tag.id
  editingTagName.value = tag.name
  tagManagerError.value = ''
}

function cancelTagEdit() {
  editingTagId.value = ''
  editingTagName.value = ''
}

function requestRemoveTag(tag: QaTag) {
  // 删除标签会同步影响已有 QA 对，所以先记录目标并交给统一确认弹窗处理。
  tagDeleteTarget.value = tag
  tagManagerError.value = ''
}

function cancelRemoveTag() {
  if (tagSaving.value) return
  tagDeleteTarget.value = null
}

function isManagedTagSelected(tagId: string) {
  return selectedManagedTagIds.value.has(tagId)
}

function setManagedTagSelection(ids: string[]) {
  selectedManagedTagIds.value = new Set(ids)
}

function toggleManagedTagSelection(tagId: string) {
  const next = new Set(selectedManagedTagIds.value)
  if (next.has(tagId)) next.delete(tagId)
  else next.add(tagId)
  selectedManagedTagIds.value = next
}

function toggleAllFilteredTags() {
  const visibleIds = filteredTagLibrary.value.map((tag) => tag.id)
  if (!visibleIds.length) return
  const next = new Set(selectedManagedTagIds.value)
  if (allFilteredTagsSelected.value) {
    for (const id of visibleIds) next.delete(id)
  } else {
    for (const id of visibleIds) next.add(id)
  }
  selectedManagedTagIds.value = next
}

function clearManagedTagSelection() {
  setManagedTagSelection([])
}

function reconcileManagedTagSelection() {
  const availableIds = new Set(tagLibrary.value.map((tag) => tag.id))
  setManagedTagSelection([...selectedManagedTagIds.value].filter((id) => availableIds.has(id)))
}

function requestBatchRemoveTags() {
  if (!selectedManagedTagCount.value || tagSaving.value) return
  tagBatchDeleteConfirm.value = true
  tagManagerError.value = ''
}

function cancelBatchRemoveTags() {
  if (tagSaving.value) return
  tagBatchDeleteConfirm.value = false
}

async function saveTagName(tag: QaTag) {
  const name = normalizeTagName(editingTagName.value)
  if (!name || tagSaving.value) return
  tagSaving.value = true
  tagManagerError.value = ''
  try {
    await api.put(`/qa-tags/${tag.id}`, { name })
    replaceSelectedTagName(tag.name, name)
    cancelTagEdit()
    await refreshTagsAfterManagerChange()
  } catch (err) {
    tagManagerError.value = apiErrorMessage(err, '保存标签失败')
  } finally {
    tagSaving.value = false
  }
}

async function confirmRemoveTag() {
  const tag = tagDeleteTarget.value
  if (!tag || tagSaving.value) return
  tagSaving.value = true
  tagManagerError.value = ''
  try {
    await api.delete(`/qa-tags/${tag.id}`)
    removeSelectedTagName(tag.name)
    tagDeleteTarget.value = null
    await refreshTagsAfterManagerChange()
  } catch (err) {
    tagManagerError.value = apiErrorMessage(err, '删除标签失败')
  } finally {
    tagSaving.value = false
  }
}

async function confirmBatchRemoveTags() {
  const tags = selectedManagedTags.value
  if (!tags.length || tagSaving.value) return
  tagSaving.value = true
  tagManagerError.value = ''
  try {
    await api.post('/qa-tags/batch/delete', { tag_ids: tags.map((tag) => tag.id) })
    removeSelectedTagNames(tags.map((tag) => tag.name))
    tagBatchDeleteConfirm.value = false
    clearManagedTagSelection()
    await refreshTagsAfterManagerChange()
  } catch (err) {
    tagManagerError.value = apiErrorMessage(err, '批量删除标签失败')
  } finally {
    tagSaving.value = false
  }
}

function replaceSelectedTagName(oldName: string, newName: string) {
  // 标签重命名成功后，同步修正当前新增/编辑表单中的已选标签，避免界面继续显示旧名称。
  const replace = (tags: string[]) => normalizeSelectedTags(tags.map((tag) => (tag === oldName ? newName : tag)))
  selectedTags.value = replace(selectedTags.value)
  if (editDialog.value) editDialog.value.selectedTags = replace(editDialog.value.selectedTags)
}

function removeSelectedTagName(name: string) {
  // 标签删除成功后，当前未提交表单中的同名已选标签也要立即移除，保持界面状态和标签库一致。
  removeSelectedTagNames([name])
}

function removeSelectedTagNames(names: string[]) {
  // 批量删除和单个删除共用前端清理逻辑，避免表单里继续残留已不存在的标签。
  const removeNames = new Set(names)
  const remove = (tags: string[]) => tags.filter((tag) => !removeNames.has(tag))
  selectedTags.value = remove(selectedTags.value)
  if (editDialog.value) editDialog.value.selectedTags = remove(editDialog.value.selectedTags)
}

async function refreshTagsAfterManagerChange() {
  await Promise.all([loadTagLibrary(), load()])
}
</script>
