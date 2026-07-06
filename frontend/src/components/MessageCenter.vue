<template>
  <div class="message-page">
    <div class="message-container">
      <!-- ===== 顶部 ===== -->
      <div class="message-header">
        <div class="header-left">
          <el-button text class="back-btn" @click="goBack">
            <i class="fas fa-arrow-left"></i> 返回
          </el-button>
          <img src="/logo.png" alt="基智" class="header-logo" />
          <h1>消息中心</h1>
          <span v-if="totalUnread > 0" class="header-badge">{{ totalUnread }}</span>
        </div>
        <el-button text class="settings-btn" @click="showSettings = true">
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>

      <el-divider />

      <!-- ===== 分类 Tab 栏 ===== -->
      <div class="tab-section">
        <button
          v-for="tab in tabList"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @click="switchTab(tab.key)"
        >
          <el-icon><component :is="tab.icon" /></el-icon>
          {{ tab.label }}
          <span v-if="tab.count > 0" class="tab-badge">{{ tab.count }}</span>
        </button>
      </div>

      <!-- ===== 批量操作栏 ===== -->
      <div class="action-bar">
        <el-checkbox v-model="selectAll" @change="toggleSelectAll">
          全选
        </el-checkbox>
        <div class="action-buttons">
          <el-button size="small" text @click="markAllRead">
            <el-icon><Check /></el-icon> 全部已读
          </el-button>
          <el-button size="small" text @click="deleteSelected">
            <el-icon><Delete /></el-icon> 删除选中
          </el-button>
          <el-button size="small" text @click="clearAll">
            <el-icon><Remove /></el-icon> 清空全部
          </el-button>
        </div>
      </div>

      <!-- ===== 消息列表 ===== -->
      <div class="message-list">
        <div
          v-for="item in filteredMessages"
          :key="item.id"
          class="message-card"
          :class="{ unread: item.message_count > 0 }"
          @click="handleMessageClick(item)"
        >
          <el-checkbox
            v-model="selectedIds"
            :value="item.id"
            @click.stop
            class="message-checkbox"
          />
          <div class="message-icon">
            <el-avatar :size="40" :src="item.sender_avatar || ''" class="msg-avatar">
              {{ item.sender_name?.[0] || 'U' }}
            </el-avatar>
            <span v-if="item.type" class="msg-type-tag" :class="item.type">
              {{ typeLabels[item.type] }}
            </span>
          </div>
          <div class="message-body">
            <div class="message-top">
              <span class="message-title">{{ item.sender_name }}</span>
              <span class="message-time">{{ formatTime(item.latest_time) }}</span>
            </div>
            <div class="message-content">
              {{ item.latest_content || '发来了一条消息' }}
            </div>
            <div class="message-count-badge" v-if="item.message_count > 1">
              {{ item.message_count }} 条消息
            </div>
          </div>
          <div v-if="item.message_count > 0" class="unread-dot"></div>
        </div>

        <div v-if="loading" class="loading-state">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>

        <div v-else-if="!filteredMessages.length" class="empty-state">
          <el-icon :size="48"><Bell /></el-icon>
          <p>{{ emptyText }}</p>
          <span>当你收到新消息时，会在这里显示</span>
        </div>
      </div>
    </div>

    <!-- ===== 设置弹窗 ===== -->
    <el-dialog
      v-model="showSettings"
      title="消息设置"
      width="520px"
      class="settings-dialog"
      destroy-on-close
    >
      <div class="settings-content">
        <div class="setting-group">
          <div class="setting-label">通知偏好</div>
          <div class="setting-items">
            <el-checkbox v-model="prefs.system">系统通知</el-checkbox>
            <el-checkbox v-model="prefs.learning">学习动态</el-checkbox>
            <el-checkbox v-model="prefs.report">学情报告</el-checkbox>
            <el-checkbox v-model="prefs.social">社交互动</el-checkbox>
          </div>
        </div>
        <div class="setting-group">
          <div class="setting-label">推送时间</div>
          <div class="setting-row">
            <span>日报推送时间</span>
            <el-select v-model="prefs.dailyTime" size="small">
              <el-option label="08:00" value="08:00" />
              <el-option label="12:00" value="12:00" />
              <el-option label="18:00" value="18:00" />
              <el-option label="20:00" value="20:00" />
            </el-select>
          </div>
          <div class="setting-row">
            <span>打卡提醒时间</span>
            <el-select v-model="prefs.checkinTime" size="small">
              <el-option label="08:00" value="08:00" />
              <el-option label="09:00" value="09:00" />
              <el-option label="10:00" value="10:00" />
              <el-option label="12:00" value="12:00" />
            </el-select>
          </div>
        </div>
        <div class="setting-group">
          <div class="setting-label">消息保留</div>
          <div class="setting-row">
            <span>保留时长</span>
            <el-select v-model="prefs.retention" size="small">
              <el-option label="7 天" value="7" />
              <el-option label="30 天" value="30" />
              <el-option label="90 天" value="90" />
              <el-option label="永久" value="forever" />
            </el-select>
          </div>
          <el-checkbox v-model="prefs.autoArchive">30天后自动归档</el-checkbox>
        </div>
      </div>
      <template #footer>
        <el-button @click="showSettings = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting,
  Bell,
  Check,
  Delete,
  Remove,
  Trophy,
  User,
  Promotion,
  ChatDotRound
} from '@element-plus/icons-vue'
import { getUnreadSummary, markMessagesRead } from '@/api/community'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('all')
const selectedIds = ref([])
const selectAll = ref(false)
const loading = ref(false)
const showSettings = ref(false)

