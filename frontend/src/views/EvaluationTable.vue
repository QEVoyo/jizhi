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

      <!-- ===== 友好加载 ===== -->
      <LoadingSpinner
        v-if="loading"
        variant="orbit"
        :size="80"
        :flow-steps="['正在读取你的全平台学习数据…', '评估 Agent 正在逐项评估…', '正在生成诊断与行动建议…']"
      />

      <!-- ===== 内容（2026-08-30：纯评估结论页——数据展示归学情报告，这里只出评级/诊断/行动） ===== -->
      <div v-else class="table-content" ref="reportContentRef">
        <!-- 1. 评级条（动画：徽章光环脉冲） -->
        <div class="rating-strip reveal-item" style="animation-delay: 0s">
          <span class="rating-badge" :style="{ color: ratingColor, borderColor: ratingColor + '66', background: ratingColor + '14' }">
            {{ rating }}
          </span>
          <span class="rating-meta">学习阶段：{{ stage }}</span>
          <span class="rating-meta muted">结论由全平台近 30 天真实使用数据生成 · 数据明细见「学情报告」</span>
        </div>

        <!-- 2. AI 深度诊断（评估核心，分块依次浮现） -->
        <div class="table-section diagnosis-section reveal-item" style="animation-delay: .12s">
          <div class="diagnosis-glow"></div>
          <h3>AI 深度诊断</h3>

          <div class="diag-core diag-step" style="animation-delay: .25s">
            <span class="diag-core-label">核心问题</span>
            <span class="diag-core-text">{{ coreIssue }}</span>
          </div>

          <div class="diag-cause diag-step" style="animation-delay: .45s">
            <span class="diag-cause-label">📌 归因</span>
            <p class="diag-cause-text">{{ cause }}</p>
          </div>

          <div class="diag-strength diag-step" style="animation-delay: .65s">
            <span class="diag-strength-label">✅ 你的优势</span>
            <span class="diag-strength-text">{{ strengths }}</span>
          </div>

          <div class="diag-actions-block diag-step" style="animation-delay: .85s">
            <span class="diag-actions-label">🎯 建议行动</span>
            <div class="diag-action-list">
              <div
                v-for="(a, i) in adviceActions"
                :key="i"
                class="diag-action-row action-row"
                :style="{ animationDelay: (0.95 + i * 0.18) + 's' }"
              >
                <span class="diag-action-index">{{ i + 1 }}</span>
                <span class="diag-action-text">{{ a }}</span>
              </div>
            </div>
          </div>

          <div class="persona-line diag-step" style="animation-delay: 1.5s">
            <span class="persona-type">小基眼中的你：{{ personaType }}</span>
            <span class="persona-desc">{{ personaDesc }}</span>
            <span
              v-for="(t, i) in personaTags"
              :key="t"
              class="persona-tag tag-pop"
              :style="{ animationDelay: (1.6 + i * 0.1) + 's' }"
            >{{ t }}</span>
          </div>
        </div>

        <!-- 3. 行动清单（逐行错峰滑入） -->
        <div class="table-section reveal-item" style="animation-delay: .9s" v-if="weakTopics.length">
          <h3>待攻克清单</h3>
          <div class="weak-list">
            <div
              v-for="(w, i) in weakTopics"
              :key="w.topic"
              class="weak-row weak-row-anim"
              :style="{ animationDelay: (1.0 + i * 0.12) + 's' }"
            >
              <span class="weak-rank-dot" :style="{ background: w.score < 40 ? '#EF4444' : '#F59E0B' }"></span>
              <span class="weak-name">{{ w.topic }}</span>
              <button class="glass-btn small-btn" @click="goPractice(w.topic)">去练习 →</button>
            </div>
          </div>
        </div>

        <!-- 4. 主 CTA -->
        <div class="cta-block reveal-item" style="animation-delay: 1.1s">
          <div class="cta-copy">
            <div class="cta-title">把诊断变成计划</div>
            <div class="cta-desc">按上面的薄弱项生成一个自定义计划，AI 拆解每日任务，逐天推进</div>
          </div>
          <button class="glass-btn primary generate-plan-btn" @click="goToPlan">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
            生成自定义计划
          </button>
          <button class="glass-btn" @click="copyDiagnosis">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
              <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
            </svg>
            复制诊断
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { ElMessage } from 'element-plus'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()

const loading = ref(true)
const pdfExporting = ref(false)
const generateDate = ref('')
const reportContentRef = ref(null)

const rating = ref('')
const ratingColor = ref(themeStore.brandColor)
const stage = ref('')
const weakTopics = ref([])

