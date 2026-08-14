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

    <!-- ===== 导航区 ===== -->
    <nav class="nav-menu" :class="{ grid: !isCollapsed, list: isCollapsed }">
      <router-link
        v-for="item in navItems"
        v-show="item.visible !== false"
        :key="item.key"
        :to="item.to"
        class="app-icon"
        :class="{ active: item.active, highlighted: item.highlight, admin: item.admin }"
        :title="isCollapsed ? item.label : ''"
      >
        <div class="icon-anchor">
          <div class="icon-wrap" :style="iconStyle(item.key)">
            <img :src="iconPath(item.icon)" :alt="item.label" class="icon-img" />
          </div>
          <span v-if="item.badgeCount > 0" class="icon-badge">{{ item.badgeCount > 99 ? '99+' : item.badgeCount }}</span>
        </div>
        <span v-if="!isCollapsed" class="icon-label">{{ item.label }}</span>
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
          <div class="icon-wrap" :style="iconStyle(item.key)">
            <img :src="iconPath(item.icon)" :alt="item.label" class="icon-img" />
          </div>
        </div>
        <span v-if="!isCollapsed" class="icon-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- ===== 对话历史面板 ===== -->
    <Teleport to="body">
      <transition name="panel-slide">
        <div v-if="chatPanelOpen" class="tool-panel-overlay" @click.self="chatPanelOpen = false">
          <div class="tool-panel">
            <div class="tp-header">
              <span class="tp-title">历史对话</span>
              <button class="tp-close" @click="chatPanelOpen = false">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
              </button>
            </div>
            <div class="tp-body">
              <div v-if="sessions.length" class="tp-list">
                <div
                  v-for="s in sessions" :key="s.id"
                  class="tp-item chat-session-item"
                  :class="{ active: s.id === currentSessionId }"
                  @click="switchSession(s.id); chatPanelOpen = false"
                >
                  <span class="tp-item-name">{{ s.title || '新对话' }}</span>
                  <button class="tp-del" @click.stop="deleteSession(s.id)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button>
                </div>
              </div>
              <div v-else class="tp-empty">暂无对话</div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- ===== 工具面板（点击工具图标弹出）===== -->
    <Teleport to="body">
      <transition name="panel-slide">
        <div v-if="panelTool" class="tool-panel-overlay" @click.self="closeToolPanel">
          <div class="tool-panel">
            <div class="tp-header">
              <span class="tp-title">{{ panelTitle }}</span>
              <button class="tp-close" @click="closeToolPanel">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
              </button>
            </div>
            <div class="tp-body">
              <!-- 打卡 -->
              <template v-if="panelTool === 'checkin'">
                <div v-if="checkinProjects.length" class="tp-list">
                  <div v-for="p in checkinProjects" :key="p.name" class="tp-item">
                    <div class="tp-item-info">
                      <span class="tp-item-name">{{ p.name }}</span>
                      <span class="tp-item-meta">{{ p.completed_days }} / {{ p.target_days }} 天</span>
                      <el-progress :percentage="Math.round((p.completed_days / p.target_days) * 100)" :stroke-width="5" :color="p.completed_days >= p.target_days ? '#67c23a' : '#409eff'" />
                    </div>
                    <el-button size="small" :type="p.last_checkin === today ? 'info' : 'success'" :disabled="p.last_checkin === today" @click="doCheckin(p.name)">{{ p.last_checkin === today ? '已打卡' : '打卡' }}</el-button>
                  </div>
                </div>
                <div v-else class="tp-empty">暂无打卡项目</div>
                <div class="tp-add">
                  <el-input v-model="newCheckinName" placeholder="项目名称" size="small" style="width:110px" />
                  <el-input-number v-model="newCheckinTarget" :min="1" :max="365" size="small" style="width:80px" />
                  <el-button size="small" type="primary" @click="addCheckin">添加</el-button>
                </div>
              </template>
              <!-- 倒计时 -->
              <template v-if="panelTool === 'countdown'">
                <div v-if="countdownEvents.length" class="tp-list">
                  <div v-for="e in countdownEvents" :key="e.id" class="tp-item">
                    <div class="tp-item-info">
                      <span class="tp-item-name">{{ e.name }}</span>
                      <span class="tp-item-meta">{{ getDaysUntil(e.target_date) >= 0 ? '还有 ' + getDaysUntil(e.target_date) + ' 天' : '已结束' }} · {{ e.target_date }}</span>
                    </div>
                    <button class="tp-del" @click="delCountdown(e.id)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button>
                  </div>
                </div>
                <div v-else class="tp-empty">暂无倒计时</div>
                <div class="tp-add">
                  <el-input v-model="newCountdownName" placeholder="事件名称" size="small" style="width:110px" />
                  <el-date-picker v-model="newCountdownDate" type="date" placeholder="日期" size="small" style="width:130px" value-format="YYYY-MM-DD" />
                  <el-button size="small" type="primary" @click="addCountdown">添加</el-button>
                </div>
              </template>
              <!-- 计时器 -->
              <template v-if="panelTool === 'timer'">
                <div v-if="activeTimerComp" class="tp-timer-active">
                  <div class="tp-timer-display">
                    <span class="tp-timer-name">{{ activeTimerComp.name }}</span>
                    <span class="tp-timer-time">{{ formatTimeComp(activeTimerComp.displaySeconds) }}</span>
                  </div>
                  <div class="tp-timer-ctls">
                    <el-button size="small" @click="pauseTimerComp">{{ activeTimerComp.paused ? '继续' : '暂停' }}</el-button>
                    <el-button size="small" type="danger" @click="stopTimerComp">取消</el-button>
                    <el-button v-if="activeTimerComp.type === 'stopwatch'" size="small" type="success" @click="completeStopwatchComp">完成</el-button>
                  </div>
                </div>
                <div v-if="timerTemplates.length" class="tp-list">
                  <div v-for="t in timerTemplates" :key="t.id" class="tp-item">
                    <div class="tp-item-info">
                      <span class="tp-item-name">{{ t.name }}</span>
                      <span class="tp-item-meta">{{ t.type === 'countdown' ? '⏳ 倒计时 ' + t.duration_minutes + '分钟' : '⏱️ 正向计时' }}</span>
                    </div>
                    <el-button size="small" type="primary" :disabled="!!activeTimerComp" @click="startTimerComp(t)">开始</el-button>
                  </div>
                </div>
                <div v-else class="tp-empty">暂无计时器模板</div>
                <div class="tp-add">
                  <el-input v-model="newTimerName" placeholder="任务名称" size="small" style="width:100px" />
                  <el-select v-model="newTimerType" size="small" style="width:90px">
                    <el-option label="倒计时" value="countdown" />
                    <el-option label="正向计时" value="stopwatch" />
                  </el-select>
                  <el-input-number v-if="newTimerType === 'countdown'" v-model="newTimerDuration" :min="1" :max="180" size="small" style="width:80px" />
                  <el-button size="small" type="primary" @click="addTimer">添加</el-button>
                </div>
              </template>
              <!-- 学习日志 -->
              <template v-if="panelTool === 'logs'">
                <div v-if="logs.length" class="tp-list">
                  <div v-for="(group, date) in groupedLogs" :key="date" class="tp-log-group">
                    <div class="tp-log-date">{{ date }}</div>
                    <div v-for="log in group" :key="log.id" class="tp-log-item">
                      <span class="tp-log-time">{{ log.time || '--:--' }}</span>
                      <span class="tp-log-keyword">{{ log.keyword }}</span>
                      <button class="tp-del" @click="delLog(log.id)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg></button>
                    </div>
                  </div>
                </div>
                <div v-else class="tp-empty">暂无学习日志</div>
              </template>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- ===== 对话区 ===== -->
    <div class="section-label" v-show="!isCollapsed"><span>对话</span></div>
    <div class="section-line" v-show="isCollapsed"></div>
    <div class="chat-mini-row" :class="{ collapsed: isCollapsed }">
      <button class="chat-mini-btn" @click="createNewSession" :title="isCollapsed ? '新对话' : ''">
        <div class="chat-mini-icon new">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>
        </div>
        <span v-if="!isCollapsed" class="chat-mini-label">新对话</span>
      </button>
      <button class="chat-mini-btn" @click="openChatHistory" :title="isCollapsed ? '历史对话' : ''">
        <div class="chat-mini-icon history">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
        </div>
        <span v-if="!isCollapsed" class="chat-mini-label">历史对话</span>
      </button>
    </div>
    </div><!-- /sidebar-scroll -->

    <!-- ===== 底部（固定）===== -->
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
import { useThemeStore } from '@/stores/theme'
import { useSessionStore } from '@/stores/session'
import { getUserStats, recordAction } from '@/api/career'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useToolsStore } from '@/stores/tools'
import { getLearningLogs, deleteLearningLog, addLearningLog } from '@/api/tools'
import { RANK_ICONS, RANK_COLORS, SUB_SYMBOLS } from '@/utils/constants'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const sessionStore = useSessionStore()
const toolsStore = useToolsStore()

