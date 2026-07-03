<template>
  <div class="sidebar-content" :class="{ collapsed: isCollapsed }">
    <!-- ===== Logo ===== -->
    <div class="logo-section" @click="goHome">
      <img src="/logo.png" alt="基智" class="sidebar-logo" />
      <span v-if="!isCollapsed" class="logo-text">基智</span>
    </div>

    <!-- ===== 用户信息 ===== -->
    <div class="user-section" @click="goProfile">
      <el-avatar :size="isCollapsed ? 40 : 44" :src="authStore.user?.avatar_url || ''" class="user-avatar">
        {{ authStore.user?.nickname?.[0] || 'U' }}
      </el-avatar>

      <div v-if="!isCollapsed" class="user-detail">
        <div class="user-name-row">
          <span class="user-name">{{ authStore.user?.nickname || '用户' }}</span>
          <span class="user-account">{{ authStore.user?.account || '' }}</span>
        </div>
        <div class="user-status-wrapper" @click.stop>
          <span class="status-dot" :class="userStatusClass" />
          <span class="status-text" @click="toggleStatusMenu">{{ userStatusText }}</span>
          <i class="fas fa-chevron-down status-arrow" :class="{ rotated: statusMenuVisible }" @click="toggleStatusMenu" />
        </div>
      </div>

      <!-- ===== 段位 ===== -->
      <div v-if="!isCollapsed" class="rank-display">
        <span class="rank-icon" :style="{ color: rankColor }">{{ rankIcon }}</span>
        <span class="rank-name" :style="{ color: rankColor }">{{ rankName }}</span>
        <span class="rank-sub" :style="{ color: rankColor }">{{ rankSubSymbol }}</span>
        <span class="rank-level">Lv.{{ userLevel }}</span>
      </div>
    </div>

    <!-- ===== 状态下拉菜单 ===== -->
    <div v-if="statusMenuVisible" class="status-dropdown" @click.stop>
      <div
        v-for="s in statusOptions"
        :key="s.value"
        class="status-option-item"
        :class="{ active: userStatus === s.value }"
        @click="selectStatus(s.value)"
      >
        <span class="status-dot" :class="s.value" />
        <span>{{ s.label }}</span>
      </div>
    </div>

    <!-- ===== 导航菜单 ===== -->
    <nav class="nav-menu">
      <router-link to="/" class="nav-item" :class="{ active: activeMenu === '/' }" :title="isCollapsed ? '主界面' : ''">
        <i class="fas fa-house"></i><span>主界面</span>
      </router-link>
      <router-link to="/profile" class="nav-item" :class="{ active: activeMenu === '/profile' }" :title="isCollapsed ? '个人中心' : ''">
        <i class="fas fa-user"></i><span>个人中心</span>
      </router-link>
      <router-link to="/resource-lib" class="nav-item" :class="{ active: activeMenu === '/resource-lib' }" :title="isCollapsed ? '资源库' : ''">
        <i class="fas fa-book-open"></i><span>资源库</span>
      </router-link>
      <router-link to="/career" class="nav-item" :class="{ active: activeMenu === '/career' }" :title="isCollapsed ? '学程' : ''">
        <i class="fas fa-route"></i><span>学程</span>
      </router-link>
    </nav>

    <!-- ===== 工作台 ===== -->
    <Workbench v-if="!isCollapsed" />

    <!-- ===== 对话管理 ===== -->
    <div v-if="!isCollapsed" class="session-section">
      <div class="session-header" @click="showSessionList = !showSessionList">
        <span><i class="fas fa-comment-dots"></i> 对话</span>
        <div class="session-actions">
          <button class="icon-btn" @click.stop="createNewSession" title="新建对话"><i class="fas fa-plus"></i></button>
          <button class="icon-btn" @click.stop="showSessionList = !showSessionList" title="历史对话">
            <i class="fas fa-chevron-down" :class="{ rotated: showSessionList }"></i>
          </button>
        </div>
      </div>
      <div v-if="showSessionList" class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: s.id === currentSessionId }"
          @click="switchSession(s.id)"
        >
          <span class="session-title">{{ s.title || '新对话' }}</span>
          <button class="icon-btn-sm" @click.stop="deleteSession(s.id)"><i class="fas fa-times"></i></button>
        </div>
        <div v-if="!sessions.length" class="session-empty">暂无对话</div>
      </div>
    </div>

    <!-- ===== 底部 ===== -->
    <div class="sidebar-footer">
      <div class="theme-toggle" :class="{ collapsed: isCollapsed }">
        <div class="theme-options" :class="{ vertical: isCollapsed }">
          <button class="theme-btn" :class="{ active: themeStore.mode === 'light' }" @click="themeStore.setMode('light')" title="浅色">
            <i class="fas fa-sun"></i>
          </button>
          <button class="theme-btn" :class="{ active: themeStore.mode === 'dark' }" @click="themeStore.setMode('dark')" title="深色">
            <i class="fas fa-moon"></i>
          </button>
          <button class="theme-btn" :class="{ active: themeStore.mode === 'system' }" @click="themeStore.setMode('system')" title="跟随系统">
            <i class="fas fa-desktop"></i>
          </button>
        </div>
      </div>

      <button class="footer-btn feedback-btn" @click="showFeedback = true" :title="isCollapsed ? '意见反馈' : ''">
        <i class="fas fa-envelope"></i>
        <span v-if="!isCollapsed">意见反馈</span>
      </button>

      <button class="footer-btn logout-btn" @click="handleLogout" :title="isCollapsed ? '退出登录' : ''">
        <i class="fas fa-right-from-bracket"></i>
        <span v-if="!isCollapsed">退出登录</span>
      </button>
    </div>
  </div>

  <!-- ===== 反馈弹窗（无遮罩） ===== -->
  <el-dialog
    v-model="showFeedback"
    title="📬 意见反馈"
    width="420px"
    :append-to-body="true"
    :modal="false"
    class="feedback-dialog-wrapper"
    destroy-on-close
  >
    <div class="feedback-dialog">
      <p class="feedback-tip">感谢你的反馈，我们会认真对待每一条建议 💪</p>
      <el-form>
        <el-form-item>
          <div class="custom-select" @click.stop="feedbackMenuVisible = !feedbackMenuVisible">
            <span class="select-display">{{ feedbackTypeLabel }}</span>
            <i class="fas fa-chevron-down select-arrow" :class="{ rotated: feedbackMenuVisible }"></i>
          </div>
          <div v-if="feedbackMenuVisible" class="custom-select-dropdown" @click.stop>
            <div
              v-for="opt in feedbackOptions"
              :key="opt.value"
              class="select-option"
              :class="{ active: feedbackType === opt.value }"
              @click="selectFeedbackType(opt.value)"
            >
              {{ opt.label }}
            </div>
          </div>
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="feedbackContent"
            type="textarea"
            :rows="4"
            placeholder="请详细描述你的想法或遇到的问题..."
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
      </el-form>
    </div>
    <template #footer>
      <el-button @click="showFeedback = false">取消</el-button>
      <el-button type="primary" :loading="feedbackSubmitting" @click="submitFeedback">
        <i class="fas fa-paper-plane"></i> 提交
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, inject, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { useSessionStore } from '@/stores/session'
import { getUserStats } from '@/api/career'
import { ElMessage, ElMessageBox } from 'element-plus'
import Workbench from './Workbench.vue'
import { RANK_ICONS, RANK_COLORS, SUB_SYMBOLS } from '@/utils/constants'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const sessionStore = useSessionStore()

