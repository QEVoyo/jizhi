<template>
  <div v-if="!hidden" class="xj-page-host" :class="{ capturing }" :style="hostStyle">
    <Transition name="xj-bubble">
      <div v-if="open" class="xj-bubble"
           :class="{ below: bubbleBelow, 'align-left': bubbleLeft }">
        <div class="xj-bubble-head">
          <span class="xj-bubble-title">{{ bubbleTitle }}</span>
          <button v-if="mode !== 'menu'" class="xj-back" @click="mode = 'menu'">←</button>
        </div>

        <template v-if="mode === 'menu'">
          <p class="xj-hint">{{ profile.bubble }}</p>

          <!-- 这一页专属的快捷动作（学程：快完成 / 可领取；社区：私信；资源库：出题…） -->
          <div v-if="pageActions.length" class="xj-page-actions">
            <span class="xj-section-label">针对这页</span>
            <button
              v-for="a in pageActions"
              :key="a.label"
              :disabled="actionBusy"
              @click="a.run"
            >{{ a.icon }} {{ a.label }}</button>
          </div>

          <p v-if="actionBusy" class="xj-loading">小基正在处理…</p>

          <span class="xj-section-label">通用</span>
          <div class="xj-actions">
            <button @click="summarize">📋 总结本页</button>
            <button @click="openOverview">📊 今日概览</button>
            <button @click="captureScreen">🖥 截图解析</button>
            <button @click="search">🔎 全局搜索</button>
            <button @click="upload">📄 传资料出题</button>
            <button @click="home">💬 找小基聊聊</button>
            <button class="ghost" @click="hide">👋 先躲起来</button>
          </div>
        </template>

        <template v-else-if="mode === 'action'">
          <p class="xj-summary">{{ actionText }}</p>
          <div class="xj-actions tight">
            <button v-if="actionLink" @click="goActionLink">去看看</button>
            <button v-if="isCareerPage" :disabled="actionBusy" @click="claimReadyTasks">再领一次</button>
            <button class="ghost" @click="mode = 'menu'">收起</button>
          </div>
        </template>

        <template v-else-if="mode === 'loading'">
          <p class="xj-loading">小基正在看这一页…</p>
        </template>

        <template v-else-if="mode === 'imageLoading'">
          <p class="xj-loading">小基正在看这张图…</p>
        </template>

        <template v-else-if="mode === 'imageResult'">
          <img v-if="imagePreview" :src="imagePreview" class="xj-img-preview" alt="截图" />
          <p class="xj-summary">{{ imageAnalysis }}</p>
          <div class="xj-actions tight">
            <button @click="captureScreen">重新截图</button>
            <button class="ghost" @click="mode = 'menu'">收起</button>
          </div>
        </template>

        <template v-else-if="mode === 'summary'">
          <p class="xj-summary">{{ summary }}</p>
          <div class="xj-actions tight">
            <button @click="summarize">重新总结</button>
            <button :disabled="busy" @click="preciseSummary">让小基细说</button>
            <button class="ghost" @click="mode = 'menu'">收起</button>
          </div>
        </template>

        <template v-else-if="mode === 'overview'">
          <div class="xj-overview">
            <div class="xj-ov-item"><b>{{ overview.studyDays }}</b><span>近7天学习(天)</span></div>
            <div class="xj-ov-item"><b>{{ overview.weekQuestions }}</b><span>本周做题</span></div>
          </div>
          <p v-if="overview.rec" class="xj-rec">{{ overview.rec }}</p>
          <p v-else class="xj-rec">还没有推荐，去主页看看？</p>
          <div class="xj-actions tight">
            <button @click="home">去主页</button>
            <button class="ghost" @click="mode = 'menu'">收起</button>
          </div>
        </template>

        <p v-if="error" class="xj-error">{{ error }}</p>
      </div>
    </Transition>

    <button class="xj-avatar-btn" :class="{ dragging }" :data-look="displayLook"
            title="小基在页面里（可以拖动）"
            @pointerdown="onPointerDown"
            @pointermove="onPointerMove"
            @pointerup="onPointerUp"
            @pointercancel="onPointerUp">
      <img :src="lookImgUrl" :class="{ static: lookFallback }"
           alt="小基" draggable="false" @load="onLookLoad" @error="onLookError" />
    </button>

    <input ref="imageInput" type="file" accept="image/*" class="xj-hidden-input"
           @change="onImagePick" />

    <!-- 框选区域截图：先截当前页面，再拖拽选择区域 -->
    <ScreenshotCropper :open="cropOpen" :image-url="cropUrl"
                       @confirm="onCropConfirm" @cancel="onCropCancel" />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNavStore } from '@/stores/nav'
