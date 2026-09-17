<template>
  <div class="sidebar-content" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-scroll">
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
        <!-- 第一行：昵称 -->
        <div class="user-name-row">
          <span class="user-name">{{ authStore.user?.nickname || '用户' }}</span>
        </div>

        <!-- 第二行：账号 | 段位 | Lv -->
        <div class="user-row-middle">
          <span class="user-account">{{ authStore.user?.user_account || '' }}</span>
          <span class="user-rank-tag" :style="{ color: rankColor }">
            {{ rankIcon }} {{ rankName }}
          </span>
          <span class="user-level-tag">Lv.{{ userLevel }}</span>
        </div>

        <!-- 第三行：年级 | 专业 + 状态 -->
        <div class="user-row-bottom">
          <span class="user-grade">{{ authStore.user?.grade || '未设置' }}</span>
          <span class="user-major">{{ authStore.user?.major || '' }}</span>
          <span class="user-status-wrapper" @click.stop>
            <span class="status-dot" :class="userStatusClass" />
            <span class="status-text" @click="toggleStatusMenu">{{ userStatusText }}</span>
            <i class="fas fa-chevron-down status-arrow" :class="{ rotated: statusMenuVisible }" @click="toggleStatusMenu" />
          </span>
        </div>
      </div>
    </div>

    <!-- ===== 状态下拉菜单 ===== -->
    <Transition name="dropdown">
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
    </Transition>

    <!-- ===== 全局搜索（点击打开搜索面板，Ctrl+K 全局可用） ===== -->
    <div class="global-search" :class="{ collapsed: isCollapsed }" @click="navStore.openSearch()">
      <i class="fas fa-search gs-search-icon" />
      <span v-if="!isCollapsed" class="gs-search-ph">搜索页面、考纲、真题…</span>
      <span v-if="!isCollapsed" class="gs-search-kbd">Ctrl K</span>
    </div>

    <!-- ===== 导航区（2026-08-25 半椭圆轮盘：上方固定 logo/用户/搜索，下方转动显示） ===== -->
    <NavWheel v-if="!isCollapsed" :items="navItems" />
    <nav v-else class="nav-menu list">
      <router-link
        v-for="item in navItems"
        :key="item.key"
        :to="item.to"
        class="app-icon"
        :class="{ active: item.active }"
        :title="item.label"
      >
        <div class="icon-anchor">
          <div class="icon-wrap">
            <img :src="iconPath(item.icon)" :alt="item.label" class="icon-img" />
          </div>
        </div>
      </router-link>
    </nav>

    <!-- 工具区分割 -->
    <div class="section-label" v-show="!isCollapsed"><span>工具</span></div>
    <div class="section-line" v-show="isCollapsed"></div>

    <!-- ===== 工具区 ===== -->
    <nav class="nav-menu" :class="{ grid: !isCollapsed, list: isCollapsed }">
      <router-link
        v-for="item in toolItems"
        :key="item.key"
        to=""
        class="app-icon tool-icon"
        :class="{ active: item.active }"
        :title="isCollapsed ? item.label : ''"
        @click.prevent="openToolPanel(item.tool)"
      >
        <div class="icon-anchor">
          <div class="icon-wrap">
            <img :src="iconPath(item.icon)" :alt="item.label" class="icon-img" />
          </div>
        </div>
        <span v-if="!isCollapsed" class="icon-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <ToolPanel ref="toolPanelRef" />

    <!-- ===== 工具面板（点击工具图标弹出，组件已抽出） ===== -->
    </div><!-- /sidebar-scroll -->

    <!-- ===== 底部（固定）===== -->
    <div class="sidebar-footer">
      <button class="footer-btn feedback-btn" @click="showFeedback = true" :title="isCollapsed ? '意见反馈' : ''">
        <i class="fas fa-envelope"></i>
        <span v-if="!isCollapsed">意见反馈</span>
      </button>

      <button class="footer-btn guide-btn" @click="$router.push('/guide')" :title="isCollapsed ? '使用指引' : ''">
        <i class="fas fa-compass"></i>
        <span v-if="!isCollapsed">使用指引</span>
      </button>

      <button class="footer-btn opensource-btn" @click="$router.push('/open-source')" :title="isCollapsed ? '开源文档' : ''">
        <i class="fas fa-book-open"></i>
        <span v-if="!isCollapsed">开源文档</span>
      </button>

      <button class="footer-btn logout-btn" @click="handleLogout" :title="isCollapsed ? '退出登录' : ''">
        <i class="fas fa-right-from-bracket"></i>
        <span v-if="!isCollapsed">退出登录</span>
      </button>
    </div>
  </div>

  <!-- ===== 反馈弹窗 ===== -->
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
import { getUserStats } from '@/api/career'
import NavWheel from '@/components/NavWheel.vue'
import ToolPanel from '@/components/ToolPanel.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { RANK_ICONS, RANK_COLORS, SUB_SYMBOLS } from '@/utils/constants'
import { useNavStore } from '@/stores/nav'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const navStore = useNavStore()

