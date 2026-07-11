<!-- 检索调试页面：展示多路召回、重排结果、引用和检索日志。 -->

<template>
  <AppShell>
    <div class="page">
      <header class="page-header">
        <div>
          <h1>检索调试</h1>
          <p class="page-subtitle">查看召回、重排和引用结果，定位检索链路问题。</p>
        </div>
      </header>

      <section class="panel">
        <form class="debug-form extended" @submit.prevent="search">
          <input v-model="query" placeholder="输入检索问题" />
          <input v-model="documentIdsText" placeholder="限定文档 ID，多个用逗号分隔" />
          <label>
            重排 TopK
            <input v-model.number="rerankTopK" type="number" min="1" max="30" />
          </label>
          <div class="toggle-row">
            <label class="checkbox-line">
              <input v-model="enableVectorRecall" type="checkbox" />
              向量召回
            </label>
            <label class="checkbox-line">
              <input v-model="enableKeywordRecall" type="checkbox" />
              关键词召回
            </label>
            <label class="checkbox-line">
              <input v-model="enableQaRecall" type="checkbox" />
              QA 召回
            </label>
          </div>
          <button class="primary" :disabled="loading || !query.trim()">
            {{ loading ? '检索中' : '检索' }}
          </button>
        </form>
        <p v-if="error" class="error">{{ error }}</p>
      </section>

      <section v-if="result" class="debug-grid">
        <div class="panel">
          <header class="panel-header">
            <div>
              <h2>重排结果</h2>
              <p>{{ result.rerank_results?.length || 0 }} 条</p>
            </div>
          </header>

          <article v-for="item in result.rerank_results" :key="item.chunk_id || item.qa_pair_id" class="chunk">
            <strong>
              {{ item.document_title || '未知文档' }}
              <span class="score-pill">{{ score(item) }}</span>
              <span v-if="sourceLabel(item)" class="score-pill neutral">{{ sourceLabel(item) }}</span>
            </strong>
            <div class="chunk-meta">
              <span v-if="item.chunk_id">切片 {{ shortId(item.chunk_id) }}</span>
              <span v-if="item.qa_pair_id">QA {{ shortId(item.qa_pair_id) }}</span>
              <span v-if="item.page_start">第 {{ item.page_start }} 页</span>
              <span v-if="item.section_path">{{ item.section_path }}</span>
            </div>
            <p>{{ item.content }}</p>
            <a v-if="item.url" :href="item.url" target="_blank">{{ item.url }}</a>
          </article>
        </div>

        <div class="panel">
          <header class="panel-header">
            <div>
              <h2>引用来源</h2>
              <p>{{ result.citations?.length || 0 }} 条</p>
            </div>
          </header>

          <a v-for="(item, index) in result.citations" :key="index" class="source-link" :href="item.url" target="_blank">
            <span>{{ index + 1 }}</span>
            <strong>{{ item.document_title || item.document_name }}</strong>
            <small>
              <template v-if="item.page_start">第 {{ item.page_start }} 页</template>
              <template v-if="item.section_path"> · {{ item.section_path }}</template>
            </small>
          </a>

          <div class="result-block">
            <strong>生效参数</strong>
            <pre>{{ JSON.stringify(result.effective_settings || {}, null, 2) }}</pre>
          </div>
        </div>

        <div class="panel full-span">
          <header class="panel-header">
            <div>
              <h2>召回明细</h2>
              <p>{{ result.recall_results?.length || 0 }} 条</p>
            </div>
          </header>

          <article v-for="item in result.recall_results" :key="`${item.source}-${item.chunk_id || item.qa_pair_id}`" class="chunk compact">
            <strong>
              {{ item.document_title || '未知文档' }}
              <span class="score-pill">{{ score(item) }}</span>
              <span class="score-pill neutral">{{ item.source || '-' }}</span>
            </strong>
            <p>{{ preview(item.content) }}</p>
          </article>
        </div>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppShell from '../components/AppShell.vue'
import { api, unwrap } from '../api/client'

const query = ref('')
const result = ref<any | null>(null)
const documentIdsText = ref('')
const rerankTopK = ref(5)
const enableVectorRecall = ref(true)
const enableKeywordRecall = ref(true)
const enableQaRecall = ref(true)
const loading = ref(false)
const error = ref('')

async function search() {
  error.value = ''
  loading.value = true
  const documentIds = documentIdsText.value.split(',').map((item) => item.trim()).filter(Boolean)
  try {
    result.value = unwrap<any>(await api.post('/retrieval/search', {
      query: query.value,
      rerank_top_k: Math.max(1, Number(rerankTopK.value || 1)),
      document_ids: documentIds.length ? documentIds : null,
      enable_vector_recall: enableVectorRecall.value,
      enable_keyword_recall: enableKeywordRecall.value,
      enable_qa_recall: enableQaRecall.value
    }))
  } catch (err) {
    error.value = err instanceof Error ? err.message : '检索失败'
  } finally {
    loading.value = false
  }
}

function score(item: any) {
  return Number(item.combined_score || item.rerank_score || item.score || 0).toFixed(3)
}

function sourceLabel(item: any) {
  const sources = item.sources || item.source
  if (Array.isArray(sources)) return sources.join(' / ')
  return sources || ''
}

function shortId(id: string) {
  return id ? id.slice(0, 8) : ''
}

function preview(content?: string) {
  if (!content) return ''
  return content.length > 280 ? `${content.slice(0, 280)}...` : content
}
</script>
