<!--
  每日学习推荐 · 学习页（2026-10-08）

  一条 `learning.daily_rec` 消息 = 一套可直接执行的任务：
  ① 学习内容 ② 题目 ③ 讲解视频。

  **首页「小基推荐」卡片和消息中心那条进的都是这里**（用户 2026-10-08 拍板：
  独立全屏页，不是弹层）—— 所以进度判定只此一份，两边不各写一套。

  路由 `/daily-learn/:id?`：带 id 看指定那条；不带就取最新一条
  （`notify()` 是先 INSERT 才拿得到 row id，link 在插入时就得定，
  所以卡片跳的是不带 id 的那个）。

  规格见 project1/message_center_design.md §六。
-->
<template>
  <div class="dl-page">
    <div class="dl-wrap">
      <!-- ===== 头部 ===== -->
      <header class="dl-head">
        <button class="dl-back" @click="goBack" title="返回">
          <i class="fas fa-arrow-left"></i>
        </button>
        <div class="dl-head-main">
          <h1>{{ title }}</h1>
          <p v-if="basis" class="dl-basis">{{ basis }}</p>
        </div>
        <div class="dl-dots" v-if="rec">
          <span v-for="b in BLOCKS" :key="b.key"
                class="dl-dot" :class="{ done: prog[b.key] }"
                :title="b.label + (prog[b.key] ? '（已完成）' : '')">
            {{ prog[b.key] ? '✓' : b.no }}
          </span>
        </div>
      </header>

      <div v-if="loading" class="dl-empty">加载中…</div>

      <div v-else-if="!rec" class="dl-empty">
        今天还没有学习推荐～<br />
        去做几道题，小基明天给你定制
      </div>

      <template v-else>
        <!-- ===== ① 学习内容 ===== -->
        <section class="dl-block" :class="{ done: prog.content, open: open.content }">
          <button class="dl-block-head" @click="toggle('content')">
            <span class="dl-no">①</span>
            <span class="dl-label">学习内容</span>
            <span class="dl-sub">约 {{ recMinutes }} 分钟</span>
            <span class="dl-state">{{ prog.content ? '已读' : (open.content ? '收起' : '展开') }}</span>
          </button>
          <div v-show="open.content" class="dl-body">
            <div v-if="contentLoading" class="dl-hint">
              正在生成正文…（首次打开要几秒，之后会缓存）
            </div>
            <template v-else-if="lesson && lesson.sections">
              <p v-if="lesson.summary" class="dl-summary">{{ lesson.summary }}</p>
              <div v-for="(s, i) in lesson.sections" :key="i" class="dl-sec">
                <h3>{{ s.heading }}</h3>
                <p v-for="(para, j) in paras(s.body)" :key="j">{{ para }}</p>
                <div v-if="s.example" class="dl-eg"><b>例</b><span>{{ s.example }}</span></div>
              </div>
              <div v-if="(lesson.common_mistakes || []).length" class="dl-mistakes">
                <h4>常见错误</h4>
                <p v-for="(m, i) in lesson.common_mistakes" :key="i">· {{ m }}</p>
              </div>
              <button v-if="!prog.content" class="dl-btn primary" @click="mark('content')">
                读完了
              </button>
            </template>
            <div v-else class="dl-hint">还没有正文</div>
          </div>
        </section>

        <!-- ===== ② 练习 ===== -->
        <section class="dl-block" :class="{ done: prog.questions, open: open.questions }">
          <button class="dl-block-head" @click="toggle('questions')">
            <span class="dl-no">②</span>
            <span class="dl-label">练习</span>
            <span class="dl-sub">{{ qCount }} 题</span>
            <span class="dl-state">{{ prog.questions ? '已完成' : (open.questions ? '收起' : '开始') }}</span>
          </button>
          <div v-show="open.questions" class="dl-body">
            <div v-if="qLoading" class="dl-hint">正在取题面…</div>
            <template v-else-if="questions.length">
              <div v-for="(q, i) in questions" :key="q.qid || i" class="dl-q">
                <div class="dl-q-head">
                  <span class="dl-q-no">{{ i + 1 }}</span>
                  <span class="dl-q-type">{{ typeLabel(q.question_type) }}</span>
                  <span v-if="q._fb" class="dl-q-ok" :class="{ bad: !q._fb.is_correct }">
                    {{ q._fb.is_correct ? '✓ 正确' : '✗ 错误' }}
                  </span>
                </div>

                <div v-if="q.missing" class="dl-hint">这道题暂时取不到题面</div>
                <template v-else>
                  <div class="dl-q-stem">{{ getStem(q) }}</div>

                  <!-- 单选 -->
                  <div v-if="isSingleChoice(q.question_type)" class="dl-opts">
                    <button v-for="(o, oi) in getOptions(q)" :key="oi"
                            class="dl-opt" :class="{ sel: q._pick === letters[oi] }"
                            :disabled="!!q._fb" @click="q._pick = letters[oi]">
                      <span class="dl-opt-l">{{ letters[oi] }}</span>{{ strip(o) }}
                    </button>
                  </div>

                  <!-- 多选 -->
                  <div v-else-if="isMultiChoice(q.question_type)" class="dl-opts">
                    <button v-for="(o, oi) in getOptions(q)" :key="oi"
                            class="dl-opt" :class="{ sel: (q._pick || []).includes(letters[oi]) }"
                            :disabled="!!q._fb" @click="toggleMulti(q, letters[oi])">
                      <span class="dl-opt-l">{{ letters[oi] }}</span>{{ strip(o) }}
                    </button>
                  </div>

                  <!-- 其它（填空/简答/翻译…） -->
                  <textarea v-else v-model="q._pick" class="dl-text" rows="3"
                            :disabled="!!q._fb"
                            :placeholder="longTextPlaceholder(q.question_type)" />

                  <div v-if="q._fb" class="dl-fb" :class="{ bad: !q._fb.is_correct }">
                    <div>{{ q._fb.is_correct ? '答对了' : '答错了' }}
                      <template v-if="q._fb.correct_answer">　正确答案：{{ q._fb.correct_answer }}</template>
                    </div>
                    <div v-if="q._fb.explanation" class="dl-fb-exp">{{ q._fb.explanation }}</div>
                    <div v-else-if="q._fb.ai_feedback" class="dl-fb-exp">{{ q._fb.ai_feedback }}</div>
                  </div>
                  <button v-else class="dl-btn primary" :disabled="submitting === i"
                          @click="submitOne(q, i)">
                    {{ submitting === i ? '提交中…' : '提交' }}
                  </button>
                </template>
              </div>

              <div class="dl-hint">
                作答会写入你的做题记录与错题本，和计划里的练习进同一个数据底座
              </div>
            </template>
            <div v-else class="dl-hint">这次的推荐没有配题目</div>
          </div>
        </section>

        <!-- ===== ③ 讲解视频 ===== -->
        <section class="dl-block" :class="{ done: prog.video, open: open.video }">
          <button class="dl-block-head" @click="toggle('video')">
            <span class="dl-no">③</span>
            <span class="dl-label">讲解视频</span>
            <span class="dl-sub">{{ video ? (video.duration || '') : '这个知识点还没有现成的视频' }}</span>
            <span class="dl-state" v-if="video">{{ prog.video ? '已看完' : (open.video ? '收起' : '播放') }}</span>
          </button>
          <div v-show="open.video && video" class="dl-body">
            <div v-if="videoLoading" class="dl-hint">正在取视频…</div>
            <template v-else-if="videoRow">
              <!-- ⚠️ seekable=false：和计划里的视频同一条规矩 ——
                   「播完 = 学完」要成立，就不能让人拖到底 -->
              <VideoLessonPlayer :video="videoRow" :seekable="false" @ended="mark('video')" />
              <div class="dl-hint">{{ video.title }}</div>
            </template>
            <div v-else class="dl-hint">视频暂时取不到（可能已被下架）</div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  getLatestRec, getRec, getRecQuestions, getRecContent, setRecProgress,
} from '@/api/dailyLearn'
import { submitPractice } from '@/api/subjectPlan'
import { getVideoDetail } from '@/api/video'
import { recordAction } from '@/api/career'
import VideoLessonPlayer from '@/components/VideoLessonPlayer.vue'
import {
  typeLabel, isSingleChoice, isMultiChoice, longTextPlaceholder, getStem, getOptions,
} from '@/utils/questionLabels'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const BLOCKS = [
  { key: 'content', no: '①', label: '学习内容' },
  { key: 'questions', no: '②', label: '练习' },
  { key: 'video', no: '③', label: '讲解视频' },
]
const letters = ['A', 'B', 'C', 'D', 'E', 'F']

