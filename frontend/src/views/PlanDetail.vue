<template>
  <div class="plan-detail-page">
    <div class="detail-container">
      <!-- ===== 顶部 ===== -->
      <div class="detail-header">
        <div class="header-left">
          <button class="glass-btn back-btn" @click="goBack">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            返回
          </button>
          <h1>{{ plan.name || '规划详情' }}</h1>
          <span class="status-badge" :data-status="plan.status">
            {{ plan.status === 'active' ? '进行中' : plan.status === 'pending' ? '待开始' : '已完成' }}
          </span>
        </div>
        <div class="header-actions">
          <button class="glass-btn" @click="refreshData" :disabled="loading">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spinning: loading }">
              <path d="M23 4v6h-6M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="divider"></div>

      <!-- ===== 规划概览 ===== -->
      <div class="overview-card">
        <div class="overview-grid">
          <div class="overview-item">
            <span class="overview-label">📅 周期</span>
            <span class="overview-value">{{ plan.start_date }} → {{ plan.end_date }}</span>
          </div>
          <div class="overview-item">
            <span class="overview-label">🎯 难度基数</span>
            <span class="overview-value">{{ plan.difficulty || 5 }}</span>
          </div>
          <div class="overview-item">
            <span class="overview-label">⏱️ 每日时长</span>
            <span class="overview-value">{{ plan.daily_minutes || 30 }} 分钟</span>
          </div>
          <div class="overview-item">
            <span class="overview-label">📊 总进度</span>
            <span class="overview-value">{{ progress }}%</span>
          </div>
        </div>
        <div class="overview-progress">
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: progress + '%' }"></div>
          </div>
        </div>
        <div class="overview-keywords">
          <span class="keywords-label">📌 关键词：</span>
          <span class="keywords-value">{{ plan.keywords || '无' }}</span>
        </div>
      </div>

      <!-- ===== 日期选择栏 ===== -->
      <div class="date-bar">
        <div
          v-for="day in days"
          :key="day.date"
          class="date-item"
          :class="{
            active: selectedDate === day.date,
            completed: day.status === 'completed',
            in_progress: day.status === 'active' || day.status === 'pending',
            locked: day.status === 'locked'
          }"
          @click="selectDate(day)"
        >
          <span class="date-day">{{ day.day }}</span>
          <span class="date-num">{{ day.month }}/{{ day.num }}</span>  <!-- 👈 显示 M/D -->
          <span class="date-status-icon" v-if="day.status === 'completed'">✓</span>
          <span class="date-status-icon" v-else-if="day.status === 'active' || day.status === 'pending'">●</span>
          <span class="date-status-icon" v-else-if="day.status === 'locked'">🔒</span>
        </div>
      </div>

      <!-- ===== 当日内容 ===== -->
      <div class="day-content" v-if="selectedDayData">
        <div class="day-header">
          <h3>📅 {{ formatDate(selectedDate) }}</h3>
          <span class="day-progress">{{ dayCompletedCount }}/{{ dayTasks.length }} 已完成</span>
        </div>

        <!-- 学习内容 -->
        <div class="content-section" v-if="dayContentItems.length">
          <div class="section-title">📖 学习内容</div>
          <div
            v-for="(item, idx) in dayContentItems"
            :key="idx"
            class="content-item"
          >
            <div class="content-topic">{{ item.topic }}</div>
            <div class="content-body">{{ item.description || item.topic + ' 核心概念讲解' }}</div>
          </div>
        </div>

        <!-- 题目列表 -->
        <div class="content-section" v-if="dayQuestions.length">
          <div class="section-title">📝 今日题目（{{ dayQuestions.length }} 道）</div>
          <div class="question-table">
            <div class="question-header">
              <span class="q-idx">#</span>
              <span class="q-topic">知识点</span>
              <span class="q-type">题型</span>
              <span class="q-difficulty">难度</span>
              <span class="q-status">状态</span>
              <span class="q-action">操作</span>
            </div>
            <div
              v-for="(q, idx) in dayQuestions"
              :key="q.id || idx"
              class="question-row"
            >
              <span class="q-idx">{{ idx + 1 }}</span>
              <span class="q-topic">{{ q.topic || '未知' }}</span>
              <span class="q-type">{{ q.question_type || '选择题' }}</span>
              <span class="q-difficulty">{{ getDifficultyText(q.difficulty_score) }}</span>
              <span class="q-status" :data-status="q.status || 'pending'">
                {{ q.status === 'completed' ? '✅ 已完成' : q.status === 'active' ? '🔄 进行中' : '⏳ 待开始' }}
              </span>
              <span class="q-action">
                <button
                  class="glass-btn primary small"
                  @click="goToQuestion(q)"
                  :disabled="q.status === 'completed'"
                >
                  {{ q.status === 'completed' ? '已掌握' : '▶ 去练习' }}
                </button>
              </span>
            </div>
          </div>
        </div>

        <!-- 学习视频 -->
        <div class="content-section" v-if="dayVideos.length">
          <div class="section-title">📺 学习视频</div>
          <div
            v-for="(v, idx) in dayVideos"
            :key="idx"
            class="video-item"
          >
            <span class="video-topic">{{ v.topic }}</span>
            <span class="video-status">⏳ 待上线</span>
          </div>
        </div>

        <div v-if="!dayTasks.length" class="empty-state">
          <span>📭 当日暂无任务</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getPlanDetail, updateTaskStatus } from '@/api/learningPlan'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const plan = ref({})
