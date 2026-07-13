<template>
  <div class="workbench-wrapper">
    <div class="workbench-header" @click="toggleWorkbench">
      <span class="workbench-title">
        <i class="fas fa-toolbox"></i> 工作台
      </span>
      <span class="workbench-toggle-icon">
        <i class="fas fa-chevron-down" :class="{ rotated: isOpen }"></i>
      </span>
    </div>

    <div v-if="isOpen" class="workbench-dropdown">
      <div class="workbench-content">
        <!-- ===== 打卡 ===== -->
        <div class="workbench-section">
          <div class="section-header" @click="toggleSection('checkin')">
            <i class="fas fa-calendar-check"></i>
            <span>打卡</span>
            <span class="badge">{{ checkinProjects.length }}</span>
            <i class="fas fa-chevron-down section-arrow" :class="{ rotated: activeSections.includes('checkin') }"></i>
          </div>
          <div v-if="activeSections.includes('checkin')" class="section-body">
            <div v-if="!checkinProjects.length" class="empty-state">暂无打卡项目</div>
            <div v-else>
              <div v-for="p in checkinProjects" :key="p.name" class="workbench-item">
                <div class="item-info">
                  <span class="item-name">{{ p.name }}</span>
                  <span class="item-progress-text">{{ p.completed_days }} / {{ p.target_days }} 天</span>
                  <el-progress
                    :percentage="Math.round((p.completed_days / p.target_days) * 100)"
                    :stroke-width="5"
                    :color="p.completed_days >= p.target_days ? '#67c23a' : '#409eff'"
                  />
                </div>
                <div class="item-actions">
                  <el-button
                    size="small"
                    :type="p.last_checkin === today ? 'info' : 'success'"
                    :disabled="p.last_checkin === today"
                    class="action-btn"
                    @click="handleCheckin(p.name)"
                  >
                    {{ p.last_checkin === today ? '已打卡' : '打卡' }}
                  </el-button>
                  <button class="icon-btn-sm" @click="handleDeleteCheckin(p.name)">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
            </div>
            <div class="add-form">
              <el-input
                v-model="newCheckinName"
                placeholder="项目名称"
                size="small"
                style="width:130px;"
                class="form-input"
              />
              <el-input-number
                v-model="newCheckinTarget"
                :min="1"
                :max="365"
                size="small"
                style="width:90px;"
                class="form-input number-input"
              />
              <el-button size="small" type="primary" class="action-btn" @click="handleAddCheckin">
                <i class="fas fa-plus"></i>
              </el-button>
            </div>
          </div>
        </div>

        <!-- ===== 倒计时 ===== -->
        <div class="workbench-section">
          <div class="section-header" @click="toggleSection('countdown')">
            <i class="fas fa-clock"></i>
            <span>倒计时</span>
            <span class="badge">{{ countdownEvents.length }}</span>
            <i class="fas fa-chevron-down section-arrow" :class="{ rotated: activeSections.includes('countdown') }"></i>
          </div>
          <div v-if="activeSections.includes('countdown')" class="section-body">
            <div v-if="!countdownEvents.length" class="empty-state">暂无倒计时事件</div>
            <div v-else>
              <div v-for="e in countdownEvents" :key="e.id" class="workbench-item">
                <div class="item-info">
                  <span class="item-name">{{ e.name }}</span>
                  <span class="item-meta">{{ getDaysUntil(e.target_date) >= 0 ? '还有 ' + getDaysUntil(e.target_date) + ' 天' : '已结束' }}</span>
                  <span class="item-meta"><i class="fas fa-calendar"></i> {{ e.target_date }}</span>
                </div>
                <button class="icon-btn-sm" @click="handleDeleteCountdown(e.id)">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>
            <div class="add-form">
              <el-input
                v-model="newCountdownName"
                placeholder="事件名称"
                size="small"
                style="width:130px;"
                class="form-input"
              />
              <el-date-picker
                v-model="newCountdownDate"
                type="date"
                placeholder="日期"
                size="small"
                style="width:130px;"
                value-format="YYYY-MM-DD"
                class="form-input"
              />
              <el-button size="small" type="primary" class="action-btn" @click="handleAddCountdown">
                <i class="fas fa-plus"></i>
              </el-button>
            </div>
          </div>
        </div>

        <!-- ===== 计时器 ===== -->
        <div class="workbench-section">
          <div class="section-header" @click="toggleSection('timer')">
            <i class="fas fa-hourglass-half"></i>
            <span>计时器</span>
            <span class="badge">{{ timerTemplates.length }}</span>
            <i class="fas fa-chevron-down section-arrow" :class="{ rotated: activeSections.includes('timer') }"></i>
          </div>
          <div v-if="activeSections.includes('timer')" class="section-body">
            <div v-if="activeTimer" class="active-timer">
              <div class="timer-display">
                <span class="timer-name">
                  <i v-if="activeTimer.type === 'stopwatch'" class="fas fa-play"></i>
                  <i v-else class="fas fa-hourglass-start"></i>
                  {{ activeTimer.name }}
                </span>
                <span class="timer-time">{{ formatTime(activeTimer.displaySeconds) }}</span>
              </div>
              <div class="timer-controls">
                <el-button size="small" class="action-btn" @click="pauseTimer">
                  {{ activeTimer.paused ? '继续' : '暂停' }}
                </el-button>
                <el-button size="small" type="danger" class="action-btn" @click="stopTimer">取消</el-button>
                <el-button v-if="activeTimer.type === 'stopwatch'" size="small" type="success" class="action-btn" @click="completeStopwatch">完成</el-button>
              </div>
            </div>
            <div v-if="!timerTemplates.length" class="empty-state">暂无计时器模板</div>
            <div v-else>
              <div v-for="t in timerTemplates" :key="t.id" class="workbench-item">
                <div class="item-info">
                  <span class="item-name">{{ t.name }}</span>
                  <span class="item-meta">{{ t.type === 'countdown' ? '⏳ 倒计时 ' + t.duration_minutes + '分钟' : '⏱️ 正向计时' }}</span>
                </div>
                <div class="item-actions">
                  <el-button size="small" type="primary" class="action-btn" :disabled="!!activeTimer" @click="startTimer(t)">开始</el-button>
                  <button class="icon-btn-sm" @click="handleDeleteTimer(t.id)"><i class="fas fa-times"></i></button>
                </div>
              </div>
            </div>
            <div class="add-form">
              <el-input
                v-model="newTimerName"
                placeholder="任务名称"
                size="small"
                style="width:110px;"
                class="form-input"
              />
              <el-select
                v-model="newTimerType"
                size="small"
                style="width:90px;"
                class="form-input"
              >
                <el-option label="倒计时" value="countdown" />
                <el-option label="正向计时" value="stopwatch" />
              </el-select>
              <el-input-number
                v-if="newTimerType === 'countdown'"
                v-model="newTimerDuration"
                :min="1"
                :max="180"
                size="small"
                style="width:80px;"
                class="form-input number-input"
              />
              <el-button size="small" type="primary" class="action-btn" @click="handleAddTimer">
                <i class="fas fa-plus"></i>
              </el-button>
            </div>
          </div>
        </div>

        <!-- ===== 学习日志（按日期分组 + 实时刷新） ===== -->
        <div class="workbench-section">
          <div class="section-header" @click="toggleSection('logs')">
            <i class="fas fa-book"></i>
            <span>学习日志</span>
            <span class="badge">{{ logs.length }}</span>
            <i class="fas fa-chevron-down section-arrow" :class="{ rotated: activeSections.includes('logs') }"></i>
          </div>
          <div v-if="activeSections.includes('logs')" class="section-body">
            <div v-if="!logs.length" class="empty-state">暂无学习日志</div>
            <div v-else>
              <div v-for="(group, date) in groupedLogs" :key="date" class="log-group">
                <div class="log-group-date">{{ date }}</div>
                <div v-for="log in group" :key="log.id" class="log-item">
                  <span class="log-time">{{ log.time || '--:--' }}</span>
                  <span class="log-keyword">{{ log.keyword }}</span>
                  <button class="log-delete-btn" @click="handleDeleteLog(log.id)">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 学情报告 ===== -->
        <div class="workbench-section">
          <div class="section-header" @click="toggleSection('report')">
            <i class="fas fa-chart-line"></i>
            <span>学情报告</span>
            <i class="fas fa-chevron-down section-arrow" :class="{ rotated: activeSections.includes('report') }"></i>
          </div>
          <div v-if="activeSections.includes('report')" class="section-body">
            <el-button size="small" type="primary" class="action-btn" :loading="reportLoading" @click="generateReport">
              <i class="fas fa-sync"></i> 生成报告
            </el-button>
            <div v-if="reportContent" class="report-result">
              <el-divider />
              <div class="report-text">{{ reportContent }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useToolsStore } from '@/stores/tools'
