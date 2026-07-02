<template>
  <div class="career-page">
    <AppLayout>
      <template #sidebar>
        <CareerSidebar />
      </template>
      <template #main>
        <div class="career-content">
          <!-- 返回按钮 -->
          <el-button text @click="goHome" class="back-btn">
            ← 返回主界面
          </el-button>

          <h1>🗺️ 学程</h1>
          <p class="subtitle">学习旅程总览</p>

          <el-divider />

          <!-- 段位信息 -->
          <div class="rank-section">
            <div class="rank-display">
              <div class="rank-icon" :style="{ color: rankColor }">
                {{ rankIcon }} {{ rank }} {{ subSymbol }}
              </div>
              <div class="rank-points">{{ points }} 分</div>
            </div>
            <div class="rank-progress">
              <el-progress
                :percentage="rankProgress"
                :color="rankColor"
                :stroke-width="8"
              />
              <span class="rank-hint">距离下一小段还需 {{ nextPoints }} 分</span>
            </div>
          </div>

          <el-divider />

          <!-- 今日施肥 -->
          <h2>🌱 今日施肥</h2>
          <p class="subtitle">每日任务 · 完成获得收获</p>

          <div class="task-table" v-if="dailyTasks.length">
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
                  @click="task.progress >= 100 && !task.done && claimReward(task)"
                />
              </span>
              <span class="task-name">{{ task.name }}</span>
              <span class="task-reward">+{{ task.reward }}</span>
              <span class="task-value">
                <span v-for="s in task.value" :key="s" class="star">★</span>
              </span>
              <span class="task-progress">
                <el-progress
                  :percentage="task.progress"
                  :color="getColor(task.progress)"
                  :stroke-width="6"
                />
              </span>
            </div>
          </div>
          <div v-else class="empty-state">暂无每日任务</div>

          <el-divider />

          <!-- 播种 -->
          <h2>🌱 播种</h2>
          <p class="subtitle">新手引导 · 第一次使用各项功能</p>
          <div class="task-table" v-if="seedTasks.length">
            <div class="task-row" v-for="(task, idx) in seedTasks.slice(0, 20)" :key="idx">
              <span class="task-status">
                <el-icon v-if="task.done" color="#67c23a"><Check /></el-icon>
                <el-icon v-else color="#909399"><Clock /></el-icon>
              </span>
              <span class="task-name">{{ task.name }}</span>
              <span class="task-reward">+{{ task.reward }}</span>
              <span class="task-value">
                <span v-for="s in task.value" :key="s" class="star">★</span>
              </span>
              <span class="task-progress">
                <el-progress :percentage="task.progress" :color="getColor(task.progress)" :stroke-width="6" />
              </span>
            </div>
          </div>
          <div v-else class="empty-state">暂无播种任务</div>

          <el-divider />

          <!-- 发芽 -->
          <h2>🌿 发芽</h2>
          <p class="subtitle">长期耕耘 · 持续积累 · 阶梯解锁</p>
          <div class="task-table" v-if="longTasks.length">
            <div class="task-row" v-for="(task, idx) in longTasks.slice(0, 20)" :key="idx">
              <span class="task-status">
                <el-icon v-if="task.done" color="#67c23a"><Check /></el-icon>
                <el-icon v-else color="#909399"><Clock /></el-icon>
              </span>
              <span class="task-name">{{ task.name }}</span>
              <span class="task-reward">+{{ task.reward }}</span>
              <span class="task-value">
                <span v-for="s in task.value" :key="s" class="star">★</span>
              </span>
              <span class="task-progress">
                <el-progress :percentage="task.progress" :color="getColor(task.progress)" :stroke-width="6" />
              </span>
            </div>
          </div>
          <div v-else class="empty-state">暂无发芽任务</div>

          <el-divider />

          <!-- 即将拾贝 -->
          <h2>🎯 即将拾贝</h2>
          <p class="subtitle">最接近完成的成就</p>
          <div v-if="pendingAchievements.length">
            <div
              v-for="ach in pendingAchievements.slice(0, 5)"
              :key="ach.id"
              class="achievement-item"
            >
              <span>{{ ach.name }}</span>
              <span class="ach-status">{{ ach.done ? '✅ 已解锁' : '⏳ 未解锁' }}</span>
              <el-progress :percentage="ach.done ? 100 : 0" :stroke-width="4" />
            </div>
          </div>
          <div v-else class="empty-state">暂无成就数据</div>
        </div>
      </template>
    </AppLayout>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
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

