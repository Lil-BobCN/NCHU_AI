// 前端路由：注册页面路径，并在进入业务页面前检查登录 token。

import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import ChatView from '../views/ChatView.vue'
import DocumentsView from '../views/DocumentsView.vue'
import QaPairsView from '../views/QaPairsView.vue'
import RetrievalDebugView from '../views/RetrievalDebugView.vue'
import EvaluationView from '../views/EvaluationView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/login', component: LoginView },
    {
      path: '/',
      component: ChatView,
      meta: { auth: true }
    },
    { path: '/documents', component: DocumentsView, meta: { auth: true } },
    { path: '/qa-pairs', component: QaPairsView, meta: { auth: true } },
    { path: '/debug', component: RetrievalDebugView, meta: { auth: true } },
    { path: '/evaluation', component: EvaluationView, meta: { auth: true } }
  ]
})

router.beforeEach((to) => {
  if (to.meta.auth && !localStorage.getItem('access_token')) {
    return '/login'
  }
})

export default router