const isCollapsed = inject('sidebarCollapsed', ref(false))
const showSessionList = ref(false)
const showFeedback = ref(false)
const feedbackType = ref('suggestion')
const feedbackContent = ref('')
const feedbackSubmitting = ref(false)

const feedbackMenuVisible = ref(false)
const feedbackOptions = [
  { value: 'suggestion', label: '💡 功能建议' },
  { value: 'bug', label: '🐛 问题反馈' },
  { value: 'feature', label: '✨ 功能请求' },
  { value: 'other', label: '📝 其他' }
]
const feedbackTypeLabel = computed(() => {
  const found = feedbackOptions.find(o => o.value === feedbackType.value)
  return found ? found.label : '选择反馈类型'
})

function selectFeedbackType(value) {
  feedbackType.value = value
  feedbackMenuVisible.value = false
}

const activeMenu = computed(() => route.path)
const sessions = computed(() => sessionStore.sessions)
const currentSessionId = computed(() => sessionStore.currentSessionId)

const userStatus = ref('online')
const statusMenuVisible = ref(false)
const statusOptions = [
  { value: 'online', label: '在线' },
  { value: 'invisible', label: '隐身' }
  // 离线由系统自动设置，用户不能手动选
]
const userStatusClass = computed(() => userStatus.value)
const userStatusText = computed(() => {
  const map = { online: '在线', offline: '离线', invisible: '隐身' }
  return map[userStatus.value] || '在线'
})

