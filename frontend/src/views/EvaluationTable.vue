<template>
  <div class="evaluation-table-page">
    <div class="table-container">
      <!-- ===== 顶部 ===== -->
      <div class="table-header">
        <div class="header-left">
          <button class="glass-btn back-btn" @click="goBack">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            返回
          </button>
          <h1>评估表</h1>
          <span class="date-tag">{{ generateDate }}</span>
        </div>
        <div class="header-actions">
          <button class="glass-btn" @click="exportPDF" :disabled="pdfExporting">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <path d="M14 2v6h6M12 18v-4M12 10v.01"/>
            </svg>
            导出PDF
          </button>
          <button class="glass-btn primary" @click="refreshData" :disabled="loading">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spinning: loading }">
              <path d="M23 4v6h-6M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
            </svg>
            刷新
          </button>
        </div>
      </div>

      <div class="divider"></div>

      <div v-if="loading" class="loading-state">
        <div class="loader"></div>
        <span>加载中...</span>
      </div>

      <div v-else class="table-content" ref="reportContentRef">
        <!-- ===== 1. 综合评分 ===== -->
        <div class="score-section">
          <div class="score-ring">
            <div class="ring-glow"></div>
            <svg viewBox="0 0 120 120" class="score-svg">
              <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(255,255,255,0.04)" stroke-width="6"/>
              <circle cx="60" cy="60" r="50" fill="none" :stroke="ratingColor" stroke-width="6" stroke-linecap="round"
                :stroke-dasharray="`${(overallScore || 0) * 3.14} 314`"
                :style="{ transform: 'rotate(-90deg)', transformOrigin: 'center' }"
              />
            </svg>
            <div class="score-center">
              <span class="score-number" :style="{ color: ratingColor }">{{ overallScore || 0 }}</span>
              <span class="score-label">综合能力</span>
            </div>
          </div>
          <div class="score-meta">
            <div class="meta-item">
              <span class="meta-label">评级</span>
              <span class="meta-value" :style="{ color: ratingColor, textShadow: `0 0 20px ${ratingColor}40` }">{{ rating }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">学习阶段</span>
              <span class="meta-value">{{ stage }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">知识点</span>
              <span class="meta-value">{{ totalTopics }}</span>
            </div>
          </div>
        </div>

        <!-- ===== 2. 学习人格总览 ===== -->
        <div class="personality-overview">
          <div class="personality-glow-bg"></div>
          <div class="personality-badge">
            <span class="personality-emoji">{{ personalityEmoji }}</span>
            <span class="personality-type">{{ personalityType }}</span>
          </div>
          <div class="personality-desc">{{ personalityDesc }}</div>
          <div class="personality-tags">
            <span v-for="tag in personalityTags" :key="tag" class="personality-tag">{{ tag }}</span>
          </div>
        </div>

        <!-- ===== 3. 六维雷达图 ===== -->
        <div class="table-section">
          <h3>多维能力雷达</h3>
          <div ref="radarChartRef" style="width: 100%; height: 300px;"></div>
        </div>

        <!-- ===== 4. 各维度详情 ===== -->
        <div class="table-section">
          <h3>各维度分析</h3>
          <div class="dimension-grid">
            <div v-for="dim in dimensions" :key="dim.name" class="dimension-card" :style="{ borderColor: dim.color + '44' }">
              <div class="dim-card-glow" :style="{ background: `radial-gradient(circle, ${dim.color}20, transparent 70%)` }"></div>
              <div class="dimension-header">
                <span class="dimension-icon">{{ dim.icon }}</span>
                <span class="dimension-name">{{ dim.name }}</span>
                <span class="dimension-score" :style="{ color: dim.color }">{{ dim.score }}%</span>
              </div>
              <div class="dimension-bar">
                <div class="dimension-fill" :style="{ width: dim.score + '%', background: `linear-gradient(90deg, ${dim.color}66, ${dim.color})` }"></div>
                <div class="bar-pulse" :style="{ left: dim.score + '%', background: dim.color }"></div>
              </div>
              <div class="dimension-status" :style="{ color: dim.color }">{{ dim.status }}</div>
            </div>
          </div>
        </div>

        <!-- ===== 5. 学习行为统计 ===== -->
        <div class="table-section">
          <h3>学习行为</h3>
          <div class="behavior-grid">
            <div v-for="item in behaviorData" :key="item.label" class="behavior-card" :style="{ borderColor: item.color + '33' }">
              <span class="behavior-number" :style="{ color: item.color }">{{ item.value }}</span>
              <span class="behavior-label">{{ item.label }}</span>
              <div class="behavior-bar">
                <div class="behavior-bar-fill" :style="{ width: item.percent + '%', background: item.color }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 6. 智能诊断 + 生成规划 ===== -->
        <div class="table-section diagnosis-section">
          <div class="diagnosis-glow"></div>
          <h3>智能诊断</h3>
          <div class="diagnosis-grid">
            <div v-for="item in diagnosisItems" :key="item.label" class="diagnosis-card" :style="{ borderColor: item.color + '44' }">
              <div class="diag-top-line" :style="{ background: `linear-gradient(90deg, ${item.color}, transparent)` }"></div>
              <div class="diagnosis-icon">{{ item.icon }}</div>
              <div class="diagnosis-label" :style="{ color: item.color }">{{ item.label }}</div>
              <div class="diagnosis-value" :style="{ color: item.color }">{{ item.value }}</div>
            </div>
          </div>

          <div class="diagnosis-actions">
            <button class="glass-btn" @click="copyDiagnosis">
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
              </svg>
              复制诊断
            </button>
            <button class="glass-btn primary generate-plan-btn" @click="goToPlan">
              <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
              生成规划
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const pdfExporting = ref(false)
const generateDate = ref('')
const radarChartRef = ref(null)
const reportContentRef = ref(null)
let radarChart = null

const overallScore = ref(0)
const totalTopics = ref(0)
const rating = ref('')
const ratingColor = ref('#409EFF')
const stage = ref('')

const personalityEmoji = ref('🧠')
const personalityType = ref('')
const personalityDesc = ref('')
const personalityTags = ref([])
const dimensions = ref([])
const behaviorData = ref([])
const diagnosisItems = ref([])

const diagnosisSummary = ref({
  strengths: '',
  weaknesses: '',
  coreIssue: '',
  advice: '',
  stage: ''
})

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

function loadRadarChart() {
  if (!radarChartRef.value) return
  if (radarChart) { radarChart.dispose(); radarChart = null }

  const data = dimensions.value.map(d => d.score)
  const names = dimensions.value.map(d => d.name)

  radarChart = echarts.init(radarChartRef.value)
  radarChart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0,0,0,0.7)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#fff' }
    },
    radar: {
      indicator: names.map(name => ({ name, max: 100 })),
      shape: 'circle',
      center: ['50%', '50%'],
      radius: '65%',
      axisName: {
        color: 'rgba(255,255,255,0.7)',
        fontSize: 13,
        fontWeight: 'bold'
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(64,158,255,0.02)', 'rgba(64,158,255,0.04)']
        }
      },
      axisLine: {
        lineStyle: { color: 'rgba(255,255,255,0.08)' }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: data,
        name: '当前能力',
        areaStyle: { color: 'rgba(64,158,255,0.15)' },
        lineStyle: { color: '#409EFF', width: 2 },
        itemStyle: { color: '#409EFF' }
      }],
      symbol: 'circle',
      symbolSize: 6,
      animationDuration: 1000,
      animationEasing: 'cubicOut'
    }]
  })
  radarChart.resize()
}

