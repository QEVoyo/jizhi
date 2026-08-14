<template>
  <div class="onboard-page">
    <!-- ====== 星空粒子背景 ====== -->
    <div class="starfield">
      <div v-for="i in 80" :key="i" class="star" :style="starStyle(i)" />
      <div v-for="i in 12" :key="'c'+i" class="comet" :style="cometStyle(i)" />
    </div>

    <!-- ====== 主内容区 ====== -->
    <div class="onboard-main">
      <!-- Logo -->
      <div class="onboard-logo" @click="$router.push('/home')">
        <img src="/logo.png" alt="基智" class="logo-img" />
        <span class="logo-text">基智</span>
      </div>

      <!-- 步骤指示器 -->
      <div class="step-indicator" v-if="!saving">
        <div class="step-track">
          <div class="step-line" :style="{ width: ((step - 1) / 2 * 100) + '%' }" />
        </div>
        <div
          v-for="s in 2"
          :key="s"
          class="step-dot"
          :class="{ active: step >= s, current: step === s }"
        >
          <span class="dot-core" />
          <span class="dot-label">{{ s === 1 ? '基本信息' : '学习偏好' }}</span>
        </div>
      </div>

      <!-- ========== Step 1: 基本信息 ========== -->
      <Transition name="step-fade" mode="out-in">
        <div v-if="step === 1 && !saving" key="s1" class="step-content">
          <h2 class="step-title">{{ isEditMode ? '✏️ 编辑基本信息' : '🌌 了解你的学习宇宙' }}</h2>
          <p class="step-sub">{{ isEditMode ? '修改你的学习阶段和年级' : '选择你的学习阶段，基智将为你精准导航' }}</p>

          <!-- 学习阶段 -->
          <div class="field-group">
            <label class="field-label">
              学习阶段 <span class="required">*</span>
            </label>
            <div class="card-row">
              <div
                v-for="opt in stageOptions"
                :key="opt.value"
                class="option-card"
                :class="{ selected: form.learning_stage === opt.value }"
                @click="form.learning_stage = opt.value; onStageChange()"
              >
                <span class="option-icon">{{ opt.icon }}</span>
                <span class="option-text">{{ opt.label }}</span>
              </div>
            </div>
          </div>

          <!-- 年级 -->
          <div class="field-group">
            <label class="field-label">
              年级 <span class="required">*</span>
            </label>
            <div class="select-wrapper">
              <select
                v-model="form.grade"
                class="sci-select"
                :disabled="!form.learning_stage"
              >
                <option value="" disabled>选择年级</option>
                <option v-for="g in gradeOptions" :key="g" :value="g">{{ g }}</option>
              </select>
              <span class="select-arrow">▾</span>
            </div>
          </div>

          <!-- 专业/方向 -->
          <div class="field-group">
            <label class="field-label">专业 / 方向</label>
            <div class="sci-input-wrap">
              <input
                v-model="form.major"
                class="sci-input"
                placeholder="输入专业名称（可跳过）"
                @input="onMajorInput"
                @focus="showMajorSuggest = true"
                @blur="hideSuggestDelay"
              />
              <div v-if="showMajorSuggest && majorSuggestions.length" class="suggest-drop">
                <div
                  v-for="item in majorSuggestions"
                  :key="item"
                  class="suggest-item"
                  @mousedown.prevent="selectMajor(item)"
                >{{ item }}</div>
              </div>
            </div>
          </div>

          <!-- 底部操作 -->
          <div class="step-actions" v-if="!isEditMode">
            <button class="btn-skip" @click="goHome">跳过，以后设置</button>
            <button class="btn-next" :disabled="!form.learning_stage || !form.grade" @click="step = 2">下一步 →</button>
          </div>
          <div class="step-actions" v-else>
            <button class="btn-back" @click="goBack">取消</button>
            <button class="btn-next" :disabled="!form.learning_stage || !form.grade" @click="step = 2">下一步 →</button>
          </div>
        </div>

        <!-- ========== Step 2: 学习偏好 ========== -->
        <div v-else-if="step === 2 && !saving" key="s2" class="step-content">
          <h2 class="step-title">{{ isEditMode ? '✏️ 编辑学习偏好' : '🎯 定制学习体验' }}</h2>
          <p class="step-sub">{{ isEditMode ? '修改偏好设置，全部可选' : '可选，全部可以跳过，后续在个人中心修改' }}</p>

          <!-- 学习目标 -->
          <div class="field-group">
            <label class="field-label">学习目标</label>
            <div class="card-row">
              <div
                v-for="opt in goalOptions"
                :key="opt.value"
                class="option-card"
                :class="{ selected: form.learning_goal === opt.value }"
                @click="form.learning_goal = form.learning_goal === opt.value ? '' : opt.value"
              >
                <span class="option-icon">{{ opt.icon }}</span>
                <span class="option-text">{{ opt.label }}</span>
              </div>
            </div>
          </div>

          <!-- 难度偏好 -->
          <div class="field-group">
            <label class="field-label">题目难度偏好</label>
            <div class="card-row">
              <div
                v-for="opt in difficultyOptions"
                :key="opt.value"
                class="option-card"
                :class="{ selected: form.difficulty_preference === opt.value }"
                @click="form.difficulty_preference = form.difficulty_preference === opt.value ? '' : opt.value"
              >
                <span class="option-icon">{{ opt.icon }}</span>
                <span class="option-text">{{ opt.label }}</span>
              </div>
            </div>
          </div>

          <!-- 讲解风格 -->
          <div class="field-group">
            <label class="field-label">讲解方式偏好</label>
            <div class="card-row">
              <div
                v-for="opt in styleOptions"
                :key="opt.value"
                class="option-card"
                :class="{ selected: form.learning_style === opt.value }"
                @click="form.learning_style = form.learning_style === opt.value ? '' : opt.value"
              >
                <span class="option-icon">{{ opt.icon }}</span>
                <span class="option-text">{{ opt.label }}</span>
              </div>
            </div>
          </div>

          <!-- 每日学习时长 -->
          <div class="field-group">
            <label class="field-label">每日可用学习时间</label>
            <div class="card-row">
              <div
                v-for="opt in timeOptions"
                :key="opt.value"
                class="option-card"
                :class="{ selected: form.daily_study_time === opt.value }"
                @click="form.daily_study_time = form.daily_study_time === opt.value ? '' : opt.value"
              >
                <span class="option-icon">{{ opt.icon }}</span>
                <span class="option-text">{{ opt.label }}</span>
              </div>
            </div>
          </div>

          <!-- 底部操作 -->
          <div class="step-actions" v-if="!isEditMode">
            <button class="btn-back" @click="step = 1">← 上一步</button>
            <button class="btn-skip" @click="goHome">全部跳过</button>
            <button class="btn-next primary-glow" @click="handleSave">🚀 完成设置</button>
          </div>
          <div class="step-actions" v-else>
            <button class="btn-back" @click="step = 1">← 上一步</button>
            <button class="btn-skip" @click="goBack">取消</button>
            <button class="btn-next primary-glow" @click="handleSave">💾 保存修改</button>
          </div>
        </div>

        <!-- ========== 保存中：科幻进度条 ========== -->
        <div v-else key="loading" class="step-content loading-view">
          <div class="loading-icon">
            <div class="hex-ring">
              <div class="hex-core" />
            </div>
          </div>
          <h2 class="step-title">{{ isEditMode ? '正在保存偏好...' : loadingText }}</h2>
          <!-- 科幻进度条 -->
          <div class="sci-progress-wrap">
            <div class="sci-progress">
              <div class="sci-progress-fill" :style="{ width: progress + '%' }" />
              <div class="sci-progress-scan" />
            </div>
            <span class="progress-text">{{ progressText }}</span>
          </div>
          <p class="loading-hint">为你构建个性化学习画像...</p>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// ===== 编辑模式检测 =====
