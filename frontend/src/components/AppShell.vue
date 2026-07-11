<!-- 应用外壳：统一提供侧边导航、顶部栏和登录退出入口。 -->

<template>
  <div class="shell">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-mark">RAG</span>
        <span>
          <strong>学校 RAG</strong>
          <small>智能问答系统</small>
        </span>
      </div>

      <nav class="sidebar-nav">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to">
          <component :is="item.icon" :size="18" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <button class="ghost sidebar-logout" @click="logout">
        <LogOut :size="18" />
        <span>退出登录</span>
      </button>
    </aside>

    <main class="main">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import {
  Bug,
  CircleHelp,
  FileText,
  FlaskConical,
  LogOut,
  MessagesSquare
} from 'lucide-vue-next'

const router = useRouter()
const navItems = [
  { to: '/', label: '智能对话', icon: MessagesSquare },
  { to: '/documents', label: '文档管理', icon: FileText },
  { to: '/qa-pairs', label: 'QA 问答对', icon: CircleHelp },
  { to: '/debug', label: '检索调试', icon: Bug },
  { to: '/evaluation', label: '效果评测', icon: FlaskConical }
]

function logout() {
  localStorage.removeItem('access_token')
  router.push('/login')
}
</script>