function generateDiagnosis() {
  const dims = dimensions.value
  const strong = dims.filter(d => d.score >= 70).map(d => d.name)
  const weak = dims.filter(d => d.score < 60).map(d => d.name)
  const mid = dims.filter(d => d.score >= 60 && d.score < 70).map(d => d.name)

  const maxDim = dims.reduce((a, b) => a.score > b.score ? a : b)

  // ✅ 直接从用户资料读取学习阶段，不靠 AI 瞎猜
  stage.value = authStore.user?.learning_stage || '未设置'

  const typeMap = [
    { name: '探索型学者', emoji: '🔬', desc: '好奇心旺盛，善于发现新知识，适合跨学科学习' },
    { name: '稳健型学习者', emoji: '🛡️', desc: '脚踏实地，基础扎实，适合系统性深入学习' },
    { name: '创新型思维者', emoji: '💡', desc: '思维灵活，善于举一反三，适合解决复杂问题' },
    { name: '专注型深耕者', emoji: '🎯', desc: '专注力强，擅长深度钻研，适合专业领域突破' },
    { name: '均衡型探索者', emoji: '⚖️', desc: '各维度发展均衡，学习适应性强' }
  ]

  let idx = 0
  if (maxDim.score >= 70) idx = Math.floor(Math.random() * 3)
  else if (maxDim.score >= 50) idx = 3
  else idx = 4

  personalityEmoji.value = typeMap[idx].emoji
  personalityType.value = typeMap[idx].name
  personalityDesc.value = typeMap[idx].desc

  const tags = []
  if (strong.length > 0) tags.push(`优势 ${strong.slice(0, 2).join('/')}`)
  if (weak.length > 0) tags.push(`待提升 ${weak.slice(0, 2).join('/')}`)
  if (mid.length > 0) tags.push(`可突破 ${mid.slice(0, 2).join('/')}`)
  if (tags.length === 0) tags.push('各维度均衡')
  personalityTags.value = tags.slice(0, 4)

  const strongText = strong.length > 0 ? strong.slice(0, 2).join('、') : '暂无明显优势'
  const weakText = weak.length > 0 ? weak.slice(0, 2).join('、') : '暂无薄弱项'
  const midText = mid.length > 0 ? mid[0] : '各维度发展良好'
  const adviceText = weak.length > 0 ? `优先攻克 ${weak[0]}` : '保持当前节奏，稳步提升'

  diagnosisItems.value = [
    { icon: '🎯', label: '核心优势', value: strongText, color: '#22C55E' },
    { icon: '📌', label: '待提升维度', value: weakText, color: '#EF4444' },
    { icon: '📈', label: '成长潜力', value: midText, color: '#F59E0B' },
    { icon: '💡', label: '学习建议', value: adviceText, color: '#409EFF' }
  ]

  // ✅ 计算综合评分并赋予积极评级
  const total = dims.reduce((s, d) => s + d.score, 0)
  overallScore.value = Math.round(total / dims.length)

  if (overallScore.value >= 85) {
    rating.value = '巅峰期'
    ratingColor.value = '#FFD700'
  } else if (overallScore.value >= 70) {
    rating.value = '卓越期'
    ratingColor.value = '#8B5CF6'
  } else if (overallScore.value >= 50) {
    rating.value = '精进期'
    ratingColor.value = '#409EFF'
  } else if (overallScore.value >= 30) {
    rating.value = '筑基期'
    ratingColor.value = '#F59E0B'
  } else {
    rating.value = '开拓期'
    ratingColor.value = '#EF4444'
  }

  diagnosisSummary.value = {
    strengths: strongText,
    weaknesses: weakText,
    coreIssue: weak.length > 0 ? `${weak.join('、')} 偏弱` : '各维度发展均衡',
    advice: adviceText,
    stage: stage.value,
    baseDifficulty: overallScore.value >= 70 ? 13 : overallScore.value >= 50 ? 9 : 5
  }
}

