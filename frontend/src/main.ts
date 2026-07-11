// 前端应用入口：创建 Vue 应用并挂载全局路由和 Pinia 状态。

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/main.css'

createApp(App).use(createPinia()).use(router).mount('#app')
