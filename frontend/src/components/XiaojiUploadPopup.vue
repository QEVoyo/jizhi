<template>
  <Teleport to="body">
    <Transition name="xj-pop">
      <div v-if="popupState.open" class="xj-overlay" @click.self="onOverlayClick">
        <section class="xj-panel">
          <!-- 头部 -->
          <header class="xj-head">
            <div class="xj-id">
              <img :src="look" alt="" class="xj-avatar">
              <div>
                <div class="xj-name">小基 · 小窗</div>
                <div class="xj-sub">{{ stageText }}</div>
              </div>
            </div>
            <div class="xj-head-right">
              <span v-if="isLockedStage" class="xj-lock">🔒 处理中</span>
              <button class="xj-x" :title="isLockedStage ? '处理中，关闭前会先确认' : '关闭'" @click="close">✕</button>
            </div>
          </header>

          <!-- 错误条 -->
          <p v-if="error" class="xj-error">{{ error }}</p>

          <!-- ① 选文件 -->
          <div v-if="stage === 'pick'" class="xj-body">
            <div
              class="xj-drop"
              :class="{ over: dragOver }"
              @dragover.prevent="dragOver = true"
              @dragleave.prevent="dragOver = false"
              @drop.prevent="onDrop"
              @click="fileInput?.click()"
            >
              <div class="xj-drop-icon">📄</div>
              <p class="xj-drop-title">把资料拖进来，我来出题</p>
              <p class="xj-drop-sub">PDF · PPTX · DOCX · XLSX · 图片 · TXT / MD</p>
              <p class="xj-drop-note">视频/音频暂时看不懂；可以先截图关键页</p>
              <input ref="fileInput" type="file" hidden
                     accept=".pdf,.pptx,.docx,.xlsx,.csv,.txt,.md,.png,.jpg,.jpeg,.webp"
                     @change="onPick">
            </div>
          </div>

          <!-- ② 解析中 -->
          <div v-else-if="stage === 'parsing'" class="xj-body xj-center">
            <div class="xj-spin"></div>
            <p class="xj-stage-title">我正在看这份文件…</p>
            <p class="xj-stage-sub">{{ parseHint }}</p>
            <div class="xj-progress"><span :style="{ width: progress + '%' }"></span></div>
          </div>

          <!-- ③ 确认可出题点 -->
          <div v-else-if="stage === 'confirm'" class="xj-body">
            <div class="xj-profile">
              <div class="xj-profile-row">
                <span class="xj-tag">{{ profileLabel }}</span>
                <span class="xj-tag">{{ job?.profile?.domain || '通用' }}</span>
                <span class="xj-tag">建议 {{ job?.profile?.estimated_questions ?? '—' }} 道</span>
                <span v-if="job?.profile?.answer_key_present" class="xj-tag warn">含答案区</span>
              </div>
              <p class="xj-rec">{{ job?.profile?.recommendation || '我读完了，下面是可出题点。' }}</p>
              <p v-if="warnings.length" class="xj-warn">{{ warnings.join('；') }}</p>
            </div>

            <div v-if="seeds.length" class="xj-seeds">
              <label class="xj-seed" v-for="s in seeds" :key="s.id" :class="{ on: isSelected(s.id) }">
                <input type="checkbox" :checked="isSelected(s.id)" @change="toggleSeed(s.id)">
                <div class="xj-seed-main">
                  <div class="xj-seed-top">
                    <span class="xj-seed-concept">{{ s.concept }}</span>
                    <span class="xj-kind">{{ kindLabel(s.kind) }}</span>
                    <span class="xj-score" :class="scoreClass(s.questionability)">
                      {{ Math.round((s.questionability || 0) * 100) }}
                    </span>
                  </div>
                  <p class="xj-prop">{{ s.proposition }}</p>
                  <details class="xj-quote">
                    <summary>看原文依据</summary>
                    <p>{{ s.evidence?.quote || '（无引用）' }}</p>
                  </details>
                </div>
              </label>
            </div>

            <div v-else class="xj-empty">
              <p class="xj-stage-title">这份文件不太适合出题</p>
              <p class="xj-stage-sub">{{ job?.profile?.recommendation || '能出题的点太少，硬出只会得到水题。' }}</p>
              <button class="xj-btn ghost" @click="reset">换一份文件</button>
            </div>

            <div v-if="seeds.length" class="xj-settings">
              <div class="xj-field">
                <span>题量</span>
                <div class="xj-chips">
                  <button v-for="n in [3, 5, 8, 12]" :key="n" :class="{ on: count === n }"
                          @click="count = n">{{ n }}</button>
                </div>
              </div>
              <div class="xj-field">
                <span>题型</span>
                <div class="xj-chips">
                  <button v-for="t in typeOptions" :key="t" :class="{ on: types.includes(t) }"
                          @click="toggleType(t)">{{ t }}</button>
                </div>
              </div>
              <div class="xj-field">
                <span>难度</span>
                <div class="xj-chips">
                  <button v-for="d in ['简单', '中等', '困难']" :key="d"
                          :class="{ on: difficulty === d }" @click="difficulty = d">{{ d }}</button>
                </div>
              </div>
            </div>

            <div v-if="seeds.length" class="xj-actions">
              <button class="xj-btn ghost" @click="reset">不生成</button>
              <button class="xj-btn ghost" :disabled="busy" @click="startGenerate(true)">先出 3 道试试</button>
              <button class="xj-btn primary" :disabled="busy || !selected.length" @click="startGenerate(false)">
                开始生成
              </button>
            </div>
          </div>

          <!-- ④ 生成中 -->
          <div v-else-if="stage === 'generating'" class="xj-body xj-center">
            <div class="xj-spin"></div>
            <p class="xj-stage-title">团队在出题…</p>
            <p class="xj-stage-sub">规划 → 生成 → 校验；没过质检的题会被丢掉</p>
            <div class="xj-progress"><span :style="{ width: progress + '%' }"></span></div>
            <button class="xj-btn ghost" @click="close">先关掉，后台继续</button>
          </div>

          <!-- ⑤ 结果 -->
          <div v-else-if="stage === 'result'" class="xj-body">
            <div class="xj-result">
              <div class="xj-result-num">{{ result?.passed || 0 }}</div>
              <p class="xj-result-label">道题通过质检</p>
              <p class="xj-result-sub">
                生成 {{ result?.generated || 0 }} 道
                <span v-if="droppedCount"> · {{ droppedCount }} 道未通过已丢弃</span>
              </p>
            </div>
            <div v-if="droppedCount" class="xj-dropped">
              <p v-for="(d, i) in (result?.dropped || []).slice(0, 3)" :key="i">
                · {{ d.title || d.seed || '一道题' }}：{{ d.reason }}
              </p>
            </div>
            <div class="xj-actions">
              <button class="xj-btn ghost" @click="reset">再传一个</button>
              <button class="xj-btn ghost" @click="gotoSet">查看题集</button>
              <button class="xj-btn primary" :disabled="!result?.questions?.length" @click="startPractice">
                开始做题
              </button>
            </div>
          </div>

          <!-- ⑥ 小窗做题 -->
          <div v-else-if="stage === 'practice'" class="xj-body">
            <div class="xj-practice-head">
              <span>第 {{ practiceIndex + 1 }} / {{ result?.questions?.length || 0 }} 题</span>
              <span class="xj-practice-score">答对 {{ correctCount }}</span>
            </div>
            <div v-if="current" class="xj-q">
              <p class="xj-q-title">{{ current.title }}</p>

              <div v-if="isChoice" class="xj-options">
                <label v-for="(text, key) in current.options" :key="key"
                       class="xj-option" :class="{ on: answer === key, disabled: !!feedback }">
                  <input type="radio" :value="key" v-model="answer" :disabled="!!feedback">
                  <b>{{ key }}</b><span>{{ text }}</span>
                </label>
              </div>

              <div v-else-if="isJudge" class="xj-options">
                <label v-for="opt in ['正确', '错误']" :key="opt"
                       class="xj-option" :class="{ on: answer === opt, disabled: !!feedback }">
                  <input type="radio" :value="opt" v-model="answer" :disabled="!!feedback">
                  <b>{{ opt }}</b>
                </label>
              </div>

              <textarea v-else v-model="answer" class="xj-input" rows="4"
                        :disabled="!!feedback" placeholder="写下你的答案…"></textarea>

              <div v-if="feedback" class="xj-feedback" :class="feedback.is_correct ? 'ok' : 'bad'">
                <p class="xj-fb-title">{{ feedback.is_correct ? '答对了' : '这题没对' }}</p>
                <p v-if="feedback.ai_feedback && typeof feedback.ai_feedback === 'object'" class="xj-fb-text">
                  {{ feedback.ai_feedback.feedback || feedback.ai_feedback.score }}
                </p>
                <p v-if="current.explanation" class="xj-fb-text">
                  <span class="xj-fb-label">解析：</span>{{ current.explanation }}
                </p>
              </div>

              <div class="xj-actions">
                <button class="xj-btn ghost" @click="toggleChat">问问小基</button>
                <button v-if="!feedback" class="xj-btn primary" :disabled="!answer || submitting"
                        @click="submitOne">{{ submitting ? '判分中…' : '提交' }}</button>
                <button v-else class="xj-btn primary" @click="nextOne">
                  {{ practiceIndex + 1 >= (result?.questions?.length || 0) ? '看结果' : '下一题' }}
                </button>
              </div>
            </div>
          </div>

          <!-- ⑦ 做题总结 -->
          <div v-else-if="stage === 'summary'" class="xj-body xj-center">
            <div class="xj-result">
              <div class="xj-result-num">{{ correctCount }} / {{ answered.length }}</div>
              <p class="xj-result-label">答对</p>
              <p class="xj-result-sub">错题已经进了错题本，之后可以再练。</p>
            </div>
            <div class="xj-actions">
              <button class="xj-btn ghost" @click="startPracticeAgain">再来一遍</button>
              <button class="xj-btn ghost" @click="gotoSet">查看题集</button>
              <button class="xj-btn primary" @click="reset">再传一个</button>
            </div>
          </div>

          <!-- 小窗对话 -->
          <div v-if="chatOpen" class="xj-chat">
            <div class="xj-chat-log">
              <p v-for="(m, i) in chatLog" :key="i" :class="m.role">{{ m.content }}</p>
              <p v-if="chatBusy" class="assistant">小基正在想…</p>
            </div>
            <div class="xj-chat-input">
              <input v-model="chatInput" placeholder="问小基关于这道题…" @keyup.enter="sendChat">
              <button :disabled="chatBusy || !chatInput.trim()" @click="sendChat">发送</button>
            </div>
          </div>
        </section>

        <!-- 关闭确认：必须画在小窗自己的层级里，ElMessageBox 会被 10020 的遮罩盖住 -->
        <div v-if="closeConfirm" class="xj-confirm-mask" @click.self="closeConfirm = ''">
          <div class="xj-confirm">
            <p class="xj-confirm-title">确认关闭</p>
            <p class="xj-confirm-text">{{ closeConfirm }}</p>
            <div class="xj-confirm-actions">
              <button class="xj-btn ghost" @click="closeConfirm = ''">继续等待</button>
              <button class="xj-btn danger" @click="doClose">关闭</button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  uploadQuestionFile, getUploadJob, confirmUpload, generateUpload,
  getUploadResult, sendXiaojiMessage,
} from '@/api/xiaoji'
import { submitPractice } from '@/api/subjectPlan'
import { popupState, closeXiaojiPopup } from '@/xiaoji/popupStore'

