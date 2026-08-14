<template>
  <div class="evaluation-report-page">
    <div class="report-container">
      <!-- ===== 顶部 ===== -->
      <div class="report-header">
        <div class="header-left">
          <el-button text class="back-btn" @click="goBack">
            <i class="fas fa-arrow-left"></i> 返回
          </el-button>
          <h1>📈 学情报告</h1>
          <el-tag size="small" type="info">{{ generateDate }}</el-tag>
        </div>
        <div class="header-actions">
          <el-button size="small" @click="exportPDF" :loading="pdfExporting">
            <i class="fas fa-file-pdf"></i> 导出PDF
          </el-button>
          <el-button size="small" type="primary" @click="refreshData" :loading="loading">
            <i class="fas fa-sync"></i> 刷新
          </el-button>
        </div>
      </div>

      <el-divider />

      <!-- ===== 加载状态 ===== -->
      <LoadingSpinner
        v-if="loading"
        variant="orbit"
        :size="80"
        :flow-steps="['正在采集学习数据...', '正在分析掌握模式...', '正在计算多维画像...']"
      />

      <!-- ===== 内容 ===== -->
      <div v-else class="report-content" ref="reportContentRef">
        <!-- 1. 统计概览 -->
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-number">{{ totalTopics }}</span>
            <span class="stat-label">知识点总数</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ masteredTopics }}</span>
            <span class="stat-label">✅ 已掌握（≥80%）</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ weakTopics }}</span>
            <span class="stat-label">🔴 待巩固（&lt;60%）</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ avgMastery }}%</span>
            <span class="stat-label">📊 平均掌握度</span>
          </div>
        </div>

        <!-- 2. 掌握度分布 -->
        <div class="report-section">
          <h3>📊 掌握度分布</h3>
          <div class="mastery-distribution">
            <div class="dist-bar-wrapper">
              <div class="dist-label">🔴 薄弱 (&lt;60%)</div>
              <div class="dist-bar-track">
                <div class="dist-bar-fill" :style="{ width: weakPercent + '%', background: '#ef4444' }"></div>
              </div>
              <span class="dist-value">{{ weakPercent }}%</span>
            </div>
            <div class="dist-bar-wrapper">
              <div class="dist-label">🟡 待巩固 (60-80%)</div>
              <div class="dist-bar-track">
                <div class="dist-bar-fill" :style="{ width: consolidatePercent + '%', background: '#f59e0b' }"></div>
              </div>
              <span class="dist-value">{{ consolidatePercent }}%</span>
            </div>
            <div class="dist-bar-wrapper">
              <div class="dist-label">🟢 已掌握 (≥80%)</div>
              <div class="dist-bar-track">
                <div class="dist-bar-fill" :style="{ width: masteredPercent + '%', background: '#22c55e' }"></div>
              </div>
              <span class="dist-value">{{ masteredPercent }}%</span>
            </div>
          </div>
        </div>

        <!-- 3. 知识点详情 -->
        <div class="report-section">
          <h3>📋 知识点详情</h3>
          <div v-if="!masteryData.length" class="empty-state">暂无知识点数据</div>
          <div v-else>
            <div class="filter-bar">
              <el-radio-group v-model="filterStatus" size="small">
                <el-radio-button label="all">全部</el-radio-button>
                <el-radio-button label="weak">🔴 薄弱</el-radio-button>
                <el-radio-button label="consolidate">🟡 待巩固</el-radio-button>
                <el-radio-button label="mastered">🟢 已掌握</el-radio-button>
              </el-radio-group>
              <el-input
                v-model="searchKeyword"
                placeholder="搜索知识点..."
                size="small"
                clearable
                style="width: 180px;"
                prefix-icon="Search"
              />
            </div>

            <div class="topic-list">
              <div
                v-for="item in filteredTopics"
                :key="item.topic"
                class="topic-row"
                :class="getStatusClass(item.mastery_score)"
              >
                <span class="topic-name">{{ item.topic }}</span>
                <div class="topic-score-bar">
                  <div class="topic-score-fill" :style="{ width: item.mastery_score + '%', background: getColor(item.mastery_score) }"></div>
                </div>
                <span class="topic-score">{{ item.mastery_score }}%</span>
                <span class="topic-badge">{{ getBadge(item.mastery_score) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 4. 近期学习动态 -->
        <div class="report-section">
          <h3>📖 近期学习动态</h3>
          <div v-if="!activities.length" class="empty-state">暂无学习动态</div>
          <div v-else>
            <div v-for="act in activities" :key="act.id" class="activity-item">
              <span class="activity-icon">{{ getActivityIcon(act.type || act.action) }}</span>
              <span class="activity-text">{{ act.content || act.details?.text || act.action || '学习记录' }}</span>
              <span class="activity-time">{{ formatTime(act.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { getMastery } from '@/api/questions'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const pdfExporting = ref(false)
const masteryData = ref([])
const activities = ref([])
const generateDate = ref('')
const filterStatus = ref('all')
const searchKeyword = ref('')
const reportContentRef = ref(null)

// ===== 20种掌握度颜色 =====
const MASTERY_COLORS = [
  '#FF0000', '#FF1A00', '#FF3300', '#FF4D00', '#FF6600',
  '#FF8000', '#FF9900', '#FFB300', '#FFCC00', '#FFE600',
  '#D4E000', '#A8D500', '#7DCC00', '#52C200', '#26B800',
  '#00AD00', '#00A300', '#009900', '#008000', '#006600'
]

function getColor(score) {
  const index = Math.min(Math.floor(score / 5), 19)
  return MASTERY_COLORS[index] || '#888'
}

// ===== 统计 =====
const totalTopics = computed(() => masteryData.value.length)
const masteredTopics = computed(() => masteryData.value.filter(t => t.mastery_score >= 80).length)
const weakTopics = computed(() => masteryData.value.filter(t => t.mastery_score < 60).length)
const avgMastery = computed(() => {
  if (!masteryData.value.length) return 0
  const sum = masteryData.value.reduce((s, t) => s + t.mastery_score, 0)
  return Math.round(sum / masteryData.value.length)
})

const weakPercent = computed(() => {
  if (!masteryData.value.length) return 0
  return Math.round((weakTopics.value / masteryData.value.length) * 100)
})
const consolidatePercent = computed(() => {
  if (!masteryData.value.length) return 0
  const count = masteryData.value.filter(t => t.mastery_score >= 60 && t.mastery_score < 80).length
  return Math.round((count / masteryData.value.length) * 100)
})
const masteredPercent = computed(() => {
  if (!masteryData.value.length) return 0
  return Math.round((masteredTopics.value / masteryData.value.length) * 100)
})

const filteredTopics = computed(() => {
  let result = masteryData.value
  if (filterStatus.value === 'weak') {
    result = result.filter(t => t.mastery_score < 60)
  } else if (filterStatus.value === 'consolidate') {
    result = result.filter(t => t.mastery_score >= 60 && t.mastery_score < 80)
  } else if (filterStatus.value === 'mastered') {
    result = result.filter(t => t.mastery_score >= 80)
  }
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.trim().toLowerCase()
    result = result.filter(t => t.topic.toLowerCase().includes(keyword))
  }
  return result
})

function getBadge(score) {
  if (score < 60) return '🔴 薄弱'
  if (score < 80) return '🟡 待巩固'
  return '🟢 已掌握'
}

function getStatusClass(score) {
  if (score < 60) return 'status-weak'
  if (score < 80) return 'status-consolidate'
  return 'status-mastered'
}

function getActivityIcon(type) {
  const map = {
    checkin: '✅',
    answer_question: '📝',
    generate_question: '✏️',
    achievement_unlocked: '🏆',
    set_created: '📁',
    timer_completed: '⏱️',
    mistake_conquered: '🎯',
    level_up: '⬆️',
    rank_up: '🏅',
    chat: '💬',
    view_report: '📊'
  }
  return map[type] || '📌'
}

function formatTime(time) {
  if (!time) return ''
  const t = new Date(time)
  const now = new Date()
  const diff = Math.floor((now - t) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 604800) return Math.floor(diff / 86400) + '天前'
  return t.toLocaleDateString()
}

async function loadData() {
  loading.value = true
  try {
    const [masteryRes] = await Promise.all([
      getMastery(authStore.user.id)
    ])
    masteryData.value = masteryRes || []
    generateDate.value = new Date().toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

async function refreshData() {
  await loadData()
  ElMessage.success('已刷新')
}

// ===== 多页PDF导出 =====
async function exportPDF() {
  if (!reportContentRef.value) return
  pdfExporting.value = true
  try {
    const canvas = await html2canvas(reportContentRef.value, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#1a1a2e',
      logging: false,
      windowHeight: reportContentRef.value.scrollHeight,
      height: reportContentRef.value.scrollHeight
    })

    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pdfWidth = pdf.internal.pageSize.getWidth()
    const pdfHeight = pdf.internal.pageSize.getHeight()
    const margin = 10
    const contentWidth = pdfWidth - margin * 2
    const contentHeight = (canvas.height * contentWidth) / canvas.width

    let remaining = contentHeight
    let position = 0
    const pageContentHeight = pdfHeight - margin * 2

    while (remaining > 0) {
      const sliceHeight = Math.min(remaining, pageContentHeight)
      const ratio = sliceHeight / contentHeight
      const sliceCanvasHeight = canvas.height * ratio

      const sliceCanvas = document.createElement('canvas')
      sliceCanvas.width = canvas.width
      sliceCanvas.height = sliceCanvasHeight
      const ctx = sliceCanvas.getContext('2d')
      const srcY = (position / contentHeight) * canvas.height
      ctx.drawImage(canvas, 0, srcY, canvas.width, sliceCanvasHeight, 0, 0, canvas.width, sliceCanvasHeight)

      const sliceData = sliceCanvas.toDataURL('image/png')

      if (position > 0) {
        pdf.addPage()
      }
      pdf.addImage(sliceData, 'PNG', margin, margin, contentWidth, sliceHeight)

      remaining -= sliceHeight
      position += sliceHeight
    }

    pdf.save(`学情报告_${new Date().toISOString().slice(0, 10)}.pdf`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    pdfExporting.value = false
  }
}

function goBack() {
  router.push('/evaluation-center')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.evaluation-report-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 30px 20px;
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  background-repeat: no-repeat;
}

[data-theme="light"] .evaluation-report-page {
  background-image: url('/assets/bg/resource_lib_bg.jpg');
}
[data-theme="dark"] .evaluation-report-page {
  background-image: url('/assets/bg/resource_lib_bl.jpg');
}

.report-container {
  max-width: 860px;
  width: 100%;
  margin: 0 auto;
  padding: 28px 36px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
}

[data-theme="dark"] .report-container {
  background: rgba(0, 0, 0, 0.30);
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
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
  background: rgba(255, 255, 255, 0.06);
}
.report-header h1 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
}
.header-actions {
  display: flex;
  gap: 6px;
}

.el-divider {
  margin: 12px 0;
}

.loading-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}
.stat-card {
  padding: 16px;
  border-radius: 12px;
  text-align: center;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.stat-number {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}
.stat-label {
  font-size: 12px;
  color: var(--text-muted);
}

.report-section {
  margin-bottom: 24px;
}
.report-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.mastery-distribution {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.dist-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}
.dist-label {
  font-size: 13px;
  color: var(--text-secondary);
  min-width: 120px;
}
.dist-bar-track {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}
.dist-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}
.dist-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 40px;
  text-align: right;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}
.topic-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.topic-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.02);
  border-left: 3px solid transparent;
}
.topic-row.status-weak {
  border-left-color: #ef4444;
}
.topic-row.status-consolidate {
  border-left-color: #f59e0b;
}
.topic-row.status-mastered {
  border-left-color: #22c55e;
}
.topic-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  min-width: 120px;
}
.topic-score-bar {
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}
.topic-score-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}
.topic-score {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 50px;
  text-align: right;
}
.topic-badge {
  font-size: 12px;
  min-width: 60px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  font-size: 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}
.activity-item:last-child {
  border-bottom: none;
}
.activity-icon {
  font-size: 16px;
}
.activity-text {
  color: var(--text-secondary);
  flex: 1;
}
.activity-time {
  font-size: 12px;
  color: var(--text-muted);
}

.empty-state {
  color: var(--text-muted);
  padding: 12px 0;
  text-align: center;
  font-size: 14px;
}

@media (max-width: 640px) {
  .report-container {
    padding: 16px 14px;
  }
  .report-header {
    flex-direction: column;
    align-items: stretch;
  }
  .header-left {
    flex-wrap: wrap;
  }
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
  .stat-number {
    font-size: 22px;
  }
  .dist-label {
    min-width: 80px;
    font-size: 12px;
  }
  .topic-row {
    flex-wrap: wrap;
    gap: 6px;
  }
  .topic-name {
    min-width: 80px;
    font-size: 13px;
  }
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-bar .el-input {
    width: 100% !important;
  }
}
</style>