const summary = ref([])
const totalUnread = ref(0)

const prefs = ref({
  system: true,
  learning: true,
  report: true,
  social: true,
  dailyTime: '18:00',
  checkinTime: '09:00',
  retention: '30',
  autoArchive: true
})

// ===== 类型标签映射 =====
const typeLabels = {
  chat: '好友消息',
  social: '社区互动',
  learning: '学习动态',
  system: '官方消息'
}

const typeIcons = {
  chat: ChatDotRound,
  social: User,
  learning: Trophy,
  system: Promotion
}

// ===== Tab 列表（5个分类） =====
const tabList = computed(() => {
  const allCount = summary.value.reduce((sum, m) => sum + (m.message_count || 0), 0)
  const chatCount = summary.value.filter(m => m.type === 'chat').reduce((sum, m) => sum + (m.message_count || 0), 0)
  const socialCount = summary.value.filter(m => m.type === 'social').reduce((sum, m) => sum + (m.message_count || 0), 0)
  const learningCount = summary.value.filter(m => m.type === 'learning').reduce((sum, m) => sum + (m.message_count || 0), 0)
  const systemCount = summary.value.filter(m => m.type === 'system').reduce((sum, m) => sum + (m.message_count || 0), 0)

  return [
    { key: 'all', icon: Bell, label: '全部', count: allCount },
    { key: 'chat', icon: ChatDotRound, label: '好友消息', count: chatCount },
    { key: 'social', icon: User, label: '社区互动', count: socialCount },
    { key: 'learning', icon: Trophy, label: '学习动态', count: learningCount },
    { key: 'system', icon: Promotion, label: '官方消息', count: systemCount }
  ]
})

// ===== 筛选消息 =====
const filteredMessages = computed(() => {
  let result = summary.value
  if (activeTab.value === 'all') return result
  return result.filter(m => m.type === activeTab.value)
})

// ===== 空状态文案 =====
const emptyText = computed(() => {
  if (activeTab.value === 'all') return '暂无消息'
  const label = typeLabels[activeTab.value] || activeTab.value
  return `暂无${label}`
})

function formatTime(time) {
  if (!time) return ''
  let utcStr = time
  if (!time.endsWith('Z') && !time.includes('+')) {
    utcStr = time + 'Z'
  }
  const dt = new Date(utcStr)
  if (isNaN(dt.getTime())) return ''
  const now = new Date()
  const diff = Math.floor((now - dt) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 604800) return Math.floor(diff / 86400) + '天前'
  return dt.toLocaleDateString('zh-CN')
}

function goBack() {
  router.push('/home')
}

function switchTab(key) {
  activeTab.value = key
  selectedIds.value = []
  selectAll.value = false
}

function toggleSelectAll(val) {
  if (val) {
    selectedIds.value = filteredMessages.value.map(m => m.id)
  } else {
    selectedIds.value = []
  }
}

async function loadData() {
  loading.value = true
  try {
    const res = await getUnreadSummary(authStore.user.id)
    summary.value = res.summary || []
    totalUnread.value = summary.value.reduce((sum, m) => sum + (m.message_count || 0), 0)
  } catch (error) {
    console.error('加载消息失败:', error)
    ElMessage.error('加载消息失败')
  } finally {
    loading.value = false
  }
}