const tasks = ref([])
const loading = ref(false)
const selectedDate = ref('')

const days = computed(() => {
  if (!plan.value.start_date || !plan.value.end_date) return []
  const start = new Date(plan.value.start_date)
  const end = new Date(plan.value.end_date)
  const result = []
  let current = new Date(start)
  let index = 0

  while (current <= end) {
    const dateStr = current.toISOString().slice(0, 10)
    const dayTasks = tasks.value.filter(t => t.date === dateStr)
    const allDone = dayTasks.length > 0 && dayTasks.every(t => t.status === 'completed')
    const anyActive = dayTasks.some(t => t.status === 'active')

    const isFirstDay = index === 0
    let isUnlocked = isFirstDay
    if (!isFirstDay) {
      const prevDate = new Date(current)
      prevDate.setDate(prevDate.getDate() - 1)
      const prevDateStr = prevDate.toISOString().slice(0, 10)
      const prevTasks = tasks.value.filter(t => t.date === prevDateStr)
      const prevAllDone = prevTasks.length > 0 && prevTasks.every(t => t.status === 'completed')
      isUnlocked = prevAllDone
    }

    let status = 'locked'
    if (isUnlocked) {
      if (allDone) status = 'completed'
      else if (anyActive) status = 'active'
      else status = 'pending'
    }

    result.push({
      date: dateStr,
      day: ['日', '一', '二', '三', '四', '五', '六'][current.getDay()],
      month: current.getMonth() + 1,    // 👈 新增月份
      num: current.getDate(),
      status: status
    })
    current.setDate(current.getDate() + 1)
    index++
  }
  return result
})

const selectedDayData = computed(() => {
  return days.value.find(d => d.date === selectedDate.value)
})

const dayTasks = computed(() => {
  return tasks.value.filter(t => t.date === selectedDate.value)
})

const dayContentItems = computed(() => {
  return dayTasks.value.filter(t => t.type === '学习内容')
})

const dayQuestions = computed(() => {
  return dayTasks.value.filter(t => t.type === '做题')
})

const dayVideos = computed(() => {
  return dayTasks.value.filter(t => t.type === '学习视频')
})

const dayCompletedCount = computed(() => {
  return dayTasks.value.filter(t => t.status === 'completed').length
})

const progress = computed(() => {
  if (!tasks.value.length) return 0
  const done = tasks.value.filter(t => t.status === 'completed').length
  return Math.round((done / tasks.value.length) * 100)
})

