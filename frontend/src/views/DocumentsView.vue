<template>
  <AppShell>
    <div class="page">
      <header class="page-header">
        <h1>文档管理</h1>
        <div class="page-header-actions">
          <button @click="exportDocuments">导出清单</button>
          <label class="upload">
            上传文件
            <input type="file" @change="upload" />
          </label>
        </div>
      </header>

      <p v-if="pageError" class="error">{{ pageError }}</p>
      <p v-if="actionMessage" class="document-state-note">{{ actionMessage }}</p>

      <section v-if="visibleUploads.length" class="upload-queue">
        <article v-for="item in visibleUploads" :key="item.id" class="upload-item">
          <div>
            <strong>{{ item.fileName }}</strong>
            <span>{{ item.status }}</span>
          </div>
          <div class="progress-line">
            <span :style="{ width: `${item.progress}%` }"></span>
          </div>
          <small>{{ item.progress }}%</small>
        </article>
      </section>

      <form class="document-toolbar" @submit.prevent="loadDocuments">
        <input v-model="documentFilters.keyword" placeholder="搜索文档名称" />
        <select v-model="documentFilters.status" aria-label="按状态筛选">
          <option value="">全部状态</option>
          <option v-for="option in documentStatusOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
        <input v-model="documentFilters.knowledgeBase" placeholder="所属知识库" list="knowledge-base-options" />
        <datalist id="knowledge-base-options">
          <option v-for="item in knowledgeBaseOptions" :key="item" :value="item" />
        </datalist>
        <button type="submit">筛选</button>
        <button type="button" @click="resetDocumentFilters">重置</button>
      </form>

      <section class="document-batch-toolbar">
        <label class="checkbox-line">
          <input type="checkbox" :checked="allVisibleDocumentsSelected" @change="toggleAllVisibleDocuments" />
          本页全选
        </label>
        <span>已选 {{ selectedDocumentIds.size }} 项</span>
        <input v-model="batchKnowledgeBase" placeholder="批量归类到知识库" list="knowledge-base-options" />
        <button :disabled="!hasSelectedDocuments || Boolean(batchBusy)" @click="batchUpdateKnowledgeBase">
          批量归类
        </button>
        <button :disabled="!hasSelectedDocuments || Boolean(batchBusy)" @click="batchReparseDocuments">
          批量重解析
        </button>
        <button :disabled="!hasSelectedDocuments || Boolean(batchBusy)" @click="batchRechunkDocuments">
          批量重切片
        </button>
        <button class="danger" :disabled="!hasSelectedDocuments || Boolean(batchBusy)" @click="batchDeleteDocuments">
          批量删除
        </button>
        <button type="button" :disabled="!hasSelectedDocuments || Boolean(batchBusy)" @click="clearDocumentSelection">
          清空选择
        </button>
        <small v-if="batchBusy">{{ batchBusy }}...</small>
      </section>

      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th class="select-cell">
                <input type="checkbox" :checked="allVisibleDocumentsSelected" @change="toggleAllVisibleDocuments" />
              </th>
              <th>文档</th>
              <th>大小</th>
              <th>所属知识库</th>
              <th>状态</th>
              <th>处理进度</th>
              <th>质量</th>
              <th>来源</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in documents" :key="doc.id">
              <td class="select-cell">
                <input
                  type="checkbox"
                  :checked="isDocumentSelected(doc.id)"
                  :aria-label="`选择 ${doc.title || doc.file_name}`"
                  @click.stop
                  @change="toggleDocumentSelection(doc.id)"
                />
              </td>
              <td class="document-name-cell" :title="doc.title || doc.file_name">{{ doc.title || doc.file_name }}</td>
              <td>{{ formatSize(doc.file_size) }}</td>
              <td><span class="knowledge-badge">{{ formatKnowledgeBase(doc) }}</span></td>
              <td><span class="status">{{ formatDocumentStatus(doc) }}</span></td>
              <td>
                <div class="table-progress">
                  <div class="progress-line">
                    <span :style="{ width: `${documentProgress(doc).progress}%` }"></span>
                  </div>
                  <small :title="documentProgress(doc).message">{{ documentProgress(doc).message }}</small>
                </div>
              </td>
              <td>{{ doc.parse_quality_score || '-' }}</td>
              <td class="source-actions">
                <button class="linklike" :disabled="!doc.preview_url && !doc.download_url" @click="openPreview(doc)">
                  预览
                </button>
                <button class="linklike" @click="jumpToParsedContent(doc)">解析文本</button>
                <button class="linklike" @click="jumpToChunks(doc)">切片</button>
              </td>
              <td class="actions">
                <button @click="inspectDocument(doc)">解析/切片</button>
                <button @click="remove(doc.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="previewDocument" class="document-preview-modal" role="dialog" aria-modal="true">
        <div class="document-preview-dialog">
          <header class="document-preview-head">
            <strong>{{ previewDocument.title || previewDocument.file_name }}</strong>
            <div>
              <button @click="jumpToParsedContent(previewDocument)">解析文本</button>
              <button @click="jumpToChunks(previewDocument)">切片</button>
              <a class="buttonlike" :href="previewDocument.download_url || previewDocument.preview_url" target="_blank">
                下载
              </a>
              <button class="icon-button" title="关闭" aria-label="关闭" @click="closePreview">×</button>
            </div>
          </header>
          <iframe
            v-if="previewDocument.preview_url"
            class="document-preview-frame"
            :src="previewDocument.preview_url"
            title="文档预览"
          />
          <div v-else class="document-preview-empty">
            <p>暂时无法预览该文件</p>
            <a :href="previewDocument.download_url" target="_blank">下载文件</a>
          </div>
        </div>
      </div>

      <div v-if="duplicateUpload" class="document-preview-modal" role="dialog" aria-modal="true">
        <div class="duplicate-upload-dialog">
          <header class="duplicate-upload-head">
            <div>
              <strong>{{ duplicateDialogTitle }}</strong>
              <p>{{ duplicateDialogMessage }}</p>
            </div>
            <button class="icon-button" title="关闭" aria-label="关闭" @click="cancelDuplicateUpload">×</button>
          </header>

          <div class="duplicate-upload-body">
            <article
              v-for="match in duplicateUpload.check.matches"
              :key="match.document.id"
              class="duplicate-match"
            >
              <div>
                <strong>{{ match.document.title || match.document.file_name }}</strong>
                <span>{{ duplicateReasonLabel(match) }}</span>
              </div>
              <small>
                {{ formatSize(match.document.file_size) }} · {{ formatDocumentStatus(match.document) }}
              </small>
            </article>
          </div>

          <footer class="duplicate-upload-actions">
            <button @click="cancelDuplicateUpload">取消</button>
            <button v-if="duplicateUpload.check.same_hash" @click="useExistingDuplicate">使用已有文档</button>
            <button @click="confirmDuplicateUpload('keep_both')">保留副本</button>
            <button
              v-if="duplicateUpload.check.same_name"
              class="primary"
              @click="confirmDuplicateUpload('overwrite')"
            >
              覆盖旧文档
            </button>
          </footer>
        </div>
      </div>

      <section v-if="selectedDocument" class="document-workspace">
        <div class="panel document-summary">
          <header class="panel-header">
            <div>
              <h2>{{ selectedDocument.title || selectedDocument.file_name }}</h2>
              <p>{{ formatDocumentStatus(selectedDocument) }} · {{ formatSize(selectedDocument.file_size) }}</p>
            </div>
            <button @click="inspectDocument(selectedDocument)">刷新</button>
          </header>

          <div class="document-actions">
            <p v-if="selectedDocumentNotice" class="document-state-note">{{ selectedDocumentNotice }}</p>
            <button :disabled="Boolean(actionBusy)" @click="runDocumentAction('reparse')">重解析</button>
            <button :disabled="Boolean(actionBusy) || !canRechunkDocument(selectedDocument)" @click="runDocumentAction('rechunk')">
              重切片
            </button>
            <button :disabled="Boolean(actionBusy) || !canReembedDocument(selectedDocument)" @click="runDocumentAction('reembed')">
              重向量化
            </button>
            <button
              v-if="canConvertDocument(selectedDocument)"
              :disabled="Boolean(actionBusy)"
              @click="runDocumentAction('convert-office')"
            >
              转换并入库
            </button>
            <button
              v-if="canExtractDocument(selectedDocument)"
              :disabled="Boolean(actionBusy)"
              @click="runDocumentAction('extract-archive')"
            >
              解压导入
            </button>
            <div class="qa-generate-controls">
              <label>
                QA 数量
                <input v-model.number="qaCount" type="number" min="1" max="50" />
              </label>
              <label class="checkbox-line">
                <input v-model="qaAutoEnable" type="checkbox" />
                自动启用
              </label>
              <button class="primary" :disabled="Boolean(actionBusy) || !canGenerateQa(selectedDocument)" @click="generateQaPairs">
                生成 QA
              </button>
            </div>
            <p v-if="actionBusy" class="empty-state">{{ actionBusy }} 已提交，等待后台任务更新</p>
          </div>

          <div class="job-list">
            <article v-for="job in selectedJobs" :key="job.id" class="job-item">
              <div>
                <strong>{{ formatJobType(job.job_type) }}</strong>
                <span>{{ formatJobStatus(job.status) }}</span>
              </div>
              <div class="progress-line">
                <span :style="{ width: `${job.progress || 0}%` }"></span>
              </div>
              <small>{{ job.message || job.error_message || '-' }}</small>
              <div v-if="hasJobResult(job)" class="job-result">
                <div v-if="job.result?.converted_document_id" class="job-result-row">
                  <span>{{ job.result.converted_file_name || '转换后的文档' }}</span>
                  <button @click="inspectDocumentById(job.result.converted_document_id)">查看</button>
                </div>
                <div
                  v-for="item in jobResultDocuments(job)"
                  :key="item.document_id"
                  class="job-result-row"
                >
                  <span>{{ item.archive_entry_name || item.file_name || item.title }}</span>
                  <button @click="inspectDocumentById(item.document_id)">查看</button>
                </div>
                <small v-if="job.result?.skipped?.length">
                  已跳过 {{ job.result.skipped.length }} 个文件
                </small>
              </div>
            </article>
          </div>

          <div v-if="parseResult" class="parse-meta">
            <strong>解析信息</strong>
            <pre>{{ JSON.stringify(parseResult.parse_meta || {}, null, 2) }}</pre>
          </div>
        </div>

        <div ref="parsePreviewEl" class="panel parse-preview">
          <header class="panel-header">
            <h2>解析预览</h2>
          </header>
          <pre v-if="parseResult" class="parse-content" v-html="highlightedParsePreview"></pre>
          <p v-else class="empty-state">暂无解析结果</p>
        </div>

        <div ref="chunkPanelEl" class="panel chunk-panel">
          <header class="panel-header">
            <div>
              <h2>切片预览</h2>
              <p>{{ chunkTotal }} 个切片</p>
            </div>
            <form class="chunk-search" @submit.prevent="loadChunks(selectedDocument.id)">
              <input v-model="chunkKeyword" placeholder="搜索切片内容" />
              <button>搜索</button>
            </form>
          </header>

          <article v-for="chunk in chunks" :key="chunk.id" class="chunk">
            <header class="chunk-head">
              <strong>
                #{{ chunk.chunk_no }}
                <span v-if="chunk.page_start">第 {{ chunk.page_start }} 页</span>
                <span v-if="chunk.section_path"> · {{ chunk.section_path }}</span>
              </strong>
              <button class="linklike" @click="locateChunkInParsedContent(chunk)">定位原文</button>
            </header>
            <div class="chunk-meta">
              <span>{{ chunk.chunk_type }}</span>
              <span>{{ chunk.char_count || chunk.content.length }} 字符</span>
              <span>{{ chunk.is_active ? '已启用' : '未启用' }}</span>
            </div>
            <p>{{ chunk.content }}</p>
          </article>

          <p v-if="!chunks.length" class="empty-state">暂无切片</p>
        </div>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import AppShell from '../components/AppShell.vue'
