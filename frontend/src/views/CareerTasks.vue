<template>
  <div class="tasks-page">
    <!-- ===== 左下角礼炮喷射 ===== -->
    <div
      v-for="p in leftBurst"
      :key="'lp-' + p.id"
      class="burst-item"
      :style="{
        position: 'fixed',
        left: p.x + 'px',
        top: p.y + 'px',
        opacity: p.opacity,
        color: p.color,
        fontSize: p.size + 'px',
        zIndex: 999,
        pointerEvents: 'none',
        transform: `rotate(${p.rot}deg)`,
      }"
    >
      {{ p.icon }}
    </div>

    <!-- ===== 右下角礼炮喷射 ===== -->
    <div
      v-for="p in rightBurst"
      :key="'rp-' + p.id"
      class="burst-item"
      :style="{
        position: 'fixed',
        left: p.x + 'px',
        top: p.y + 'px',
        opacity: p.opacity,
        color: p.color,
        fontSize: p.size + 'px',
        zIndex: 999,
        pointerEvents: 'none',
        transform: `rotate(${p.rot}deg)`,
      }"
    >
      {{ p.icon }}
    </div>

    <!-- ===== 闪光 ===== -->
    <div v-if="flash" class="flash-overlay" :style="{ opacity: flashOpacity }" />

    <!-- ===== 金币 ===== -->
    <div
      v-if="flying"
      class="coin-fly"
      :style="{
        left: coinX + 'px',
        top: coinY + 'px',
        opacity: coinOpacity,
        transform: `scale(${coinScale}) rotate(${coinRotate}deg)`,
      }"
    >
      🪙
    </div>

    <AppLayout locked>
      <template #sidebar>
        <CareerSidebar current-page="tasks" />
      </template>
      <template #main>
        <div class="tasks-content">
          <!-- ===== 积分栏 ===== -->
          <div class="score-bar" ref="scoreBarRef">
            <span class="score-label">🏅 段位</span>
            <span class="score-value" ref="scoreRef">{{ userStats.points || 0 }}</span>
            <span class="score-divider">|</span>
            <span class="score-label">⭐ 等级</span>
            <span class="score-value level-score" ref="levelScoreRef">{{ userStats.level_points || 0 }}</span>
          </div>

          <h1>🌾 勤耕</h1>
          <p class="subtitle">日积月累，勤耕不辍</p>

          <el-divider />

          <LoadingSpinner
            v-if="loading"
            variant="flow"
            :flow-steps="['正在同步任务数据...', '正在检查完成状态...', '正在整理成就列表...', '马上就好...']"
          />

          <!-- ===== 播种 ===== -->
          <div class="task-section">
            <h2>🌰 播种</h2>
            <p class="subtitle">新手引导 · 第一次使用各项功能</p>
            <div class="task-table" v-if="seedTasks.length">
              <div class="task-row header">
                <span>状态</span>
                <span>种子</span>
                <span>收获</span>
                <span>价值</span>
                <span>进度</span>
                <span>操作</span>
              </div>
              <div class="task-row" v-for="(task, idx) in seedTasks" :key="idx">
                <span class="status-icon">
                  <el-icon v-if="task.done" color="#67c23a"><Check /></el-icon>
                  <el-icon v-else-if="task.ready" color="#e6a23c"><Present /></el-icon>
                  <el-icon v-else color="#909399"><Clock /></el-icon>
                </span>
                <span class="task-name">{{ task.name }}</span>
                <span class="task-reward">+{{ task.reward || 0 }}</span>
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
                <span class="task-action">
                  <el-button
                    v-if="task.ready && !task.done"
                    size="small"
                    type="warning"
                    class="claim-btn"
                    @click.stop="claimTask(task, $event)"
                  >
                    🎁 领取
                  </el-button>
                  <span v-else-if="task.done" class="claimed-text">✅ 已领取</span>
                  <span v-else class="pending-text">⏳ 进行中</span>
                </span>
              </div>
            </div>
            <div v-else class="empty-state">暂无播种任务</div>
          </div>

          <el-divider />

          <!-- ===== 施肥 ===== -->
          <div class="task-section">
            <div class="section-header-wrap">
              <h2>🌱 施肥</h2>
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
                <span>状态</span>
                <span>肥料</span>
                <span>收获</span>
                <span>价值</span>
                <span>进度</span>
                <span>操作</span>
              </div>
              <div class="task-row" v-for="(task, idx) in displayDaily" :key="idx">
                <span class="status-icon">
                  <el-icon v-if="task.done" color="#67c23a"><Check /></el-icon>
                  <el-icon v-else-if="task.ready" color="#e6a23c"><Present /></el-icon>
                  <el-icon v-else color="#909399"><Clock /></el-icon>
                </span>
                <span class="task-name">{{ task.name }}</span>
                <span class="task-reward">+{{ task.reward || 0 }}</span>
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
                <span class="task-action">
                  <el-button
                    v-if="task.ready && !task.done"
                    size="small"
                    type="warning"
                    class="claim-btn"
                    @click.stop="claimTask(task, $event)"
                  >
                    🎁 领取
                  </el-button>
                  <span v-else-if="task.done" class="claimed-text">✅ 已领取</span>
                  <span v-else class="pending-text">⏳ 进行中</span>
                </span>
              </div>
            </div>
            <div v-else class="empty-state">暂无每日任务</div>

            <!-- 全部完成奖励 -->
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
                @click="claimBonus($event)"
              >
                🎁 领取
              </el-button>
              <el-button v-else size="small" disabled class="claim-btn done">
                ✅ 已领取
              </el-button>
            </div>
          </div>

          <el-divider />

          <!-- ===== 发芽 ===== -->
          <div class="task-section">
            <div class="section-header-wrap">
              <h2>🌿 发芽</h2>
              <span class="task-count">{{ longTasks.filter(t => t.done).length }} / {{ longTasks.length }} 完成</span>
            </div>
            <p class="subtitle">长期耕耘 · 持续积累 · 阶梯解锁</p>
            <div class="task-table" v-if="longTasks.length">
              <div class="task-row header">
                <span>状态</span>
                <span>扎根</span>
                <span>收获</span>
                <span>价值</span>
                <span>进度</span>
                <span>操作</span>
              </div>
              <div class="task-row" v-for="(task, idx) in longTasks" :key="idx">
                <span class="status-icon">
                  <el-icon v-if="task.done" color="#67c23a"><Check /></el-icon>
                  <el-icon v-else-if="task.ready" color="#e6a23c"><Present /></el-icon>
                  <el-icon v-else-if="task.locked" color="#909399"><Lock /></el-icon>
                  <el-icon v-else color="#909399"><Clock /></el-icon>
                </span>
                <span class="task-name" :class="{ locked: task.locked }">{{ task.name }}</span>
                <span class="task-reward">+{{ task.reward || 0 }}</span>
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
                          background: task.locked ? '#555' : getProgressColor(task.progress)
                        }"
                      />
                    </div>
                    <span class="progress-label">{{ task.locked ? '🔒' : task.progress + '%' }}</span>
                  </div>
                </span>
                <span class="task-action">
                  <el-button
                    v-if="task.ready && !task.done && !task.locked"
                    size="small"
                    type="warning"
                    class="claim-btn"
                    @click.stop="claimTask(task, $event)"
                  >
                    🎁 领取
                  </el-button>
                  <span v-else-if="task.done" class="claimed-text">✅ 已领取</span>
                  <span v-else-if="task.locked" class="locked-text">🔒 未解锁</span>
                  <span v-else class="pending-text">⏳ 进行中</span>
                </span>
              </div>
            </div>
            <div v-else class="empty-state">暂无发芽任务</div>
          </div>

          <el-divider />

          <!-- ===== 丰收 ===== -->
          <div class="task-section">
            <h2>🌾 丰收</h2>
            <p class="subtitle">最接近完成的成就 · 加把劲就能收获</p>
            <div v-if="pendingAchievements.length" class="achievement-list">
              <div
                v-for="ach in pendingAchievements.slice(0, 8)"
                :key="ach.id"
                class="ach-row"
              >
                <div
                  class="ach-icon"
                  :style="{ color: ach.done ? ach.themeColor : '#555' }"
                >
                  <i :class="getIcon(ach.id)"></i>
                </div>
                <div class="ach-info">
                  <span class="ach-name">{{ ach.name }}</span>
                  <span class="ach-condition">{{ ach.condition }}</span>
                </div>
                <span class="ach-status">
                  <span v-if="ach.done">✅ 已拾取</span>
                  <span v-else-if="ach.ready" style="color:#e6a23c;">🎁 可领取</span>
                  <span v-else>⏳ 未解锁</span>
                </span>
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

            <el-button class="view-all-btn" @click="goAchievements">
              📋 查看全部成就 →
            </el-button>
          </div>
        </div>
      </template>
    </AppLayout>

    <!-- ===== 毛玻璃升级弹窗 ===== -->
    <div v-if="showUpgradeModal" class="glass-fullscreen" @click="closeUpgrade">
      <div class="glass-full-content glass-upgrade">
        <div class="glass-full-icon">{{ upgradeIcon }}</div>
        <div class="glass-full-title">{{ upgradeTitle }}</div>
        <div class="glass-full-text">{{ upgradeText }}</div>
        <div v-if="upgradeOldRank" class="glass-full-rank">
          {{ upgradeOldRank }} {{ upgradeOldSub }} → {{ upgradeNewRank }} {{ upgradeNewSub }}
        </div>
        <div v-if="upgradeOldLevel" class="glass-full-level">
          Lv.{{ upgradeOldLevel }} → Lv.{{ upgradeNewLevel }}
        </div>
        <div class="glass-full-points">+{{ upgradePoints }}</div>
        <div class="glass-full-hint">点击任意处关闭</div>
      </div>
    </div>

    <!-- ===== 毛玻璃通知 ===== -->
    <div v-if="showGlass" class="glass-fullscreen" @click="showGlass = false">
      <div class="glass-full-content glass-toast">
        <div class="glass-full-icon">🎊</div>
        <div class="glass-full-title">领取成功！</div>
        <div class="glass-full-points">+{{ lastPoints }}</div>
        <div class="glass-full-detail">
          段位 <span class="highlight-gold">+{{ lastRank }}</span>
          ·
          等级 <span class="highlight-green">+{{ lastLevel }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/AppLayout.vue'
import CareerSidebar from '@/components/CareerSidebar.vue'
import { getTaskProgress, getUserStats } from '@/api/career'
import { ElMessage } from 'element-plus'
import { Check, Present, Clock, Lock } from '@element-plus/icons-vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const router = useRouter()
const authStore = useAuthStore()

const taskData = ref({ seed: [], daily: [], long: [], achievements: [] })
const loading = ref(true)
const refreshUsed = ref(false)
const bonusClaimed = ref(false)

// ===== 用户积分 =====
const userStats = ref({ points: 0, level_points: 0 })

// ===== 礼炮喷射 =====
const leftBurst = ref([])
const rightBurst = ref([])
const flash = ref(false)
const flashOpacity = ref(0)
const flying = ref(false)
const showGlass = ref(false)

const coinX = ref(0)
const coinY = ref(0)
const coinOpacity = ref(1)
const coinScale = ref(0.3)
const coinRotate = ref(0)

const lastPoints = ref(0)
const lastRank = ref(0)
const lastLevel = ref(0)

const scoreBarRef = ref(null)
const scoreRef = ref(null)
const levelScoreRef = ref(null)

let animId = null
let timer = null
let burstAnimId = null

// ===== 毛玻璃升级弹窗 =====
const showUpgradeModal = ref(false)
const upgradeTitle = ref('🎉 升级啦！')
const upgradeIcon = ref('🚀')
const upgradeText = ref('')
const upgradePoints = ref(0)
const upgradeOldRank = ref('')
const upgradeNewRank = ref('')
const upgradeOldSub = ref('')
const upgradeNewSub = ref('')
const upgradeOldLevel = ref(0)
const upgradeNewLevel = ref(0)

function showUpgrade(result) {
  let hasUpgrade = false
  if (result.rank_up) {
    hasUpgrade = true
    upgradeTitle.value = '🏆 段位晋升！'
    upgradeIcon.value = '🏆'
    upgradeText.value = `从「${result.old_rank}」晋升到「${result.new_rank}」`
    upgradeOldRank.value = result.old_rank
    upgradeNewRank.value = result.new_rank
    const subMap = { 1: 'V', 2: 'IV', 3: 'III', 4: 'II', 5: 'I' }
    upgradeOldSub.value = subMap[result.old_sub_rank] || ''
    upgradeNewSub.value = subMap[result.new_sub_rank] || ''
  }
  if (result.level_up) {
    hasUpgrade = true
    if (!result.rank_up) {
      upgradeTitle.value = '📈 等级提升！'
      upgradeIcon.value = '📈'
      upgradeText.value = `Lv.${result.old_level} → Lv.${result.new_level}`
    }
    upgradeOldLevel.value = result.old_level
    upgradeNewLevel.value = result.new_level
  }
  if (hasUpgrade) {
    upgradePoints.value = result.points_gained || 0
    showUpgradeModal.value = true
    // 2秒后自动关闭
    setTimeout(() => {
      showUpgradeModal.value = false
    }, 2500)
  }
}

function closeUpgrade() {
  showUpgradeModal.value = false
}

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

function getStarColor(value) {
  const colors = {
    1: '#8B8B8B', 2: '#66CC66', 3: '#4CAF50',
    4: '#42A5F5', 5: '#FFD700', 6: '#FF9800',
    7: '#FF5722', 8: '#F44336', 9: '#9C27B0', 10: '#FFD700'
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

// ===== 礼炮喷射动画 =====
function fireLeft() {
  const items = []
  const icons = ['✦', '✧', '✦', '✧', '✦', '✧', '✦', '✧']
  const colors = ['#FFD700', '#FF6B6B', '#FF1493', '#00BFFF', '#FFA500', '#FF4500', '#FFD700', '#7B68EE']

  const cx = 0
  const cy = window.innerHeight * 0.75

  for (let i = 0; i < 25; i++) {
    const angle = -0.3 + Math.random() * 1.2
    const dist = 80 + Math.random() * 450
    items.push({
      id: Math.random(),
      x: cx + Math.random() * 30,
      y: cy - 20 + Math.random() * 40,
      targetX: cx + Math.cos(angle) * dist,
      targetY: cy + Math.sin(angle) * dist * 0.7 - 200,
      opacity: 1,
      color: colors[Math.floor(Math.random() * colors.length)],
      size: 14 + Math.random() * 24,
      icon: icons[Math.floor(Math.random() * icons.length)],
      rot: Math.random() * 360,
    })
  }

  leftBurst.value = items
}

function fireRight() {
  const items = []
  const icons = ['✦', '✧', '✦', '✧', '✦', '✧', '✦', '✧']
  const colors = ['#FFD700', '#FF6B6B', '#FF1493', '#00BFFF', '#FFA500', '#FF4500', '#FFD700', '#7B68EE']

  const cx = window.innerWidth
  const cy = window.innerHeight * 0.75

  for (let i = 0; i < 25; i++) {
    const angle = Math.PI - 0.3 + Math.random() * 1.2
    const dist = 80 + Math.random() * 450
    items.push({
      id: Math.random(),
      x: cx - Math.random() * 30,
      y: cy - 20 + Math.random() * 40,
      targetX: cx + Math.cos(angle) * dist,
      targetY: cy + Math.sin(angle) * dist * 0.7 - 200,
      opacity: 1,
      color: colors[Math.floor(Math.random() * colors.length)],
      size: 14 + Math.random() * 24,
      icon: icons[Math.floor(Math.random() * icons.length)],
      rot: Math.random() * 360,
    })
  }

  rightBurst.value = items
}

function animateBurst() {
  const dur = 900
  const start = performance.now()

  function step(time) {
    const p = Math.min((time - start) / dur, 1)
    const ease = p

    leftBurst.value = leftBurst.value
      .map(item => ({
        ...item,
        x: item.x + (item.targetX - item.x) * 0.05,
        y: item.y + (item.targetY - item.y) * 0.05,
        opacity: 1 - ease * 0.7,
        rot: item.rot + 3,
      }))
      .filter(item => item.opacity > 0.05)

    rightBurst.value = rightBurst.value
      .map(item => ({
        ...item,
        x: item.x + (item.targetX - item.x) * 0.05,
        y: item.y + (item.targetY - item.y) * 0.05,
        opacity: 1 - ease * 0.7,
        rot: item.rot + 3,
      }))
      .filter(item => item.opacity > 0.05)

    if (p < 1 && (leftBurst.value.length > 0 || rightBurst.value.length > 0)) {
      burstAnimId = requestAnimationFrame(step)
    } else {
      leftBurst.value = []
      rightBurst.value = []
      burstAnimId = null
    }
  }
  burstAnimId = requestAnimationFrame(step)
}

function flyCoin(sx, sy, ex, ey) {
  flying.value = true
  coinX.value = sx - 20
  coinY.value = sy - 20
  coinOpacity.value = 1
  coinScale.value = 0.3
  coinRotate.value = 0

  const dur = 600
  const start = performance.now()

  function step(time) {
    const p = Math.min((time - start) / dur, 1)
    const ease = p

    const arc = Math.sin(p * Math.PI) * 50
    coinX.value = sx + (ex - sx) * ease - 20
    coinY.value = sy + (ey - sy) * ease - arc - 20
    coinScale.value = 0.3 + ease * 0.8
    coinRotate.value = p * 720

    if (p < 1) {
      animId = requestAnimationFrame(step)
    } else {
      flying.value = false
      coinOpacity.value = 0

      // 闪光
      flash.value = true
      flashOpacity.value = 1
      let fp = 0
      const fstart = performance.now()
      function flashStep(t) {
        fp = (t - fstart) / 400
        if (fp >= 1) { flash.value = false; flashOpacity.value = 0; return }
        flashOpacity.value = 1 - fp
        requestAnimationFrame(flashStep)
      }
      requestAnimationFrame(flashStep)

      // 积分跳动
      if (scoreRef.value) {
        scoreRef.value.style.transform = 'scale(1.5)'
        scoreRef.value.style.color = '#FFD700'
        setTimeout(() => {
          if (scoreRef.value) {
            scoreRef.value.style.transform = 'scale(1)'
            scoreRef.value.style.color = ''
          }
        }, 300)
      }
      if (levelScoreRef.value) {
        levelScoreRef.value.style.transform = 'scale(1.5)'
        levelScoreRef.value.style.color = '#6BCB77'
        setTimeout(() => {
          if (levelScoreRef.value) {
            levelScoreRef.value.style.transform = 'scale(1)'
            levelScoreRef.value.style.color = ''
          }
        }, 300)
      }

      // 更新积分
      userStats.value.points += lastRank.value
      userStats.value.level_points += lastLevel.value

      // 毛玻璃通知
      setTimeout(() => {
        showGlass.value = true
        setTimeout(() => { showGlass.value = false }, 2000)
      }, 300)
    }
  }
  animId = requestAnimationFrame(step)
}

// ===== 领取任务 =====
async function claimTask(task, event) {
  const btn = event?.target?.closest?.('.claim-btn') || event?.target
  const btnRect = btn?.getBoundingClientRect?.()
  const barRect = scoreBarRef.value?.getBoundingClientRect()

  if (!btnRect || !barRect) {
    ElMessage.error('页面加载中，请稍后重试')
    return
  }

  const startX = btnRect.left + btnRect.width / 2
  const startY = btnRect.top + btnRect.height / 2
  const endX = barRect.left + barRect.width - 30
  const endY = barRect.top + barRect.height / 2

  try {
    let taskType = 'seed'
    const isDaily = displayDaily.value.some(t => t.name === task.name)
    const isLong = longTasks.value.some(t => t.name === task.name)
    if (isDaily) {
      taskType = 'daily'
    } else if (isLong) {
      taskType = 'long'
    }

    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/career/task/claim`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({
        user_id: authStore.user.id,
        task_id: task.id || task.name,
        task_type: taskType
      })
    })
    const result = await res.json()

    if (result.success) {
      lastRank.value = result.rank_points_gained || 0
      lastLevel.value = result.level_points_gained || 0
      lastPoints.value = lastRank.value + lastLevel.value

      // 礼炮喷射
      fireLeft()
      fireRight()
      animateBurst()

      // 1秒后金币飞出
      timer = setTimeout(() => {
        leftBurst.value = []
        rightBurst.value = []
        flyCoin(startX, startY, endX, endY)
      }, 1000)

      // 升级弹窗在金币飞完后显示
      if (result.rank_up || result.level_up) {
        setTimeout(() => {
          showUpgrade(result)
        }, 2000)
      }

      await loadData()
      window.dispatchEvent(new CustomEvent('task-claimed'))

    } else {
      ElMessage.error(result.message || '领取失败')
    }
  } catch (error) {
    console.error('领取失败:', error)
    ElMessage.error('领取失败，请稍后重试')
  }
}

// ===== 领取每日全部奖励 =====
async function claimBonus(event) {
  const btn = event?.target
  const btnRect = btn?.getBoundingClientRect?.()
  const barRect = scoreBarRef.value?.getBoundingClientRect()

  if (!btnRect || !barRect) {
    ElMessage.error('页面加载中，请稍后重试')
    return
  }

  const startX = btnRect.left + btnRect.width / 2
  const startY = btnRect.top + btnRect.height / 2
  const endX = barRect.left + barRect.width - 30
  const endY = barRect.top + barRect.height / 2

  try {
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/career/bonus/claim`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({ user_id: authStore.user.id })
    })
    const result = await res.json()

    if (result.success) {
      lastRank.value = result.rank_points_gained || 20
      lastLevel.value = result.level_points_gained || 30
      lastPoints.value = lastRank.value + lastLevel.value

      fireLeft()
      fireRight()
      animateBurst()

      timer = setTimeout(() => {
        leftBurst.value = []
        rightBurst.value = []
        flyCoin(startX, startY, endX, endY)
      }, 1000)

      if (result.rank_up || result.level_up) {
        setTimeout(() => {
          showUpgrade(result)
        }, 2000)
      }

      bonusClaimed.value = true
      await loadData()
      window.dispatchEvent(new CustomEvent('task-claimed'))

    } else {
      ElMessage.error(result.message || '领取失败')
    }
  } catch (error) {
    console.error('领取失败:', error)
    ElMessage.error('领取失败，请稍后重试')
  }
}

async function handleRefreshDaily() {
  if (refreshUsed.value) {
    ElMessage.warning('今日已更换过任务')
    return
  }
  refreshUsed.value = true
  refreshDailyTasks()
  ElMessage.success('🔄 任务已更换')
}

async function loadData() {
  loading.value = true
  try {
    const [progress, stats] = await Promise.all([
      getTaskProgress(authStore.user.id),
      getUserStats(authStore.user.id)
    ])
    taskData.value = progress
    userStats.value = stats
    selectDailyTasks()
  } catch (error) {
    ElMessage.error('加载任务失败')
  } finally {
    loading.value = false
  }
}

watch(allDailyTasks, () => {
  selectDailyTasks()
}, { deep: true })

function goAchievements() {
  router.push('/career/achievements')
}

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId)
  if (burstAnimId) cancelAnimationFrame(burstAnimId)
  if (timer) clearTimeout(timer)
})
</script>