function getDifficultyText(score) {
  if (!score) return '-'
  if (score <= 3) return '简单'
  if (score <= 7) return '中等'
  return '困难'
}

function selectDate(day) {
  if (day.status === 'locked') {
    ElMessage.warning('该日期尚未解锁，请先完成前一天任务')
    return
  }
  selectedDate.value = day.date
}

function goToQuestion(q) {
  if (q.status === 'completed') {
    ElMessage.info('该题目已掌握')
    return
  }

  if (q.status !== 'active') {
    updateTaskStatus(q.id, 'active').catch(() => {})
  }

  const questionData = {
    id: q.id,
    title: q.topic || '题目',
    topic: q.topic || '',
    category: plan.value.keywords || plan.value.major || '通用',
    question_type: q.question_type || 'choice',
    difficulty_score: q.difficulty_score || 5,
    question_content: q.question_content || '',
    options: q.options || {},
    answer: q.answer || '',
    hint: q.hint || ''
  }

  sessionStorage.setItem('current_question', JSON.stringify(questionData))

  router.push({
    path: `/do-question/${q.id}`,
    query: {
      topic: q.topic || '',
      questionType: q.question_type || '选择题',
      difficulty: q.difficulty_score || 5,
      planId: plan.value.id,
      question: q.question_content || '',
      options: q.options || [],
      answer: q.answer || ''
    }
  })
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

async function loadData() {
  const id = route.params.id
  if (!id) {
    ElMessage.error('规划不存在')
    return
  }
  loading.value = true
  try {
    const data = await getPlanDetail(id)
    plan.value = data
    tasks.value = data.tasks || []

    // 默认选中第一个非锁定日
    const firstUnlocked = days.value.find(d => d.status !== 'locked')
    if (firstUnlocked) {
      selectedDate.value = firstUnlocked.date
    } else if (tasks.value.length) {
      selectedDate.value = tasks.value[0].date || plan.value.start_date
    } else {
      selectedDate.value = plan.value.start_date
    }
  } catch (error) {
    console.error('加载失败:', error)
    ElMessage.error('加载规划失败')
  } finally {
    loading.value = false
  }
}

function refreshData() {
  loadData()
  ElMessage.success('已刷新')
}

function goBack() {
  router.push('/learning-plan')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
/* 样式基本不变，只改 date-num 和布局 */
.plan-detail-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 30px 20px;
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
}
[data-theme="light"] .plan-detail-page {
  background-image: url('/assets/bg/resource_lib_bg.jpg');
}
[data-theme="dark"] .plan-detail-page {
  background-image: url('/assets/bg/resource_lib_bl.jpg');
}

.detail-container {
  max-width: 960px;
  width: 100%;
  padding: 28px 36px;
  border-radius: 20px;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.06);
  box-shadow: 0 8px 48px rgba(0,0,0,0.08);
}
[data-theme="dark"] .detail-container {
  background: rgba(0,0,0,0.30);
}

.detail-header {
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
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.status-badge {
  font-size: 12px;
  padding: 2px 12px;
  border-radius: 12px;
  font-weight: 500;
}
.status-badge[data-status="active"] {
  background: rgba(64,158,255,0.10);
  color: #409EFF;
}
.status-badge[data-status="pending"] {
  background: rgba(245,158,11,0.10);
  color: #F59E0B;
}
.status-badge[data-status="completed"] {
  background: rgba(34,197,94,0.10);
  color: #22C55E;
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
.glass-btn:active { transform: scale(0.97); }
.glass-btn.primary {
  color: #409EFF;
  background: rgba(64,158,255,0.08);
  border-color: rgba(64,158,255,0.10);
}
.glass-btn.primary:hover {
  background: rgba(64,158,255,0.14);
  border-color: rgba(64,158,255,0.20);
}
.glass-btn .icon { width: 18px; height: 18px; }
.glass-btn.small { padding: 4px 12px; font-size: 12px; }
.back-btn .icon { width: 20px; height: 20px; }
.glass-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }
.spinning { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
  margin: 16px 0 20px;
}

.overview-card {
  padding: 16px 20px;
  border-radius: 12px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  margin-bottom: 16px;
}
.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 12px;
}
.overview-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.overview-label {
  font-size: 11px;
  color: var(--text-muted);
}
.overview-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.overview-progress {
  margin-top: 10px;
}
.overview-progress .progress-track {
  height: 6px;
  border-radius: 3px;
  background: rgba(255,255,255,0.06);
  overflow: hidden;
}
.overview-progress .progress-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, #409EFF, #8B5CF6);
  transition: width 0.6s ease;
}
.overview-keywords {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(255,255,255,0.04);
  font-size: 13px;
}
.keywords-label {
  color: var(--text-muted);
}
.keywords-value {
  color: var(--text-primary);
  font-weight: 500;
}

