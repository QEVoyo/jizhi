<template>
  <div class="mc-page">
    <div class="mc-container">
      <!-- ===== Header ===== -->
      <div class="mc-header">
        <div class="header-left">
          <button class="g-btn" @click="goBack">
            <el-icon><ArrowLeft /></el-icon> 返回
          </button>
          <img src="/logo.png" class="header-logo" />
          <h1>消息中心</h1>
          <span v-if="totalUnread" class="total-badge">{{ totalUnread }}</span>
        </div>
        <button class="g-btn icon-only" :class="{ active: showSettings }" @click="showSettings = !showSettings">
          <el-icon><Setting /></el-icon>
        </button>
      </div>

      <!-- ===== 设置面板 ===== -->
      <Transition name="slide">
        <div v-if="showSettings" class="settings-panel">
          <h3>消息设置</h3>
          <div class="settings-grid">
            <div v-for="s in settingItems" :key="s.key" class="set-row">
              <div class="set-info">
                <el-icon><component :is="s.icon" /></el-icon>
                <span>{{ s.label }}</span>
              </div>
              <label class="toggle">
                <input type="checkbox" v-model="settings[s.key]" @change="saveSettings" />
                <span class="toggle-track"><span class="toggle-thumb" /></span>
              </label>
            </div>
          </div>
          <div class="settings-extras">
            <div class="extra-pair">
              <span>每日推荐</span>
              <select v-model="settings.daily_rec_time" @change="saveSettings" class="g-select">
                <option value="07:00">07:00</option><option value="08:00">08:00</option><option value="09:00">09:00</option>
              </select>
            </div>
            <div class="extra-pair">
              <span>昨日总结</span>
              <select v-model="settings.daily_summary_time" @change="saveSettings" class="g-select">
                <option value="07:00">07:00</option><option value="08:00">08:00</option><option value="09:00">09:00</option>
              </select>
            </div>
          </div>
        </div>
      </Transition>

      <!-- ===== Tab 栏 ===== -->
      <div class="tab-bar">
        <button v-for="tab in tabs" :key="tab.key"
          class="tab-btn" :class="{ active: activeTab === tab.key }" @click="switchTab(tab.key)">
          <el-icon><component :is="tab.icon" /></el-icon>
          {{ tab.label }}
          <span v-if="tab.count" class="tab-badge">{{ tab.count > 99 ? '99+' : tab.count }}</span>
        </button>
      </div>

      <!-- ===== 操作栏 ===== -->
      <div class="action-bar">
        <button class="g-btn sm" @click="markAllCurrent">全部已读</button>
        <button class="g-btn sm danger" @click="clearCurrent">清空此分类</button>
      </div>

      <!-- ===== 消息列表 ===== -->
      <div class="mc-list">
        <div v-for="item in filteredList" :key="item.id"
          class="mc-card" :class="{ unread: unreadLike(item) }"
          @click="handleClick(item)">

          <!-- 头像区 -->
          <div class="mc-avatar-wrap">
            <div class="mc-avatar">
              <img v-if="item.sender_avatar" :src="item.sender_avatar" />
              <span v-else>{{ (item.sender_name || item.title)?.[0] || 'N' }}</span>
            </div>
            <span class="type-dot" :class="item.type || 'system'" />
          </div>

          <!-- 正文 -->
          <div class="mc-body">
            <div class="mc-top">
              <span class="mc-name">{{ item.sender_name || item.title }}</span>
              <span class="mc-time">{{ formatTime(item.latest_time || item.created_at) }}</span>
            </div>
            <div class="mc-preview">{{ item.latest_content || item.content }}</div>

            <!-- 公告展开内容 -->
            <div v-if="item.type === 'announcement' && expandedAnns.has(item.id)" class="announce-detail">
              <div v-if="item.image_url" class="announce-img">
                <img :src="item.image_url" />
              </div>
              <div class="announce-text">{{ item.content }}</div>
            </div>

            <!-- 条数 / 摘要 -->
            <div class="mc-extra" v-if="item.message_count > 1 || item.summary || item.action_label">
              <span v-if="item.message_count > 1" class="count-tag">{{ item.message_count }} 条消息</span>
              <span v-if="item.summary" class="summary-text">{{ item.summary }}</span>
              <button v-if="item.action_label" class="g-btn primary xs" @click.stop="handleAction(item)">
                {{ item.action_label }}
              </button>
            </div>
          </div>

          <el-icon class="mc-arrow"><ArrowRight /></el-icon>
        </div>

        <!-- 空态 -->
        <div v-if="loading" class="mc-state"><el-icon class="spin"><Loading /></el-icon> 加载中...</div>
        <div v-else-if="!filteredList.length" class="mc-state">
          <el-icon :size="36"><Bell /></el-icon>
          <p>{{ activeTab === 'all' ? '暂无消息' : '暂无' + typeName(activeTab) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  ArrowLeft, ArrowRight, Setting, Bell, ChatDotRound,
  User, Trophy, Clock, DataAnalysis, Sunrise, Notification, Loading
} from '@element-plus/icons-vue'
import {
  getUnreadSummary, markAllRead, markMessagesRead,
  clearMessages, getNotificationSettings, updateNotificationSettings
} from '@/api/community'

const router = useRouter()
const authStore = useAuthStore()

// ===== 状态 =====
const showSettings = ref(false)
const loading = ref(false)
const activeTab = ref('all')
const summary = ref([])
const totalUnread = ref(0)
const savingSettings = ref(false)

// ===== 设置 =====
const settings = ref({
  chat_enabled: true, social_enabled: true, learning_enabled: true,
  plan_reminder_enabled: true, evaluation_enabled: true,
  daily_rec_enabled: true, daily_summary_enabled: true, system_enabled: true,
  daily_rec_time: '08:00', daily_summary_time: '07:00', retention_days: 30
})

const settingItems = [
  { key: 'chat_enabled', label: '好友消息', icon: ChatDotRound },
  { key: 'social_enabled', label: '社区互动', icon: User },
  { key: 'learning_enabled', label: '学程动态', icon: Trophy },
  { key: 'plan_reminder_enabled', label: '计划提醒', icon: Clock },
  { key: 'evaluation_enabled', label: '评估报告', icon: DataAnalysis },
  { key: 'daily_rec_enabled', label: '每日推荐', icon: Sunrise },
  { key: 'daily_summary_enabled', label: '昨日总结', icon: Notification },
  { key: 'system_enabled', label: '系统消息', icon: Bell },
]

const typeNames = {
  chat: '好友消息', social: '社区互动', learning: '学程动态',
  plan_reminder: '计划提醒', evaluation: '评估报告',
  daily_rec: '每日推荐', daily_summary: '昨日总结', system: '系统消息',
  announcement: '公告'
}
function typeName(key) { return typeNames[key] || key }

// ===== Tab 列表 =====
const tabs = computed(() => {
  const counts = {}
  summary.value.forEach(m => { counts[m.type] = (counts[m.type] || 0) + (m.message_count || 0) })
  const allCount = Object.values(counts).reduce((a, b) => a + b, 0)
  return [
    { key: 'all', icon: Bell, label: '全部', count: allCount },
    { key: 'chat', icon: ChatDotRound, label: '好友消息', count: counts.chat || 0 },
    { key: 'social', icon: User, label: '社区互动', count: counts.social || 0 },
    { key: 'learning', icon: Trophy, label: '学程动态', count: counts.learning || 0 },
    { key: 'plan_reminder', icon: Clock, label: '计划提醒', count: counts.plan_reminder || 0 },
    { key: 'evaluation', icon: DataAnalysis, label: '评估报告', count: counts.evaluation || 0 },
    { key: 'daily_rec', icon: Sunrise, label: '每日推荐', count: counts.daily_rec || 0 },
    { key: 'daily_summary', icon: Notification, label: '昨日总结', count: counts.daily_summary || 0 },
    { key: 'system', icon: Bell, label: '系统消息', count: counts.system || 0 },
    { key: 'announcement', icon: Bell, label: '公告', count: announcementCount.value },
  ]
})

const announcementItems = computed(() => announcements.value.map(a => ({
  id: a.id, type: 'announcement', title: a.title, content: a.content,
  sender_name: '系统公告', sender_avatar: '/logo.png', created_at: a.created_at,
  is_read: true, image_url: a.image_url,
})))

// ===== 列表 =====
const filteredList = computed(() => {
  if (activeTab.value === 'announcement') return announcementItems.value
  if (activeTab.value === 'all') {
    return [...announcementItems.value, ...summary.value]
      .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
  }
  return summary.value.filter(m => m.type === activeTab.value)
})

function unreadLike(item) {
  return (item.message_count || 0) > 0 || item.is_read === false
}

// 公告
const announcements = ref([])
const expandedAnns = ref(new Set())
const announcementCount = computed(() => announcements.value.length)

async function loadAnnouncements() {
  try {
    const base = import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'
    const res = await fetch(`${base}/admin/announcements/active`)
    if (res.ok) announcements.value = await res.json()
  } catch { announcements.value = [] }
}

// ===== 加载 =====
async function loadData() {
  loading.value = true
  try {
    const res = await getUnreadSummary(authStore.user.id)
    summary.value = res.summary || []
    totalUnread.value = summary.value.reduce((s, m) => s + (m.message_count || 0), 0)
  } catch (e) { console.error('加载消息失败:', e) }
  finally { loading.value = false }
}

async function loadSettings() {
  try {
    const res = await getNotificationSettings(authStore.user.id)
    if (res.user_id) Object.assign(settings.value, res)
  } catch (e) { /* ignore */ }
}

// ===== 操作 =====
function switchTab(key) { activeTab.value = key; if (key === 'announcement') loadAnnouncements() }

async function markAllCurrent() {
  await markAllRead(authStore.user.id, activeTab.value === 'all' ? 'all' : activeTab.value)
  loadData()
}

async function clearCurrent() {
  await clearMessages(authStore.user.id, activeTab.value === 'all' ? 'all' : activeTab.value)
  loadData()
}

async function handleClick(item) {
  if (item.type === 'announcement') {
    const s = expandedAnns.value
    s.has(item.id) ? s.delete(item.id) : s.add(item.id)
    expandedAnns.value = new Set(s)  // 触发响应式
    return
  }
  // 标记已读：chat 按 sender，其他按类型
  if (item.type === 'chat' && item.sender_id) {
    markMessagesRead(authStore.user.id, item.sender_id).catch(() => {})
  } else if (item.type && item.id) {
    markAllRead(authStore.user.id, item.type).catch(() => {})
  }
  if (item.message_count !== undefined) item.message_count = 0
  totalUnread.value = summary.value.reduce((s, m) => s + (m.message_count || 0), 0)

  // 导航到详情
  if (item.type === 'chat' && item.sender_id) {
    router.push(`/community/chat/${item.sender_id}`)
    return
  }
  if (item.link) { router.push(item.link); return }
  if (item.action_link) { router.push(item.action_link); return }
}

function handleAction(item) {
  if (item.action_link) router.push(item.action_link)
}

async function saveSettings() {
  if (savingSettings.value) return
  savingSettings.value = true
  try {
    await updateNotificationSettings({ user_id: authStore.user.id, data: settings.value })
  } catch (e) { /* ignore */ }
  savingSettings.value = false
}

function goBack() { router.push('/home') }

function formatTime(time) {
  if (!time) return ''
  const dt = new Date(time.endsWith('Z') || time.includes('+') ? time : time + 'Z')
  if (isNaN(dt.getTime())) return ''
  const now = new Date(), diff = Math.floor((now - dt) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 604800) return Math.floor(diff / 86400) + '天前'
  return dt.toLocaleDateString('zh-CN')
}

// ===== 轮询 =====
let poll = null
onMounted(() => { loadData(); loadSettings(); loadAnnouncements(); poll = setInterval(loadData, 30000) })
onUnmounted(() => clearInterval(poll))
</script>

<style scoped>
.mc-page { min-height: 100vh; display: flex; justify-content: center; padding: 28px 20px; }

.mc-container {
  max-width: 780px; width: 100%; padding: 24px 30px;
  border-radius: 18px;
  background: rgba(255,255,255,0.04); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 8px 32px rgba(0,0,0,0.06);
  max-height: 92vh; overflow-y: auto; display: flex; flex-direction: column;
}
.mc-container::-webkit-scrollbar { width: 4px; }
.mc-container::-webkit-scrollbar-thumb { background: rgba(128,128,128,0.2); border-radius: 2px; }

/* Header */
.mc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.header-left { display: flex; align-items: center; gap: 10px; }
.header-logo { width: 28px; height: 28px; border-radius: 6px; }
.mc-header h1 { font-size: 20px; color: var(--text-primary); margin: 0; font-weight: 700; }
.total-badge { background: rgba(239,68,68,0.15); color: #ef4444; font-size: 12px; font-weight: 700; padding: 1px 10px; border-radius: 12px; }

/* 按钮系统 */
.g-btn { display: inline-flex; align-items: center; gap: 5px; padding: 7px 16px; font-size: 13px; font-weight: 500; color: var(--text-secondary); background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 10px; cursor: pointer; transition: all 0.25s ease; font-family: inherit; }
.g-btn:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.12); transform: translateY(-1px); }
.g-btn:active { transform: scale(0.97); }
.g-btn.sm { padding: 5px 12px; font-size: 12px; }
.g-btn.xs { padding: 3px 10px; font-size: 11px; }
.g-btn.icon-only { padding: 7px 10px; }
.g-btn.icon-only.active { background: rgba(64,158,255,0.12); border-color: rgba(64,158,255,0.2); color: #409eff; }
.g-btn.primary { color: #409eff; background: rgba(64,158,255,0.08); border-color: rgba(64,158,255,0.1); }
.g-btn.primary:hover { background: rgba(64,158,255,0.15); }
.g-btn.danger { color: #f56c6c; }
.g-btn.danger:hover { background: rgba(245,108,108,0.08); border-color: rgba(245,108,108,0.15); }
.g-btn .el-icon { font-size: 15px; }

/* 设置面板 */
.settings-panel { margin-bottom: 16px; padding: 20px 24px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 14px; }
.slide-enter-active, .slide-leave-active { transition: all 0.3s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; max-height: 0; padding-top: 0; padding-bottom: 0; margin-bottom: 0; overflow: hidden; }
.settings-panel h3 { font-size: 14px; font-weight: 600; color: var(--text-primary); margin: 0 0 14px; }
.settings-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 8px; margin-bottom: 14px; }
.set-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; border-radius: 8px; background: rgba(255,255,255,0.02); }
.set-info { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-secondary); }
.settings-extras { display: flex; gap: 20px; flex-wrap: wrap; }
.extra-pair { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-secondary); }
.g-select { padding: 5px 10px; border-radius: 8px; font-size: 13px; color: var(--text-primary); background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); cursor: pointer; outline: none; font-family: inherit; }
.g-select:focus { border-color: rgba(64,158,255,0.2); }