const coreIssue = ref('')
const cause = ref('')
const strengths = ref('')
const adviceActions = ref([])
const personaType = ref('')
const personaDesc = ref('')
const personaTags = ref([])

// 用于「生成自定义计划」透传
const planPayload = ref({ weaknesses: '', strengths: '', coreIssue: '', advice: '', stage: '', difficulty: 13 })

const RATING_COLORS = () => ({
  '巅峰期': '#FFD700', '卓越期': '#8B5CF6', '精进期': themeStore.brandColor, '筑基期': '#F59E0B', '开拓期': '#EF4444',
})

async function loadData() {
  loading.value = true
  try {
    const uid = authStore.user.id
    const base = import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'
    const headers = { Authorization: `Bearer ${authStore.token}` }
    const [ovRes, anRes] = await Promise.all([
      fetch(`${base}/evaluation/overview?user_id=${uid}`, { headers }).then(r => r.json()),
      fetch(`${base}/evaluation/deep-analysis?user_id=${uid}`, { headers })
        .then(r => r.json())
        .catch(() => ({ analysis: null })),
    ])
    const ov = ovRes || {}
    const analysis = anRes?.analysis || null

    // 六维仅作内部评分依据（不对外展示数据面板；明细在学情报告）
    const rhythm = ov.rhythm || {}
    const mastery = ov.mastery || { avg_mastery: 0, topic_count: 0, weak_topics: [], mistakes: { total: 0, conquered: 0, conquered_rate: 0 } }
    const practice = ov.practice || { total: 0, rate: 0 }
    const exams = ov.exams || { count: 0, avg: 0, best: 0 }
    const plan = ov.subject_plan || { tasks_total: 0, tasks_done: 0, completion: 0 }

    const investScore = rhythm.active_days ? Math.min(100, Math.round(rhythm.active_days / 90 * 100)) : 0
    const dims = [
      { name: '知识基础', score: mastery.avg_mastery || 0 },
      { name: '做题正确率', score: practice.rate || 0 },
      { name: '错题攻克率', score: mastery.mistakes.conquered_rate || 0 },
      { name: '真题实战', score: Math.round(exams.avg || 0) },
      { name: '计划推进', score: plan.completion || 0 },
      { name: '习惯坚持', score: investScore },
    ]
    weakTopics.value = mastery.weak_topics.slice(0, 5)
    stage.value = authStore.user?.learning_stage || '未设置'

    // ===== 规则兜底诊断（AI 结论到达即覆盖） =====
    const strong = dims.filter(d => d.score >= 70)
    const weak = dims.filter(d => d.score < 60)
    const strongText = strong.length ? strong.slice(0, 2).map(d => d.name).join('、') : '暂无明显优势'
    const weakText = weak.length ? weak.slice(0, 2).map(d => d.name).join('、') : '暂无薄弱项'
    const coreText = weak.length ? `${weak.map(d => d.name).join('、')} 偏弱` : '各维度发展均衡'
    const adviceText = weak.length ? `优先攻克 ${weak[0].name}，每天 3 题起` : '保持当前节奏，稳步提升'

    coreIssue.value = coreText
    cause.value = weak.length
      ? `${weak.map(d => `${d.name}（${d.score}%）`).join('、')} 明显低于其他维度，说明练习投入与知识输出之间存在缺口，需要针对性补练而非泛泛刷题。`
      : '各维度发展均衡，继续按当前方式积累即可。'
    strengths.value = strongText
    adviceActions.value = [
      adviceText,
      weak.length > 1 ? `以「${weak[0].name}」为本周主线，穿插复习「${weak[1].name}」` : '把本周目标拆成每天 20 分钟的小任务',
      ov.mastery?.weak_topics?.length ? `从「${ov.mastery.weak_topics[0].topic}」开始，用一次练习评估真实水平` : '完成一次诊断，让数据更立体',
    ]

    if (analysis?.diagnosis) {
      const d = analysis.diagnosis
      if (d.core_issue) coreIssue.value = d.core_issue
      if (d.cause) cause.value = d.cause
      if (d.strengths) strengths.value = d.strengths
      if (Array.isArray(d.advice_actions) && d.advice_actions.length) adviceActions.value = d.advice_actions
      else if (d.advice) adviceActions.value = [d.advice, ...adviceActions.value.slice(1)]
      if (d.rating && RATING_COLORS()[d.rating]) {
        rating.value = d.rating
        ratingColor.value = RATING_COLORS()[d.rating]
      }
      planPayload.value = {
        weaknesses: d.weaknesses || weakText,
        strengths: d.strengths || strongText,
        coreIssue: d.core_issue || coreText,
        advice: d.advice || adviceText,
        stage: stage.value,
        difficulty: Number(d.base_difficulty) || 7,
      }
    }
    if (!rating.value) {
      const total = dims.reduce((s, d) => s + d.score, 0)
      const avg = dims.length ? Math.round(total / dims.length) : 0
      const localRating = avg >= 85 ? '巅峰期' : avg >= 70 ? '卓越期' : avg >= 50 ? '精进期' : avg >= 30 ? '筑基期' : '开拓期'
      rating.value = localRating
      ratingColor.value = RATING_COLORS()[localRating]
      planPayload.value = {
        weaknesses: weakText, strengths: strongText, coreIssue: coreText,
        advice: adviceText, stage: stage.value,
        difficulty: avg >= 70 ? 13 : avg >= 50 ? 9 : 5,
      }
    }

    // ===== 人格一行（AI 优先，规则兜底） =====
    if (analysis?.personality) {
      personaType.value = analysis.personality.type
      personaDesc.value = analysis.personality.desc
      personaTags.value = analysis.personality.tags || []
    } else {
      personaType.value = strong.length ? `${strong[0].name}型学习者` : '均衡型学习者'
      personaDesc.value = `优势在 ${strongText}，待提升 ${weakText}`
      personaTags.value = ['基于评估生成']
    }

    generateDate.value = new Date().toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    })
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

