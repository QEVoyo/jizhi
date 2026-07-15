<template>
  <div class="plan-preview-page">
    <div class="preview-container">
      <!-- ===== 顶部 ===== -->
      <div class="preview-header">
        <div class="header-left">
          <button class="glass-btn back-btn" @click="goBack">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            返回
          </button>
          <h1>规划预览</h1>
          <span class="preview-badge">📋 预览</span>
        </div>
        <div class="header-actions">
          <button class="glass-btn primary" @click="confirmPlan" :disabled="confirming">
            {{ confirming ? '保存中...' : '✅ 确认生成' }}
          </button>
        </div>
      </div>

      <div class="divider"></div>

      <!-- ===== 规划基本信息 ===== -->
      <div class="preview-card info-card">
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">规划名称</span>
            <input class="glass-input" v-model="planInfo.name" placeholder="输入规划名称" />
          </div>
          <div class="info-item">
            <span class="info-label">学习阶段</span>
            <select class="glass-input" v-model="planInfo.stage" @change="onStageChange">
              <option value="小学">小学</option>
              <option value="初中">初中</option>
              <option value="高中">高中</option>
              <option value="大学">大学</option>
              <option value="研究生">研究生</option>
              <option value="职场">职场</option>
            </select>
          </div>
          <div class="info-item">
            <span class="info-label">年级</span>
            <select class="glass-input" v-model="planInfo.grade">
              <option v-for="g in gradeOptions" :key="g" :value="g">{{ g }}</option>
            </select>
          </div>
          <div class="info-item">
            <span class="info-label">专业/方向</span>
            <input class="glass-input" v-model="planInfo.major" placeholder="如：计算机科学" />
          </div>
          <div class="info-item">
            <span class="info-label">难度基数 <span class="hint">(1-20)</span></span>
            <input class="glass-input" type="number" v-model="planInfo.difficulty" min="1" max="20" />
          </div>
          <div class="info-item">
            <span class="info-label">每日学习时长</span>
            <select class="glass-input" v-model="planInfo.dailyMinutes">
              <option :value="15">15 分钟</option>
              <option :value="30">30 分钟</option>
              <option :value="45">45 分钟</option>
              <option :value="60">60 分钟</option>
              <option :value="90">90 分钟</option>
            </select>
          </div>
          <div class="info-item">
            <span class="info-label">开始日期</span>
            <input class="glass-input" type="date" v-model="planInfo.startDate" />
          </div>
          <div class="info-item">
            <span class="info-label">结束日期</span>
            <input class="glass-input" type="date" v-model="planInfo.endDate" />
          </div>
        </div>
        <div class="info-keywords">
          <span class="info-label">知识点 <span class="hint">（AI 会拆分为多个子知识点）</span></span>
          <input class="glass-input" v-model="planInfo.keywords" placeholder="如：哈希表、唐诗、民法" />
        </div>
      </div>

      <!-- ===== Agent 调用状态 ===== -->
      <div v-if="agentLoading" class="agent-status">
        <div class="agent-spinner"></div>
        <span>🤖 正在调用生成 Agent...</span>
        <span class="agent-progress">{{ agentProgress }}</span>
      </div>

      <!-- ===== AI 生成的任务预览 ===== -->
      <div v-else class="preview-card tasks-card">
        <div class="tasks-header">
          <h3>📚 生成的学习任务</h3>
          <span class="task-count">{{ tasks.length }} 个任务</span>
        </div>

        <div v-if="!tasks.length" class="empty-state">
          <div class="empty-icon">📋</div>
          <div class="empty-text">点击「生成任务」让 AI 为你规划</div>
          <button class="glass-btn primary" @click="generateTasks">🚀 生成任务</button>
        </div>

        <div v-else>
          <!-- 学习内容 -->
          <div v-if="contentTasks.length" class="task-group">
            <div class="task-group-title">📖 学习内容</div>
            <div v-for="(task, idx) in contentTasks" :key="'c-' + idx" class="task-item content-item">
              <div class="task-icon">📖</div>
              <div class="task-content">
                <div class="task-topic">{{ task.topic }}</div>
                <div class="task-desc">{{ task.description }}</div>
              </div>
            </div>
          </div>

          <!-- 做题 -->
          <div v-if="questionTasks.length" class="task-group">
            <div class="task-group-title">📝 做题（{{ questionTasks.length }} 道）</div>
            <div class="question-table">
              <div class="question-header">
                <span>#</span>
                <span>知识点</span>
                <span>题型</span>
                <span>操作</span>
              </div>
              <div v-for="(task, idx) in questionTasks" :key="'q-' + idx" class="question-row">
                <span>{{ idx + 1 }}</span>
                <span>{{ task.topic }}</span>
                <span>{{ task.question_type || '选择题' }}</span>
                <span>
                  <button class="glass-btn primary small" @click="previewQuestion(task)">▶ 预览</button>
                </span>
              </div>
            </div>
          </div>

          <!-- 学习视频 -->
          <div v-if="videoTasks.length" class="task-group">
            <div class="task-group-title">📺 学习视频</div>
            <div v-for="(task, idx) in videoTasks" :key="'v-' + idx" class="task-item video-item">
              <div class="task-icon">📺</div>
              <div class="task-content">
                <div class="task-topic">{{ task.topic }}</div>
                <div class="task-desc">{{ task.description }}</div>
              </div>
              <span class="video-badge">⏳ 待上线</span>
            </div>
          </div>

          <div class="tasks-summary">
            <span>📊 共 {{ tasks.length }} 个任务</span>
            <span>📝 {{ questionTasks.length }} 道题</span>
            <span>📖 {{ contentTasks.length }} 个学习内容</span>
            <span>📺 {{ videoTasks.length }} 个视频</span>
          </div>
        </div>

        <div class="tasks-actions" v-if="tasks.length">
          <button class="glass-btn" @click="generateTasks" :disabled="agentLoading">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M23 4v6h-6M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
            </svg>
            重新生成
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'  // 👈 加上 watch
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { createPlan } from '@/api/learningPlan'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const confirming = ref(false)
const agentLoading = ref(false)
const agentProgress = ref('初始化...')

