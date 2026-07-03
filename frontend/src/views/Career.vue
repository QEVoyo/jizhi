<template>
  <div class="career-page">
    <AppLayout locked>
      <template #sidebar>
        <CareerSidebar current-page="career" />
      </template>
      <template #main>
        <div class="career-content">
          <h1>🗺️ 学程</h1>
          <p class="subtitle">学习旅程总览</p>

          <el-divider />

          <!-- ===== 段位 + 等级 ===== -->
          <div class="rank-section">
            <div class="rank-left">
              <div class="rank-display">
                <span class="rank-icon" :style="{ color: rankColor }">
                  {{ rankIcon }} {{ rankName }} {{ rankSubSymbol }}
                </span>
                <span class="rank-points">{{ points }} 分</span>
              </div>
              <div class="rank-level-display">
                <span class="level-label">Lv.{{ userLevel }}</span>
                <span class="level-points">{{ points }} 分</span>
              </div>
              <div class="rank-progress">
                <div class="progress-track">
                  <div
                    class="progress-fill blue"
                    :style="{
                      width: levelProgress + '%',
                      background: '#409eff'
                    }"
                  />
                </div>
                <span class="rank-hint">
                  距离 Lv.{{ userLevel + 1 }} 还需 {{ nextLevelPoints }} 分
                </span>
              </div>
            </div>
          </div>

          <el-divider />

          <!-- ===== 今日施肥（5个任务） ===== -->
          <div class="daily-section">
            <div class="section-header-wrap">
              <h2>🌱 今日施肥</h2>
              <div class="section-actions">
                <el-button
                  v-if="!refreshUsed"
                  size="small"
                  class="refresh-btn"
                  @click="handleRefreshDaily"
                >
                  🔄 换一批
                </el-button>
                <el-button
                  v-else
                  size="small"
                  class="refresh-btn disabled"
                  disabled
                >
                  ✅ 已更换
                </el-button>
                <span class="task-count">{{ displayDaily.length }} / 5 个任务</span>
              </div>
            </div>
            <p class="subtitle">每日任务 · 完成获得收获</p>

            <div class="task-table" v-if="displayDaily.length">
              <div class="task-row header">
                <span class="task-status">状态</span>
                <span class="task-name">肥料</span>
                <span class="task-reward">收获</span>
                <span class="task-value">价值</span>
                <span class="task-progress">进度</span>
              </div>
              <div class="task-row" v-for="(task, idx) in displayDaily" :key="idx">
                <span class="task-status">
                  <el-button
                    :type="task.done ? 'success' : task.progress >= 100 ? 'warning' : 'info'"
                    :icon="task.done ? 'Check' : task.progress >= 100 ? 'Present' : 'Clock'"
                    circle
                    size="small"
                    :disabled="!task.done && task.progress < 100"
                    class="task-btn"
                    @click="task.progress >= 100 && !task.done && claimReward(task)"
                  />
                </span>
                <span class="task-name">{{ task.name }}</span>
                <span class="task-reward">+{{ task.reward }}</span>
                <span class="task-value">
                  <span
                    v-for="s in task.value"
                    :key="s"
                    class="star"
                    :style="{ color: getStarColor(task.value) }"
                  >★</span>
                </span>
                <span class="task-progress">
                  <div class="progress-wrapper">
                    <div class="progress-track">
                      <div
                        class="progress-fill"
                        :style="{
                          width: task.progress + '%',
                          background: getProgressColor(task.progress)
                        }"
                      />
                    </div>
                    <span class="progress-label">{{ task.progress }}%</span>
                  </div>
                </span>
              </div>
            </div>
            <div v-else class="empty-state">暂无每日任务</div>

            <!-- ===== 全部完成奖励 ===== -->
            <div v-if="displayDaily.length === 5 && allDailyDone" class="bonus-row">
              <span class="bonus-label">🎯 完成全部每日任务</span>
              <span class="bonus-reward">+50</span>
              <span class="bonus-value">
                <span class="star" style="color:#FFD700;">★★★★★</span>
              </span>
              <div class="bonus-progress">
                <div class="progress-wrapper">
                  <div class="progress-track">
                    <div class="progress-fill" style="width:100%; background:#6BCB77;" />
                  </div>
                  <span class="progress-label">100%</span>
                </div>
              </div>
              <el-button
                v-if="!bonusClaimed"
                type="warning"
                size="small"
                class="claim-btn"
                @click="claimBonus"
              >
                🎁 领取
              </el-button>
              <el-button v-else size="small" disabled class="claim-btn done">
                ✅ 已领取
              </el-button>
            </div>
          </div>

          <el-divider />

          <!-- ===== 即将拾贝 ===== -->
          <div class="achievement-section">
            <h2>🎯 即将拾贝</h2>
            <p class="subtitle">最接近完成的成就</p>
            <div v-if="pendingAchievements.length" class="achievement-list">
              <div
                v-for="ach in pendingAchievements.slice(0, 5)"
                :key="ach.id"
                class="achievement-item"
              >
                <div
                  class="ach-icon"
                  :style="{ color: ach.done ? ach.themeColor : '#555' }"
                >
                  <i :class="getIcon(ach.id)"></i>
                </div>
                <div class="ach-info">
                  <div class="ach-name">{{ ach.name }}</div>
                  <div class="ach-condition">{{ ach.condition }}</div>
                </div>
                <div class="ach-status">
                  <span v-if="ach.done">✅ 已拾取</span>
                  <span v-else-if="ach.ready" style="color:#e6a23c;">🎁 可领取</span>
                  <span v-else>⏳ 未解锁</span>
                </div>
                <div class="ach-progress">
                  <div class="progress-track">
                    <div
                      class="progress-fill"
                      :style="{
                        width: ach.done || ach.ready ? '100%' : '0%',
                        background: ach.done || ach.ready
                          ? `linear-gradient(90deg, ${ach.themeColor}66, ${ach.themeColor})`
                          : '#333'
                      }"
                    />
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">🎉 所有成就已解锁！继续加油！</div>
          </div>
        </div>
      </template>
    </AppLayout>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/AppLayout.vue'
