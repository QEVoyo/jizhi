<template>
  <div class="pp-page">
    <div class="pp-container">
      <!-- Header -->
      <div class="pp-header">
        <div class="header-left">
          <button class="g-btn" @click="goBack">
            <el-icon><ArrowLeft /></el-icon> 返回
          </button>
          <h1>规划预览</h1>
        </div>
        <button class="g-btn primary" @click="confirmPlan" :disabled="confirming || !tasks.length">
          {{ confirming ? '保存中...' : '确认生成' }}
        </button>
      </div>

      <!-- 规划信息表单 -->
      <div class="info-card">
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">规划名称</span>
            <input class="g-input" v-model="planInfo.name" placeholder="输入规划名称" />
          </div>
          <div class="info-item">
            <span class="info-label">学习阶段</span>
            <select class="g-input" v-model="planInfo.stage" @change="onStageChange">
              <option v-for="s in stages" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div class="info-item">
            <span class="info-label">年级</span>
            <select class="g-input" v-model="planInfo.grade">
              <option v-for="g in gradeOptions" :key="g" :value="g">{{ g }}</option>
            </select>
          </div>
          <div class="info-item">
            <span class="info-label">专业/方向</span>
            <input class="g-input" v-model="planInfo.major" placeholder="如：计算机科学" />
          </div>
          <div class="info-item">
            <span class="info-label">难度 (1-20)</span>
            <input class="g-input" type="number" v-model="planInfo.difficulty" min="1" max="20" />
          </div>
          <div class="info-item">
            <span class="info-label">每日学习</span>
            <select class="g-input" v-model="planInfo.dailyMinutes">
              <option :value="15">15 分钟</option><option :value="30">30 分钟</option>
              <option :value="45">45 分钟</option><option :value="60">60 分钟</option>
              <option :value="90">90 分钟</option>
            </select>
          </div>
          <div class="info-item">
            <span class="info-label">开始日期</span>
            <input class="g-input" type="date" v-model="planInfo.startDate" />
          </div>
          <div class="info-item">
            <span class="info-label">结束日期</span>
            <input class="g-input" type="date" v-model="planInfo.endDate" />
          </div>
        </div>
        <div class="info-keywords">
          <span class="info-label">知识点</span>
          <input class="g-input" v-model="planInfo.keywords" placeholder="如：哈希表、唐诗鉴赏、民法总则" />
        </div>
      </div>

      <!-- ====== 星座生成动画 ====== -->
      <div v-if="generating" class="constellation-stage">
        <div class="cosmos-bg">
          <div class="nebula"></div>
          <div class="nebula-2"></div>
          <div v-for="i in 60" :key="'bg'+i" class="bg-star" :style="bgStarStyle(i)" />
        </div>

        <!-- 中央知识核心 -->
        <div class="knowledge-core">
          <div class="core-ring ring-1"></div>
          <div class="core-ring ring-2"></div>
          <div class="core-ring ring-3"></div>
          <div class="core-dot"></div>
          <span class="core-label">{{ planInfo.keywords || '知识核心' }}</span>
        </div>

        <!-- 星座节点 -->
        <div
          v-for="(star, idx) in constellationNodes"
          :key="idx"
          class="constellation-star"
          :class="{ revealed: idx < revealedCount }"
          :style="star.style"
        >
          <svg class="star-connector" v-if="idx > 0 && idx <= revealedCount"
            :style="connectorStyle(star, idx)" />
          <div class="star-glow"></div>
          <div class="star-core"></div>
          <span class="star-label">{{ star.topic }}</span>
          <span class="star-day">Day {{ star.day }}</span>
        </div>

        <div class="gen-status">
          <span class="gen-text">{{ genStatusText }}</span>
          <span class="gen-count">{{ revealedCount }} / {{ constellationNodes.length }}</span>
        </div>
      </div>

      <!-- ====== 任务列表（生成完成） ====== -->
      <div v-else-if="tasks.length" class="tasks-card">
        <div class="tasks-header">
          <h3>学习计划</h3>
          <span class="tasks-meta">{{ tasks.length }} 个任务 · {{ dayCount }} 天 · {{ questionCount }} 道题</span>
        </div>

        <div v-for="(group, idx) in groupedTasks" :key="idx" class="day-group">
          <div class="day-bar">
            <span class="day-num">Day {{ group.day }}</span>
            <span class="day-topic">{{ group.topic }}</span>
            <span class="day-stats">
              <el-icon><Reading /></el-icon> {{ group.contents }} 内容
              <el-icon><EditPen /></el-icon> {{ group.questions }} 题
              <el-icon><VideoCamera /></el-icon> 视频
            </span>
          </div>
          <div class="day-detail">
            <div class="day-questions">
              <div v-for="(q, qi) in group.questionList" :key="qi" class="mini-q">
                <span class="q-type-tag">{{ q.question_type }}</span>
                <span class="q-text">{{ (q.question_content || '').slice(0, 60) }}{{ (q.question_content || '').length > 60 ? '...' : '' }}</span>
              </div>
            </div>
            <div class="day-video">
              <el-icon><VideoCamera /></el-icon>
              <span>搜索：{{ group.videoQuery }}</span>
            </div>
          </div>
        </div>

        <div class="tasks-actions">
          <button class="g-btn" @click="regenerateTasks">重新生成</button>
          <span v-if="source === 'fallback'" class="fallback-tag">AI 暂不可用，使用模板任务</span>
        </div>
      </div>

      <!-- 空态：还没生成 -->
      <div v-else class="empty-card">
        <div class="empty-icon">✦</div>
        <h3>AI 将为你定制学习计划</h3>
        <p>{{ planInfo.keywords ? '基于「' + planInfo.keywords + '」拆分为每日任务' : '请输入知识点后开始' }}</p>
        <button class="g-btn primary" @click="generateTasks" :disabled="!planInfo.keywords.trim()">
          生成学习计划
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { createPlan } from '@/api/learningPlan'
import { ArrowLeft, Reading, EditPen, VideoCamera } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const confirming = ref(false)
const generating = ref(false)
const revealedCount = ref(0)
const genStatusText = ref('正在分析知识点...')
const source = ref('')