function goPractice(topic) {
  router.push({ path: '/generate-from-mastery', query: { topic } })
}

function copyDiagnosis() {
  const lines = [
    `智能诊断报告（${generateDate.value}）`,
    `评级：${rating.value}`,
    `核心问题：${coreIssue.value}`,
    `归因：${cause.value}`,
    `优势：${strengths.value}`,
    ...adviceActions.value.map((a, i) => `${i + 1}. ${a}`),
  ]
  navigator.clipboard.writeText(lines.join('\n')).then(() => {
    ElMessage.success('诊断已复制')
  }).catch(() => {
    ElMessage.warning('复制失败，请手动复制')
  })
}

function goToPlan() {
  const p = planPayload.value
  let planName = '综合能力提升'
  const weakList = (p.weaknesses || '').split('、').filter(Boolean)
  const strongList = (p.strengths || '').split('、').filter(Boolean)
  if (weakList.length && p.weaknesses !== '暂无薄弱项') {
    planName = strongList.length && p.strengths !== '暂无明显优势'
      ? `强化 ${strongList[0]} · 攻克 ${weakList[0]}`
      : `攻克 ${weakList[0]}`
  }
  const params = new URLSearchParams({
    name: planName,
    weaknesses: p.weaknesses || '',
    strengths: p.strengths || '',
    coreIssue: p.coreIssue || '',
    advice: p.advice || '',
    stage: p.stage || '大学',
    difficulty: p.difficulty || 7,
    keywords: p.weaknesses || '',
  })
  router.push(`/plan-preview?${params.toString()}`)
}

function goBack() {
  router.push('/evaluation-center')
}

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
  }

.table-container {
  max-width: 900px;
  width: 100%;
  padding: 32px 40px;
  border-radius: 20px;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.06);
  box-shadow: 0 8px 48px rgba(0,0,0,0.08);
}
[data-theme="dark"] .table-container {
  background: var(--well);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: all 0.3s ease;
}
.glass-btn:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
  border-color: var(--line-soft);
  transform: translateY(-2px);
}
.glass-btn:active {
  transform: scale(0.97);
}
.glass-btn.primary {
  color: var(--brand);
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  border-color: color-mix(in srgb, var(--brand) 10%, transparent);
}
.glass-btn.primary:hover {
  background: color-mix(in srgb, var(--brand) 14%, transparent);
  border-color: color-mix(in srgb, var(--brand) 20%, transparent);
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
.small-btn {
  padding: 5px 12px;
  font-size: 13px;
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

/* ===== 入场与结论动效（2026-08-30：结论依次浮现，尊重系统减少动态效果） ===== */
.reveal-item {
  animation: riseIn 0.55s cubic-bezier(0.22, 0.8, 0.36, 1) both;
}
@keyframes riseIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: none; }
}
.diag-step {
  animation: riseIn 0.5s cubic-bezier(0.22, 0.8, 0.36, 1) both;
}
.action-row {
  animation: slideIn 0.45s cubic-bezier(0.22, 0.8, 0.36, 1) both;
}
@keyframes slideIn {
  from { opacity: 0; transform: translateX(-14px); }
  to { opacity: 1; transform: none; }
}
.diag-action-index {
  animation: popIn 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}