const isEditMode = ref(false)

onMounted(() => {
  if (route.query.edit === 'true') {
    isEditMode.value = true
    const u = authStore.user || {}
    form.learning_stage = u.learning_stage || ''
    form.grade = u.grade || ''
    form.major = u.major || ''
    form.learning_goal = u.learning_goal || ''
    form.difficulty_preference = u.difficulty_preference || ''
    form.learning_style = u.learning_style || ''
    form.daily_study_time = u.daily_study_time || ''
    if (form.learning_stage) onStageChange()
  }
})

// ===== 步骤状态 =====
const step = ref(1)
const saving = ref(false)
const progress = ref(0)
const loadingText = ref('正在初始化学习引擎...')
const loadingSteps = [
  { p: 20, text: '分析学习阶段...', delay: 400 },
  { p: 45, text: '匹配知识图谱...', delay: 700 },
  { p: 70, text: '校准推荐模型...', delay: 500 },
  { p: 90, text: '生成学习画像...', delay: 600 },
  { p: 100, text: '准备就绪！', delay: 300 },
]

const progressText = computed(() => `${Math.round(progress.value)}%`)

// ===== 表单 =====
const form = reactive({
  learning_stage: '',
  grade: '',
  major: '',
  learning_goal: '',
  difficulty_preference: '',
  learning_style: '',
  daily_study_time: ''
})

