<template>
  <div class="login-page">
    <BubbleBackground />
    <div class="login-container">
      <div class="login-header">
        <div class="login-brand">
          <img src="/logo.png" alt="基智" class="login-logo-img" />
          <h1>基智</h1>
        </div>
        <p>多智能体学习助手</p >
      </div>

      <el-tabs v-model="activeTab" class="login-tabs">
        <el-tab-pane label="登录" name="login">
          <el-form @submit.prevent="handleLogin">
            <el-form-item>
              <el-input
                v-model="loginForm.loginInput"
                placeholder="账号 / 邮箱"
                size="large"
                prefix-icon="User"
              />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                size="large"
                prefix-icon="Lock"
                @keyup.enter="handleLogin"
              />
            </el-form-item>

            <el-form-item>
              <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            </el-form-item>

            <el-button
              type="primary"
              size="large"
              :loading="loginLoading"
              @click="handleLogin"
              class="submit-btn"
            >
              {{ loginLoading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form>
          <div v-if="loginError" class="error-msg">{{ loginError }}</div>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
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
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { ElMessage } from 'element-plus'
import BubbleBackground from '@/components/BubbleBackground.vue'

const router = useRouter()
const authStore = useAuthStore()
const sessionStore = useSessionStore()

const activeTab = ref('login')
const loginLoading = ref(false)
const registerLoading = ref(false)
const loginError = ref('')
const registerError = ref('')
const registerMsg = ref('')
const rememberMe = ref(false)

const loginForm = reactive({
  loginInput: '',
  password: ''
})

const registerForm = reactive({
  email: '',
  password: '',
  confirmPassword: ''
})

async function handleLogin() {
  if (!loginForm.loginInput || !loginForm.password) {
    loginError.value = '请输入账号/邮箱和密码'
    return
  }
  loginError.value = ''
  loginLoading.value = true

  const result = await authStore.login(
    loginForm.loginInput,
    loginForm.password,
    rememberMe.value
  )
  loginLoading.value = false

  if (result.success) {
    sessionStore.createSession('新对话')
    ElMessage.success('登录成功！')
    router.push('/')
  } else {
    loginError.value = result.error
  }
}

async function handleRegister() {
  const { email, password, confirmPassword } = registerForm
  if (!email || !password) {
    registerError.value = '请填写邮箱和密码'
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

  const result = await authStore.register(email, password, '')
  registerLoading.value = false

  if (result.success) {
    registerMsg.value = '验证邮件已发送，请查收邮箱并点击验证链接。'
    registerForm.email = ''
    registerForm.password = ''
    registerForm.confirmPassword = ''
  } else {
    registerError.value = result.error
  }
}
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
  padding: 40px 36px;
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

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.login-logo-img {
  width: 36px;
  height: 36px;
  object-fit: contain;
  display: block;
  margin: 0;
}

.login-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  text-shadow: 0 2px 20px rgba(0, 0, 0, 0.03);
  margin: 0;
}

.login-header p {
  color: var(--text-secondary);
  font-size: 14px;
  margin-top: 4px;
  opacity: 0.6;
}

.login-tabs :deep(.el-tabs__header) {
  margin-bottom: 24px;
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
  margin-top: 8px;
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

.error-msg {
  color: #f56c6c;
  font-size: 13px;
  margin-top: 12px;
  text-align: center;
}
.success-msg {
  color: #67c23a;
  font-size: 13px;
  margin-top: 12px;
  text-align: center;
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
</style>