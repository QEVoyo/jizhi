<template>
  <div class="sp-page" :class="{ 'pgm-mode': question?.question_type === 'programming' }">
    <div class="sp-bg"></div>
    <div class="sp-container" :class="{ 'full-width': question?.question_type === 'programming' }">
      <!-- 顶栏 -->
      <div class="sp-topbar">
        <button class="back-btn" @click="$router.back()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          <span>返回</span>
        </button>
        <div class="q-progress" v-if="question">
          <span>{{ qIndex + 1 }} / {{ questionIds.length }}</span>
        </div>
        <div class="q-timer" v-if="question && !feedback && !allDone">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          <span>{{ timerDisplay }}</span>
        </div>
      </div>

      <!-- 加载 -->
      <div v-if="loading" class="sp-loading">
        <div class="loading-pulse"></div>
        <span>准备题目中...</span>
      </div>

      <!-- 题目卡片 -->
      <div v-else-if="question" class="q-card glass-panel" :class="{ 'pgm-split': question.question_type === 'programming' }">

        <!-- 编程题 — 左右分栏布局 -->
        <template v-if="question.question_type === 'programming'">
          <div class="q-meta">
            <span class="q-badge" :class="'bdg-' + question.category">{{ categoryLabel(question.category) }}</span>
            <span class="q-type">{{ typeLabel(question.question_type) }}</span>
            <span class="q-diff">{{ '★'.repeat(question.difficulty || 1) }}</span>
          </div>
          <div class="split-container">
            <!-- 左侧：题目面板 -->
            <div class="split-left">
              <div class="lg-section" v-if="parsedProblem.stem">
                <h4>题目描述</h4>
                <p>{{ parsedProblem.stem }}</p>
              </div>
              <div class="lg-section" v-if="parsedProblem.input">
                <h4>输入格式</h4>
                <p>{{ parsedProblem.input }}</p>
              </div>
              <div class="lg-section" v-if="parsedProblem.output">
                <h4>输出格式</h4>
                <p>{{ parsedProblem.output }}</p>
              </div>
              <div class="lg-section" v-if="parsedProblem.testCases.length">
                <h4>样例</h4>
                <div v-for="(tc, i) in parsedProblem.testCases" :key="i" class="lg-sample">
                  <div class="lg-sample-row"><span class="lg-sample-label">输入 #{{ i+1 }}</span><pre class="lg-sample-text">{{ tc.input }}</pre></div>
                  <div class="lg-sample-row"><span class="lg-sample-label">输出 #{{ i+1 }}</span><pre class="lg-sample-text">{{ tc.output }}</pre></div>
                  <div v-if="tc.description" class="lg-sample-desc">{{ tc.description }}</div>
                </div>
              </div>
              <div class="lg-section" v-if="parsedProblem.constraints">
                <h4>限制</h4>
                <p class="lg-constraints">{{ parsedProblem.constraints }}</p>
              </div>
              <div class="lg-section lg-meta-row">
                <span class="lg-meta-item">通过率: --</span>
                <span class="lg-meta-item">提交: --</span>
              </div>
            </div>
            <!-- 右侧：代码编辑器 -->
            <div class="split-right">
              <div class="code-toolbar">
                <select v-model="codeLanguage" class="glass-select code-lang-select">
                  <option v-for="l in supportedLangs" :key="l" :value="l">{{ langLabel(l) }}</option>
                </select>
                <div class="code-actions">
                  <button class="btn-test small" :disabled="!fillAnswer || testing || submitting" @click="runCode">{{ testing ? '运行中...' : '▶ 运行' }}</button>
                  <button class="btn-primary small" :disabled="!canSubmit || submitting" @click="doSubmit">{{ submitting ? '判题中...' : '提交' }}</button>
                </div>
              </div>
              <textarea v-model="fillAnswer" class="code-editor" placeholder="输入代码..." spellcheck="false" @keydown="handleCodeKey"></textarea>
              <details class="custom-input-toggle">
                <summary>自定义输入</summary>
                <textarea v-model="customInput" class="custom-input-area" placeholder="输入测试数据..." rows="4"></textarea>
              </details>
              <div v-if="runOutput" class="run-output glass-panel">
                <div class="tr-header"><span class="tr-title">运行输出</span></div>
                <pre class="run-output-text">{{ runOutput }}</pre>
              </div>
              <div v-if="testResults && testResults.length" class="test-results glass-panel">
                <div class="tr-header"><span class="tr-title">测试结果</span><span class="tr-score" :class="judgePassed ? 'ac' : 'wa'">{{ passedPoints }} / {{ totalPoints }} 分</span></div>
                <div v-for="tr in testResults" :key="tr.index" class="tr-row" :class="'tr-' + tr.status.toLowerCase()">
                  <span class="tr-status" :class="tr.status">{{ tr.status }}</span>
                  <span class="tr-desc">{{ tr.description }}</span>
                  <span class="tr-pts">{{ tr.earned }}/{{ tr.points }}</span>
                  <button v-if="tr.stderr" class="tr-detail-btn" @click="tr.showDetail = !tr.showDetail">详情</button>
                  <div v-if="tr.showDetail && tr.stderr" class="tr-detail">{{ tr.stderr }}</div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- 非编程题 — 普通 stem -->
        <template v-else>
        <div class="q-meta">
          <span class="q-badge" :class="'bdg-' + question.category">{{ categoryLabel(question.category) }}</span>
          <span class="q-type">{{ typeLabel(question.question_type) }}</span>
          <span class="q-diff">{{ '★'.repeat(question.difficulty || 1) }}</span>
        </div>
        <div class="q-stem">{{ getStem(question) }}</div>
        </template>

        <!-- 非编程题 — 答题区域 -->
        <template v-if="question.question_type !== 'programming'">
        <!-- 选择题（单选） -->
        <div v-if="isSingleChoice(question.question_type)" class="q-options">
          <button
            v-for="(o, i) in getOptions(question)"
            :key="i"
            class="opt-btn"
            :class="{ selected: selectedIndex === i }"
            @click="selectedIndex = i"
          >
            <span class="opt-letter">{{ letters[i] }}</span>
            <span class="opt-text">{{ o.replace(/^[A-D][.\s、]+/, '') }}</span>
          </button>
        </div>

        <!-- 多选题 -->
        <div v-else-if="isMultiChoice(question.question_type)" class="q-options">
          <button
            v-for="(o, i) in getOptions(question)"
            :key="i"
            class="opt-btn"
            :class="{ selected: (multiSelected || []).includes(letters[i]) }"
            @click="toggleMulti(letters[i])"
          >
            <span class="opt-letter">{{ letters[i] }}</span>
            <span class="opt-text">{{ o.replace(/^[A-D][.\s、]+/, '') }}</span>
            <svg v-if="(multiSelected || []).includes(letters[i])" class="opt-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6L9 17l-5-5"/></svg>
          </button>
          <div class="multi-hint">可多选，点击已选项取消</div>
        </div>

        <!-- 填空题 -->
        <div v-else-if="question.question_type === 'fill'" class="q-fill">
          <div class="fill-stem" v-html="fillStemHtml"></div>
          <input
            ref="fillInput"
            v-model="fillAnswer"
            class="glass-input"
            placeholder="输入答案..."
            autofocus
            @keyup.enter="doSubmit"
          />
        </div>

        <!-- 完形填空 -->
        <div v-else-if="question.question_type === 'cloze'" class="q-cloze">
          <div class="cloze-text">{{ getStem(question) }}</div>
          <div class="cloze-options">
            <div v-for="(o, i) in getOptions(question)" :key="i" class="cloze-opt-row">
              <span class="co-num">{{ i + 1 }}</span>
              <select v-model="clozeAnswers[i]" class="glass-select">
                <option value="">-- 选择 --</option>
                <option v-for="o2 in getOptions(question)" :key="o2" :value="o2">{{ o2 }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- 翻译 / 作文 / 简答 / 案例分析 / 教学设计 -->
        <div v-else-if="isLongTextType(question.question_type)" class="q-longtext">
          <textarea
            v-model="fillAnswer"
            class="glass-input textarea"
            :rows="5"
            :placeholder="longTextPlaceholder(question.question_type)"
            @keyup.ctrl.enter="doSubmit"
          ></textarea>
          <div class="lt-hint">Ctrl+Enter 提交</div>
        </div>

        <!-- 计算题 -->
        <div v-else-if="question.question_type === 'calculation'" class="q-fill">
          <input
            ref="fillInput"
            v-model="fillAnswer"
            class="glass-input"
            placeholder="输入答案（数值或表达式）..."
            autofocus
            @keyup.enter="doSubmit"
          />
        </div>

        <!-- 提交 -->
        </template>
        <div v-if="question.question_type !== 'programming'" class="q-actions">
          <button class="btn-primary" :disabled="!canSubmit || submitting" @click="doSubmit">
            <span v-if="submitting" class="btn-spinner"></span>
            {{ submitting ? '批改中...' : '提交答案' }}
          </button>
        </div>
      </div>

      <!-- 批改结果 -->
      <div v-if="feedback && question?.question_type !== 'programming'" class="feedback glass-panel" :class="feedback.is_correct ? 'fb-ok' : 'fb-err'">
        <div class="fb-verdict">
          <span>{{ feedback.is_correct ? '回答正确' : '回答错误' }}</span>
          <span v-if="feedback.ai_feedback?.score" class="fb-score">{{ feedback.ai_feedback.score }} 分</span>
        </div>
        <div v-if="feedback.explanation" class="fb-expl">{{ feedback.explanation }}</div>
        <div v-if="feedback.ai_feedback?.feedback" class="fb-ai">{{ feedback.ai_feedback.feedback }}</div>
        <div v-if="feedback.correct_answer" class="fb-correct">正确答案：{{ feedback.correct_answer }}</div>
        <div class="fb-nav">
          <button v-if="qIndex < questionIds.length - 1" class="btn-primary" @click="nextQuestion">下一题</button>
          <button v-else class="btn-primary" @click="$router.back()">完成，返回</button>
        </div>
      </div>

      <!-- 全部完成 -->
      <div v-if="allDone" class="done-state glass-panel">
        <div class="done-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        </div>
        <h3>全部完成！</h3>
        <p>今天的练习已经完成</p>
        <button class="btn-primary" @click="$router.back()">返回计划</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { submitAnswer as apiSubmit } from '@/api/subjectPlan'
import request from '@/utils/request'
import { typeLabel, buildCategoryMap, isSingleChoice, isMultiChoice, isLongTextType, longTextPlaceholder } from '@/utils/questionLabels'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const planId = route.query.plan_id
const syllabusId = route.query.syllabus_id || ''
const questionIds = computed(() => (route.query.questions || '').split(',').filter(Boolean))

const loading = ref(true)
const submitting = ref(false)
const testing = ref(false)
const customInput = ref('')
const runOutput = ref('')
const questions = ref([])
const qIndex = ref(0)
const question = computed(() => questions.value[qIndex.value] || null)
const selectedIndex = ref(-1)
const multiSelected = ref([])
const fillAnswer = ref('')
const fillInput = ref(null)
const clozeAnswers = ref([])
const feedback = ref(null)
const allDone = ref(false)

// 倒计时（正向计时）
const timerSeconds = ref(0)
let timerInterval = null
const timerDisplay = computed(() => {
  const m = Math.floor(timerSeconds.value / 60)
  const s = timerSeconds.value % 60
  return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
})
function startTimer() {
  timerSeconds.value = 0
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = setInterval(() => { timerSeconds.value++ }, 1000)
}
function stopTimer() {
  if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
}
const letters = ['A', 'B', 'C', 'D']

// 编程题状态
const testResults = ref(null)
const passedPoints = ref(0)
const totalPoints = ref(0)
const judgePassed = ref(false)
const syllabusLangs = ref((route.query.langs || 'python').split(',').filter(Boolean))
const codeLanguage = ref(localStorage.getItem('jizhi_code_lang') || syllabusLangs.value[0] || 'python')
watch(codeLanguage, (val) => { localStorage.setItem('jizhi_code_lang', val) })
const availableLangs = ref(['python', 'c', 'cpp', 'java'])
const supportedLangs = computed(() => {
  // 取 syllabus 允许的语言 与 系统可用语言的交集
  return syllabusLangs.value.filter(l => availableLangs.value.includes(l))
})
// 解析编程题的洛谷风格结构化字段
// 解析 ---TEST_CASES--- 文本为数组
function parseTestCasesText(tcText) {
  if (!tcText) return []
  const cases = []
  // 按 输入/input 行分割
  const lines = tcText.split('\n')
  let cur = null
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue
    const inMatch = trimmed.match(/^(?:input|输入)[：:]\s*(.+)/i)
    const outMatch = trimmed.match(/^(?:output|输出)[：:]\s*(.+)/i)
    if (inMatch) {
      if (cur && cur.input && cur.output) cases.push(cur)
      cur = { input: inMatch[1].trim(), output: '', description: '' }
    } else if (outMatch && cur) {
      cur.output = outMatch[1].trim()
    }
  }
  if (cur && cur.input && cur.output) cases.push(cur)
  return cases
}