<style scoped>
.tasks-content {
  padding: 8px 4px;
  max-width: 1000px;
  margin: 0 auto;
}

/* ===== 积分栏 ===== */
.score-bar {
  position: fixed;
  top: 20px;
  right: 24px;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}
.score-label {
  font-size: 13px;
}
.score-value {
  color: #FFD700;
  font-size: 20px;
  font-weight: 700;
  transition: all 0.3s ease;
  min-width: 28px;
}
.score-value.level-score {
  color: #6BCB77;
}
.score-divider {
  opacity: 0.15;
}

h1 { font-size: 28px; color: var(--text-primary); }
.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  opacity: 0.6;
}

.task-section {
  background: rgba(255,255,255,0.03);
  backdrop-filter: blur(12px);
  border-radius: 14px;
  padding: 20px 24px;
  border: 1px solid var(--border-color);
  margin-bottom: 8px;
}

.section-header-wrap {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.section-header-wrap h2 { font-size: 20px; margin: 0; color: var(--text-primary); }
.section-actions { display: flex; align-items: center; gap: 8px; }
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
  grid-template-columns: 50px 1fr 60px 70px 1fr 100px;
  gap: 8px;
  align-items: center;
  padding: 6px 8px;
  border-radius: 8px;
  font-size: 14px;
}
.task-row.header { font-weight: 600; color: var(--text-muted); font-size: 12px; }
.task-row:hover { background: rgba(128,128,128,0.04); }
.status-icon { display: flex; justify-content: center; }
.task-name { color: var(--text-primary); }
.task-name.locked { color: var(--text-muted); opacity: 0.5; }
.task-reward { color: var(--text-secondary); }
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