import { getXiaojiDaily } from '@/api/xiaoji'
import { getTaskProgress, claimCareerTask } from '@/api/career'
import { summarizePage, analyzeImage } from '@/api/agents'
import { localOverview, pageLightContext } from '@/xiaoji/pageFrameworks'
import { openXiaojiPopup } from '@/xiaoji/popupStore'
import ScreenshotCropper from '@/components/ScreenshotCropper.vue'

const props = defineProps({
  routePath: { type: String, default: '' },
})

const router = useRouter()
const authStore = useAuthStore()
const navStore = useNavStore()

const AVATAR_W = 92
const AVATAR_H = 122
const MARGIN = 8
const POS_KEY = 'xiaoji_page_pos'

const open = ref(false)
const hidden = ref(false)
const mode = ref('menu')          // menu / loading / summary / overview / action
const summary = ref('')
const overview = ref({ studyDays: 0, weekQuestions: 0, rec: '' })
const error = ref('')
const busy = ref(false)
const actionBusy = ref(false)
const actionText = ref('')
const actionLink = ref('')
const imageInput = ref(null)
const imagePreview = ref('')
const imageAnalysis = ref('')
const cropOpen = ref(false)
const cropUrl = ref('')
const capturing = ref(false)

const WEBP_MAP = {
  idle: '/xiaoji/xiaoji_idle_loop.webp',
  thinking: '/xiaoji/xiaoji_thinking_loop.webp',
  speaking: '/xiaoji/xiaoji_speaking_loop.webp',
  happy: '/xiaoji/xiaoji_happy_loop.webp',
  sleeping: '/xiaoji/xiaoji_sleeping_loop.webp',
}
const STATIC_LOOKS = {
  idle: '/images/xiaoji/xiaoji_idle-full.png',
  thinking: '/images/xiaoji/xiaoji_thinking.png',
  speaking: '/images/xiaoji/xiaoji_speaking.png',
  happy: '/images/xiaoji/xiaoji_happy-full.png',
  sleeping: '/images/xiaoji/xiaoji_sleeping.png',
}
const look = ref('idle')
const idleLook = ref('')
const lookFallback = ref(false)
const lookBust = ref(0)
const displayLook = computed(() =>
  look.value !== 'idle' ? look.value : (idleLook.value || 'idle'))
const lookUrl = computed(() => STATIC_LOOKS[displayLook.value] || STATIC_LOOKS.idle)
const lookWebpUrl = computed(() => WEBP_MAP[displayLook.value] || WEBP_MAP.idle)
const lookImgUrl = computed(() => lookFallback.value
  ? lookUrl.value
  : lookWebpUrl.value + (lookBust.value ? `?v=${lookBust.value}` : ''))
let lookTimer = null
let idleTimer = null
let idleActionTimer = null

let lookRetried = false

function setLook(name, revertMs = 0) {
  look.value = WEBP_MAP[name] ? name : 'idle'
  lookFallback.value = false
  lookRetried = false
  if (lookTimer) clearTimeout(lookTimer)
  if (revertMs) {
    lookTimer = setTimeout(() => { look.value = 'idle' }, revertMs)
  }
}

function onLookLoad() {
  lookRetried = false
  lookFallback.value = false
}

function onLookError() {
  // WebP 失败先补一次 cache-bust 重试（常见于 dev server 刚换文件），
  // 仍失败才回落静态 PNG；静态 PNG 由 CSS 继续做循环呼吸。
  if (!lookRetried) {
    lookRetried = true
    lookBust.value = Date.now()
    lookFallback.value = false
    return
  }
  lookFallback.value = true
}