const parsedProblem = computed(() => {
  const q = question.value
  if (!q || q.question_type !== 'programming') return { stem: '', input: '', output: '', testCases: [], constraints: '' }
  const c = q.content || {}
  if (typeof c === 'string') {
    const parts = c.split('---TEST_CASES---')
    return { stem: (parts[0] || '').trim(), input: '', output: '', testCases: parseTestCasesText(parts[1] || ''), constraints: '' }
  }
  // 结构化字段
  let stem = c.stem || ''
  let tcText = ''
  const tcIdx = stem.indexOf('---TEST_CASES---')
  if (tcIdx >= 0) {
    tcText = stem.substring(tcIdx + 17).trim()
    stem = stem.substring(0, tcIdx).trim()
  }
  let testCases = (Array.isArray(c.test_cases) && c.test_cases.length) ? c.test_cases : parseTestCasesText(tcText)
  return {
    stem,
    input: c.input_description || '',
    output: c.output_description || '',
    testCases,
    constraints: c.constraints || '',
  }
})


const canSubmit = computed(() => {
  if (!question.value) return false
  const qt = question.value.question_type
  if (isSingleChoice(qt)) return selectedIndex.value >= 0
  if (isMultiChoice(qt)) return (multiSelected.value || []).length > 0
  if (qt === 'programming') return fillAnswer.value.trim().length > 0
  if (qt === 'fill' || qt === 'calculation' || isLongTextType(qt)) return fillAnswer.value.trim().length > 0
  if (qt === 'cloze') return clozeAnswers.value.length > 0 && clozeAnswers.value.some(a => a)
  return false
})

