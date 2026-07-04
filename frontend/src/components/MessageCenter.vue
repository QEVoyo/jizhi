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
        </div>
        <el-button text class="settings-btn" @click="showSettings = true">
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>

      <el-divider />

      <!-- ===== Tab 分类 ===== -->
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
          v-for="msg in filteredMessages"
          :key="msg.id"
          class="message-card"
          :class="{ unread: !msg.is_read }"
          @click="handleMessageClick(msg)"
        >
          <el-checkbox
            v-model="selectedIds"
            :value="msg.id"
            @click.stop
            class="message-checkbox"
          />
          <div class="message-icon" :style="{ color: msg.iconColor }">
            <el-icon :size="24"><component :is="msg.icon" /></el-icon>
          </div>
          <div class="message-body">
            <div class="message-top">
              <span class="message-title">{{ msg.title }}</span>
              <span class="message-time">{{ msg.time }}</span>
            </div>
            <div class="message-content">{{ msg.content }}</div>
            <div v-if="msg.actions" class="message-actions">
              <button
                v-for="action in msg.actions"
                :key="action.label"
                class="msg-action-btn"
                @click.stop="handleAction(action, msg)"
              >
                {{ action.label }}
              </button>
            </div>
          </div>
          <div v-if="!msg.is_read" class="unread-dot"></div>
        </div>

        <div v-if="!filteredMessages.length" class="empty-state">
          <el-icon :size="48"><Bell /></el-icon>
          <p>暂无消息</p>
          <span>当你收到新消息时，会在这里显示</span>
        </div>

        <div v-if="filteredMessages.length" class="load-more">
          <el-button text @click="loadMore" :loading="loadingMore">
            {{ hasMore ? '加载更多' : '已加载全部' }}
          </el-button>
        </div>
      </div>
    </div>

    <!-- ===== 设置弹窗 - 内联强制毛玻璃 ===== -->
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
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting,
  Bell,
  Check,
  Delete,
  Remove,
  Trophy,
  Star,
  Calendar,
  DataLine,
  User,
  FolderOpened,
  Promotion
} from '@element-plus/icons-vue'

const router = useRouter()

const activeTab = ref('all')
const selectedIds = ref([])
const selectAll = ref(false)
const loadingMore = ref(false)
const hasMore = ref(true)
const showSettings = ref(false)

const messages = ref([
  {
    id: 1,
    type: 'system',
    icon: Promotion,
    iconColor: '#409EFF',
    title: '基智学习助手 v2.0 已上线',
    content: '新增社区功能、多模态素材生成、Q&A帮助中心，快来体验吧！',
    time: '刚刚',
    is_read: false,
    actions: [{ label: '查看详情', route: '/community' }]
  },
  {
    id: 2,
    type: 'report',
    icon: DataLine,
    iconColor: '#67C23A',
    title: '本周学情报告已生成',
    content: '本周掌握度整体提升 12%，薄弱项：导数（42%），建议加强练习。',
    time: '2小时前',
    is_read: false,
    actions: [{ label: '查看报告', route: '/profile' }]
  },
  {
    id: 3,
    type: 'social',
    icon: User,
    iconColor: '#E6A23C',
    title: '好友请求',
    content: '用户「小明」请求添加你为好友，来自同一学习小组。',
    time: '3小时前',
    is_read: false,
    actions: [
      { label: '接受', action: 'accept' },
      { label: '拒绝', action: 'reject' }
    ]
  },
  {
    id: 4,
    type: 'learning',
    icon: Trophy,
    iconColor: '#F56C6C',
    title: '成就解锁：错题猎手',
    content: '恭喜你攻克 10 道错题，获得「错题猎手」成就！继续加油！',
    time: '昨天 18:30',
    is_read: true,
    actions: [{ label: '查看成就', route: '/career/achievements' }]
  },
  {
    id: 5,
    type: 'learning',
    icon: Star,
    iconColor: '#9C27B0',
    title: '段位晋升：明理',
    content: '恭喜你晋升到「明理」段位！积分已达 500 分，继续攀登！',
    time: '昨天 14:20',
    is_read: true,
    actions: [{ label: '查看段位', route: '/career/rank' }]
  },
  {
    id: 6,
    type: 'system',
    icon: Calendar,
    iconColor: '#409EFF',
    title: '打卡提醒',
    content: '今日尚未打卡，坚持学习才能不断进步，快来打卡吧！',
    time: '昨天 09:00',
    is_read: true,
    actions: [{ label: '去打卡', route: '/home' }]
  },
  {
    id: 7,
    type: 'social',
    icon: FolderOpened,
    iconColor: '#42A5F5',
    title: '题集分享',
    content: '好友「小红」向你分享题集「高数必刷100题」，共 50 道题。',
    time: '2天前',
    is_read: true,
    actions: [
      { label: '接收', action: 'receive_set' },
      { label: '拒绝', action: 'reject_set' }
    ]
  }
])

