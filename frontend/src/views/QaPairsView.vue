<template>
  <AppShell>
    <div class="page two-column">
      <section class="panel workspace-panel">
        <header class="panel-header">
          <div>
            <h1>QA 问答对</h1>
            <p>维护高频标准问答，作为检索召回的补充来源。</p>
          </div>
          <button class="primary" @click="save">新增问答</button>
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
          <label class="qa-tag-field">
            标签
            <input v-model="tagText" placeholder="多个标签用英文逗号分隔" />
            <div class="tag-preview" aria-label="标签预览">
              <span class="tag-preview-title">标签预览</span>
              <div v-if="tagPreview.length" class="tag-list">
                <span v-for="tag in tagPreview" :key="tag.key" class="tag-chip tag-preview-chip">
                  <span class="tag-preview-label">{{ tag.value }}</span>
                  <button
                    type="button"
                    class="tag-remove-button"
                    :aria-label="`删除标签 ${tag.value}`"
                    :title="`删除标签 ${tag.value}`"
                    @click.prevent="requestTagDelete('create', tag)"
                  >
                    ×
                  </button>
                </span>
              </div>
              <span v-else class="tag-preview-empty">暂无标签</span>
            </div>
          </label>
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
            <label>
              标签筛选
              <select v-model="selectedTag" @change="applyTagFilter">
                <option value="">全部标签</option>
                <option v-for="tag in availableTags" :key="tag" :value="tag">{{ tag }}</option>
              </select>
            </label>
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

      <ConfirmDialog
        v-if="tagDeleteTarget"
        title="确认删除标签"
        :message="`将从标签输入框中删除“${tagDeleteTarget.value}”。`"
        subject-label="1 个标签"
        detail="仅删除当前输入框中的标签文本，不会立即保存问答记录。"
        prompt="请确认是否继续删除"
        cancel-text="取消"
        confirm-text="确认删除"
        @cancel="cancelTagDelete"
        @confirm="confirmTagDelete"
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
            <label class="qa-tag-field">
              标签
              <input v-model="editDialog.tagText" placeholder="多个标签用英文逗号分隔" />
              <div class="tag-preview" aria-label="标签预览">
                <span class="tag-preview-title">标签预览</span>
                <div v-if="editTagPreview.length" class="tag-list">
                  <span v-for="tag in editTagPreview" :key="tag.key" class="tag-chip tag-preview-chip">
                    <span class="tag-preview-label">{{ tag.value }}</span>
                    <button
                      type="button"
                      class="tag-remove-button"
                      :aria-label="`删除标签 ${tag.value}`"
                      :title="`删除标签 ${tag.value}`"
                      @click.prevent="requestTagDelete('edit', tag)"
                    >
                      ×
                    </button>
                  </span>
                </div>
                <span v-else class="tag-preview-empty">暂无标签</span>
              </div>
            </label>
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
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '../components/AppShell.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { api, apiErrorMessage, unwrap } from '../api/client'

type TagInputSource = 'create' | 'edit'

type TagPreviewItem = {
  key: string
  value: string
  segmentIndex: number
}

const route = useRoute()
const router = useRouter()
const items = ref<any[]>([])
const availableTags = ref<string[]>([])
const tagText = ref('')
const form = reactive({ question: '', answer: '', status: 'enabled' })
const error = ref('')
const editError = ref('')
const selectedTag = ref(routeTagFilter())
const deleteTarget = ref<any | null>(null)
const requiredDialog = ref<{ message: string; subject: string } | null>(null)
const duplicateQuestionDialog = ref(false)
const tagDeleteTarget = ref<(TagPreviewItem & { source: TagInputSource }) | null>(null)
// 左侧表单只负责新增；单条记录编辑使用独立弹窗状态，避免新增草稿和编辑内容互相污染。
const editDialog = ref<{
  id: string
  question: string
  answer: string
  status: string
  tagText: string
} | null>(null)
const tagPreview = computed(() => parseTagPreview(tagText.value))
const editTagPreview = computed(() => parseTagPreview(editDialog.value?.tagText || ''))

onMounted(load)

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
  // 智能对话里的标签 chip 会通过 /qa-pairs?tag=xxx 跳转过来；这里做一次规整，确保刷新页面和同页跳转都能直接进入对应筛选结果。
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

async function load() {
  try {
    const params = selectedTag.value ? { tag: selectedTag.value } : undefined
    const data = unwrap<any>(await api.get('/qa-pairs', { params }))
    items.value = data.items
    // 由后端按当前列表范围返回完整标签集合，避免只从当前页数据聚合导致筛选项缺失。
    availableTags.value = data.available_tags || []
  } catch (err) {
    error.value = apiErrorMessage(err, '加载问答对失败')
  }
}

function parseTagText(value: string) {
  // 标签预览和提交共用同一套英文逗号分割规则，确保“标签1”和“标签1,”都得到同样的实际标签结果。
  return value.split(',').map((x) => x.trim()).filter(Boolean)
}

function parseTagPreview(value: string): TagPreviewItem[] {
  // 预览项保留原始分段位置，删除某个 chip 时可以精准移除输入框里对应的那一段文本。
  return value
    .split(',')
    .map((segment, segmentIndex) => ({ value: segment.trim(), segmentIndex }))
    .filter((tag) => Boolean(tag.value))
    .map((tag) => ({ ...tag, key: `${tag.segmentIndex}-${tag.value}` }))
}

function removeTagSegment(value: string, segmentIndex: number) {
  // 删除后重新按英文逗号拼接有效标签，顺手清理多余空白和尾随逗号，保持输入框内容与预览结果一致。
  return value
    .split(',')
    .filter((_, index) => index !== segmentIndex)
    .map((segment) => segment.trim())
    .filter(Boolean)
    .join(',')
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
    // 当前列表已加载到完全相同问题时，直接在前端拦截，避免用户等待一次必然失败的新增请求。
    openDuplicateQuestionDialog()
    return
  }
  const payload = {
    question,
    answer,
    status: form.status,
    tags: parseTagText(tagText.value)
  }
  try {
    await api.post('/qa-pairs', payload)
    form.question = ''
    form.answer = ''
    tagText.value = ''
    await load()
  } catch (err) {
    const message = apiErrorMessage(err, '保存问答对失败')
    if (message === '当前已经存在该问答') {
      // 后端仍是最终权威判重，覆盖分页、筛选或多用户并发导致前端当前列表未命中的重复问题。
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

function requestTagDelete(source: TagInputSource, tag: TagPreviewItem) {
  tagDeleteTarget.value = { ...tag, source }
}

function cancelTagDelete() {
  tagDeleteTarget.value = null
}

function confirmTagDelete() {
  const target = tagDeleteTarget.value
  if (!target) return
  if (target.source === 'create') {
    tagText.value = removeTagSegment(tagText.value, target.segmentIndex)
  } else if (editDialog.value) {
    editDialog.value.tagText = removeTagSegment(editDialog.value.tagText, target.segmentIndex)
  }
  tagDeleteTarget.value = null
}

function openEditDialog(item: any) {
  editError.value = ''
  editDialog.value = {
    id: item.id,
    question: item.question || '',
    answer: item.answer || '',
    status: item.status || 'enabled',
    tagText: (item.tags || []).join(',')
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
      tags: parseTagText(editDialog.value.tagText)
    })
    closeEditDialog()
    await load()
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
    await load()
  } catch (err) {
    error.value = apiErrorMessage(err, '删除问答对失败')
  }
}
</script>
