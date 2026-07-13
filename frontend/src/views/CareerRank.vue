<template>
  <div class="rank-page">
    <AppLayout locked>
      <template #sidebar>
        <CareerSidebar current-page="rank" />
      </template>
      <template #main>
        <div class="rank-content">
          <h1>⛰️ 登攀</h1>
          <p class="subtitle">学如登山，步步高升</p>
          <el-divider />

          <!-- ===== 当前段位 ===== -->
          <div class="rank-card">
            <!-- 段位行 -->
            <div class="rank-main">
              <div class="rank-big" :style="{ color: rankColor }">
                {{ rankIcon }} {{ rankName }}
              </div>
              <div class="rank-sub-display" :style="{ color: rankColor }">
                {{ rankSubSymbol }} 小段 {{ subRankDisplay }}
              </div>
              <div class="rank-points-big">{{ points }} 分</div>
            </div>
            <div class="rank-progress-wrap">
              <div class="progress-track">
                <div
                  class="progress-fill"
                  :style="{
                    width: rankProgress + '%',
                    background: rankColor
                  }"
                />
              </div>
              <span class="hint">距离下一小段还需 {{ nextPoints }} 分</span>
            </div>

            <!-- 等级行（分开显示） -->
            <div class="level-divider"></div>
            <div class="level-main">
              <div class="level-label">Lv.{{ userLevel }}</div>
              <div class="level-points">{{ levelPoints }} 分</div>
            </div>
            <div class="level-progress-wrap">
              <div class="progress-track">
                <div
                  class="progress-fill blue"
                  :style="{
                    width: levelProgress + '%',
                    background: '#409eff'
                  }"
                />
              </div>
              <span class="hint">距离 Lv.{{ userLevel + 1 }} 还需 {{ nextLevelPoints }} 分</span>
            </div>
          </div>

          <el-divider />

          <!-- ===== 攀登足迹 ===== -->
          <h3>📜 攀登足迹</h3>
          <div v-if="rankHistory.length" class="history-grid">
            <div
              v-for="(h, idx) in rankHistory.slice(0, 6)"
              :key="idx"
              class="history-item"
            >
              <div class="history-date">{{ h.date?.slice(0, 10) }}</div>
              <div class="history-rank" :style="{ color: RANK_COLORS[h.rank] }">
                {{ h.rank }} {{ SUB_SYMBOLS[h.sub_rank] }}
              </div>
              <div class="history-level" v-if="h.level">
                Lv.{{ h.level }}
              </div>
              <div class="history-points">{{ h.points }} 分</div>
            </div>
          </div>
          <div v-else class="empty-state">📭 暂无攀登足迹，继续努力！</div>

          <el-divider />

          <!-- ===== 段位说明 ===== -->
          <div class="rank-info-wrapper">
            <div class="rank-info-header" @click="showRankInfo = !showRankInfo">
              <span>📖 段位说明</span>
              <i class="fas fa-chevron-down" :class="{ rotated: showRankInfo }"></i>
            </div>
            <div v-show="showRankInfo" class="rank-info-body">
              <div class="info-grid">
                <div class="info-card">
                  <h4>🎨 主题色</h4>
                  <div class="rank-table">
                    <div class="rank-row header">
                      <span>段位</span>
                      <span>符号</span>
                      <span>颜色</span>
                    </div>
                    <div
                      v-for="r in RANK_ORDER"
                      :key="r"
                      class="rank-row"
                    >
                      <span :style="{ color: RANK_COLORS[r] }">{{ r }}</span>
                      <span :style="{ color: RANK_COLORS[r] }">{{ RANK_ICONS[r] }}</span>
                      <span
                        class="color-dot"
                        :style="{ background: RANK_COLORS[r] }"
                      />
                    </div>
                  </div>
                </div>

                <div class="info-card">
                  <h4>🗺️ 山阶</h4>
                  <div class="rank-table">
                    <div class="rank-row header">
                      <span>段位</span>
                      <span>V</span>
                      <span>IV</span>
                      <span>III</span>
                      <span>II</span>
                      <span>I</span>
                    </div>
                    <div
                      v-for="r in RANK_ORDER"
                      :key="r"
                      class="rank-row"
                    >
                      <span :style="{ color: RANK_COLORS[r] }">{{ r }}</span>
                      <span :style="{ color: RANK_COLORS[r] }">○</span>
                      <span :style="{ color: RANK_COLORS[r] }">◌</span>
                      <span :style="{ color: RANK_COLORS[r] }">◎</span>
                      <span :style="{ color: RANK_COLORS[r] }">◍</span>
                      <span :style="{ color: RANK_COLORS[r] }">●</span>
                    </div>
                  </div>
                </div>

                <div class="info-card">
                  <h4>🔍 小段位</h4>
                  <div class="rank-table">
                    <div class="rank-row header">
                      <span>符号</span>
                      <span>小段位</span>
                      <span>含义</span>
                    </div>
                    <div class="rank-row">
                      <span style="font-size:16px; opacity:0.4;">○</span>
                      <span>V</span>
                      <span style="font-size:12px; color:var(--text-muted);">空环（起步）</span>
                    </div>
                    <div class="rank-row">
                      <span style="font-size:16px; opacity:0.4;">◌</span>
                      <span>IV</span>
                      <span style="font-size:12px; color:var(--text-muted);">半环（成长）</span>
                    </div>
                    <div class="rank-row">
                      <span style="font-size:16px; opacity:0.4;">◎</span>
                      <span>III</span>
                      <span style="font-size:12px; color:var(--text-muted);">双环（进步）</span>
                    </div>
                    <div class="rank-row">
                      <span style="font-size:16px; opacity:0.4;">◍</span>
                      <span>II</span>
                      <span style="font-size:12px; color:var(--text-muted);">实半环（将成）</span>
                    </div>
                    <div class="rank-row">
                      <span style="font-size:16px; opacity:0.4;">●</span>
                      <span>I</span>
                      <span style="font-size:12px; color:var(--text-muted);">实心环（圆满）</span>
                    </div>
                    <div class="rank-row">
                      <span style="font-size:16px; opacity:0.4;">★</span>
                      <span>—</span>
                      <span style="font-size:12px; color:var(--text-muted);">传说</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </AppLayout>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onDeactivated } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/AppLayout.vue'