const seedTasks = computed(() => taskData.value.seed || [])
const dailyTasks = computed(() => taskData.value.daily || [])
const longTasks = computed(() => taskData.value.long || [])
const achievements = computed(() => taskData.value.achievements || [])

const displayDaily = computed(() => {
  const tasks = dailyTasks.value
  if (tasks.length <= 5) return tasks
  return tasks.slice(0, 5)
})

const pendingAchievements = computed(() => {
  return achievements.value.filter(a => !a.done)
})

const points = computed(() => stats.value.points || 0)
const rank = computed(() => stats.value.rank || '启程')
const subRank = computed(() => stats.value.sub_rank || 1)
const rankIcon = computed(() => RANK_ICONS[rank.value] || '◈')
const rankColor = computed(() => RANK_COLORS[rank.value] || '#888')
const subSymbol = computed(() => SUB_SYMBOLS[subRank.value] || '○')

const rankIndex = computed(() => RANK_ORDER.indexOf(rank.value) || 0)
const rankProgress = computed(() => {
  const base = rankIndex.value * 500
  const subStart = base + (subRank.value - 1) * 100
  const subEnd = base + subRank.value * 100
  const progress = ((points.value - subStart) / 100) * 100
  return Math.min(Math.max(progress, 0), 100)
})
const nextPoints = computed(() => {
  const base = rankIndex.value * 500
  const subEnd = base + subRank.value * 100
  return subEnd - points.value
})

function getColor(progress) {
  if (progress < 30) return '#FF6B6B'
  if (progress < 60) return '#FFB74D'
  if (progress < 80) return '#FFD93D'
  return '#6BCB77'
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

async function loadData() {
  loading.value = true
  try {
    const [tasks, statsData] = await Promise.all([
      getTaskProgress(authStore.user.id),
      getUserStats(authStore.user.id)
    ])
    taskData.value = tasks
    stats.value = statsData
    await recordAction(authStore.user.id, 'view_career')
  } catch (error) {
    console.error('加载数据失败', error)
  } finally {
    loading.value = false
  }
}

function goHome() {
  router.push('/')
}

onMounted(loadData)
</script>

<style scoped>
.career-content {
  padding: 8px 4px;
}
.back-btn {
  margin-bottom: 12px;
  color: var(--text-secondary);
}
h1 {
  font-size: 28px;
  color: var(--text-primary);
}
.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  opacity: 0.6;
  margin-bottom: 4px;
}

.rank-section {
  display: flex;
  gap: 40px;
  align-items: center;
  flex-wrap: wrap;
  padding: 16px 0;
}
.rank-display {
  display: flex;
  align-items: center;
  gap: 20px;
}
.rank-icon {
  font-size: 28px;
  font-weight: 700;
}
.rank-points {
  font-size: 22px;
  font-weight: 600;
}
.rank-progress {
  flex: 1;
  min-width: 200px;
}
.rank-hint {
  font-size: 12px;
  color: var(--text-muted);
}

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
.task-row.header {
  font-weight: 600;
  color: var(--text-muted);
  font-size: 12px;
}
.task-row:hover {
  background: rgba(128, 128, 128, 0.04);
}
.task-status {
  display: flex;
  align-items: center;
  justify-content: center;
}
.task-value .star {
  color: #FFD700;
  font-size: 12px;
}
.empty-state {
  color: var(--text-muted);
  padding: 20px 0;
  text-align: center;
}

.achievement-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 6px 0;
  font-size: 14px;
}
.ach-status {
  font-size: 12px;
  min-width: 80px;
}

:deep(.el-progress__text) {
  font-size: 11px !important;
  color: var(--text-muted) !important;
}
</style>