/* Toggle */
.toggle { position: relative; display: inline-block; cursor: pointer; }
.toggle input { display: none; }
.toggle-track { display: block; width: 40px; height: 22px; border-radius: 11px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.08); transition: all 0.25s ease; position: relative; }
.toggle input:checked + .toggle-track { background: rgba(64,158,255,0.3); border-color: rgba(64,158,255,0.4); }
.toggle-thumb { position: absolute; top: 2px; left: 2px; width: 16px; height: 16px; border-radius: 50%; background: var(--text-muted); transition: all 0.25s ease; }
.toggle input:checked + .toggle-track .toggle-thumb { left: 20px; background: #409eff; box-shadow: 0 0 8px rgba(64,158,255,0.4); }

/* Tab */
.tab-bar { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 10px; }
.tab-btn { display: flex; align-items: center; gap: 5px; padding: 6px 14px; font-size: 13px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05); background: rgba(255,255,255,0.02); color: var(--text-secondary); cursor: pointer; transition: all 0.25s ease; font-family: inherit; }
.tab-btn:hover { background: rgba(255,255,255,0.06); }
.tab-btn.active { background: rgba(64,158,255,0.1); border-color: rgba(64,158,255,0.2); color: #409eff; }
.tab-badge { background: rgba(128,128,128,0.12); color: var(--text-secondary); font-size: 10px; padding: 0 7px; border-radius: 8px; font-weight: 600; line-height: 18px; }

/* Action bar */
.action-bar { display: flex; gap: 8px; padding: 6px 0 10px; border-bottom: 1px solid rgba(255,255,255,0.04); margin-bottom: 10px; }

/* 消息列表 */
.mc-list { flex: 1; display: flex; flex-direction: column; gap: 6px; }
.mc-card { display: flex; align-items: flex-start; gap: 12px; padding: 14px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.04); background: rgba(255,255,255,0.02); cursor: pointer; transition: all 0.25s ease; }
.mc-card:hover { background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.1); transform: translateX(3px); }
.mc-card.unread { border-left: 3px solid rgba(64,158,255,0.35); background: rgba(64,158,255,0.03); }