import { getLearningLogs, clearLearningLogs, deleteLearningLog, getReport } from '@/api/tools'
import { addLearningLog as apiAddLog } from '@/api/tools'
import { recordAction } from '@/api/career'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()
const toolsStore = useToolsStore()

const isOpen = ref(false)
const activeSections = ref([])

let logTimer = null

function toggleWorkbench() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    loadLogs()
  }
}

function toggleSection(name) {
  const index = activeSections.value.indexOf(name)
  if (index > -1) {
    activeSections.value.splice(index, 1)
  } else {
    activeSections.value.push(name)
  }
}

// ===== 打卡 =====
const newCheckinName = ref('')
const newCheckinTarget = ref(30)
const today = new Date().toISOString().slice(0, 10)
const checkinProjects = computed(() => toolsStore.checkinProjects)

async function handleCheckin(name) {
  const success = toolsStore.doCheckin(name)
  if (!success) {
    ElMessage.warning('今天已经打卡过了')
    return
  }
  await toolsStore.saveCheckinData(authStore.user.id, toolsStore.checkinProjects)
  await recordAction(authStore.user.id, 'checkin')
  ElMessage.success('打卡成功！')
}

function handleDeleteCheckin(name) {
  toolsStore.deleteCheckinProject(name)
  toolsStore.saveCheckinData(authStore.user.id, toolsStore.checkinProjects)
}