const loading = ref(true)
const rec = ref(null)
const prog = reactive({ content: false, questions: false, video: false })
const open = reactive({ content: false, questions: false, video: false })

const lesson = ref(null)
const contentLoading = ref(false)
const questions = ref([])
const qLoading = ref(false)
const submitting = ref(null)
const videoRow = ref(null)
const videoLoading = ref(false)

const title = computed(() => rec.value?.payload?.content?.title || rec.value?.title || '今日学习推荐')
const basis = computed(() => rec.value?.payload?.content?.basis || '')
const recMinutes = computed(() => rec.value?.payload?.content?.minutes || 0)
const video = computed(() => rec.value?.payload?.video || null)
const qCount = computed(() => (rec.value?.payload?.questions || []).length)

function strip(o) { return String(o || '').replace(/^[A-F][.\s、]+/, '') }
function paras(body) { return String(body || '').split(/\n+/).map(s => s.trim()).filter(Boolean) }

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/home')
}

// ===== 取数据 =====
async function load() {
  loading.value = true
  try {
    const uid = authStore.user?.id
    const id = route.params.id
    rec.value = id ? await getRec(id, uid) : await getLatestRec(uid)
    if (rec.value) {
      const p = rec.value.payload?.progress || {}
      BLOCKS.forEach(b => { prog[b.key] = !!p[b.key] })
      // 正文若已生成过，payload 里就有 sections，直接显示不再烧一次
      const c = rec.value.payload?.content
      if (c && c.sections) lesson.value = c
      // 自动展开第一个还没做的块，省一次点击
      const next = BLOCKS.find(b => !prog[b.key])
      if (next) open[next.key] = true
    }
  } catch (e) {
    if (e?.response?.status !== 404) ElMessage.error('读取推荐失败')
    rec.value = null
  } finally {
    loading.value = false
  }
}