.mc-avatar-wrap { position: relative; flex-shrink: 0; }
.mc-avatar { width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.06); border: 2px solid rgba(255,255,255,0.08); overflow: hidden; font-size: 18px; font-weight: 600; color: var(--text-secondary); }
.mc-avatar img { width: 100%; height: 100%; object-fit: cover; }
.type-dot { position: absolute; bottom: -2px; right: -2px; width: 10px; height: 10px; border-radius: 50%; border: 2px solid var(--bg-color); background: #909399; }
.type-dot.chat { background: #409eff; }
.type-dot.social { background: #e6a23c; }
.type-dot.learning { background: #67c23a; }
.type-dot.plan_reminder { background: #f56c6c; }
.type-dot.evaluation { background: #8b5cf6; }
.type-dot.daily_rec { background: #10b981; }
.type-dot.daily_summary { background: #f59e0b; }

.mc-body { flex: 1; min-width: 0; }
.mc-top { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.mc-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.mc-time { font-size: 11px; color: var(--text-muted); flex-shrink: 0; }
.mc-preview { font-size: 13px; color: var(--text-secondary); margin-top: 3px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.5; }
.mc-extra { display: flex; align-items: center; gap: 10px; margin-top: 8px; flex-wrap: wrap; }
.count-tag { font-size: 12px; color: #409eff; background: rgba(64,158,255,0.1); padding: 2px 10px; border-radius: 8px; font-weight: 600; }
.summary-text { font-size: 12px; color: var(--text-muted); }

.mc-arrow { flex-shrink: 0; color: var(--text-muted); opacity: 0.3; margin-top: 10px; }
.mc-card:hover .mc-arrow { opacity: 1; }

.mc-state { text-align: center; padding: 40px 20px; color: var(--text-muted); }
.mc-state p { font-size: 15px; color: var(--text-secondary); margin: 6px 0; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.announce-detail {
  margin-top: 10px; padding: 12px; border-radius: 10px;
  background: rgba(255,255,255,.03); border-left: 3px solid rgba(245,158,11,.3);
  animation: fadeIn .2s ease;
}
@keyframes fadeIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
.announce-img img { max-width: 100%; max-height: 200px; border-radius: 8px; margin-bottom: 8px; }
.announce-text { font-size: 13px; color: #cbd5e1; line-height: 1.7; white-space: pre-wrap; }

@media (max-width: 640px) {
  .mc-page { padding: 10px 8px; }
  .mc-container { padding: 14px 12px; max-height: 96vh; }
  .mc-header h1 { font-size: 17px; }
  .settings-grid { grid-template-columns: repeat(2, 1fr); }
  .settings-extras { flex-direction: column; gap: 8px; }
  .tab-btn { padding: 5px 10px; font-size: 12px; }
  .mc-card { padding: 10px 12px; }
}
</style>