const fillStemHtml = computed(() => {
  // 先用 textContent 安全地剥离 HTML 标签，再标记空位
  const s = getStem(question.value)
  const safe = s.replace(/<[^>]*>/g, '')
  return safe.replace(/_{2,}|\[blank\]|___/gi, '<span class="fc-blank">______</span>')
})

// 从 query 参数解析 dimensions（JSON 编码），构建动态分类标签映射
const dimLabelMap = computed(() => {
  try {
    const raw = route.query.dimensions || ''
    if (raw) {
      const dims = JSON.parse(decodeURIComponent(raw))
      return buildCategoryMap(dims)
    }
  } catch {}
  // 回退：从题目数据构建
  const map = {}
  questions.value.forEach(q => {
    const cat = q?.category
    if (cat && !map[cat]) map[cat] = cat
  })
  return buildCategoryMap(Object.entries(map).map(([cat]) => ({ category: cat, name: cat })))
})

function categoryLabel(c) {
  return dimLabelMap.value[c] || c
}

function getStem(q) {
  if (!q) return ''
  const c = q.content || {}
  if (typeof c === 'string') {
    // 编程题文本格式：去除测试用例部分，只显示题目描述
    const idx = c.indexOf('---TEST_CASES---')
    return idx >= 0 ? c.substring(0, idx).trim() : c
  }
  return c.stem || ''
}
function getOptions(q) { if (!q) return []; const c = q.content || {}; return typeof c === 'string' ? [] : (c.options || []) }

// 使用共享工具中的 isSingleChoice（不包含 cloze）、isMultiChoice、isLongTextType、longTextPlaceholder
// 在前端模板中，cloze 通过 `v-else-if="question.question_type === 'cloze'"` 单独处理

