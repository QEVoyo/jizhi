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

      <!-- ===== 友好加载 ===== -->
      <LoadingSpinner
        v-if="loading"
        variant="orbit"
        :size="80"
        :flow-steps="['正在采集全平台学习数据…', '正在汇总掌握度与做题记录…', '正在分析错题与学习节奏…', 'AI 正在生成深度解读…']"
      />

      <!-- ===== 内容 ===== -->
      <div v-else class="report-content" ref="reportContentRef">
        <!-- 1. AI 深度解读（2026-08-30：全平台数据喂给 LLM 生成，规则兜底） -->
        <div class="report-section ai-section">
          <h3>✨ AI 学情解读</h3>
          <div class="ai-summary-box">
            <p class="ai-summary-text">{{ aiSummary }}</p>
            <div class="ai-summary-foot">
              <span class="ai-note">基于你近 30 天的全平台学习数据生成 · 15 分钟内不重复调用</span>
            </div>
          </div>
        </div>

        <!-- 2. 总览卡（2026-08-30 精简：只留三个核心指标，其余各归各板块） -->
        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-number">{{ overview.practice.total }}</span>
            <span class="stat-label">近30天做题量</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ overview.practice.rate }}%</span>
            <span class="stat-label">🎯 做题正确率</span>
          </div>
          <div class="stat-card">
            <span class="stat-number">{{ overview.mastery.avg_mastery }}%</span>
            <span class="stat-label">📊 平均掌握度</span>
          </div>
        </div>

        <!-- 3. 30 天趋势（做题量 / 正确率 双小图，避免双轴混图） -->
        <div class="report-section">
          <h3>📈 近 30 天趋势</h3>
          <div class="trend-grid" v-if="practiceTotal > 0">
            <div class="trend-card">
              <div class="trend-title">做题量（道/天）</div>
              <div ref="countChartRef" class="trend-chart"></div>
            </div>
            <div class="trend-card">
              <div class="trend-title">正确率（%）</div>
              <div ref="rateChartRef" class="trend-chart"></div>
            </div>
          </div>
          <div v-else class="empty-state">
            近 30 天还没有题库做题记录——去「学科计划」做几道题，趋势图就会亮起来
          </div>
        </div>

        <!-- 4. 掌握度分布 -->
        <div class="report-section">
          <h3>📊 掌握度分布</h3>
          <div class="mastery-distribution" v-if="overview.mastery.topic_count">
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
          <div v-else class="empty-state">暂无掌握度数据——在「生成题目」里作答评估后会逐步积累</div>
        </div>

        <!-- 5. 薄弱知识点（可一键练习） -->
        <div class="report-section" v-if="overview.mastery.weak_topics.length">
          <h3>🎯 薄弱知识点</h3>
          <div class="weak-grid">
            <div
              v-for="w in overview.mastery.weak_topics"
              :key="w.topic"
              class="weak-card"
              :style="{ borderLeftColor: getColor(w.score) }"
            >
              <span class="weak-topic">{{ w.topic }}</span>
              <span class="weak-score">{{ w.score }}%</span>
              <el-button size="small" round class="weak-btn" @click="goPractice(w.topic)">
                攻克 →
              </el-button>
            </div>
          </div>
        </div>

        <!-- 6. 错题画像 -->
        <div class="report-section" v-if="overview.mastery.mistakes.total > 0">
          <h3>🩹 错题画像</h3>
          <div class="mistake-summary">
            <div class="mistake-num">
              <span class="mistake-big">{{ overview.mastery.mistakes.total }}</span>
              <span class="mistake-label">错题总数</span>
            </div>
            <div class="mistake-num">
              <span class="mistake-big">{{ overview.mastery.mistakes.conquered_rate }}%</span>
              <span class="mistake-label">攻克率（已攻克 {{ overview.mastery.mistakes.conquered }}）</span>
            </div>
          </div>
          <div class="mistake-panels">
            <div class="mistake-panel">
              <div class="panel-title">错题集中的知识点</div>
              <div v-if="overview.mastery.mistakes.by_topic.length" class="mistake-topic-list">
                <div v-for="(m, i) in topMistakeTopics" :key="m.topic" class="mistake-topic-row">
                  <span class="mistake-rank">{{ i + 1 }}</span>
                  <span class="mistake-topic">{{ m.topic }}</span>
                  <span class="mistake-count">{{ m.count }} 题</span>
                  <div class="mistake-mini-bar">
                    <div
                      class="mistake-mini-fill"
                      :style="{ width: (m.count / topMistakeTopics[0].count * 100) + '%' }"
                    ></div>
                  </div>
                </div>
              </div>
              <div v-else class="empty-state small">暂无</div>
            </div>
            <div class="mistake-panel">
              <div class="panel-title">错误题型分布</div>
              <div class="type-chips">
                <span v-for="t in overview.mastery.mistakes.by_type" :key="t.name" class="type-chip">
                  {{ getTypeDisplay(t.name) }} × {{ t.count }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 7. 真题卷战绩 -->
        <div class="report-section">
          <h3>📜 真题卷战绩</h3>
          <div v-if="overview.exams.count" class="exam-summary">
            <div class="exam-num"><span class="exam-big">{{ overview.exams.count }}</span><span>已做套卷</span></div>
            <div class="exam-num"><span class="exam-big">{{ overview.exams.avg.toFixed(1) }}</span><span>平均分（百分制）</span></div>
            <div class="exam-num"><span class="exam-big">{{ overview.exams.best.toFixed(1) }}</span><span>最佳成绩</span></div>
          </div>
          <div v-else class="empty-state">
            还没有真题卷记录——去「学科计划 → 真题套卷」交一卷，成绩曲线就会出现在这里
          </div>
          <div v-if="overview.exams.records.length" class="exam-list">
            <div v-for="(e, i) in overview.exams.records" :key="i" class="exam-row">
              <span class="exam-name">{{ e.paper_name }}</span>
              <span class="exam-date">{{ e.date }}</span>
              <span class="exam-score" :style="{ color: e.score >= 60 ? '#22c55e' : '#f59e0b' }">{{ e.score.toFixed(1) }}</span>
            </div>
          </div>
        </div>

        <!-- 8. 学习节奏 -->
        <div class="report-section">
          <h3>⏱ 学习节奏</h3>
          <div class="rhythm-top">
            <div class="rhythm-num"><span class="rhythm-big">{{ overview.rhythm.active_days }}</span><span>近90天活跃天数</span></div>
            <div class="rhythm-num"><span class="rhythm-big">{{ overview.rhythm.max_streak }}<small>天</small></span><span>最长连续学习</span></div>
            <div class="rhythm-num">
              <span class="rhythm-big">
                <template v-if="overview.rhythm.peak_hours.length">{{ peakHourText }}</template>
                <template v-else>—</template>
              </span>
              <span>高效时段</span>
            </div>
          </div>
          <div class="rhythm-calendar-wrap">
            <div class="calendar-grid">
              <div
                v-for="cell in overview.rhythm.calendar"
                :key="cell.date"
                class="calendar-cell"
                :class="'lv' + cell.level"
                :title="`${cell.date} · ${cell.count} 次学习行为`"
              ></div>
            </div>
            <div class="calendar-legend">
              <span>少</span>
              <span class="calendar-cell lv1"></span>
              <span class="calendar-cell lv2"></span>
              <span class="calendar-cell lv3"></span>
              <span class="calendar-cell lv4"></span>
              <span>多</span>
            </div>
          </div>
        </div>

        <!-- 9. 计划进度 -->
        <div class="report-section">
          <h3>🗓 计划进度</h3>
          <div class="plan-cards">
            <div class="plan-card">
              <div class="pc-title">学科计划</div>
              <div class="pc-body">
                <div v-if="overview.subject_plan.plans">
                  <span class="pc-big">{{ overview.subject_plan.tasks_done }}/{{ overview.subject_plan.tasks_total }}</span>
                  <span class="pc-small">近30天每日任务完成</span>
                  <div class="pc-bar"><div class="pc-fill" :style="{ width: overview.subject_plan.completion + '%' }"></div></div>
                </div>
                <div v-else class="empty-state small">还没有学科计划——从考纲诊断开始</div>
              </div>
            </div>
            <div class="plan-card">
              <div class="pc-title">自定义计划</div>
              <div class="pc-body">
                <div v-if="overview.learning_plans.latest">
                  <span class="pc-name">{{ overview.learning_plans.latest.name }}</span>
                  <span class="pc-big">{{ overview.learning_plans.latest.progress }}%</span>
                  <div class="pc-bar"><div class="pc-fill green" :style="{ width: overview.learning_plans.latest.progress + '%' }"></div></div>
                </div>
                <div v-else class="empty-state small">还没有自定义计划</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 10. 知识点详情（明细列表放在最末尾：默认 20 条可展开，不挡前方洞察板块） -->
        <div class="report-section topic-detail-last" v-if="overview.mastery.topic_count">
          <h3>📋 知识点详情</h3>
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
              v-for="item in displayTopics"
              :key="item.topic"
              class="topic-row"
              :class="getStatusClass(item.score)"
            >
              <span class="topic-name">{{ item.topic }}</span>
              <div class="topic-score-bar">
                <div class="topic-score-fill" :style="{ width: item.score + '%', background: getColor(item.score) }"></div>
              </div>
              <span class="topic-score">{{ item.score }}%</span>
              <span class="topic-badge">{{ getBadge(item.score) }}</span>
            </div>
          </div>
          <div v-if="filteredTopics.length > 20" class="topic-more">
            <el-button size="small" text type="primary" @click="showAllTopics = !showAllTopics">
              {{ showAllTopics ? '▲ 收起' : `▼ 展开全部（共 ${filteredTopics.length} 条）` }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore, hexToRgb } from '@/stores/theme'
import { ElMessage } from 'element-plus'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import * as echarts from 'echarts'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const loading = ref(true)
const pdfExporting = ref(false)
const overview = ref(defaultOverview())
const aiSummary = ref('')
const generateDate = ref('')
const filterStatus = ref('all')
const searchKeyword = ref('')
const reportContentRef = ref(null)
const countChartRef = ref(null)
const rateChartRef = ref(null)

let countChart = null
let rateChart = null

function defaultOverview() {
  return {
    practice: { total: 0, rate: 0, daily: [] },
    mastery: { avg_mastery: 0, topic_count: 0, topic_list: [], weak_topics: [], mistakes: { total: 0, conquered: 0, conquered_rate: 0, by_topic: [], by_type: [] } },
    subject_plan: { plans: 0, tasks_total: 0, tasks_done: 0, completion: 0 },
    exams: { count: 0, avg: 0, best: 0, records: [] },
    learning_plans: { count: 0, avg_progress: 0, latest: null },
    words: { total: 0, mastered: 0, lookups_30d: 0 },
    rhythm: { calendar: [], current_streak: 0, max_streak: 0, active_days: 0, peak_hours: [] },
  }
}

// ===== 主题感知的图表取色 =====
// ECharts canvas 不认 CSS var()/color-mix——品牌色半透明需 JS 解析成 rgba（2026-09-02 主题定制）
function brandSoft(alpha) {
  const c = hexToRgb(themeStore.brandColor) || { r: 64, g: 158, b: 255 }
  return `rgba(${c.r}, ${c.g}, ${c.b}, ${alpha})`
}
function chartInk() {
  const cs = getComputedStyle(document.documentElement)
  return {
    muted: cs.getPropertyValue('--text-muted').trim() || 'rgba(140,150,170,.8)',
    secondary: cs.getPropertyValue('--text-secondary').trim() || 'rgba(200,210,230,.8)',
  }
}

const practiceTotal = computed(() => overview.value.practice.total)
const weakPercent = computed(() => {
  const n = overview.value.mastery.topic_count
  if (!n) return 0
  return Math.round(overview.value.mastery.topic_list.filter(t => t.score < 60).length / n * 100)
})
const consolidatePercent = computed(() => {
  const n = overview.value.mastery.topic_count
  if (!n) return 0
  return Math.round(overview.value.mastery.topic_list.filter(t => t.score >= 60 && t.score < 80).length / n * 100)
})
const masteredPercent = computed(() => {
  const n = overview.value.mastery.topic_count
  if (!n) return 0
  return Math.round(overview.value.mastery.topic_list.filter(t => t.score >= 80).length / n * 100)
})

const filteredTopics = computed(() => {
  let list = overview.value.mastery.topic_list
  if (filterStatus.value === 'weak') list = list.filter(t => t.score < 60)
  else if (filterStatus.value === 'consolidate') list = list.filter(t => t.score >= 60 && t.score < 80)
  else if (filterStatus.value === 'mastered') list = list.filter(t => t.score >= 80)
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    list = list.filter(t => (t.topic || '').toLowerCase().includes(kw))
  }
  return list
})

