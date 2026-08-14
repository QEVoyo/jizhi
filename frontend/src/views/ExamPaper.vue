<template>
  <div class="ep-page">
    <div class="ep-bg"></div>

    <!-- ===== 顶部栏 ===== -->
    <div class="ep-topbar glass-panel">
      <button class="ep-back" @click="handleBack">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
      </button>
      <div class="ep-title-area">
        <h1 class="ep-title">{{ paper?.name || '加载中...' }}</h1>
        <div class="ep-meta">
          <span class="ep-type-tag" :class="paper?.paper_type === 'simulation' ? 'sim' : 'real'">
            {{ paper?.paper_type === 'simulation' ? 'AI 仿真卷' : '真题' }}
          </span>
          <span v-if="paper?.available_note" class="ep-note">{{ paper.available_note }}</span>
        </div>
      </div>
      <div class="ep-top-actions">
        <span v-if="mode === 'practice'" class="ep-timer" :class="{ warning: timerSec > 60 && timerSec % 60 < 10 }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          {{ timerDisplay }}
        </span>
        <span v-if="mode === 'review' && history?.has_history" class="ep-history-badge">
          历史 {{ history.total_attempts }} 次 · 最高 {{ history.latest_score_pct }}%
        </span>
      </div>
    </div>

    <!-- ===== 加载 ===== -->
    <div v-if="loading" class="ep-loading">
      <div class="loading-pulse"></div>
      <span>加载套卷中...</span>
    </div>

    <!-- ===== 主体内容 ===== -->
    <div v-else class="ep-main">
      <!-- 左侧：卷面分区导航 -->
      <aside class="ep-nav glass-panel">
        <div v-for="sec in visibleSections" :key="sec.order" class="ep-nav-section"
          :class="{ active: activeSection === sec.order, done: isSectionDone(sec) }"
          @click="scrollToSection(sec.order)">
          <span class="ep-nav-num">{{ sec.order }}</span>
          <div class="ep-nav-info">
            <span class="ep-nav-name">{{ sec.name }}</span>
            <span class="ep-nav-score">{{ sec.section_score }}分 ({{ sec.duration_minutes }}min)</span>
          </div>
          <span v-if="isSectionDone(sec)" class="ep-nav-check">✓</span>
        </div>
      </aside>

      <!-- 右侧：题目区域 -->
      <div class="ep-content" ref="contentRef">
        <div v-for="sec in visibleSections" :key="sec.order" :ref="el => sectionRefs[sec.order] = el" class="ep-section">

          <!-- Section 标题 -->
          <div class="ep-section-head glass-panel">
            <div class="ep-section-badge">{{ sec.order }}</div>
            <div>
              <h3>{{ sec.name }}</h3>
              <p>{{ sec.instruction }}</p>
              <p class="ep-section-meta">{{ sec.section_score }}分 · {{ sec.duration_minutes }}分钟</p>
            </div>
          </div>

          <!-- ===== 选词填空 (banked_cloze) ===== -->
          <div v-if="sec.question_type === 'banked_cloze'" class="ep-banked-cloze glass-panel">
            <div class="bc-word-bank">
              <span v-for="w in sec.word_bank" :key="w.letter" class="bc-word" :class="{ used: usedWordBank[sec.order]?.has(w.letter) }">
                <b>{{ w.letter }}.</b> {{ w.word }}
              </span>
            </div>
            <div class="bc-passage" v-html="renderBankedPassage(sec)"></div>
            <!-- 解析模式：答案表 -->
            <div v-if="mode === 'review'" class="bc-answers glass-panel">
              <div v-for="q in sec.questions" :key="q.blank_index" class="bc-answer-row">
                <span class="bc-ans-num">{{ q.blank_index }}</span>
                <span class="bc-ans-letter" :class="{ correct: getBankedHistory(sec.order, q.blank_index)?.isCorrect, wrong: getBankedHistory(sec.order, q.blank_index) && !getBankedHistory(sec.order, q.blank_index)?.isCorrect }">
                  {{ q.answer }}
                </span>
                <span class="bc-ans-word">{{ getWordByLetter(sec.word_bank, q.answer) }}</span>
                <div class="bc-ans-exp">{{ q.explanation }}</div>
                <div v-if="getBankedHistory(sec.order, q.blank_index)" class="bc-user-info">
                  你选：<b>{{ getBankedHistory(sec.order, q.blank_index).lastAnswer }}</b>
                  · 正确率 {{ getBankedHistory(sec.order, q.blank_index).accuracy }}%
                </div>
              </div>
            </div>
          </div>

          <!-- ===== 题目列表 (常规题型) ===== -->
          <template v-for="q in sec.questions" :key="'q' + (q.index || q.question_number)">
            <div class="ep-question glass-panel" :class="{
              correct: mode === 'review' && getQuestionResult(sec.order, q)?.isCorrect === true,
              wrong: mode === 'review' && getQuestionResult(sec.order, q)?.isCorrect === false
            }">
              <!-- 题号 + 分值 -->
              <div class="ep-q-head">
                <span class="ep-q-num">{{ sec.name }} · 第{{ q.index || q.question_number }}题</span>
                <span class="ep-q-score">{{ q.score }}分</span>
              </div>

              <!-- 题干 -->
              <div v-if="q.stem" class="ep-q-stem">{{ q.stem }}</div>
              <div v-if="q.content?.stem" class="ep-q-stem">{{ q.content.stem }}</div>

              <!-- 文章引用 -->
              <div v-if="q.passage" class="ep-q-passage">{{ q.passage }}</div>

              <!-- 选择题选项 -->
              <div v-if="q.question_type === 'choice' && q.options" class="ep-choices">
                <label v-for="opt in q.options" :key="opt.key" class="ep-choice" :class="{
                  selected: answers[answerKey(sec.order, q)] === opt.key,
                  'is-correct': mode === 'review' && opt.key === q.answer,
                  'is-wrong': mode === 'review' && answers[answerKey(sec.order, q)] === opt.key && opt.key !== q.answer
                }">
                  <input v-if="mode === 'practice'" type="radio" :name="'q-' + sec.order + '-' + (q.index || q.question_number)"
                    :value="opt.key" v-model="answers[answerKey(sec.order, q)]" />
                  <span class="ep-choice-key">{{ opt.key }}</span>
                  <span class="ep-choice-text">{{ opt.text }}</span>
                </label>
              </div>

              <!-- 主观题输入 -->
              <div v-if="isSubjective(q)" class="ep-subjective">
                <textarea v-if="mode === 'practice'"
                  v-model="answers[answerKey(sec.order, q)]"
                  :placeholder="q.question_type === 'translation' ? '请输入你的翻译...' : '请输入你的作文...'"
                  :maxlength="q.question_type === 'translation' ? 3000 : 5000"
                  rows="8"
                  class="ep-textarea glass-input"></textarea>
                <div v-else class="ep-submitted-answer">{{ answers[answerKey(sec.order, q)] || '（未作答）' }}</div>
              </div>

              <!-- 解析模式：答案与解析 -->
              <div v-if="mode === 'review'" class="ep-review-block">
                <!-- ===== 情况1：用户做过这道题 ===== -->
                <template v-if="getQuestionStat(sec.order, q)">
                  <div class="ep-done-badge">✅ 你已做过 · {{ getQuestionStat(sec.order, q).attempts }}次 · 正确率 {{ getQuestionStat(sec.order, q).accuracy }}%</div>

                  <!-- 上次你的答案 -->
                  <div class="ep-your-answer" :class="{ correct: isLastAnswerCorrect(sec.order, q), wrong: !isLastAnswerCorrect(sec.order, q) }">
                    <span class="ep-label">你的答案</span>
                    <span v-if="q.question_type === 'choice'">{{ getQuestionStat(sec.order, q).lastAnswer }}{{ q.options ? '. ' + getOptionText(q.options, getQuestionStat(sec.order, q).lastAnswer) : '' }}</span>
                    <span v-else class="ep-submitted-answer">{{ getQuestionStat(sec.order, q).lastAnswer }}</span>
                  </div>

                  <!-- 正确答案 -->
                  <div v-if="q.answer" class="ep-answer-line">
                    <span class="ep-label">正确答案</span>
                    <span class="ep-answer-val">{{ q.answer }}{{ q.options ? ' (' + getOptionText(q.options, q.answer) + ')' : '' }}</span>
                  </div>

                  <!-- 解析 -->
                  <div v-if="q.explanation" class="ep-explanation">
                    <span class="ep-label">解析</span>
                    <p>{{ q.explanation }}</p>
                  </div>

                  <!-- AI 批改反馈（主观题） -->
                  <div v-if="getQuestionStat(sec.order, q).ai_feedback" class="ep-ai-feedback">
                    <div class="ep-ai-score">AI 评分：{{ getQuestionStat(sec.order, q).ai_feedback.score }} / {{ getQuestionStat(sec.order, q).ai_feedback.max_score }}</div>
                    <p class="ep-ai-fb-text">{{ getQuestionStat(sec.order, q).ai_feedback.feedback }}</p>
                    <div v-if="getQuestionStat(sec.order, q).ai_feedback.highlights?.length" class="ep-ai-detail">
                      <span class="ep-ai-tag good">亮点</span>
                      <ul><li v-for="h in getQuestionStat(sec.order, q).ai_feedback.highlights" :key="h">{{ h }}</li></ul>
                    </div>
                    <div v-if="getQuestionStat(sec.order, q).ai_feedback.errors?.length" class="ep-ai-detail">
                      <span class="ep-ai-tag bad">问题</span>
                      <ul><li v-for="e in getQuestionStat(sec.order, q).ai_feedback.errors" :key="e.detail">{{ e.type }}：{{ e.detail }}</li></ul>
                    </div>
                    <div v-if="getQuestionStat(sec.order, q).ai_feedback.suggestion" class="ep-ai-suggestion">
                      💡 {{ getQuestionStat(sec.order, q).ai_feedback.suggestion }}
                    </div>
                  </div>

                  <!-- 错题 AI 实时分析（客观题做错时自动生成） -->
                  <div v-if="getLatestResult(sec.order, q)?.ai_mistake_analysis && !isLastAnswerCorrect(sec.order, q)" class="ep-ai-mistake">
                    <div class="ep-ai-mistake-title">🤖 AI 错因分析</div>
                    <p><span class="ep-ai-tag bad">原因</span> {{ getLatestResult(sec.order, q).ai_mistake_analysis }}</p>
                    <p><span class="ep-ai-tag good">正解</span> {{ getLatestResult(sec.order, q).ai_correction }}</p>
                    <div class="ep-ai-suggestion">💡 {{ getLatestResult(sec.order, q).ai_study_tip }}</div>
                  </div>

                  <!-- 客观题 AI 分析 -->
                  <div v-if="q.ai_analysis_hint && !getQuestionStat(sec.order, q).ai_feedback && !getLatestResult(sec.order, q)?.ai_mistake_analysis" class="ep-ai-hint">
                    <span class="ep-label">💡 AI 分析</span>
                    <p>{{ q.ai_analysis_hint }}</p>
                  </div>

                  <!-- 历史答案记录 -->
                  <details v-if="getQuestionStat(sec.order, q).all_answers?.length > 1" class="ep-history-detail">
                    <summary>历史答案 ({{ getQuestionStat(sec.order, q).all_answers.length }}次)</summary>
                    <div class="ep-history-list">
                      <span v-for="(ans, i) in getQuestionStat(sec.order, q).all_answers" :key="i" class="ep-history-tag">{{ ans || '空' }}</span>
                    </div>
                  </details>
                </template>

                <!-- ===== 情况2：用户没做过这道题 ===== -->
                <template v-else>
                  <div class="ep-undone-badge">📝 你还没做过这道题</div>

                  <!-- 正确答案 -->
                  <div v-if="q.answer" class="ep-answer-line">
                    <span class="ep-label">正确答案</span>
                    <span class="ep-answer-val">{{ q.answer }}{{ q.options ? ' (' + getOptionText(q.options, q.answer) + ')' : '' }}</span>
                  </div>

                  <!-- 解析 -->
                  <div v-if="q.explanation" class="ep-explanation">
                    <span class="ep-label">解析</span>
                    <p>{{ q.explanation }}</p>
                  </div>

                  <!-- AI 分析提示 -->
                  <div v-if="q.ai_analysis_hint" class="ep-ai-hint">
                    <span class="ep-label">💡 AI 分析</span>
                    <p>{{ q.ai_analysis_hint }}</p>
                  </div>

                  <!-- 提示先做题 -->
                  <div class="ep-ai-placeholder">
                    🔒 先做题才能获得 AI 个性化批改和建议
                  </div>
                </template>

                <!-- 参考译文/范文（两种情况下都显示） -->
                <div v-if="q.answer?.reference_translation" class="ep-ref">
                  <span class="ep-label">参考译文</span>
                  <p>{{ q.answer.reference_translation }}</p>
                </div>
                <div v-if="q.answer?.sample_essay" class="ep-ref">
                  <span class="ep-label">参考范文</span>
                  <p>{{ q.answer.sample_essay }}</p>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- ===== 浮动提交栏 ===== -->
        <div v-if="mode === 'practice'" class="ep-submit-bar glass-panel">
          <div class="ep-submit-info">
            <span>已答 {{ answeredCount }} / {{ totalQuestionCount }} 题</span>
            <div class="ep-submit-progress">
              <div class="ep-submit-fill" :style="{ width: (answeredCount / totalQuestionCount * 100) + '%' }"></div>
            </div>
          </div>
          <button class="ep-submit-btn" :disabled="submitting" @click="handleSubmit">
            {{ submitting ? '批改中...' : '交卷' }}
          </button>
        </div>

        <!-- ===== 解析模式：底部返回 ===== -->
        <div v-if="mode === 'review'" class="ep-review-footer">
          <button class="ep-submit-btn" @click="handleBack">返回</button>
        </div>
      </div>
    </div>

    <!-- ===== 交卷结果弹窗 ===== -->
    <div v-if="showResult" class="ep-modal-overlay" @click.self="showResult = false">
      <div class="ep-result-modal glass-panel">
        <h2 class="ep-result-title">📝 交卷完成</h2>
        <div class="ep-score-circle" :class="scoreLevel">
          <span class="ep-score-num">{{ result?.score_pct || 0 }}</span>
          <span class="ep-score-unit">分</span>
        </div>
        <div class="ep-score-detail">
          {{ result?.total_score }} / {{ result?.max_score }} 分
          <span v-if="result?.max_score_full !== result?.max_score">（全卷 {{ result?.max_score_full }} 分）</span>
        </div>
        <div v-if="result?.section_scores" class="ep-section-scores">
          <div v-for="s in result.section_scores" :key="s.order" class="ep-ss-row">
            <span>{{ s.name }}</span>
            <span>{{ s.score }} / {{ s.max_score }}</span>
          </div>
        </div>
        <div class="ep-result-actions">
          <button class="ep-result-btn gen" @click="generatePlan" :disabled="generatingPlan">
            {{ generatingPlan ? '生成中...' : '生成备考计划' }}
          </button>
          <button class="ep-result-btn sec" @click="switchToReview">查看解析</button>
          <button class="ep-result-btn pri" @click="handleBack">返回</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getExamPaper, submitExamPaper, submitExamPlan } from '@/api/subjectPlan'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const paperId = computed(() => route.params.paperId)