import { api, apiErrorMessage, unwrap } from '../api/client'
import { createLocalId } from '../utils/id'

type UploadItem = {
  id: string
  fileName: string
  progress: number
  status: string
  documentId?: string
  done?: boolean
}

type ProgressState = {
  progress: number
  message: string
  active: boolean
  jobs: any[]
}

type DuplicatePolicy = 'reject' | 'overwrite' | 'keep_both'

type DuplicateMatch = {
  same_name: boolean
  same_hash: boolean
  reason: string
  document: any
}

type DuplicateCheck = {
  requested_file_name: string
  file_hash?: string
  has_duplicate: boolean
  same_name: boolean
  same_hash: boolean
  recommended_action: string
  matches: DuplicateMatch[]
  message?: string
}

type PendingDuplicateUpload = {
  file: File
  fileHash: string
  check: DuplicateCheck
}

type UploadOptions = {
  duplicatePolicy?: DuplicatePolicy
  overwriteDocumentId?: string
}

const documents = ref<any[]>([])
const chunks = ref<any[]>([])
const chunkTotal = ref(0)
const chunkKeyword = ref('')
const selectedDocument = ref<any | null>(null)
const parseResult = ref<any | null>(null)
const uploads = ref<UploadItem[]>([])
const processing = ref<Record<string, ProgressState>>({})
const selectedJobs = ref<any[]>([])
const previewDocument = ref<any | null>(null)
const qaCount = ref(10)
const qaAutoEnable = ref(true)
const actionBusy = ref('')
const actionMessage = ref('')
const batchBusy = ref('')
const pageError = ref('')
const duplicateUpload = ref<PendingDuplicateUpload | null>(null)
const selectedDocumentIds = ref<Set<string>>(new Set())
const batchKnowledgeBase = ref('')
const parsePreviewEl = ref<HTMLElement | null>(null)
const chunkPanelEl = ref<HTMLElement | null>(null)
const highlightedChunkText = ref('')
const documentFilters = ref({
  keyword: '',
  status: '',
  knowledgeBase: ''
})
let pollTimer: number | undefined

