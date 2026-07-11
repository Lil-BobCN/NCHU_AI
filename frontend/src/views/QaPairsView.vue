<!-- QA 对页面：维护人工/自动生成的标准问答和启停状态。 -->

<template>
  <AppShell>
    <div class="page two-column">
      <section class="panel workspace-panel">
        <header class="panel-header">
          <div>
            <h1>QA 问答对</h1>
            <p>维护高频标准问答，作为检索召回的补充来源。</p>
          </div>
          <button class="primary" @click="save">{{ form.id ? '保存修改' : '新增问答' }}</button>
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
          <label>
            标签
            <input v-model="tagText" placeholder="多个标签用逗号分隔" />
          </label>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
      </section>

      <section class="panel">
        <header class="panel-header">
          <div>
            <h2>问答列表</h2>
            <p>{{ items.length }} 条</p>
          </div>
        </header>

        <article v-for="item in items" :key="item.id" class="qa-item">
          <button class="linklike qa-title" @click="edit(item)">{{ item.question }}</button>
          <p>{{ item.answer }}</p>
          <div class="row">
            <span class="status">{{ item.status }}</span>
            <button @click="toggle(item)">{{ item.status === 'enabled' ? '停用' : '启用' }}</button>
            <button @click="remove(item.id)">删除</button>
          </div>
        </article>

        <p v-if="!items.length" class="empty-state">暂无问答对</p>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import AppShell from '../components/AppShell.vue'
import { api, apiErrorMessage, unwrap } from '../api/client'

const items = ref<any[]>([])
const tagText = ref('')
const form = reactive({ id: '', question: '', answer: '', status: 'enabled' })
const error = ref('')

onMounted(load)

async function load() {
  try {
    const data = unwrap<any>(await api.get('/qa-pairs'))
    items.value = data.items
  } catch (err) {
    error.value = apiErrorMessage(err, '加载问答对失败')
  }
}

function edit(item: any) {
  form.id = item.id
  form.question = item.question
  form.answer = item.answer
  form.status = item.status
  tagText.value = (item.tags || []).join(',')
}

async function save() {
  error.value = ''
  const payload = {
    question: form.question,
    answer: form.answer,
    status: form.status,
    tags: tagText.value.split(',').map((x) => x.trim()).filter(Boolean)
  }
  try {
    if (form.id) await api.put(`/qa-pairs/${form.id}`, payload)
    else await api.post('/qa-pairs', payload)
    form.id = ''
    form.question = ''
    form.answer = ''
    tagText.value = ''
    await load()
  } catch (err) {
    error.value = apiErrorMessage(err, '保存问答对失败')
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

async function remove(id: string) {
  error.value = ''
  try {
    await api.delete(`/qa-pairs/${id}`)
    await load()
  } catch (err) {
    error.value = apiErrorMessage(err, '删除问答对失败')
  }
}
</script>