// ===== 工具面板 =====
const panelTool = ref(null)
const panelTitle = computed(() => ({ checkin: '打卡', countdown: '倒计时', timer: '计时器', logs: '学习日志' }[panelTool.value] || ''))

function openToolPanel(tool) {
  if (panelTool.value === tool) { closeToolPanel(); return }
  panelTool.value = tool
  if (tool === 'logs') loadLogsPanel()
}
function closeToolPanel() { panelTool.value = null }

// 打卡
const today = new Date().toISOString().slice(0, 10)
const checkinProjects = computed(() => toolsStore.checkinProjects)
const newCheckinName = ref('')
const newCheckinTarget = ref(30)
function doCheckin(name) { toolsStore.doCheckin(name); toolsStore.saveCheckinData(authStore.user.id, toolsStore.checkinProjects); recordAction(authStore.user.id, 'checkin') }
function addCheckin() { if (!newCheckinName.value) return; toolsStore.addCheckinProject(newCheckinName.value, newCheckinTarget.value); toolsStore.saveCheckinData(authStore.user.id, toolsStore.checkinProjects); newCheckinName.value = '' }

// 倒计时
const countdownEvents = computed(() => toolsStore.countdownEvents)
const newCountdownName = ref('')
const newCountdownDate = ref('')
function getDaysUntil(d) { return toolsStore.getDaysUntil(d) }
function delCountdown(id) { toolsStore.deleteCountdownEvent(id); toolsStore.saveCountdownData(authStore.user.id, toolsStore.countdownEvents) }
function addCountdown() { if (!newCountdownName.value || !newCountdownDate.value) return; toolsStore.addCountdownEvent(newCountdownName.value, newCountdownDate.value); toolsStore.saveCountdownData(authStore.user.id, toolsStore.countdownEvents); newCountdownName.value = ''; newCountdownDate.value = '' }