const router = useRouter()
const authStore = useAuthStore()
const userId = computed(() => authStore.user?.id || '')

const look = '/images/xiaoji/xiaoji_idle.png'
const stage = ref('pick')
const fileInput = ref(null)
const dragOver = ref(false)
const file = ref(null)
const job = ref(null)
const seeds = ref([])
const selected = ref([])
const count = ref(8)
const types = ref(['选择题'])
const difficulty = ref('中等')
const result = ref(null)
const error = ref('')
const closeConfirm = ref('')
const busy = ref(false)
const progress = ref(0)
const practiceIndex = ref(0)
const answer = ref('')
const feedback = ref(null)
const answered = ref([])
const submitting = ref(false)
const chatOpen = ref(false)
const chatLog = ref([])
const chatInput = ref('')
const chatBusy = ref(false)
let timer = null
let pollToken = 0
let startedAt = 0

const typeOptions = ['选择题', '判断题', '填空题', '计算题', '简答题']

const stageText = computed(() => ({
  pick: '拖一份资料进来',
  parsing: '正在读文件',
  confirm: '看看能出什么题',
  generating: '团队出题中',
  result: '题好了',
  practice: '一起做题',
  summary: '这轮做完了',
}[stage.value] || ''))

const parseHint = computed(() => {
  if (progress.value < 30) return '提取文字 / 识别扫描页'
  if (progress.value < 55) return '判断文件类型与可出题比例'
  return '抽象可出题点（不是 OCR 完就直接出题）'
})

