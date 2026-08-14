<template>
  <div class="profile-page">
    <!-- 自定义 Toast -->
    <Teleport to="body">
      <TransitionGroup name="toast" tag="div" class="toast-stack">
        <div v-for="t in toasts" :key="t.id" :class="['toast-item', 'toast-' + t.type]">
          <span class="toast-icon">{{ t.type === 'success' ? '✓' : t.type === 'error' ? '✕' : '!' }}</span>
          <span class="toast-msg">{{ t.msg }}</span>
        </div>
      </TransitionGroup>
    </Teleport>

    <!-- 自定义确认弹窗 -->
    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="confirm.show" class="modal-overlay" @click.self="confirm.reject">
          <div class="modal-card">
            <div class="modal-title">{{ confirm.title }}</div>
            <div class="modal-body">{{ confirm.message }}</div>
            <div class="modal-actions">
              <button class="glass-btn" @click="confirm.reject">取消</button>
              <button class="glass-btn danger" @click="confirm.resolve">确认</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 顶部返回 -->
    <div class="profile-topbar">
      <button class="glass-btn back-btn" @click="goHome">
        <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回主界面
      </button>
      <h1>个人中心</h1>
    </div>

    <div class="profile-container">
      <!-- ===== 头像 ===== -->
      <div class="profile-card avatar-section">
        <div class="avatar-wrapper">
          <div class="avatar-ring">
            <img v-if="user?.avatar_url" :src="user.avatar_url" class="avatar-img" />
            <span v-else class="avatar-placeholder">{{ user?.nickname?.[0] || 'U' }}</span>
          </div>
          <label class="glass-btn primary small upload-btn">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
              <path d="M12 11v6M9 14l3-3 3 3"/>
            </svg>
            更换头像
            <input type="file" accept="image/*" @change="handleAvatarUpload" style="display:none;" />
          </label>
        </div>
        <div class="user-basic">
          <div class="basic-row">
            <span class="label">账号</span>
            <span class="value">{{ user?.user_account || '未设置' }}</span>
          </div>
          <div class="basic-row">
            <span class="label">邮箱</span>
            <span class="value">{{ user?.email || '未设置' }}</span>
          </div>
        </div>
      </div>

      <!-- ===== 昵称 ===== -->
      <div class="profile-card">
        <div class="field-label">昵称</div>
        <div class="field-row">
          <input class="glass-input" v-model="nickname" placeholder="请输入昵称" />
          <button class="glass-btn primary" @click="handleUpdateNickname">保存</button>
        </div>
      </div>

      <!-- ===== 简介 ===== -->
      <div class="profile-card">
        <div class="field-label">个人简介</div>
        <textarea class="glass-input textarea" v-model="bio" rows="3" placeholder="介绍一下自己..."></textarea>
        <button class="glass-btn primary" style="margin-top:8px;" @click="handleUpdateBio">保存简介</button>
      </div>

      <!-- ===== 学习画像总览 ===== -->
      <div class="profile-card preferences-section">
        <div class="section-header">
          <div class="section-title-group">
            <span class="field-label">🎯 学习画像</span>
            <span class="section-hint">这些信息帮助基智为你提供更精准的学习建议</span>
          </div>
          <button class="glass-btn primary refill-btn" @click="goOnboarding">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            重新填写偏好问卷
          </button>
        </div>

        <div class="prefs-grid">
          <!-- 学习阶段 -->
          <div class="pref-tile" :class="{ empty: !user?.learning_stage }">
            <span class="pref-icon">🏫</span>
            <span class="pref-label">学习阶段</span>
            <span class="pref-value">{{ user?.learning_stage || '未设置' }}</span>
          </div>
          <!-- 年级 -->
          <div class="pref-tile" :class="{ empty: !user?.grade }">
            <span class="pref-icon">📚</span>
            <span class="pref-label">年级</span>
            <span class="pref-value">{{ user?.grade || '未设置' }}</span>
          </div>
          <!-- 专业 -->
          <div class="pref-tile" :class="{ empty: !user?.major }">
            <span class="pref-icon">🔬</span>
            <span class="pref-label">专业/方向</span>
            <span class="pref-value">{{ user?.major || '未设置' }}</span>
          </div>
          <!-- 学习目标 -->
          <div class="pref-tile" :class="{ empty: !pref('learning_goal') }">
            <span class="pref-icon">🎯</span>
            <span class="pref-label">学习目标</span>
            <span class="pref-value">{{ pref('learning_goal') || '未设置' }}</span>
          </div>
          <!-- 难度偏好 -->
          <div class="pref-tile" :class="{ empty: !pref('difficulty_preference') }">
            <span class="pref-icon">📊</span>
            <span class="pref-label">题目难度</span>
            <span class="pref-value">{{ pref('difficulty_preference') || '未设置' }}</span>
          </div>
          <!-- 讲解偏好 -->
          <div class="pref-tile" :class="{ empty: !pref('learning_style') }">
            <span class="pref-icon">💬</span>
            <span class="pref-label">讲解方式</span>
            <span class="pref-value">{{ pref('learning_style') || '未设置' }}</span>
          </div>
          <!-- 每日时长 -->
          <div class="pref-tile" :class="{ empty: !pref('daily_study_time') }">
            <span class="pref-icon">⏱</span>
            <span class="pref-label">每日学习</span>
            <span class="pref-value">{{ pref('daily_study_time') || '未设置' }}</span>
          </div>
        </div>

        <div class="refill-desc">
          💡 点击上方按钮可进入偏好问卷，一站式更新全部学习画像数据。
          问卷中的偏好项目均可跳过，数据会实时同步给基智 AI。
        </div>
      </div>

      <!-- ===== 微信绑定 ===== -->
      <div class="profile-card">
        <div class="field-label">🔗 微信绑定</div>
        <div v-if="user?.wechat_openid" class="wechat-bound">
          <i class="fab fa-weixin" style="color:#07c160;font-size:20px"></i>
          <span>已绑定微信</span>
        </div>
        <div v-else>
          <!-- 未显示二维码时 -->
          <button v-if="!bindQrcode" class="glass-btn wechat-bind-btn" :loading="bindLoading" @click="handleBindWechat">
            <i class="fab fa-weixin"></i> 绑定微信
          </button>
          <!-- 扫码中 -->
          <div v-if="bindQrcode" class="wechat-bind-panel">
            <img :src="bindQrcode" alt="微信扫码绑定" class="wechat-bind-qr" />
            <p class="wechat-bind-tip">{{ bindStatus }}</p>
            <button class="glass-btn small" @click="cancelBind">取消</button>
          </div>
        </div>
      </div>

      <!-- ===== 修改密码 ===== -->
      <div class="profile-card">
        <div class="field-label">修改密码</div>
        <input class="glass-input" v-model="oldPassword" type="password" placeholder="当前密码" style="margin-bottom:10px;" />
        <input class="glass-input" v-model="newPassword" type="password" placeholder="新密码（至少6位）" style="margin-bottom:10px;" />
        <input class="glass-input" v-model="confirmPassword" type="password" placeholder="确认新密码" />
        <button class="glass-btn warning" style="margin-top:10px;" @click="handleUpdatePassword">修改密码</button>
      </div>

      <!-- ===== 退出登录 ===== -->
      <button class="glass-btn danger logout-btn" @click="handleLogout">退出登录</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { setUser } from '@/utils/storage'