import CareerSidebar from '@/components/CareerSidebar.vue'
import { getTaskProgress, getUserStats, updateStats, recordAction } from '@/api/career'
import { ElMessage } from 'element-plus'
import { RANK_ICONS, RANK_COLORS, RANK_ORDER, SUB_SYMBOLS } from '@/utils/constants'

const router = useRouter()
const authStore = useAuthStore()

const taskData = ref({ seed: [], daily: [], long: [], achievements: [] })
const stats = ref({ points: 0, rank: '启程', sub_rank: 1 })
const loading = ref(true)
const refreshUsed = ref(false)
const bonusClaimed = ref(false)

const allDailyTasks = computed(() => taskData.value.daily || [])
const displayDaily = ref([])

const seedTasks = computed(() => taskData.value.seed || [])
const longTasks = computed(() => taskData.value.long || [])
const achievements = computed(() => taskData.value.achievements || [])
const pendingAchievements = computed(() => achievements.value.filter(a => !a.done))

const allDailyDone = computed(() => {
  const tasks = displayDaily.value
  return tasks.length === 5 && tasks.every(t => t.done)
})

const points = computed(() => stats.value.points || 0)
const rank = computed(() => stats.value.rank || '启程')
const subRank = computed(() => stats.value.sub_rank || 1)
const rankIcon = computed(() => RANK_ICONS[rank.value] || '◈')
const rankName = computed(() => rank.value)
const rankColor = computed(() => RANK_COLORS[rank.value] || '#888')
const rankSubSymbol = computed(() => SUB_SYMBOLS[subRank.value] || '○')
const rankIndex = computed(() => RANK_ORDER.indexOf(rank.value) || 0)

// ===== 等级计算（等差数列） =====
const userLevel = computed(() => {
  let level = 1
  let totalNeeded = 2
  while (points.value >= totalNeeded) {
    level++
    totalNeeded += (level + 1)
  }
  return level
})

const levelProgress = computed(() => {
  let used = 0
  for (let i = 1; i < userLevel.value; i++) {
    used += (i + 1)
  }
  const currentProgress = points.value - used
  const currentNeeded = userLevel.value + 1
  return Math.min(100, (currentProgress / currentNeeded) * 100)
})

const nextLevelPoints = computed(() => {
  let used = 0
  for (let i = 1; i <= userLevel.value; i++) {
    used += (i + 1)
  }
  return used - points.value
})

const rankProgress = computed(() => {
  const base = rankIndex.value * 500
  const subStart = base + (subRank.value - 1) * 100
  const subEnd = base + subRank.value * 100
  const progress = ((points.value - subStart) / 100) * 100
  return Math.min(Math.max(progress, 0), 100)
})

function getStarColor(value) {
  const colors = {
    1: '#8B8B8B',
    2: '#66CC66',
    3: '#4CAF50',
    4: '#42A5F5',
    5: '#FFD700',
    6: '#FF9800',
    7: '#FF5722',
    8: '#F44336',
    9: '#9C27B0',
    10: '#FFD700'
  }
  return colors[value] || '#888'
}

