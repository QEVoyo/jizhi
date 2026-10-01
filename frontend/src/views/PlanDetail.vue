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
          <LoadingSpinner
            v-if="loading"
            variant="breathe"
            :flow-steps="['正在展开计划详情...', '正在加载每日任务...', '马上就好...']"
          />

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
          <!-- 当日**最佳率**：按每题「做对过没有」算，重做做错不回退（2026-10-01 用户定调） -->
          <span class="day-acc" v-if="dayAnsweredCount">
            当日最佳率 <b>{{ dayBestRate }}%</b>
            <span class="day-acc-sub">（{{ dayBestCount }}/{{ dayAnsweredCount }} 题做对过）</span>
          </span>
        </div>

        <!-- 学习内容：列表里**只露前两行**，点进去才看完整正文（2026-10-01 用户定调） -->
        <div class="content-section" v-if="dayContentItems.length">
          <div class="section-title">📖 学习内容</div>
          <div
            v-for="(item, idx) in dayContentItems"
            :key="idx"
            class="content-item clickable"
            @click="openLesson(item)"
          >
            <div class="content-topic">
              {{ item.topic }}
              <span class="content-more">{{ item.status === 'completed' ? '✅ 已学' : '点击学习 →' }}</span>
            </div>
            <div class="content-body clamp2">{{ item.description || item.topic + ' 核心概念讲解' }}</div>
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
                <template v-if="q.attempts > 0">
                  {{ q.best_correct ? '✅ 做对过' : '⚠️ 还没做对' }}
                  <span v-if="q.attempts > 1" class="q-attempts">· {{ q.attempts }} 次</span>
                </template>
                <template v-else>⏳ 未做</template>
              </span>
              <span class="q-action">
                <!-- 做错了可以重做（用户定调）；做对过也留着，想刷更高分随他 -->
                <button class="glass-btn primary small" @click="goToQuestion(q)">
                  {{ q.attempts > 0 ? '🔄 再做一次' : '▶ 去做' }}
                </button>
              </span>
            </div>
          </div>
        </div>

        <!-- 学习视频：从自营视频库取（2026-10-01）。
             原来这里是一行写死的「⏳ 待上线」—— video_query 是个 B站搜索词，
             从来没真的取过视频。 -->
        <div class="content-section" v-if="dayVideos.length">
          <div class="section-title">📺 学习视频</div>
          <div v-for="v in dayVideos" :key="v.id" class="video-item">
            <div class="video-head">
              <span class="video-topic">{{ v.topic }}</span>
              <span v-if="v.status === 'completed'" class="video-done">✅ 已看</span>
            </div>

            <div v-if="libState(v.id).loading" class="video-tip">正在视频库里找…</div>

            <!-- 真命中（match_score ≥ 90）：**确实是这个知识点**的讲解 -->
            <template v-else-if="libState(v.id).hits.length">
              <button
                v-for="it in shownHits(v.id)"
                :key="it.id"
                class="video-pick"
                @click="playPlanVideo(v, it)"
              >
                <span class="video-pick-t">{{ it.knowledge_name || it.title || '讲解' }}</span>
                <span class="video-pick-m">
                  <template v-if="ANGLE_LABELS[it.angle]">{{ ANGLE_LABELS[it.angle] }} · </template>
                  {{ it.audio_duration ? Math.round(it.audio_duration) + 's' : '' }}
                </span>
                <span class="video-pick-go">▶ 播放</span>
              </button>
              <!-- 超过 5 条才出「查看更多」（一个知识点可能有多个角度的讲解） -->
              <div
                v-if="libState(v.id).hits.length > 5"
                class="video-more"
                @click="toggleMoreVideos(v.id)"
              >
                {{ libState(v.id).expanded ? '收起' : `查看更多（共 ${libState(v.id).hits.length} 条）` }}
              </div>
            </template>

            <!-- 没有真命中 → 出「生成」按钮（用户定调：**没有就要有个键**） -->
            <template v-else>
              <div class="video-tip">
                视频库里还没有「{{ v.topic }}」的讲解
                <button class="video-gen" @click="loadPlanVideo(v, { ensure: true })">
                  ✦ 生成知识点视频
                </button>
              </div>
              <div v-if="libState(v.id).triggered" class="video-tip sub">
                已排入生成队列，生成好会自动出现（这页在自动等）
              </div>

              <!-- 同学科其它知识点：**标题里就写明不是本知识点**，折叠起来不喧宾夺主 -->
              <details v-if="libState(v.id).related.length" class="video-related">
                <summary>同学科的其他讲解（{{ libState(v.id).related.length }}）· 不是本知识点</summary>
                <button
                  v-for="it in libState(v.id).related"
                  :key="it.id"
                  class="video-pick"
                  @click="playPlanVideo(v, it)"
                >
                  <span class="video-pick-t">{{ it.knowledge_name || it.title || '讲解' }}</span>
                  <span class="video-pick-m">{{ it.audio_duration ? Math.round(it.audio_duration) + 's' : '' }}</span>
                  <span class="video-pick-go">▶ 播放</span>
                </button>
              </details>
            </template>
          </div>
        </div>

        <!-- 播放器：计划里的视频**禁拖进度** —— 只有真看完，「播完 = 学完」才成立 -->
        <el-dialog
          v-model="playingOpen"
          width="880px"
          destroy-on-close
          class="vp-dialog"
          :title="playing?.task?.topic || '学习视频'"
        >
          <VideoLessonPlayer
            v-if="playing"
            :video="playing.video"
            :seekable="false"
            @ended="onVideoEnded"
          />
          <p class="video-note">这段视频不能拖动进度条 —— 从头看完会自动标记为已学。</p>
        </el-dialog>

        <div v-if="!dayTasks.length" class="empty-state">
          <span>📭 当日暂无任务</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