.date-bar {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding: 8px 0 12px;
  margin-bottom: 16px;
}
.date-bar::-webkit-scrollbar { height: 3px; }
.date-bar::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.10);
  border-radius: 2px;
}
.date-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 10px;
  min-width: 46px;  /* 👈 加宽一点，防止 M/D 显示不下 */
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
}
.date-item:hover {
  background: rgba(255,255,255,0.06);
}
.date-item.active {
  background: rgba(64,158,255,0.10);
  border-color: rgba(64,158,255,0.20);
}
.date-item.completed .date-num { color: #22C55E; }
.date-item.in_progress .date-num { color: #409EFF; }
.date-item.locked {
  opacity: 0.35;
  cursor: not-allowed;
}
.date-item.locked:hover { background: transparent; }
.date-item .date-day { font-size: 10px; color: var(--text-muted); }
.date-item .date-num { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.date-status-icon { font-size: 8px; margin-top: 1px; }

.day-content {
  margin-top: 4px;
}
.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.day-header h3 {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.day-progress {
  font-size: 13px;
  color: var(--text-muted);
}

.content-section {
  margin-bottom: 18px;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}

.content-item {
  padding: 10px 14px;
  border-radius: 8px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  margin-bottom: 6px;
}
.content-topic {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 14px;
}
.content-body {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
  line-height: 1.6;
}

.question-table {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.04);
}
.question-header {
  display: grid;
  grid-template-columns: 40px 1fr 80px 60px 80px 90px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  background: rgba(255,255,255,0.02);
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.question-row {
  display: grid;
  grid-template-columns: 40px 1fr 80px 60px 80px 90px;
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  align-items: center;
  border-bottom: 1px solid rgba(255,255,255,0.02);
}
.question-row:hover {
  background: rgba(255,255,255,0.02);
}
.question-row:last-child { border-bottom: none; }
.q-idx { font-weight: 600; color: var(--text-muted); }
.q-topic { color: var(--text-primary); }
.q-type { font-size: 12px; }
.q-difficulty { font-size: 12px; font-weight: 500; }
.q-status { font-size: 12px; }
.q-status[data-status="completed"] { color: #22C55E; }
.q-status[data-status="active"] { color: #409EFF; }
.q-status[data-status="pending"] { color: var(--text-muted); }
.q-action { display: flex; justify-content: center; }

.video-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 14px;
  border-radius: 8px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  margin-bottom: 4px;
}
.video-topic { font-weight: 500; color: var(--text-primary); }
.video-status { font-size: 12px; color: var(--text-muted); }

.empty-state {
  text-align: center;
  padding: 30px 20px;
  color: var(--text-muted);
}

@media (max-width: 768px) {
  .detail-container { padding: 16px; }
  .detail-header { flex-direction: column; align-items: stretch; }
  .overview-grid { grid-template-columns: 1fr 1fr; }
  .question-header, .question-row {
    grid-template-columns: 30px 1fr 60px 40px 60px 70px;
    font-size: 12px;
    padding: 4px 8px;
  }
  .q-action .glass-btn { font-size: 11px; padding: 3px 8px; }
}
</style>