function copyDiagnosis() {
  const text = diagnosisItems.value.map(item => `${item.icon} ${item.label}：${item.value}`).join('\n')
  navigator.clipboard.writeText(`智能诊断报告\n\n${text}`).then(() => {
    ElMessage.success('诊断已复制')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动复制')
  })
}

function goToPlan() {
  // ✅ 智能生成规划名称
  let planName = '综合能力提升'
  if (diagnosisSummary.value.weaknesses && diagnosisSummary.value.weaknesses !== '暂无薄弱项') {
    const weakList = diagnosisSummary.value.weaknesses.split('、')
    if (diagnosisSummary.value.strengths && diagnosisSummary.value.strengths !== '暂无明显优势') {
      const strongList = diagnosisSummary.value.strengths.split('、')
      planName = `强化 ${strongList[0]} · 攻克 ${weakList[0]}`
    } else {
      planName = `攻克 ${weakList[0]}`
    }
  }

  const params = new URLSearchParams({
    name: planName,
    weaknesses: diagnosisSummary.value.weaknesses || '',
    strengths: diagnosisSummary.value.strengths || '',
    coreIssue: diagnosisSummary.value.coreIssue || '',
    advice: diagnosisSummary.value.advice || '',
    stage: stage.value || '大学',
    difficulty: diagnosisSummary.value.baseDifficulty || 13,
    keywords: diagnosisSummary.value.weaknesses || ''
  })
  router.push(`/plan-preview?${params.toString()}`)
}

