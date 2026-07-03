<template>
  <div class="achievements-page">
    <AppLayout locked>
      <template #sidebar>
        <CareerSidebar current-page="achievements" />
      </template>
      <template #main>
        <div class="achievements-content">
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
              <div
                class="ach-icon"
                :style="{
                  color: ach._color
                }"
              >
                <el-icon :size="36">
                  <component :is="ach._icon || Trophy" />
                </el-icon>
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
                @click.stop="claimAchievement(ach)"
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

    <el-dialog
      v-model="detailVisible"
      :title="detailData?.name || '成就详情'"
      width="420px"
      class="ach-detail-dialog"
      destroy-on-close
      :close-on-click-modal="true"
    >
      <div v-if="detailData" class="detail-content">
        <div
          class="detail-icon"
          :style="{ color: detailData._color }"
        >
          <el-icon :size="56">
            <component :is="detailData._icon || Trophy" />
          </el-icon>
        </div>
        <div class="detail-name" :style="{ color: detailData._color }">
          {{ detailData.name }}
        </div>
        <div class="detail-condition">{{ detailData.condition }}</div>
        <div class="detail-reward">🎁 +{{ detailData.reward }} 收获</div>
        <div class="detail-value">
          <span
            v-for="s in detailData.value"
            :key="s"
            class="star"
            :style="{ color: getStarColor(detailData.value) }"
          >★</span>
        </div>
        <div class="detail-status">
          <span v-if="detailData.done" style="color:#67c23a;">✅ 已拾取</span>
          <span v-else-if="detailData.ready" style="color:#e6a23c;">🎁 可领取</span>
          <span v-else :style="{ color: detailData._color + '80' }">⏳ 未达成</span>
        </div>
        <div v-if="detailData.done && detailData.unlock_time" class="detail-time">
          📅 {{ formatDate(detailData.unlock_time) }}
        </div>
        <div class="detail-progress-wrap">
          <div class="progress-track">
            <div
              class="progress-fill"
              :style="{
                width: (detailData.progress || 0) + '%',
                background: `linear-gradient(90deg, ${detailData._color}66, ${detailData._color})`
              }"
            />
          </div>
          <span class="detail-progress-label">{{ detailData.progress || 0 }}%</span>
        </div>
        <el-button
          v-if="detailData.ready && !detailData.done"
          type="warning"
          class="claim-ach-btn active"
          :style="{
            background: detailData._color + '20 !important',
            borderColor: detailData._color + '40 !important',
            color: detailData._color + ' !important'
          }"
          @click="claimAchievement(detailData)"
        >
          🎁 领取成就
        </el-button>
        <el-button
          v-else-if="detailData.done"
          class="claim-ach-btn done"
          :style="{
            color: detailData._color + ' !important',
            opacity: '0.5'
          }"
          disabled
        >
          ✅ 已领取
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/AppLayout.vue'
import CareerSidebar from '@/components/CareerSidebar.vue'
import { getTaskProgress, recordAction } from '@/api/career'
import { ElMessage } from 'element-plus'

// ===== 所有图标 =====
import {
  Calendar, Sunny, Star, ChatDotRound, Message,
  MapLocation, MagicStick, Search, EditPen, Files,
  DocumentCopy, CircleCheck, Lightning, Aim, Trophy,
  FolderAdd, FolderOpened, Folder, Collection, School,
  Medal, Timer
} from '@element-plus/icons-vue'

const authStore = useAuthStore()

const achievements = ref([])
const loading = ref(true)
const detailVisible = ref(false)
const detailData = ref(null)

const doneCount = computed(() => achievements.value.filter(a => a.done).length)
const totalCount = computed(() => achievements.value.length)
const totalProgress = computed(() => {
  if (!totalCount.value) return 0
  return Math.round((doneCount.value / totalCount.value) * 100)
})

// ===== 25 种颜色 + 25 个图标（按顺序循环） =====
const COLORS = [
  '#FF6B6B', '#FF8E53', '#FFB74D', '#FFD93D', '#A8E06C',
  '#6BCB77', '#4ECDC4', '#45B7D1', '#4A9FF5', '#7C6DF0',
  '#9B59B6', '#E040FB', '#EC407A', '#F06292', '#FF8A80',
  '#A1887F', '#90A4AE', '#26A69A', '#42A5F5', '#4CAF50',
  '#FFB300', '#FF6F00', '#9C27B0', '#FF6B6B', '#78909C'
]