function toggleStatusMenu(e) {
  e.stopPropagation()
  statusMenuVisible.value = !statusMenuVisible.value
}

function selectStatus(value) {
  userStatus.value = value
  statusMenuVisible.value = false
}

function handleClickOutside() {
  statusMenuVisible.value = false
  feedbackMenuVisible.value = false
}

const rankData = ref({ points: 0, rank: '启程', sub_rank: 1 })
const userLevel = ref(1)
const rankName = computed(() => rankData.value.rank || '启程')
const rankIcon = computed(() => RANK_ICONS[rankName.value] || '◈')
const rankColor = computed(() => RANK_COLORS[rankName.value] || '#888')
const rankSubSymbol = computed(() => SUB_SYMBOLS[rankData.value.sub_rank] || '○')

async function loadRankData() {
  try {
    const data = await getUserStats(authStore.user.id)
    rankData.value = data
    userLevel.value = Math.floor((data.points || 0) / 100) + 1
  } catch (error) {
    console.error('加载段位数据失败', error)
  }
}

function createNewSession() {
  sessionStore.createSession('新对话')
  ElMessage.success('新对话已创建')
  showSessionList.value = true
}

function switchSession(id) {
  sessionStore.switchSession(id)
}

function deleteSession(id) {
  ElMessageBox.confirm('确定要删除这个对话吗？', '确认删除')
    .then(() => {
      sessionStore.deleteSession(id)
      ElMessage.success('已删除')
    })
    .catch(() => {})
}

function goHome() {
  router.push('/')
}

function goProfile() {
  router.push('/profile')
}

async function submitFeedback() {
  if (!feedbackContent.value || feedbackContent.value.length < 10) {
    ElMessage.warning('内容至少10个字')
    return
  }
  if (!feedbackType.value) {
    ElMessage.warning('请选择反馈类型')
    return
  }
  feedbackSubmitting.value = true
  try {
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/feedback/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({
        user_id: authStore.user.id,
        user_email: authStore.user.email,
        user_nickname: authStore.user.nickname,
        type: feedbackType.value,
        content: feedbackContent.value
      })
    })
    if (res.ok) {
      ElMessage.success('感谢反馈！🎉')
      showFeedback.value = false
      feedbackContent.value = ''
      feedbackType.value = 'suggestion'
    } else {
      ElMessage.error('提交失败，请稍后重试')
    }
  } catch {
    ElMessage.error('网络错误')
  } finally {
    feedbackSubmitting.value = false
  }
}

function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '确认退出')
    .then(() => {
      authStore.logout()
      ElMessage.success('已退出')
      router.push('/login')
    })
    .catch(() => {})
}

onMounted(() => {
  sessionStore.loadSessions()
  loadRankData()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.sidebar-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 8px;
  position: relative;
}
.sidebar-logo {
  width: 28px;
  height: 28px;
  object-fit: contain;
  flex-shrink: 0;
}
.sidebar-content.collapsed .logo-text,
.sidebar-content.collapsed .user-detail,
.sidebar-content.collapsed .rank-display,
.sidebar-content.collapsed .nav-item span,
.sidebar-content.collapsed .footer-btn span {
  display: none;
}
.sidebar-content.collapsed .user-section {
  justify-content: center;
  padding: 4px 0;
}
.sidebar-content.collapsed .nav-item {
  justify-content: center;
  padding: 10px;
}
.sidebar-content.collapsed .nav-item i {
  font-size: 20px;
  margin: 0;
}
.sidebar-content.collapsed .theme-toggle {
  justify-content: center;
  padding: 4px;
}
.sidebar-content.collapsed .theme-options {
  flex-direction: column;
  gap: 2px;
}
.sidebar-content.collapsed .theme-btn {
  width: 28px;
  height: 28px;
  font-size: 14px;
}
.sidebar-content.collapsed .footer-btn {
  justify-content: center;
  padding: 8px;
}
.sidebar-content.collapsed .footer-btn i {
  font-size: 16px;
  margin: 0;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px 8px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.3s ease;
}
.logo-section:hover {
  opacity: 0.7;
  transform: scale(0.98);
}

.logo-icon {
  font-size: 24px;
  color: var(--text-primary);
  flex-shrink: 0;
}
.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 1px;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.04);
  cursor: pointer;
  transition: all 0.3s ease;
}
.user-section:hover {
  background: rgba(255, 255, 255, 0.10);
  transform: translateY(-1px);
}
[data-theme="dark"] .user-section {
  background: rgba(255, 255, 255, 0.02);
}
[data-theme="dark"] .user-section:hover {
  background: rgba(255, 255, 255, 0.06);
}