function getIcon(id) {
  const map = {
    'first_checkin': 'fa-book-open',
    'checkin_7': 'fa-fire',
    'checkin_30': 'fa-calendar-check',
    'first_chat': 'fa-comment',
    'first_plan': 'fa-sitemap',
    'first_generate': 'fa-pen-fancy',
    'first_evaluate': 'fa-search',
    'questions_100': 'fa-scroll',
    'questions_1000': 'fa-crown',
    'mistakes_10': 'fa-bullseye',
    'mistakes_100': 'fa-shield-halved',
    'sets_5': 'fa-folder-open',
    'sets_20': 'fa-layer-group',
    'rank_mingli': 'fa-graduation-cap',
    'rank_zhizhi': 'fa-brain',
    'rank_duxing': 'fa-rocket',
    'rank_zhenjing': 'fa-star',
    'legend': 'fa-crown',
    'share_10': 'fa-share-alt',
    'study_7': 'fa-sun',
    'timer_10h': 'fa-clock',
    'logs_50': 'fa-book',
    'report_10': 'fa-chart-line',
    'sets_50': 'fa-building',
    'messages_500': 'fa-comments'
  }
  return map[id] || 'fa-trophy'
}

function getProgressColor(progress) {
  if (progress < 5) return '#FF0000'
  if (progress < 10) return '#FF1A00'
  if (progress < 15) return '#FF3300'
  if (progress < 20) return '#FF4D00'
  if (progress < 25) return '#FF6600'
  if (progress < 30) return '#FF8000'
  if (progress < 35) return '#FF9900'
  if (progress < 40) return '#FFB300'
  if (progress < 45) return '#FFCC00'
  if (progress < 50) return '#FFE600'
  if (progress < 55) return '#D4E000'
  if (progress < 60) return '#A8D500'
  if (progress < 65) return '#7DCC00'
  if (progress < 70) return '#52C200'
  if (progress < 75) return '#26B800'
  if (progress < 80) return '#00AD00'
  if (progress < 85) return '#00A300'
  if (progress < 90) return '#009900'
  if (progress < 95) return '#008000'
  return '#006600'
}

function shuffleArray(arr) {
  const shuffled = [...arr]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

function getStoredDaily() {
  try {
    const stored = sessionStorage.getItem('daily_tasks')
    if (stored) {
      const parsed = JSON.parse(stored)
      if (parsed.length > 0) return parsed
    }
  } catch {}
  return null
}

function selectDailyTasks() {
  const pool = allDailyTasks.value
  if (!pool.length) {
    displayDaily.value = []
    return
  }
  const stored = getStoredDaily()
  if (stored && stored.length === 5) {
    const poolNames = new Set(pool.map(t => t.name))
    const allExist = stored.every(t => poolNames.has(t.name))
    if (allExist) {
      displayDaily.value = stored
      return
    }
  }
  const shuffled = shuffleArray(pool)
  const selected = shuffled.slice(0, 5)
  displayDaily.value = selected
  sessionStorage.setItem('daily_tasks', JSON.stringify(selected))
}

function refreshDailyTasks() {
  const pool = allDailyTasks.value
  if (!pool.length) return
  const shuffled = shuffleArray(pool)
  const selected = shuffled.slice(0, 5)
  displayDaily.value = selected
  sessionStorage.setItem('daily_tasks', JSON.stringify(selected))
}

async function claimReward(task) {
  try {
    await updateStats({
      user_id: authStore.user.id,
      points_change: task.reward
    })
    ElMessage.success(`✅ 获得 ${task.reward} 分！`)
    await loadData()
  } catch {
    ElMessage.error('领取失败')
  }
}

async function claimBonus() {
  try {
    await updateStats({
      user_id: authStore.user.id,
      points_change: 50
    })
    bonusClaimed.value = true
    ElMessage.success('🎉 获得 50 分！')
    await loadData()
  } catch {
    ElMessage.error('领取失败')
  }
}

async function handleRefreshDaily() {
  if (refreshUsed.value) {
    ElMessage.warning('今日已更换过任务')
    return
  }
  refreshUsed.value = true
  refreshDailyTasks()
  ElMessage.success('🔄 今日施肥任务已更换')
}

async function loadData() {
  loading.value = true
  try {
    const [tasks, statsData] = await Promise.all([
      getTaskProgress(authStore.user.id),
      getUserStats(authStore.user.id)
    ])
    taskData.value = tasks
    stats.value = statsData
    selectDailyTasks()
    await recordAction(authStore.user.id, 'view_career')
  } catch (error) {
    console.error('加载数据失败', error)
  } finally {
    loading.value = false
  }
}

watch(allDailyTasks, () => {
  selectDailyTasks()
}, { deep: true })

onMounted(loadData)
</script>

<style scoped>
.career-content {
  padding: 8px 4px;
  max-width: 900px;
  margin: 0 auto;
}
h1 { font-size: 28px; color: var(--text-primary); }
.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  opacity: 0.6;
  margin-bottom: 4px;
}

