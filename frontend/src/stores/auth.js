import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, register as apiRegister, logout as apiLogout, getUserInfo, updateStatus, updateLearningInfo, getWechatQrcode, getWechatBindQrcode, wechatPoll, getWechatUser } from '@/api/auth'
import { setToken, removeToken, getToken, setUser, removeUser, getUser } from '@/utils/storage'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(getUser() || null)
  // 确保 role 字段始终存在（兼容旧 localStorage 数据）
  if (user.value && !user.value.role) {
    user.value.role = 'user'
  }
  const token = ref(getToken() || null)
  const isLoggedIn = computed(() => !!token.value && !!user.value)

  // ===== 登录 =====
  async function login(loginInput, password, rememberMe = false) {
    try {
      const res = await apiLogin(loginInput, password)
      console.log('=== authStore 收到响应 ===', res)

      if (res && res.id && res.access_token) {
        token.value = res.access_token
        user.value = {
          id: res.id,
          email: res.email,
          nickname: res.nickname,
          user_account: res.user_account,
          avatar_url: res.avatar_url,
          bio: res.bio,
          learning_stage: res.learning_stage || '',
          grade: res.grade || '',
          major: res.major || '',
          learning_goal: res.learning_goal || '',
          difficulty_preference: res.difficulty_preference || '',
          learning_style: res.learning_style || '',
          daily_study_time: res.daily_study_time || '',
          is_admin: res.is_admin || false,
          role: res.role || 'user'
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

  // ===== 注册（✅ 改为接收对象参数，含 code） =====
  async function register(data) {
    try {
      const res = await apiRegister(data.email, data.password, data.code, data.nickname || '')
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

  // ===== 是否需要首次引导 =====
  const needsOnboarding = computed(() => {
    return isLoggedIn.value && !user.value?.learning_stage
  })

  // ===== 更新学习偏好（本地 + 后端） =====
  async function updatePreferences(prefs) {
    if (!user.value?.id) return { success: false }
    try {
      const res = await updateLearningInfo({ user_id: user.value.id, ...prefs })
      if (res.success) {
        // 保护 role 和 is_admin 不被资料更新覆盖
        const { role, is_admin, ...safePrefs } = prefs
        Object.assign(user.value, safePrefs)
        setUser(user.value)
      }
      return res
    } catch (error) {
      console.error('更新偏好失败:', error)
      return { success: false }
    }
  }

  // ===== 微信扫码登录 =====

  // 第一步：获取二维码和轮询 token
  async function wechatLogin(redirect = '/home') {
    try {
      const data = await getWechatQrcode(redirect)
      return { success: true, qrcode: data.qrcode, pollToken: data.poll_token }
    } catch (e) {
      console.error('获取微信二维码失败:', e)
      return { success: false, message: e?.response?.data?.detail || '微信登录配置未就绪' }
    }
  }

  // 第二步：轮询等待用户扫码授权
  async function wechatPollLogin(pollToken) {
    try {
      const res = await wechatPoll(pollToken)
      if (res.ready) {
        if (res.access_token) {
          token.value = res.access_token
          user.value = res.user
          setToken(res.access_token)
          setUser(res.user)
          try { await updateStatus(res.user.id, 'online') } catch (e) {}
          return { success: true, user: res.user }
        }
        // bound: false — 微信未绑定任何账号
        if (res.bound === false) {
          return { success: false, notBound: true }
        }
      }
      return { success: false, ready: false }
    } catch (e) {
      console.error('微信轮询失败:', e)
      return { success: false, message: '登录检查失败' }
    }
  }

  // ===== 微信绑定（已登录用户）=====
  async function bindWechat() {
    try {
      const data = await getWechatBindQrcode()
      return { success: true, qrcode: data.qrcode, pollToken: data.poll_token }
    } catch (e) {
      return { success: false, message: e?.response?.data?.detail || '获取绑定二维码失败' }
    }
  }

  // 轮询绑定结果
  async function bindWechatPoll(pollToken) {
    try {
      const res = await wechatPoll(pollToken)
      if (res.ready) {
        if (res.bound) return { success: true, nickname: res.nickname }
        return { success: false, message: res.error || '绑定失败' }
      }
      return { success: false, ready: false }
    } catch (e) {
      return { success: false, message: '绑定检查失败' }
    }
  }

  return {
    user,
    token,
    isLoggedIn,
    needsOnboarding,
    login,
    register,
    logout,
    setUserStatus,
    fetchUserInfo,
    updatePreferences,
    wechatLogin,
    wechatPollLogin,
    bindWechat,
    bindWechatPoll
  }
})