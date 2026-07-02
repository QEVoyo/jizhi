<template>
  <div class="rank-page">
    <AppLayout>
      <template #sidebar>
        <CareerSidebar />
      </template>
      <template #main>
        <div class="rank-content">
          <el-button text @click="goBack" class="back-btn">← 返回</el-button>
          <h1>⛰️ 登攀</h1>
          <p class="subtitle">学如登山，步步高升</p>
          <el-divider />

          <!-- 当前段位 -->
          <div class="rank-card">
            <div class="rank-main">
              <div class="rank-big" :style="{ color: rankColor }">
                {{ rankIcon }} {{ rank }} {{ subSymbol }}
              </div>
              <div class="rank-points-big">{{ points }} 分</div>
            </div>
            <div class="rank-progress-wrap">
              <el-progress :percentage="rankProgress" :color="rankColor" :stroke-width="10" />
              <span class="hint">距离下一小段还需 {{ nextPoints }} 分</span>
            </div>
          </div>

          <el-divider />

          <!-- 攀登足迹 -->
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
              <div class="history-points">{{ h.points }} 分</div>
            </div>
          </div>
          <div v-else class="empty-state">📭 暂无攀登足迹，继续努力！</div>

          <el-divider />

          <!-- ===== 段位说明（三栏） ===== -->
          <el-collapse>
            <el-collapse-item title="📖 段位说明">
              <div class="rank-info">
                <!-- 主题色 -->
                <div class="info-section">
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

                <!-- 山阶 -->
                <div class="info-section">
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

                <!-- 小段位 -->
                <div class="info-section">
                  <h4>🔍 小段位</h4>
                  <div class="rank-table">
                    <div class="rank-row header">
                      <span>符号</span>
                      <span>小段位</span>
                      <span>含义</span>
                    </div>
                    <div class="rank-row">
                      <span style="font-size:18px; opacity:0.4;">○</span>
                      <span>V</span>
                      <span style="color:var(--text-muted); font-size:13px;">空环（起步）</span>
                    </div>
                    <div class="rank-row">
                      <span style="font-size:18px; opacity:0.4;">◌</span>
                      <span>IV</span>
                      <span style="color:var(--text-muted); font-size:13px;">半环（成长）</span>
                    </div>
                    <div class="rank-row">
                      <span style="font-size:18px; opacity:0.4;">◎</span>
                      <span>III</span>
                      <span style="color:var(--text-muted); font-size:13px;">双环（进步）</span>
                    </div>
                    <div class="rank-row">
                      <span style="font-size:18px; opacity:0.4;">◍</span>
                      <span>II</span>
                      <span style="color:var(--text-muted); font-size:13px;">实半环（将成）</span>
                    </div>
                    <div class="rank-row">
                      <span style="font-size:18px; opacity:0.4;">●</span>
                      <span>I</span>
                      <span style="color:var(--text-muted); font-size:13px;">实心环（圆满）</span>
                    </div>
                    <div class="rank-row">
                      <span style="font-size:18px; opacity:0.4;">★</span>
                      <span>—</span>
                      <span style="color:var(--text-muted); font-size:13px;">传说</span>
                    </div>
                  </div>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
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
import { getUserStats } from '@/api/career'
import { RANK_ICONS, RANK_COLORS, RANK_ORDER, SUB_SYMBOLS } from '@/utils/constants'

const router = useRouter()
const authStore = useAuthStore()

const stats = ref({ points: 0, rank: '启程', sub_rank: 1, rank_history: [] })
const loading = ref(true)

const points = computed(() => stats.value.points || 0)
const rank = computed(() => stats.value.rank || '启程')
const subRank = computed(() => stats.value.sub_rank || 1)
const rankIcon = computed(() => RANK_ICONS[rank.value] || '◈')
const rankColor = computed(() => RANK_COLORS[rank.value] || '#888')
const subSymbol = computed(() => SUB_SYMBOLS[subRank.value] || '○')
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

function goBack() {
  router.push('/career')
}

onMounted(loadData)
</script>

<style scoped>
.rank-content {
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
}

.rank-card {
  padding: 24px 28px;
  border-radius: 16px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
}
.rank-main {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}
.rank-big {
  font-size: 32px;
  font-weight: 700;
}
.rank-points-big {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-secondary);
}
.rank-progress-wrap {
  margin-top: 16px;
}
.hint {
  font-size: 13px;
  color: var(--text-muted);
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
  margin-top: 8px;
}
.history-item {
  padding: 12px 8px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  text-align: center;
}
.history-date {
  font-size: 11px;
  color: var(--text-muted);
}
.history-rank {
  font-size: 16px;
  font-weight: 600;
  margin: 4px 0;
}
.history-points {
  font-size: 12px;
  color: var(--text-muted);
}

.rank-info {
  padding: 8px 0;
}
.info-section {
  margin-bottom: 20px;
}
.info-section:last-child {
  margin-bottom: 0;
}
.info-section h4 {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.rank-table {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.rank-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(50px, 1fr));
  padding: 4px 8px;
  font-size: 14px;
  border-radius: 4px;
}
.rank-row.header {
  font-weight: 600;
  color: var(--text-muted);
  font-size: 12px;
}
.rank-row:hover {
  background: rgba(128, 128, 128, 0.03);
}
.color-dot {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 4px;
}
.empty-state {
  color: var(--text-muted);
  padding: 16px 0;
}
</style>