.user-avatar {
  flex-shrink: 0;
  border: 2px solid var(--border-color);
}
.user-detail {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.user-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
  white-space: nowrap;
}
.user-account {
  font-size: 11px;
  color: var(--text-muted);
  opacity: 0.6;
  white-space: nowrap;
}
.user-status-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 2px 0;
  border-radius: 4px;
  transition: all 0.2s ease;
  user-select: none;
}
.user-status-wrapper:hover {
  color: var(--text-primary);
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}
.status-dot.online { background: #22c55e; box-shadow: 0 0 8px rgba(34, 197, 94, 0.4); }
.status-dot.offline { background: #6b7280; }
.status-dot.invisible { background: #8b5cf6; box-shadow: 0 0 8px rgba(139, 92, 246, 0.4); }

.status-text {
  font-size: 12px;
}
.status-arrow {
  font-size: 10px;
  transition: transform 0.3s ease;
}
.status-arrow.rotated {
  transform: rotate(180deg);
}

.status-dropdown {
  position: absolute;
  top: 118px;
  left: 80px;
  background: rgba(255, 255, 255, 0.10);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 4px 0;
  min-width: 90px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  z-index: 100;
}
[data-theme="dark"] .status-dropdown {
  background: rgba(0, 0, 0, 0.35);
}
.status-option-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  transition: all 0.2s ease;
  border-radius: 6px;
  margin: 2px 4px;
}
.status-option-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
  transform: translateX(2px);
}
.status-option-item.active {
  background: rgba(255, 255, 255, 0.10);
  color: var(--text-primary);
}

.rank-display {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  padding: 4px 8px;
  border-radius: 10px;
  background: rgba(128, 128, 128, 0.06);
  flex-shrink: 0;
  margin-left: auto;
}
.rank-icon { font-size: 14px; }
.rank-name { font-weight: 600; font-size: 13px; }
.rank-sub { font-size: 13px; }
.rank-level { font-size: 11px; color: var(--text-muted); margin-left: 2px; }

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s ease;
  cursor: pointer;
}
.nav-item i { font-size: 18px; width: 22px; text-align: center; flex-shrink: 0; }
.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
  transform: translateX(4px);
}
.nav-item.active {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
}
[data-theme="dark"] .nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
}
[data-theme="dark"] .nav-item.active {
  background: rgba(255, 255, 255, 0.06);
}

.session-section {
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 255, 255, 0.04);
  padding: 6px 10px;
  margin-top: 2px;
}
[data-theme="dark"] .session-section {
  background: rgba(255, 255, 255, 0.02);
}
.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--text-secondary);
  padding: 2px 0;
  cursor: pointer;
}
.session-header i { font-size: 14px; margin-right: 4px; }
.session-header .fa-chevron-down { transition: transform 0.3s ease; }
.session-header .fa-chevron-down.rotated { transform: rotate(180deg); }
.session-actions { display: flex; gap: 2px; }
.icon-btn {
  background: none; border: none; color: var(--text-muted); cursor: pointer;
  padding: 4px 6px; border-radius: 6px; font-size: 13px; transition: all 0.2s ease;
}
.icon-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
  transform: scale(1.05);
}
.icon-btn-sm {
  background: none; border: none; color: var(--text-muted); cursor: pointer;
  padding: 2px 4px; border-radius: 4px; font-size: 11px; transition: all 0.2s ease;
}
.icon-btn-sm:hover {
  color: #f56c6c;
  transform: scale(1.1);
}
.session-list { margin-top: 6px; max-height: 150px; overflow-y: auto; }
.session-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 6px; border-radius: 6px; font-size: 13px; cursor: pointer;
  color: var(--text-secondary); transition: all 0.2s ease;
}
.session-item:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateX(2px);
}
.session-item.active {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
}
.session-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-empty { padding: 6px 0; font-size: 12px; color: var(--text-muted); text-align: center; }

.sidebar-footer {
  border-top: 1px solid var(--border-color);
  padding-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: auto;
}

.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.03);
}
.theme-options {
  display: flex;
  gap: 4px;
}
.theme-options.vertical {
  flex-direction: column;
  gap: 2px;
}
.theme-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.3s ease;
  color: var(--text-secondary);
}
.theme-btn:hover {
  background: rgba(255, 255, 255, 0.10);
  transform: scale(1.08);
  color: var(--text-primary);
}
.theme-btn.active {
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 0 0 2px rgba(128, 128, 128, 0.12);
  color: var(--text-primary);
}
.sidebar-content.collapsed .theme-btn {
  width: 28px;
  height: 28px;
  font-size: 14px;
}

