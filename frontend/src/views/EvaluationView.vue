<!-- 评估页面：维护测试问题集，并发起/查看检索评估批次。 -->

<template>
  <AppShell>
    <div class="page two-column">
      <section class="panel workspace-panel">
        <header class="panel-header">
          <div>
            <h1>评测样本</h1>
            <p>维护固定问题集，用于回归检索和回答质量。</p>
          </div>
          <button class="primary" @click="createCase">新增样本</button>
        </header>

        <div class="form-grid">
          <label>
            问题
            <textarea v-model="caseForm.question" rows="3" placeholder="请输入评测问题" />
          </label>
          <label>
            期望答案
            <textarea v-model="caseForm.expected_answer" rows="4" placeholder="可填写关键答案或判断依据" />
          </label>
          <label>
            期望文档 ID
            <input v-model="expectedDocIds" placeholder="多个 ID 用逗号分隔" />
          </label>
          <label>
            期望切片 ID
            <input v-model="expectedChunkIds" placeholder="多个 ID 用逗号分隔" />
          </label>
        </div>
        <p v-if="error" class="error">{{ error }}</p>

        <section class="inline-list">
          <article v-for="item in cases" :key="item.id" class="qa-item">
            <strong>{{ item.question }}</strong>
            <p>{{ item.expected_answer || '未填写期望答案' }}</p>
            <div class="chunk-meta">
              <span v-if="item.expected_document_ids?.length">文档 {{ item.expected_document_ids.length }}</span>
              <span v-if="item.expected_chunk_ids?.length">切片 {{ item.expected_chunk_ids.length }}</span>
            </div>
          </article>
          <p v-if="!cases.length" class="empty-state">暂无评测样本</p>
        </section>
      </section>

      <section class="panel">
        <header class="panel-header">
          <div>
            <h2>评测运行</h2>
            <p>按当前启用样本启动一次评测。</p>
          </div>
          <button class="primary" :disabled="running" @click="runEval">
            {{ running ? '运行中' : '启动评测' }}
          </button>
        </header>

        <template v-if="run">
          <article class="result-block">
            <strong>{{ run.name }} · {{ run.status }}</strong>
            <div class="metric-grid">
              <div v-for="item in metricItems" :key="item.label" class="metric-item">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </article>

          <section class="inline-list">
            <article v-for="item in run.results" :key="item.id" class="eval-result">
              <header>
                <strong>{{ caseTitle(item.case_id) }}</strong>
                <span class="status">{{ item.failure_reason || 'passed' }}</span>
              </header>
              <div class="score-row">
                <span>Top3 {{ scoreText(item.hit_top3) }}</span>
                <span>Top5 {{ scoreText(item.hit_top5) }}</span>
                <span>答案 {{ percentText(item.answer_score) }}</span>
                <span>引用 {{ percentText(item.citation_score) }}</span>
                <span>追问 {{ percentText(item.suggested_question_score) }}</span>
              </div>
              <p>{{ item.answer || '暂无答案' }}</p>
              <details>
                <summary>检索与引用明细</summary>
                <pre>{{ JSON.stringify(item.trace || {}, null, 2) }}</pre>
              </details>
            </article>
          </section>
        </template>
        <p v-else class="empty-state">暂无运行结果</p>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import AppShell from '../components/AppShell.vue'
import { api, apiErrorMessage, unwrap } from '../api/client'

const cases = ref<any[]>([])
const run = ref<any | null>(null)
const expectedDocIds = ref('')
const expectedChunkIds = ref('')
const caseForm = reactive({ question: '', expected_answer: '' })
const running = ref(false)
const error = ref('')
let runTimer: number | undefined

onMounted(loadCases)
onUnmounted(() => {
  if (runTimer) window.clearInterval(runTimer)
})

const metricItems = computed(() => {
  const metrics = run.value?.metrics || {}
  return [
    { label: '样本数', value: metrics.case_count ?? '-' },
    { label: '有来源样本', value: metrics.source_case_count ?? '-' },
    { label: 'Top3 命中', value: percentText(metrics.top3_hit_rate) },
    { label: 'Top5 命中', value: percentText(metrics.top5_hit_rate) },
    { label: '答案得分', value: percentText(metrics.answer_score_avg) },
    { label: '引用得分', value: percentText(metrics.citation_score_avg) },
    { label: '追问得分', value: percentText(metrics.suggested_question_score_avg) }
  ]
})

async function loadCases() {
  try {
    const data = unwrap<any>(await api.get('/evaluation/cases'))
    cases.value = data.items
  } catch (err) {
    error.value = apiErrorMessage(err, '加载评测样本失败')
  }
}

async function createCase() {
  if (!caseForm.question.trim()) return
  error.value = ''
  try {
    await api.post('/evaluation/cases', {
      question: caseForm.question,
      expected_answer: caseForm.expected_answer,
      expected_document_ids: splitIds(expectedDocIds.value),
      expected_chunk_ids: splitIds(expectedChunkIds.value)
    })
    caseForm.question = ''
    caseForm.expected_answer = ''
    expectedDocIds.value = ''
    expectedChunkIds.value = ''
    await loadCases()
  } catch (err) {
    error.value = apiErrorMessage(err, '新增评测样本失败')
  }
}

async function runEval() {
  if (running.value) return
  running.value = true
  error.value = ''
  try {
    const created = unwrap<any>(await api.post('/evaluation/runs', { name: `评测 ${new Date().toLocaleString()}` }))
    await loadRun(created.run_id)
    if (runTimer) window.clearInterval(runTimer)
    runTimer = window.setInterval(() => loadRun(created.run_id), 2000)
  } catch (err) {
    running.value = false
    error.value = apiErrorMessage(err, '启动评测失败')
  }
}

async function loadRun(runId: string) {
  try {
    run.value = unwrap<any>(await api.get(`/evaluation/runs/${runId}`))
    running.value = run.value?.status === 'running'
    if (!running.value && runTimer) {
      window.clearInterval(runTimer)
      runTimer = undefined
    }
  } catch (err) {
    running.value = false
    error.value = apiErrorMessage(err, '加载评测结果失败')
  }
}

function splitIds(value: string) {
  return value.split(',').map((x) => x.trim()).filter(Boolean)
}

function caseTitle(caseId: string) {
  return cases.value.find((item) => item.id === caseId)?.question || caseId
}

function percentText(value: number | null | undefined) {
  if (value === null || value === undefined) return '-'
  const numeric = Number(value)
  if (Number.isNaN(numeric)) return '-'
  return `${Math.round(numeric * 100)}%`
}

function scoreText(value: boolean | null | undefined) {
  if (value === null || value === undefined) return '-'
  return value ? '命中' : '未命中'
}
</script>