import { updateNickname as apiUpdateNickname, updateBio as apiUpdateBio, uploadAvatar } from '@/api/auth'
import { recordAction } from '@/api/career'

const router = useRouter()
const authStore = useAuthStore()

const user = computed(() => authStore.user)
const nickname = ref('')
const bio = ref('')
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

// ===== 偏好辅助 =====
function pref(key) {
  return user.value?.[key] || ''
}

// ===== 自定义 Toast =====
const toasts = ref([])
let toastId = 0
function showToast(msg, type = 'success') {
  const id = ++toastId
  toasts.value.push({ id, msg, type })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 2500)
}

// ===== 自定义确认弹窗 =====
const confirm = reactive({ show: false, title: '', message: '', resolve: null, reject: null })
function showConfirm(title, message) {
  return new Promise((resolve, reject) => {
    Object.assign(confirm, { show: true, title, message, resolve: () => { confirm.show = false; resolve() }, reject: () => { confirm.show = false; reject() } })
  })
}

// ===== 头像上传 =====
async function handleAvatarUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  try {
    const result = await uploadAvatar(authStore.user.id, file)
    if (result.success) {
      authStore.user.avatar_url = result.avatar_url
      setUser(authStore.user)
      await recordAction(authStore.user.id, 'update_avatar')
      showToast('头像上传成功')
    }
  } catch (error) {
    showToast('上传失败', 'error')
  }
  event.target.value = ''
}