/* ===== 段位 ===== */
.rank-section {
  padding: 20px 24px;
  border-radius: 14px;
  border: 1px solid var(--border-color);
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(12px);
}
.rank-left { flex: 1; }
.rank-display {
  display: flex;
  align-items: center;
  gap: 20px;
}
.rank-icon { font-size: 28px; font-weight: 700; }
.rank-points { font-size: 22px; font-weight: 600; color: var(--text-secondary); }
.rank-level-display {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 6px 0 4px;
}
.level-label { font-size: 18px; font-weight: 600; color: var(--text-primary); }
.level-points { font-size: 14px; color: var(--text-muted); }
.rank-progress { margin-top: 4px; }
.progress-track {
  height: 8px;
  border-radius: 4px;
  background: rgba(128,128,128,0.15);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}
.progress-fill.blue {
  background: #409eff !important;
  box-shadow: 0 0 12px rgba(64,158,255,0.3);
}
.rank-hint {
  font-size: 12px;
  color: var(--text-muted);
  display: block;
  margin-top: 4px;
}

/* ===== 每日施肥 ===== */
.daily-section {
  background: rgba(255,255,255,0.03);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  padding: 20px 24px;
  border: 1px solid var(--border-color);
}
.section-header-wrap {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.section-header-wrap h2 { font-size: 20px; margin: 0; color: var(--text-primary); }
.section-actions { display: flex; align-items: center; gap: 12px; }
.task-count { font-size: 13px; color: var(--text-muted); }
.refresh-btn {
  transition: all 0.3s ease !important;
  border-radius: 10px !important;
}
.refresh-btn:hover { transform: translateY(-2px) scale(1.03) !important; }
.refresh-btn.disabled { opacity: 0.5; }

.task-table {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}
.task-row {
  display: grid;
  grid-template-columns: 60px 1fr 70px 70px 1fr;
  gap: 8px;
  align-items: center;
  padding: 6px 8px;
  border-radius: 8px;
  font-size: 14px;
}
.task-row.header { font-weight: 600; color: var(--text-muted); font-size: 12px; }
.task-row:hover { background: rgba(128,128,128,0.04); }
.task-status { display: flex; align-items: center; justify-content: center; }
.task-btn { transition: all 0.3s ease !important; }
.task-btn:hover { transform: scale(1.08) !important; }
.star { font-size: 12px; letter-spacing: 1px; }

.progress-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}
.progress-track {
  flex: 1;
  height: 6px;
  border-radius: 4px;
  background: rgba(128,128,128,0.15);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}
.progress-label {
  font-size: 11px;
  color: var(--text-muted);
  min-width: 32px;
  text-align: right;
}

.bonus-row {
  display: grid;
  grid-template-columns: 60px 1fr 70px 70px 1fr 100px;
  gap: 8px;
  align-items: center;
  padding: 10px 8px;
  margin-top: 8px;
  border-radius: 8px;
  background: rgba(255,215,0,0.06);
  border: 1px solid rgba(255,215,0,0.12);
}
.bonus-label { font-weight: 600; color: var(--text-primary); }
.bonus-reward { color: #FFB300; font-weight: 600; }
.claim-btn { transition: all 0.3s ease !important; }
.claim-btn:hover { transform: translateY(-2px) scale(1.03) !important; }
.claim-btn.done { opacity: 0.5; }

/* ===== 成就 ===== */
.achievement-section {
  background: rgba(255,255,255,0.03);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  padding: 20px 24px;
  border: 1px solid var(--border-color);
}
.achievement-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}
.achievement-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}
.achievement-item:hover { background: rgba(128,128,128,0.04); }
.ach-icon { font-size: 22px; width: 32px; text-align: center; }
.ach-info { flex: 1; }
.ach-name { font-size: 14px; color: var(--text-primary); }
.ach-condition { font-size: 12px; color: var(--text-muted); }
.ach-status { font-size: 12px; min-width: 80px; }
.ach-progress { flex: 1; max-width: 120px; }
.ach-progress .progress-track { height: 4px; }
.empty-state {
  color: var(--text-muted);
  padding: 16px 0;
  text-align: center;
}
:deep(.el-progress__text) {
  font-size: 11px !important;
  color: var(--text-muted) !important;
}

@media (max-width: 768px) {
  .task-row {
    grid-template-columns: 40px 1fr 50px 50px 1fr;
    font-size: 12px;
    gap: 4px;
  }
  .bonus-row {
    grid-template-columns: 40px 1fr 50px 50px 1fr 80px;
    font-size: 12px;
  }
  .section-header-wrap { flex-direction: column; align-items: flex-start; }
}
</style>