.task-action {
  display: flex;
  justify-content: center;
}
.claim-btn {
  transition: all 0.3s ease !important;
  border-radius: 8px !important;
}
.claim-btn:hover { transform: translateY(-2px) scale(1.03) !important; }
.claim-btn.done { opacity: 0.5; cursor: not-allowed; }
.claimed-text { color: #67c23a; font-size: 13px; }
.pending-text { color: var(--text-muted); font-size: 13px; }
.locked-text { color: #909399; font-size: 13px; }

.bonus-row {
  display: grid;
  grid-template-columns: 50px 1fr 60px 70px 1fr 100px;
  gap: 8px;
  align-items: center;
  padding: 10px 8px;
  margin-top: 12px;
  border-radius: 8px;
  background: rgba(255,215,0,0.06);
  border: 1px solid rgba(255,215,0,0.12);
}
.bonus-label { font-weight: 600; color: var(--text-primary); }
.bonus-reward { color: #FFB300; font-weight: 600; }

.achievement-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
}
.ach-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  border-radius: 8px;
  transition: all 0.3s ease;
}
.ach-row:hover { background: rgba(128,128,128,0.04); }
.ach-icon { font-size: 18px; width: 28px; text-align: center; }
.ach-info { flex: 1; }
.ach-name { font-size: 13px; color: var(--text-primary); }
.ach-condition { font-size: 11px; color: var(--text-muted); }
.ach-status { font-size: 12px; min-width: 70px; }
.ach-progress { flex: 1; max-width: 100px; }
.ach-progress .progress-track { height: 4px; }

.empty-state {
  color: var(--text-muted);
  padding: 16px 0;
  text-align: center;
}

.view-all-btn {
  margin-top: 16px;
  width: 100%;
  border: 1px solid var(--border-color) !important;
  border-radius: 10px !important;
  background: transparent !important;
  color: var(--text-secondary) !important;
  transition: all 0.3s ease !important;
}
.view-all-btn:hover { transform: translateY(-2px) scale(1.02) !important; }

/* ===== 喷射粒子 ===== */
.burst-item {
  font-weight: 300;
  text-shadow: 0 0 20px currentColor;
}

/* ===== 闪光 ===== */
.flash-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: radial-gradient(circle, rgba(255,255,255,0.5), rgba(255,215,0,0.1));
  pointer-events: none;
}