const ICONS = [
  Calendar, Sunny, Star, ChatDotRound, Message,
  MapLocation, MagicStick, Search, EditPen, Files,
  DocumentCopy, CircleCheck, Lightning, Aim, Trophy,
  FolderAdd, FolderOpened, Folder, Collection, School,
  Brain, Rocket, Medal, Crown, Timer
]

// ===== 辅助：hex 转 rgb =====
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

async function loadData() {
  loading.value = true
  try {
    if (!authStore.user?.id) {
      achievements.value = []
      loading.value = false
      return
    }
    const data = await getTaskProgress(authStore.user.id)
    achievements.value = (data.achievements || []).map((a, index) => {
      const color = COLORS[index % COLORS.length]
      const icon = ICONS[index % ICONS.length]
      return {
        ...a,
        _color: color,
        _icon: icon,
        progress: a.progress !== undefined ? a.progress : (a.done ? 100 : 0),
        ready: a.done ? false : (a.progress >= 100)
      }
    })
  } catch (error) {
    console.error('加载成就失败', error)
    achievements.value = []
  } finally {
    loading.value = false
  }
}

async function claimAchievement(ach) {
  try {
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
      ElMessage.success(`🎉 成就「${ach.name}」已拾取！`)
      await recordAction(authStore.user.id, 'claim_achievement')
      await loadData()
      detailVisible.value = false
    } else {
      ElMessage.error(result.message || '领取失败')
    }
  } catch (error) {
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
</script>

<style scoped>
.achievements-content {
  padding: 8px 4px;
  max-width: 1000px;
  margin: 0 auto;
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

/* ===== 毛玻璃卡片 ===== */
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
  font-size: 32px;
  margin-bottom: 4px;
  display: flex;
  justify-content: center;
  align-items: center;
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

/* ===== 弹窗毛玻璃 ===== */
.ach-detail-dialog :deep(.el-dialog) {
  background: rgba(255, 255, 255, 0.08) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.10) !important;
  border-radius: 16px !important;
  box-shadow: 0 8px 48px rgba(0, 0, 0, 0.15) !important;
}
[data-theme="dark"] .ach-detail-dialog :deep(.el-dialog) {
  background: rgba(0, 0, 0, 0.35) !important;
  border-color: rgba(255, 255, 255, 0.06) !important;
}
.ach-detail-dialog :deep(.el-dialog__title) {
  color: var(--text-primary) !important;
  font-weight: 600;
}
.ach-detail-dialog :deep(.el-dialog__body) {
  padding: 12px 20px 20px;
}
.ach-detail-dialog :deep(.el-dialog__header) {
  padding: 16px 20px 0;
}
.ach-detail-dialog :deep(.el-dialog__footer) {
  padding: 0 20px 16px;
}

.detail-content {
  text-align: center;
}
.detail-icon {
  font-size: 56px;
  margin-bottom: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
}
.detail-name {
  font-size: 22px;
  font-weight: 700;
}
.detail-condition {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 4px 0;
}
.detail-reward {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 4px 0;
}
.detail-value .star { font-size: 18px; letter-spacing: 2px; }
.detail-status { font-size: 15px; margin: 6px 0; }
.detail-time {
  font-size: 13px;
  color: var(--text-muted);
  margin: 4px 0;
}
.detail-progress-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 12px 0;
}
.detail-progress-wrap .progress-track {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: rgba(128, 128, 128, 0.15);
  overflow: hidden;
}
.detail-progress-wrap .progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}
.detail-progress-label {
  font-size: 13px;
  color: var(--text-muted);
  min-width: 40px;
}
.detail-content .claim-ach-btn {
  margin-top: 12px;
}

@media (max-width: 640px) {
  .achievement-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 10px;
  }
  .ach-card { padding: 14px 10px; }
  .ach-icon { font-size: 26px; }
}
</style>