function langLabel(l) {
  return { python: 'Python 3', python3: 'Python 3', cpp: 'C++', 'c++': 'C++', java: 'Java', javascript: 'JavaScript', js: 'JavaScript', typescript: 'TypeScript', c: 'C', go: 'Go', rust: 'Rust' }[l] || l
}
function langPlaceholder(l) {
  if (l === 'python' || l === 'python3') return '# 输入你的 Python 代码...\n\ndef solve():\n    pass\n'
  if (l === 'cpp' || l === 'c++') return '// 输入你的 C++ 代码...\n#include <iostream>\nusing namespace std;\n\nint main() {\n    \n    return 0;\n}\n'
  if (l === 'java') return '// 输入你的 Java 代码...\nclass Solution {\n    public static void main(String[] args) {\n        \n    }\n}\n'
  if (l === 'javascript' || l === 'js') return '// 输入你的 JavaScript 代码...\n\nfunction solve() {\n    \n}\n'
  return '// 输入代码...\n'
}
function handleCodeKey(e) {
  if (e.key === 'Tab') {
    e.preventDefault()
    const ta = e.target
    const start = ta.selectionStart
    const end = ta.selectionEnd
    fillAnswer.value = fillAnswer.value.substring(0, start) + '    ' + fillAnswer.value.substring(end)
    nextTick(() => { ta.selectionStart = ta.selectionEnd = start + 4 })
  }
  if (e.key === 'Enter') {
    e.preventDefault()
    const ta = e.target
    const start = ta.selectionStart
    const before = fillAnswer.value.substring(0, start)
    const after = fillAnswer.value.substring(start)
    // 取当前行的缩进
    const lastLine = before.split('\n').pop() || ''
    const indent = lastLine.match(/^(\s*)/)[1]
    // 如果行尾是 : { ( [ 则增加一级缩进
    const extra = /[{([]\s*$/.test(lastLine.trimEnd()) ? '    ' : ''
    fillAnswer.value = before + '\n' + indent + extra + after
    const pos = start + 1 + indent.length + extra.length
    nextTick(() => { ta.selectionStart = ta.selectionEnd = pos })
  }
}
function toggleMulti(letter) {
  if (!multiSelected.value) multiSelected.value = []
  const arr = multiSelected.value
  const idx = arr.indexOf(letter)
  if (idx >= 0) arr.splice(idx, 1)
  else arr.push(letter)
}

async function loadQuestions() {
  if (!questionIds.value.length) { loading.value = false; return }
  try {
    const params = { ids: questionIds.value.join(','), user_id: authStore.user.id }
    if (syllabusId) params.syllabus_id = syllabusId
    const res = await request.get('/subject-plan/questions/by-ids', { params })
    questions.value = res.data?.questions || []
    if (!questions.value.length) { allDone.value = true }
    else { startTimer() }
  } catch (e) { console.error(e) } finally { loading.value = false; nextTick(() => fillInput.value?.focus()) }
}

async function runCode() {
  if (!question.value || !fillAnswer.value || testing.value) return
  testing.value = true; runOutput.value = ''
  try {
    const res = await request.post('/subject-plan/code/run', {
      question_id: question.value.id,
      syllabus_id: syllabusId || '',
      language: codeLanguage.value,
      code: fillAnswer.value,
      input: customInput.value,
    })
    runOutput.value = res.data?.output || res.data?.error || '(无输出)'
  } catch (e) { runOutput.value = '运行出错: ' + (e.response?.data?.detail || e.message) }
  finally { testing.value = false }
}

async function doSubmit() {
  if (!question.value || submitting.value) return
  submitting.value = true; stopTimer()
  feedback.value = null
  testResults.value = null

  const qt = question.value.question_type

  // 编程题 → 代码执行判题
  if (qt === 'programming') {
    try {
      const res = await request.post('/subject-plan/code/submit', {
        user_id: authStore.user?.id || '',
        plan_id: planId || '',
        syllabus_id: syllabusId || '',
        question_id: question.value.id,
        language: codeLanguage.value,
        code: fillAnswer.value,
        source: 'daily',
      })
      const d = res.data
      if (d.has_test_cases) {
        testResults.value = d.test_results || []
        passedPoints.value = d.passed_points || 0
        totalPoints.value = d.total_points || 0
        judgePassed.value = d.is_correct || false
      } else {
        // 无测试用例 → 显示 AI 批改
        feedback.value = d
      }
    } catch (e) { console.error(e) }
    finally { submitting.value = false }
    return
  }

  // 非编程题 → 原有逻辑
  let userAnswer
  if (isSingleChoice(qt)) { userAnswer = letters[selectedIndex.value] }
  else if (isMultiChoice(qt)) { userAnswer = [...(multiSelected.value || [])] }
  else if (isLongTextType(qt) || qt === 'fill' || qt === 'calculation') { userAnswer = fillAnswer.value.trim() }
  else if (qt === 'cloze') { userAnswer = clozeAnswers.value }

  try {
    const res = await apiSubmit(planId, {
      user_id: authStore.user.id,
      plan_id: planId,
      question_id: question.value.id,
      user_answer: userAnswer,
      source: 'daily',
    })
    feedback.value = res
  } catch (e) { console.error(e) } finally { submitting.value = false }
}

function nextQuestion() {
  feedback.value = null; stopTimer()
  testResults.value = null
  passedPoints.value = 0
  totalPoints.value = 0
  judgePassed.value = false
  selectedIndex.value = -1
  multiSelected.value = []
  fillAnswer.value = ''
  clozeAnswers.value = []
  if (qIndex.value < questionIds.value.length - 1) {
    qIndex.value++
    nextTick(() => fillInput.value?.focus())
  } else {
    allDone.value = true
  }
}

async function fetchLanguages() {
  try {
    const res = await request.get('/subject-plan/code/languages')
    const langs = res.data?.languages || {}
    availableLangs.value = Object.keys(langs).filter(k => langs[k].available)
    if (availableLangs.value.length === 0) availableLangs.value = ['python']
  } catch(e) { /* 默认 python */ }
}
onMounted(() => { loadQuestions(); fetchLanguages() })
onUnmounted(() => { if (timerInterval) clearInterval(timerInterval) })
</script>

<style scoped>
/* ==================== 基底：深空背景 ==================== */
.sp-page {
  min-height: 100vh; position: relative; padding: 32px 24px 80px;
  background: #080d18;
  color: #e2e8f0; overflow-x: hidden;
}
.sp-page.pgm-mode { height: 100vh; padding: 10px 20px 10px; overflow: hidden; display: flex; flex-direction: column; }
.sp-page.pgm-mode .sp-bg { display: none; }
.sp-page.pgm-mode .sp-container { flex: 1; min-height: 0; display: flex; flex-direction: column; max-width: none; }
.sp-page.pgm-mode .sp-topbar { flex-shrink: 0; margin-bottom: 6px; }
.sp-page::before {
  content: ''; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background:
    radial-gradient(ellipse 80% 60% at 20% 10%, rgba(108,140,255,.04) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 80%, rgba(139,92,246,.03) 0%, transparent 60%),
    radial-gradient(ellipse 40% 30% at 50% 50%, rgba(0,212,170,.02) 0%, transparent 60%);
  animation: bg-drift 20s ease-in-out infinite;
}
@keyframes bg-drift {
  0%, 100% { opacity: 1; }
  50% { opacity: .7; }
}

/* 粒子网格 */
.sp-page::after {
  content: ''; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image:
    linear-gradient(rgba(108,140,255,.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(108,140,255,.03) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse 60% 50% at 50% 50%, black 30%, transparent 70%);
}
.sp-container { width: 100%; max-width: 780px; margin: 0 auto; position: relative; z-index: 1; }
.sp-container.full-width { max-width: calc(100vw - 60px); }

/* ==================== 公用：超毛玻璃 ==================== */
.glass-panel {
  background: rgba(12,18,30,.6);
  border: 1px solid rgba(255,255,255,.06);
  backdrop-filter: blur(24px) saturate(1.2);
  -webkit-backdrop-filter: blur(24px) saturate(1.2);
  border-radius: 18px;
  transition: all .4s cubic-bezier(.4,0,.2,1);
  box-shadow: 0 4px 24px rgba(0,0,0,.2), inset 0 1px 0 rgba(255,255,255,.03);
}
.glass-panel:hover { border-color: rgba(255,255,255,.1); box-shadow: 0 8px 40px rgba(0,0,0,.3), inset 0 1px 0 rgba(255,255,255,.05); }

.btn-primary {
  display: inline-flex; align-items: center; gap: 8px; padding: 12px 28px;
  border-radius: 12px; border: none;
  background: linear-gradient(135deg, #6c8cff 0%, #8b5cf6 100%);
  color: #fff; font-size: 14px; font-weight: 600; cursor: pointer;
  transition: all .3s; font-family: inherit;
  box-shadow: 0 4px 20px rgba(108,140,255,.2);
  position: relative; overflow: hidden;
}
.btn-primary::after {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(135deg, transparent 40%, rgba(255,255,255,.1) 50%, transparent 60%);
  transform: translateX(-100%); transition: transform .6s;
}
.btn-primary:hover::after { transform: translateX(100%); }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 30px rgba(108,140,255,.35); }
.btn-primary:active { transform: translateY(0); }
.btn-primary:disabled { opacity: .35; cursor: not-allowed; transform: none; box-shadow: none; }
.btn-primary:disabled::after { display: none; }
.btn-primary.small { padding: 8px 18px; font-size: 12px; border-radius: 8px; }
.btn-spinner { width: 14px; height: 14px; border: 2px solid rgba(255,255,255,.2); border-top-color: #fff; border-radius: 50%; animation: spin .6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.glass-input {
  width: 100%; padding: 12px 16px; border-radius: 10px;
  border: 1px solid rgba(255,255,255,.06); background: rgba(8,13,24,.5);
  color: #e2e8f0; font-size: 14px; font-family: inherit; outline: none;
  backdrop-filter: blur(12px); transition: all .25s;
}
.glass-input:focus { border-color: rgba(108,140,255,.3); box-shadow: 0 0 0 3px rgba(108,140,255,.06); }
.glass-input.textarea { resize: vertical; min-height: 100px; }
.glass-select {
  padding: 8px 30px 8px 14px; border-radius: 8px; font-size: 13px;
  color: #94a3b8; background: rgba(8,13,24,.5); border: 1px solid rgba(255,255,255,.06);
  outline: none; cursor: pointer; font-family: inherit; backdrop-filter: blur(12px);
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 8px center; background-size: 14px;
  transition: all .25s;
}
.glass-select:focus { border-color: rgba(108,140,255,.3); }
.glass-select:hover { border-color: rgba(255,255,255,.1); }

/* ==================== 顶栏 ==================== */
.sp-topbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 28px; }
.back-btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px;
  border-radius: 10px; border: 1px solid rgba(255,255,255,.06);
  background: rgba(12,18,30,.5); color: #94a3b8; font-size: 13px;
  cursor: pointer; backdrop-filter: blur(16px); transition: all .3s;
}
.back-btn:hover { background: rgba(255,255,255,.06); color: #e2e8f0; border-color: rgba(255,255,255,.12); transform: translateX(-2px); }
.back-btn svg { width: 14px; height: 14px; }
.q-progress {
  font-size: 13px; color: #6c8cff; padding: 6px 14px; border-radius: 20px;
  background: rgba(108,140,255,.08); border: 1px solid rgba(108,140,255,.12);
  font-variant-numeric: tabular-nums;
}
.q-timer {
  display: flex; align-items: center; gap: 5px;
  font-size: 13px; color: #f59e0b; padding: 6px 12px; border-radius: 20px;
  background: rgba(245,158,11,.08); border: 1px solid rgba(245,158,11,.12);
  font-variant-numeric: tabular-nums;
}
.q-timer svg { width: 14px; height: 14px; }

/* ==================== 加载 ==================== */
.sp-loading { display: flex; flex-direction: column; align-items: center; gap: 20px; padding: 100px 0; }
.loading-pulse {
  width: 48px; height: 48px; border-radius: 50%;
  background: conic-gradient(from 0deg, transparent, #6c8cff, #8b5cf6, transparent);
  animation: pulse-rotate 1.5s linear infinite;
}
@keyframes pulse-rotate { to { transform: rotate(360deg); } }
.sp-loading span { font-size: 14px; color: #64748b; animation: text-fade 2s ease-in-out infinite; }
@keyframes text-fade { 0%, 100% { opacity: .5; } 50% { opacity: 1; } }

/* ==================== 题目卡片 ==================== */
.q-card {
  padding: 32px 30px; margin-bottom: 20px;
  animation: card-enter .5s ease-out;
  position: relative; overflow: hidden;
}
.q-card::before {
  content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(108,140,255,.3), rgba(139,92,246,.3), transparent);
  animation: border-sweep 3s ease-in-out infinite;
}
@keyframes card-enter { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
@keyframes border-sweep { 0%, 100% { opacity: .5; } 50% { opacity: 1; } }

.q-meta { display: flex; gap: 8px; align-items: center; margin-bottom: 20px; flex-wrap: wrap; }
.q-badge {
  font-size: 11px; padding: 4px 12px; border-radius: 8px; font-weight: 600;
  backdrop-filter: blur(8px); letter-spacing: .02em;
}
.bdg-vocabulary { background: rgba(64,158,255,.1); color: #409eff; border: 1px solid rgba(64,158,255,.15); }
.bdg-grammar { background: rgba(139,92,246,.1); color: #8b5cf6; border: 1px solid rgba(139,92,246,.15); }
.bdg-reading { background: rgba(34,197,94,.1); color: #22c55e; border: 1px solid rgba(34,197,94,.15); }
.bdg-translation { background: rgba(245,158,11,.1); color: #f59e0b; border: 1px solid rgba(245,158,11,.15); }
.bdg-writing { background: rgba(236,72,153,.1); color: #ec4899; border: 1px solid rgba(236,72,153,.15); }
.bdg-cloze { background: rgba(168,85,247,.1); color: #a855f7; border: 1px solid rgba(168,85,247,.15); }
.q-type { font-size: 11px; color: #64748b; }
.q-diff { font-size: 11px; color: #f59e0b; margin-left: auto; letter-spacing: 2px; }

.q-stem { font-size: 17px; line-height: 1.9; margin-bottom: 28px; color: #e8ecf2; letter-spacing: .01em; }

/* 选择题 */
.q-options { display: flex; flex-direction: column; gap: 8px; margin-bottom: 24px; }
.opt-btn {
  display: flex; align-items: center; gap: 14px; padding: 14px 18px;
  border-radius: 12px; border: 1px solid rgba(255,255,255,.05);
  background: rgba(12,18,30,.4); color: #cbd5e1; text-align: left;
  cursor: pointer; font-size: 14px; font-family: inherit;
  backdrop-filter: blur(12px); transition: all .25s cubic-bezier(.4,0,.2,1);
}
.opt-btn:hover { border-color: rgba(108,140,255,.25); background: rgba(108,140,255,.06); transform: translateX(4px); box-shadow: 0 4px 16px rgba(108,140,255,.08); }
.opt-btn.selected { border-color: #6c8cff; background: rgba(108,140,255,.12); box-shadow: 0 0 20px rgba(108,140,255,.12); }
.opt-letter {
  width: 28px; height: 28px; border-radius: 8px;
  background: rgba(255,255,255,.04); display: flex; align-items: center;
  justify-content: center; font-size: 13px; font-weight: 700; flex-shrink: 0;
  border: 1px solid rgba(255,255,255,.06); transition: all .25s;
}
.opt-btn.selected .opt-letter { background: linear-gradient(135deg, #6c8cff, #8b5cf6); border-color: transparent; color: #fff; }
.opt-btn.selected .opt-text { color: #fff; }

/* 填空 */
.q-fill { margin-bottom: 24px; }
.fill-stem { font-size: 16px; line-height: 2; margin-bottom: 18px; }
.fill-stem :deep(.fc-blank) {
  color: #6c8cff; font-weight: 600; padding: 2px 10px;
  border-bottom: 2px dashed rgba(108,140,255,.4);
  background: rgba(108,140,255,.04); border-radius: 4px 4px 0 0;
}

/* 完形填空 */
.q-cloze { margin-bottom: 24px; }
.cloze-text { font-size: 15px; line-height: 1.9; margin-bottom: 16px; padding: 18px; border-radius: 12px; background: rgba(8,13,24,.4); border: 1px solid rgba(255,255,255,.04); }
.cloze-options { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.cloze-opt-row { display: flex; align-items: center; gap: 10px; }
.co-num { font-size: 12px; color: #64748b; width: 22px; }

/* 多选 */
.multi-hint { font-size: 11px; color: #64748b; margin-top: 6px; }
.opt-check { width: 18px; height: 18px; margin-left: auto; color: #6c8cff; flex-shrink: 0; }

/* 长文本 */
.q-longtext { margin-bottom: 24px; }
.lt-hint { font-size: 11px; color: #475569; margin-top: 8px; text-align: right; }

/* 提交 */
.q-actions { display: flex; justify-content: flex-end; }

/* ==================== 反馈面板 ==================== */
.feedback { padding: 24px 28px; margin-top: 20px; animation: card-enter .4s ease-out; }
.feedback.fb-ok { border-color: rgba(34,197,94,.2); background: rgba(34,197,94,.04); }
.feedback.fb-err { border-color: rgba(239,68,68,.15); background: rgba(239,68,68,.03); }
.fb-verdict { display: flex; justify-content: space-between; align-items: center; font-size: 16px; font-weight: 700; margin-bottom: 14px; }
.fb-ok .fb-verdict { color: #22c55e; }
.fb-err .fb-verdict { color: #ef4444; }
.fb-score { font-size: 22px; color: #6c8cff; font-weight: 800; }
.fb-expl { font-size: 14px; color: #94a3b8; line-height: 1.7; margin-bottom: 10px; }
.fb-ai { font-size: 13px; color: #8b5cf6; line-height: 1.7; margin-bottom: 10px; padding: 12px; border-radius: 10px; background: rgba(139,92,246,.06); border: 1px solid rgba(139,92,246,.1); }
.fb-correct { font-size: 13px; color: #22c55e; margin-bottom: 18px; font-weight: 500; }
.fb-nav { display: flex; justify-content: flex-end; }

/* ==================== 完成状态 ==================== */
.done-state { text-align: center; padding: 80px 40px; animation: card-enter .5s ease-out; }
.done-icon {
  width: 72px; height: 72px; margin: 0 auto 20px; border-radius: 50%;
  background: linear-gradient(135deg, rgba(34,197,94,.15), rgba(108,140,255,.1));
  display: flex; align-items: center; justify-content: center; color: #22c55e;
  animation: done-pop .6s ease-out;
}
@keyframes done-pop { 0% { transform: scale(0); } 50% { transform: scale(1.2); } 100% { transform: scale(1); } }
.done-icon svg { width: 32px; height: 32px; }
.done-state h3 { font-size: 20px; margin: 0 0 8px; }
.done-state p { font-size: 14px; color: #64748b; margin: 0 0 24px; }

/* ==================== 编程题：代码编辑器 ==================== */
.q-programming { margin-bottom: 24px; }
.code-toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.code-lang-select { min-width: 130px; }
.code-lang-hint { font-size: 11px; color: #475569; }
.code-editor {
  width: 100%; min-height: 220px; padding: 18px;
  border-radius: 12px; border: 1px solid rgba(0,212,170,.15);
  background: linear-gradient(180deg, #0a0f1a 0%, #0d1520 100%);
  color: #c9d1d9; font-size: 14px;
  font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace;
  line-height: 1.7; resize: vertical; outline: none;
  tab-size: 4; transition: all .3s;
  box-shadow: inset 0 2px 12px rgba(0,0,0,.3);
}
.code-editor:focus {
  border-color: rgba(0,212,170,.5);
  box-shadow: 0 0 0 3px rgba(0,212,170,.06), inset 0 2px 12px rgba(0,0,0,.3), 0 8px 30px rgba(0,212,170,.06);
}
/* ==================== 编程题分栏布局 ==================== */
.q-card.pgm-split { padding: 0; overflow: hidden; display: flex; flex-direction: column; flex: 1; min-height: 0; }
.pgm-split .q-meta { padding: 10px 16px; border-bottom: 1px solid rgba(255,255,255,.06); flex-shrink: 0; }
.split-container { display: flex; flex: 1; min-height: 0; }
.split-left { width: 34%; overflow-y: auto; padding: 14px 18px; border-right: 1px solid rgba(255,255,255,.06); background: rgba(0,0,0,.1); }
.split-right { flex: 1; display: flex; flex-direction: column; padding: 10px 12px; min-width: 0; }
.split-left h4 { font-size: 13px; font-weight: 600; color: #94a3b8; margin: 0 0 4px; }
.split-left p { font-size: 14px; color: #cbd5e1; line-height: 1.65; margin: 0; }
.lg-section { margin-bottom: 12px; }
.lg-sample { background: rgba(0,0,0,.2); border-radius: 6px; padding: 8px 10px; margin-bottom: 6px; }
.lg-sample-text { font-size: 13px; color: #e2e8f0; font-family: 'Fira Code','Consolas',monospace; background: rgba(0,0,0,.25); padding: 5px 8px; border-radius: 4px; margin: 2px 0; white-space: pre-wrap; overflow-x: auto; }
.lg-sample-label { font-size: 11px; color: #64748b; font-weight: 600; }
.lg-sample-desc { font-size: 12px; color: #64748b; margin-top: 2px; }
.lg-constraints { font-family: 'Fira Code','Consolas',monospace; font-size: 13px; color: #fbbf24 !important; }
.lg-meta-row { display: flex; gap: 16px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,.05); margin-top: auto; }
.lg-meta-item { font-size: 12px; color: #64748b; }
/* 右侧：工具栏 */
.split-right .code-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; gap: 8px; flex-shrink: 0; }
.split-right .code-toolbar .code-lang-select { width: auto; min-width: 100px; font-size: 12px; padding: 4px 8px; }
.split-right .code-actions { display: flex; gap: 6px; }
.split-right .btn-test, .split-right .btn-primary { font-size: 12px; padding: 6px 12px; }
/* 代码编辑器占主体 */
.split-right .code-editor { flex: 1; min-height: 0; resize: none; font-size: 13px; line-height: 1.55; font-family: 'Fira Code','Consolas',monospace; background: rgba(0,0,0,.3); border: 1px solid rgba(255,255,255,.06); border-radius: 6px; color: #e2e8f0; padding: 12px 14px; }
/* 自定义输入折叠 */
.custom-input-toggle { margin-top: 6px; flex-shrink: 0; }
.custom-input-toggle summary { font-size: 11px; color: #64748b; cursor: pointer; padding: 4px 0; user-select: none; }
.custom-input-toggle .custom-input-area { width: 100%; margin-top: 4px; font-size: 13px; min-height: 80px; }

/* ==================== 通用按钮 ==================== */
.btn-test { padding: 6px 12px; border-radius: 6px; border: 1px solid rgba(148,163,184,.3); background: rgba(148,163,184,.08); color: #94a3b8; cursor: pointer; font-size: 12px; transition: all .2s; }
.btn-test:hover:not(:disabled) { background: rgba(148,163,184,.15); color: #e2e8f0; }
.custom-input-area { width: 100%; background: rgba(0,0,0,.25); border: 1px solid rgba(255,255,255,.08); border-radius: 4px; color: #e2e8f0; font-family: 'Fira Code','Consolas',monospace; font-size: 12px; padding: 6px 8px; resize: vertical; }
.custom-input-area::placeholder { color: #475569; }
.run-output { padding: 10px 12px; margin-top: 8px; flex-shrink: 0; }
.run-output-text { font-family: 'Fira Code','Consolas',monospace; font-size: 12px; color: #e2e8f0; white-space: pre-wrap; margin: 4px 0 0; }

/* ==================== 判题动画 ==================== */
.test-results { padding: 22px 24px; margin-top: 20px; animation: card-enter .5s ease-out; }
.tr-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,.05); }
.tr-title { font-size: 15px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.tr-title::before { content: ''; width: 8px; height: 8px; border-radius: 50%; background: #6c8cff; animation: dot-pulse 1.5s ease-in-out infinite; }
@keyframes dot-pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(108,140,255,.4); } 50% { box-shadow: 0 0 0 8px rgba(108,140,255,0); } }
.tr-score { font-size: 18px; font-weight: 700; font-variant-numeric: tabular-nums; }
.tr-score.ac { color: #22c55e; text-shadow: 0 0 16px rgba(34,197,94,.3); }
.tr-score.wa { color: #ef4444; text-shadow: 0 0 16px rgba(239,68,68,.3); }

.tr-row {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 8px;
  font-size: 13px; margin-bottom: 4px;
  background: rgba(255,255,255,.01); transition: all .3s;
  animation: row-reveal .4s ease-out both;
}
.tr-row:nth-child(1) { animation-delay: .1s; }
.tr-row:nth-child(2) { animation-delay: .2s; }
.tr-row:nth-child(3) { animation-delay: .3s; }
.tr-row:nth-child(4) { animation-delay: .4s; }
.tr-row:nth-child(5) { animation-delay: .5s; }
@keyframes row-reveal { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: translateX(0); } }

.tr-row.tr-ac { background: rgba(34,197,94,.05); border-left: 2px solid rgba(34,197,94,.3); }
.tr-row.tr-wa { background: rgba(239,68,68,.05); border-left: 2px solid rgba(239,68,68,.3); }
.tr-row.tr-tle { background: rgba(245,158,11,.05); border-left: 2px solid rgba(245,158,11,.3); }
.tr-row.tr-re { background: rgba(168,85,247,.05); border-left: 2px solid rgba(168,85,247,.3); }

.tr-status { font-size: 11px; font-weight: 800; padding: 3px 10px; border-radius: 5px; min-width: 40px; text-align: center; letter-spacing: .05em; }
.tr-status.AC { background: rgba(34,197,94,.15); color: #22c55e; }
.tr-status.WA { background: rgba(239,68,68,.15); color: #ef4444; }
.tr-status.TLE { background: rgba(245,158,11,.15); color: #f59e0b; }
.tr-status.RE { background: rgba(168,85,247,.15); color: #a855f7; }
.tr-desc { flex: 1; color: #94a3b8; }
.tr-pts { font-size: 12px; color: #94a3b8; font-variant-numeric: tabular-nums; font-weight: 500; }
.tr-detail-btn { font-size: 11px; padding: 3px 10px; border-radius: 5px; border: 1px solid rgba(255,255,255,.06); background: rgba(255,255,255,.02); color: #64748b; cursor: pointer; transition: all .2s; font-family: inherit; }
.tr-detail-btn:hover { color: #e2e8f0; background: rgba(255,255,255,.06); border-color: rgba(255,255,255,.12); }
.tr-detail { width: 100%; margin-top: 8px; padding: 12px; border-radius: 8px; background: rgba(0,0,0,.4); font-family: 'Consolas', monospace; font-size: 12px; color: #ef4444; white-space: pre-wrap; overflow-x: auto; border: 1px solid rgba(239,68,68,.1); }
</style>