// ===== 工具面板（2026-08-25 抽到 ToolPanel 组件，学程/社区侧边栏与主界面中枢共用） =====
const toolPanelRef = ref(null)

function openToolPanel(tool) { toolPanelRef.value?.openTool(tool) }

const iconBase = '/assets/icons/sidebar/'
function iconPath(name) { return iconBase + name }

const navItems = computed(() => {
  const items = [
    { to: '/home',         icon: 'xiaoji.png',          label: '小基',     key: 'home' },
    { to: '/profile',      icon: 'profile.png',         label: '个人中心', key: 'profile' },
    { to: '/settings',     icon: 'settings.png',        label: '设置',     key: 'settings' },
    { to: '/resource-lib', icon: 'resource-lib.png',    label: '资源库',   key: 'resource-lib' },
    { to: '/evaluation-center', icon: 'evaluation.png', label: '评估中心', key: 'evaluation-center' },
    { to: '/career',       icon: 'career.png',          label: '学程',     key: 'career',     badge: 'career' },
    { to: '/profile-card', icon: 'profile-card.png',    label: '个人画像', key: 'profile-card', highlight: true },
    { to: '/subject-plan', icon: 'subject-plan.png',    label: '学科计划', key: 'subject-plan' },
    { to: '/video-square', icon: 'video-library.png',   label: '视频库',   key: 'video-square' },
    { to: '/community',    icon: 'community.png',       label: '社区',     key: 'community',  badge: 'community' },
    { to: '/qa',           icon: 'qa.png',              label: 'Q&A',      key: 'qa' },
    { to: '/message',      icon: 'messages.png',        label: '消息中心', key: 'messages',   badge: 'total' },
    { to: '/agent-center', icon: 'agent-center.png',    label: '智能体中心', key: 'agent-center' },
    { to: '/wordbook',     icon: 'wordbook.png',        label: '词条本',   key: 'wordbook' },
    { to: '/api-center',   icon: 'api-center.png',      label: 'API管理',  key: 'api-center' },
  ]
  if (authStore.user?.role !== 'user') {
    items.push({ to: '/admin', icon: 'admin.png', label: '管理后台', key: 'admin', admin: true })
  }
  // 工具区
  return items.map(item => ({
    ...item,
    active: route.path.startsWith(item.to),
    badgeCount: item.badge === 'career' ? careerBadge.value
              : item.badge === 'community' ? communityUnreadCount.value
              : item.badge === 'total' ? unreadCount.value
              : 0,
  }))
})

// 工具区图标（独立分组）
const toolItems = computed(() => {
  const tools = [
    { icon: 'checkin.png',   label: '打卡',     key: 'checkin',   tool: 'checkin' },
    { icon: 'countdown.png', label: '时间胶囊', key: 'countdown', tool: 'countdown' },
    { icon: 'timer.png',     label: '计时器',   key: 'timer',     tool: 'timer' },
  ]
  return tools.map(t => ({
    ...t,
    active: false,
    badgeCount: 0,
  }))
})

const userStatus = ref('online')
const statusMenuVisible = ref(false)
const statusOptions = [
  { value: 'online', label: '在线' },
  { value: 'invisible', label: '隐身' }
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

const rankData = ref({ points: 0, level_points: 0, rank: '启程', sub_rank: 1 })

function calcLevel(lp) {
  let level = 1
  let totalNeeded = 2
  while (lp >= totalNeeded) {
    level++
    totalNeeded += (level + 1)
  }
  return level
}

const userLevel = computed(() => calcLevel(rankData.value.level_points || 0))
const rankName = computed(() => rankData.value.rank || '启程')
const rankIcon = computed(() => RANK_ICONS[rankName.value] || '◈')
const rankColor = computed(() => RANK_COLORS[rankName.value] || '#888')
const rankSubSymbol = computed(() => SUB_SYMBOLS[rankData.value.sub_rank] || '○')

async function loadRankData() {
  if (!authStore.user?.id) return
  try {
    const data = await getUserStats(authStore.user.id)
    rankData.value = data
  } catch (error) {
    console.error('加载段位数据失败', error)
  }
}



function goHome() {
  router.push('/home')
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
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/feedback/submit`, {
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
    .then(async () => {
      await authStore.logout()
      ElMessage.success('已退出')
      await new Promise(resolve => setTimeout(resolve, 100))
      router.push('/login')
    })
    .catch(() => {})
}

const unreadCount = ref(0)
const communityUnreadCount = ref(0)
const careerBadge = ref(0)

async function loadBadges() {
  const uid = authStore.user?.id
  const token = authStore.token
  if (!uid || !token) { stopBadgePolling(); return }
  const base = import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'
  try {
    const res = await fetch(`${base}/community/sidebar-badges?user_id=${uid}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.status === 401) {
      // token 过期，停止轮询，不再骚扰后端
      stopBadgePolling()
      return
    }
    if (!res.ok) throw new Error('badges failed')
    const data = await res.json()
    const b = data.badges || {}
    unreadCount.value = b.total || 0
    communityUnreadCount.value = b.community || 0
    careerBadge.value = b.career || 0
  } catch {
    // 网络错误等静默处理
  }
}