const planInfo = ref({
  name: '',
  stage: '大学',
  grade: '大一',
  major: '',
  difficulty: 13,
  dailyMinutes: 30,
  startDate: '',
  endDate: '',
  keywords: ''
})

const tasks = ref([])

const stageGradeMap = {
  '小学': ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级'],
  '初中': ['初一', '初二', '初三'],
  '高中': ['高一', '高二', '高三'],
  '大学': ['大一', '大二', '大三', '大四'],
  '研究生': ['研一', '研二', '研三'],
  '职场': ['初级', '中级', '高级']
}

const gradeOptions = computed(() => {
  return stageGradeMap[planInfo.value.stage] || ['大一', '大二', '大三', '大四']
})

const contentTasks = computed(() => tasks.value.filter(t => t.type === '学习内容'))
const questionTasks = computed(() => tasks.value.filter(t => t.type === '做题'))
const videoTasks = computed(() => tasks.value.filter(t => t.type === '学习视频'))

function onStageChange() {
  gradeOptions.value = stageGradeMap[planInfo.value.stage] || ['大一', '大二', '大三', '大四']
  planInfo.value.grade = gradeOptions.value[0] || ''
}

function loadFromRoute() {
  const query = route.query
  if (query.name) planInfo.value.name = query.name
  if (query.stage) planInfo.value.stage = query.stage
  if (query.grade) planInfo.value.grade = query.grade
  if (query.major) planInfo.value.major = query.major
  if (query.difficulty) planInfo.value.difficulty = parseInt(query.difficulty) || 13
  if (query.keywords) planInfo.value.keywords = query.keywords
  if (query.weaknesses && !query.keywords) {
    planInfo.value.keywords = query.weaknesses.split('、')[0] || ''
    if (!query.name) planInfo.value.name = `攻克 ${planInfo.value.keywords || '薄弱点'}`
  }
  if (!planInfo.value.name) planInfo.value.name = '学习规划'

  // 开始日期
  if (!planInfo.value.startDate) {
    planInfo.value.startDate = new Date().toISOString().slice(0, 10)
  }

  // 结束日期：绝不覆盖用户选择！只有用户完全没选时才给默认值
  if (!planInfo.value.endDate) {
    const d = new Date(planInfo.value.startDate || new Date())
    d.setDate(d.getDate() + 7)
    planInfo.value.endDate = d.toISOString().slice(0, 10)
  }
}

function loadFromProfile() {
  const user = authStore.user
  if (user) {
    if (user.learning_stage) planInfo.value.stage = user.learning_stage
    if (user.grade) planInfo.value.grade = user.grade
    if (user.major) planInfo.value.major = user.major
    onStageChange()
  }
}