function scheduleIdleAction() {
  if (idleTimer) clearTimeout(idleTimer)
  idleTimer = setTimeout(() => {
    if (look.value !== 'idle' || hidden.value) {
      scheduleIdleAction()
      return
    }
    const pool = ['happy', 'thinking', 'sleeping']
    const pick = pool[Math.floor(Math.random() * pool.length)]
    idleLook.value = pick
    const dur = pick === 'happy' ? 2000 : (pick === 'thinking' ? 3000 : 3500)
    idleActionTimer = setTimeout(() => {
      idleLook.value = ''
      scheduleIdleAction()
    }, dur)
  }, 7000 + Math.random() * 7000)
}

function startIdleActions() {
  if (idleTimer || idleActionTimer) return
  scheduleIdleAction()
}

function stopIdleActions() {
  if (idleTimer) clearTimeout(idleTimer)
  if (idleActionTimer) clearTimeout(idleActionTimer)
  idleTimer = null
  idleActionTimer = null
  idleLook.value = ''
}
const pos = ref({ x: 0, y: 0 })
const dragging = ref(false)
const moved = ref(false)

let dragStart = null

const PAGE_PROFILES = [
  { match: /\/do-question|\/subject-plan\/.+\/practice/, bubble: '卡住了？做完这题我帮你看错因。' },
  { match: /\/subject-plan\/.+\/exam\//, bubble: '计时中，我先安静；交卷后帮你复盘。' },
  { match: /\/mastery-board/, bubble: '薄弱点我帮你盯着，别只刷会的。' },
  { match: /\/resource-lib|\/set-detail/, bubble: '传份资料，我给你出题；题集也能直接练。' },
  { match: /\/evaluation-report|\/evaluation-center/, bubble: '报告里看不懂的地方，问我。' },
  { match: /\/learning-plan|\/plan-detail|\/plan-preview/, bubble: '计划落后了？我帮你把任务量调小一点。' },
]

const profile = computed(() =>
  PAGE_PROFILES.find(p => p.match.test(props.routePath || '')) || {
    bubble: '需要我帮忙吗？我可以总结这页、看今日概览，或者陪你聊聊。',
  })

const isCareerPage = computed(() => /^\/career(\/|$)/.test(props.routePath || ''))

// ===== 每页专属动作 =====
// 只放「这一页真的有东西可做」的按钮；没有专属动作的页面不显示这一栏。
const pageActions = computed(() => {
  const p = props.routePath || ''
  if (isCareerPage.value) return [
    { icon: '⚡', label: '快完成任务', run: showNearDoneTasks },
    { icon: '🎁', label: '可领取任务', run: claimReadyTasks },
    { icon: '🏆', label: '看好友排行', run: () => go('/career/rank') },
  ]
  if (/^\/(?:subject-plan\/.+\/practice|do-question)/.test(p)) return [
    { icon: '✅', label: '今日任务', run: () => go('/learning-plan') },
    { icon: '🎯', label: '看薄弱点', run: () => go('/mastery-board') },
    { icon: '💬', label: '问小基', run: () => go('/home') },
  ]
  if (/^\/(?:resource-lib|set-detail)/.test(p)) return [
    { icon: '🎯', label: '薄弱点出题', run: () => go('/generate-from-mastery') },
    { icon: '📄', label: '传资料出题', run: upload },
    { icon: '📊', label: '掌握度看板', run: () => go('/mastery-board') },
  ]
  if (/^\/evaluation-/.test(p)) return [
    { icon: '📋', label: '生成新计划', run: () => go('/generate-from-mastery') },
    { icon: '🧮', label: '评估表', run: () => go('/evaluation-table') },
    { icon: '🎯', label: '薄弱点', run: () => go('/mastery-board') },
  ]
  if (/^\/(?:learning-plan|plan-detail|plan-preview|daily-learn)/.test(p)) return [
    { icon: '✅', label: '今日任务', run: () => go('/learning-plan') },
    { icon: '📊', label: '掌握度', run: () => go('/mastery-board') },
    { icon: '📈', label: '评估报告', run: () => go('/evaluation-report') },
  ]
  if (/^\/community/.test(p)) return [
    { icon: '🏠', label: '动态广场', run: () => go('/community') },
    { icon: '💬', label: '好友私信', run: () => go('/community/friends') },
    { icon: '🔔', label: '消息中心', run: () => go('/message') },
  ]
  if (/^\/mastery-board/.test(p)) return [
    { icon: '🎯', label: '薄弱点出题', run: () => go('/generate-from-mastery') },
    { icon: '📚', label: '回资源库', run: () => go('/resource-lib') },
  ]
  if (/^\/(?:video-square|video\/)/.test(p)) return [
    { icon: '🎬', label: '视频广场', run: () => go('/video-square') },
    { icon: '💬', label: '问小基', run: () => go('/home') },
  ]
  if (/^\/message/.test(p)) return [
    { icon: '👥', label: '好友私信', run: () => go('/community/friends') },
    { icon: '🏠', label: '回首页', run: () => go('/home') },
  ]
  if (/^\/(?:profile-card|agent-center)/.test(p)) return [
    { icon: '🎯', label: '看掌握度', run: () => go('/mastery-board') },
    { icon: '🏠', label: '回首页', run: () => go('/home') },
  ]
  return []
})

const bubbleTitle = computed(() => ({
  menu: '小基',
  loading: '正在总结',
  summary: '本页总结',
  overview: '今日概览',
  imageLoading: '正在识图',
  imageResult: '截图解析',
  action: '小基办好了',
}[mode.value] || '小基'))

const hostStyle = computed(() => ({
  left: pos.value.x + 'px',
  top: pos.value.y + 'px',
}))

const bubbleBelow = computed(() => pos.value.y < 250)
const bubbleLeft = computed(() => pos.value.x < 280)

function clampPos(x, y) {
  const maxX = Math.max(MARGIN, window.innerWidth - AVATAR_W - MARGIN)
  const maxY = Math.max(MARGIN, window.innerHeight - AVATAR_H - MARGIN)
  return {
    x: Math.min(maxX, Math.max(MARGIN, x)),
    y: Math.min(maxY, Math.max(MARGIN, y)),
  }
}

function loadPos() {
  try {
    const raw = localStorage.getItem(POS_KEY)
    if (raw) {
      const p = JSON.parse(raw)
      if (Number.isFinite(p.x) && Number.isFinite(p.y)) {
        pos.value = clampPos(p.x, p.y)
        return
      }
    }
  } catch { /* ignore */ }
  pos.value = clampPos(
    window.innerWidth - AVATAR_W - 22,
    window.innerHeight - AVATAR_H - 22,
  )
}

function savePos() {
  try { localStorage.setItem(POS_KEY, JSON.stringify(pos.value)) } catch { /* ignore */ }
}

function onResize() { pos.value = clampPos(pos.value.x, pos.value.y) }

function onPointerDown(e) {
  if (e.button !== 0) return
  dragging.value = true
  moved.value = false
  dragStart = { x: e.clientX, y: e.clientY, px: pos.value.x, py: pos.value.y }
  try { e.currentTarget.setPointerCapture(e.pointerId) } catch { /* ignore */ }
  e.preventDefault()
}

function onPointerMove(e) {
  if (!dragging.value || !dragStart) return
  const dx = e.clientX - dragStart.x
  const dy = e.clientY - dragStart.y
  if (!moved.value && Math.hypot(dx, dy) > 4) moved.value = true
  pos.value = clampPos(dragStart.px + dx, dragStart.py + dy)
}

function onPointerUp(e) {
  if (!dragging.value) return
  dragging.value = false
  try { e.currentTarget.releasePointerCapture(e.pointerId) } catch { /* ignore */ }
  if (!moved.value) toggleOpen()
  else savePos()
  dragStart = null
}

function toggleOpen() {
  open.value = !open.value
  if (open.value) {
    mode.value = 'menu'
    error.value = ''
    setLook('happy', 900)
  } else {
    setLook('idle')
  }
}

function onDocPointerDown(e) {
  // 点小基/气泡外面才收起；气泡内操作（总结、截图、上传）不会把它弄没
  if (!open.value) return
  const t = e.target
  if (t instanceof Element && t.closest('.xj-page-host')) return
  open.value = false
  setLook('idle')
}

function plainText(s) {
  // 小气泡不是 Markdown 渲染器：把标题/加粗/列表记号压成纯文本
  return String(s || '')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/^\s*[-*]\s+/gm, '· ')
    .trim()
}

