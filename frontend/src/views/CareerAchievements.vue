<template>
  <div class="achievements-page">
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
        <CareerSidebar current-page="achievements" />
      </template>
      <template #main>
        <div class="achievements-content">
          <!-- ===== 积分栏 ===== -->
          <div class="score-bar" ref="scoreBarRef">
            <span class="score-label">🏅 段位</span>
            <span class="score-value" ref="scoreRef">{{ userStats.points || 0 }}</span>
            <span class="score-divider">|</span>
            <span class="score-label">⭐ 等级</span>
            <span class="score-value level-score" ref="levelScoreRef">{{ userStats.level_points || 0 }}</span>
          </div>

          <h1>🐚 拾贝</h1>
          <p class="subtitle">学海拾贝，采撷成果</p>
          <el-divider />

          <div class="stats-bar">
            <span>已拾取：{{ doneCount }} / {{ totalCount }}</span>
            <el-progress
              :percentage="totalProgress"
              :color="totalProgress >= 80 ? '#6BCB77' : '#FFB74D'"
              :stroke-width="8"
              style="flex:1; max-width:300px;"
            />
          </div>

          <el-divider />

          <div class="achievement-grid">
            <div
              v-for="(ach, index) in achievements"
              :key="ach.id || index"
              class="ach-card"
              :class="{
                unlocked: ach.done,
                locked: !ach.done && !ach.ready,
                ready: ach.ready && !ach.done
              }"
              :style="{
                borderColor: ach._color + '40',
                background: ach.done || ach.ready
                  ? `rgba(${hexToRgb(ach._color)}, 0.08)`
                  : 'rgba(255,255,255,0.04)'
              }"
              @click="showDetail(ach)"
            >
              <div class="ach-icon">
                <img
                  :src="iconMap[ach.id]"
                  :alt="ach.name"
                  class="ach-icon-img"
                />
              </div>
              <div class="ach-name" :style="{ color: ach._color }">
                {{ ach.name }}
              </div>
              <div class="ach-condition">{{ ach.condition }}</div>
              <div class="ach-reward">+{{ ach.reward }}</div>
              <div class="ach-status">
                <span v-if="ach.done" style="color:#67c23a;">✅ 已拾取</span>
                <span v-else-if="ach.ready" style="color:#e6a23c;">🎁 可领取</span>
                <span v-else :style="{ color: ach._color + '80' }">⏳ 未达成</span>
              </div>
              <div class="ach-progress-wrap">
                <div class="progress-track">
                  <div
                    class="progress-fill"
                    :style="{
                      width: (ach.progress || 0) + '%',
                      background: `linear-gradient(90deg, ${ach._color}66, ${ach._color})`
                    }"
                  />
                </div>
                <span class="progress-label">{{ ach.progress || 0 }}%</span>
              </div>
              <el-button
                v-if="ach.ready && !ach.done"
                size="small"
                type="warning"
                class="claim-ach-btn active"
                :style="{
                  background: ach._color + '20 !important',
                  borderColor: ach._color + '40 !important',
                  color: ach._color + ' !important'
                }"
                @click.stop="claimAchievement(ach, $event)"
              >
                🎁 领取
              </el-button>
              <el-button
                v-else-if="ach.done"
                size="small"
                class="claim-ach-btn done"
                :style="{
                  color: ach._color + ' !important',
                  opacity: '0.5'
                }"
                disabled
              >
                ✅ 已领取
              </el-button>
            </div>
          </div>

          <div v-if="!achievements.length && !loading" class="empty-state">
            📭 暂无成就数据
          </div>
          <div v-if="loading" class="loading-state">⏳ 加载中...</div>
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

    <!-- ===== 毛玻璃成就详情弹窗 ===== -->
    <div v-if="detailVisible" class="glass-fullscreen" @click="detailVisible = false">
      <div class="glass-full-content glass-detail" @click.stop>
        <div class="glass-detail-icon">
          <img
            :src="iconMap[detailData?.id]"
            :alt="detailData?.name"
            class="detail-icon-img"
          />
        </div>
        <div class="glass-detail-name" :style="{ color: detailData?._color }">
          {{ detailData?.name }}
        </div>
        <div class="glass-detail-condition">{{ detailData?.condition }}</div>
        <div class="glass-detail-reward">🎁 +{{ detailData?.reward }} 收获</div>
        <div class="glass-detail-value">
          <span
            v-for="s in detailData?.value"
            :key="s"
            class="star"
            :style="{ color: getStarColor(detailData?.value) }"
          >★</span>
        </div>
        <div class="glass-detail-status">
          <span v-if="detailData?.done" style="color:#67c23a;">✅ 已拾取</span>
          <span v-else-if="detailData?.ready" style="color:#e6a23c;">🎁 可领取</span>
          <span v-else :style="{ color: detailData?._color + '80' }">⏳ 未达成</span>
        </div>
        <div v-if="detailData?.done && detailData?.unlock_time" class="glass-detail-time">
          📅 {{ formatDate(detailData.unlock_time) }}
        </div>
        <div class="glass-detail-progress">
          <div class="progress-track">
            <div
              class="progress-fill"
              :style="{
                width: (detailData?.progress || 0) + '%',
                background: `linear-gradient(90deg, ${detailData?._color}66, ${detailData?._color})`
              }"
            />
          </div>
          <span class="progress-label">{{ detailData?.progress || 0 }}%</span>
        </div>
        <el-button
          v-if="detailData?.ready && !detailData?.done"
          type="warning"
          class="claim-ach-btn active"
          :style="{
            background: detailData?._color + '20 !important',
            borderColor: detailData?._color + '40 !important',
            color: detailData?._color + ' !important'
          }"
          @click="claimAchievement(detailData)"
        >
          🎁 领取成就
        </el-button>
        <el-button
          v-else-if="detailData?.done"
          class="claim-ach-btn done"
          :style="{
            color: detailData?._color + ' !important',
            opacity: '0.5'
          }"
          disabled
        >
          ✅ 已领取
        </el-button>
        <div class="glass-detail-hint">点击外部关闭</div>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/AppLayout.vue'