async function handleMessageClick(item) {
  if (item.type === 'chat' && item.message_count > 0) {
    try {
      await markMessagesRead(authStore.user.id, item.sender_id)
      item.message_count = 0
      totalUnread.value = summary.value.reduce((sum, m) => sum + (m.message_count || 0), 0)
    } catch (error) {
      console.error('标记已读失败:', error)
    }
    router.push(`/community/chat/${item.sender_id}`)
    return
  }

  if (item.link) {
    router.push(item.link)
  }
}

function markAllRead() {
  ElMessageBox.confirm('确定要标记所有消息为已读吗？', '确认操作')
    .then(async () => {
      const targets = selectedIds.value.length > 0 ? selectedIds.value : summary.value.map(m => m.id)
      for (const id of targets) {
        const item = summary.value.find(m => m.id === id)
        if (item && item.message_count > 0) {
          try {
            if (item.type === 'chat' && item.sender_id) {
              await markMessagesRead(authStore.user.id, item.sender_id)
            }
            item.message_count = 0
          } catch (error) {
            console.error('标记已读失败:', error)
          }
        }
      }
      totalUnread.value = summary.value.reduce((sum, m) => sum + (m.message_count || 0), 0)
      selectedIds.value = []
      selectAll.value = false
      ElMessage.success('已标记为已读')
    })
    .catch(() => {})
}

function deleteSelected() {
  if (!selectedIds.value.length) {
    ElMessage.warning('请先选择消息')
    return
  }
  ElMessageBox.confirm('确定要删除选中的消息记录吗？', '确认删除')
    .then(() => {
      const toRemove = new Set(selectedIds.value)
      summary.value = summary.value.filter(m => !toRemove.has(m.id))
      selectedIds.value = []
      selectAll.value = false
      totalUnread.value = summary.value.reduce((sum, m) => sum + (m.message_count || 0), 0)
      ElMessage.success('删除成功')
    })
    .catch(() => {})
}

function clearAll() {
  ElMessageBox.confirm('确定要清空所有消息记录吗？', '确认清空')
    .then(() => {
      summary.value = []
      totalUnread.value = 0
      ElMessage.success('已清空')
    })
    .catch(() => {})
}

function saveSettings() {
  showSettings.value = false
  ElMessage.success('设置已保存')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.message-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding: 30px 20px;
  background: transparent;
}

.message-container {
  max-width: 820px;
  width: 100%;
  padding: 28px 36px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  max-height: 90vh;
  overflow-y: auto;
}
.message-container::-webkit-scrollbar { width: 4px; }
.message-container::-webkit-scrollbar-thumb { background: rgba(128,128,128,0.2); border-radius: 2px; }

.message-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.back-btn {
  color: var(--text-secondary) !important;
  font-size: 15px;
  padding: 4px 8px;
  transition: all 0.3s ease !important;
}
.back-btn:hover {
  color: var(--text-primary) !important;
  transform: translateX(-2px);
  background: rgba(255,255,255,0.06);
}
.header-logo { width: 28px; height: 28px; object-fit: contain; }
.message-header h1 { font-size: 22px; color: var(--text-primary); margin: 0; }
.header-badge {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  font-size: 12px;
  font-weight: 600;
  padding: 1px 10px;
  border-radius: 12px;
  line-height: 20px;
}

.settings-btn {
  color: var(--text-secondary) !important;
  font-size: 20px;
  transition: all 0.3s ease !important;
}
.settings-btn:hover {
  color: var(--text-primary) !important;
  transform: rotate(60deg);
}
.el-divider { margin: 12px 0; }

.tab-section {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.02);
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
}
.tab-item:hover {
  background: rgba(255,255,255,0.06);
  transform: translateY(-2px);
  border-color: rgba(255,255,255,0.12);
}
.tab-item.active {
  background: rgba(64,158,255,0.10);
  border-color: rgba(64,158,255,0.2);
  color: #409eff;
}
.tab-item .el-icon { font-size: 16px; }
.tab-badge {
  background: rgba(128,128,128,0.15);
  color: var(--text-secondary);
  font-size: 11px;
  padding: 0 8px;
  border-radius: 10px;
  margin-left: 2px;
}

.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 4px 10px 4px;
  flex-wrap: wrap;
  gap: 6px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.action-buttons { display: flex; gap: 4px; }
