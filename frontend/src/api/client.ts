// API 客户端：集中处理后端地址、JWT 注入、统一响应解包和错误提示。

import axios from 'axios'

function buildApiBaseURL(base?: string): string {
  const trimmed = base?.replace(/\/$/, '')
  if (!trimmed) return '/api/v1'
  return trimmed.endsWith('/api/v1') ? trimmed : `${trimmed}/api/v1`
}

export const apiBaseURL = buildApiBaseURL(import.meta.env.VITE_API_BASE_URL)

export const api = axios.create({
  baseURL: apiBaseURL,
  timeout: 30000
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      localStorage.removeItem('access_token')
      if (window.location.pathname !== '/login') window.location.assign('/login')
    }
    return Promise.reject(error)
  }
)

export function unwrap<T>(response: { data: { data: T } }): T {
  return response.data.data
}

export function streamApiUrl(path: string): string {
  const baseURL = import.meta.env.VITE_STREAM_API_BASE_URL
    ? buildApiBaseURL(import.meta.env.VITE_STREAM_API_BASE_URL)
    : apiBaseURL
  return `${baseURL}${path.startsWith('/') ? path : `/${path}`}`
}

export function apiErrorMessage(error: unknown, fallback = '操作失败'): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail || error.response?.data?.message
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
    if (error.message) return error.message
  }
  return error instanceof Error ? error.message : fallback
}