// ===== 选项配置 =====
const stageOptions = [
  { value: '初中', label: '初中', icon: '🏫' },
  { value: '高中', label: '高中', icon: '📚' },
  { value: '大学', label: '大学', icon: '🎓' },
  { value: '考研', label: '考研', icon: '📖' },
  { value: '在职', label: '在职', icon: '💼' },
  { value: '其他', label: '其他', icon: '✨' },
]

const stageGradeMap = {
  '初中': ['初一', '初二', '初三'],
  '高中': ['高一', '高二', '高三'],
  '大学': ['大一', '大二', '大三', '大四', '大五'],
  '考研': ['一战', '二战', '大三备考', '大四备考'],
  '在职': ['初级', '中级', '高级'],
  '其他': ['初级', '中级', '高级'],
}

const gradeOptions = computed(() => stageGradeMap[form.learning_stage] || [])

function onStageChange() {
  form.grade = (gradeOptions.value[0]) || ''
}

const goalOptions = [
  { value: '考试备考', label: '考试备考', icon: '📝' },
  { value: '兴趣学习', label: '兴趣学习', icon: '💡' },
  { value: '补课提升', label: '补课提升', icon: '📈' },
  { value: '考研复习', label: '考研复习', icon: '🎯' },
  { value: '工作提升', label: '工作提升', icon: '🚀' },
  { value: '其他', label: '其他', icon: '🌟' },
]

const difficultyOptions = [
  { value: '基础巩固', label: '基础巩固', icon: '🟢' },
  { value: '适中练习', label: '适中练习', icon: '🟡' },
  { value: '挑战难题', label: '挑战难题', icon: '🔴' },
]

const styleOptions = [
  { value: '详细讲解', label: '详细讲解', icon: '📖' },
  { value: '精简要点', label: '精简要点', icon: '⚡' },
  { value: '举例说明', label: '举例说明', icon: '💬' },
]

const timeOptions = [
  { value: '30分钟内', label: '30分钟', icon: '⏱' },
  { value: '1小时左右', label: '1小时', icon: '🕐' },
  { value: '2小时左右', label: '2小时', icon: '🕑' },
  { value: '2小时以上', label: '2h+', icon: '🚀' },
]

// ===== 专业自动补全 =====
const majorDatabase = [
  '计算机科学与技术', '软件工程', '人工智能', '数据科学', '信息安全',
  '电子信息工程', '通信工程', '自动化', '电气工程', '机械工程',
  '土木工程', '建筑学', '数学', '物理学', '化学', '生物科学',
  '临床医学', '药学', '护理学', '中医学', '口腔医学',
  '金融学', '会计学', '工商管理', '市场营销', '经济学',
  '法学', '英语', '汉语言文学', '新闻传播', '历史学',
  '教育学', '心理学', '社会学', '哲学', '艺术设计',
  '环境科学', '材料科学', '能源工程', '航空航天', '海洋科学',
  '地理信息', '统计学', '物联网', '区块链', '云计算'
]