function summarize() {
  // 默认走「页面框架 + 本地模板」：0 token、即时返回。
  // 只有用户点「让小基细说」才调模型，且只传框架 + 1200 字节选。
  error.value = ''
  setLook('thinking')
  const local = localOverview(props.routePath, { auth: authStore.user })
  summary.value = plainText(local.text)
  mode.value = 'summary'
  setLook('speaking', 2200)
}

async function preciseSummary() {
  const uid = authStore.user?.id
  if (!uid || busy.value) return
  busy.value = true
  error.value = ''
  mode.value = 'loading'
  setLook('thinking')
  try {
    const ctx = pageLightContext(props.routePath)
    const res = await summarizePage(uid, {
      route: props.routePath,
      title: ctx.title,
      page_key: ctx.page_key,
      framework: ctx.framework,
      snippet: ctx.snippet,
    })
    if (res?.summary) summary.value = plainText(res.summary)
    mode.value = 'summary'
    setLook('speaking', 2400)
  } catch (e) {
    error.value = e?.response?.data?.detail || '细说失败，先用上面的概述'
    mode.value = 'summary'
    setLook('idle')
  } finally {
    busy.value = false
  }
}

async function openOverview() {
  const uid = authStore.user?.id
  if (!uid) return
  error.value = ''
  setLook('thinking')
  try {
    const d = await getXiaojiDaily(uid)
    overview.value = {
      studyDays: d?.stats?.study_days_7d || 0,
      weekQuestions: d?.stats?.week_questions || 0,
      rec: d?.recommendation?.title || d?.recommendation?.content || '',
    }
    mode.value = 'overview'
    setLook('speaking', 2200)
  } catch (e) {
    error.value = '今日概览暂时拿不到'
    mode.value = 'menu'
    setLook('idle')
  }
}

