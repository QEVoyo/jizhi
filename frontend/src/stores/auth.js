import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi } from '@/api/auth'
import { setToken, getToken, removeToken, setUser, getUser, removeUser } from '@/utils/storage'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(getToken())
  const user = ref(getUser())
  const isLoggedIn = computed(() => !!token.value && !!user.value)

  async function login(loginInput, password, remember = false) {
    try {
      const data = await loginApi(loginInput, password)
      token.value = data.access_token
      user.value = {
        id: data.id,
        email: data.email,
        account: data.user_account,
        nickname: data.nickname,
        avatar_url: data.avatar_url,
        bio: data.bio
      }

      if (remember) {
        setToken(token.value)
        setUser(user.value)
      } else {
        removeToken()
        removeUser()
      }

      return { success: true, data }
    } catch (error) {
      return { success: false, error: error.message || '登录失败' }
    }
  }

  async function register(email, password, nickname) {
    try {
      const data = await registerApi(email, password, nickname)
      return { success: true, data }
    } catch (error) {
      return { success: false, error: error.message || '注册失败' }
    }
  }

  function logout() {
    token.value = null
    user.value = null
    removeToken()
    removeUser()
  }

  function updateUser(newData) {
    user.value = { ...user.value, ...newData }
    if (getToken()) {
      setUser(user.value)
    }
  }

  return {
    user,
    token,
    isLoggedIn,
    login,
    register,
    logout,
    updateUser
  }
})