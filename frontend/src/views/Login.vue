<template>
  <div class="login-page">
    <BubbleBackground />
    <div class="login-container">
      <div class="login-back" @click="$router.push('/')">
        <i class="fas fa-arrow-left"></i> 返回首页
      </div>

      <div class="login-header">
        <div class="login-brand">
          <img src="/logo.png" alt="基智" class="login-logo-img" />
          <h1>基智</h1>
        </div>
        <p>多智能体学习助手</p>
      </div>

      <el-tabs v-model="activeTab" class="login-tabs">
        <!-- ===== 用户登录 ===== -->
        <el-tab-pane label="用户登录" name="user">
          <el-form @submit.prevent="handleUserLogin">
            <el-form-item>
              <el-input
                v-model="userForm.loginInput"
                placeholder="账号 / 邮箱"
                size="large"
                prefix-icon="User"
              />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="userForm.password"
                type="password"
                placeholder="密码"
                size="large"
                prefix-icon="Lock"
                @keyup.enter="handleUserLogin"
              />
            </el-form-item>
            <el-form-item>
              <el-checkbox v-model="userRememberMe">记住我</el-checkbox>
            </el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="userLoading"
              @click="handleUserLogin"
              class="submit-btn"
            >
              {{ userLoading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form>
          <div v-if="userError" class="error-msg">{{ userError }}</div>
        </el-tab-pane>

        <!-- ===== 管理员登录 ===== -->
        <el-tab-pane name="admin">
          <template #label>
            <span class="admin-tab-label">
              <i class="fas fa-shield-halved"></i> 管理员登录
            </span>
          </template>
          <el-form @submit.prevent="handleAdminLogin">
            <el-form-item>
              <el-input
                v-model="adminForm.loginInput"
                placeholder="管理员账号 / 邮箱"
                size="large"
                prefix-icon="User"
              />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="adminForm.password"
                type="password"
                placeholder="密码"
                size="large"
                prefix-icon="Lock"
                @keyup.enter="handleAdminLogin"
              />
            </el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="adminLoading"
              @click="handleAdminLogin"
              class="submit-btn admin-btn"
            >
              {{ adminLoading ? '验证中...' : '管理员登录' }}
            </el-button>
          </el-form>
          <div v-if="adminError" class="error-msg">{{ adminError }}</div>
        </el-tab-pane>

        <!-- ===== 用户注册 ===== -->
        <el-tab-pane label="用户注册" name="register">
          <el-form @submit.prevent="handleRegister">
            <el-form-item>
              <el-input
                v-model="registerForm.email"
                placeholder="邮箱"
                size="large"
                prefix-icon="Message"
              />
            </el-form-item>
            <el-form-item>
              <div class="captcha-row">
                <el-input
                  v-model="registerForm.code"
                  placeholder="验证码"
                  size="large"
                  prefix-icon="Key"
                  class="captcha-input"
                />
                <el-button
                  size="large"
                  :loading="sendingCode"
                  :disabled="codeCountdown > 0 || !registerForm.email"
                  @click="handleSendCode"
                  class="captcha-btn"
                >
                  {{ codeCountdown > 0 ? `${codeCountdown}s` : '获取验证码' }}
                </el-button>
              </div>
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="密码（至少6位）"
                size="large"
                prefix-icon="Lock"
              />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="确认密码"
                size="large"
                prefix-icon="Lock"
              />
            </el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="registerLoading"
              @click="handleRegister"
              class="submit-btn"
            >
              {{ registerLoading ? '注册中...' : '注 册' }}
            </el-button>
          </el-form>
          <div v-if="registerMsg" class="success-msg">{{ registerMsg }}</div>
          <div v-if="registerError" class="error-msg">{{ registerError }}</div>
        </el-tab-pane>
      </el-tabs>

      <!-- ===== 微信扫码登录 ===== -->
      <div class="wechat-login-section">
        <div class="divider"><span>或</span></div>

        <!-- 未发起扫码时：显示按钮 -->
        <button
          v-if="!wechatQrcode"
          class="wechat-login-btn"
          :loading="wechatLoading"
          @click="handleWechatLogin"
        >
          <i class="fab fa-weixin"></i>
          {{ wechatLoading ? '加载中...' : '微信扫码登录' }}
        </button>

        <!-- 扫码中：显示二维码 -->
        <div v-if="wechatQrcode" class="wechat-qrcode-panel">
          <img :src="wechatQrcode" alt="微信扫码登录" class="wechat-qrcode-img" />
          <p class="wechat-qrcode-tip">{{ pollStatus }}</p>
          <button class="wechat-cancel-btn" @click="cancelWechatLogin">取消</button>
        </div>

        <p v-if="!wechatQrcode" class="wechat-hint">
          需先前往 mp.weixin.qq.com/debug 获取测试号 appid/secret
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { ElMessage } from 'element-plus'
import BubbleBackground from '@/components/BubbleBackground.vue'
import { recordAction } from '@/api/career'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const sessionStore = useSessionStore()

const activeTab = ref(route.query.tab === 'register' ? 'register' : 'user')
const userLoading = ref(false)
const adminLoading = ref(false)
const registerLoading = ref(false)
const wechatLoading = ref(false)
const wechatQrcode = ref('')       // 二维码 base64
const pollStatus = ref('')         // 扫码状态提示
let pollTimer = null               // 轮询定时器
let pollToken = ''                 // 当前轮询 token
const userError = ref('')
const adminError = ref('')
const registerError = ref('')
const registerMsg = ref('')
const userRememberMe = ref(false)

// 验证码相关
const sendingCode = ref(false)
const codeCountdown = ref(0)
let countdownTimer = null

// 用户登录表单
const userForm = reactive({
  loginInput: '',
  password: ''
})

// 管理员登录表单
const adminForm = reactive({
  loginInput: '',
  password: ''
})

// 注册表单
const registerForm = reactive({
  email: '',
  password: '',
  confirmPassword: '',
  code: ''
})

// ===== 发送验证码 =====
async function handleSendCode() {
  const email = registerForm.email.trim()
  if (!email) { ElMessage.warning('请先填写邮箱'); return }
  if (!email.includes('@')) { ElMessage.warning('邮箱格式不正确'); return }

  sendingCode.value = true
  try {
    const baseUrl = import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'
    const res = await fetch(`${baseUrl}/auth/send-code?email=${encodeURIComponent(email)}`, { method: 'POST' })
    const data = await res.json()
    if (data.success) {
      ElMessage.success('验证码已发送，请查收邮箱')
      codeCountdown.value = 60
      if (countdownTimer) clearInterval(countdownTimer)
      countdownTimer = setInterval(() => {
        codeCountdown.value--
        if (codeCountdown.value <= 0) { clearInterval(countdownTimer); countdownTimer = null }
      }, 1000)
    } else {
      ElMessage.error(data.message || '发送失败')
    }
  } catch (error) {
    ElMessage.error('发送验证码失败')
  } finally {
    sendingCode.value = false
  }
}

// ===== 用户登录 =====
async function handleUserLogin() {
  if (!userForm.loginInput || !userForm.password) {
    userError.value = '请输入账号/邮箱和密码'
    return
  }
  userError.value = ''
  userLoading.value = true

  const result = await authStore.login(userForm.loginInput, userForm.password, userRememberMe.value)
  userLoading.value = false

  if (result && result.success) {
    sessionStore.createSession('新对话')
    try { await recordAction(result.user?.id || authStore.user?.id, 'login') } catch (e) {}
    ElMessage.success('登录成功！')
    router.push('/home')
  } else {
    userError.value = result?.message || '登录失败'
  }
}

// ===== 管理员登录 =====
async function handleAdminLogin() {
  if (!adminForm.loginInput || !adminForm.password) {
    adminError.value = '请输入管理员账号/邮箱和密码'
    return
  }
  adminError.value = ''
  adminLoading.value = true

  const result = await authStore.login(adminForm.loginInput, adminForm.password, false)
  adminLoading.value = false

  if (result && result.success) {
    if (!authStore.user?.is_admin) {
      // 不是管理员，清除登录态
      await authStore.logout()
      adminError.value = '该账号无管理员权限'
      return
    }
    sessionStore.createSession('新对话')
    try { await recordAction(result.user?.id || authStore.user?.id, 'login') } catch (e) {}
    ElMessage.success('管理员登录成功！')
    router.push('/admin')
  } else {
    adminError.value = result?.message || '登录失败'
  }
}

async function handleRegister() {
  const { email, password, confirmPassword, code } = registerForm
  if (!email || !password || !code) {
    registerError.value = '请填写完整信息'
    return
  }
  if (!email.includes('@')) {
    registerError.value = '邮箱格式不正确'
    return
  }
  if (password.length < 6) {
    registerError.value = '密码至少6位'
    return
  }
  if (password !== confirmPassword) {
    registerError.value = '两次密码不一致'
    return
  }
  registerError.value = ''
  registerMsg.value = ''
  registerLoading.value = true

  const result = await authStore.register({
    email: email,
    password: password,
    code: code,
    nickname: ''
  })

  registerLoading.value = false

  if (result.success) {
    registerMsg.value = '🎉 注册成功！请前往登录'
    registerForm.email = ''
    registerForm.password = ''
    registerForm.confirmPassword = ''
    registerForm.code = ''
    // 切换到登录 Tab
    setTimeout(() => {
      activeTab.value = 'user'
    }, 1500)
  } else {
    registerError.value = result.message || '注册失败'
  }
}

// ===== 微信扫码登录 =====
async function handleWechatLogin() {
  wechatLoading.value = true
  const redirect = (route.query.redirect) || '/home'

  const result = await authStore.wechatLogin(redirect)
  wechatLoading.value = false

  if (!result.success) {
    userError.value = result.message || '微信登录配置未就绪'
    return
  }

  // 显示二维码
  wechatQrcode.value = result.qrcode
  pollToken = result.pollToken
  pollStatus.value = '请用微信扫描二维码'

  // 开始轮询（每 2 秒一次，最多 5 分钟）
  let attempts = 0
  pollTimer = setInterval(async () => {
    attempts++
    if (attempts > 150) {
      // 5 分钟超时
      clearInterval(pollTimer)
      pollTimer = null
      pollStatus.value = '二维码已过期，请重新获取'
      setTimeout(() => { wechatQrcode.value = '' }, 2000)
      return
    }

    const pollResult = await authStore.wechatPollLogin(pollToken)
    if (pollResult.success) {
      clearInterval(pollTimer)
      pollTimer = null
      pollStatus.value = '登录成功！'
      sessionStore.createSession('新对话')
      try { await recordAction(pollResult.user?.id, 'login') } catch (e) {}
      ElMessage.success('微信登录成功！')
      router.replace(redirect)
    } else if (pollResult.notBound) {
      // 微信未绑定账号
      clearInterval(pollTimer)
      pollTimer = null
      wechatQrcode.value = ''
      ElMessage.warning('该微信未绑定账号，请先用账号密码登录，然后在个人中心绑定微信')
    } else if (pollResult.message) {
      clearInterval(pollTimer)
      pollTimer = null
      pollStatus.value = pollResult.message
      setTimeout(() => { wechatQrcode.value = '' }, 2000)
    }
  }, 2000)
}

function cancelWechatLogin() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  wechatQrcode.value = ''
  pollToken = ''
  pollStatus.value = ''
}

// 组件卸载时清除定时器
onUnmounted(() => {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-container {
  position: relative;
  z-index: 10;
  width: 420px;
  padding: 40px 36px 36px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.04), inset 0 0 60px rgba(255, 255, 255, 0.02);
}

[data-theme="dark"] .login-container {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(255, 255, 255, 0.06);
}

.login-back {
  position: absolute;
  top: 14px;
  left: 18px;
  font-size: 13px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  z-index: 20;
}
.login-back:hover {
  color: var(--text-primary);
  transform: translateX(-2px);
}

.login-header {
  text-align: center;
  margin-bottom: 24px;
}

.login-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.login-logo-img {
  width: 32px;
  height: 32px;
  object-fit: contain;
  display: block;
}

.login-header h1 {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.login-header p {
  color: var(--text-secondary);
  font-size: 14px;
  margin-top: 2px;
  opacity: 0.6;
}

.login-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
  border: none;
}
.login-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  color: var(--text-secondary);
}
.login-tabs :deep(.el-tabs__item.is-active) {
  color: var(--text-primary);
}
.login-tabs :deep(.el-tabs__active-bar) {
  background: var(--text-primary);
}
.login-tabs :deep(.el-tabs__item:hover) {
  color: var(--text-primary);
}

.submit-btn {
  width: 100%;
  margin-top: 4px;
  background: rgba(128, 128, 128, 0.08) !important;
  border: 1px solid rgba(128, 128, 128, 0.12) !important;
  color: var(--text-primary) !important;
  border-radius: 12px !important;
  transition: all 0.3s ease !important;
}
.submit-btn:hover {
  background: rgba(128, 128, 128, 0.14) !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}
.submit-btn:active {
  transform: translateY(0px);
}

/* 管理员按钮金色调 */
.admin-btn {
  background: rgba(245, 158, 11, 0.12) !important;
  border: 1px solid rgba(245, 158, 11, 0.2) !important;
  color: #f59e0b !important;
}
.admin-btn:hover {
  background: rgba(245, 158, 11, 0.2) !important;
  box-shadow: 0 4px 20px rgba(245, 158, 11, 0.12);
}

/* 管理员 Tab 标签样式 */
.admin-tab-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.admin-tab-label i {
  font-size: 13px;
  color: #f59e0b;
}

.error-msg {
  color: #f56c6c;
  font-size: 13px;
  margin-top: 10px;
  text-align: center;
}
.success-msg {
  color: #67c23a;
  font-size: 13px;
  margin-top: 10px;
  text-align: center;
}

/* ✅ 验证码行 */
.captcha-row {
  display: flex;
  gap: 10px;
  width: 100%;
}
.captcha-input {
  flex: 1;
}
.captcha-btn {
  flex-shrink: 0;
  width: 130px;
  background: rgba(128, 128, 128, 0.06) !important;
  border: 1px solid rgba(128, 128, 128, 0.10) !important;
  color: var(--text-primary) !important;
  border-radius: 12px !important;
}
.captcha-btn:hover:not(:disabled) {
  background: rgba(128, 128, 128, 0.12) !important;
}
.captcha-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

:deep(.el-input__wrapper) {
  background: rgba(128, 128, 128, 0.05) !important;
  border: 1px solid rgba(128, 128, 128, 0.08) !important;
  border-radius: 12px !important;
  box-shadow: inset 0 1px 4px rgba(0, 0, 0, 0.02) !important;
}
:deep(.el-input__wrapper:hover) {
  border-color: rgba(128, 128, 128, 0.15) !important;
}
:deep(.el-input__wrapper.is-focus) {
  border-color: rgba(128, 128, 128, 0.2) !important;
  box-shadow: inset 0 1px 8px rgba(0, 0, 0, 0.04) !important;
}
:deep(.el-input__inner) {
  color: var(--text-primary) !important;
}
:deep(.el-input__prefix) {
  color: var(--text-muted) !important;
}

:deep(.el-checkbox__inner) {
  background: rgba(255, 255, 255, 0.08) !important;
  border-color: rgba(128, 128, 128, 0.3) !important;
  transition: all 0.3s ease !important;
}
:deep(.el-checkbox__inner:hover) {
  border-color: rgba(128, 128, 128, 0.5) !important;
}
:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background: #409eff !important;
  border-color: #409eff !important;
}
:deep(.el-checkbox__input.is-checked .el-checkbox__inner::after) {
  border-color: #fff !important;
}
:deep(.el-checkbox__label) {
  color: var(--text-secondary) !important;
}