async function handleAddCheckin() {
  if (!newCheckinName.value) {
    ElMessage.warning('请输入项目名称')
    return
  }
  toolsStore.addCheckinProject(newCheckinName.value, newCheckinTarget.value)
  await toolsStore.saveCheckinData(authStore.user.id, toolsStore.checkinProjects)
  newCheckinName.value = ''
  ElMessage.success('添加成功')
}

// ===== 倒计时 =====
const newCountdownName = ref('')
const newCountdownDate = ref('')
const countdownEvents = computed(() => toolsStore.countdownEvents)

function getDaysUntil(dateStr) {
  return toolsStore.getDaysUntil(dateStr)
}

function handleDeleteCountdown(id) {
  toolsStore.deleteCountdownEvent(id)
  toolsStore.saveCountdownData(authStore.user.id, toolsStore.countdownEvents)
}

async function handleAddCountdown() {
  if (!newCountdownName.value || !newCountdownDate.value) {
    ElMessage.warning('请填写完整信息')
    return
  }
  toolsStore.addCountdownEvent(newCountdownName.value, newCountdownDate.value)
  await toolsStore.saveCountdownData(authStore.user.id, toolsStore.countdownEvents)
  newCountdownName.value = ''
  newCountdownDate.value = ''
  ElMessage.success('添加成功')
}

// ===== 计时器 =====
const newTimerName = ref('')
const newTimerType = ref('countdown')
const newTimerDuration = ref(25)
const activeTimer = ref(null)
let timerInterval = null
const timerTemplates = computed(() => toolsStore.timerTemplates)

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

function startTimer(template) {
  if (activeTimer.value) {
    ElMessage.warning('已有计时器在运行')
    return
  }
  const totalSeconds = template.type === 'countdown' ? template.duration_minutes * 60 : 0
  activeTimer.value = {
    id: template.id,
    name: template.name,
    type: template.type,
    displaySeconds: totalSeconds,
    paused: false,
    totalSeconds: totalSeconds
  }
  startTimerLoop()
}