// 作答结果由做题页回写（PUT /learning-plan/task/answer，见 SubjectPractice）；
// updateTaskStatus 在这里仍要用 —— 学完学习内容、看完视频都由这一页标完成。
import { getPlanDetail, updateTaskStatus } from '@/api/learningPlan'
import { getVideoRelated, ensureVideoLib } from '@/api/video'
import { knowledgeKey, ANGLE_LABELS } from '@/utils/videoLib'
import VideoLessonPlayer from '@/components/VideoLessonPlayer.vue'
import { ElMessage } from 'element-plus'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

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
    const todayStr = new Date().toISOString().slice(0, 10)
    const isPastOrToday = dateStr <= todayStr
    let isUnlocked = isFirstDay || isPastOrToday
    if (!isFirstDay && !isPastOrToday) {
      const prevDate = new Date(current)
      prevDate.setDate(prevDate.getDate() - 1)
      const prevDateStr = prevDate.toISOString().slice(0, 10)
      const prevTasks = tasks.value.filter(t => t.date === prevDateStr)
      const prevDone = prevTasks.filter(t => t.status === 'completed').length
      const prevHalf = prevTasks.length > 0 && prevDone >= Math.ceil(prevTasks.length / 2)
      isUnlocked = prevHalf
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

// ===== 当日最佳率（2026-10-01）=====
// 分母是**当天做过的题**（attempts > 0），不是全部任务 ——
// 学习内容和视频不参与正确率，否则这个数会被它们稀释得没意义。
// 分子是其中「做对过」的（best_correct 只增不减，重做做错不回退）。
const dayAnsweredCount = computed(() =>
  dayQuestions.value.filter(q => (q.attempts || 0) > 0).length)
const dayBestCount = computed(() =>
  dayQuestions.value.filter(q => q.best_correct).length)
const dayBestRate = computed(() =>
  dayAnsweredCount.value ? Math.round(dayBestCount.value / dayAnsweredCount.value * 100) : 0)

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

/**
 * 去做某道题（2026-10-01 重写）。
 *
 * ⚠️ 以前跳 `/do-question/{q.id}`，而那个 q.id 是 **learning_tasks 的行 id**。
 *    DoQuestion 拿它去查 `/questions/{id}` —— 查不到 → 404 → 「加载题目失败」，
 *    然后 `router.back()` 直接弹回来，**不会再下落到 sessionStorage 那一层**
 *    （而题目其实就存在那儿）。所以「▶ 去练习」从来没能用过。
 *
 * 现在跳**真正的做题页** SubjectPractice，带 `question_id` —— 阶段 2 已经把
 * 题目落进 `questions` 表并回填了这个字段，所以这一跳取得到题。
 * `lp_task` / `return_to` 是给做题页的：做完回写哪一行、回哪一页。
 *
 * 不再拦「已完成」—— 用户要求「做题错了可以重做」，做对过也想再刷随他。
 */
function goToQuestion(q) {
  if (!q.question_id) {
    ElMessage.warning('这道题还没有题目数据，重新生成一次计划即可')
    return
  }
  const pid = plan.value?.id || route.params.id
  router.push({
    path: '/subject-plan/_/practice',
    query: {
      questions: q.question_id,
      lp_task: q.id,
      return_to: `/plan-detail/${pid}`,
    },
  })
}

/**
 * 进学习页看完整正文。
 * 正文**按需生成**（照学科计划 `generate-learning` 的先例），
 * 列表里只露前两行 —— 一次把 N 天的正文全生成会撑爆响应。
 */
function openLesson(item) {
  const pid = plan.value?.id || route.params.id
  router.push({
    path: `/plan-lesson/${item.id}`,
    // plan_id 要给学习页用来标完成（`PUT /task/status` 需要它才能重算进度）
    query: { plan_id: pid, return_to: `/plan-detail/${pid}` },
  })
}

// ===== 学习视频：接自营视频库（2026-10-01）=====
//
// 以前这里是一行写死的「⏳ 待上线」—— 任务里的 `video_query` 存的是个**B站搜索词**，
// 从来没有真的取过视频。
//
// 现在按知识点去自营视频库检索；没有就一键触发懒生成。这条链路
// 和旧做题页 `DoQuestion.loadLibraryVideos` 是同一套（那边已经跑通了）：
//   getVideoRelated  —— 按 knowledge_key 检索排行
//   ensureVideoLib   —— 没有就排产（懒生成）
//
// 一天可以有**多条**视频 —— 阶段 1 已经让 AI 每天给 1~3 个 knowledge_points，
// 每个知识点一条任务行，所以「内容多的日子多条视频」是数据层自带的，不用开关。
const videoLib = reactive({})   // { [taskId]: { loading, items, triggered } }
const playing = ref(null)       // { task, video }

const videoSubject = computed(() => plan.value?.keywords || '通用')
const playingOpen = computed({
  get: () => !!playing.value,
  set: (v) => { if (!v) playing.value = null },
})

function libState(taskId) {
  if (!videoLib[taskId]) {
    videoLib[taskId] = { loading: false, hits: [], related: [], triggered: false, expanded: false }
  }
  return videoLib[taskId]
}

// 真命中超过 5 条就折叠 —— 一个知识点可能有好几个角度的讲解（讲法/例题/易错…）
const VIDEO_SHOW = 5
function shownHits(taskId) {
  const st = libState(taskId)
  return st.expanded ? st.hits : st.hits.slice(0, VIDEO_SHOW)
}
function toggleMoreVideos(taskId) {
  const st = libState(taskId)
  st.expanded = !st.expanded
}

/**
 * 按 `match_score` 拆开检索结果。**这是这一块的关键。**
 *
 * 后端 `related_videos` 给每条打了分（services/video_gen.py:648）：
 *   100 = 本知识点的 ready 视频
 *    90 = 同一个知识点、只是 subject 命名不同（历史遗留的三套命名）
 *    70 = 同学科的**其它**知识点
 *    55 = **全局热门兜底** —— 和这个知识点毫无关系
 *
 * ⚠️ 第一版我直接拿 `items` 当结果用，而 55 分的兜底**永远非空** ——
 *    于是「生成视频」那个按钮永远不出现，用户设了「三角函数」却看到一堆
 *    「Excel 操作」。只认 ≥90 才叫「这个知识点的讲解」，70/55 是推荐不是答案。
 */
function splitByMatch(items) {
  const all = items || []
  return {
    hits: all.filter(i => (i.match_score || 0) >= 90),
    related: all.filter(i => (i.match_score || 0) === 70),
  }
}

/** 轮询等排产的视频生出来（生成要几分钟；这页会自己刷，不用用户手动重进） */
const pollTimers = {}
function pollPlanVideo(task, key, tries = 0) {
  clearTimeout(pollTimers[task.id])
  if (tries >= 25) return                    // 3s × 25 ≈ 75 秒还没好就不再打扰
  pollTimers[task.id] = setTimeout(async () => {
    const st = libState(task.id)
    try {
      const res = await getVideoRelated({
        knowledge_key: key, subject: videoSubject.value, limit: 8,
      })
      const { hits } = splitByMatch(res?.items)
      st.hits = hits
    } catch { /* 轮询失败就算了，下次进页面还会查 */ }
    if (!st.hits.length) pollPlanVideo(task, key, tries + 1)
  }, 3000)   // 8s → 3s：实测生成只要 25~48 秒，8 秒一跳太钝（2026-10-01）
}

/**
 * 查这个知识点的讲解视频。
 * @param {boolean} ensure true = 没有就排产（用户点「生成知识点视频」时）
 */
async function loadPlanVideo(task, { ensure = false } = {}) {
  const st = libState(task.id)
  const kp = task.topic || task.video_query || ''
  if (!kp) return
  const key = knowledgeKey(videoSubject.value, kp)
  st.loading = true
  try {
    if (ensure) {
      const r = await ensureVideoLib({
        knowledge_key: key, knowledge_name: kp, subject: videoSubject.value,
        // 「1 个保底」—— 不管检索到多少，至少让这个知识点有一条（后端默认就是 1）
        goal: 1,
        // 推送到我的视频库：视频库新增的「推送」分类读的就是这张表。
        // 视频本身是全站共享的，所以推的是「这条和我有关」，不是「这条归我」。
        user_id: authStore.user?.id || '',
        source: 'plan',
        source_ref: task.id,
      })
      st.triggered = !!r?.triggered
      pollPlanVideo(task, key)     // 排产之后自己等它出来
    }
    const res = await getVideoRelated({
      knowledge_key: key, subject: videoSubject.value, limit: 8,
    })
    const { hits, related } = splitByMatch(res?.items)
    st.hits = hits
    st.related = related
  } catch (e) {
    console.warn('视频库检索失败:', e)
    st.hits = []; st.related = []
  } finally {
    st.loading = false
  }
}

/** 当日视频任务一进页面就各查一次（并行，不阻塞） */
function loadPlanVideos() {
  dayVideos.value.forEach(v => loadPlanVideo(v))
}

function playPlanVideo(task, video) { playing.value = { task, video } }

/**
 * 播完 → 标完成 → 回计划详情。
 * 播放器传的是 `:seekable="false"`，所以「播完」意味着**真的看完了** ——
 * 能拖进度的话这个信号就不成立（用户定调：计划里的视频不能拉进度）。
 */
async function onVideoEnded() {
  const t = playing.value?.task
  playing.value = null
  if (!t) return
  try {
    await updateTaskStatus({
      task_id: t.id, status: 'completed', plan_id: plan.value?.id || route.params.id,
    })
    ElMessage.success('视频看完了，已标记完成')
    await loadData()
  } catch (e) {
    console.warn('标记视频完成失败:', e)
    ElMessage.warning('看完了，但完成状态没存上，刷新后再试')
  }
}

// 切到别的日子也要给它那天的视频查一次（结果按任务 id 缓存，重复切不会重复请求）
watch(selectedDate, () => loadPlanVideos())

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
    loadPlanVideos()   // 给当天的视频任务各查一次视频库（并行、不阻塞）
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
  height: calc(100vh - var(--jz-top, 0px));
  overflow-y: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 30px 20px;
  }