[data-theme="dark"] :deep(.el-checkbox__inner) {
  background: rgba(255, 255, 255, 0.04) !important;
  border-color: rgba(255, 255, 255, 0.2) !important;
}
[data-theme="dark"] :deep(.el-checkbox__inner:hover) {
  border-color: rgba(255, 255, 255, 0.35) !important;
}
[data-theme="dark"] :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background: #409eff !important;
  border-color: #409eff !important;
}

/* ===== 微信扫码登录 ===== */
.wechat-login-section {
  margin-top: 20px;
  text-align: center;
}

.divider {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 16px;
  color: var(--text-muted);
  font-size: 12px;
  opacity: 0.5;
}
.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--text-muted);
  opacity: 0.2;
}

.wechat-login-btn {
  width: 100%;
  padding: 13px 0;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: linear-gradient(135deg, #07c160, #06ad56);
  color: #fff;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}
.wechat-login-btn i {
  font-size: 20px;
}
.wechat-login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(7, 193, 96, 0.35);
}
.wechat-login-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(7, 193, 96, 0.25);
}
.wechat-login-btn::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
  transition: left 0.5s;
}
.wechat-login-btn:hover::after {
  left: 100%;
}

/* ── 二维码面板 ── */
.wechat-qrcode-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 20px;
  background: #fff;
  border-radius: 16px;
  border: 2px solid #07c160;
}
.wechat-qrcode-img {
  width: 200px;
  height: 200px;
  border-radius: 8px;
  display: block;
}
.wechat-qrcode-tip {
  font-size: 14px;
  color: #333;
  margin: 0;
  font-weight: 500;
}
.wechat-cancel-btn {
  padding: 6px 24px;
  border: 1px solid #ddd;
  border-radius: 20px;
  background: #fff;
  color: #999;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}
.wechat-cancel-btn:hover {
  border-color: #f56c6c;
  color: #f56c6c;
}

.wechat-hint {
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-muted);
  opacity: 0.5;
}
</style>