.footer-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border: none;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.03);
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.footer-btn i { font-size: 16px; }
.feedback-btn:hover {
  background: rgba(64, 158, 255, 0.12);
  border-color: rgba(64, 158, 255, 0.2);
  color: #409eff;
  transform: translateY(-2px);
}
.logout-btn:hover {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  transform: translateY(-2px);
}

.custom-select {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-secondary);
  font-size: 14px;
  user-select: none;
}
.custom-select:hover {
  background: rgba(255, 255, 255, 0.10);
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateY(-1px);
}
[data-theme="dark"] .custom-select {
  background: rgba(255, 255, 255, 0.03);
}
.select-display { color: var(--text-primary); }
.select-arrow {
  font-size: 12px;
  color: var(--text-muted);
  transition: transform 0.3s ease;
}
.select-arrow.rotated { transform: rotate(180deg); }

.custom-select-dropdown {
  position: absolute;
  top: 44px;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.10);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 4px 0;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  z-index: 100;
  min-width: 160px;
}
[data-theme="dark"] .custom-select-dropdown {
  background: rgba(0, 0, 0, 0.35);
}
.select-option {
  padding: 8px 14px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all 0.2s ease;
  border-radius: 6px;
  margin: 2px 4px;
}
.select-option:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
  transform: translateX(2px);
}
.select-option.active {
  background: rgba(255, 255, 255, 0.10);
  color: var(--text-primary);
}

.feedback-dialog {
  padding: 4px 0;
}
.feedback-tip {
  color: var(--text-muted);
  font-size: 14px;
  margin-bottom: 16px;
  text-align: center;
}
.feedback-dialog :deep(.el-form-item) {
  margin-bottom: 16px;
  position: relative;
}
.feedback-dialog :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.06) !important;
  color: var(--text-primary) !important;
  border-radius: 10px !important;
  transition: all 0.3s ease !important;
}
.feedback-dialog :deep(.el-textarea__inner:hover) {
  border-color: rgba(255, 255, 255, 0.15) !important;
}
[data-theme="dark"] .feedback-dialog :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.04) !important;
}
.feedback-dialog :deep(.el-textarea__inner:focus) {
  border-color: rgba(255, 255, 255, 0.2) !important;
}
.feedback-dialog :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.06) !important;
  border-radius: 10px !important;
  transition: all 0.3s ease !important;
}
.feedback-dialog :deep(.el-input__wrapper:hover) {
  border-color: rgba(255, 255, 255, 0.15) !important;
}
[data-theme="dark"] .feedback-dialog :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.04) !important;
}
</style>

<style>
/* ===== 反馈弹窗（无遮罩，独立毛玻璃） ===== */
.feedback-dialog-wrapper {
  --el-dialog-bg-color: transparent;
}
.feedback-dialog-wrapper .el-overlay {
  background: transparent !important;
  backdrop-filter: none !important;
}
.feedback-dialog-wrapper .el-dialog {
  background: rgba(255, 255, 255, 0.08) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.10) !important;
  border-radius: 16px !important;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.2) !important;
}
[data-theme="dark"] .feedback-dialog-wrapper .el-dialog {
  background: rgba(0, 0, 0, 0.3) !important;
  border-color: rgba(255, 255, 255, 0.06) !important;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4) !important;
}
.feedback-dialog-wrapper .el-dialog__header {
  padding: 16px 20px 0;
}
.feedback-dialog-wrapper .el-dialog__title {
  color: var(--text-primary) !important;
  font-weight: 600;
}
.feedback-dialog-wrapper .el-dialog__body {
  padding: 12px 20px 8px;
}
.feedback-dialog-wrapper .el-dialog__footer {
  padding: 0 20px 16px;
}
.feedback-dialog-wrapper .el-button {
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
  color: var(--text-secondary) !important;
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}
.feedback-dialog-wrapper .el-button:hover {
  background: rgba(255, 255, 255, 0.12) !important;
  transform: translateY(-2px);
}
.feedback-dialog-wrapper .el-button--primary {
  background: rgba(64, 158, 255, 0.15) !important;
  border-color: rgba(64, 158, 255, 0.2) !important;
  color: #66b1ff !important;
}
.feedback-dialog-wrapper .el-button--primary:hover {
  background: rgba(64, 158, 255, 0.25) !important;
}
</style>