const warnings = computed(() => {
  const w = job.value?.profile?.warnings
  return Array.isArray(w) ? w : []
})

const profileLabel = computed(() => ({
  textbook: '教材/讲义', slides: '课件', paper: '论文/研究', report: '报告',
  notes: '笔记', dataset: '数据表', image: '图片', mixed: '混合内容',
  unknown: '未知类型', exam: '试题', code: '代码',
}[job.value?.profile?.doc_type] || '文档'))

const droppedCount = computed(() => (result.value?.dropped || []).length)
const current = computed(() => result.value?.questions?.[practiceIndex.value] || null)
const qtype = computed(() => String(current.value?.question_type || '').toLowerCase())
const isChoice = computed(() => ['choice', '选择题', '单选'].includes(qtype.value))
const isJudge = computed(() => ['judge', '判断题'].includes(qtype.value))
const correctCount = computed(() => answered.value.filter(a => a.correct).length)

watch(() => popupState.open, (open) => {
  if (!open) { closeConfirm.value = ''; stopTimer(); return }
  if (popupState.jobId) {
    loadJob(popupState.jobId)
  } else if (popupState.file) {
    handleFile(popupState.file)
  } else if (stage.value === 'pick') {
    // 保持
  }
})

onMounted(() => window.addEventListener('beforeunload', onBeforeUnload))
onBeforeUnmount(() => {
  stopTimer()
  window.removeEventListener('beforeunload', onBeforeUnload)
})