function onImagePick(e) {
  const f = e.target.files?.[0]
  e.target.value = ''
  if (f) analyzeImageFile(f)
}

async function captureScreen() {
  // 框选区域截图：先把当前页面画成一张图，再在图上拖拽选择区域。
  // 不走 getDisplayMedia（那是「分享屏幕」），不需要浏览器授权。
  if (capturing.value || cropOpen.value) return
  open.value = false
  error.value = ''
  capturing.value = true
  setLook('thinking')
  await nextTick()
  await new Promise(r => setTimeout(r, 120))
  try {
    const { default: html2canvas } = await import('html2canvas')
    const el = document.querySelector('.app-container') || document.body
    const canvas = await html2canvas(el, {
      backgroundColor: '#0b1020',
      scale: 1,
      useCORS: true,
      logging: false,
      // 用浏览器自己的 foreignObject 渲染：项目大量使用 color-mix()，
      // html2canvas 默认的 CSS 解析器会报 "unsupported color function color"。
      foreignObjectRendering: true,
      width: window.innerWidth,
      height: window.innerHeight,
      windowWidth: window.innerWidth,
      windowHeight: window.innerHeight,
      x: window.scrollX,
      y: window.scrollY,
    })
    cropUrl.value = canvas.toDataURL('image/jpeg', 0.92)
    cropOpen.value = true
  } catch (e) {
    console.error('[xiaoji capture]', e)
    error.value = '页面截图失败，可以改用粘贴截图'
    open.value = true
    mode.value = 'menu'
    setLook('idle')
  } finally {
    capturing.value = false
  }
}

function onCropConfirm(blob) {
  cropOpen.value = false
  cropUrl.value = ''
  setLook('thinking')
  if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
  imagePreview.value = URL.createObjectURL(blob)
  analyzeImageBlob(blob)
}

function onCropCancel() {
  cropOpen.value = false
  cropUrl.value = ''
  open.value = true
  mode.value = 'menu'
  setLook('idle')
}