// 👇 新增：监听用户手动修改结束日期
watch(
  () => planInfo.value.endDate,
  (newVal) => {
    if (newVal) {
      console.log('📅 用户选择结束日期:', newVal)
    }
  }
)

async function generateTasks() {
  if (!planInfo.value.keywords.trim()) {
    ElMessage.warning('请输入知识点')
    return
  }

  agentLoading.value = true
  agentProgress.value = '正在调用 AI 分析知识点...'

  try {
    // 使用当前最新的 startDate 和 endDate
    const start = new Date(planInfo.value.startDate)
    const end = new Date(planInfo.value.endDate)
    const totalDays = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1)

    const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/learning-plan/generate-tasks`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({
        keywords: planInfo.value.keywords,
        difficulty: planInfo.value.difficulty,
        daily_minutes: planInfo.value.dailyMinutes,
        total_days: totalDays
      })
    })

    const result = await response.json()

    if (!result.success) {
      ElMessage.error(result.message || 'AI 生成失败')
      agentLoading.value = false
      return
    }

    const aiData = result.data
    const taskList = []

    aiData.tasks.forEach((item) => {
      // 1. 学习内容
      taskList.push({
        type: '学习内容',
        topic: item.topic,
        description: item.content || `${item.topic} 核心概念讲解`
      })

      // 2. 做题
      if (item.questions && item.questions.length > 0) {
        item.questions.forEach((q) => {
          let dbQuestionType = 'choice'
          if (q.type === '选择题' || q.type === 'choice') dbQuestionType = 'choice'
          else if (q.type === '填空题' || q.type === 'fill') dbQuestionType = 'fill'
          else if (q.type === '判断题' || q.type === 'judge') dbQuestionType = 'judge'

          taskList.push({
            type: '做题',
            topic: item.topic,
            question_type: dbQuestionType,
            question_content: q.question || '',
            options: q.options || [],
            answer: q.answer || '',
            difficulty_score: q.difficulty_score || 5
          })
        })
      }

      // 3. 学习视频
      taskList.push({
        type: '学习视频',
        topic: item.topic,
        description: `${item.topic} 视频讲解（待上线）`
      })
    })

    tasks.value = taskList
    const questionCount = taskList.filter(t => t.type === '做题').length
    ElMessage.success(`AI 已生成 ${aiData.tasks.length} 个子知识点，共 ${questionCount} 道题目`)

  } catch (error) {
    console.error('生成失败:', error)
    ElMessage.error('AI 生成失败，请重试')
  } finally {
    agentLoading.value = false
  }
}

function previewQuestion(task) {
  const content = task.question_content || '暂无题目内容'
  const options = task.options && task.options.length > 0 ? `\n选项：${JSON.stringify(task.options)}` : ''
  const answer = task.answer ? `\n答案：${task.answer}` : ''
  ElMessage.info(`📝 ${content}${options}${answer}`)
}

async function confirmPlan() {
  if (!planInfo.value.name.trim()) {
    ElMessage.warning('请输入规划名称')
    return
  }
  if (!tasks.value.length) {
    ElMessage.warning('请先生成任务')
    return
  }

  confirming.value = true
  try {
    const start = new Date(planInfo.value.startDate)
    const end = new Date(planInfo.value.endDate)
    const totalDays = Math.max(1, Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1)

    // ✅ 安全构造：逐字段指定，杜绝脏数据
    const safeTasks = tasks.value.map((t, index) => {
      const dayOffset = index % totalDays
      const currentDate = new Date(start)
      currentDate.setDate(currentDate.getDate() + dayOffset)

      return {
        type: t.type,
        topic: t.topic,
        description: t.description || '',
        question_type: t.question_type || '',
        question_content: t.question_content || '',
        options: t.options || [],
        answer: t.answer || '',
        difficulty_score: t.difficulty_score || 5,
        date: currentDate.toISOString().slice(0, 10)
      }
    })

    const result = await createPlan({
      user_id: authStore.user.id,
      name: planInfo.value.name,
      stage: planInfo.value.stage,
      grade: planInfo.value.grade,
      major: planInfo.value.major,
      difficulty: planInfo.value.difficulty,
      daily_minutes: planInfo.value.dailyMinutes,
      start_date: planInfo.value.startDate,
      end_date: planInfo.value.endDate,
      keywords: planInfo.value.keywords,
      tasks: safeTasks
    })

    if (result.success) {
      ElMessage.success('🎉 规划已生成！')
      router.push('/learning-plan')
    } else {
      ElMessage.error(result.message || '保存失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败，请重试')
  } finally {
    confirming.value = false
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

function goBack() {
  router.go(-1)
}

onMounted(() => {
  loadFromProfile()
  loadFromRoute()
})
</script>

<style scoped>
/* 样式保持不变 */
.plan-preview-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 30px 20px;
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
}
[data-theme="light"] .plan-preview-page {
  background-image: url('/assets/bg/resource_lib_bg.jpg');
}
[data-theme="dark"] .plan-preview-page {
  background-image: url('/assets/bg/resource_lib_bl.jpg');
}

.preview-container {
  max-width: 960px;
  width: 100%;
  padding: 28px 36px;
  border-radius: 20px;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.06);
  box-shadow: 0 8px 48px rgba(0,0,0,0.08);
}
[data-theme="dark"] .preview-container {
  background: rgba(0,0,0,0.30);
}

.preview-header {
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
.preview-badge {
  font-size: 12px;
  padding: 2px 12px;
  border-radius: 12px;
  background: rgba(64,158,255,0.10);
  color: #409EFF;
  font-weight: 500;
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

.preview-card {
  padding: 20px 24px;
  border-radius: 14px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  margin-bottom: 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 12px;
}
.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.info-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}
.info-label .hint {
  font-size: 10px;
  color: var(--text-muted);
  font-weight: 400;
}
.info-keywords {
  margin-top: 12px;
}
.info-keywords .info-label {
  display: block;
  margin-bottom: 4px;
}

.glass-input {
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  color: var(--text-primary);
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.3s ease;
  outline: none;
  font-family: inherit;
}
.glass-input::placeholder { color: var(--text-muted); opacity: 0.4; }
.glass-input:focus {
  border-color: rgba(64,158,255,0.15);
  background: rgba(255,255,255,0.04);
  box-shadow: 0 0 0 4px rgba(64,158,255,0.04);
}
select.glass-input { cursor: pointer; appearance: none; }
select.glass-input option { background: #1a1a2e; color: #fff; }

.agent-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-radius: 12px;
  background: rgba(64,158,255,0.04);
  border: 1px solid rgba(64,158,255,0.06);
  margin-bottom: 16px;
}
.agent-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(64,158,255,0.12);
  border-top-color: #409EFF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.agent-status span { font-size: 14px; color: var(--text-secondary); }
.agent-progress { font-size: 12px; color: var(--text-muted); margin-left: auto; }

.tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.tasks-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.task-count {
  font-size: 12px;
  color: var(--text-muted);
}

.task-group {
  margin-bottom: 16px;
}
.task-group-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}

.task-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  margin-bottom: 4px;
}
.task-icon { font-size: 20px; flex-shrink: 0; margin-top: 1px; }
.task-content { flex: 1; min-width: 0; }
.task-topic { font-weight: 600; color: var(--text-primary); font-size: 14px; }
.task-desc { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }
.video-badge {
  font-size: 11px;
  color: var(--text-muted);
  padding: 2px 10px;
  border-radius: 10px;
  background: rgba(128,128,128,0.06);
  flex-shrink: 0;
  margin-top: 4px;
}

.question-table {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.04);
}
.question-header {
  display: grid;
  grid-template-columns: 40px 1fr 100px 80px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  background: rgba(255,255,255,0.02);
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.question-row {
  display: grid;
  grid-template-columns: 40px 1fr 100px 80px;
  padding: 6px 12px;
  font-size: 13px;
  color: var(--text-secondary);
  align-items: center;
  border-bottom: 1px solid rgba(255,255,255,0.02);
}
.question-row:last-child { border-bottom: none; }
.question-row:hover { background: rgba(255,255,255,0.02); }

.tasks-summary {
  display: flex;
  gap: 16px;
  padding-top: 12px;
  margin-top: 12px;
  border-top: 1px solid rgba(255,255,255,0.04);
  font-size: 12px;
  color: var(--text-muted);
}
.tasks-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  justify-content: flex-end;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}
.empty-icon { font-size: 40px; margin-bottom: 8px; opacity: 0.3; }
.empty-text { font-size: 14px; margin-bottom: 12px; }

@media (max-width: 768px) {
  .preview-container { padding: 16px; }
  .info-grid { grid-template-columns: 1fr 1fr; }
  .preview-header { flex-direction: column; align-items: stretch; }
  .question-header, .question-row {
    grid-template-columns: 30px 1fr 70px 60px;
    font-size: 12px;
    padding: 4px 8px;
  }
}
</style>