function startTimerLoop() {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
  timerInterval = setInterval(() => {
    if (!activeTimer.value || activeTimer.value.paused) return

    if (activeTimer.value.type === 'countdown') {
      activeTimer.value.displaySeconds -= 1
      if (activeTimer.value.displaySeconds <= 0) {
        activeTimer.value.displaySeconds = 0
        clearInterval(timerInterval)
        timerInterval = null
        ElMessage.success(`⏰ ${activeTimer.value.name} 时间到！`)
        recordAction(authStore.user.id, 'timer_complete')
        return
      }
    } else {
      activeTimer.value.displaySeconds += 1
    }
  }, 1000)
}

function pauseTimer() {
  if (!activeTimer.value) return
  activeTimer.value.paused = !activeTimer.value.paused
  if (activeTimer.value.paused) {
    if (timerInterval) {
      clearInterval(timerInterval)
      timerInterval = null
    }
  } else {
    startTimerLoop()
  }
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
  activeTimer.value = null
}

async function completeStopwatch() {
  if (!activeTimer.value || activeTimer.value.type !== 'stopwatch') return
  const totalSeconds = activeTimer.value.displaySeconds
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  let timeStr = ''
  if (minutes > 0 && seconds > 0) {
    timeStr = `${minutes}分${seconds}秒`
  } else if (minutes > 0) {
    timeStr = `${minutes}分钟`
  } else {
    timeStr = `${seconds}秒`
  }

  if (totalSeconds > 0) {
    const keyword = `学习了「${activeTimer.value.name}」${timeStr}`
    await addLog(keyword)
    ElMessage.success(`✅ ${keyword}，已记录到学习日志`)
    await recordAction(authStore.user.id, 'use_timer')
  } else {
    ElMessage.warning('计时太短，未记录')
  }
  stopTimer()
}

function handleDeleteTimer(id) {
  if (activeTimer.value && activeTimer.value.id === id) {
    stopTimer()
  }
  toolsStore.deleteTimerTemplate(id)
  toolsStore.saveTimerData(authStore.user.id, toolsStore.timerTemplates)
}

async function handleAddTimer() {
  if (!newTimerName.value) {
    ElMessage.warning('请输入任务名称')
    return
  }
  toolsStore.addTimerTemplate(newTimerName.value, newTimerType.value, newTimerDuration.value)
  await toolsStore.saveTimerData(authStore.user.id, toolsStore.timerTemplates)
  newTimerName.value = ''
  ElMessage.success('添加成功')
}

// ===== 学习日志 =====
const logs = ref([])

async function loadLogs() {
  try {
    const data = await getLearningLogs(authStore.user.id)
    const rawLogs = data.logs || []
    logs.value = rawLogs.sort((a, b) => {
      const timeA = a.created_at || a.date || ''
      const timeB = b.created_at || b.date || ''
      return timeB.localeCompare(timeA)
    })
  } catch (e) {
    console.error('加载日志失败', e)
  }
}

async function addLog(keyword) {
  try {
    await apiAddLog(authStore.user.id, keyword)
    await loadLogs()
  } catch (e) {
    console.error('添加日志失败', e)
  }
}