async function analyzeImageFile(file) {
  if (!file) return
  if (!file.type.startsWith('image/')) {
    error.value = '请选择图片（png / jpg / webp）'
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    error.value = '图片超过 10MB，请压缩后再试'
    return
  }
  if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
  imagePreview.value = URL.createObjectURL(file)
  await analyzeImageBlob(file)
}

async function analyzeImageBlob(blob) {
  const uid = authStore.user?.id
  if (!uid) return
  open.value = true
  mode.value = 'imageLoading'
  error.value = ''
  setLook('thinking')
  try {
    const file = blob instanceof File
      ? blob
      : new File([blob], 'screenshot.jpg', { type: blob.type || 'image/jpeg' })
    const title = (document.title || props.routePath || '').slice(0, 40)
    const res = await analyzeImage(
      uid, file,
      `请解析这张截图。用户当前在页面「${title}」。它是什么页面、题目或图表？提取关键信息，并给出下一步建议。看不清的地方直说。`,
    )
    imageAnalysis.value = plainText(res?.analysis || '这张图我没看懂，可以重新截一张。')
    mode.value = 'imageResult'
    setLook('speaking', 2600)
  } catch (e) {
    error.value = e?.response?.data?.detail || e?.message || '识图失败，请重试'
    mode.value = 'menu'
    setLook('idle')
  }
}

function onPaste(e) {
  if (!open.value) return
  const t = e.target
  if (t && ['INPUT', 'TEXTAREA'].includes(t.tagName)) return
  const items = Array.from(e.clipboardData?.items || [])
  const item = items.find(i => i.type.startsWith('image/'))
  if (!item) return
  const f = item.getAsFile()
  if (f) {
    e.preventDefault()
    analyzeImageFile(f)
  }
}

function search() {
  open.value = false
  navStore.openSearch()
}

function upload() {
  open.value = false
  openXiaojiPopup({ mode: 'upload' })
}

function home() {
  open.value = false
  router.push('/home')
}

function go(path) {
  open.value = false
  if (path) router.push(path)
}

function goActionLink() {
  if (actionLink.value) go(actionLink.value)
}

// ===== 学程页专属动作 =====
const TASK_TYPE_LABEL = { seed: '播种', daily: '每日', long: '长期' }

function flattenTasks(data) {
  const out = []
  for (const type of ['seed', 'daily', 'long']) {
    for (const task of (data?.[type] || [])) out.push({ type, task })
  }
  return out
}

async function showNearDoneTasks() {
  if (actionBusy.value) return
  const uid = authStore.user?.id
  if (!uid) return
  actionBusy.value = true
  error.value = ''
  setLook('thinking')
  try {
    const data = await getTaskProgress(uid)
    const all = flattenTasks(data)
    const near = all
      .filter(({ task }) => !task.done && !task.locked && Number(task.progress || 0) >= 50)
      .sort((a, b) => (b.task.progress || 0) - (a.task.progress || 0))
      .slice(0, 4)

    if (near.length) {
      actionText.value = '快到终点了：' + near.map(({ type, task }) =>
        `${task.name}（${TASK_TYPE_LABEL[type]} ${Math.round(task.progress || 0)}%）`
      ).join('；') + '。要现在去完成吗？'
    } else {
      const ready = all.filter(({ task }) => task.ready && !task.done).length
      actionText.value = ready
        ? `有 ${ready} 个任务已经可以领取，点「可领取任务」我直接帮你收。`
        : '暂时没有完成度过半的任务，先从每日任务开始吧。'
    }
    actionLink.value = '/career/tasks'
    mode.value = 'action'
    setLook('speaking', 2600)
  } catch (e) {
    console.error('[xiaoji page] 任务进度读取失败', e)
    error.value = '任务进度读取失败，请稍后重试'
    mode.value = 'menu'
    setLook('idle')
  } finally {
    actionBusy.value = false
  }
}

