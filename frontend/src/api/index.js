import axios from 'axios'
import { useUserStore } from '@/stores/user'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,  // AI 端点 60s
  withCredentials: true,
})

// 请求拦截：后端用 cookie session，axios withCredentials 自动带 cookie，无需 token header
api.interceptors.request.use((config) => config)

// 响应拦截：统一错误处理
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.detail || error.response?.data?.error || '海风停了一下'

    // 401 → 清登录态 + 跳登录
    if (status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      if (window.location.pathname !== '/login') {
        window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`
      }
    }

    // 网络错误 / 500
    if (!error.response || status >= 500) {
      console.error('[API]', message)
    }

    return Promise.reject(new Error(message))
  }
)

export default api
