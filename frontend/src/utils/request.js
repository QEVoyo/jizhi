import axios from 'axios'
import { BACKEND_URL } from './constants'
import { getToken, removeToken } from './storage'
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

request.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default request