async function claimReadyTasks() {
  if (actionBusy.value) return
  const uid = authStore.user?.id
  if (!uid) return
  actionBusy.value = true
  error.value = ''
  setLook('thinking')
  try {
    const data = await getTaskProgress(uid)
    const ready = flattenTasks(data)
      .filter(({ task }) => task.ready && !task.done && !task.locked)

    if (!ready.length) {
      actionText.value = '现在没有可领取的奖励。先把进行中的任务推一推，完成后再来。'
      actionLink.value = '/career/tasks'
      mode.value = 'action'
      setLook('speaking', 2200)
      return
    }

    let ok = 0
    let failed = 0
    let points = 0
    for (const { type, task } of ready) {
      try {
        const res = await claimCareerTask(uid, task.id || task.name, type)
        if (res?.success) {
          ok += 1
          points += (res.rank_points_gained || 0) + (res.level_points_gained || 0)
        } else {
          failed += 1
        }
      } catch {
        failed += 1
      }
    }

    actionText.value = `已领取 ${ok} 个奖励${points ? `，共 +${points} 积分` : ''}` +
      `${failed ? `；${failed} 个没领成功，可以去学程页重试` : ''}。`
    actionLink.value = '/career/tasks'
    mode.value = 'action'
    setLook('happy', 2600)
    window.dispatchEvent(new CustomEvent('task-claimed'))
    // 学程页正开着时刷新任务数据（CareerTasks.vue 监听这个事件）
    window.dispatchEvent(new CustomEvent('xiaoji-claimed-tasks'))
  } catch (e) {
    console.error('[xiaoji page] 领取失败', e)
    error.value = '领取失败，请稍后重试'
    mode.value = 'menu'
    setLook('idle')
  } finally {
    actionBusy.value = false
  }
}

function hide() {
  open.value = false
  setLook('idle')
  stopIdleActions()
  hidden.value = true
  try { sessionStorage.setItem('xiaoji_page_hidden', '1') } catch { /* ignore */ }
}

onMounted(() => {
  try { hidden.value = sessionStorage.getItem('xiaoji_page_hidden') === '1' } catch { /* ignore */ }
  loadPos()
  startIdleActions()
  window.addEventListener('resize', onResize)
  window.addEventListener('paste', onPaste)
  document.addEventListener('pointerdown', onDocPointerDown, true)
})

onBeforeUnmount(() => {
  stopIdleActions()
  window.removeEventListener('resize', onResize)
  window.removeEventListener('paste', onPaste)
  document.removeEventListener('pointerdown', onDocPointerDown, true)
  if (imagePreview.value) URL.revokeObjectURL(imagePreview.value)
})
</script>

<style scoped>
.xj-page-host {
  position: fixed; z-index: 9000;
  pointer-events: none;
}
/* 截图的一瞬间把自己藏起来，别把头像截进图里 */
.xj-page-host.capturing { visibility: hidden; }
/* ===== 页面驻扎小基：3D 玻璃球（2026-10-30）=====
   原始 MP4 是浅底、无 alpha；装进球里就不用透明裁剪了。 */
.xj-avatar-btn {
  position: relative;
  width: 92px; height: 122px;
  display: block; padding: 0; border: none; background: transparent;
  cursor: grab; pointer-events: auto; touch-action: none;
  user-select: none; -webkit-user-select: none;
  filter: drop-shadow(0 8px 14px rgba(0, 0, 0, .35));
  transition: transform .18s ease, filter .18s ease;
}
.xj-avatar-btn:hover {
  transform: translateY(-2px) scale(1.03);
  filter: drop-shadow(0 12px 20px rgba(0, 0, 0, .4));
}
.xj-avatar-btn.dragging {
  cursor: grabbing; transform: scale(1.05);
  filter: drop-shadow(0 14px 24px rgba(0, 0, 0, .45));
}
.xj-avatar-btn img {
  width: 100%; height: 100%; object-fit: contain; display: block;
  user-select: none; -webkit-user-drag: none;
  will-change: transform;
  /* 即使 WebP 因浏览器/网络原因没动，整只小基也一直在轻轻浮动 */
  animation: xj-float 4.2s ease-in-out infinite;
}
/* WebP 失败回落到静态 PNG 时换个更慢的节奏，仍然有循环动作 */
.xj-avatar-btn img.static { animation-duration: 3.6s; }
.xj-avatar-btn.dragging img { animation: none; }
@keyframes xj-float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50% { transform: translateY(-3px) rotate(-1deg); }
}