// ===== 更新昵称 =====
async function handleUpdateNickname() {
  if (!nickname.value) { showToast('请输入昵称', 'error'); return }
  try {
    await apiUpdateNickname(authStore.user.id, nickname.value)
    authStore.user.nickname = nickname.value
    setUser(authStore.user)
    await recordAction(authStore.user.id, 'update_nickname')
    showToast('昵称更新成功')
  } catch (error) {
    showToast('更新失败', 'error')
  }
}

// ===== 更新简介 =====
async function handleUpdateBio() {
  try {
    await apiUpdateBio(authStore.user.id, bio.value)
    authStore.user.bio = bio.value
    setUser(authStore.user)
    await recordAction(authStore.user.id, 'update_bio')
    showToast('简介更新成功')
  } catch (error) {
    showToast('更新失败', 'error')
  }
}

// ===== 修改密码 =====
async function handleUpdatePassword() {
  if (!oldPassword.value) { showToast('请输入当前密码', 'error'); return }
  if (!newPassword.value || newPassword.value.length < 6) { showToast('新密码至少6位', 'error'); return }
  if (newPassword.value !== confirmPassword.value) { showToast('两次密码不一致', 'error'); return }
  try {
    const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/auth/update-password?user_id=${authStore.user.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({ old_password: oldPassword.value, new_password: newPassword.value })
    })
    const result = await response.json()
    if (result.success) {
      showToast('密码修改成功')
      oldPassword.value = ''
      newPassword.value = ''
      confirmPassword.value = ''
    } else {
      showToast(result.detail || '修改失败', 'error')
    }
  } catch (error) {
    showToast('修改失败，请检查网络', 'error')
  }
}

// ===== 跳转到问卷编辑模式 =====
function goOnboarding() {
  router.push('/onboarding?edit=true')
}

// ===== 退出登录 =====
async function handleLogout() {
  try {
    await showConfirm('确认退出', '确定要退出登录吗？')
    await authStore.logout()
    showToast('已退出')
    router.push('/login')
  } catch (e) { /* 用户取消 */ }
}

function goHome() { router.push('/') }

// ===== 微信绑定 =====
const bindQrcode = ref('')
const bindStatus = ref('')
const bindLoading = ref(false)
let bindPollTimer = null

async function handleBindWechat() {
  bindLoading.value = true
  const result = await authStore.bindWechat()
  bindLoading.value = false
  if (result.success) {
    bindQrcode.value = result.qrcode
    bindStatus.value = '请用微信扫描二维码'
    let attempts = 0
    bindPollTimer = setInterval(async () => {
      attempts++
      if (attempts > 150) {
        clearInterval(bindPollTimer); bindPollTimer = null
        bindStatus.value = '已过期，请重新获取'
        setTimeout(() => { bindQrcode.value = '' }, 2000)
        return
      }
      const pr = await authStore.bindWechatPoll(result.pollToken)
      if (pr.success) {
        clearInterval(bindPollTimer); bindPollTimer = null
        bindStatus.value = '绑定成功！'
        if (authStore.user) {
          authStore.user.wechat_openid = 'bound'
        }
        showToast('微信绑定成功！')
        setTimeout(() => { bindQrcode.value = '' }, 1500)
      } else if (pr.message) {
        clearInterval(bindPollTimer); bindPollTimer = null
        bindStatus.value = pr.message
        setTimeout(() => { bindQrcode.value = '' }, 2000)
      }
    }, 2000)
  } else {
    showToast(result.message || '获取绑定二维码失败', 'error')
  }
}