// 知识点详情默认只展示 20 条（2026-08-30：列表过长会淹没下方板块，展开按钮兜底）
const showAllTopics = ref(false)
const displayTopics = computed(() =>
  showAllTopics.value ? filteredTopics.value : filteredTopics.value.slice(0, 20)
)

const topMistakeTopics = computed(() => overview.value.mastery.mistakes.by_topic.slice(0, 6))
const peakHourText = computed(() => {
  const h = overview.value.rhythm.peak_hours[0].hour
  const label = h < 6 ? '凌晨' : h < 12 ? '上午' : h < 14 ? '中午' : h < 18 ? '下午' : '晚上'
  return `${label} ${overview.value.rhythm.peak_hours[0].hour} 点`
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
function getColor(score) {
  // 掌握度单色顺序渐变（红→黄→绿），来自现状站点配色
  const stops = [
    [5, '#FF1A00'], [15, '#FF6600'], [25, '#FF9900'], [35, '#FFCC00'], [45, '#FFE600'],
    [55, '#D4E000'], [65, '#A8D500'], [75, '#52C200'], [85, '#00A300'], [100, '#006600'],
  ]
  return stops.find(s => score < s[0])?.[1] || '#006600'
}
const TYPE_DISPLAY = { choice: '选择题', fill: '填空题', judge: '判断题', essay: '简答题', calculation: '计算题', coding: '编程题' }
function getTypeDisplay(t) { return TYPE_DISPLAY[t] || t }

function goPractice(topic) {
  router.push({ path: '/generate-from-mastery', query: { topic } })
}

// ===== 30 天趋势（两个小图，避免双轴混图） =====
function renderTrendCharts() {
  const daily = overview.value.practice.daily
  if (!daily.length) return
  const ink = chartInk()
  const dates = daily.map(d => d.date)
  const counts = daily.map(d => d.count)
  const rates = daily.map(d => (d.count ? d.rate : null))

  const base = {
    grid: { left: 6, right: 6, top: 10, bottom: 4, containLabel: true },
    xAxis: {
      type: 'category', data: dates,
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: ink.muted, fontSize: 10, interval: 4 },
    },
  }

  if (countChartRef.value) {
    countChart = echarts.init(countChartRef.value)
    countChart.setOption({
      ...base,
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: p => `${p[0].name} · 做题 <b>${p[0].value}</b> 道` },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: 'rgba(128,140,170,.10)' } }, axisLabel: { color: ink.muted, fontSize: 10 } },
      series: [{
        type: 'bar', data: counts, barWidth: 6,
        itemStyle: { color: themeStore.brandColor, borderRadius: [3, 3, 0, 0] },
        emphasis: { itemStyle: { color: '#6c8cff' } },
      }],
    })
  }
  if (rateChartRef.value) {
    rateChart = echarts.init(rateChartRef.value)
    rateChart.setOption({
      ...base,
      tooltip: { trigger: 'axis', formatter: p => (p[0].value == null ? `${p[0].name} · 当天无做题` : `${p[0].name} · 正确率 <b>${p[0].value}%</b>`) },
      yAxis: { type: 'value', min: 0, max: 100, splitLine: { lineStyle: { color: 'rgba(128,140,170,.10)' } }, axisLabel: { color: ink.muted, fontSize: 10 } },
      series: [{
        type: 'line', data: rates, connectNulls: false,
        lineStyle: { color: themeStore.brandColor, width: 2 },
        symbol: 'circle', symbolSize: 7,
        itemStyle: { color: themeStore.brandColor, borderWidth: 2, borderColor: 'transparent' },
        areaStyle: { color: brandSoft(0.08) },
      }],
    })
  }
}