const syllabusId = computed(() => route.query.syllabus_id || '')
const mode = computed(() => route.query.mode || 'practice') // 'practice' | 'review'

const loading = ref(true)
const paper = ref(null)
const history = ref(null)
const answers = ref({})
const submitting = ref(false)
const showResult = ref(false)
const result = ref(null)
const timerSec = ref(0)
let timerInterval = null

const activeSection = ref(1)
const contentRef = ref(null)
const sectionRefs = ref({})
const usedWordBank = ref({})

// ===== 计算 =====

const visibleSections = computed(() => {
  return (paper.value?.sections || []).filter(s => !s.disabled)
})

const totalQuestionCount = computed(() => {
  let count = 0
  for (const sec of visibleSections.value) {
    count += sec.questions?.length || 0
  }
  return count
})

const answeredCount = computed(() => {
  let count = 0
  for (const sec of visibleSections.value) {
    for (const q of (sec.questions || [])) {
      const key = answerKey(sec.order, q)
      if (answers.value[key] && answers.value[key].trim()) count++
    }
  }
  return count
})

const timerDisplay = computed(() => {
  const m = Math.floor(timerSec.value / 60)
  const s = timerSec.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

const scoreLevel = computed(() => {
  const pct = result.value?.score_pct || 0
  if (pct >= 85) return 'great'
  if (pct >= 60) return 'pass'
  return 'fail'
})

// ===== 辅助函数 =====

function answerKey(secOrder, q) {
  const idx = q.index || q.question_number || q.blank_index
  return `${secOrder}_${idx}`
}

function isSubjective(q) {
  return ['essay', 'translation', 'short_answer', 'case_analysis', 'teaching_design', 'analysis'].includes(q.question_type)
}

function getOptionText(options, key) {
  return options?.find(o => o.key === key)?.text || ''
}

function getWordByLetter(wordBank, letter) {
  return wordBank?.find(w => w.letter === letter)?.word || ''
}

function isSectionDone(sec) {
  if (!sec.questions?.length) return false
  return sec.questions.every(q => {
    const key = answerKey(sec.order, q)
    return answers.value[key] && answers.value[key].trim()
  })
}

// ===== 选词填空渲染 =====

function renderBankedPassage(sec) {
  let text = (sec.passage || '').replace(/\((\d+)\)____/g, (_, num) => {
    const idx = parseInt(num)
    const sel = answers.value[`${sec.order}_${idx}`] || ''
    if (sel) {
      const word = getWordByLetter(sec.word_bank, sel)
      return `<span class="bc-blank filled">${sel}. ${word}</span>`
    }
    return `<span class="bc-blank">(${num})___</span>`
  })
  return text
}

function getBankedHistory(secOrder, blankIndex) {
  if (!history.value?.question_accuracy) return null
  const stat = history.value.question_accuracy[String(blankIndex)]
  if (!stat) return null
  return {
    lastAnswer: stat.last_answer,
    accuracy: stat.accuracy,
    isCorrect: stat.last_answer && stat.last_answer !== '' ? null : null
  }
}

function getQuestionResult(secOrder, q) {
  // 返回该题的用户答题结果（仅在提交后 review 时使用）
  if (!result.value?.question_results) return null
  const idx = q.index || q.question_number
  const r = result.value.question_results.find(
    r => r.section_order === secOrder && r.index === idx
  ) || result.value.question_results.find(
    r => r.section?.includes && r.index === idx
  )
  return r || null
}

function getQuestionStat(secOrder, q) {
  if (!history.value?.question_accuracy) return null
  const idx = q.index || q.question_number || q.blank_index
  return history.value.question_accuracy[String(idx)] || null
}

function getLatestResult(secOrder, q) {
  // 返回最近一次提交的完整结果（含 AI 实时分析）
  if (!history.value?.latest_results) return null
  const idx = q.index || q.question_number || q.blank_index
  return history.value.latest_results[String(idx)] || null
}

function isLastAnswerCorrect(secOrder, q) {
  const stat = getQuestionStat(secOrder, q)
  if (!stat || stat.attempts === 0) return null
  // 客观题：对比答案
  const correctAns = q.answer?.trim().toUpperCase()
  const lastAns = stat.last_answer?.trim().toUpperCase()
  if (correctAns && lastAns) return lastAns === correctAns
  // 主观题：从 AI feedback 判断
  if (stat.ai_feedback) {
    const score = stat.ai_feedback.score || 0
    const max = stat.ai_feedback.max_score || 1
    return (score / max) >= 0.6
  }
  return null
}

// ===== 加载套卷 =====

async function loadPaper() {
  loading.value = true
  try {
    const userId = authStore.user?.id || ''
    const data = await getExamPaper(paperId.value, mode.value, userId)
    if (data.error) {
      alert('套卷不存在')
      router.back()
      return
    }
    paper.value = data
    history.value = data.user_history || null

    // 解析模式：预填历史答案
    if (mode.value === 'review' && history.value?.question_accuracy) {
      for (const sec of data.sections) {
        if (sec.disabled) continue
        for (const q of (sec.questions || [])) {
          const idx = q.index || q.question_number || q.blank_index
          const stat = history.value.question_accuracy[String(idx)]
          if (stat?.last_answer) {
            answers.value[answerKey(sec.order, q)] = stat.last_answer
          }
        }
      }
    }
  } catch (e) {
    console.error('加载套卷失败:', e)
    alert('加载套卷失败')
  } finally {
    loading.value = false
  }
}

// ===== 计时器 =====

function startTimer() {
  if (mode.value !== 'practice') return
  timerInterval = setInterval(() => { timerSec.value++ }, 1000)
}

// ===== 提交 =====

async function handleSubmit() {
  const unanswered = totalQuestionCount.value - answeredCount.value
  if (unanswered > 0) {
    if (!confirm(`还有 ${unanswered} 题未作答，确定交卷吗？`)) return
  }
  submitting.value = true
  try {
    const payload = {
      user_id: authStore.user?.id || '',
      answers: {},
      elapsed_seconds: timerSec.value,
    }
    // 收集所有答案
    for (const sec of visibleSections.value) {
      for (const q of (sec.questions || [])) {
        const key = answerKey(sec.order, q)
        payload.answers[key] = answers.value[key] || ''
      }
    }
    result.value = await submitExamPaper(paperId.value, payload)
    showResult.value = true
  } catch (e) {
    console.error('交卷失败:', e)
    alert('交卷失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    submitting.value = false
  }
}

// ===== 切换到解析 =====

const generatingPlan = ref(false)

async function generatePlan() {
  generatingPlan.value = true
  try {
    const res = await submitExamPlan(paperId.value, {
      user_id: authStore.user?.id || '',
      period_days: 30,
      daily_minutes: 60
    })
    if (res.error) { alert(res.error); return }
    showResult.value = false
    router.push(`/plan-detail/${res.plan_id}`)
  } catch (e) {
    alert('生成计划失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    generatingPlan.value = false
  }
}

function switchToReview() {
  showResult.value = false
  router.replace({
    path: route.path,
    query: { ...route.query, mode: 'review' }
  })
}

// ===== 导航 =====

function scrollToSection(order) {
  activeSection.value = order
  const el = sectionRefs.value[order]
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function handleBack() {
  if (syllabusId.value) {
    router.push(`/subject-plan/${syllabusId.value}`)
  } else {
    router.back()
  }
}

// ===== 生命周期 =====

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  loadPaper().then(() => {
    if (mode.value === 'practice') startTimer()
  })
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
  window.removeEventListener('scroll', onScroll)
})

// 监听滚动以更新当前 section
let scrollTimer = null
function onScroll() {
  if (scrollTimer) return
  scrollTimer = setTimeout(() => {
    scrollTimer = null
    let closest = 1
    let minDist = Infinity
    for (const sec of visibleSections.value) {
      const el = sectionRefs.value[sec.order]
      if (!el) continue
      const rect = el.getBoundingClientRect()
      const dist = Math.abs(rect.top - 120)
      if (dist < minDist) { minDist = dist; closest = sec.order }
    }
    activeSection.value = closest
  }, 100)
}

// 做题↔解析模式切换：重新加载
let lastMode = mode.value
watch(() => route.query.mode, async (newMode) => {
  const m = newMode || 'practice'
  if (m !== lastMode && paper.value) {
    lastMode = m
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
    await loadPaper()
    if (m === 'practice') startTimer()
  }
})
</script>

<style scoped>
/* ===== 页面容器 ===== */
.ep-page {
  min-height: 100vh;
  position: relative;
  color: #e0e0e0;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.ep-bg {
  position: fixed; inset: 0;
  background: radial-gradient(ellipse at 20% 20%, rgba(64,158,255,.06) 0%, transparent 60%),
              radial-gradient(ellipse at 80% 80%, rgba(139,92,246,.05) 0%, transparent 60%),
              #080d18;
  z-index: -1;
}

/* ===== 毛玻璃面板 ===== */
.glass-panel {
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.06);
  backdrop-filter: blur(16px);
  border-radius: 14px;
}
.glass-input {
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 10px;
  color: #e0e0e0;
  padding: 12px 16px;
  font-size: 15px;
  resize: vertical;
  width: 100%;
  font-family: inherit;
  transition: border-color .2s;
}
.glass-input:focus {
  outline: none;
  border-color: rgba(64,158,255,.4);
}

/* ===== 顶部栏 ===== */
.ep-topbar {
  position: sticky; top: 12px; z-index: 100;
  display: flex; align-items: center; gap: 16px;
  padding: 12px 20px; margin: 12px 20px 0;
}
.ep-back {
  width: 40px; height: 40px;
  display: flex; align-items: center; justify-content: center;
  background: none; border: 1px solid rgba(255,255,255,.08);
  border-radius: 10px; color: #999; cursor: pointer;
  flex-shrink: 0; transition: all .2s;
}
.ep-back:hover { color: #fff; border-color: rgba(255,255,255,.2); }
.ep-back svg { width: 18px; height: 18px; }
.ep-title-area { flex: 1; min-width: 0; }
.ep-title { font-size: 18px; font-weight: 700; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ep-meta { display: flex; gap: 10px; align-items: center; margin-top: 4px; font-size: 13px; color: #999; }
.ep-type-tag { padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
.ep-type-tag.real { background: rgba(255,107,107,.15); color: #ff6b6b; }
.ep-type-tag.sim { background: rgba(255,179,0,.15); color: #ffb300; border: 1px dashed rgba(255,179,0,.3); }
.ep-note { color: #888; font-size: 12px; }
.ep-top-actions { flex-shrink: 0; }
.ep-timer { display: flex; align-items: center; gap: 6px; font-size: 16px; font-weight: 600; font-variant-numeric: tabular-nums; color: #fff; }
.ep-timer svg { width: 16px; height: 16px; }
.ep-timer.warning { color: #ff6b6b; animation: pulse-warn 1s infinite; }
@keyframes pulse-warn { 0%,100% { opacity: 1; } 50% { opacity: .5; } }
.ep-history-badge { font-size: 13px; color: #409eff; padding: 4px 10px; background: rgba(64,158,255,.1); border-radius: 8px; }

/* ===== 加载 ===== */
.ep-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; gap: 16px; color: #999; }
.loading-pulse { width: 40px; height: 40px; border-radius: 50%; background: rgba(64,158,255,.3); animation: pulse 1.5s infinite; }
@keyframes pulse { 0% { transform: scale(.8); opacity: .3; } 50% { transform: scale(1.1); opacity: .8; } 100% { transform: scale(.8); opacity: .3; } }

/* ===== 主内容 ===== */
.ep-main { display: flex; gap: 20px; padding: 16px 20px 100px; max-width: 1400px; margin: 0 auto; }

/* 左侧导航 */
.ep-nav { width: 240px; padding: 10px; position: sticky; top: 100px; height: fit-content; flex-shrink: 0; }
.ep-nav-section { display: flex; align-items: center; gap: 10px; padding: 12px 14px; border-radius: 10px; cursor: pointer; transition: all .2s; margin-bottom: 2px; }
.ep-nav-section:hover { background: rgba(255,255,255,.04); }
.ep-nav-section.active { background: rgba(64,158,255,.08); border: 1px solid rgba(64,158,255,.2); }
.ep-nav-section.done { opacity: .6; }
.ep-nav-num { width: 28px; height: 28px; border-radius: 50%; background: rgba(255,255,255,.06); display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.ep-nav-info { flex: 1; min-width: 0; }
.ep-nav-name { display: block; font-size: 13px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ep-nav-score { font-size: 11px; color: #888; }
.ep-nav-check { color: #10b981; font-size: 14px; font-weight: 700; }

/* 右侧内容 */
.ep-content { flex: 1; max-width: 900px; overflow-y: visible; }

/* Section 标题 */
.ep-section-head { display: flex; gap: 14px; padding: 18px 22px; margin-bottom: 14px; align-items: flex-start; }
.ep-section-head h3 { margin: 0 0 4px; font-size: 17px; }
.ep-section-head p { margin: 0; font-size: 13px; color: #999; }
.ep-section-badge { width: 36px; height: 36px; border-radius: 10px; background: rgba(64,158,255,.15); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px; color: #409eff; flex-shrink: 0; }
.ep-section-meta { color: #666 !important; font-size: 12px !important; }

/* ===== 选词填空 ===== */
.ep-banked-cloze { padding: 20px 24px; margin-bottom: 14px; }
.bc-word-bank { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid rgba(255,255,255,.06); }
.bc-word { padding: 4px 10px; background: rgba(255,255,255,.05); border-radius: 6px; font-size: 13px; color: #ccc; }
.bc-word b { color: #409eff; }
.bc-word.used { opacity: .3; text-decoration: line-through; }
.bc-passage { line-height: 2; font-size: 15px; }
:deep(.bc-blank) { display: inline-block; min-width: 80px; padding: 2px 8px; margin: 0 2px; background: rgba(64,158,255,.1); border: 1px dashed rgba(64,158,255,.25); border-radius: 4px; text-align: center; font-size: 13px; color: #409eff; }
:deep(.bc-blank.filled) { border-style: solid; border-color: rgba(64,158,255,.4); }

/* 选词填空答案 */
.bc-answers { margin-top: 14px; padding: 14px 18px; }
.bc-answer-row { display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,.03); }
.bc-ans-num { font-weight: 700; color: #666; width: 24px; }
.bc-ans-letter { display: inline-flex; width: 28px; height: 28px; align-items: center; justify-content: center; border-radius: 6px; background: rgba(64,158,255,.1); font-weight: 700; }
.bc-ans-letter.correct { background: rgba(16,185,129,.15); color: #10b981; }
.bc-ans-letter.wrong { background: rgba(255,107,107,.15); color: #ff6b6b; }
.bc-ans-word { color: #ccc; font-size: 13px; }
.bc-ans-exp { flex-basis: 100%; font-size: 13px; color: #888; margin-top: 2px; }
.bc-user-info { font-size: 12px; color: #409eff; }

/* ===== 题目卡片 ===== */
.ep-question { padding: 22px 24px; margin-bottom: 14px; transition: border-color .3s; }
.ep-question.correct { border-color: rgba(16,185,129,.25); }
.ep-question.wrong { border-color: rgba(255,107,107,.25); }
.ep-q-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.ep-q-num { font-size: 13px; color: #888; font-weight: 600; }
.ep-q-score { font-size: 13px; color: #409eff; font-weight: 600; }
.ep-q-stem { font-size: 15px; line-height: 1.7; margin-bottom: 14px; white-space: pre-wrap; }
.ep-q-passage { font-size: 14px; line-height: 1.8; margin-bottom: 14px; padding: 14px 18px; background: rgba(255,255,255,.02); border-left: 3px solid rgba(64,158,255,.2); border-radius: 0 8px 8px 0; }

/* 选择题 */
.ep-choices { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
.ep-choice { display: flex; align-items: center; gap: 10px; padding: 10px 14px; border-radius: 8px; cursor: pointer; transition: all .2s; border: 1px solid transparent; }
.ep-choice:hover { background: rgba(255,255,255,.03); }
.ep-choice.selected { background: rgba(64,158,255,.08); border-color: rgba(64,158,255,.25); }
.ep-choice.is-correct { background: rgba(16,185,129,.06); border-color: rgba(16,185,129,.3); }
.ep-choice.is-wrong { background: rgba(255,107,107,.06); border-color: rgba(255,107,107,.3); }
.ep-choice input { accent-color: #409eff; }
.ep-choice-key { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: rgba(255,255,255,.08); font-weight: 700; font-size: 13px; flex-shrink: 0; }
.ep-choice-text { font-size: 14px; line-height: 1.5; }

/* 主观题 */
.ep-subjective { margin-bottom: 14px; }
.ep-textarea { min-height: 160px; }
.ep-submitted-answer { padding: 14px 18px; background: rgba(255,255,255,.02); border-radius: 10px; border: 1px solid rgba(255,255,255,.06); font-size: 14px; line-height: 1.6; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }

/* ===== 解析区 ===== */
.ep-review-block { margin-top: 14px; padding: 16px 18px; background: rgba(255,255,255,.02); border-radius: 10px; display: flex; flex-direction: column; gap: 12px; }
.ep-label { font-size: 12px; font-weight: 700; color: #666; text-transform: uppercase; display: block; margin-bottom: 4px; }
.ep-answer-line { }
.ep-answer-val { font-size: 15px; font-weight: 700; color: #10b981; }
.ep-ref p { font-size: 14px; line-height: 1.6; color: #bbb; margin: 4px 0 0; white-space: pre-wrap; }
.ep-explanation p { font-size: 14px; line-height: 1.7; color: #ccc; margin: 4px 0 0; }
.ep-ai-hint { padding: 10px 14px; background: rgba(139,92,246,.08); border-radius: 8px; border-left: 3px solid rgba(139,92,246,.3); }
.ep-ai-hint p { font-size: 13px; line-height: 1.6; color: #bbb; margin: 4px 0 0; }
.ep-user-stat { display: flex; gap: 8px; align-items: baseline; flex-wrap: wrap; padding: 8px 12px; background: rgba(64,158,255,.06); border-radius: 8px; font-size: 13px; color: #999; }
.ep-user-stat .ep-label { display: inline; margin-right: 4px; }

/* ===== 解析模式 — 已做/未做区分 ===== */
.ep-done-badge { font-size: 13px; color: #10b981; padding: 6px 10px; background: rgba(16,185,129,.08); border-radius: 8px; margin-bottom: 4px; }
.ep-undone-badge { font-size: 13px; color: #f59e0b; padding: 6px 10px; background: rgba(245,158,11,.08); border-radius: 8px; margin-bottom: 4px; }
.ep-your-answer { padding: 10px 14px; border-radius: 8px; margin: 6px 0; font-size: 14px; }
.ep-your-answer.correct { background: rgba(16,185,129,.06); border: 1px solid rgba(16,185,129,.15); }
.ep-your-answer.wrong { background: rgba(255,107,107,.06); border: 1px solid rgba(255,107,107,.15); }
.ep-your-answer .ep-label { color: #888; }
.ep-ai-feedback { margin-top: 8px; padding: 10px 14px; background: rgba(139,92,246,.04); border-radius: 8px; border-left: 3px solid rgba(139,92,246,.25); }
.ep-ai-score { font-size: 14px; font-weight: 700; color: #a78bfa; margin-bottom: 6px; }
.ep-ai-fb-text { font-size: 14px; line-height: 1.6; color: #ccc; margin: 0; }
.ep-ai-detail { margin-top: 8px; }
.ep-ai-tag { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 700; }
.ep-ai-tag.good { background: rgba(16,185,129,.12); color: #10b981; }
.ep-ai-tag.bad { background: rgba(255,107,107,.12); color: #ff6b6b; }
.ep-ai-detail ul { margin: 6px 0 0 18px; font-size: 13px; color: #bbb; line-height: 1.5; }
.ep-ai-suggestion { margin-top: 8px; font-size: 13px; color: #a78bfa; line-height: 1.6; background: rgba(139,92,246,.06); padding: 8px 12px; border-radius: 6px; }
.ep-ai-placeholder { margin-top: 8px; padding: 12px 16px; background: rgba(255,255,255,.02); border: 1px dashed rgba(255,255,255,.1); border-radius: 8px; font-size: 13px; color: #666; text-align: center; }
.ep-ai-mistake { margin-top: 8px; padding: 12px 16px; background: rgba(255,152,0,.04); border-left: 3px solid rgba(255,152,0,.35); border-radius: 8px; }
.ep-ai-mistake-title { font-size: 13px; font-weight: 700; color: #ff9800; margin-bottom: 8px; }
.ep-ai-mistake p { font-size: 13px; color: #ccc; margin: 4px 0; line-height: 1.5; }
.ep-history-detail { margin-top: 8px; font-size: 13px; color: #888; }
.ep-history-detail summary { cursor: pointer; color: #999; }
.ep-history-list { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }
.ep-history-tag { padding: 2px 8px; background: rgba(255,255,255,.04); border-radius: 4px; font-size: 12px; color: #aaa; }

/* ===== 浮动提交栏 ===== */
.ep-submit-bar { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); display: flex; align-items: center; gap: 20px; padding: 12px 24px; z-index: 200; border: 1px solid rgba(255,255,255,.1); box-shadow: 0 8px 32px rgba(0,0,0,.5); }
.ep-submit-info { display: flex; flex-direction: column; gap: 6px; min-width: 160px; font-size: 13px; color: #999; }
.ep-submit-progress { width: 100%; height: 4px; background: rgba(255,255,255,.06); border-radius: 2px; overflow: hidden; }
.ep-submit-fill { height: 100%; background: linear-gradient(90deg, #409eff, #10b981); border-radius: 2px; transition: width .3s; }
.ep-submit-btn { padding: 10px 32px; border: none; border-radius: 10px; font-size: 15px; font-weight: 700; cursor: pointer; background: linear-gradient(135deg, #ff6b6b, #ff4757); color: #fff; transition: all .2s; }
.ep-submit-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(255,107,107,.4); }
.ep-submit-btn:disabled { opacity: .5; cursor: not-allowed; }

/* ===== 解析底部 ===== */
.ep-review-footer { display: flex; justify-content: center; margin: 30px 0 60px; }
.ep-review-footer .ep-submit-btn { background: linear-gradient(135deg, #409eff, #6366f1); }

/* ===== 结果弹窗 ===== */
.ep-modal-overlay { position: fixed; inset: 0; z-index: 300; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,.6); backdrop-filter: blur(8px); }
.ep-result-modal { padding: 36px 44px; text-align: center; max-width: 460px; width: 90%; }
.ep-result-title { font-size: 22px; margin: 0 0 24px; }
.ep-score-circle { width: 120px; height: 120px; border-radius: 50%; margin: 0 auto 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 4px solid; }
.ep-score-circle.great { border-color: #10b981; color: #10b981; }
.ep-score-circle.pass { border-color: #f59e0b; color: #f59e0b; }
.ep-score-circle.fail { border-color: #ff6b6b; color: #ff6b6b; }
.ep-score-num { font-size: 36px; font-weight: 800; line-height: 1; }
.ep-score-unit { font-size: 14px; }
.ep-score-detail { font-size: 15px; color: #999; margin-bottom: 16px; }
.ep-section-scores { display: flex; flex-direction: column; gap: 6px; margin-bottom: 20px; }
.ep-ss-row { display: flex; justify-content: space-between; font-size: 14px; color: #ccc; padding: 4px 12px; }
.ep-result-actions { display: flex; gap: 12px; justify-content: center; }
.ep-result-btn { padding: 10px 28px; border-radius: 10px; border: none; font-size: 15px; font-weight: 600; cursor: pointer; transition: all .2s; }
.ep-result-btn.pri { background: rgba(255,255,255,.1); color: #ccc; }
.ep-result-btn.pri:hover { background: rgba(255,255,255,.2); }
.ep-result-btn.sec { background: rgba(64,158,255,.15); color: #409eff; }
.ep-result-btn.sec:hover { background: rgba(64,158,255,.25); }
.ep-result-btn.gen { background: linear-gradient(135deg, rgba(16,185,129,.2), rgba(64,158,255,.2)); color: #10b981; border: 1px solid rgba(16,185,129,.2); }
.ep-result-btn.gen:hover:not(:disabled) { background: linear-gradient(135deg, rgba(16,185,129,.35), rgba(64,158,255,.35)); }
.ep-result-btn.gen:disabled { opacity: .4; }

@media (max-width: 900px) {
  .ep-nav { display: none; }
  .ep-main { padding: 12px; }
  .ep-topbar { margin: 8px; padding: 10px 14px; }
  .ep-submit-bar { left: 12px; right: 12px; transform: none; }
}
</style>