async function handleDeleteLog(logId) {
  try {
    await ElMessageBox.confirm('确定要删除这条日志吗？', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteLearningLog(authStore.user.id, logId)
    await loadLogs()
    ElMessage.success('已删除')
  } catch {
    // 用户取消
  }
}

const groupedLogs = computed(() => {
  const groups = {}
  const todayStr = new Date().toISOString().slice(0, 10)
  const yesterdayStr = new Date(Date.now() - 86400000).toISOString().slice(0, 10)

  logs.value.forEach(log => {
    const date = log.date || log.created_at?.slice(0, 10) || '未知日期'
    let displayDate = date
    if (date === todayStr) {
      displayDate = '今天'
    } else if (date === yesterdayStr) {
      displayDate = '昨天'
    }
    if (!groups[displayDate]) {
      groups[displayDate] = []
    }
    groups[displayDate].push(log)
  })
  return groups
})

// ===== 学情报告 =====
const reportContent = ref('')
const reportLoading = ref(false)

async function generateReport() {
  reportLoading.value = true
  try {
    const data = await getReport(authStore.user.id)
    const keywords = data.keywords || []
    const totalDays = data.total_checkin_days || 0
    const keywordsStr = keywords.length ? keywords.slice(0, 10).join('、') : '暂无'
    reportContent.value = `
📊 学习报告

近期学习内容：${keywordsStr}
累计打卡天数：${totalDays} 天
学习项目数：${data.project_count || 0} 个

💪 继续保持，你正在进步！
    `
    await recordAction(authStore.user.id, 'view_report')
  } catch (e) {
    ElMessage.error('生成报告失败')
  } finally {
    reportLoading.value = false
  }
}

// ===== 生命周期 =====
onMounted(() => {
  toolsStore.loadCheckin(authStore.user.id)
  toolsStore.loadCountdown(authStore.user.id)
  toolsStore.loadTimer(authStore.user.id)
  loadLogs()

  logTimer = setInterval(() => {
    loadLogs()
  }, 30000)
})

onUnmounted(() => {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
  if (logTimer) {
    clearInterval(logTimer)
    logTimer = null
  }
})
</script>

<style scoped>
/* ===== 强制移除所有列表符号 ===== */
.workbench-dropdown ul,
.workbench-dropdown ol,
.workbench-dropdown li,
.log-group ul,
.log-group ol,
.log-group li,
.log-item {
  list-style: none !important;
  list-style-type: none !important;
  padding-left: 0 !important;
  margin-left: 0 !important;
}
.log-item::marker {
  content: none !important;
  display: none !important;
  font-size: 0 !important;
  color: transparent !important;
}

.workbench-wrapper {
  position: relative;
  margin-top: 4px;
}

.workbench-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-secondary);
  font-size: 13px;
}
.workbench-header:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
  transform: translateX(2px);
}
.workbench-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}
.workbench-toggle-icon {
  transition: transform 0.3s ease;
}
.workbench-toggle-icon .rotated {
  transform: rotate(180deg);
}

.workbench-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 100;
  background: var(--card-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 8px 12px;
  max-height: 420px;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}
[data-theme="dark"] .workbench-dropdown {
  background: rgba(20, 20, 35, 0.9);
}

.workbench-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.workbench-section {
  border-bottom: 1px solid var(--border-color);
  padding: 4px 0;
}
.workbench-section:last-child {
  border-bottom: none;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  border-radius: 6px;
  transition: all 0.3s ease;
}
.section-header:hover {
  color: var(--text-primary);
  transform: translateX(2px);
}
.section-header .badge {
  background: rgba(128, 128, 128, 0.12);
  border-radius: 10px;
  padding: 0 8px;
  font-size: 11px;
  color: var(--text-muted);
  margin-left: auto;
}
.section-arrow {
  font-size: 11px;
  transition: transform 0.3s ease;
}
.section-arrow.rotated {
  transform: rotate(180deg);
}

.section-body {
  padding: 4px 0 8px 20px;
}

.workbench-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  gap: 8px;
  flex-wrap: wrap;
  border-bottom: 1px solid rgba(128, 128, 128, 0.04);
}
.workbench-item:last-child {
  border-bottom: none;
}
.workbench-item:hover {
  background: rgba(128, 128, 128, 0.02);
}

.item-info {
  flex: 1;
  min-width: 100px;
}
.item-name {
  font-weight: 500;
  font-size: 13px;
  color: var(--text-primary);
}
.item-meta {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: 6px;
}
.item-progress-text {
  font-size: 12px;
  color: var(--text-muted);
  margin-left: 6px;
}
.item-actions {
  display: flex;
  gap: 4px;
  align-items: center;
}

.add-form {
  display: flex;
  gap: 6px;
  margin-top: 6px;
  flex-wrap: wrap;
  align-items: center;
}

.form-input {
  transition: all 0.3s ease;
}
.form-input:hover {
  transform: scale(1.02);
}
.form-input:focus-within {
  transform: scale(1.02);
}