import CareerSidebar from '@/components/CareerSidebar.vue'
import { getTaskProgress, recordAction, getUserStats } from '@/api/career'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()

// ===== 积分 =====
const userStats = ref({ points: 0, level_points: 0 })

// ===== 礼炮 =====
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

// ===== 成就 =====
const achievements = ref([])
const loading = ref(true)
const detailVisible = ref(false)
const detailData = ref(null)

// ===== 升级弹窗 =====
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
    setTimeout(() => {
      showUpgradeModal.value = false
    }, 3000)
  }
}

function closeUpgrade() {
  showUpgradeModal.value = false
}

const doneCount = computed(() => achievements.value.filter(a => a.done).length)
const totalCount = computed(() => achievements.value.length)
const totalProgress = computed(() => {
  if (!totalCount.value) return 0
  return Math.round((doneCount.value / totalCount.value) * 100)
})

// ===== 颜色 =====
const COLORS = [
  '#FF6B6B', '#FF8E53', '#FFB74D', '#FFD93D', '#A8E06C',
  '#6BCB77', '#4ECDC4', '#45B7D1', '#4A9FF5', '#7C6DF0',
  '#9B59B6', '#E040FB', '#EC407A', '#F06292', '#FF8A80',
  '#A1887F', '#90A4AE', '#26A69A', '#42A5F5', '#4CAF50',
  '#FFB300', '#FF6F00', '#9C27B0', '#FF6B6B', '#78909C'
]