const tabList = computed(() => [
  { key: 'all', icon: Bell, label: '全部', count: 0 },
  { key: 'unread', icon: Bell, label: '未读', count: messages.value.filter(m => !m.is_read).length },
  { key: 'system', icon: Promotion, label: '系统', count: messages.value.filter(m => m.type === 'system' && !m.is_read).length },
  { key: 'learning', icon: Trophy, label: '学习', count: messages.value.filter(m => m.type === 'learning' && !m.is_read).length },
  { key: 'social', icon: User, label: '社交', count: messages.value.filter(m => m.type === 'social' && !m.is_read).length },
  { key: 'report', icon: DataLine, label: '学情', count: messages.value.filter(m => m.type === 'report' && !m.is_read).length }
])

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

const filteredMessages = computed(() => {
  let result = messages.value
  if (activeTab.value === 'unread') {
    result = result.filter(m => !m.is_read)
  } else if (activeTab.value !== 'all') {
    result = result.filter(m => m.type === activeTab.value)
  }
  return result
})

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

function markAllRead() {
  messages.value.forEach(m => {
    if (selectedIds.value.length === 0 || selectedIds.value.includes(m.id)) {
      m.is_read = true
    }
  })
  ElMessage.success('已标记为已读')
  selectedIds.value = []
  selectAll.value = false
}

function deleteSelected() {
  if (!selectedIds.value.length) {
    ElMessage.warning('请先选择消息')
    return
  }
  ElMessageBox.confirm('确定要删除选中的消息吗？', '确认删除')
    .then(() => {
      messages.value = messages.value.filter(m => !selectedIds.value.includes(m.id))
      selectedIds.value = []
      selectAll.value = false
      ElMessage.success('删除成功')
    })
    .catch(() => {})
}

function clearAll() {
  ElMessageBox.confirm('确定要清空所有消息吗？', '确认清空')
    .then(() => {
      messages.value = []
      selectedIds.value = []
      selectAll.value = false
      ElMessage.success('已清空')
    })
    .catch(() => {})
}

function handleMessageClick(msg) {
  if (!msg.is_read) {
    msg.is_read = true
  }
  if (msg.actions && msg.actions.length === 1 && msg.actions[0].route) {
    router.push(msg.actions[0].route)
  }
}

function handleAction(action, msg) {
  if (action.route) {
    router.push(action.route)
  } else if (action.action === 'accept') {
    ElMessage.success('已接受好友请求')
    msg.is_read = true
  } else if (action.action === 'reject') {
    ElMessage.info('已拒绝好友请求')
    msg.is_read = true
  } else if (action.action === 'receive_set') {
    ElMessage.success('题集已接收，已保存到你的题集列表')
    msg.is_read = true
  } else if (action.action === 'reject_set') {
    ElMessage.info('已拒绝题集分享')
    msg.is_read = true
  }
}

function loadMore() {
  loadingMore.value = true
  setTimeout(() => {
    loadingMore.value = false
    hasMore.value = false
    ElMessage.info('已加载全部消息')
  }, 1000)
}

function saveSettings() {
  showSettings.value = false
  ElMessage.success('设置已保存')
}
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
.message-card:active { transform: translateX(2px) scale(0.99); }

.message-checkbox { margin-top: 2px; flex-shrink: 0; }

.message-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  background: rgba(255,255,255,0.04);
}
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
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.5;
}
.message-actions { display: flex; gap: 10px; margin-top: 8px; }
.msg-action-btn {
  padding: 2px 12px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.02);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.msg-action-btn:hover {
  background: rgba(64,158,255,0.10);
  border-color: rgba(64,158,255,0.2);
  color: #409eff;
  transform: translateY(-2px);
}
.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(128,128,128,0.4);
  flex-shrink: 0;
  margin-top: 8px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}
.empty-state .el-icon { color: var(--text-muted); opacity: 0.3; margin-bottom: 12px; }
.empty-state p { font-size: 16px; color: var(--text-secondary); margin: 4px 0; }
.empty-state span { font-size: 14px; opacity: 0.6; }

.load-more { text-align: center; padding: 10px 0; }
.load-more .el-button { color: var(--text-muted) !important; font-size: 13px; }
.load-more .el-button:hover { color: var(--text-primary) !important; }

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
/* ===== 设置弹窗毛玻璃 - 全局强制覆盖 ===== */
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

/* 下拉框毛玻璃 */
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

/* 弹窗内复选框 */
.settings-dialog .el-checkbox__label {
  color: var(--text-secondary) !important;
}
</style>