/* ===== 金币 ===== */
.coin-fly {
  position: fixed;
  z-index: 20;
  pointer-events: none;
  font-size: 48px;
  filter: drop-shadow(0 0 30px rgba(255,215,0,0.5));
}

/* ===== 毛玻璃通用 ===== */
.glass-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  animation: fadeIn 0.4s ease;
}
@keyframes fadeIn {
  0% { opacity: 0; backdrop-filter: blur(0); }
  100% { opacity: 1; backdrop-filter: blur(8px); }
}

.glass-full-content {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 32px;
  padding: 40px 56px;
  text-align: center;
  max-width: 420px;
  width: 90%;
  box-shadow: 0 8px 80px rgba(0, 0, 0, 0.6);
  animation: popIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}
@keyframes popIn {
  0% { transform: scale(0.8); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

.glass-full-icon {
  font-size: 48px;
  margin-bottom: 4px;
}
.glass-full-title {
  font-size: 20px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}
.glass-full-text {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
}
.glass-full-rank {
  font-size: 16px;
  color: #FFD700;
  margin-top: 4px;
}
.glass-full-level {
  font-size: 16px;
  color: #6BCB77;
  margin-top: 2px;
}
.glass-full-points {
  font-size: 40px;
  font-weight: 900;
  background: linear-gradient(135deg, #FFD700, #FF6B00);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-top: 4px;
}
.glass-full-detail {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 6px;
}
.glass-full-hint {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.2);
  margin-top: 12px;
}
.highlight-gold {
  color: #FFD700;
  font-weight: 600;
}
.highlight-green {
  color: #6BCB77;
  font-weight: 600;
}

/* ===== 毛玻璃通知单独样式 ===== */
.glass-toast {
  max-width: 380px;
}

@media (max-width: 768px) {
  .task-row {
    grid-template-columns: 40px 1fr 50px 50px 1fr 80px;
    font-size: 12px;
    gap: 4px;
  }
  .bonus-row {
    grid-template-columns: 40px 1fr 50px 50px 1fr 80px;
    font-size: 12px;
  }
  .score-bar {
    font-size: 12px;
    padding: 8px 12px;
    flex-wrap: wrap;
    top: 12px;
    right: 12px;
  }
  .score-value {
    font-size: 16px;
  }
  .glass-full-content {
    padding: 28px 24px;
  }
  .glass-full-points {
    font-size: 32px;
  }
}
</style>