async function loadData() {
  loading.value = true
  try {
    const res = await fetch(
      `${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/evaluation/profile-data?user_id=${authStore.user.id}`,
      { headers: { Authorization: `Bearer ${authStore.token}` } }
    )
    const data = await res.json()

    const kb = data.knowledge_base || { list: [], avg_score: 0 }
    totalTopics.value = kb.list.length || 0

    const dims = [
      { name: '知识基础', icon: 'K', score: kb.avg_score || 0, color: '#409EFF', status: kb.avg_score >= 70 ? '良好' : kb.avg_score >= 50 ? '提升中' : '待加强' },
      { name: '认知风格', icon: 'C', score: 55, color: '#8B5CF6', status: '综合型' },
      { name: '易错偏好', icon: 'E', score: data.mistake_pattern?.conquered_rate || 0, color: '#F59E0B', status: data.mistake_pattern?.conquered_rate >= 60 ? '攻克率高' : '需加强' },
      { name: '学习目标', icon: 'G', score: data.learning_goal?.total_sets ? Math.min(100, data.learning_goal.total_sets * 20) : 0, color: '#22C55E', status: data.learning_goal?.total_sets > 0 ? '已创建题集' : '未创建' },
      { name: '兴趣领域', icon: 'I', score: data.interest_field?.list?.length ? Math.min(100, data.interest_field.list.length * 20) : 0, color: '#EC4899', status: data.interest_field?.list?.length > 0 ? '兴趣明确' : '待拓展' },
      { name: '学习人格', icon: 'P', score: 55, color: '#06B6D4', status: '探索中' }
    ]

    if (data.mistake_pattern?.total > 0) {
      dims[2].score = data.mistake_pattern.conquered_rate || 0
    }
    if (data.learning_goal?.total_sets > 0) {
      dims[3].score = Math.min(100, data.learning_goal.total_sets * 20)
    }
    if (data.interest_field?.list?.length > 0) {
      dims[4].score = Math.min(100, data.interest_field.list.length * 20)
    }

    dimensions.value = dims

    behaviorData.value = [
      { label: '活跃天数', value: 12, percent: 40, color: '#409EFF' },
      { label: '连续学习', value: '7天', percent: 50, color: '#22C55E' },
      { label: '日均做题', value: 8, percent: 60, color: '#F59E0B' },
      { label: '总做题数', value: 96, percent: 70, color: '#8B5CF6' }
    ]

    generateDiagnosis()

    generateDate.value = new Date().toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    })

    await nextTick()
    setTimeout(() => loadRadarChart(), 300)
  } catch (error) {
    console.error('加载失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

function refreshData() {
  loadData()
  ElMessage.success('已刷新')
}

function goBack() {
  router.push('/evaluation-center')
}

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
      if (position > 0) pdf.addPage()
      pdf.addImage(sliceData, 'PNG', margin, margin, contentWidth, sliceHeight)
      remaining -= sliceHeight
      position += sliceHeight
    }

    pdf.save(`评估表_${new Date().toISOString().slice(0, 10)}.pdf`)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    pdfExporting.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.evaluation-table-page {
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
[data-theme="light"] .evaluation-table-page {
  background-image: url('/assets/bg/resource_lib_bg.jpg');
}
[data-theme="dark"] .evaluation-table-page {
  background-image: url('/assets/bg/resource_lib_bl.jpg');
}

.table-container {
  max-width: 900px;
  width: 100%;
  padding: 32px 40px;
  border-radius: 20px;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.06);
  box-shadow: 0 8px 48px rgba(0,0,0,0.08);
}
[data-theme="dark"] .table-container {
  background: rgba(0,0,0,0.30);
  border-color: rgba(255,255,255,0.04);
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.header-left h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.date-tag {
  font-size: 13px;
  color: var(--text-muted);
  padding: 2px 12px;
  border-radius: 12px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.04);
}
.header-actions {
  display: flex;
  gap: 8px;
}

.glass-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: all 0.3s ease;
}
.glass-btn:hover {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.10);
  transform: translateY(-2px);
}
.glass-btn:active {
  transform: scale(0.97);
}
.glass-btn.primary {
  color: #409EFF;
  background: rgba(64,158,255,0.08);
  border-color: rgba(64,158,255,0.10);
}
.glass-btn.primary:hover {
  background: rgba(64,158,255,0.14);
  border-color: rgba(64,158,255,0.20);
}
.glass-btn .icon {
  width: 18px;
  height: 18px;
}
.glass-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}
.back-btn .icon {
  width: 20px;
  height: 20px;
}
.spinning {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
  margin: 16px 0 20px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 20px;
  color: var(--text-muted);
}
.loader {
  width: 32px;
  height: 32px;
  border: 2px solid rgba(64,158,255,0.12);
  border-top-color: #409EFF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.table-section {
  margin-bottom: 24px;
}
.table-section h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 14px 0;
  letter-spacing: 0.3px;
}