.detail-container {
  max-width: 960px;
  width: 100%;
  padding: 28px 36px;
  border-radius: 20px;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.06);
  box-shadow: 0 8px 48px rgba(0,0,0,0.08);
}
[data-theme="dark"] .detail-container {
  background: var(--well);
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
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  color: var(--brand);
}
.status-badge[data-status="pending"] {
  background: rgba(245,158,11,0.10);
  color: color-mix(in srgb, #F59E0B 70%, var(--text-primary));
}
/* ===== 2026-10-01 新增：当日最佳率 / 学习内容折叠 / 重做 ===== */
.day-acc { margin-left: 14px; font-size: 13px; color: var(--text-muted); }
.day-acc b { color: var(--brand-bright); font-size: 15px; }
.day-acc-sub { font-size: 11.5px; opacity: .8; }

.content-item.clickable { cursor: pointer; transition: border-color .2s ease, transform .2s ease; }
.content-item.clickable:hover { border-color: var(--brand); transform: translateX(3px); }
.content-more { float: right; font-size: 11.5px; font-weight: 400; color: var(--brand-bright); }

/* 列表里只露两行 —— 完整正文点进学习页再看 */
.clamp2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.q-attempts { font-size: 11px; opacity: .75; }

/* ===== 学习视频（2026-10-01 接视频库）===== */
.video-head { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.video-done { font-size: 11.5px; color: #67c23a; }
.video-tip { font-size: 12.5px; color: var(--text-muted); display: flex; align-items: center;
  gap: 10px; flex-wrap: wrap; }
.video-tip.sub { margin-top: 6px; font-size: 11.5px; color: var(--brand-bright); }
.video-gen { padding: 4px 12px; border-radius: 999px; font-size: 12px; font-family: inherit;
  color: var(--brand-bright); cursor: pointer;
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand) 28%, transparent); }
.video-pick { display: flex; align-items: center; gap: 10px; width: 100%;
  padding: 8px 12px; margin-bottom: 6px; border-radius: 10px; text-align: left;
  font-family: inherit; font-size: 13px; color: var(--text-primary); cursor: pointer;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid var(--line-soft); transition: border-color .2s ease; }
.video-pick:hover { border-color: var(--brand); }
.video-pick-t { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.video-pick-m { font-size: 11.5px; color: var(--text-muted); }
.video-pick-go { font-size: 12px; font-weight: 700; color: var(--brand-bright); }
.video-note { margin: 12px 0 0; font-size: 12px; color: var(--text-muted); text-align: center; }
/* 同学科推荐：默认折叠，标题自带「不是本知识点」的说明 */
.video-related { margin-top: 10px; }
.video-related summary { font-size: 12px; color: var(--text-muted); cursor: pointer; padding: 4px 0; }
.video-related .video-pick { margin-top: 6px; opacity: .85; }
.video-more { align-self: center; margin-top: 2px; padding: 4px 14px; border-radius: 999px;
  font-size: 11.5px; font-weight: 600; color: var(--brand-bright); cursor: pointer; text-align: center;
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand) 22%, transparent); }