// ===== 数据加载 =====
async function loadData() {
  loading.value = true
  try {
    const uid = authStore.user.id
    const [ovRes, anRes] = await Promise.all([
      fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/evaluation/overview?user_id=${uid}`, {
        headers: { Authorization: `Bearer ${authStore.token}` },
      }).then(r => r.json()),
      fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/evaluation/deep-analysis?user_id=${uid}`, {
        headers: { Authorization: `Bearer ${authStore.token}` },
      }).then(r => r.json()).catch(() => ({ analysis: null })),
    ])
    overview.value = { ...defaultOverview(), ...(ovRes || {}) }
    const analysis = anRes?.analysis
    if (analysis?.summary) {
      aiSummary.value = analysis.summary
    } else {
      aiSummary.value = fallbackSummary()
    }
    generateDate.value = new Date().toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
    })
    await nextTick()
    renderTrendCharts()
  } catch {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

function fallbackSummary() {
  const o = overview.value
  const weak = o.mastery.weak_topics.slice(0, 2).map(w => w.topic).join('、')
  return [
    `近 30 天你做了 ${o.practice.total} 道题，正确率 ${o.practice.rate}%；`,
    o.mastery.avg_mastery ? `当前平均掌握度 ${o.mastery.avg_mastery}%，覆盖 ${o.mastery.topic_count} 个知识点；` : '掌握度数据还在积累中；',
    weak ? `目前最需要巩固的是「${weak}」；` : '',
    o.rhythm.max_streak ? `最长连续学习 ${o.rhythm.max_streak} 天，保持这个节奏！` : '从每天学一点开始，画像会更完整。',
  ].join('')
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
    const isLight = document.documentElement.getAttribute('data-theme') === 'light'
    const canvas = await html2canvas(reportContentRef.value, {
      scale: 2,
      useCORS: true,
      backgroundColor: isLight ? '#f4f6fb' : '#0b1220',
      logging: false,
      windowHeight: reportContentRef.value.scrollHeight,
      height: reportContentRef.value.scrollHeight,
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

function onResize() {
  countChart?.resize()
  rateChart?.resize()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  countChart?.dispose()
  rateChart?.dispose()
})
</script>

<style scoped>
.evaluation-report-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 30px 20px;
  }

.report-container {
  max-width: 880px;
  width: 100%;
  margin: 0 auto;
  padding: 28px 36px;
  border-radius: 18px;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--line-soft);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
}

[data-theme="dark"] .report-container {
  background: var(--well);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
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

/* AI 解读 */
.ai-section h3 { margin-bottom: 10px; }
.ai-loading-box {
  padding: 34px 20px;
  display: flex;
  justify-content: center;
}
.ai-summary-box {
  padding: 18px 20px 12px;
  border-radius: 14px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--brand) 8%, transparent), rgba(139,92,246,.08));
  border: 1px solid color-mix(in srgb, var(--brand) 16%, transparent);
}
.ai-summary-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.9;
  color: var(--text-primary);
  white-space: pre-wrap;
}
.ai-summary-foot {
  margin-top: 10px;
  text-align: right;
}
.ai-note {
  font-size: 11px;
  color: var(--text-muted);
}

