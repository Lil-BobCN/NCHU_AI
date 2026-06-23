<template>
  <div class="login-page">
    <img class="login-hero-image" :src="loginHero" alt="" />

    <div class="login-brand">
      <span class="login-brand-mark">RAG</span>
      <span>学校知识问答</span>
    </div>

    <form class="login-panel" @submit.prevent="login">
      <div class="login-panel-head">
        <p>欢迎登录</p>
        <h1>学校 RAG 智能问答系统</h1>
      </div>

      <label class="login-field">
        <UserRound :size="20" />
        <input v-model="username" autocomplete="username" placeholder="请输入您的账号" />
      </label>

      <label class="login-field">
        <LockKeyhole :size="20" />
        <input v-model="password" type="password" autocomplete="current-password" placeholder="请输入密码" />
      </label>

      <button type="submit" class="primary login-submit" :disabled="loading">
        {{ loading ? '登录中' : '登录' }}
      </button>

      <p v-if="error" class="error">{{ error }}</p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { LockKeyhole, UserRound } from 'lucide-vue-next'
import { api, unwrap } from '../api/client'
import loginHero from '../assets/login-hero.png'

const router = useRouter()
const username = ref('admin')
const password = ref('admin123')
const error = ref('')
const loading = ref(false)

async function login() {
  error.value = ''
  loading.value = true
  try {
    const data = unwrap<any>(await api.post('/auth/login', { username: username.value, password: password.value }))
    localStorage.setItem('access_token', data.access_token)
    router.push('/')
  } catch {
    error.value = '账号或密码错误'
  } finally {
    loading.value = false
  }
}
</script>