const documentStatusOptions = [
  { value: 'uploaded', label: '已上传' },
  { value: 'parsed', label: '已解析' },
  { value: 'chunked', label: '已切片' },
  { value: 'indexed', label: '处理完成' },
  { value: 'failed', label: '处理失败' },
  { value: 'needs_conversion', label: '待转换' },
  { value: 'needs_extraction', label: '待解压' },
  { value: 'no_indexable_content', label: '无可入库正文' }
]

const selectedDocumentNotice = computed(() => {
  if (!selectedDocument.value) return ''
  return documentBlocker(selectedDocument.value) || actionMessage.value
})

const visibleUploads = computed(() => uploads.value.filter((item) => !item.done))
const hasSelectedDocuments = computed(() => selectedDocumentIds.value.size > 0)
const allVisibleDocumentsSelected = computed(() => (
  documents.value.length > 0 && documents.value.every((doc) => selectedDocumentIds.value.has(doc.id))
))
const selectedDocumentIdList = computed(() => [...selectedDocumentIds.value])
const knowledgeBaseOptions = computed(() => {
  const values = new Set(['default'])
  for (const doc of documents.value) values.add(formatKnowledgeBase(doc))
  return [...values].sort()
})
const highlightedParsePreview = computed(() => {
  const content = previewContent(parseResult.value?.content || '')
  const needle = highlightedChunkText.value.trim()
  if (!needle) return escapeHtml(content)
  const sample = needle.length > 220 ? needle.slice(0, 220) : needle
  const index = content.indexOf(sample)
  if (index < 0) return escapeHtml(content)
  return [
    escapeHtml(content.slice(0, index)),
    '<mark class="parse-highlight">',
    escapeHtml(content.slice(index, index + sample.length)),
    '</mark>',
    escapeHtml(content.slice(index + sample.length))
  ].join('')
})
const duplicateDialogTitle = computed(() => {
  const check = duplicateUpload.value?.check
  if (!check) return ''
  if (check.same_hash) return '检测到相同内容的文档'
  if (check.same_name) return '检测到同名文档'
  return '检测到疑似重复文档'
})
const duplicateDialogMessage = computed(() => {
  const check = duplicateUpload.value?.check
  if (!check) return ''
  if (check.same_name && check.same_hash) {
    return '知识库中已有同名且内容一致的文档，建议直接使用已有文档。'
  }
  if (check.same_name) {
    return '知识库中已有同名文档，可以覆盖旧文档，也可以自动改名后保留副本。'
  }
  return '知识库中已有内容一致的文档，建议直接使用已有文档。'
})