import CareerSidebar from '@/components/CareerSidebar.vue'
import { getUserStats } from '@/api/career'
import { RANK_ICONS, RANK_COLORS, RANK_ORDER, SUB_SYMBOLS } from '@/utils/constants'

const router = useRouter()
const authStore = useAuthStore()

const showRankInfo = ref(false)
const stats = ref({ points: 0, level_points: 0, rank: '启程', sub_rank: 1, rank_history: [] })
const loading = ref(true)

const points = computed(() => stats.value.points || 0)
const levelPoints = computed(() => stats.value.level_points || 0)
const rank = computed(() => stats.value.rank || '启程')
const rankName = computed(() => rank.value)
const subRank = computed(() => stats.value.sub_rank || 1)
const subRankDisplay = computed(() => {
  const map = { 1: 'V', 2: 'IV', 3: 'III', 4: 'II', 5: 'I' }
  return map[subRank.value] || 'V'
})
const rankIcon = computed(() => RANK_ICONS[rank.value] || '◈')
const rankColor = computed(() => RANK_COLORS[rank.value] || '#888')
const rankSubSymbol = computed(() => SUB_SYMBOLS[subRank.value] || '○')
const rankHistory = computed(() => stats.value.rank_history || [])

const rankIndex = computed(() => RANK_ORDER.indexOf(rank.value) || 0)
const rankProgress = computed(() => {
  const base = rankIndex.value * 500
  const subStart = base + (subRank.value - 1) * 100
  const subEnd = base + subRank.value * 100
  return Math.min(Math.max(((points.value - subStart) / 100) * 100, 0), 100)
})
const nextPoints = computed(() => {
  const base = rankIndex.value * 500
  const subEnd = base + subRank.value * 100
  return subEnd - points.value
})

// ===== 等级计算（使用 level_points） =====
const userLevel = computed(() => {
  let level = 1
  let totalNeeded = 2
  const lp = levelPoints.value
  while (lp >= totalNeeded) {
    level++
    totalNeeded += (level + 1)
  }
  return level
})

const levelProgress = computed(() => {
  let used = 0
  const lp = levelPoints.value
  for (let i = 1; i < userLevel.value; i++) {
    used += (i + 1)
  }
  const currentProgress = lp - used
  const currentNeeded = userLevel.value + 1
  return Math.min(100, (currentProgress / currentNeeded) * 100)
})

const nextLevelPoints = computed(() => {
  let used = 0
  const lp = levelPoints.value
  for (let i = 1; i <= userLevel.value; i++) {
    used += (i + 1)
  }
  return used - lp
})

