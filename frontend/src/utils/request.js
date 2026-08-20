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
    // 登录/注册等认证接口返回的 401 是业务错误（密码错误、邮箱未验证等），
    // 不能当作登录态失效处理，否则真实原因会被清掉并强制跳回登录页
    const url = error.config?.url || ''
    const isAuthFlow = url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/wx-bind')
    if (error.response?.status === 401 && !isLoggingOut && !isAuthFlow) {
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