const planInfo = ref({
  name: '', stage: '大学', grade: '大一', major: '',
  difficulty: 13, dailyMinutes: 30, startDate: '', endDate: '', keywords: ''
})
const tasks = ref([])
const constellationNodes = ref([])

const stages = ['小学', '初中', '高中', '大学', '研究生', '职场']
const stageGradeMap = {
  '小学': ['一年级','二年级','三年级','四年级','五年级','六年级'],
  '初中': ['初一','初二','初三'],
  '高中': ['高一','高二','高三'],
  '大学': ['大一','大二','大三','大四'],
  '研究生': ['研一','研二','研三'],
  '职场': ['初级','中级','高级']
}
const gradeOptions = computed(() => stageGradeMap[planInfo.value.stage] || ['大一','大二','大三','大四'])

const dayCount = computed(() => {
  const s = new Date(planInfo.value.startDate), e = new Date(planInfo.value.endDate)
  return Math.max(1, Math.ceil((e - s) / 86400000) + 1)
})
const questionCount = computed(() => tasks.value.filter(t => t.type === '做题').length)

const groupedTasks = computed(() => {
  const map = {}
  tasks.value.forEach(t => {
    const d = t.date || planInfo.value.startDate
    if (!map[d]) map[d] = { day: '', topic: '', contents: 0, questions: 0, videoQuery: '', questionList: [] }
    if (t.type === '学习内容') { map[d].contents++; map[d].topic = map[d].topic || t.topic }
    if (t.type === '做题') { map[d].questions++; map[d].questionList.push(t); map[d].topic = map[d].topic || t.topic }
    if (t.type === '学习视频') map[d].videoQuery = t.video_query || t.description || ''
    if (!map[d].day) {
      const start = new Date(planInfo.value.startDate)
      const cur = new Date(d)
      map[d].day = Math.max(1, Math.ceil((cur - start) / 86400000) + 1)
    }
  })
  return Object.values(map).sort((a, b) => a.day - b.day)
})

function onStageChange() {
  planInfo.value.grade = (stageGradeMap[planInfo.value.stage] || ['大一'])[0]
}