/* 综合评分 */
.score-section {
  display: flex;
  align-items: center;
  gap: 30px;
  padding: 16px 20px;
  border-radius: 12px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  margin-bottom: 20px;
}
.score-ring {
  position: relative;
  width: 120px;
  height: 120px;
  flex-shrink: 0;
}
.ring-glow {
  position: absolute;
  top: -10px;
  left: -10px;
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(64,158,255,0.08), transparent 70%);
  animation: pulseGlow 3s ease-in-out infinite;
}
@keyframes pulseGlow {
  0%, 100% { opacity: 0.3; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.05); }
}
.score-svg { width: 100%; height: 100%; }
.score-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.score-number {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}
.score-label {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
}
.score-meta {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}
.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.meta-label { font-size: 12px; color: var(--text-muted); }
.meta-value { font-size: 18px; font-weight: 600; color: var(--text-primary); }

/* 人格总览 */
.personality-overview {
  position: relative;
  padding: 24px 24px 20px;
  border-radius: 14px;
  text-align: center;
  overflow: hidden;
  margin-bottom: 20px;
  background: linear-gradient(135deg, rgba(64,158,255,0.06), rgba(139,92,246,0.06));
  border: 1px solid rgba(64,158,255,0.08);
}
.personality-glow-bg {
  position: absolute;
  top: -50%;
  left: -20%;
  width: 140%;
  height: 140%;
  background: radial-gradient(ellipse at center, rgba(64,158,255,0.06), transparent 60%);
  animation: glowPulse 4s ease-in-out infinite;
  pointer-events: none;
}
@keyframes glowPulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.1); opacity: 1; }
}
.personality-badge {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
.personality-emoji {
  font-size: 40px;
  animation: float 3s ease-in-out infinite;
}
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
.personality-type {
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(135deg, #409EFF, #8B5CF6, #F59E0B);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: shimmer 4s ease-in-out infinite;
}
@keyframes shimmer {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}
.personality-desc {
  position: relative;
  font-size: 14px;
  color: var(--text-secondary);
  margin: 6px 0 10px;
}
.personality-tags {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
}
.personality-tag {
  padding: 3px 14px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(64,158,255,0.08);
  color: #409EFF;
  border: 1px solid rgba(64,158,255,0.08);
}

/* 维度卡片 */
.dimension-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.dimension-card {
  position: relative;
  padding: 12px 16px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.04);
  background: rgba(255,255,255,0.02);
  overflow: hidden;
  transition: all 0.3s ease;
}
.dimension-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255,255,255,0.08);
}
.dim-card-glow {
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.6s ease;
}
.dimension-card:hover .dim-card-glow {
  opacity: 1;
}
.dimension-header {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
  z-index: 1;
}
.dimension-icon { font-size: 16px; }
.dimension-name { font-size: 14px; color: var(--text-secondary); flex: 1; }
.dimension-score { font-size: 16px; font-weight: 700; }
.dimension-bar {
  position: relative;
  height: 4px;
  border-radius: 2px;
  background: rgba(255,255,255,0.06);
  margin-top: 6px;
  overflow: hidden;
}
.dimension-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.8s ease;
}
.bar-pulse {
  position: absolute;
  top: -2px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  opacity: 0.6;
  animation: barPulse 2s ease-in-out infinite;
  transform: translateX(-50%);
}
@keyframes barPulse {
  0%, 100% { opacity: 0.3; transform: translateX(-50%) scale(0.8); }
  50% { opacity: 1; transform: translateX(-50%) scale(1.2); }
}
.dimension-status { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

/* 行为 */
.behavior-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}
.behavior-card {
  padding: 14px 12px;
  border-radius: 10px;
  text-align: center;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
}
.behavior-number {
  display: block;
  font-size: 24px;
  font-weight: 700;
}
.behavior-label {
  font-size: 12px;
  color: var(--text-muted);
}
.behavior-bar {
  width: 100%;
  height: 2px;
  border-radius: 1px;
  background: rgba(255,255,255,0.04);
  margin-top: 6px;
  overflow: hidden;
}
.behavior-bar-fill {
  height: 100%;
  border-radius: 1px;
  transition: width 0.8s ease;
}