// ===== 图标映射 =====
const iconMap = {
  "first_checkin": "/assets/achievements/Novice_ace.png",
  "checkin_7": "/assets/achievements/Accumulation_ace.png",
  "checkin_30": "/assets/achievements/Persistent_ace.png",
  "first_chat": "/assets/achievements/Boundless_ace.png",
  "first_plan": "/assets/achievements/Dreamer_ace.png",
  "first_generate": "/assets/achievements/Eloquent_ace.png",
  "first_evaluate": "/assets/achievements/Keen_ace.png",
  "questions_100": "/assets/achievements/Beat 100 Questions_ace.png",
  "questions_1000": "/assets/achievements/Fanatic_ace.png",
  "mistakes_10": "/assets/achievements/Hunter_ace.png",
  "mistakes_100": "/assets/achievements/Vanquisher_ace.png",
  "sets_5": "/assets/achievements/Collector_ace.png",
  "sets_20": "/assets/achievements/Pro_ace.png",
  "rank_mingli": "/assets/achievements/Prudent_ace.png",
  "rank_zhizhi": "/assets/achievements/Master Insight_ace.png",
  "rank_duxing": "/assets/achievements/Independent_ace.png",
  "rank_zhenjing": "/assets/achievements/Accomplished_ace.png",
  "legend": "/assets/achievements/Legend_ace.png",
  "share_10": "/assets/achievements/Sharer_ace.png",
  "study_7": "/assets/achievements/Time Management.ace.png",
  "timer_10h": "/assets/achievements/Valian_ace.png",
  "logs_50": "/assets/achievements/Learning Ace_ace.png",
  "report_10": "/assets/achievements/Hundred Blades_ace.png",
  "sets_50": "/assets/achievements/Master_ace.png",
  "messages_500": "/assets/achievements/Persevere_ace.png"
}

function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}` : '255,255,255'
}

function getStarColor(value) {
  const colors = {
    1: '#8B8B8B', 2: '#66CC66', 3: '#4CAF50',
    4: '#42A5F5', 5: '#FFD700', 6: '#FF9800',
    7: '#FF5722', 8: '#F44336', 9: '#9C27B0', 10: '#FFD700'
  }
  return colors[value] || '#888'
}

function formatDate(date) {
  if (!date) return '未知时间'
  try {
    const d = new Date(date)
    return d.toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit',
      day: '2-digit', hour: '2-digit', minute: '2-digit'
    })
  } catch { return date }
}

// ===== 礼炮动画 =====
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

      userStats.value.points += lastRank.value
      userStats.value.level_points += lastLevel.value

      setTimeout(() => {
        showGlass.value = true
        setTimeout(() => { showGlass.value = false }, 2000)
      }, 300)
    }
  }
  animId = requestAnimationFrame(step)
}

// ===== 加载数据 =====
async function loadData() {
  loading.value = true
  try {
    // ✅ 从 authStore 取 user
    const userId = authStore.user?.id
    console.log('🔍 authStore.user:', authStore.user)
    console.log('🔍 userId:', userId)

    if (!userId) {
      console.warn('❌ userId 为空')
      achievements.value = []
      loading.value = false
      return
    }

    const [data, stats] = await Promise.all([
      getTaskProgress(userId),
      getUserStats(userId)
    ])

    achievements.value = (data.achievements || []).map((a, index) => {
      const color = COLORS[index % COLORS.length]
      return {
        ...a,
        _color: color,
        progress: a.progress !== undefined ? a.progress : (a.done ? 100 : 0),
        ready: a.ready || false
      }
    })
    userStats.value = stats
  } catch (error) {
    console.error('加载成就失败:', error)
    achievements.value = []
  } finally {
    loading.value = false
  }
}

// ===== 领取成就 =====
async function claimAchievement(ach, event) {
  try {
    let startX = window.innerWidth / 2
    let startY = window.innerHeight / 2
    let targetBtn = event?.target
    if (targetBtn) {
      const rect = targetBtn.getBoundingClientRect()
      startX = rect.left + rect.width / 2
      startY = rect.top
    }

    const barRect = scoreBarRef.value?.getBoundingClientRect()
    const endX = barRect ? barRect.left + barRect.width - 30 : window.innerWidth - 100
    const endY = barRect ? barRect.top + barRect.height / 2 : 60

    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/career/achievement/claim`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({
        user_id: authStore.user.id,
        achievement_id: ach.id
      })
    })
    const result = await res.json()

    if (result.success) {
      lastRank.value = result.rank_points_gained || ach.reward
      lastLevel.value = result.level_points_gained || 0
      lastPoints.value = lastRank.value + lastLevel.value

      // 礼炮喷射
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

      await recordAction(authStore.user.id, 'claim_achievement')
      await loadData()
      detailVisible.value = false
    } else {
      ElMessage.error(result.message || '领取失败')
    }
  } catch (error) {
    console.error('领取失败:', error)
    ElMessage.error('领取失败，请稍后重试')
  }
}