function toggle(key) {
  open[key] = !open[key]
  if (!open[key]) return
  if (key === 'content') ensureContent()
  if (key === 'questions') ensureQuestions()
  if (key === 'video') ensureVideo()
}

// ===== ① 正文：按需生成，后端幂等 =====
async function ensureContent() {
  if (lesson.value?.sections || contentLoading.value || !rec.value) return
  contentLoading.value = true
  try {
    const res = await getRecContent(rec.value.id, authStore.user.id)
    lesson.value = res.lesson
  } catch (e) {
    ElMessage.error('正文生成失败，请稍后重试')
  } finally {
    contentLoading.value = false
  }
}

// ===== ② 题目 =====
async function ensureQuestions() {
  if (questions.value.length || qLoading.value || !rec.value) return
  qLoading.value = true
  try {
    const res = await getRecQuestions(rec.value.id, authStore.user.id)
    questions.value = (res.questions || []).map(q => ({
      ...q,
      _pick: isMultiChoice(q.question_type) ? [] : '',
      _fb: null,
    }))
  } catch (e) {
    ElMessage.error('取题面失败，请稍后重试')
  } finally {
    qLoading.value = false
  }
}

function toggleMulti(q, letter) {
  const arr = q._pick || []
  const i = arr.indexOf(letter)
  if (i >= 0) arr.splice(i, 1)
  else arr.push(letter)
  q._pick = [...arr].sort()
}

async function submitOne(q, idx) {
  const ans = q._pick
  if (ans === '' || ans === null || (Array.isArray(ans) && !ans.length)) {
    ElMessage.warning('先作答再提交')
    return
  }
  submitting.value = idx
  try {
    const res = await submitPractice({
      user_id: authStore.user.id,
      plan_id: '',                    // ⚠️ 每日推荐**不挂在任何计划上**
      question_id: q.qid || q.id,
      // ⚠️ 必须带：题库 497 个 id 横跨多库，后端靠它定位题目，
      //    不带就会跨库猜 —— 拿 A 科目的题判 B 科目的分
      syllabus_id: q.syllabus_id || '',
      user_answer: ans,
      source: 'daily_rec',
      time_spent: 0,
    })
    q._fb = res
    recordAction(authStore.user.id, 'complete_question')
    // 全部答完 → 这一块算完成
    if (questions.value.every(x => x._fb || x.missing)) await mark('questions')
  } catch (e) {
    ElMessage.error('提交失败，请重试')
  } finally {
    submitting.value = null
  }
}