const showMajorSuggest = ref(false)
const majorInput = computed({
  get: () => form.major,
  set: (v) => { form.major = v }
})

const majorSuggestions = computed(() => {
  const input = form.major.trim().toLowerCase()
  if (!input || input.length < 1) return majorDatabase.slice(0, 8)
  return majorDatabase
    .filter(m => m.toLowerCase().includes(input) || input.includes(m.slice(0, 2)))
    .slice(0, 5)
})

function onMajorInput() {
  showMajorSuggest.value = true
}

function selectMajor(item) {
  form.major = item
  showMajorSuggest.value = false
}

function hideSuggestDelay() {
  setTimeout(() => { showMajorSuggest.value = false }, 200)
}

// ===== 保存 =====
async function handleSave() {
  saving.value = true
  step.value = 0

  // 进度条动画
  for (const ls of loadingSteps) {
    await sleep(ls.delay)
    progress.value = ls.p
    loadingText.value = ls.text
  }

  // 保存到后端
  await authStore.updatePreferences({
    learning_stage: form.learning_stage,
    grade: form.grade,
    major: form.major,
    learning_goal: form.learning_goal,
    difficulty_preference: form.difficulty_preference,
    learning_style: form.learning_style,
    daily_study_time: form.daily_study_time
  })

  await sleep(500)
  if (isEditMode.value) {
    router.push('/profile')
  } else {
    router.push('/home')
  }
}

function goHome() {
  if (form.learning_stage && form.grade) {
    authStore.updatePreferences({
      learning_stage: form.learning_stage,
      grade: form.grade,
      major: form.major
    })
  }
  router.push('/home')
}

function goBack() {
  // 编辑模式下取消，回到个人中心
  router.push('/profile')
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// ===== 星空样式 =====
function starStyle(i) {
  const size = Math.random() * 2.5 + 1
  const animDuration = Math.random() * 3 + 2
  const animDelay = Math.random() * 5
  return {
    width: size + 'px',
    height: size + 'px',
    left: (i * 1.27 * 17) % 100 + '%',
    top: (i * 7.3 * 13) % 100 + '%',
    opacity: Math.random() * 0.6 + 0.2,
    animationDuration: animDuration + 's',
    animationDelay: animDelay + 's'
  }
}

function cometStyle(i) {
  return {
    left: (i * 23 + 10) % 100 + '%',
    top: (i * 17 + 5) % 100 + '%',
    animationDuration: (Math.random() * 6 + 8) + 's',
    animationDelay: (Math.random() * 10 + i * 2) + 's'
  }
}
</script>

<style scoped>
/* ====== 页面容器 ====== */
.onboard-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-color);
  overflow: hidden;
  position: relative;
}

/* ====== 星空粒子背景 ====== */
.starfield {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
.star {
  position: absolute;
  background: var(--text-primary);
  border-radius: 50%;
  animation: twinkle ease-in-out infinite alternate;
}
@keyframes twinkle {
  0% { opacity: 0.2; transform: scale(1); }
  100% { opacity: 0.8; transform: scale(1.4); }
}
.comet {
  position: absolute;
  width: 80px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(74, 108, 247, 0.4), transparent);
  animation: cometFly linear infinite;
  opacity: 0;
}
@keyframes cometFly {
  0% { transform: translateX(-100px); opacity: 0; }
  20% { opacity: 1; }
  80% { opacity: 0; }
  100% { transform: translateX(calc(100vw + 100px)); opacity: 0; }
}

/* ====== 主内容区 ====== */
.onboard-main {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 620px;
  padding: 0 24px;
}

/* Logo */
.onboard-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 32px;
  cursor: pointer;
  user-select: none;
}
.logo-img {
  width: 36px;
  height: 36px;
  border-radius: 8px;
}
.logo-text {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 2px;
}