@keyframes popIn {
  from { opacity: 0; transform: scale(0.3); }
  to { opacity: 1; transform: scale(1); }
}
.weak-row-anim {
  animation: slideIn 0.45s cubic-bezier(0.22, 0.8, 0.36, 1) both;
}
.tag-pop {
  animation: tagPop 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both;
}
@keyframes tagPop {
  from { opacity: 0; transform: scale(0.6) translateY(6px); }
  to { opacity: 1; transform: none; }
}

/* 评级条 */
.rating-strip {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 20px;
  padding: 12px 16px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  border: 1px solid rgba(255,255,255,0.04);
}
.rating-badge {
  position: relative;
  font-size: 17px;
  font-weight: 700;
  padding: 4px 16px;
  border-radius: 18px;
  border: 1px solid;
}
.rating-badge::after {
  content: '';
  position: absolute;
  inset: -5px;
  border-radius: 22px;
  border: 1px solid currentColor;
  opacity: 0;
  animation: badgeRipple 2.6s ease-out 1.2s infinite;
}
@keyframes badgeRipple {
  0% { opacity: .55; transform: scale(.92); }
  70%, 100% { opacity: 0; transform: scale(1.18); }
}
.rating-meta {
  font-size: 13px;
  color: var(--text-secondary);
}
.rating-meta.muted {
  color: var(--text-muted);
}

/* AI 深度诊断 */
.diagnosis-section {
  background: linear-gradient(135deg, color-mix(in srgb, var(--brand) 4%, transparent), rgba(139,92,246,0.04));
  border: 1px solid color-mix(in srgb, var(--brand) 6%, transparent);
  border-radius: 12px;
  padding: 18px 20px;
  position: relative;
  overflow: hidden;
}
.diagnosis-glow {
  position: absolute;
  top: -30%;
  right: -10%;
  width: 60%;
  height: 160%;
  background: radial-gradient(ellipse, color-mix(in srgb, var(--brand) 4%, transparent), transparent 70%);
  pointer-events: none;
}
.diag-core {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 12px;
}
.diag-core-label {
  font-size: 12px;
  color: var(--brand);
  flex-shrink: 0;
  font-weight: 600;
}
.diag-core-text {
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}
.diag-cause {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
.diag-cause-label {
  font-size: 12px;
  color: var(--text-secondary);
  flex-shrink: 0;
  font-weight: 600;
}
.diag-cause-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.8;
  color: var(--text-secondary);
}
.diag-strength {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
}
.diag-strength-label {
  font-size: 12px;
  color: color-mix(in srgb, #22C55E 65%, var(--text-primary));
  flex-shrink: 0;
  font-weight: 600;
}
.diag-strength-text {
  font-size: 13px;
  color: var(--text-primary);
}
.diag-actions-block {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
}
.diag-actions-label {
  font-size: 12px;
  color: color-mix(in srgb, #F59E0B 70%, var(--text-primary));
  flex-shrink: 0;
  font-weight: 600;
}
.diag-action-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.diag-action-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.diag-action-index {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(245,158,11,.14);
  color: color-mix(in srgb, #F59E0B 70%, var(--text-primary));
  font-size: 11px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.diag-action-text {
  font-size: 13px;
  color: var(--text-primary);
}

/* 人格一行 */
.persona-line {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding-top: 10px;
  border-top: 1px dashed var(--line-soft);
}
.persona-type {
  font-size: 13px;
  font-weight: 600;
  color: color-mix(in srgb, #8B5CF6 60%, var(--text-primary));
}
.persona-desc {
  font-size: 12px;
  color: var(--text-secondary);
}
.persona-tag {
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  background: rgba(139,92,246,.10);
  color: color-mix(in srgb, #a78bfa 60%, var(--text-primary));
  border: 1px solid rgba(139,92,246,.14);
}

/* 待攻克清单 */
.weak-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.weak-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  border: 1px solid rgba(255,255,255,0.05);
}
.weak-rank-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.weak-name {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

/* 主 CTA */
.cta-block {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  padding: 18px 20px;
  border-radius: 14px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--brand) 10%, transparent), rgba(139,92,246,0.10));
  border: 1px solid color-mix(in srgb, var(--brand) 16%, transparent);
}
.cta-copy {
  flex: 1;
  min-width: 220px;
}
.cta-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}
.cta-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
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
  .cta-block { flex-direction: column; align-items: stretch; }
  .cta-block .glass-btn { justify-content: center; }
}

/* 尊重系统「减少动态效果」：关闭全部入场动画 */
@media (prefers-reduced-motion: reduce) {
  .reveal-item, .diag-step, .action-row, .weak-row-anim, .tag-pop,
  .diag-action-index, .rating-badge::after {
    animation: none !important;
  }
}
</style>