/* 诊断 */
.diagnosis-section {
  background: linear-gradient(135deg, rgba(64,158,255,0.04), rgba(139,92,246,0.04));
  border: 1px solid rgba(64,158,255,0.06);
  border-radius: 12px;
  padding: 16px 20px;
  position: relative;
  overflow: hidden;
}
.diagnosis-glow {
  position: absolute;
  top: -30%;
  right: -10%;
  width: 60%;
  height: 160%;
  background: radial-gradient(ellipse, rgba(64,158,255,0.04), transparent 70%);
  pointer-events: none;
}
.diagnosis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  position: relative;
  z-index: 1;
}
.diagnosis-card {
  position: relative;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  overflow: hidden;
}
.diag-top-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  opacity: 0.4;
}
.diagnosis-icon { font-size: 22px; }
.diagnosis-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}
.diagnosis-value {
  font-size: 14px;
  font-weight: 600;
  margin-top: 4px;
  line-height: 1.4;
}
.diagnosis-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
  position: relative;
  z-index: 1;
  justify-content: flex-end;
}
.generate-plan-btn {
  position: relative;
  overflow: hidden;
}
.generate-plan-btn::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
  animation: btnShine 3s ease-in-out infinite;
}
@keyframes btnShine {
  0% { transform: translateX(-100%) rotate(45deg); }
  100% { transform: translateX(100%) rotate(45deg); }
}

@media (max-width: 640px) {
  .table-container { padding: 16px; }
  .table-header { flex-direction: column; align-items: stretch; }
  .score-section { flex-direction: column; align-items: center; }
  .score-meta { justify-content: center; }
  .dimension-grid { grid-template-columns: 1fr; }
  .diagnosis-grid { grid-template-columns: 1fr; }
  .behavior-grid { grid-template-columns: 1fr 1fr; }
  .personality-type { font-size: 22px; }
  .diagnosis-actions { flex-direction: column; }
  .diagnosis-actions .glass-btn { justify-content: center; }
}
</style>