import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister, logout as apiLogout, getUserInfo, updateStatus } from '@/api/auth'
import { setToken, removeToken, getToken, setUser, removeUser, getUser } from '@/utils/storage'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(getUser() || null)
  const token = ref(getToken() || null)
  const isLoggedIn = computed(() => !!token.value && !!user.value)

  // ===== 登录 =====
  async function login(loginInput, password, rememberMe = false) {
  try {
    const res = await apiLogin(loginInput, password)
    console.log('=== authStore 收到响应 ===', res)

    // 只要返回了 id 和 access_token，就算登录成功
    if (res && res.id && res.access_token) {
      token.value = res.access_token
      user.value = {
        id: res.id,
        email: res.email,
        nickname: res.nickname,
        user_account: res.user_account,
        avatar_url: res.avatar_url,
        bio: res.bio
      }
      setToken(res.access_token)
      setUser(user.value)

      try {
        await updateStatus(res.id, 'online')
      } catch (e) {
        console.error('更新在线状态失败:', e)
      }
      return { success: true, user: user.value }
    }

    return { success: false, message: res.message || '登录失败' }
  } catch (error) {
    console.error('登录异常:', error)
    return { success: false, message: error.message || '登录失败' }
  }
}

  // ===== 注册 =====
  async function register(data) {
    try {
      const res = await apiRegister(data)
      if (res.success) {
        return { success: true }
      }
      return { success: false, message: res.message || '注册失败' }
    } catch (error) {
      return { success: false, message: error.message || '注册失败' }
    }
  }

  // ===== 退出登录 =====
  async function logout() {
    try {
      // 👇 退出时更新状态为 offline
      if (user.value?.id) {
        try {
          await updateStatus(user.value.id, 'offline')
        } catch (e) {
          console.error('更新离线状态失败:', e)
        }
      }
    } catch (e) {
      console.error('退出时更新状态失败:', e)
    }

    token.value = null
    user.value = null
    removeToken()
    removeUser()
  }

  // ===== 切换隐身状态 =====
  async function setUserStatus(status) {
    if (!user.value?.id) return
    try {
      await updateStatus(user.value.id, status)
      // 本地也更新一下
      if (user.value) {
        user.value.status = status
        setUser(user.value)
      }
      return { success: true }
    } catch (error) {
      console.error('切换状态失败:', error)
      return { success: false }
    }
  }

  // ===== 获取用户信息 =====
  async function fetchUserInfo() {
    if (!token.value) return
    try {
      const res = await getUserInfo()
      if (res) {
        user.value = res
        setUser(res)
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }

  return {
    user,
    token,
    isLoggedIn,
    login,
    register,
    logout,
    setUserStatus,
    fetchUserInfo
  }
})