function cancelBind() {
  if (bindPollTimer) { clearInterval(bindPollTimer); bindPollTimer = null }
  bindQrcode.value = ''
  bindStatus.value = ''
}

onMounted(() => {
  nickname.value = user.value?.nickname || ''
  bio.value = user.value?.bio || ''
})

onUnmounted(() => {
  if (bindPollTimer) { clearInterval(bindPollTimer); bindPollTimer = null }
})

import { reactive } from 'vue'
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  padding: 20px 28px;
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
}
[data-theme="light"] .profile-page { background-image: url('/assets/bg/profile_bg.jpg'); }
[data-theme="dark"]  .profile-page { background-image: url('/assets/bg/profile_bl.jpg'); }

.profile-topbar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}
.profile-topbar h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.profile-container {
  max-width: 700px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ====== 毛玻璃卡片 ====== */
.profile-card {
  padding: 20px 24px;
  border-radius: 16px;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.06);
  transition: all 0.3s ease;
}
.profile-card:hover {
  border-color: rgba(255,255,255,0.10);
}
[data-theme="dark"] .profile-card {
  background: rgba(0,0,0,0.25);
  border-color: rgba(255,255,255,0.04);
}
[data-theme="dark"] .profile-card:hover {
  border-color: rgba(255,255,255,0.08);
}

/* ====== 按钮系统 ====== */
.glass-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: all 0.25s ease;
  font-family: inherit;
}
.glass-btn:hover {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.10);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}
.glass-btn:active { transform: scale(0.97); }
.glass-btn .icon { width: 18px; height: 18px; }
.glass-btn.small { padding: 4px 14px; font-size: 13px; }
.back-btn .icon { width: 20px; height: 20px; }
.glass-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none !important; }

.glass-btn.primary {
  color: #409EFF;
  background: rgba(64,158,255,0.08);
  border-color: rgba(64,158,255,0.10);
}
.glass-btn.primary:hover {
  background: rgba(64,158,255,0.15);
  border-color: rgba(64,158,255,0.22);
  box-shadow: 0 4px 20px rgba(64,158,255,0.12);
}

.glass-btn.warning {
  color: #F59E0B;
  background: rgba(245,158,11,0.08);
  border-color: rgba(245,158,11,0.10);
}
.glass-btn.warning:hover {
  background: rgba(245,158,11,0.14);
  border-color: rgba(245,158,11,0.20);
}

.glass-btn.danger {
  color: #f56c6c;
  background: rgba(245,108,108,0.06);
  border-color: rgba(245,108,108,0.06);
}
.glass-btn.danger:hover {
  background: rgba(245,108,108,0.14);
  border-color: rgba(245,108,108,0.16);
}

/* ====== 表单控件 ====== */
.field-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.field-row {
  display: flex;
  gap: 10px;
}
.field-row .glass-input { flex: 1; }

.glass-input {
  width: 100%;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary);
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.25s ease;
  outline: none;
  font-family: inherit;
}
.glass-input::placeholder { color: var(--text-muted); opacity: 0.4; }
.glass-input:focus {
  border-color: rgba(64,158,255,0.20);
  background: rgba(255,255,255,0.04);
  box-shadow: 0 0 0 4px rgba(64,158,255,0.04);
}
.glass-input.textarea { resize: vertical; min-height: 80px; }
select.glass-input { cursor: pointer; appearance: none; }

/* ====== 头像区 ====== */
.avatar-section {
  display: flex;
  align-items: center;
  gap: 32px;
  flex-wrap: wrap;
}
.avatar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}
.avatar-ring {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  border: 3px solid var(--border-color);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.04);
  transition: border-color 0.3s;
}
.avatar-ring:hover { border-color: rgba(64,158,255,0.3); }
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder { font-size: 40px; font-weight: 700; color: var(--text-primary); }