/* 总览卡 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 22px;
}
.stat-card {
  padding: 14px 8px;
  border-radius: 12px;
  text-align: center;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.stat-number {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}
.stat-number small {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}
.stat-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
  display: block;
}

/* 趋势 */
.trend-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.trend-card {
  padding: 10px 14px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
.trend-title {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}
.trend-chart {
  height: 130px;
  width: 100%;
}

/* 分布 */
.report-section {
  margin-bottom: 26px;
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
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
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

/* 薄弱知识点 */
.weak-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 10px;
}
.weak-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-left: 3px solid #ef4444;
  transition: transform .2s;
}
.weak-card:hover { transform: translateY(-2px); }
.weak-topic {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.weak-score {
  font-size: 13px;
  font-weight: 700;
  color: #ef4444;
}
.weak-btn {
  flex-shrink: 0;
}

/* 知识点详情 */
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
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  border-left: 3px solid transparent;
}
.topic-row.status-weak { border-left-color: #ef4444; }
.topic-row.status-consolidate { border-left-color: #f59e0b; }
.topic-row.status-mastered { border-left-color: #22c55e; }
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
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
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
.topic-badge { font-size: 12px; min-width: 60px; }
.topic-more {
  margin-top: 10px;
  display: flex;
  justify-content: center;
}

/* 错题画像 */
.mistake-summary {
  display: flex;
  gap: 34px;
  margin-bottom: 14px;
}
.mistake-big {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  margin-right: 8px;
}
.mistake-label { font-size: 12px; color: var(--text-muted); }
.mistake-num { display: flex; flex-direction: column; gap: 2px; }
.mistake-panels {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 12px;
}
.mistake-panel {
  padding: 12px 14px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
.panel-title {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 10px;
}
.mistake-topic-list { display: flex; flex-direction: column; gap: 6px; }
.mistake-topic-row { display: flex; align-items: center; gap: 8px; }
.mistake-rank {
  width: 18px; height: 18px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; color: var(--brand);
  background: color-mix(in srgb, var(--brand) 12%, transparent);
}
.mistake-topic { width: 120px; font-size: 13px; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mistake-count { font-size: 12px; color: var(--text-secondary); width: 44px; text-align: right; flex-shrink: 0; }
.mistake-mini-bar {
  flex: 1;
  height: 5px;
  border-radius: 3px;
  background: rgba(239,68,68,.12);
  overflow: hidden;
}
.mistake-mini-fill {
  height: 100%;
  border-radius: 3px;
  background: #ef4444;
  min-width: 6px;
}
.type-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.type-chip {
  padding: 5px 12px;
  border-radius: 14px;
  font-size: 12px;
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255,255,255,.06);
}

/* 真题卷 */
.exam-summary {
  display: flex;
  gap: 34px;
  margin-bottom: 12px;
}
.exam-num { display: flex; flex-direction: column; gap: 2px; }
.exam-num span:last-child { font-size: 12px; color: var(--text-muted); }
.exam-big {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}
.exam-list { display: flex; flex-direction: column; gap: 6px; }
.exam-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  border: 1px solid rgba(255, 255, 255, 0.04);
}
.exam-name { flex: 1; font-size: 13px; color: var(--text-primary); }
.exam-date { font-size: 12px; color: var(--text-muted); }
.exam-score { font-size: 15px; font-weight: 700; }

/* 节奏日历 */
.rhythm-top {
  display: flex;
  gap: 34px;
  margin-bottom: 14px;
}
.rhythm-num { display: flex; flex-direction: column; gap: 2px; }
.rhythm-num span:last-child { font-size: 12px; color: var(--text-muted); }
.rhythm-big {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}
.rhythm-big small { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.rhythm-calendar-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.calendar-grid {
  display: grid;
  grid-auto-flow: column;
  grid-template-rows: repeat(7, 11px);
  grid-auto-columns: 11px;
  gap: 3px;
  justify-content: start;
}
.calendar-cell {
  width: 11px;
  height: 11px;
  border-radius: 3px;
  background: rgba(128, 140, 170, 0.10);
  cursor: default;
}
.calendar-cell.lv1 { background: color-mix(in srgb, var(--brand) 22%, transparent); }
.calendar-cell.lv2 { background: color-mix(in srgb, var(--brand) 45%, transparent); }
.calendar-cell.lv3 { background: color-mix(in srgb, var(--brand) 72%, transparent); }
.calendar-cell.lv4 { background: var(--brand); }
.calendar-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-muted);
}

/* 计划进度 */
.plan-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.plan-card {
  padding: 12px 14px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
.pc-title { font-size: 12px; color: var(--text-secondary); margin-bottom: 8px; }
.pc-body { display: flex; flex-direction: column; gap: 4px; }
.pc-big {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  font-variant-numeric: tabular-nums;
}
.pc-name {
  font-size: 13px;
  color: var(--text-primary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.pc-small { font-size: 11px; color: var(--text-muted); }
.pc-bar {
  margin-top: 6px;
  height: 6px;
  border-radius: 3px;
  background: color-mix(in srgb, var(--surface, #ffffff) 7%, transparent);
  overflow: hidden;
}
.pc-fill {
  height: 100%;
  border-radius: 3px;
  background: var(--brand);
  transition: width .6s ease;
}
.pc-fill.green { background: #22c55e; }

.empty-state {
  color: var(--text-muted);
  padding: 14px 0;
  text-align: center;
  font-size: 13px;
}
.empty-state.small { padding: 8px 0; font-size: 12px; }

@media (max-width: 760px) {
  .report-container { padding: 16px 14px; }
  .report-header { flex-direction: column; align-items: stretch; }
  .header-left { flex-wrap: wrap; }
  .stats-grid { grid-template-columns: repeat(3, 1fr); }
  .trend-grid { grid-template-columns: 1fr; }
  .mistake-panels { grid-template-columns: 1fr; }
  .plan-cards { grid-template-columns: 1fr; }
  .dist-label { min-width: 84px; font-size: 12px; }
  .stat-number { font-size: 20px; }
}
</style>