// ===== ③ 视频 =====
async function ensureVideo() {
  if (videoRow.value || videoLoading.value) return
  const v = video.value
  if (!v?.video_id) return
  videoLoading.value = true
  try {
    // ⚠️ payload 里只有 video_id / 标题 / 时长，**没有 audio_url** ——
    //    播放器要的是整行 video_library，所以这里必须补拉一次
    const res = await getVideoDetail(v.video_id)
    videoRow.value = res?.video || null
  } catch (e) {
    videoRow.value = null
  } finally {
    videoLoading.value = false
  }
}

// ===== 进度 =====
async function mark(block) {
  if (!rec.value || prog[block]) return
  try {
    const res = await setRecProgress(rec.value.id, authStore.user.id, block)
    prog[block] = true
    if (res?.all_done) ElMessage.success('今天的三块都完成了 🎉')
  } catch (e) {
    ElMessage.error('进度保存失败，请重试')
  }
}

onMounted(load)
// 从消息中心点另一条推荐进来时重新加载
watch(() => route.params.id, () => { if (route.name === 'DailyLearn') resetAndLoad() })

function resetAndLoad() {
  rec.value = null; lesson.value = null; questions.value = []
  videoRow.value = null
  BLOCKS.forEach(b => { prog[b.key] = false; open[b.key] = false })
  load()
}
</script>

<style scoped>
.dl-page {
  height: calc(100vh - var(--jz-top, 0px));
  overflow-y: auto;
  padding: 28px 20px 80px;
}
.dl-wrap { max-width: 860px; margin: 0 auto; }