function showDetail(ach) {
  detailData.value = ach
  detailVisible.value = true
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
.achievements-content {
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

.stats-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.stats-bar span { font-size: 16px; font-weight: 600; color: var(--text-primary); }

.achievement-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-top: 8px;
}

.ach-card {
  padding: 18px 14px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.10);
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
  position: relative;
}
[data-theme="dark"] .ach-card {
  background: rgba(0, 0, 0, 0.25);
  border-color: rgba(255, 255, 255, 0.06);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}

.ach-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.12);
  border-color: rgba(255, 255, 255, 0.20);
}
[data-theme="dark"] .ach-card:hover {
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4);
  border-color: rgba(255, 255, 255, 0.12);
}
.ach-card:active {
  transform: translateY(-2px) scale(0.98);
}

.ach-card.unlocked {
  box-shadow: 0 0 30px rgba(103, 194, 58, 0.06);
}
.ach-card.locked {
  opacity: 0.6;
}
.ach-card.locked:hover {
  opacity: 0.8;
}
.ach-card.ready {
  animation: readyPulse 2s ease-in-out infinite;
}
@keyframes readyPulse {
  0%, 100% { box-shadow: 0 0 20px rgba(230, 162, 60, 0.05); }
  50% { box-shadow: 0 0 40px rgba(230, 162, 60, 0.15); }
}
.ach-card.ready:hover {
  transform: translateY(-6px) scale(1.02);
}

.ach-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 4px;
}
.ach-icon-img {
  width: 52px;
  height: 52px;
  object-fit: contain;
  border-radius: 8px;
}
.ach-name {
  font-weight: 600;
  font-size: 15px;
  margin: 4px 0 2px;
}
.ach-condition {
  font-size: 12px;
  color: var(--text-muted);
}
.ach-reward {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin: 4px 0;
}
.ach-status { font-size: 12px; }

.ach-progress-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}
.ach-progress-wrap .progress-track {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: rgba(128, 128, 128, 0.15);
  overflow: hidden;
}
.ach-progress-wrap .progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.6s ease;
}
.ach-progress-wrap .progress-label {
  font-size: 11px;
  color: var(--text-muted);
  min-width: 32px;
  text-align: right;
}

.claim-ach-btn {
  margin-top: 8px;
  border-radius: 8px !important;
  width: 100%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  border: 1px solid transparent !important;
}
.claim-ach-btn.active:hover {
  transform: translateY(-3px) scale(1.03) !important;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.15) !important;
}
.claim-ach-btn.active:active {
  transform: translateY(0px) scale(0.97) !important;
}
.claim-ach-btn.done {
  cursor: not-allowed !important;
}

.empty-state, .loading-state {
  color: var(--text-muted);
  padding: 40px 0;
  text-align: center;
  font-size: 16px;
}

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
.glass-toast {
  max-width: 380px;
}

/* ===== 成就详情毛玻璃 ===== */
.glass-detail {
  max-width: 380px;
}
.glass-detail-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 4px;
}
.detail-icon-img {
  width: 64px;
  height: 64px;
  object-fit: contain;
  border-radius: 12px;
}
.glass-detail-name {
  font-size: 22px;
  font-weight: 700;
}
.glass-detail-condition {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
  margin: 4px 0;
}
.glass-detail-reward {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.6);
}
.glass-detail-value .star {
  font-size: 18px;
  letter-spacing: 2px;
}
.glass-detail-status {
  font-size: 14px;
  margin: 6px 0;
}
.glass-detail-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
}
.glass-detail-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 12px 0;
}
.glass-detail-progress .progress-track {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: rgba(128, 128, 128, 0.15);
  overflow: hidden;
}
.glass-detail-progress .progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}
.glass-detail-progress .progress-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  min-width: 40px;
}
.glass-detail-hint {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.15);
  margin-top: 8px;
}

@media (max-width: 640px) {
  .achievement-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 10px;
  }
  .ach-card { padding: 14px 10px; }
  .ach-icon-img { width: 40px; height: 40px; }
  .glass-full-content {
    padding: 28px 24px;
  }
  .glass-full-points {
    font-size: 32px;
  }
  .score-bar {
    font-size: 12px;
    padding: 8px 12px;
    top: 12px;
    right: 12px;
  }
  .score-value {
    font-size: 16px;
  }
}
</style>