async function loadData() {
  loading.value = true
  try {
    stats.value = await getUserStats(authStore.user.id)
  } catch (error) {
    console.error('加载失败', error)
  } finally {
    loading.value = false
  }
}

let refreshTimer = null

// ===== 监听任务领取事件 =====
function handleTaskClaimed() {
  loadData()
}

onMounted(() => {
  loadData()
  // 定时刷新兜底
  refreshTimer = setInterval(loadData, 30000)
  // 监听任务领取事件（从 CareerTasks 触发）
  window.addEventListener('task-claimed', handleTaskClaimed)
})

onDeactivated(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  window.removeEventListener('task-claimed', handleTaskClaimed)
})
</script>

<style scoped>
.rank-content {
  padding: 8px 4px;
  max-width: 900px;
  margin: 0 auto;
}
h1 {
  font-size: 28px;
  color: var(--text-primary);
}
.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  opacity: 0.6;
}

/* ===== 段位卡片 ===== */
.rank-card {
  padding: 20px 24px;
  border-radius: 14px;
  border: 1px solid var(--border-color);
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(12px);
}

/* 段位行 */
.rank-main {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
.rank-big {
  font-size: 28px;
  font-weight: 700;
}
.rank-sub-display {
  font-size: 18px;
  font-weight: 500;
  opacity: 0.8;
}
.rank-points-big {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-left: auto;
}
.rank-progress-wrap {
  margin-top: 8px;
}
.progress-track {
  height: 6px;
  border-radius: 4px;
  background: rgba(128, 128, 128, 0.15);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}
.hint {
  font-size: 12px;
  color: var(--text-muted);
  display: block;
  margin-top: 2px;
}

/* 等级行（分开） */
.level-divider {
  height: 1px;
  background: var(--border-color);
  margin: 14px 0 12px;
  opacity: 0.5;
}
.level-main {
  display: flex;
  align-items: center;
  gap: 16px;
}
.level-label {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}
.level-points {
  font-size: 15px;
  color: var(--text-muted);
}
.level-progress-wrap {
  margin-top: 6px;
}
.progress-fill.blue {
  background: #409eff !important;
  box-shadow: 0 0 12px rgba(64, 158, 255, 0.3);
}

/* ===== 攀登足迹 ===== */
.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 10px;
  margin-top: 8px;
}
.history-item {
  padding: 10px 8px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  text-align: center;
  background: rgba(255,255,255,0.02);
  transition: all 0.3s ease;
}
.history-item:hover {
  transform: translateY(-2px);
  border-color: rgba(128,128,128,0.15);
}
.history-date {
  font-size: 10px;
  color: var(--text-muted);
}
.history-rank {
  font-size: 15px;
  font-weight: 600;
  margin: 2px 0;
}
.history-level {
  font-size: 11px;
  color: var(--text-secondary);
}
.history-points {
  font-size: 11px;
  color: var(--text-muted);
}
.empty-state {
  color: var(--text-muted);
  padding: 16px 0;
  text-align: center;
}

/* ===== 段位说明（自定义展开） ===== */
.rank-info-wrapper {
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: rgba(255,255,255,0.03);
  backdrop-filter: blur(8px);
  overflow: hidden;
}
.rank-info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.3s ease;
  user-select: none;
}
.rank-info-header:hover {
  color: var(--text-primary);
  background: rgba(255,255,255,0.04);
}
.rank-info-header i {
  transition: transform 0.3s ease;
  font-size: 13px;
  color: var(--text-muted);
}
.rank-info-header i.rotated {
  transform: rotate(180deg);
}

.rank-info-body {
  padding: 0 16px 16px;
}
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
}
.info-card {
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  background: rgba(255,255,255,0.02);
}
.info-card h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 6px 0;
}
.rank-table {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.rank-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(32px, 1fr));
  padding: 2px 4px;
  font-size: 12px;
  border-radius: 3px;
}
.rank-row.header {
  font-weight: 600;
  color: var(--text-muted);
  font-size: 10px;
}
.rank-row:hover {
  background: rgba(128, 128, 128, 0.03);
}
.color-dot {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 3px;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .info-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  .rank-main {
    gap: 12px;
  }
  .rank-big {
    font-size: 22px;
  }
  .rank-points-big {
    font-size: 17px;
    margin-left: 0;
  }
  .level-label {
    font-size: 17px;
  }
  .history-grid {
    grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  }
}
</style>