/* ====== 步骤指示器 ====== */
.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: 40px;
  position: relative;
}
.step-track {
  position: absolute;
  top: 22px;
  left: calc(50% - 90px);
  width: 180px;
  height: 2px;
  background: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
}
.step-line {
  height: 100%;
  background: linear-gradient(90deg, #4a6cf7, #6c8cff);
  border-radius: 2px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 8px rgba(74, 108, 247, 0.6);
}
.step-dot {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  position: relative;
  z-index: 1;
}
.step-dot:first-child { margin-right: 180px; }
.dot-core {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--border-color);
  transition: all 0.4s ease;
  display: block;
}
.step-dot.active .dot-core {
  background: #4a6cf7;
  box-shadow: 0 0 12px rgba(74, 108, 247, 0.6);
}
.step-dot.current .dot-core {
  box-shadow: 0 0 20px rgba(74, 108, 247, 0.9);
  animation: pulse-dot 1.5s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { box-shadow: 0 0 8px rgba(74, 108, 247, 0.5); }
  50% { box-shadow: 0 0 20px rgba(74, 108, 247, 0.9); }
}
.dot-label {
  font-size: 11px;
  color: var(--text-muted);
  white-space: nowrap;
  transition: color 0.3s;
}
.step-dot.active .dot-label { color: var(--text-secondary); }
.step-dot.current .dot-label { color: #4a6cf7; }

/* ====== 步骤内容 ====== */
.step-content {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 40px 36px;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: var(--shadow);
}
.step-fade-enter-active,
.step-fade-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.step-fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}
.step-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
.step-title {
  text-align: center;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 6px;
}
.step-sub {
  text-align: center;
  font-size: 13px;
  color: var(--text-muted);
  margin: 0 0 28px;
}