.status-badge[data-status="completed"] {
  background: rgba(34,197,94,0.10);
  color: color-mix(in srgb, #22C55E 65%, var(--text-primary));
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
.glass-btn:active { transform: scale(0.97); }
.glass-btn.primary {
  color: var(--brand);
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  border-color: color-mix(in srgb, var(--brand) 10%, transparent);
}
.glass-btn.primary:hover {
  background: color-mix(in srgb, var(--brand) 14%, transparent);
  border-color: color-mix(in srgb, var(--brand) 20%, transparent);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  overflow: hidden;
}
.overview-progress .progress-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, var(--brand), #8B5CF6);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
  border: 1px solid rgba(255,255,255,0.04);
}
.date-item:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
}
.date-item.active {
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  border-color: color-mix(in srgb, var(--brand) 20%, transparent);
}
.date-item.completed .date-num { color: color-mix(in srgb, #22C55E 65%, var(--text-primary)); }
.date-item.in_progress .date-num { color: var(--brand); }
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
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
}
.question-row:last-child { border-bottom: none; }
.q-idx { font-weight: 600; color: var(--text-muted); }
.q-topic { color: var(--text-primary); }
.q-type { font-size: 12px; }
.q-difficulty { font-size: 12px; font-weight: 500; }
.q-status { font-size: 12px; }
.q-status[data-status="completed"] { color: color-mix(in srgb, #22C55E 65%, var(--text-primary)); }
.q-status[data-status="active"] { color: var(--brand); }
.q-status[data-status="pending"] { color: var(--text-muted); }
.q-action { display: flex; justify-content: center; }

.video-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 14px;
  border-radius: 8px;
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
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