.number-input {
  width: 90px !important;
}
.number-input :deep(.el-input-number) {
  height: 34px !important;
  width: 100% !important;
}
.number-input :deep(.el-input-number .el-input) {
  height: 34px !important;
}
.number-input :deep(.el-input-number .el-input__wrapper) {
  padding: 0 30px !important;
  border-radius: 8px !important;
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid var(--border-color) !important;
  box-shadow: none !important;
}
.number-input :deep(.el-input-number .el-input__inner) {
  text-align: center !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  color: var(--text-primary) !important;
  height: 32px !important;
  line-height: 32px !important;
}
.number-input :deep(.el-input-number .el-input-number__decrease),
.number-input :deep(.el-input-number .el-input-number__increase) {
  width: 28px !important;
  height: 28px !important;
  font-size: 16px !important;
  border-radius: 6px !important;
  background: rgba(255, 255, 255, 0.06) !important;
  border: 1px solid var(--border-color) !important;
  color: var(--text-secondary) !important;
  transition: all 0.3s ease !important;
  margin: 1px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}
.number-input :deep(.el-input-number .el-input-number__decrease:hover),
.number-input :deep(.el-input-number .el-input-number__increase:hover) {
  background: rgba(64, 158, 255, 0.12) !important;
  color: #409eff !important;
  transform: scale(1.05);
}
.number-input :deep(.el-input-number .el-input-number__decrease:active),
.number-input :deep(.el-input-number .el-input-number__increase:active) {
  transform: scale(0.95);
}
.number-input :deep(.el-input-number .el-input-number__decrease.is-disabled),
.number-input :deep(.el-input-number .el-input-number__increase.is-disabled) {
  opacity: 0.3 !important;
  cursor: not-allowed !important;
}

[data-theme="dark"] .number-input :deep(.el-input-number .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.03) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
}
[data-theme="dark"] .number-input :deep(.el-input-number .el-input-number__decrease),
[data-theme="dark"] .number-input :deep(.el-input-number .el-input-number__increase) {
  background: rgba(255, 255, 255, 0.04) !important;
  border-color: rgba(255, 255, 255, 0.06) !important;
  color: var(--text-muted) !important;
}
[data-theme="dark"] .number-input :deep(.el-input-number .el-input-number__decrease:hover),
[data-theme="dark"] .number-input :deep(.el-input-number .el-input-number__increase:hover) {
  background: rgba(64, 158, 255, 0.15) !important;
  color: #66b1ff !important;
}
[data-theme="dark"] .number-input :deep(.el-input-number .el-input__inner) {
  color: var(--text-primary) !important;
}

.empty-state {
  color: var(--text-muted);
  padding: 4px 0;
  font-size: 13px;
}

.active-timer {
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(128, 128, 128, 0.04);
  margin-bottom: 8px;
}
.timer-display {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
}
.timer-time {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}
.timer-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
}
.timer-controls {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

/* ===== 学习日志 ===== */
.log-group {
  margin-bottom: 8px;
  padding-left: 0 !important;
  list-style: none !important;
}
.log-group ul,
.log-group ol {
  padding-left: 0 !important;
  list-style: none !important;
}
.log-group-date {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 4px 0 2px 0;
  border-bottom: 1px solid rgba(128, 128, 128, 0.06);
  margin-bottom: 4px;
}
.log-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
  font-size: 13px;
  border-bottom: 1px solid rgba(128, 128, 128, 0.04);
  transition: all 0.2s ease;
  list-style: none !important;
  list-style-type: none !important;
  padding-left: 0 !important;
  margin-left: 0 !important;
}
.log-item::marker {
  content: none !important;
  display: none !important;
  font-size: 0 !important;
  color: transparent !important;
}
.log-item:hover {
  background: rgba(128, 128, 128, 0.03);
  transform: translateX(2px);
}
.log-item:hover .log-delete-btn {
  opacity: 1;
}
.log-date {
  color: var(--text-muted);
  font-size: 12px;
  min-width: 60px;
  flex-shrink: 0;
}
.log-keyword {
  color: var(--text-primary);
  flex: 1;
}
.log-delete-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  opacity: 0;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.log-delete-btn:hover {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.08);
}

.report-result {
  margin-top: 6px;
}
.report-text {
  white-space: pre-wrap;
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-primary);
}

.action-btn {
  transition: all 0.3s ease !important;
}
.action-btn:hover {
  transform: translateY(-2px) scale(1.03) !important;
}
.action-btn:active {
  transform: scale(0.95) !important;
}

.icon-btn-sm {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 12px;
  transition: all 0.3s ease;
}
.icon-btn-sm:hover {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.08);
  transform: scale(1.1);
}
</style>