/* ===== 头部 ===== */
.dl-head { display: flex; align-items: flex-start; gap: 14px; margin-bottom: 22px; }
.dl-back {
  flex: none; width: 34px; height: 34px; border-radius: 10px; cursor: pointer;
  border: 1px solid var(--border, rgba(0,0,0,.1));
  background: color-mix(in srgb, var(--surface, #fff) 70%, transparent);
  color: var(--text-secondary); transition: all .2s ease;
}
.dl-back:hover { color: var(--text-primary); transform: translateX(-2px); }
.dl-head-main { flex: 1; min-width: 0; }
.dl-head-main h1 { margin: 0; font-size: 22px; color: var(--text-primary); }
.dl-basis { margin: 6px 0 0; font-size: 13px; color: var(--text-muted); }

.dl-dots { display: flex; gap: 8px; flex: none; padding-top: 4px; }
.dl-dot {
  width: 26px; height: 26px; border-radius: 50%; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid var(--border, rgba(0,0,0,.12));
  color: var(--text-muted);
}
.dl-dot.done { background: #67C23A; border-color: #67C23A; color: #fff; }

.dl-empty {
  padding: 70px 20px; text-align: center; line-height: 1.9;
  color: var(--text-muted); font-size: 14px;
}

/* ===== 三块 ===== */
.dl-block {
  margin-bottom: 14px; border-radius: 16px; overflow: hidden;
  border: 1px solid var(--border, rgba(0,0,0,.1));
  background: color-mix(in srgb, var(--surface, #fff) 72%, transparent);
  backdrop-filter: blur(20px) saturate(1.4);
}
.dl-block.done { border-color: color-mix(in srgb, #67C23A 45%, transparent); }
.dl-block-head {
  width: 100%; display: flex; align-items: center; gap: 12px;
  padding: 16px 18px; cursor: pointer; font: inherit; text-align: left;
  background: transparent; border: none; color: var(--text-primary);
}
.dl-no { font-size: 16px; color: var(--text-secondary); }
.dl-label { font-size: 15px; font-weight: 600; }
.dl-sub { flex: 1; font-size: 12px; color: var(--text-muted); }
.dl-state { font-size: 12px; color: var(--brand, #3B82F6); }
.dl-block.done .dl-state { color: #67C23A; }

.dl-body { padding: 0 18px 18px; }

/* ===== 正文 ===== */
.dl-summary { margin: 0 0 14px; font-size: 14px; color: var(--text-secondary); }
.dl-sec { margin-bottom: 18px; }
.dl-sec h3 { margin: 0 0 8px; font-size: 15px; color: var(--text-primary); }
.dl-sec p { margin: 0 0 8px; font-size: 14px; line-height: 1.85; color: var(--text-secondary); }
.dl-eg {
  display: flex; gap: 10px; padding: 10px 12px; border-radius: 10px;
  background: color-mix(in srgb, var(--brand, #3B82F6) 7%, transparent);
  font-size: 13px; line-height: 1.8; color: var(--text-secondary);
}
.dl-eg b { flex: none; color: var(--brand, #3B82F6); }
.dl-mistakes { margin-top: 6px; font-size: 13px; color: var(--text-secondary); }
.dl-mistakes h4 { margin: 0 0 6px; font-size: 13px; color: #F56C6C; }

/* ===== 题目 ===== */
.dl-q { padding: 14px 0; border-top: 1px solid var(--border, rgba(0,0,0,.07)); }
.dl-q:first-child { border-top: none; }
.dl-q-head { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.dl-q-no {
  width: 20px; height: 20px; border-radius: 6px; font-size: 11px;
  display: flex; align-items: center; justify-content: center;
  background: color-mix(in srgb, var(--brand, #3B82F6) 14%, transparent);
  color: var(--brand, #3B82F6);
}
.dl-q-type { font-size: 11px; color: var(--text-muted); }
.dl-q-ok { margin-left: auto; font-size: 12px; color: #67C23A; }
.dl-q-ok.bad { color: #F56C6C; }
.dl-q-stem { margin-bottom: 12px; font-size: 14px; line-height: 1.8; color: var(--text-primary); }

.dl-opts { display: flex; flex-direction: column; gap: 8px; }
.dl-opt {
  display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px;
  border-radius: 10px; cursor: pointer; font: inherit; text-align: left; font-size: 13.5px;
  border: 1px solid var(--border, rgba(0,0,0,.1));
  background: transparent; color: var(--text-secondary);
  transition: all .16s ease;
}
.dl-opt:hover:not(:disabled) { border-color: var(--brand, #3B82F6); }
.dl-opt.sel {
  border-color: var(--brand, #3B82F6);
  background: color-mix(in srgb, var(--brand, #3B82F6) 10%, transparent);
  color: var(--text-primary);
}
.dl-opt:disabled { cursor: default; opacity: .85; }
.dl-opt-l { flex: none; font-weight: 700; color: var(--brand, #3B82F6); }

.dl-text {
  width: 100%; box-sizing: border-box; padding: 10px 12px; border-radius: 10px;
  border: 1px solid var(--border, rgba(0,0,0,.1)); font: inherit; font-size: 13.5px;
  background: transparent; color: var(--text-primary); resize: vertical;
}

.dl-fb {
  margin-top: 10px; padding: 10px 12px; border-radius: 10px; font-size: 13px;
  background: color-mix(in srgb, #67C23A 10%, transparent); color: var(--text-secondary);
}
.dl-fb.bad { background: color-mix(in srgb, #F56C6C 10%, transparent); }
.dl-fb-exp { margin-top: 6px; line-height: 1.8; opacity: .9; }

/* ===== 通用 ===== */
.dl-btn {
  margin-top: 12px; padding: 9px 20px; border-radius: 10px; cursor: pointer;
  font: inherit; font-size: 13.5px;
  border: 1px solid var(--border, rgba(0,0,0,.12));
  background: transparent; color: var(--text-primary);
}
.dl-btn.primary {
  border-color: transparent; background: var(--brand, #3B82F6); color: #fff;
}
.dl-btn:disabled { opacity: .6; cursor: default; }
.dl-hint { margin-top: 10px; font-size: 12.5px; line-height: 1.8; color: var(--text-muted); }
</style>