onMounted(async () => {
  await load()
  pollTimer = window.setInterval(pollProcessing, 2000)
})

onUnmounted(() => {
  if (pollTimer) window.clearInterval(pollTimer)
})

async function load() {
  await loadDocuments()
  await pollProcessing(false)
}

async function loadDocuments() {
  try {
    const data = unwrap<any>(await api.get('/documents', { params: documentListParams() }))
    documents.value = data.items
    pruneDocumentSelection()
    if (selectedDocument.value) {
      const updated = documents.value.find((item) => item.id === selectedDocument.value?.id)
      if (updated) selectedDocument.value = updated
    }
    syncUploadStatuses()
  } catch (error) {
    pageError.value = apiErrorMessage(error, '加载文档失败')
  }
}

function documentListParams() {
  return {
    keyword: documentFilters.value.keyword.trim() || undefined,
    status: documentFilters.value.status || undefined,
    knowledge_base: documentFilters.value.knowledgeBase.trim() || undefined,
    page_size: 100
  }
}

async function resetDocumentFilters() {
  documentFilters.value = { keyword: '', status: '', knowledgeBase: '' }
  await loadDocuments()
}

async function upload(event: Event) {
  pageError.value = ''
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  const item: UploadItem = {
    id: createLocalId(),
    fileName: file.name,
    progress: 0,
    status: '检查重复文件'
  }
  uploads.value.unshift(item)
  input.value = ''
  try {
    const fileHash = await sha256File(file)
    const duplicateCheck = unwrap<DuplicateCheck>(
      await api.get('/documents/upload/check', {
        params: {
          file_name: file.name,
          file_hash: fileHash,
          file_size: file.size
        }
      })
    )
    if (duplicateCheck.has_duplicate) {
      item.done = true
      duplicateUpload.value = { file, fileHash, check: duplicateCheck }
      syncUploadStatuses()
      return
    }
    await startUpload(file, {}, item)
  } catch (error) {
    item.status = apiErrorMessage(error, '上传失败')
    pageError.value = item.status
  }
}

