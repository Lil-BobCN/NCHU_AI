import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [vue()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: env.VITE_API_PROXY_TARGET || 'http://localhost:8010',
          changeOrigin: true
        },
        '/rag-documents': {
          target: env.VITE_MINIO_PROXY_TARGET || 'http://localhost:9002',
          changeOrigin: false
        },
        '/rag-parsed': {
          target: env.VITE_MINIO_PROXY_TARGET || 'http://localhost:9002',
          changeOrigin: false
        },
        '/rag-preview': {
          target: env.VITE_MINIO_PROXY_TARGET || 'http://localhost:9002',
          changeOrigin: false
        }
      }
    }
  }
})