// 解析/生成途中刷新或关标签页也要拦一下：后台任务不会停，但这一窗的结果就找不回来了
function onBeforeUnload(e) {
  if (!isLockedStage.value) return
  e.preventDefault()
  e.returnValue = ''
}

function stopTimer() {
  if (timer) { clearInterval(timer); timer = null }
  // 让所有在途的 tick 立刻失效。
  // ⚠️ 2026-10-30 实测：上传轮询和生成轮询共用一个 timer，
  //    上一个 tick 的 Promise 可能在用户点「开始生成」之后才返回，
  //    把 stage 又写回 'confirm'，并顺手 stopTimer() 杀掉生成轮询 ——
  //    表现就是「点完生成一直停在确认页，结果永远不出来」。
  pollToken += 1
}

// 处理中：遮罩完全点不动，X 按钮要走二次确认 —— 用户很容易点空白处误关
const isLockedStage = computed(() => stage.value === 'parsing' || stage.value === 'generating')

function onOverlayClick() {
  if (isLockedStage.value || stage.value === 'confirm') return
  closeXiaojiPopup()
}

function close() {
  if (stage.value === 'parsing') {
    closeConfirm.value = '资料还在解析，关掉后这次解析会作废，需要重新上传。'
    return
  }
  if (stage.value === 'generating') {
    closeConfirm.value = '题目还在生成。关掉小窗后看不到这次结果（后台会继续跑完）。'
    return
  }
  if (stage.value === 'confirm') {
    closeConfirm.value = '关闭后已解析的内容会丢掉，需要重新上传资料。'
    return
  }
  doClose()
}

function doClose() {
  closeConfirm.value = ''
  closeXiaojiPopup()
}

function reset() {
  stopTimer()
  stage.value = 'pick'
  file.value = null
  job.value = null
  seeds.value = []
  selected.value = []
  result.value = null
  error.value = ''
  progress.value = 0
  practiceIndex.value = 0
  answer.value = ''
  feedback.value = null
  answered.value = []
  if (fileInput.value) fileInput.value.value = ''
}

function onPick(e) {
  const f = e.target.files?.[0]
  if (f) handleFile(f)
}

function onDrop(e) {
  dragOver.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f) handleFile(f)
}

async function handleFile(f) {
  if (!userId.value) { ElMessage.error('请先登录'); return }
  file.value = f
  error.value = ''
  stage.value = 'parsing'
  progress.value = 5
  try {
    const res = await uploadQuestionFile(userId.value, f)
    job.value = { id: res.job_id, status: 'parsing', profile: {} }
    pollJob(res.job_id)
  } catch (e) {
    error.value = e?.response?.data?.detail || '上传失败，请重试'
    stage.value = 'pick'
  }
}

function pollJob(jobId) {
  stopTimer()
  const token = ++pollToken
  const tick = async () => {
    try {
      const data = await getUploadJob(jobId, userId.value)
      if (token !== pollToken) return          // 已被更新的一轮取代
      job.value = data.job || job.value
      progress.value = data.job?.progress || progress.value
      if (data.job?.status === 'awaiting_confirm' || data.job?.status === 'confirmed') {
        stopTimer()
        seeds.value = data.seeds || []
        selected.value = seeds.value.map(s => s.id)
        count.value = Math.max(3, Math.min(12, seeds.value.length || 3))
        stage.value = 'confirm'
      } else if (data.job?.status === 'failed') {
        stopTimer()
        error.value = data.job.error || '解析失败'
        stage.value = 'pick'
      }
    } catch (e) {
      if (token !== pollToken) return
      stopTimer()
      error.value = e?.response?.data?.detail || '读取解析进度失败'
      stage.value = 'pick'
    }
  }
  tick()
  timer = setInterval(tick, 1200)
}