async function startUpload(file: File, options: UploadOptions = {}, existingItem?: UploadItem) {
  const item: UploadItem =
    existingItem ||
    {
      id: createLocalId(),
      fileName: file.name,
      progress: 0,
      status: '上传中'
    }
  if (!existingItem) uploads.value.unshift(item)
  item.status = '上传中'
  item.progress = 0
  item.done = false
  const form = new FormData()
  form.append('file', file)
  form.append('auto_process', 'true')
  form.append('duplicate_policy', options.duplicatePolicy || 'reject')
  if (options.overwriteDocumentId) form.append('overwrite_document_id', options.overwriteDocumentId)
  try {
    const response = await api.post('/documents/upload', form, {
      timeout: 0,
      onUploadProgress(progressEvent) {
        if (progressEvent.total) {
          item.progress = Math.min(100, Math.round((progressEvent.loaded / progressEvent.total) * 100))
        }
      }
    })
    const data = unwrap<any>(response)
    item.progress = 100
    item.status = uploadStatusLabel(data.document)
    item.fileName = data.document.file_name || item.fileName
    item.documentId = data.document.id
    await load()
    await refreshJobs(data.document.id)
    syncUploadStatuses()
  } catch (error) {
    const duplicateCheck = duplicateCheckFromError(error)
    if (duplicateCheck) {
      item.done = true
      duplicateUpload.value = { file, fileHash: duplicateCheck.file_hash || '', check: duplicateCheck }
      syncUploadStatuses()
      return
    }
    item.status = apiErrorMessage(error, '上传失败')
    pageError.value = item.status
  }
}

function cancelDuplicateUpload() {
  duplicateUpload.value = null
}

async function confirmDuplicateUpload(policy: Exclude<DuplicatePolicy, 'reject'>) {
  const pending = duplicateUpload.value
  if (!pending) return
  const target = primaryDuplicateDocument(pending.check)
  duplicateUpload.value = null
  await startUpload(pending.file, {
    duplicatePolicy: policy,
    overwriteDocumentId: policy === 'overwrite' ? target?.id : undefined
  })
}

async function useExistingDuplicate() {
  const pending = duplicateUpload.value
  if (!pending) return
  const target = primaryDuplicateDocument(pending.check)
  duplicateUpload.value = null
  if (!target) return
  await loadDocuments()
  const current = documents.value.find((item) => item.id === target.id) || target
  await inspectDocument(current)
}

async function sha256File(file: File) {
  if (!window.crypto?.subtle) return ''
  const buffer = await file.arrayBuffer()
  const digest = await window.crypto.subtle.digest('SHA-256', buffer)
  return Array.from(new Uint8Array(digest))
    .map((item) => item.toString(16).padStart(2, '0'))
    .join('')
}

function duplicateCheckFromError(error: unknown): DuplicateCheck | null {
  if (!error || typeof error !== 'object') return null
  const response = (error as { response?: { data?: { detail?: unknown } } }).response
  const detail = response?.data?.detail
  if (!detail || typeof detail !== 'object') return null
  const check = detail as Partial<DuplicateCheck>
  return check.has_duplicate && Array.isArray(check.matches) ? (check as DuplicateCheck) : null
}

function primaryDuplicateDocument(check: DuplicateCheck) {
  return (
    check.matches.find((match) => match.same_name && match.same_hash)?.document ||
    check.matches.find((match) => match.same_name)?.document ||
    check.matches.find((match) => match.same_hash)?.document ||
    check.matches[0]?.document
  )
}

function duplicateReasonLabel(match: DuplicateMatch) {
  if (match.same_name && match.same_hash) return '同名且内容一致'
  if (match.same_name) return '同名文档'
  if (match.same_hash) return '内容一致'
  return '疑似重复'
}

async function remove(id: string) {
  pageError.value = ''
  try {
    await api.delete(`/documents/${id}`)
    if (selectedDocument.value?.id === id) {
      selectedDocument.value = null
      chunks.value = []
      parseResult.value = null
      selectedJobs.value = []
    }
    await load()
  } catch (error) {
    pageError.value = apiErrorMessage(error, '删除文档失败')
  }
}

function isDocumentSelected(id: string) {
  return selectedDocumentIds.value.has(id)
}