.xj-bubble {
  position: absolute; bottom: calc(100% + 6px); right: 0;
  pointer-events: auto;
  width: 252px; max-height: 380px; overflow-y: auto;
  padding: 12px 14px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--surface, #ffffff) 92%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand) 20%, transparent);
  box-shadow: 0 12px 36px rgba(0, 0, 0, .18);
  backdrop-filter: blur(22px) saturate(1.4);
}
[data-theme="dark"] .xj-bubble {
  background: color-mix(in srgb, var(--surface, #0f172a) 88%, transparent);
}
.xj-bubble.below { bottom: auto; top: calc(100% + 6px); }
.xj-bubble.align-left { right: auto; left: 0; }

.xj-bubble-head { display: flex; align-items: center; gap: 8px; }
.xj-bubble-title { font-size: 12.5px; font-weight: 700; color: var(--text-primary); }
.xj-back {
  margin-left: auto; border: none; background: transparent; cursor: pointer;
  color: var(--text-muted); font-size: 14px; padding: 0 2px;
}
.xj-back:hover { color: var(--text-primary); }
.xj-hint { margin: 7px 0 9px; font-size: 12px; line-height: 1.6; color: var(--text-secondary); }

.xj-section-label {
  display: block; margin: 9px 0 5px;
  font-size: 10.5px; color: var(--text-muted); letter-spacing: .4px;
}
.xj-page-actions { display: flex; flex-direction: column; gap: 6px; }
.xj-page-actions button,
.xj-actions button {
  text-align: left; padding: 7px 10px; border-radius: 9px;
  border: 1px solid var(--border-color); background: transparent;
  color: var(--text-primary); font-size: 12px; font-family: inherit; cursor: pointer;
  transition: all .18s ease;
}
.xj-page-actions button {
  border-color: color-mix(in srgb, var(--brand) 28%, transparent);
  background: color-mix(in srgb, var(--brand) 7%, transparent);
  font-weight: 600;
}
.xj-page-actions button:hover:not(:disabled),
.xj-actions button:hover {
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  border-color: color-mix(in srgb, var(--brand) 40%, transparent);
}
.xj-page-actions button:disabled { opacity: .5; cursor: wait; }
.xj-actions { display: flex; flex-direction: column; gap: 6px; }
.xj-actions.tight { margin-top: 10px; flex-direction: row; flex-wrap: wrap; }
.xj-actions button.ghost { color: var(--text-muted); }

.xj-loading { margin: 8px 0; font-size: 12px; color: var(--text-muted); }
.xj-summary {
  margin: 8px 0 0; font-size: 12px; line-height: 1.7; color: var(--text-secondary);
  white-space: pre-wrap; word-break: break-word;
}
.xj-overview { display: flex; gap: 8px; margin: 10px 0 8px; }
.xj-ov-item {
  flex: 1; padding: 8px 6px; border-radius: 10px; text-align: center;
  background: color-mix(in srgb, var(--brand) 7%, transparent);
}
.xj-ov-item b { display: block; font-size: 18px; color: var(--text-primary); }
.xj-ov-item span { font-size: 10.5px; color: var(--text-muted); }
.xj-rec { margin: 6px 0 0; font-size: 12px; line-height: 1.6; color: var(--text-secondary); }
.xj-error { margin: 8px 0 0; font-size: 12px; line-height: 1.6; color: #e6a23c; }
.xj-hidden-input { display: none; }
.xj-img-preview {
  width: 100%; max-height: 150px; object-fit: contain;
  border-radius: 10px; margin: 8px 0;
  background: rgba(128, 128, 128, .08);
}

@media (max-width: 640px) {
  .xj-avatar-btn { width: 64px; height: 92px; }
  .xj-bubble { width: 228px; }
}

/* 系统开了「减少动态效果」：保留形象，但不再漂浮/循环闪动 */
@media (prefers-reduced-motion: reduce) {
  .xj-avatar-btn img { animation: none; }
}

.xj-bubble-enter-active, .xj-bubble-leave-active { transition: opacity .18s ease, transform .18s ease; }
.xj-bubble-enter-from, .xj-bubble-leave-to { opacity: 0; transform: translateY(6px) scale(.97); }
</style>
