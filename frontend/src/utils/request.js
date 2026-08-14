import axios from 'axios'
import { BACKEND_URL } from './constants'
import { getToken, removeToken, removeUser } from './storage'
import { useAuthStore } from '@/stores/auth'

const request = axios.create({
  baseURL: BACKEND_URL,
  timeout: 60000,  // 流式响应时间长一点
  headers: {
    'Content-Type': 'application/json'
  }
})

request.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

let isLoggingOut = false

request.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !isLoggingOut) {
      isLoggingOut = true
      const authStore = useAuthStore()
      // 先同步清除 Pinia 状态
      authStore.token = null
      authStore.user = null
      // 同步清除 localStorage
      removeToken()
      removeUser()
      // 跳转登录页
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default request