function stopBadgePolling() {
  if (badgeTimer) { clearInterval(badgeTimer); badgeTimer = null }
}

function startBadgePolling() {
  stopBadgePolling()
  loadBadges()
  badgeTimer = setInterval(() => { loadBadges() }, 30000)
}

let badgeTimer = null

onMounted(() => {
  // 仅在已登录时加载
  if (!authStore.isLoggedIn) return

  loadRankData()
  loadBadges()
  document.addEventListener('click', handleClickOutside)
  badgeTimer = setInterval(() => { loadBadges() }, 30000)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (badgeTimer) clearInterval(badgeTimer)
})
</script>

<style scoped>
.sidebar-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  position: relative;
}

/* 可滚动的上半部分 */
.sidebar-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-bottom: 4px;
}
.sidebar-scroll::-webkit-scrollbar { width: 3px; }
.sidebar-scroll::-webkit-scrollbar-thumb { background: rgba(128,128,128,.15); border-radius: 2px; }

.sidebar-logo {
  width: 28px;
  height: 28px;
  object-fit: contain;
  flex-shrink: 0;
}

/* 收起时 — 用 opacity + max-width 过渡替代 display:none */
.sidebar-content.collapsed .logo-text,
.sidebar-content.collapsed .user-detail,
.sidebar-content.collapsed .icon-label,
.sidebar-content.collapsed .footer-btn span,
.sidebar-content.collapsed .section-label span,
.sidebar-content.collapsed .user-section {
  justify-content: center;
  padding: 4px 0;
}
.sidebar-content.collapsed .app-icon {
  justify-content: center;
  padding: 4px 2px;
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

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 1px;
  opacity: 1;
  max-width: 120px;
  overflow: hidden;
  white-space: nowrap;
  transition: opacity 0.3s ease, max-width 0.3s ease;
}

/* ===== 用户信息 ===== */
.user-section {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: all 0.3s ease;
}