function toggleDocumentSelection(id: string) {
  const next = new Set(selectedDocumentIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  selectedDocumentIds.value = next
}

function toggleAllVisibleDocuments() {
  if (allVisibleDocumentsSelected.value) {
    selectedDocumentIds.value = new Set()
    return
  }
  selectedDocumentIds.value = new Set(documents.value.map((doc) => doc.id))
}

function clearDocumentSelection() {
  selectedDocumentIds.value = new Set()
}

function pruneDocumentSelection() {
  const visibleIds = new Set(documents.value.map((doc) => doc.id))
  const next = new Set([...selectedDocumentIds.value].filter((id) => visibleIds.has(id)))
  if (next.size !== selectedDocumentIds.value.size) selectedDocumentIds.value = next
}

async function batchDeleteDocuments() {
  if (!hasSelectedDocuments.value || batchBusy.value) return
  const confirmed = window.confirm(`确认删除选中的 ${selectedDocumentIds.value.size} 个文档？`)
  if (!confirmed) return
  await runBatchAction('批量删除', async () => {
    await api.post('/documents/batch/delete', { document_ids: selectedDocumentIdList.value })
    if (selectedDocument.value && selectedDocumentIds.value.has(selectedDocument.value.id)) {
      selectedDocument.value = null
      chunks.value = []
      parseResult.value = null
      selectedJobs.value = []
    }
    clearDocumentSelection()
  })
}

async function batchUpdateKnowledgeBase() {
  const target = batchKnowledgeBase.value.trim()
  if (!hasSelectedDocuments.value || batchBusy.value || !target) {
    if (!target) pageError.value = '请输入要归类到的知识库名称'
    return
  }
  await runBatchAction('批量归类', async () => {
    await api.post('/documents/batch/knowledge-base', {
      document_ids: selectedDocumentIdList.value,
      knowledge_base: target
    })
  })
}

async function batchReparseDocuments() {
  if (!hasSelectedDocuments.value || batchBusy.value) return
  await runBatchAction('批量重解析', async () => {
    await api.post('/documents/batch/reparse', { document_ids: selectedDocumentIdList.value })
  })
}

async function batchRechunkDocuments() {
  if (!hasSelectedDocuments.value || batchBusy.value) return
  await runBatchAction('批量重切片', async () => {
    const data = unwrap<any>(await api.post('/documents/batch/rechunk', { document_ids: selectedDocumentIdList.value }))
    if (data.skipped?.length) {
      actionMessage.value = `已提交 ${data.count || 0} 个重切片任务，${data.skipped.length} 个文档因状态限制跳过`
    }
  })
}

async function runBatchAction(label: string, action: () => Promise<void>) {
  pageError.value = ''
  actionMessage.value = ''
  batchBusy.value = label
  try {
    await action()
    if (!actionMessage.value) actionMessage.value = `${label}已提交`
    await load()
  } catch (error) {
    pageError.value = apiErrorMessage(error, `${label}失败`)
  } finally {
    batchBusy.value = ''
  }
}

async function exportDocuments() {
  pageError.value = ''
  try {
    const response = await api.get('/documents/export', {
      params: documentListParams(),
      responseType: 'blob',
      timeout: 0
    })
    const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = exportFileName(response.headers['content-disposition'])
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch (error) {
    pageError.value = apiErrorMessage(error, '导出文档清单失败')
  }
}

function exportFileName(disposition?: string) {
  const match = String(disposition || '').match(/filename="?([^";]+)"?/i)
  return match?.[1] || `documents-${new Date().toISOString().slice(0, 10)}.csv`
}

function openPreview(doc: any) {
  previewDocument.value = doc
}

function closePreview() {
  previewDocument.value = null
}

async function jumpToParsedContent(doc: any) {
  closePreview()
  await inspectDocument(doc)
  highlightedChunkText.value = ''
  await nextTick()
  parsePreviewEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function jumpToChunks(doc: any) {
  closePreview()
  await inspectDocument(doc)
  await nextTick()
  chunkPanelEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function locateChunkInParsedContent(chunk: any) {
  highlightedChunkText.value = String(chunk?.content || '')
  await nextTick()
  parsePreviewEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function inspectDocument(doc: any) {
  pageError.value = ''
  try {
    selectedDocument.value = doc
    await Promise.all([loadParseResult(doc.id), loadChunks(doc.id), refreshJobs(doc.id)])
  } catch (error) {
    pageError.value = apiErrorMessage(error, '加载文档详情失败')
  }
}

async function runDocumentAction(
  action: 'reparse' | 'rechunk' | 'reembed' | 'convert-office' | 'extract-archive'
) {
  if (!selectedDocument.value || actionBusy.value) return
  actionBusy.value = actionLabel(action)
  actionMessage.value = ''
  try {
    const response = await api.post(`/documents/${selectedDocument.value.id}/${action}`)
    const data = unwrap<any>(response)
    if (data?.status === 'skipped') actionMessage.value = data.message || '已跳过'
    await refreshJobs(selectedDocument.value.id)
    await loadDocuments()
  } catch (error) {
    pageError.value = apiErrorMessage(error, `${actionLabel(action)}失败`)
  } finally {
    actionBusy.value = ''
  }
}

async function inspectDocumentById(id: string) {
  await loadDocuments()
  let document = documents.value.find((item) => item.id === id)
  if (!document) {
    document = unwrap<any>(await api.get(`/documents/${id}`))
  }
  if (document) {
    await inspectDocument(document)
  }
}

async function generateQaPairs() {
  if (!selectedDocument.value || actionBusy.value) return
  actionBusy.value = '生成 QA'
  actionMessage.value = ''
  try {
    const response = await api.post(`/documents/${selectedDocument.value.id}/qa-pairs/generate`, null, {
      params: {
        count: Math.max(1, Number(qaCount.value || 1)),
        auto_enable: qaAutoEnable.value
      }
    })
    const data = unwrap<any>(response)
    if (data?.status === 'skipped') actionMessage.value = data.message || '已跳过'
    await refreshJobs(selectedDocument.value.id)
  } catch (error) {
    pageError.value = apiErrorMessage(error, '生成 QA 失败')
  } finally {
    actionBusy.value = ''
  }
}

async function loadParseResult(id: string) {
  try {
    parseResult.value = unwrap<any>(await api.get(`/documents/${id}/parse-result`))
  } catch {
    parseResult.value = null
  }
}

async function loadChunks(id: string) {
  const params: Record<string, any> = { page_size: 50 }
  if (chunkKeyword.value.trim()) params.keyword = chunkKeyword.value.trim()
  const data = unwrap<any>(await api.get(`/documents/${id}/chunks`, { params }))
  chunks.value = data.items
  chunkTotal.value = data.total
}

async function pollProcessing(refreshDocuments = true) {
  const targets = documents.value.filter((doc) => shouldPoll(doc))
  await Promise.all(targets.map((doc) => refreshJobs(doc.id)))
  if (selectedDocument.value) {
    await refreshJobs(selectedDocument.value.id)
  }
  if (refreshDocuments && (targets.length || selectedDocument.value)) {
    const previousStatus = selectedDocument.value?.status
    await loadDocuments()
    if (selectedDocument.value && selectedDocument.value.status !== previousStatus) {
      await refreshSelectedDocumentContent()
    }
  }
}

async function refreshSelectedDocumentContent() {
  if (!selectedDocument.value) return
  await Promise.all([loadParseResult(selectedDocument.value.id), loadChunks(selectedDocument.value.id)])
}

async function refreshJobs(documentId: string) {
  try {
    const jobs = unwrap<any[]>(await api.get(`/documents/${documentId}/jobs`))
    processing.value[documentId] = aggregateJobs(jobs)
    if (selectedDocument.value?.id === documentId) {
      selectedJobs.value = jobs
    }
  } catch {
    processing.value[documentId] = { progress: 0, message: '暂无任务', active: false, jobs: [] }
  }
}

function shouldPoll(doc: any) {
  const state = processing.value[doc.id]
  if (state?.active) return true
  return ['uploaded', 'parsed', 'chunked'].includes(doc.status)
}

function aggregateJobs(jobs: any[]): ProgressState {
  if (!jobs.length) return { progress: 0, message: '暂无任务', active: false, jobs }
  const ranges: Record<string, [number, number]> = {
    parse: [0, 30],
    chunk: [30, 60],
    embed: [60, 100]
  }
  let progress = 0
  for (const job of jobs) {
    const [start, end] = ranges[job.job_type] || [0, 100]
    const jobProgress = ['succeeded', 'skipped'].includes(job.status) ? 100 : Number(job.progress || 0)
    progress = Math.max(progress, Math.round(start + ((end - start) * jobProgress) / 100))
  }
  const activeJob = jobs.find((job) => ['pending', 'running'].includes(job.status))
  const latest = activeJob || jobs[0]
  const failedJob = latest?.status === 'failed' ? latest : null
  return {
    progress: failedJob ? progress : Math.min(progress, 100),
    message: latest?.message || latest?.error_message || latest?.status || '-',
    active: Boolean(activeJob),
    jobs
  }
}

function documentProgress(doc: any): ProgressState {
  if (processing.value[doc.id]) return processing.value[doc.id]
  if (doc.status === 'indexed') return { progress: 100, message: '已完成', active: false, jobs: [] }
  if (doc.status === 'needs_conversion') return { progress: 100, message: doc.error_message || '待转换', active: false, jobs: [] }
  if (doc.status === 'needs_extraction') return { progress: 100, message: doc.error_message || '待解压', active: false, jobs: [] }
  if (doc.status === 'no_indexable_content') return { progress: 100, message: doc.error_message || '无可入库正文', active: false, jobs: [] }
  if (doc.status === 'converted') return { progress: 100, message: '已转换，请查看转换后的文档', active: false, jobs: [] }
  if (doc.status === 'extracted') return { progress: 100, message: '已解压，请查看导入的文档', active: false, jobs: [] }
  if (doc.status === 'failed') return { progress: 100, message: doc.error_message || '处理失败', active: false, jobs: [] }
  return { progress: 0, message: '等待处理', active: false, jobs: [] }
}

function formatJobType(type: string) {
  const labels: Record<string, string> = {
    parse: '解析',
    chunk: '切片',
    embed: '向量化',
    convert_office: '旧版 Office 转换',
    extract_import: '压缩包解压',
    qa_generate: '问答生成'
  }
  return labels[type] || type
}

function formatJobStatus(status: string) {
  const labels: Record<string, string> = {
    pending: '等待中',
    running: '处理中',
    succeeded: '已完成',
    failed: '失败',
    skipped: '已跳过',
    canceled: '已取消'
  }
  return labels[status] || status
}

function formatDocumentStatus(doc: any) {
  const labels: Record<string, string> = {
    uploaded: '已上传',
    parsed: '已解析',
    chunked: '已切片',
    indexed: '处理完成',
    failed: '处理失败',
    needs_conversion: '待转换',
    needs_extraction: '待解压',
    no_indexable_content: '无可入库正文',
    converted: '已转换',
    extracted: '已解压',
    deleted: '已删除'
  }
  return labels[String(doc?.status || '')] || doc?.status || '-'
}

function formatKnowledgeBase(doc: any) {
  return String(doc?.knowledge_base || 'default')
}

function documentBlocker(doc: any) {
  const status = String(doc?.status || '')
  const meta = parseResult.value?.parse_meta || {}
  if (status === 'needs_conversion' || meta.needs_conversion) {
    return '当前文件需要先转换为新版 Office 格式，转换后的文档会自动入库。'
  }
  if (status === 'needs_extraction' || meta.needs_extraction) {
    return '当前压缩包需要先解压导入，内部文档会自动入库。'
  }
  if (status === 'converted') return '原始文件已转换，请在转换后的文档上继续处理。'
  if (status === 'extracted') return '压缩包已解压，请在导入的文档上继续处理。'
  if (status === 'no_indexable_content' || meta.skip_chunking) return '当前解析结果没有可入库正文。'
  return ''
}

function canRechunkDocument(doc: any) {
  return Boolean(doc && parseResult.value && !documentBlocker(doc))
}

function canReembedDocument(doc: any) {
  return Boolean(doc && chunkTotal.value > 0 && !documentBlocker(doc))
}

function canGenerateQa(doc: any) {
  return Boolean(doc && parseResult.value?.content?.trim() && !documentBlocker(doc))
}

function actionLabel(action: string) {
  const labels: Record<string, string> = {
    reparse: '重解析',
    rechunk: '重切片',
    reembed: '重向量化',
    'convert-office': '转换并入库',
    'extract-archive': '解压导入'
  }
  return labels[action] || action
}

function canConvertDocument(doc: any) {
  const ext = String(doc?.file_ext || '').toLowerCase()
  return ['.doc', '.xls'].includes(ext) && ['needs_conversion', 'failed'].includes(String(doc?.status || ''))
}

function canExtractDocument(doc: any) {
  const ext = String(doc?.file_ext || '').toLowerCase()
  return ['.zip', '.rar'].includes(ext) && ['needs_extraction', 'failed'].includes(String(doc?.status || ''))
}

function uploadStatusLabel(doc: any) {
  const status = String(doc?.status || '')
  if (status === 'indexed') return '处理完成'
  if (status === 'failed') return '处理失败'
  if (status === 'needs_conversion') return '待转换'
  if (status === 'needs_extraction') return '待解压'
  if (status === 'no_indexable_content') return '无可入库正文'
  if (status === 'converted') return '已转换'
  if (status === 'extracted') return '已解压'
  return '处理中'
}

function isFinalUploadStatus(doc: any) {
  return [
    'indexed',
    'failed',
    'needs_conversion',
    'needs_extraction',
    'no_indexable_content',
    'converted',
    'extracted'
  ].includes(String(doc?.status || ''))
}

function syncUploadStatuses() {
  for (const item of uploads.value) {
    if (!item.documentId) continue
    const document = documents.value.find((doc) => doc.id === item.documentId)
    if (!document) continue
    const progress = documentProgress(document)
    item.progress = progress.progress
    item.status = uploadStatusLabel(document)
    item.done = isFinalUploadStatus(document)
  }
  uploads.value = uploads.value.filter((item) => !item.done || item.status === '处理失败')
}

function hasJobResult(job: any) {
  return Boolean(job?.result?.converted_document_id || job?.result?.imported_documents?.length || job?.result?.skipped?.length)
}

function jobResultDocuments(job: any) {
  return Array.isArray(job?.result?.imported_documents) ? job.result.imported_documents : []
}

function previewContent(content: string) {
  if (!content) return ''
  if (content.length <= 8000) return content
  return `${content.slice(0, 8000)}\n\n...`
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function formatSize(size: number) {
  if (!size) return '-'
  return `${(size / 1024 / 1024).toFixed(2)} MB`
}
</script>