/* ====== 表单区 ====== */
.field-group {
  margin-bottom: 22px;
}
.field-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
}
.required { color: #f56c6c; }

/* ====== 卡片选项 ====== */
.card-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.option-card {
  flex: 1 1 auto;
  min-width: 80px;
  padding: 14px 16px;
  text-align: center;
  background: var(--input-bg);
  border: 2px solid var(--border-color);
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.option-card:hover {
  border-color: rgba(74, 108, 247, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}
.option-card.selected {
  border-color: #4a6cf7;
  background: rgba(74, 108, 247, 0.1);
  box-shadow: 0 0 20px rgba(74, 108, 247, 0.15), inset 0 0 20px rgba(74, 108, 247, 0.05);
}
[data-theme="dark"] .option-card.selected {
  background: rgba(74, 108, 247, 0.15);
  box-shadow: 0 0 24px rgba(74, 108, 247, 0.2), inset 0 0 20px rgba(74, 108, 247, 0.08);
}
.option-icon { font-size: 22px; }
.option-text {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: color 0.2s;
}
.option-card.selected .option-text { color: #4a6cf7; }

/* ====== 下拉框 ====== */
.select-wrapper {
  position: relative;
}
.sci-select {
  width: 100%;
  padding: 12px 16px;
  font-size: 14px;
  background: var(--input-bg);
  border: 2px solid var(--border-color);
  border-radius: 12px;
  color: var(--text-primary);
  appearance: none;
  cursor: pointer;
  transition: border-color 0.25s;
  font-family: inherit;
}
.sci-select:focus {
  outline: none;
  border-color: #4a6cf7;
  box-shadow: 0 0 12px rgba(74, 108, 247, 0.15);
}
.sci-select:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.select-arrow {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
  font-size: 12px;
}

/* ====== 输入框 ====== */
.sci-input-wrap { position: relative; }
.sci-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 14px;
  background: var(--input-bg);
  border: 2px solid var(--border-color);
  border-radius: 12px;
  color: var(--text-primary);
  font-family: inherit;
  transition: border-color 0.25s;
}
.sci-input:focus {
  outline: none;
  border-color: #4a6cf7;
  box-shadow: 0 0 12px rgba(74, 108, 247, 0.15);
}
.sci-input::placeholder { color: var(--text-muted); }
.suggest-drop {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  max-height: 160px;
  overflow-y: auto;
  z-index: 10;
  box-shadow: var(--shadow-hover);
  backdrop-filter: blur(16px);
}
.suggest-item {
  padding: 10px 14px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: background 0.15s;
}
.suggest-item:hover {
  background: rgba(74, 108, 247, 0.1);
  color: var(--text-primary);
}

/* ====== 底部按钮 ====== */
.step-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 32px;
  flex-wrap: wrap;
}
.btn-next,
.btn-back,
.btn-skip {
  padding: 12px 28px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  transition: all 0.25s ease;
  font-family: inherit;
}
.btn-next {
  background: linear-gradient(135deg, #4a6cf7, #6c8cff);
  color: #fff;
  box-shadow: 0 4px 16px rgba(74, 108, 247, 0.3);
}
.btn-next:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(74, 108, 247, 0.45);
}
.btn-next:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.btn-next.primary-glow {
  box-shadow: 0 4px 24px rgba(74, 108, 247, 0.5), 0 0 40px rgba(74, 108, 247, 0.2);
  animation: glow-pulse 2s ease-in-out infinite;
}
@keyframes glow-pulse {
  0%, 100% { box-shadow: 0 4px 24px rgba(74, 108, 247, 0.4), 0 0 40px rgba(74, 108, 247, 0.15); }
  50% { box-shadow: 0 4px 32px rgba(74, 108, 247, 0.6), 0 0 56px rgba(74, 108, 247, 0.3); }
}
.btn-back {
  background: var(--input-bg);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}
.btn-back:hover {
  border-color: rgba(74, 108, 247, 0.3);
  color: var(--text-primary);
}
.btn-skip {
  background: transparent;
  color: var(--text-muted);
}
.btn-skip:hover { color: var(--text-secondary); }

/* ====== 科幻进度条 ====== */
.loading-view {
  text-align: center;
  padding: 48px 36px;
}
.loading-icon {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}
.hex-ring {
  width: 64px;
  height: 64px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.hex-ring::before {
  content: '';
  position: absolute;
  inset: 0;
  border: 2px solid transparent;
  border-top-color: #4a6cf7;
  border-radius: 50%;
  animation: hex-spin 1.2s linear infinite;
}
.hex-ring::after {
  content: '';
  position: absolute;
  inset: 8px;
  border: 2px solid transparent;
  border-bottom-color: rgba(74, 108, 247, 0.5);
  border-radius: 50%;
  animation: hex-spin 1.8s linear infinite reverse;
}
@keyframes hex-spin {
  to { transform: rotate(360deg); }
}
.hex-core {
  width: 16px;
  height: 16px;
  background: #4a6cf7;
  border-radius: 50%;
  box-shadow: 0 0 20px rgba(74, 108, 247, 0.7);
  animation: core-pulse 1.5s ease-in-out infinite;
}
@keyframes core-pulse {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.3); opacity: 1; }
}
.sci-progress-wrap {
  max-width: 320px;
  margin: 24px auto;
}
.sci-progress {
  height: 4px;
  background: var(--border-color);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}
.sci-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4a6cf7, #6c8cff, #4a6cf7);
  background-size: 200% 100%;
  border-radius: 4px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  animation: progress-shimmer 1.5s linear infinite;
}
@keyframes progress-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: 0 0; }
}
.sci-progress-scan {
  position: absolute;
  top: 0;
  left: 0;
  width: 30px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
  animation: scan-bar 1.2s ease-in-out infinite;
}
@keyframes scan-bar {
  0% { left: -30px; }
  100% { left: 100%; }
}
.progress-text {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: #4a6cf7;
  margin-top: 12px;
  font-family: 'Courier New', monospace;
  text-shadow: 0 0 16px rgba(74, 108, 247, 0.4);
}
.loading-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 20px;
}

/* ====== 响应式 ====== */
@media (max-width: 500px) {
  .step-content { padding: 28px 20px; }
  .option-card { min-width: 60px; padding: 10px 12px; }
  .option-icon { font-size: 18px; }
  .option-text { font-size: 12px; }
  .step-dot:first-child { margin-right: 140px; }
  .step-track { width: 140px; left: calc(50% - 70px); }
}
</style>