// ===== 星座动画 =====
async function generateTasks() {
  if (!planInfo.value.keywords.trim()) return
  generating.value = true
  source.value = ''
  revealedCount.value = 0
  constellationNodes.value = []

  // 先计算天数，生成占位节点
  const days = dayCount.value
  for (let i = 0; i < days; i++) {
    const angle = (i / days) * Math.PI * 2 - Math.PI / 2
    const radius = 140 + Math.random() * 40
    constellationNodes.value.push({
      topic: '加载中...', day: i + 1,
      style: {
        left: `calc(50% + ${Math.cos(angle) * radius}px)`,
        top: `calc(50% + ${Math.sin(angle) * radius}px)`,
        animationDelay: `${i * 0.2}s`
      }
    })
  }

  // 动画阶段
  const phases = [
    { text: '分析知识点结构...', count: 0, delay: 600 },
    { text: '拆分子知识点...', count: 0, delay: 800 },
    { text: '匹配学习内容...', count: 0, delay: 400 },
    { text: '生成练习题...', count: 0, delay: 300 },
    { text: '推荐学习视频...', count: 0, delay: 400 },
  ]

  for (const phase of phases) {
    genStatusText.value = phase.text
    await sleep(phase.delay)
  }

  // 调 AI
  genStatusText.value = 'AI 正在生成学习计划...'
  let result = null
  try {
    const totalDays = dayCount.value
    const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/learning-plan/generate-tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authStore.token}` },
      body: JSON.stringify({
        keywords: planInfo.value.keywords,
        difficulty: planInfo.value.difficulty,
        daily_minutes: planInfo.value.dailyMinutes,
        total_days: totalDays
      })
    })
    result = await response.json()
    // 兼容新旧两种返回格式：新格式 data 是数组，旧格式 data.tasks 是数组
    let aiDays = result.data || []
    if (!Array.isArray(aiDays) && aiDays.tasks) {
      aiDays = aiDays.tasks
    }
    source.value = result.source || ''

    // 更新节点标签
    constellationNodes.value = []
    const start = new Date(planInfo.value.startDate)
    for (let i = 0; i < Math.min(aiDays.length, days); i++) {
      const d = aiDays[i]
      const angle = (i / Math.max(aiDays.length, 1)) * Math.PI * 2 - Math.PI / 2
      const radius = 140 + (i % 3) * 20
      constellationNodes.value.push({
        topic: d.topic, day: d.day || i + 1,
        style: {
          left: `calc(50% + ${Math.cos(angle) * radius}px)`,
          top: `calc(50% + ${Math.sin(angle) * radius}px)`,
        }
      })
    }

  } catch (e) {
    console.error('AI 生成失败:', e)
    constellationNodes.value = []
  }

  // 逐个点亮节点
  genStatusText.value = '正在构建学习路径...'
  for (let i = 0; i < constellationNodes.value.length; i++) {
    revealedCount.value = i + 1
    await sleep(250)
  }

  // 构建任务列表
  genStatusText.value = '正在组装任务...'
  await sleep(400)
  const dayData = result?.data
  const rawData = Array.isArray(dayData) ? dayData : (dayData?.tasks || [])
  // 新格式 (含 .questions) → buildTaskList 处理；旧格式 (含 .type) → 直接使用
  if (rawData.length && rawData[0].questions) {
    buildTaskList(rawData, source.value)
  } else if (rawData.length && rawData[0].type) {
    tasks.value = rawData
  } else {
    buildTaskList(rawData, source.value)
  }

  genStatusText.value = '完成'
  await sleep(500)
  generating.value = false
}

function buildTaskList(aiDays, src) {
  const taskList = []
  const start = new Date(planInfo.value.startDate)
  aiDays.forEach((d, i) => {
    const currentDate = new Date(start)
    currentDate.setDate(currentDate.getDate() + i)
    const dateStr = currentDate.toISOString().slice(0, 10)

    taskList.push({
      type: '学习内容', topic: d.topic,
      description: d.content || `${d.topic} 核心讲解`, date: dateStr
    })
    if (d.questions) {
      d.questions.forEach(q => {
        let qt = 'choice'
        if (q.type === '填空题' || q.type === 'fill') qt = 'fill'
        else if (q.type === '判断题' || q.type === 'judge') qt = 'judge'
        taskList.push({
          type: '做题', topic: d.topic, question_type: qt,
          question_content: q.question || '',
          options: q.options || [], answer: q.answer || '',
          difficulty_score: q.difficulty_score || 5, date: dateStr
        })
      })
    }
    taskList.push({
      type: '学习视频', topic: d.topic,
      video_query: d.video_query || d.topic,
      description: `搜索：${d.video_query || d.topic}`, date: dateStr
    })
  })
  tasks.value = taskList
}

// ===== 确认保存 =====
async function confirmPlan() {
  if (!planInfo.value.name.trim() || !tasks.value.length) return
  confirming.value = true
  try {
    const safeTasks = tasks.value.map(t => ({
      type: t.type, topic: t.topic, description: t.description || '',
      question_type: t.question_type || '', question_content: t.question_content || '',
      options: t.options || [], answer: t.answer || '',
      difficulty_score: t.difficulty_score || 5,
      video_query: t.video_query || '', date: t.date || planInfo.value.startDate
    }))
    const result = await createPlan({
      user_id: authStore.user.id, name: planInfo.value.name,
      stage: planInfo.value.stage, grade: planInfo.value.grade, major: planInfo.value.major,
      difficulty: planInfo.value.difficulty, daily_minutes: planInfo.value.dailyMinutes,
      start_date: planInfo.value.startDate, end_date: planInfo.value.endDate,
      keywords: planInfo.value.keywords, tasks: safeTasks
    })
    if (result.success) {
      router.push(`/plan-detail/${result.plan_id}`)
    }
  } catch (e) { console.error('保存失败:', e) }
  finally { confirming.value = false }
}

async function regenerateTasks() { tasks.value = []; await generateTasks() }

// ===== 星座样式 =====
function bgStarStyle(i) {
  return {
    left: ((i * 13.7) % 100) + '%', top: ((i * 7.3) % 100) + '%',
    width: (Math.random() * 2 + 1) + 'px', height: (Math.random() * 2 + 1) + 'px',
    opacity: Math.random() * 0.5 + 0.2,
    animationDelay: (Math.random() * 3) + 's'
  }
}
function connectorStyle(star, idx) {
  return {} // handled by CSS
}

function loadFromRoute() {
  const q = route.query
  if (q.name) planInfo.value.name = q.name
  if (q.stage) planInfo.value.stage = q.stage
  if (q.grade) planInfo.value.grade = q.grade
  if (q.major) planInfo.value.major = q.major
  if (q.difficulty) planInfo.value.difficulty = parseInt(q.difficulty) || 13
  if (q.keywords) planInfo.value.keywords = q.keywords
  if (q.dailyMinutes) planInfo.value.dailyMinutes = parseInt(q.dailyMinutes) || 30
  if (q.startDate) planInfo.value.startDate = q.startDate
  if (q.endDate) planInfo.value.endDate = q.endDate
  if (q.weaknesses && !q.keywords) {
    planInfo.value.keywords = q.weaknesses.split('、')[0] || ''
    if (!q.name) planInfo.value.name = `攻克 ${planInfo.value.keywords || '薄弱点'}`
  }
  // 兜底默认值
  if (!planInfo.value.startDate) planInfo.value.startDate = new Date().toISOString().slice(0, 10)
  if (!planInfo.value.endDate) {
    const d = new Date(planInfo.value.startDate || new Date())
    d.setDate(d.getDate() + 7)
    planInfo.value.endDate = d.toISOString().slice(0, 10)
  }
}

function loadProfile() {
  const u = authStore.user
  if (u) {
    if (u.learning_stage) planInfo.value.stage = u.learning_stage
    if (u.grade) planInfo.value.grade = u.grade
    if (u.major) planInfo.value.major = u.major
    onStageChange()
  }
}

function goBack() { router.go(-1) }

function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }

onMounted(() => { loadProfile(); loadFromRoute() })
</script>

<style scoped>
.pp-page { min-height: 100vh; display: flex; justify-content: center; padding: 28px 20px; }

.pp-container {
  max-width: 880px; width: 100%; padding: 24px 30px;
  border-radius: 18px;
  background: rgba(255,255,255,0.04); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 8px 32px rgba(0,0,0,0.06);
}
[data-theme="dark"] .pp-container { background: rgba(0,0,0,0.30); }

.pp-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
.pp-header h1 { font-size: 22px; font-weight: 700; color: var(--text-primary); margin: 0; }

.g-btn {
  display: inline-flex; align-items: center; gap: 5px; padding: 8px 18px;
  font-size: 13px; font-weight: 500; color: var(--text-secondary);
  background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px; cursor: pointer; transition: all 0.25s ease; font-family: inherit;
}
.g-btn:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.12); transform: translateY(-1px); }
.g-btn:active { transform: scale(0.97); }
.g-btn.primary { color: #409eff; background: rgba(64,158,255,0.08); border-color: rgba(64,158,255,0.12); }
.g-btn.primary:hover { background: rgba(64,158,255,0.16); box-shadow: 0 0 20px rgba(64,158,255,0.15); }
.g-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none !important; }

/* 信息表单 */
.info-card {
  padding: 18px 22px; border-radius: 14px;
  background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04);
  margin-bottom: 20px;
}
.info-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-label { font-size: 12px; font-weight: 500; color: var(--text-secondary); }
.info-keywords { margin-top: 12px; }
.g-input {
  width: 100%; padding: 8px 12px; border-radius: 8px; font-size: 13px;
  color: var(--text-primary); background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06); outline: none; font-family: inherit;
  transition: all 0.25s ease;
}
.g-input:focus { border-color: rgba(64,158,255,0.2); box-shadow: 0 0 0 3px rgba(64,158,255,0.04); }
.g-input::placeholder { color: var(--text-muted); opacity: 0.4; }
select.g-input { cursor: pointer; appearance: none; }

/* ====== 星座舞台 ====== */
.constellation-stage {
  position: relative; height: 420px; border-radius: 16px; overflow: hidden;
  background: radial-gradient(ellipse at center, rgba(30,30,60,0.8) 0%, rgba(10,10,25,0.95) 100%);
  border: 1px solid rgba(255,255,255,0.06);
}
[data-theme="light"] .constellation-stage {
  background: radial-gradient(ellipse at center, rgba(200,210,240,0.4) 0%, rgba(240,242,255,0.9) 100%);
}

.cosmos-bg { position: absolute; inset: 0; pointer-events: none; }
.nebula {
  position: absolute; width: 200px; height: 200px; border-radius: 50%;
  top: 20%; left: 30%;
  background: radial-gradient(circle, rgba(74,108,247,0.12), transparent 70%);
  animation: nebula-drift 8s ease-in-out infinite;
}
.nebula-2 {
  position: absolute; width: 160px; height: 160px; border-radius: 50%;
  bottom: 25%; right: 25%;
  background: radial-gradient(circle, rgba(139,92,246,0.10), transparent 70%);
  animation: nebula-drift 10s ease-in-out infinite reverse;
}
@keyframes nebula-drift {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(20px, -15px) scale(1.1); }
  66% { transform: translate(-10px, 10px) scale(0.95); }
}
.bg-star {
  position: absolute; border-radius: 50%; background: #fff;
  animation: bg-twinkle 2s ease-in-out infinite alternate;
}
@keyframes bg-twinkle { 0% { opacity: 0.2; } 100% { opacity: 0.8; } }

/* 知识核心 */
.knowledge-core { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 2; }
.core-ring {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); border-radius: 50%;
  border: 1px solid rgba(74,108,247,0.2);
}
.ring-1 { width: 80px; height: 80px; animation: ring-pulse 3s ease-in-out infinite; }
.ring-2 { width: 110px; height: 110px; animation: ring-pulse 3s ease-in-out infinite 0.5s; }
.ring-3 { width: 140px; height: 140px; animation: ring-pulse 3s ease-in-out infinite 1s; }
@keyframes ring-pulse {
  0%, 100% { opacity: 0.3; transform: translate(-50%, -50%) scale(1); }
  50% { opacity: 0.6; transform: translate(-50%, -50%) scale(1.05); }
}
.core-dot {
  width: 16px; height: 16px; border-radius: 50%; background: #4a6cf7;
  box-shadow: 0 0 24px rgba(74,108,247,0.8), 0 0 48px rgba(74,108,247,0.4);
  position: relative; z-index: 1;
}
.core-label {
  position: absolute; top: calc(100% + 14px); left: 50%; transform: translateX(-50%);
  white-space: nowrap; font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.7);
  text-shadow: 0 0 10px rgba(74,108,247,0.4);
}
[data-theme="light"] .core-label { color: rgba(0,0,0,0.6); }

/* 星座节点 */
.constellation-star {
  position: absolute; z-index: 3; transform: translate(-50%, -50%);
  opacity: 0; transition: opacity 0.5s ease, transform 0.5s ease;
}
.constellation-star.revealed { opacity: 1; }
.star-glow {
  width: 36px; height: 36px; border-radius: 50%;
  background: radial-gradient(circle, rgba(74,108,247,0.3), transparent 70%);
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  animation: star-pulse 2s ease-in-out infinite;
}
@keyframes star-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.5; }
  50% { transform: translate(-50%, -50%) scale(1.4); opacity: 1; }
}
.star-core {
  width: 8px; height: 8px; border-radius: 50%; background: #fff;
  box-shadow: 0 0 10px rgba(255,255,255,0.6);
  position: relative; z-index: 1; margin: 0 auto;
}
.star-label {
  position: absolute; top: 22px; left: 50%; transform: translateX(-50%);
  white-space: nowrap; font-size: 10px; color: rgba(255,255,255,0.6);
  text-align: center; max-width: 90px; overflow: hidden; text-overflow: ellipsis;
}
[data-theme="light"] .star-label { color: rgba(0,0,0,0.5); }
.star-day {
  position: absolute; top: 6px; left: 50%; transform: translateX(-50%);
  font-size: 9px; color: rgba(74,108,247,0.6); font-weight: 600;
}

/* 生成状态 */
.gen-status {
  position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 16px; z-index: 4;
}
.gen-text { font-size: 14px; color: rgba(255,255,255,0.6); font-weight: 500; }
.gen-count { font-size: 20px; font-weight: 700; color: #4a6cf7; font-family: 'Courier New', monospace; text-shadow: 0 0 12px rgba(74,108,247,0.4); }
[data-theme="light"] .gen-text { color: rgba(0,0,0,0.5); }

/* 任务列表 */
.tasks-card { padding: 0; }
.tasks-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.tasks-header h3 { font-size: 16px; font-weight: 600; color: var(--text-primary); margin: 0; }
.tasks-meta { font-size: 12px; color: var(--text-muted); }
.day-group {
  margin-bottom: 10px; border-radius: 10px;
  background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.04);
  overflow: hidden;
}
.day-bar {
  display: flex; align-items: center; gap: 12px; padding: 10px 16px;
  background: rgba(255,255,255,0.02); cursor: default;
}
.day-num { font-size: 13px; font-weight: 700; color: #4a6cf7; min-width: 44px; }
.day-topic { font-size: 13px; font-weight: 600; color: var(--text-primary); flex: 1; }
.day-stats { display: flex; align-items: center; gap: 12px; font-size: 11px; color: var(--text-muted); }
.day-stats .el-icon { font-size: 13px; }
.day-detail { padding: 6px 16px 10px; border-top: 1px solid rgba(255,255,255,0.03); }
.mini-q { display: flex; align-items: center; gap: 8px; padding: 3px 0; font-size: 12px; }
.q-type-tag {
  font-size: 10px; padding: 1px 6px; border-radius: 4px; flex-shrink: 0;
  background: rgba(64,158,255,0.1); color: #409eff;
}
.q-text { color: var(--text-secondary); }
.day-video { display: flex; align-items: center; gap: 6px; padding-top: 6px; font-size: 11px; color: var(--text-muted); }
.day-video .el-icon { font-size: 13px; color: #f59e0b; }
.fallback-tag { font-size: 11px; color: #e6a23c; padding: 4px 10px; background: rgba(230,162,60,0.08); border-radius: 6px; }
.tasks-actions { display: flex; align-items: center; gap: 12px; margin-top: 14px; justify-content: flex-end; }

/* 空态 */
.empty-card { text-align: center; padding: 60px 20px; color: var(--text-muted); }
.empty-icon { font-size: 48px; margin-bottom: 12px; opacity: 0.3; }
.empty-card h3 { font-size: 18px; color: var(--text-primary); margin: 0 0 8px; }
.empty-card p { font-size: 13px; margin: 0 0 20px; }

@media (max-width: 768px) {
  .pp-container { padding: 16px; }
  .info-grid { grid-template-columns: 1fr 1fr; }
  .constellation-stage { height: 320px; }
  .star-label { font-size: 8px; max-width: 60px; }
  .day-stats { display: none; }
}
</style>