async function loadJob(jobId) {
  try {
    const data = await getUploadJob(jobId, userId.value)
    job.value = data.job
    seeds.value = data.seeds || []
    selected.value = seeds.value.map(s => s.id)
    stage.value = data.job?.status === 'awaiting_confirm' ? 'confirm' : 'parsing'
    if (stage.value === 'parsing') pollJob(jobId)
  } catch (e) {
    error.value = '任务不存在或已过期'
    stage.value = 'pick'
  }
}

function isSelected(id) { return selected.value.includes(id) }
function toggleSeed(id) {
  selected.value = isSelected(id)
    ? selected.value.filter(x => x !== id)
    : [...selected.value, id]
}
function toggleType(t) {
  types.value = types.value.includes(t)
    ? types.value.filter(x => x !== t)
    : [...types.value, t]
  if (!types.value.length) types.value = ['选择题']
}

function kindLabel(k) {
  return ({
    definition: '定义', fact: '事实', relation: '关系', process: '流程',
    comparison: '对比', classification: '分类', formula: '公式',
    calculation: '计算', application: '应用', argument: '论证',
    data_trend: '数据', causal: '因果', method: '方法', limitation: '边界',
  }[k] || k)
}
function scoreClass(v) {
  if (v >= 0.8) return 'good'
  if (v >= 0.7) return 'ok'
  return 'weak'
}

async function startGenerate(tryThree) {
  if (!selected.value.length) { ElMessage.warning('至少选一个可出题点'); return }
  busy.value = true
  error.value = ''
  stage.value = 'generating'
  progress.value = 10
  try {
    await confirmUpload(job.value.id, userId.value, {
      seed_ids: selected.value,
      count: tryThree ? 3 : count.value,
      types: types.value,
      difficulty: difficulty.value,
      mode: 'generate',
    })
    await generateUpload(job.value.id, userId.value)
    pollResult(job.value.id)
  } catch (e) {
    error.value = e?.response?.data?.detail || '生成失败'
    busy.value = false
    stage.value = 'confirm'
  }
}

function pollResult(jobId) {
  stopTimer()
  const token = ++pollToken
  const tick = async () => {
    try {
      const data = await getUploadResult(jobId, userId.value)
      if (token !== pollToken) return          // 已被更新的一轮取代
      progress.value = data.progress || progress.value
      if (data.status === 'ready') {
        stopTimer()
        result.value = data
        busy.value = false
        stage.value = 'result'
      } else if (data.status === 'failed') {
        stopTimer()
        busy.value = false
        error.value = data.error || '生成失败'
        stage.value = 'confirm'
      }
    } catch (e) {
      if (token !== pollToken) return
      stopTimer()
      busy.value = false
      error.value = e?.response?.data?.detail || '读取生成结果失败'
      stage.value = 'confirm'
    }
  }
  tick()
  timer = setInterval(tick, 1500)
}

function startPractice() {
  if (!result.value?.questions?.length) return
  practiceIndex.value = 0
  answer.value = ''
  feedback.value = null
  answered.value = []
  stage.value = 'practice'
  startedAt = Date.now()
}

function startPracticeAgain() {
  const qs = result.value?.questions || []
  result.value = { ...result.value, questions: qs }
  startPractice()
}

async function submitOne() {
  if (!current.value || !answer.value || submitting.value) return
  submitting.value = true
  try {
    const res = await submitPractice({
      user_id: userId.value,
      plan_id: '',
      question_id: current.value.id,
      syllabus_id: '',
      user_answer: answer.value,
      source: 'upload',
      time_spent: Math.max(1, Math.round((Date.now() - startedAt) / 1000)),
    })
    feedback.value = res
    answered.value.push({
      questionId: current.value.id,
      correct: !!res.is_correct,
      userAnswer: answer.value,
    })
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '判分失败，请重试')
  } finally {
    submitting.value = false
  }
}

function nextOne() {
  if (practiceIndex.value + 1 >= (result.value?.questions?.length || 0)) {
    stage.value = 'summary'
    return
  }
  practiceIndex.value += 1
  answer.value = ''
  feedback.value = null
  startedAt = Date.now()
}

function toggleChat() {
  chatOpen.value = !chatOpen.value
  if (chatOpen.value && !chatLog.value.length) {
    chatLog.value.push({ role: 'assistant', content: '这题想先听哪一步？我可以只讲思路，不直接告诉你答案。' })
  }
}