.user-basic { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.basic-row {
  display: flex; gap: 16px; padding: 6px 12px;
  border-radius: 8px;
  background: rgba(128,128,128,0.04);
}
.basic-row .label { color: var(--text-muted); font-size: 13px; min-width: 60px; }
.basic-row .value { color: var(--text-primary); font-size: 13px; font-weight: 500; }

/* ====== 偏好展示 ====== */
.preferences-section {
  /* subtle glow accent */
}
.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 16px;
  flex-wrap: wrap;
}
.section-title-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.section-hint {
  font-size: 12px;
  color: var(--text-muted);
}
.refill-btn {
  flex-shrink: 0;
  padding: 10px 22px;
}
.refill-btn:hover {
  box-shadow: 0 0 24px rgba(64,158,255,0.2), 0 4px 16px rgba(64,158,255,0.1);
}

.prefs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}
.pref-tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 14px 10px;
  border-radius: 12px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.25s ease;
  cursor: default;
}
.pref-tile:hover {
  background: rgba(255,255,255,0.06);
  border-color: rgba(255,255,255,0.10);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
[data-theme="dark"] .pref-tile { background: rgba(255,255,255,0.02); border-color: rgba(255,255,255,0.02); }
[data-theme="dark"] .pref-tile:hover { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.06); }

.pref-tile.empty .pref-value {
  color: var(--text-muted);
  font-style: italic;
}
.pref-tile:not(.empty) .pref-value {
  color: #409EFF;
}
.pref-icon { font-size: 20px; }
.pref-label { font-size: 11px; color: var(--text-muted); }
.pref-value { font-size: 13px; font-weight: 600; }

.refill-desc {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(64,158,255,0.04);
  border: 1px solid rgba(64,158,255,0.06);
}

/* ====== Toast ====== */
.toast-stack {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}
.toast-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  border-radius: 12px;
  background: rgba(20,20,40,0.92);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  pointer-events: auto;
  font-size: 14px;
  color: var(--text-primary);
}
.toast-success .toast-icon { color: #67c23a; font-weight: 700; }
.toast-error .toast-icon { color: #f56c6c; font-weight: 700; }
.toast-warning .toast-icon { color: #e6a23c; font-weight: 700; }

.toast-enter-active { transition: all 0.3s ease-out; }
.toast-leave-active { transition: all 0.2s ease-in; }
.toast-enter-from { opacity: 0; transform: translateX(40px); }
.toast-leave-to { opacity: 0; transform: translateX(40px); }

/* ====== 确认弹窗 ====== */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.45);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}
.modal-card {
  background: rgba(20,20,40,0.94);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 18px;
  padding: 28px 32px;
  max-width: 360px;
  width: 90%;
  box-shadow: 0 16px 48px rgba(0,0,0,0.3);
}
.modal-title { font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.modal-body { font-size: 14px; color: var(--text-secondary); margin-bottom: 20px; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }

.modal-fade-enter-active,
.modal-fade-leave-active { transition: opacity 0.25s ease; }
.modal-fade-enter-from,
.modal-fade-leave-to { opacity: 0; }

/* ====== 退出按钮 ====== */
.logout-btn {
  width: 100%;
  margin-top: 4px;
  justify-content: center;
  border-color: rgba(245,108,108,0.2) !important;
}

@media (max-width: 600px) {
  .profile-page { padding: 12px 16px; }
  .profile-card { padding: 16px; }
  .avatar-section { flex-direction: column; align-items: center; text-align: center; }
  .field-row { flex-direction: column; }
  .profile-topbar { flex-wrap: wrap; }
  .prefs-grid { grid-template-columns: repeat(2, 1fr); }
}

/* ===== 微信绑定 ===== */
.wechat-bound {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  font-size: 15px;
  color: var(--text-primary);
}
.wechat-bind-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #07c160, #06ad56) !important;
  color: #fff !important;
  border: none !important;
}
.wechat-bind-btn:hover {
  box-shadow: 0 4px 16px rgba(7, 193, 96, 0.3);
}
.wechat-bind-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-radius: 14px;
  border: 2px solid #07c160;
}
.wechat-bind-qr {
  width: 180px;
  height: 180px;
  border-radius: 8px;
}
.wechat-bind-tip {
  font-size: 14px;
  color: #333;
  margin: 0;
  font-weight: 500;
}
</style>