.action-buttons .el-button {
  color: var(--text-secondary) !important;
  font-size: 13px;
  transition: all 0.3s ease !important;
}
.action-buttons .el-button:hover {
  color: var(--text-primary) !important;
  transform: translateY(-2px);
}
.action-buttons .el-button .el-icon { font-size: 14px; }

.message-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 10px;
}

.message-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.04);
  background: rgba(255,255,255,0.02);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}
.message-card:hover {
  background: rgba(255,255,255,0.05);
  border-color: rgba(255,255,255,0.08);
  transform: translateX(4px);
}
.message-card.unread { border-left: 3px solid rgba(64,158,255,0.4); }

.message-checkbox { margin-top: 2px; flex-shrink: 0; }

.message-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  position: relative;
}
.msg-avatar {
  width: 40px !important;
  height: 40px !important;
  border: 2px solid rgba(255,255,255,0.06);
}
.msg-type-tag {
  position: absolute;
  bottom: -4px;
  right: -4px;
  font-size: 9px;
  padding: 1px 4px;
  border-radius: 6px;
  color: #fff;
  line-height: 1.4;
}
.msg-type-tag.chat { background: #409eff; }
.msg-type-tag.social { background: #e6a23c; }
.msg-type-tag.learning { background: #67c23a; }
.msg-type-tag.system { background: #909399; }

.message-body { flex: 1; min-width: 0; }
.message-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}
.message-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.message-time { font-size: 12px; color: var(--text-muted); flex-shrink: 0; }
.message-content {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 2px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}
.message-count-badge {
  display: inline-block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted);
  background: rgba(255,255,255,0.04);
  padding: 0 10px;
  border-radius: 10px;
  line-height: 20px;
}
.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(64,158,255,0.6);
  flex-shrink: 0;
  margin-top: 8px;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}
.empty-state .el-icon { color: var(--text-muted); opacity: 0.3; margin-bottom: 12px; }
.empty-state p { font-size: 16px; color: var(--text-secondary); margin: 4px 0; }
.empty-state span { font-size: 14px; opacity: 0.6; }

.settings-content { display: flex; flex-direction: column; gap: 18px; }
.setting-group { display: flex; flex-direction: column; gap: 8px; }
.setting-label { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.setting-items { display: flex; gap: 16px; flex-wrap: wrap; }
.setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}
.setting-row span { font-size: 14px; color: var(--text-secondary); }
.setting-row .el-select { width: 120px; }

@media (max-width: 640px) {
  .message-page { padding: 12px 10px; }
  .message-container { padding: 16px 14px; max-height: 95vh; }
  .message-header h1 { font-size: 18px; }
  .header-logo { width: 24px; height: 24px; }
  .tab-section { gap: 4px; }
  .tab-item { font-size: 12px; padding: 4px 10px; }
  .tab-item .el-icon { font-size: 14px; }
  .action-bar { flex-direction: column; align-items: stretch; gap: 6px; }
  .action-buttons { flex-wrap: wrap; }
  .message-card { padding: 10px 12px; flex-wrap: wrap; }
  .message-top { flex-wrap: wrap; }
  .message-title { font-size: 14px; }
  .settings-content { gap: 14px; }
  .setting-items { gap: 10px; }
  .setting-row { flex-direction: column; align-items: flex-start; gap: 4px; }
}
</style>

<style>
.settings-dialog .el-dialog {
  background: rgba(20, 20, 30, 0.15) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.10) !important;
  border-radius: 16px !important;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.25) !important;
}
[data-theme="dark"] .settings-dialog .el-dialog {
  background: rgba(0, 0, 0, 0.40) !important;
  border-color: rgba(255, 255, 255, 0.06) !important;
}
.settings-dialog .el-select-dropdown {
  background: rgba(20, 20, 30, 0.15) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 12px !important;
}
[data-theme="dark"] .settings-dialog .el-select-dropdown {
  background: rgba(0, 0, 0, 0.40) !important;
}
.settings-dialog .el-select-dropdown__item {
  color: var(--text-secondary) !important;
}
.settings-dialog .el-select-dropdown__item:hover {
  background: rgba(255, 255, 255, 0.06) !important;
  color: var(--text-primary) !important;
}
.settings-dialog .el-select-dropdown__item.selected {
  color: #409eff !important;
}
.settings-dialog .el-checkbox__label {
  color: var(--text-secondary) !important;
}
</style>