// 计时器
const timerTemplates = computed(() => toolsStore.timerTemplates)
const activeTimerComp = ref(null)
let timerInt = null
const newTimerName = ref('')
const newTimerType = ref('countdown')
const newTimerDuration = ref(25)
function formatTimeComp(s) { return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}` }
function startTimerComp(t) { if (activeTimerComp.value) return; const total = t.type === 'countdown' ? t.duration_minutes * 60 : 0; activeTimerComp.value = { id: t.id, name: t.name, type: t.type, displaySeconds: total, paused: false }; timerInt = setInterval(() => { if (!activeTimerComp.value || activeTimerComp.value.paused) return; if (activeTimerComp.value.type === 'countdown') { activeTimerComp.value.displaySeconds--; if (activeTimerComp.value.displaySeconds <= 0) { clearInterval(timerInt); activeTimerComp.value.displaySeconds = 0 } } else { activeTimerComp.value.displaySeconds++ } }, 1000) }
function pauseTimerComp() { if (!activeTimerComp.value) return; activeTimerComp.value.paused = !activeTimerComp.value.paused }
function stopTimerComp() { clearInterval(timerInt); timerInt = null; activeTimerComp.value = null }
async function completeStopwatchComp() { if (!activeTimerComp.value || activeTimerComp.value.type !== 'stopwatch') return; const s = activeTimerComp.value.displaySeconds; const m = Math.floor(s / 60); const sec = s % 60; const str = m > 0 && sec > 0 ? `${m}分${sec}秒` : m > 0 ? `${m}分钟` : `${sec}秒`; if (s > 0) { await addLearningLog(authStore.user.id, `学习了「${activeTimerComp.value.name}」${str}`); loadLogsPanel() } stopTimerComp() }
function addTimer() { if (!newTimerName.value) return; toolsStore.addTimerTemplate(newTimerName.value, newTimerType.value, newTimerDuration.value); toolsStore.saveTimerData(authStore.user.id, toolsStore.timerTemplates); newTimerName.value = '' }

// 学习日志
const logs = ref([])
const logTimerRef = ref(null)
async function loadLogsPanel() { try { const data = await getLearningLogs(authStore.user.id); logs.value = (data.logs || []).sort((a, b) => (b.created_at || b.date || '').localeCompare(a.created_at || a.date || '')) } catch {} }
async function delLog(id) { try { await deleteLearningLog(authStore.user.id, id); loadLogsPanel() } catch {} }
const groupedLogs = computed(() => { const g = {}; const td = new Date().toISOString().slice(0, 10); const yd = new Date(Date.now() - 86400000).toISOString().slice(0, 10); logs.value.forEach(l => { const d = l.date || (l.created_at || '').slice(0, 10) || '未知'; const dd = d === td ? '今天' : d === yd ? '昨天' : d; if (!g[dd]) g[dd] = []; g[dd].push(l) }); return g })

const isCollapsed = inject('sidebarCollapsed', ref(false))
const chatPanelOpen = ref(false)
function openChatHistory() { chatPanelOpen.value = true }
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

const iconBase = '/assets/icons/sidebar/'
function iconPath(name) { return iconBase + name }

// 每个 App 图标的渐变色（半透明，不抢图标）
const iconColors = {
  home:            'linear-gradient(145deg, rgba(71,118,230,.55) 0%, rgba(142,84,233,.55) 100%)',
  profile:         'linear-gradient(145deg, rgba(240,147,251,.50) 0%, rgba(245,87,108,.50) 100%)',
  settings:        'linear-gradient(145deg, rgba(99,102,241,.55) 0%, rgba(168,85,247,.55) 100%)',
  'resource-lib':  'linear-gradient(145deg, rgba(30,60,114,.50) 0%, rgba(42,146,221,.55) 100%)',
  career:          'linear-gradient(145deg, rgba(17,153,142,.50) 0%, rgba(56,239,125,.50) 100%)',
  'profile-card':  'linear-gradient(145deg, rgba(123,44,191,.55) 0%, rgba(255,126,179,.50) 100%)',
  'subject-plan':  'linear-gradient(145deg, rgba(19,78,94,.50) 0%, rgba(113,178,128,.50) 100%)',
  community:       'linear-gradient(145deg, rgba(250,112,154,.50) 0%, rgba(254,225,64,.50) 100%)',
  qa:              'linear-gradient(145deg, rgba(26,41,128,.55) 0%, rgba(38,208,206,.55) 100%)',
  messages:        'linear-gradient(145deg, rgba(248,87,166,.50) 0%, rgba(255,88,88,.50) 100%)',
  'api-center':    'linear-gradient(145deg, rgba(72,52,212,.55) 0%, rgba(153,128,250,.55) 100%)',
  admin:           'linear-gradient(145deg, rgba(203,45,62,.55) 0%, rgba(242,153,74,.50) 100%)',
  checkin:         'linear-gradient(145deg, rgba(34,197,94,.55) 0%, rgba(20,184,166,.55) 100%)',
  countdown:       'linear-gradient(145deg, rgba(251,146,60,.55) 0%, rgba(250,204,21,.55) 100%)',
  timer:           'linear-gradient(145deg, rgba(168,85,247,.55) 0%, rgba(236,72,153,.55) 100%)',
  logs:            'linear-gradient(145deg, rgba(6,182,212,.55) 0%, rgba(59,130,246,.55) 100%)',
}
function iconStyle(name) {
  const c = iconColors[name] || 'linear-gradient(145deg, #94a3b8 0%, #64748b 40%, #475569 100%)'
  return { background: c }
}

const navItems = computed(() => {
  const items = [
    { to: '/',             icon: 'home.png',            label: '主界面',   key: 'home' },
    { to: '/profile',      icon: 'profile.png',         label: '个人中心', key: 'profile' },
    { to: '/settings',     icon: 'settings.png',        label: '设置',     key: 'settings' },
    { to: '/resource-lib', icon: 'resource-lib.png',    label: '资源库',   key: 'resource-lib' },
    { to: '/career',       icon: 'career.png',          label: '学程',     key: 'career',     badge: 'career' },
    { to: '/profile-card', icon: 'profile-card.png',    label: '个人画像', key: 'profile-card', highlight: true },
    { to: '/subject-plan', icon: 'subject-plan.png',    label: '学科计划', key: 'subject-plan' },
    { to: '/community',    icon: 'community.png',       label: '社区',     key: 'community',  badge: 'community' },
    { to: '/qa',           icon: 'qa.png',              label: 'Q&A',      key: 'qa' },
    { to: '/message',      icon: 'messages.png',        label: '消息中心', key: 'messages',   badge: 'total' },
    { to: '/api-center',   icon: 'api-center.png',      label: 'API管理',  key: 'api-center' },
  ]
  if (authStore.user?.role !== 'user') {
    items.push({ to: '/admin', icon: 'admin.png', label: '管理后台', key: 'admin', admin: true })
  }
  // 工具区
  return items.map(item => ({
    ...item,
    active: item.to === '/' ? (route.path === '/' || route.path === '/home') : route.path.startsWith(item.to),
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
    { icon: 'countdown.png', label: '倒计时',   key: 'countdown', tool: 'countdown' },
    { icon: 'timer.png',     label: '计时器',   key: 'timer',     tool: 'timer' },
    { icon: 'logs.png',      label: '学习日志', key: 'logs',      tool: 'logs' },
  ]
  return tools.map(t => ({
    ...t,
    active: panelTool.value === t.tool,
    badgeCount: 0,
  }))
})
const sessions = computed(() => sessionStore.sessions)
const currentSessionId = computed(() => sessionStore.currentSessionId)

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

function createNewSession() {
  sessionStore.createSession('新对话')
  ElMessage.success('新对话已创建')
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

  sessionStore.loadSessions()
  loadRankData()
  loadBadges()
  // 预加载工具数据
  toolsStore.loadCheckin(authStore.user?.id)
  toolsStore.loadCountdown(authStore.user?.id)
  toolsStore.loadTimer(authStore.user?.id)
  document.addEventListener('click', handleClickOutside)
  badgeTimer = setInterval(() => { loadBadges() }, 30000)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (badgeTimer) clearInterval(badgeTimer)
  if (timerInt) clearInterval(timerInt)
  if (logTimerRef.value) clearInterval(logTimerRef.value)
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
.sidebar-content.collapsed .chat-mini-label {
  opacity: 0;
  max-width: 0;
  overflow: hidden;
  white-space: nowrap;
  transition: opacity 0.3s ease, max-width 0.3s ease;
  pointer-events: none;
}
.sidebar-content.collapsed .user-section {
  justify-content: center;
  padding: 4px 0;
}
.sidebar-content.collapsed .app-icon {
  justify-content: center;
  padding: 4px 2px;
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
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: all 0.3s ease;
}
.user-section:hover {
  background: rgba(255,255,255,0.08);
}
[data-theme="dark"] .user-section {
  background: rgba(255,255,255,0.02);
}
[data-theme="dark"] .user-section:hover {
  background: rgba(255,255,255,0.06);
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
  color: #409EFF;
  background: rgba(64,158,255,0.10);
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
  background: rgba(255,255,255,0.04);
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
  background: rgba(255,255,255,0.10);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 4px 0;
  min-width: 90px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
  z-index: 100;
}
[data-theme="dark"] .status-dropdown {
  background: rgba(0,0,0,0.35);
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
  background: rgba(255,255,255,0.08);
  color: var(--text-primary);
  transform: translateX(2px);
}
.status-option-item.active {
  background: rgba(255,255,255,0.10);
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
  outline: 2px solid rgba(255,255,255,.18);
  outline-offset: 2px;
  border-radius: 13px;
}

/* ===== 图标容器 ===== */
.icon-anchor { position: relative; flex-shrink: 0; }
.icon-wrap {
  position: relative; width: 52px; height: 52px;
  border-radius: 13px; overflow: hidden;
  border: 1px solid rgba(255,255,255,.08);
  transition: all .25s ease;
}
/* 玻璃高光层 — 对角线光泽 */
.icon-wrap::after {
  content: ''; position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: linear-gradient(160deg,
    rgba(255,255,255,.18) 0%,
    rgba(255,255,255,.06) 35%,
    transparent 55%,
    rgba(0,0,0,.04) 100%
  );
  border-radius: inherit;
}
.nav-menu.list .icon-wrap { width: 40px; height: 40px; border-radius: 10px; }
.icon-img { width: 100%; height: 100%; object-fit: cover; display: block; }

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
  color: #475569; letter-spacing: .1em; text-transform: uppercase;
  opacity: 1;
  transition: opacity 0.3s ease, max-height 0.3s ease, padding 0.3s ease;
}
.section-line { height: 1px; margin: 4px 8px; background: rgba(255,255,255,.05); }

/* 标签 */
.icon-label {
  font-size: 10px; color: #94a3b8; text-align: center;
  line-height: 1.2; max-width: 64px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  opacity: 1;
  transition: opacity 0.3s ease;
}


/* ===== 对话迷你按钮 ===== */
.chat-mini-row { display: flex; gap: 6px; }
.chat-mini-row.collapsed { flex-direction: column; align-items: center; gap: 4px; }
.chat-mini-btn {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px;
  padding: 8px 4px; border-radius: 10px; border: 1px solid rgba(255,255,255,.04);
  background: rgba(255,255,255,.02); cursor: pointer;
  transition: all .2s ease; font-family: inherit;
}
.chat-mini-btn:hover { background: rgba(255,255,255,.06); border-color: rgba(255,255,255,.08); transform: scale(1.03); }
.chat-mini-btn:active { transform: scale(.95); }
.chat-mini-icon {
  width: 32px; height: 32px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s;
}
.chat-mini-icon svg { width: 16px; height: 16px; }
.chat-mini-icon.new { background: linear-gradient(145deg, rgba(34,197,94,.3), rgba(20,184,166,.3)); color: #4ade80; }
.chat-mini-icon.history { background: linear-gradient(145deg, rgba(99,102,241,.3), rgba(139,92,246,.3)); color: #a78bfa; }
.chat-mini-label { font-size: 10px; color: #94a3b8; opacity: 1; transition: opacity 0.3s ease; }
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

.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  border-radius: 10px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.03);
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
  background: rgba(255,255,255,0.10);
  transform: scale(1.08);
  color: var(--text-primary);
}
.theme-btn.active {
  background: rgba(255,255,255,0.12);
  box-shadow: 0 0 0 2px rgba(128,128,128,0.12);
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
  background: rgba(255,255,255,0.03);
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
  background: rgba(64,158,255,0.12);
  border-color: rgba(64,158,255,0.2);
  color: #409eff;
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
  color: #34d399;
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
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.06);
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-secondary);
  font-size: 14px;
  user-select: none;
}
.custom-select:hover {
  background: rgba(255,255,255,0.10);
  border-color: rgba(255,255,255,0.12);
  transform: translateY(-1px);
}
[data-theme="dark"] .custom-select {
  background: rgba(255,255,255,0.03);
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
  background: rgba(255,255,255,0.10);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  padding: 4px 0;
  box-shadow: 0 8px 32px rgba(0,0,0,0.15);
  z-index: 100;
  min-width: 160px;
}
[data-theme="dark"] .custom-select-dropdown {
  background: rgba(0,0,0,0.35);
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
  background: rgba(255,255,255,0.08);
  color: var(--text-primary);
  transform: translateX(2px);
}
.select-option.active {
  background: rgba(255,255,255,0.10);
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
  background: rgba(255,255,255,0.05) !important;
  border-color: rgba(255,255,255,0.06) !important;
  color: var(--text-primary) !important;
  border-radius: 10px !important;
  transition: all 0.3s ease !important;
}
.feedback-dialog :deep(.el-textarea__inner:hover) {
  border-color: rgba(255,255,255,0.15) !important;
}
[data-theme="dark"] .feedback-dialog :deep(.el-textarea__inner) {
  background: rgba(255,255,255,0.04) !important;
}
.feedback-dialog :deep(.el-textarea__inner:focus) {
  border-color: rgba(255,255,255,0.2) !important;
}
.feedback-dialog :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.05) !important;
  border-color: rgba(255,255,255,0.06) !important;
  border-radius: 10px !important;
  transition: all 0.3s ease !important;
}
.feedback-dialog :deep(.el-input__wrapper:hover) {
  border-color: rgba(255,255,255,0.15) !important;
}
[data-theme="dark"] .feedback-dialog :deep(.el-input__wrapper) {
  background: rgba(255,255,255,0.04) !important;
}
</style>

<style>
/* ===== 工具面板（右侧滑出毛玻璃）===== */
.tool-panel-overlay {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(0,0,0,.25);
  display: flex; justify-content: flex-end;
}
.tool-panel {
  width: 380px; max-width: 90vw; height: 100vh;
  background: linear-gradient(170deg, rgba(255,255,255,.06), rgba(255,255,255,.02));
  backdrop-filter: blur(28px) saturate(1.2);
  -webkit-backdrop-filter: blur(28px) saturate(1.2);
  border-left: 1px solid rgba(255,255,255,.06);
  display: flex; flex-direction: column;
  padding: 20px;
  overflow-y: auto;
}
.tp-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.tp-title { font-size: 18px; font-weight: 700; color: #e2e8f0; }
.tp-close {
  width: 32px; height: 32px; border-radius: 8px; border: 1px solid rgba(255,255,255,.06);
  background: rgba(255,255,255,.04); color: #94a3b8; cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all .2s;
}
.tp-close:hover { background: rgba(255,255,255,.1); color: #e2e8f0; }
.tp-close svg { width: 16px; height: 16px; }
.tp-body { flex: 1; overflow-y: auto; }
.tp-list { display: flex; flex-direction: column; gap: 8px; }
.tp-item {
  display: flex; align-items: center; gap: 12px; padding: 12px 14px;
  border-radius: 10px; background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.04);
}
.tp-item-info { flex: 1; min-width: 0; }
.tp-item-name { font-size: 13px; font-weight: 600; color: #e2e8f0; }
.tp-item-meta { font-size: 11px; color: #64748b; margin-top: 2px; display: block; }
.tp-empty { text-align: center; padding: 40px 0; color: #475569; font-size: 14px; }
.tp-add { display: flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; align-items: center; }
.tp-del {
  width: 24px; height: 24px; border: none; background: transparent; color: #475569;
  cursor: pointer; border-radius: 4px; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: all .2s;
}
.tp-del:hover { color: #ef4444; background: rgba(239,68,68,.08); }
.tp-del svg { width: 12px; height: 12px; }
.chat-session-item { cursor: pointer; transition: all .2s; }
.chat-session-item:hover { background: rgba(99,102,241,.06); border-color: rgba(99,102,241,.12); }
.chat-session-item.active { background: rgba(99,102,241,.08); border-color: rgba(99,102,241,.2); }

/* 计时器激活态 */
.tp-timer-active {
  padding: 16px; border-radius: 12px; margin-bottom: 16px;
  background: rgba(168,85,247,.08); border: 1px solid rgba(168,85,247,.15);
}
.tp-timer-display { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.tp-timer-name { font-size: 14px; color: #e2e8f0; }
.tp-timer-time { font-size: 28px; font-weight: 700; color: #a78bfa; font-variant-numeric: tabular-nums; }
.tp-timer-ctls { display: flex; gap: 6px; }

/* 日志 */
.tp-log-group { margin-bottom: 12px; }
.tp-log-date { font-size: 12px; font-weight: 600; color: #64748b; padding-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,.04); margin-bottom: 4px; }
.tp-log-item { display: flex; align-items: center; gap: 10px; padding: 6px 0; font-size: 13px; color: #cbd5e1; }
.tp-log-time { color: #64748b; font-size: 11px; flex-shrink: 0; width: 40px; }
.tp-log-keyword { flex: 1; }

/* 过渡动画 */
.panel-slide-enter-active { transition: all .3s ease; }
.panel-slide-leave-active { transition: all .25s ease; }
.panel-slide-enter-from .tool-panel { transform: translateX(100%); }
.panel-slide-enter-to .tool-panel { transform: translateX(0); }
.panel-slide-leave-from .tool-panel { transform: translateX(0); }
.panel-slide-leave-to .tool-panel { transform: translateX(100%); }
.panel-slide-enter-from { opacity: 0; }
.panel-slide-enter-to { opacity: 1; }
.panel-slide-leave-from { opacity: 1; }
.panel-slide-leave-to { opacity: 0; }

.feedback-dialog-wrapper {
  --el-dialog-bg-color: transparent;
}
.feedback-dialog-wrapper .el-overlay {
  background: transparent !important;
  backdrop-filter: none !important;
}
.feedback-dialog-wrapper .el-dialog {
  background: rgba(255,255,255,0.08) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 16px !important;
  box-shadow: 0 8px 40px rgba(0,0,0,0.2) !important;
}
[data-theme="dark"] .feedback-dialog-wrapper .el-dialog {
  background: rgba(0,0,0,0.3) !important;
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
  background: rgba(255,255,255,0.06) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  color: var(--text-secondary) !important;
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}
.feedback-dialog-wrapper .el-button:hover {
  background: rgba(255,255,255,0.12) !important;
  transform: translateY(-2px);
}
.feedback-dialog-wrapper .el-button--primary {
  background: rgba(64,158,255,0.15) !important;
  border-color: rgba(64,158,255,0.2) !important;
  color: #66b1ff !important;
}
.feedback-dialog-wrapper .el-button--primary:hover {
  background: rgba(64,158,255,0.25) !important;
}
</style>