/* ===== 全局搜索框（点击打开搜索面板） ===== */
.global-search {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 2px 2px;
  padding: 9px 12px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  border: 1px solid var(--line-soft);
  cursor: pointer;
  transition: all 0.25s ease;
}
.global-search:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 9%, transparent);
  border-color: rgba(108,140,255,0.35);
}
.global-search.collapsed {
  justify-content: center;
  padding: 9px 0;
  margin: 10px 0 2px;
}
.gs-search-icon { color: var(--text-muted, #94a3b8); font-size: 13px; }
.gs-search-ph {
  flex: 1;
  color: var(--text-muted, #94a3b8);
  font-size: 12.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.gs-search-kbd {
  font-size: 10px;
  color: var(--text-muted, #94a3b8);
  border: 1px solid var(--line-soft);
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  padding: 1px 6px;
  border-radius: 4px;
  flex-shrink: 0;
}
.user-section:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
}
[data-theme="dark"] .user-section {
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
}
[data-theme="dark"] .user-section:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
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
  justify-content: center;
  gap: 1px;
  opacity: 1;
  transition: opacity 0.3s ease;
}

/* 第一行：昵称 */
.user-name-row {
  display: flex;
  align-items: center;
}
.user-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 15px;
  line-height: 1.4;
}

/* 第二行：账号 | 段位 | Lv */
.user-row-middle {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.user-account {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}
.user-rank-tag {
  font-size: 11px;
  font-weight: 500;
  background: rgba(128,128,128,0.06);
  padding: 0 8px;
  border-radius: 10px;
}
.user-level-tag {
  font-size: 11px;
  font-weight: 500;
  color: var(--brand);
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  padding: 0 8px;
  border-radius: 10px;
}

/* 第三行：年级 | 专业 + 状态 */
.user-row-bottom {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.user-grade {
  font-size: 11px;
  color: var(--text-muted);
  background: rgba(128,128,128,0.06);
  padding: 0 6px;
  border-radius: 4px;
}
.user-major {
  font-size: 11px;
  color: var(--text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 80px;
}
.user-status-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-muted);
  cursor: pointer;
  padding: 1px 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
  margin-left: auto;
}
.user-status-wrapper:hover {
  color: var(--text-primary);
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
  flex-shrink: 0;
}
.status-dot.online { background: #22c55e; box-shadow: 0 0 8px rgba(34,197,94,0.3); }
.status-dot.offline { background: #6b7280; }
.status-dot.invisible { background: #8b5cf6; box-shadow: 0 0 8px rgba(139,92,246,0.3); }
.status-text { font-size: 11px; }
.status-arrow { font-size: 9px; transition: transform 0.3s ease; }
.status-arrow.rotated { transform: rotate(180deg); }

/* ===== 状态下拉菜单 ===== */
.status-dropdown {
  position: absolute;
  top: 120px;
  left: 80px;
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--line-soft);
  border-radius: 10px;
  padding: 4px 0;
  min-width: 90px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
  z-index: 100;
}
[data-theme="dark"] .status-dropdown {
  background: var(--well);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
  color: var(--text-primary);
  transform: translateX(2px);
}
.status-option-item.active {
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  color: var(--text-primary);
}

/* ===== 导航菜单 — App 图标网格 ===== */
.nav-menu {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  transition: grid-template-columns 0.3s ease, gap 0.3s ease;
}
.nav-menu.list {
  grid-template-columns: 1fr;
  gap: 4px;
  justify-items: center;
}

/* ===== 单个 App 图标 ===== */
.app-icon {
  display: flex; flex-direction: column; align-items: center; gap: 5px;
  padding: 6px 2px; border-radius: 12px;
  text-decoration: none; cursor: pointer;
  transition: transform .2s ease, filter .2s ease;
  -webkit-tap-highlight-color: transparent;
}
.app-icon:hover { transform: scale(1.05); }
.app-icon:active { transform: scale(.94); }
.app-icon.active .icon-wrap {
  filter: brightness(1.2) drop-shadow(0 0 6px rgba(255,255,255,.3));
  transform: scale(1.06);
}

/* ===== 图标容器（2026-08-25 全部改裸 PNG：只有图标本身，无任何装饰） ===== */
.icon-anchor { position: relative; flex-shrink: 0; }
.icon-wrap {
  position: relative; width: 52px; height: 52px;
  border: none;
  background: transparent;
  transition: all .25s ease;
}
.nav-menu.list .icon-wrap { width: 40px; height: 40px; border-radius: 10px; }
.icon-img { width: 100%; height: 100%; object-fit: contain; display: block; }

/* 角标 — 挂在 icon-anchor 上，不被 overflow:hidden 切割 */
.icon-badge {
  position: absolute; top: -5px; right: -5px;
  min-width: 18px; height: 18px; padding: 0 6px;
  border-radius: 9px; font-size: 10px; font-weight: 700;
  line-height: 18px; text-align: center;
  background: #ef4444; color: #fff;
  pointer-events: none; z-index: 2;
}

/* 区域分隔 */
.section-label {
  text-align: center; padding: 6px 0 2px; font-size: 10px;
  color: var(--text-muted); letter-spacing: .1em; text-transform: uppercase;
  opacity: 1;
  transition: opacity 0.3s ease, max-height 0.3s ease, padding 0.3s ease;
}
.section-line { height: 1px; margin: 4px 8px; background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent); }

/* 标签 */
.icon-label {
  font-size: 10px; color: var(--text-secondary); text-align: center;
  line-height: 1.2; max-width: 64px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  opacity: 1;
  transition: opacity 0.3s ease;
}


/* ===== 对话迷你按钮 ===== */
.chat-mini-btn:active { transform: scale(.95); }
.chat-mini-icon {
  width: 32px; height: 32px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s;
}
.chat-mini-icon svg { width: 16px; height: 16px; }
.chat-mini-icon.new { background: linear-gradient(145deg, rgba(34,197,94,.3), rgba(20,184,166,.3)); color: #4ade80; }
.chat-mini-icon.history { background: linear-gradient(145deg, rgba(99,102,241,.3), rgba(139,92,246,.3)); color: #a78bfa; }
.chat-mini-label { font-size: 10px; color: var(--text-secondary); opacity: 1; transition: opacity 0.3s ease; }
.chat-mini-row.collapsed .chat-mini-icon { width: 28px; height: 28px; border-radius: 7px; }
.chat-mini-row.collapsed .chat-mini-icon svg { width: 13px; height: 13px; }

.sidebar-footer {
  border-top: 1px solid var(--border-color);
  padding-top: 8px;
  padding-bottom: 0;
  margin-bottom: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;           /* 固定不收缩 */
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
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid rgba(255,255,255,0.03);
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.footer-btn i {
  font-size: 16px;
}
/* ===== 下拉过渡动画 ===== */
.dropdown-enter-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.dropdown-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.dropdown-enter-from { opacity: 0; transform: translateY(-6px) scale(0.96); }
.dropdown-leave-to { opacity: 0; transform: translateY(-4px) scale(0.96); }

.feedback-btn:hover {
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  border-color: color-mix(in srgb, var(--brand) 20%, transparent);
  color: var(--brand);
  transform: translateY(-2px);
}
.opensource-btn {
  font-size: 12px !important;
  opacity: 0.55;
}
.opensource-btn i { font-size: 13px !important; }
.opensource-btn span { font-size: 12px !important; }
.opensource-btn:hover {
  background: rgba(16,185,129,0.10);
  border-color: rgba(16,185,129,0.15);
  color: color-mix(in srgb, #34d399 65%, var(--text-primary));
  transform: translateY(-1px);
  opacity: 0.9;
}
.logout-btn:hover {
  background: rgba(239,68,68,0.12);
  border-color: rgba(239,68,68,0.2);
  color: #ef4444;
  transform: translateY(-2px);
}

.custom-select {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  border: 1px solid rgba(255,255,255,0.06);
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-secondary);
  font-size: 14px;
  user-select: none;
}
.custom-select:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  border-color: var(--line-soft);
  transform: translateY(-1px);
}
[data-theme="dark"] .custom-select {
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
}
.select-display {
  color: var(--text-primary);
}
.select-arrow {
  font-size: 12px;
  color: var(--text-muted);
  transition: transform 0.3s ease;
}
.select-arrow.rotated {
  transform: rotate(180deg);
}

.custom-select-dropdown {
  position: absolute;
  top: 44px;
  left: 0;
  right: 0;
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--line-soft);
  border-radius: 10px;
  padding: 4px 0;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
  z-index: 100;
  min-width: 160px;
}
[data-theme="dark"] .custom-select-dropdown {
  background: var(--well);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
  color: var(--text-primary);
  transform: translateX(2px);
}
.select-option.active {
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent) !important;
  border-color: rgba(255,255,255,0.06) !important;
  color: var(--text-primary) !important;
  border-radius: 10px !important;
  transition: all 0.3s ease !important;
}
.feedback-dialog :deep(.el-textarea__inner:hover) {
  border-color: var(--line) !important;
}
[data-theme="dark"] .feedback-dialog :deep(.el-textarea__inner) {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent) !important;
}
.feedback-dialog :deep(.el-textarea__inner:focus) {
  border-color: var(--line-strong) !important;
}
.feedback-dialog :deep(.el-input__wrapper) {
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent) !important;
  border-color: rgba(255,255,255,0.06) !important;
  border-radius: 10px !important;
  transition: all 0.3s ease !important;
}
.feedback-dialog :deep(.el-input__wrapper:hover) {
  border-color: var(--line) !important;
}
[data-theme="dark"] .feedback-dialog :deep(.el-input__wrapper) {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent) !important;
}
</style>

<style>

.feedback-dialog-wrapper {
  --el-dialog-bg-color: transparent;
}
.feedback-dialog-wrapper .el-overlay {
  background: transparent !important;
  backdrop-filter: none !important;
}
.feedback-dialog-wrapper .el-dialog {
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid var(--line-soft) !important;
  border-radius: 16px !important;
  box-shadow: 0 8px 40px rgba(0,0,0,0.2) !important;
}
[data-theme="dark"] .feedback-dialog-wrapper .el-dialog {
  background: var(--well) !important;
  border-color: rgba(255,255,255,0.06) !important;
  box-shadow: 0 8px 40px rgba(0,0,0,0.4) !important;
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
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  color: var(--text-secondary) !important;
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}
.feedback-dialog-wrapper .el-button:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 12%, transparent) !important;
  transform: translateY(-2px);
}
.feedback-dialog-wrapper .el-button--primary {
  background: color-mix(in srgb, var(--brand) 15%, transparent) !important;
  border-color: color-mix(in srgb, var(--brand) 20%, transparent) !important;
  color: var(--brand-bright) !important;
}
.feedback-dialog-wrapper .el-button--primary:hover {
  background: color-mix(in srgb, var(--brand) 25%, transparent) !important;
}
</style>