async function sendChat() {
  const text = chatInput.value.trim()
  if (!text || chatBusy.value) return
  chatInput.value = ''
  chatLog.value.push({ role: 'user', content: text })
  chatBusy.value = true
  try {
    const ctx = current.value ? `我正在做这道题：「${current.value.title}」。` : ''
    const res = await sendXiaojiMessage({ user_id: userId.value, content: ctx + text })
    chatLog.value.push({ role: 'assistant', content: res.reply || '（小基没说话）' })
  } catch (e) {
    chatLog.value.push({ role: 'assistant', content: '我这边卡了一下，再试一次？' })
  } finally {
    chatBusy.value = false
  }
}

function gotoSet() {
  const id = result.value?.result_set_id || result.value?.set?.id
  if (!id) { ElMessage.info('题集还在生成中'); return }
  close()
  router.push({ path: '/set-detail', query: { id } })
}
</script>

<style scoped>
.xj-overlay {
  position: fixed; inset: 0; z-index: 10020;
  background: rgba(10, 16, 30, .42);
  backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.xj-panel {
  width: min(760px, 94vw); max-height: min(86vh, 860px);
  display: flex; flex-direction: column;
  background: color-mix(in srgb, var(--surface, #ffffff) 92%, transparent);
  border: 1px solid rgba(255, 255, 255, .28);
  border-radius: 20px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, .28);
  overflow: hidden;
}
[data-theme="dark"] .xj-panel {
  background: color-mix(in srgb, var(--surface, #161b26) 92%, transparent);
  border-color: rgba(255, 255, 255, .10);
}
.xj-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; border-bottom: 1px solid rgba(128, 128, 128, .14);
}
.xj-id { display: flex; align-items: center; gap: 10px; }
.xj-head-right { display: flex; align-items: center; gap: 8px; }
.xj-lock { font-size: 11px; color: var(--text-muted); white-space: nowrap; }

/* 关闭确认画在 xj-overlay 内部，避免被 10020 的遮罩盖住 */
.xj-confirm-mask {
  position: absolute; inset: 0; z-index: 10;
  background: rgba(10, 16, 30, .38);
  backdrop-filter: blur(2px);
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.xj-confirm {
  width: min(360px, 92%);
  background: var(--surface, #ffffff);
  border: 1px solid rgba(128, 128, 128, .16);
  border-radius: 16px;
  padding: 18px 18px 14px;
  box-shadow: 0 18px 50px rgba(0, 0, 0, .24);
}
[data-theme="dark"] .xj-confirm { background: var(--surface, #161b26); }
.xj-confirm-title { font-size: 14px; font-weight: 700; color: var(--text-primary); margin: 0 0 6px; }
.xj-confirm-text { font-size: 12.5px; color: var(--text-secondary); line-height: 1.65; margin: 0 0 14px; }
.xj-confirm-actions { display: flex; justify-content: flex-end; gap: 8px; }
.xj-btn.danger {
  border-color: rgba(245, 108, 108, .5);
  background: rgba(245, 108, 108, .12);
  color: #f56c6c; font-weight: 600;
}
.xj-btn.danger:hover:not(:disabled) { background: rgba(245, 108, 108, .2); color: #f56c6c; }
.xj-avatar { width: 38px; height: 38px; object-fit: contain; }
.xj-name { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.xj-sub { font-size: 11.5px; color: var(--text-muted); margin-top: 1px; }
.xj-x {
  width: 30px; height: 30px; border: none; border-radius: 9px;
  background: transparent; color: var(--text-muted); cursor: pointer; font-size: 14px;
}
.xj-x:hover { background: rgba(128, 128, 128, .14); color: var(--text-primary); }

.xj-body { padding: 18px; overflow-y: auto; }
.xj-center { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; text-align: center; }
.xj-stage-title { font-size: 15px; font-weight: 600; color: var(--text-primary); margin: 12px 0 4px; }
.xj-stage-sub { font-size: 12.5px; color: var(--text-muted); margin: 0 0 14px; line-height: 1.6; }

.xj-drop {
  border: 1.5px dashed color-mix(in srgb, var(--brand) 35%, transparent);
  border-radius: 16px; padding: 40px 20px; text-align: center; cursor: pointer;
  background: color-mix(in srgb, var(--brand) 4%, transparent);
  transition: all .2s ease;
}
.xj-drop.over, .xj-drop:hover {
  border-color: var(--brand-bright); background: color-mix(in srgb, var(--brand) 10%, transparent);
}
.xj-drop-icon { font-size: 34px; }
.xj-drop-title { font-size: 15px; font-weight: 600; color: var(--text-primary); margin: 8px 0 4px; }
.xj-drop-sub { font-size: 12px; color: var(--text-secondary); margin: 0; }
.xj-drop-note { font-size: 11.5px; color: var(--text-muted); margin: 10px 0 0; }

.xj-spin {
  width: 34px; height: 34px; border-radius: 50%;
  border: 3px solid color-mix(in srgb, var(--brand) 20%, transparent);
  border-top-color: var(--brand-bright); animation: xj-spin 0.9s linear infinite;
}
@keyframes xj-spin { to { transform: rotate(360deg); } }
.xj-progress {
  width: min(360px, 80%); height: 6px; border-radius: 3px;
  background: rgba(128, 128, 128, .16); overflow: hidden; margin: 4px 0 10px;
}
.xj-progress span {
  display: block; height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--brand), var(--brand-bright));
  transition: width .4s ease;
}

.xj-profile { margin-bottom: 14px; }
.xj-profile-row { display: flex; gap: 6px; flex-wrap: wrap; }
.xj-tag {
  font-size: 11px; color: var(--text-secondary);
  background: rgba(128, 128, 128, .10); padding: 3px 9px; border-radius: 9px;
}
.xj-tag.warn { color: #d48806; background: rgba(250, 178, 25, .12); }
.xj-rec { font-size: 13px; color: var(--text-primary); margin: 10px 0 4px; line-height: 1.6; }
.xj-warn { font-size: 11.5px; color: var(--text-muted); margin: 0; line-height: 1.6; }

.xj-seeds { display: flex; flex-direction: column; gap: 8px; max-height: 300px; overflow-y: auto; padding-right: 2px; }
.xj-seed {
  display: flex; gap: 10px; align-items: flex-start;
  border: 1px solid rgba(128, 128, 128, .16); border-radius: 12px;
  padding: 10px 12px; cursor: pointer; transition: all .15s ease;
}
.xj-seed.on { border-color: color-mix(in srgb, var(--brand) 45%, transparent); background: color-mix(in srgb, var(--brand) 6%, transparent); }
.xj-seed input { margin-top: 3px; }
.xj-seed-main { flex: 1; min-width: 0; }
.xj-seed-top { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.xj-seed-concept { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.xj-kind { font-size: 10.5px; color: var(--text-muted); background: rgba(128, 128, 128, .10); padding: 1px 6px; border-radius: 6px; }
.xj-score { font-size: 10.5px; padding: 1px 6px; border-radius: 6px; font-variant-numeric: tabular-nums; }
.xj-score.good { color: #0ca30c; background: rgba(12, 163, 12, .10); }
.xj-score.ok { color: #d48806; background: rgba(250, 178, 25, .12); }
.xj-score.weak { color: var(--text-muted); background: rgba(128, 128, 128, .10); }
.xj-prop { font-size: 12.5px; color: var(--text-secondary); margin: 4px 0 0; line-height: 1.55; }
.xj-quote { margin-top: 4px; }
.xj-quote summary { font-size: 11px; color: var(--text-muted); cursor: pointer; }
.xj-quote p { font-size: 11.5px; color: var(--text-muted); margin: 4px 0 0; line-height: 1.55; }

.xj-settings { display: flex; flex-direction: column; gap: 10px; margin: 14px 0; }
.xj-field { display: flex; align-items: center; gap: 12px; }
.xj-field > span { width: 40px; font-size: 12px; color: var(--text-muted); flex: none; }
.xj-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.xj-chips button {
  padding: 4px 10px; border-radius: 8px; font-size: 12px; cursor: pointer;
  font-family: inherit; border: 1px solid var(--border-color);
  background: transparent; color: var(--text-secondary);
}
.xj-chips button.on {
  border-color: color-mix(in srgb, var(--brand) 45%, transparent);
  background: color-mix(in srgb, var(--brand) 14%, transparent);
  color: var(--brand-bright); font-weight: 600;
}

.xj-actions { display: flex; gap: 8px; justify-content: flex-end; flex-wrap: wrap; margin-top: 14px; }
.xj-btn {
  padding: 7px 16px; border-radius: 9px; font-size: 12.5px; cursor: pointer;
  font-family: inherit; border: 1px solid var(--border-color);
  background: transparent; color: var(--text-secondary); transition: all .2s ease;
}
.xj-btn:hover:not(:disabled) { background: rgba(128, 128, 128, .10); color: var(--text-primary); }
.xj-btn.primary {
  border-color: color-mix(in srgb, var(--brand) 45%, transparent);
  background: color-mix(in srgb, var(--brand) 16%, transparent);
  color: var(--brand-bright); font-weight: 600;
}
.xj-btn:disabled { opacity: .45; cursor: not-allowed; }

.xj-empty { text-align: center; padding: 10px 0 4px; }
.xj-result { text-align: center; padding: 12px 0 6px; }
.xj-result-num { font-size: 46px; font-weight: 800; color: var(--brand-bright); line-height: 1; }
.xj-result-label { font-size: 13px; color: var(--text-secondary); margin: 4px 0 2px; }
.xj-result-sub { font-size: 12px; color: var(--text-muted); margin: 0; }
.xj-dropped { margin: 10px 0 0; padding: 8px 12px; border-radius: 10px; background: rgba(250, 178, 25, .08); }
.xj-dropped p { font-size: 11.5px; color: var(--text-muted); margin: 2px 0; line-height: 1.5; }

.xj-practice-head { display: flex; justify-content: space-between; font-size: 12px; color: var(--text-muted); margin-bottom: 10px; }
.xj-practice-score { color: var(--brand-bright); }
.xj-q-title { font-size: 15px; font-weight: 600; color: var(--text-primary); line-height: 1.7; margin: 0 0 14px; }
.xj-options { display: flex; flex-direction: column; gap: 8px; }
.xj-option {
  display: flex; gap: 10px; align-items: flex-start;
  border: 1px solid rgba(128, 128, 128, .18); border-radius: 11px;
  padding: 10px 12px; cursor: pointer; transition: all .15s ease;
}
.xj-option.on { border-color: color-mix(in srgb, var(--brand) 45%, transparent); background: color-mix(in srgb, var(--brand) 8%, transparent); }
.xj-option.disabled { cursor: default; opacity: .82; }
.xj-option b { flex: none; width: 20px; height: 20px; border-radius: 50%; background: rgba(128, 128, 128, .12); display: flex; align-items: center; justify-content: center; font-size: 11px; }
.xj-option span { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }
.xj-input {
  width: 100%; border: 1px solid var(--border-color); border-radius: 11px;
  padding: 10px 12px; font-size: 13px; font-family: inherit;
  color: var(--text-primary); background: transparent; resize: vertical;
}
.xj-feedback { margin-top: 12px; border-radius: 11px; padding: 10px 12px; }
.xj-feedback.ok { background: rgba(12, 163, 12, .08); }
.xj-feedback.bad { background: rgba(245, 108, 108, .08); }
.xj-fb-title { font-size: 13px; font-weight: 700; margin: 0 0 4px; color: var(--text-primary); }
.xj-fb-text { font-size: 12px; color: var(--text-secondary); margin: 2px 0; line-height: 1.6; white-space: pre-wrap; }
.xj-fb-label { color: var(--text-muted); }

.xj-error {
  margin: 0; padding: 8px 18px; font-size: 12px; color: #f56c6c;
  background: rgba(245, 108, 108, .08); border-bottom: 1px solid rgba(245, 108, 108, .16);
}

.xj-chat { border-top: 1px solid rgba(128, 128, 128, .14); padding: 10px 16px 14px; }
.xj-chat-log { max-height: 140px; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px; }
.xj-chat-log p { font-size: 12px; line-height: 1.6; margin: 0; padding: 6px 10px; border-radius: 9px; max-width: 86%; }
.xj-chat-log .user { align-self: flex-end; background: color-mix(in srgb, var(--brand) 14%, transparent); color: var(--text-primary); }
.xj-chat-log .assistant { align-self: flex-start; background: rgba(128, 128, 128, .10); color: var(--text-secondary); }
.xj-chat-input { display: flex; gap: 8px; }
.xj-chat-input input {
  flex: 1; border: 1px solid var(--border-color); border-radius: 9px;
  padding: 7px 11px; font-size: 12.5px; font-family: inherit;
  background: transparent; color: var(--text-primary);
}
.xj-chat-input button {
  padding: 7px 14px; border-radius: 9px; font-size: 12px; cursor: pointer;
  font-family: inherit; border: 1px solid color-mix(in srgb, var(--brand) 40%, transparent);
  background: color-mix(in srgb, var(--brand) 12%, transparent); color: var(--brand-bright);
}
.xj-chat-input button:disabled { opacity: .45; cursor: not-allowed; }

.xj-pop-enter-active, .xj-pop-leave-active { transition: opacity .2s ease; }
.xj-pop-enter-from, .xj-pop-leave-to { opacity: 0; }
.xj-pop-enter-active .xj-panel, .xj-pop-leave-active .xj-panel { transition: transform .22s ease; }
.xj-pop-enter-from .xj-panel, .xj-pop-leave-to .xj-panel { transform: translateY(16px) scale(.985); }

@media (max-width: 640px) {
  .xj-overlay { padding: 0; align-items: stretch; }
  .xj-panel { width: 100vw; max-height: 100vh; border-radius: 0; }
}
</style>
