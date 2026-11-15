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

          <!-- 记忆流 / 我的路线（2026-11-04）：
               学习出来的路线（接着上次 / 下一步 / 常走）和用户自己设的固定路线分开展示。
               学习部分证据不够时不渲染；「我的路线」是用户明确设的，冷启动也有。 -->
          <div v-if="customRoute || memorySuggestions.length || memoryRoute.length || memoryMsg" class="xj-memory">
            <template v-if="customRoute">
              <span class="xj-section-label">我的路线</span>
              <button
                v-if="customNext"
                class="xj-memory-jump"
                :disabled="memoryBusy"
                @click="goCustomRoute"
              >
                <span class="xj-memory-ic">🧭</span>
                <span class="xj-memory-body">
                  <b>{{ memoryTitle(customNext) }}</b>
                  <em>{{ customNext.reason }}</em>
                </span>
              </button>
              <div class="xj-memory-route">我的路线：{{ customRouteLine }}</div>
              <div class="xj-memory-foot">
                <button @click="openRouteEditor">编辑</button>
              </div>
            </template>

            <div v-if="memorySuggestions.length || memoryRoute.length" class="xj-memory-learned">
              <span class="xj-section-label">小基记下的</span>
              <button
                v-for="s in memorySuggestions"
                :key="s.id"
                class="xj-memory-jump"
                :disabled="memoryBusy"
                @click="onMemoryJump(s)"
              >
                <span class="xj-memory-ic">{{ s.type === 'resume' ? '↩' : '→' }}</span>
                <span class="xj-memory-body">
                  <b>{{ memoryTitle(s) }}</b>
                  <em>{{ s.reason }}</em>
                </span>
              </button>
              <div v-if="memoryRoute.length" class="xj-memory-route">
                你常这样走：{{ memoryRoute.map(x => memoryTitle(x)).join(' → ') }}
              </div>
              <div class="xj-memory-foot">
                <button v-if="memorySuggestions.length" @click="dismissMemoryHint">{{ memoryDismissLabel }}</button>
                <button @click="clearMemory">{{ clearArmed ? '确定清空' : '清空记忆' }}</button>
              </div>
            </div>

            <p v-if="memoryMsg" class="xj-memory-msg">{{ memoryMsg }}</p>
          </div>

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
            <button @click="openTasks">⏱ 任务</button>
            <button @click="openRouteEditor">🗺 设置路线</button>
            <button @click="home">💬 找小基聊聊</button>
            <button class="ghost" @click="hide">👋 先躲起来</button>
          </div>
        </template>

        <template v-else-if="mode === 'route'">
          <p class="xj-hint">按顺序加入页面；保存后，小基按你当前的位置提示下一步。</p>

          <div v-if="routeDraft.length" class="xj-route-steps">
            <div v-for="(s, i) in routeDraft" :key="`${s.key}-${i}`" class="xj-route-step">
              <span class="xj-route-no">{{ i + 1 }}</span>
              <span class="xj-route-name">{{ memoryTitle(s) }}</span>
              <button class="xj-route-mini" :disabled="i === 0" title="上移"
                      @click="moveRouteStep(i, -1)">↑</button>
              <button class="xj-route-mini" :disabled="i === routeDraft.length - 1" title="下移"
                      @click="moveRouteStep(i, 1)">↓</button>
              <button class="xj-route-mini xj-route-del" title="移除"
                      @click="removeRouteStep(i)">×</button>
            </div>
          </div>
          <p v-if="!routeDraft.length" class="xj-hint">还没有步骤，从下面选一个页面加入。</p>
          <p v-else-if="routeDraft.length === 1" class="xj-hint">再加一个页面就可以保存了。</p>

          <div class="xj-route-add">
            <select v-model="routePick" class="xj-route-select">
              <option value="">选一个页面…</option>
              <option value="__current__">当前页：{{ memoryTitle(currentRouteStep) }}</option>
              <optgroup v-for="g in routeGroups" :key="g.name" :label="g.name">
                <option v-for="p in g.pages" :key="p.path" :value="p.path">{{ p.title }}</option>
              </optgroup>
            </select>
            <button class="xj-route-addbtn" :disabled="!routePick" @click="addRouteStep">加入</button>
          </div>

          <p v-if="routeError" class="xj-error">{{ routeError }}</p>

          <div class="xj-actions tight">
            <button :disabled="routeDraft.length < 2" @click="saveRoute">保存路线</button>
            <button class="ghost" @click="mode = 'menu'">取消</button>
          </div>
          <div v-if="customRoute" class="xj-route-delete">
            <button @click="deleteCustomRoute">{{ routeClearArmed ? '确定删除' : '删除我的路线' }}</button>
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

        <!-- 跨页任务：与智能体中心共用同一份 run 数据 -->
        <template v-else-if="mode === 'tasks'">
          <p v-if="runState.error" class="xj-error">{{ runState.error }}</p>
          <p v-if="!activeRuns.length" class="xj-hint">当前没有进行中的任务。拖资料出题后会在这里看到进度。</p>
          <div v-else class="xj-run-list">
            <div v-for="r in activeRuns" :key="r.id" class="xj-run-item">
              <div class="xj-run-top">
                <b class="xj-run-title">{{ r.title || workflowName(r.workflow_key) }}</b>
                <span class="xj-run-pct">{{ r.progress || 0 }}%</span>
              </div>
              <div class="xj-run-bar"><span :style="{ width: (r.progress || 0) + '%' }"></span></div>
              <p class="xj-run-stage">{{ stageText(r) }}</p>
              <div class="xj-run-actions">
                <button v-if="r.status === 'awaiting_confirm'" @click="goConfirmTask(r)">去确认</button>
                <button v-else-if="r.link" @click="goTaskLink(r)">看结果</button>
                <button v-if="canResumeRun(r)" class="ghost" :disabled="taskBusyRun === r.id" @click="resumeTask(r)">继续</button>
                <button v-else-if="canPauseRun(r)" class="ghost" :disabled="taskBusyRun === r.id" @click="pauseTask(r)">暂停</button>
                <button class="ghost" :disabled="taskBusyRun === r.id" @click="cancelTask(r)">
                  {{ taskBusyRun === r.id ? '处理中…' : '取消' }}
                </button>
              </div>
            </div>
          </div>
          <div class="xj-actions tight">
            <button class="ghost" @click="mode = 'menu'">收起</button>
          </div>
        </template>

        <p v-if="error" class="xj-error">{{ error }}</p>
      </div>
    </Transition>

    <!-- 记忆流：新会话第一次落到业务页时，只在头像上方提示一次「接着上次」。
         不自动跳转、不自动展开气泡；忽略或点掉后本次会话不再打扰。 -->
    <button v-if="resumeChip && resumeChipVisible && !open && !hidden"
            class="xj-resume-chip" :class="{ below: bubbleBelow }" title="接着上次"
            @click="onMemoryJump(resumeChip)">
      <span class="xj-resume-text">接着上次 · {{ memoryTitle(resumeChip) }}</span>
      <span class="xj-resume-x" title="先不用" @click.stop="dismissResumeChip">×</span>
    </button>

    <!-- 页面事件反应（2026-11-11）：答题对错 / 生成完成等只在头像旁说一句，
         不展开气泡、不挡点击；用户打开气泡或拖走小基时不显示。 -->
    <div v-if="reactionVisible && reactionText && !open && !hidden"
         class="xj-reaction-chip"
         :class="{
           below: bubbleBelow,
           stacked: resumeChip && resumeChipVisible && !open,
         }"
         role="status" aria-live="polite">
      {{ reactionText }}
    </div>

    <!-- 跨页任务进度环：有活跃 run 时出现在头像右上角 -->
    <button v-if="activeRuns.length" class="xj-task-ring" :style="ringStyle"
            :title="`${activeRuns.length} 个任务未结束`"
            @pointerdown.stop @click.stop="openTasks">
      <span class="xj-ring-core">{{ activeRuns.length }}</span>
    </button>

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
import { computed, ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNavStore } from '@/stores/nav'
import { getXiaojiDaily } from '@/api/xiaoji'
import { getTaskProgress, claimCareerTask } from '@/api/career'
import { summarizePage, analyzeImage } from '@/api/agents'
import { localOverview, pageLightContext } from '@/xiaoji/pageFrameworks'
import { openXiaojiPopup } from '@/xiaoji/popupStore'
import { onXiaoji } from '@/xiaoji/bus'
import { resolveReaction } from '@/xiaoji/reactions'
import { resolvePageTitle, STATIC_PAGES } from '@/utils/pageMeta'
import {
  getMemoryFlow, pageKeyOf, acceptSuggestion, rejectSuggestion,
  dismissResume, clearRouteMemory,
  getCustomRoute, saveCustomRoute, clearCustomRoute, nextCustomStep,
} from '@/utils/routeMemory'
import {
  runState, activeRuns, startRunPolling, cancelRunById,
  pauseRunById, resumeRunById, canPauseRun, canResumeRun,
} from '@/stores/runStore'
import ScreenshotCropper from '@/components/ScreenshotCropper.vue'

const props = defineProps({
  routePath: { type: String, default: '' },
})

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const navStore = useNavStore()

const AVATAR_W = 92
const AVATAR_H = 122
const MARGIN = 8
const POS_KEY = 'xiaoji_page_pos'

const open = ref(false)
const hidden = ref(false)
const mode = ref('menu')          // menu / loading / summary / overview / action / tasks / route
const taskBusyRun = ref('')
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

// ===== 页面事件感知（2026-11-11）=====
// 页面通过 xiaoji/bus 发事件；这里只负责表情、节流和头像旁的一句短话。
const reactionText = ref('')
const reactionVisible = ref(false)
const reducedMotion = ref(false)
const reactionLastAt = new Map()   // 事件类型 → 上次反应时间
const reactionSeenOnce = new Set() // payload.once 的事件只反应一次
let reactionTimer = null
let lastAnyReactionAt = 0
let motionMq = null
let offXiaojiBus = null

// ===== 记忆流（2026-11-04）=====
const memorySuggestions = ref([])
const memoryRoute = ref([])
const resumeChip = ref(null)
const memoryBusy = ref(false)
const memoryMsg = ref('')
const memoryDismissed = ref(false)   // 本次停留已说过「不太准」，不再推下一步
const clearArmed = ref(false)        // 「清空」二次确认
const resumeChipVisible = ref(false) // 新会话只在第一个业务页提示一次
const customRoute = ref(null)        // 用户自己设的固定路线
const routeDraft = ref([])
const routePick = ref('')
const routeError = ref('')
const routeClearArmed = ref(false)
let memoryFirstPath = ''
let memoryMsgTimer = null

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
// 系统开了「减少动态效果」时直接用静态 PNG：WebP 自己会循环播放，
// 只关 CSS 浮动不够（设计文档 12.4 的已知差距）。
const lookImgUrl = computed(() => {
  if (reducedMotion.value || lookFallback.value) return lookUrl.value
  return lookWebpUrl.value + (lookBust.value ? `?v=${lookBust.value}` : '')
})
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

// ===== 页面事件反应（2026-11-11）=====
function showReaction(text, ms = 3200) {
  reactionText.value = text
  reactionVisible.value = true
  if (reactionTimer) clearTimeout(reactionTimer)
  reactionTimer = setTimeout(() => {
    reactionVisible.value = false
    reactionText.value = ''
    reactionTimer = null
  }, ms)
}

function clearReaction() {
  if (reactionTimer) clearTimeout(reactionTimer)
  reactionTimer = null
  reactionVisible.value = false
  reactionText.value = ''
}

function onPageEvent(e) {
  if (hidden.value || !e?.type) return
  // 异步任务完成时用户可能已经换页了，过期事件不再反应
  if (e.page && props.routePath && e.page !== props.routePath) return
  const r = resolveReaction(e)
  if (!r) return

  const now = Date.now()
  const lastType = reactionLastAt.get(e.type) || 0
  if (!r.force && r.cooldown && now - lastType < r.cooldown) return
  // 不同事件之间也留一点间隔，避免两个事件同时到达时表情乱跳；
  // 但不能太长 —— 答题接口很快返回时，submit → correct 不能被吞掉。
  if (!r.force && now - lastAnyReactionAt < 200) return
  // 正在总结/识图/办动作时不抢状态
  if (mode.value === 'loading' || mode.value === 'imageLoading' || actionBusy.value) return
  // once 的事件只反应一次
  if (e.once) {
    const key = `${e.type}:${e.page || ''}`
    if (reactionSeenOnce.has(key)) return
    reactionSeenOnce.add(key)
  }

  reactionLastAt.set(e.type, now)
  lastAnyReactionAt = now
  setLook(r.look, r.duration)

  if (!r.text || open.value || dragging.value) return
  // 考试页只做表情，不弹字（设计文档 4.3）
  if (r.quietOnExam && /\/exam\//.test(props.routePath || '')) return
  showReaction(r.text, r.bubbleMs)
}

function onMotionPrefChange(e) {
  reducedMotion.value = !!e?.matches
  if (reducedMotion.value) lookFallback.value = false
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

// ===== 记忆流（2026-11-04）=====
// 读取由 routeMemory 在全局记录的本机路线；这里只负责展示、跳转和反馈。
// 没把握时 getMemoryFlow 返回空，界面就不出现这一块。
function memoryTitle(item) {
  const raw = String(item?.titleKey || item?.path || item?.key || '')
  const clean = raw.split('?')[0]
  const resolved = resolvePageTitle(clean)
  // 静态页/可识别前缀用命名册；认不出来的动态页用保存时的标题兜底
  if (resolved && resolved !== clean) return resolved
  return item?.title || resolved || '这个页面'
}

// 「接着上次」是事实，不是猜测，别用「不太准」这种反馈词
const memoryDismissLabel = computed(() =>
  memorySuggestions.value.some(s => s.type === 'next') ? '不太准' : '先不用')

// ===== 我的路线（用户自己设的固定路线）=====
// 与学习出来的记忆流分开：这里只认用户保存的顺序，不参与衰减/阈值。
const ROUTE_SKIP = new Set([
  '/settings', '/qa', '/open-source', '/guide', '/agreement', '/privacy',
  '/animation-demo', '/vlp-debug', '/onboarding', '/theme', '/api-center',
  '/xiaoji/tree', '/xiaoji/search', '/xiaoji/settings',
])

const routeGroups = computed(() => {
  const groups = new Map()
  for (const p of STATIC_PAGES) {
    if (ROUTE_SKIP.has(p.path)) continue
    const g = p.group || '其他'
    if (!groups.has(g)) groups.set(g, [])
    groups.get(g).push({ key: p.path, path: p.path, title: p.title })
  }
  return [...groups.entries()].map(([name, pages]) => ({ name, pages }))
})

const currentRouteStep = computed(() => ({
  key: pageKeyOf(route),
  // 加入「当前页」时保留 query/hash（如题集 id、学科 id），跳回去才是原处
  path: route.fullPath || route.path,
  title: resolvePageTitle(route.path),
}))

const customNext = computed(() => {
  const steps = customRoute.value?.steps || []
  const target = nextCustomStep(steps, currentRouteStep.value.key)
  return target ? { ...target, id: 'custom' } : null
})

const customRouteLine = computed(() =>
  (customRoute.value?.steps || []).map(s => memoryTitle(s)).join(' → '))

function refreshMemory() {
  const uid = authStore.user?.id
  if (!uid) {
    memorySuggestions.value = []
    memoryRoute.value = []
    resumeChip.value = null
    customRoute.value = null
    return
  }
  customRoute.value = getCustomRoute(uid)
  const data = getMemoryFlow(uid, pageKeyOf(route), { currentPath: route.path })
  resumeChip.value = data.resume || null
  memorySuggestions.value = memoryDismissed.value
    ? data.suggestions.filter(s => s.type === 'resume')
    : data.suggestions
  memoryRoute.value = memoryDismissed.value ? [] : (data.route || [])
}

// ===== 路线编辑器 =====
function openRouteEditor() {
  const uid = authStore.user?.id
  if (!uid) return
  const saved = getCustomRoute(uid)
  routeDraft.value = saved ? saved.steps.map(s => ({ ...s })) : []
  routePick.value = ''
  routeError.value = ''
  routeClearArmed.value = false
  mode.value = 'route'
  open.value = true
  error.value = ''
  setLook('thinking', 1200)
}

function addRouteStep() {
  routeError.value = ''
  const pick = routePick.value
  if (!pick) return
  let step
  if (pick === '__current__') {
    step = { ...currentRouteStep.value }
  } else {
    const hit = STATIC_PAGES.find(p => p.path === pick)
    if (!hit) return
    step = { key: hit.path, path: hit.path, title: hit.title }
  }
  if (routeDraft.value.length >= 10) {
    routeError.value = '一条路线最多 10 步'
    return
  }
  const last = routeDraft.value[routeDraft.value.length - 1]
  if (last && last.key === step.key) {
    routeError.value = '连续两步不能是同一页'
    return
  }
  routeDraft.value.push(step)
  routePick.value = ''
  routeClearArmed.value = false
}

function removeRouteStep(i) {
  routeDraft.value.splice(i, 1)
  routeError.value = ''
  routeClearArmed.value = false
}

function moveRouteStep(i, delta) {
  const j = i + delta
  const arr = routeDraft.value
  if (j < 0 || j >= arr.length) return
  const [item] = arr.splice(i, 1)
  arr.splice(j, 0, item)
  routeError.value = ''
  routeClearArmed.value = false
}

function saveRoute() {
  routeError.value = ''
  if (routeDraft.value.length < 2) {
    routeError.value = '至少选两个页面才算一条路线'
    return
  }
  const uid = authStore.user?.id
  if (!uid) return
  if (!saveCustomRoute(uid, routeDraft.value)) {
    routeError.value = '保存失败，再试一次'
    return
  }
  customRoute.value = getCustomRoute(uid)
  mode.value = 'menu'
  flashMemoryMsg('路线已保存')
  setLook('happy', 1800)
}

function deleteCustomRoute() {
  const uid = authStore.user?.id
  if (!uid) return
  // 编辑器里没有共享消息位，第一次点击只改按钮文案
  if (!routeClearArmed.value) {
    routeClearArmed.value = true
    return
  }
  clearCustomRoute(uid)
  customRoute.value = null
  routeDraft.value = []
  routeClearArmed.value = false
  mode.value = 'menu'
  flashMemoryMsg('已删除我的路线')
}

function goCustomRoute() {
  const target = customNext.value
  if (!target?.path || memoryBusy.value) return
  memoryBusy.value = true
  open.value = false
  setLook('happy', 900)
  router.push(target.path)
    .catch(() => {
      open.value = true
      mode.value = 'menu'
      flashMemoryMsg('这个页面暂时打不开')
    })
    .finally(() => { memoryBusy.value = false })
}

function flashMemoryMsg(text) {
  memoryMsg.value = text
  if (memoryMsgTimer) clearTimeout(memoryMsgTimer)
  memoryMsgTimer = setTimeout(() => { memoryMsg.value = '' }, 4000)
}

function onMemoryJump(s) {
  if (!s?.path || memoryBusy.value) return
  memoryBusy.value = true
  const uid = authStore.user?.id
  if (uid) acceptSuggestion(uid, s)
  open.value = false
  setLook('happy', 900)
  router.push(s.path)
    .catch(() => {
      // 跳转被拦下时把气泡打开，别让用户以为点了没反应
      open.value = true
      mode.value = 'menu'
      flashMemoryMsg('这个页面暂时打不开')
    })
    .finally(() => { memoryBusy.value = false })
}

function dismissMemoryHint() {
  const uid = authStore.user?.id
  if (!uid) return
  const target = memorySuggestions.value.find(s => s.type === 'next')
  if (target) {
    rejectSuggestion(uid, target)
    memoryDismissed.value = true
    flashMemoryMsg('记下了，这条先不推')
  } else if (resumeChip.value) {
    dismissResume(uid)
    resumeChip.value = null
    flashMemoryMsg('好，这次先不提醒')
  }
  refreshMemory()
}

function dismissResumeChip() {
  const uid = authStore.user?.id
  if (uid) dismissResume(uid)
  resumeChipVisible.value = false
  resumeChip.value = null
}

function clearMemory() {
  if (!clearArmed.value) {
    clearArmed.value = true
    flashMemoryMsg(customRoute.value
      ? '再点一次清空学习记忆（我的路线保留）'
      : '再点一次就清空学习记忆')
    return
  }
  const uid = authStore.user?.id
  if (uid) clearRouteMemory(uid)
  clearArmed.value = false
  resumeChipVisible.value = false
  memoryDismissed.value = false
  flashMemoryMsg(customRoute.value ? '学习记忆已清空，我的路线还在' : '学习记忆已清空')
  refreshMemory()
}

// 「接着上次」小提示：每个浏览器标签页、每个用户只提示一次。
// 用 sessionStorage 而不是 localStorage —— 关掉标签页再开就是新一次"打开"。
function resumeChipSeenKey(uid) { return `xj_resume_chip_seen:${uid || 'anon'}` }
function markResumeChipSeen(uid) {
  try { sessionStorage.setItem(resumeChipSeenKey(uid), '1') } catch { /* ignore */ }
}
function hasSeenResumeChip(uid) {
  try { return sessionStorage.getItem(resumeChipSeenKey(uid)) === '1' } catch { return false }
}

const bubbleTitle = computed(() => ({
  menu: '小基',
  loading: '正在总结',
  summary: '本页总结',
  overview: '今日概览',
  imageLoading: '正在识图',
  imageResult: '截图解析',
  action: '小基办好了',
  tasks: '任务进度',
  route: '设置路线',
}[mode.value] || '小基'))

// 进度环：取所有活跃 run 的平均进度；没有活跃任务时不渲染
const ringProgress = computed(() => {
  const xs = activeRuns.value.map(r => Number(r.progress) || 0)
  if (!xs.length) return 0
  return Math.round(xs.reduce((a, b) => a + b, 0) / xs.length)
})
const ringStyle = computed(() => ({
  '--p': `${Math.max(6, ringProgress.value)}%`,
}))

const HOST_WORKFLOW_NAMES = {
  file_to_questions: '上传出题',
  question_gen: '团队出题',
  evaluate: '团队评估',
  tuning_debate: '调参圆桌',
}
function workflowName(key) { return HOST_WORKFLOW_NAMES[key] || key || '任务' }
function stageText(r) {
  const map = {
    queued: '排队中', paused: '已暂停', pausing: '正在暂停',
    extracting: '提取文字 / 识别扫描页',
    profiling: '判断资料类型', seeding: '抽象可出题点',
    awaiting_confirm: '等你确认要生成哪些点', confirmed: '已确认，等待生成',
    generating: '生成题目中', crosschecking: '独立复核中',
    saving: '建题集', cancelling: '正在取消',
    ready: '已完成', failed: '失败', cancelled: '已取消',
  }
  return map[r.stage] || map[r.status] || ''
}

function openTasks() {
  error.value = ''
  open.value = true
  mode.value = 'tasks'
}

function goConfirmTask(r) {
  const jobId = r.input?.job_id
  if (jobId) {
    openXiaojiPopup({ mode: 'upload', jobId })
    open.value = false
  }
}

function goTaskLink(r) {
  if (!r.link) return
  open.value = false
  router.push(r.link)
}

async function cancelTask(r) {
  if (!r?.id || taskBusyRun.value) return
  taskBusyRun.value = r.id
  try {
    await cancelRunById(r.id)
  } catch (e) {
    error.value = e?.response?.data?.detail || '取消失败'
  } finally {
    taskBusyRun.value = ''
  }
}

async function pauseTask(r) {
  if (!r?.id || taskBusyRun.value) return
  taskBusyRun.value = r.id
  try {
    await pauseRunById(r.id)
  } catch (e) {
    error.value = e?.response?.data?.detail || '暂停失败'
  } finally {
    taskBusyRun.value = ''
  }
}

async function resumeTask(r) {
  if (!r?.id || taskBusyRun.value) return
  taskBusyRun.value = r.id
  try {
    await resumeRunById(r.id)
  } catch (e) {
    error.value = e?.response?.data?.detail || '继续失败'
  } finally {
    taskBusyRun.value = ''
  }
}

// 任务完成/失败时主动弹一次；正在总结/识图/处理动作时不打断
function onRunDone(e) {
  const r = e.detail || {}
  if (!r.id) return
  if (mode.value === 'loading' || mode.value === 'imageLoading' || actionBusy.value) return
  if (r.status === 'completed') {
    actionText.value = `${r.title || '任务'}已经完成`
      + (r.link ? '，要现在去看看吗？' : '。')
    actionLink.value = r.link || ''
    setLook('happy', 4000)
  } else if (r.status === 'failed') {
    actionText.value = `${r.title || '任务'}失败了：${r.error || '未知原因'}`
    actionLink.value = ''
    setLook('thinking', 4000)
  } else {
    return
  }
  error.value = ''
  open.value = true
  mode.value = 'action'
}

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

// 记忆流：换页时重算；「接着上次」只在新会话的第一个业务页露一次
watch(() => props.routePath, (path) => {
  if (memoryFirstPath && path !== memoryFirstPath) resumeChipVisible.value = false
  memoryDismissed.value = false
  clearArmed.value = false
  if (memoryMsgTimer) clearTimeout(memoryMsgTimer)
  memoryMsg.value = ''
  clearReaction()
  refreshMemory()
})

watch(open, (v) => {
  if (v) {
    clearReaction()
    refreshMemory()
    clearArmed.value = false
  }
})

watch(() => authStore.user?.id, () => {
  memoryDismissed.value = false
  clearArmed.value = false
  refreshMemory()
})

onMounted(() => {
  try { hidden.value = sessionStorage.getItem('xiaoji_page_hidden') === '1' } catch { /* ignore */ }
  loadPos()
  startIdleActions()
  if (authStore.user?.id) startRunPolling(authStore.user.id)
  memoryFirstPath = props.routePath
  refreshMemory()
  const uid = authStore.user?.id
  if (resumeChip.value && !hasSeenResumeChip(uid)) {
    resumeChipVisible.value = true
    markResumeChipSeen(uid)
  }
  window.addEventListener('resize', onResize)
  window.addEventListener('paste', onPaste)
  window.addEventListener('xiaoji-run-done', onRunDone)
  document.addEventListener('pointerdown', onDocPointerDown, true)

  // 页面事件感知：通配订阅，规则由 reactions.js 决定
  offXiaojiBus = onXiaoji('*', onPageEvent)
  try {
    motionMq = window.matchMedia('(prefers-reduced-motion: reduce)')
    reducedMotion.value = motionMq.matches
    if (motionMq.addEventListener) motionMq.addEventListener('change', onMotionPrefChange)
    else if (motionMq.addListener) motionMq.addListener(onMotionPrefChange) // 老 Safari
  } catch { /* ignore */ }
})

onBeforeUnmount(() => {
  stopIdleActions()
  clearReaction()
  if (offXiaojiBus) { offXiaojiBus(); offXiaojiBus = null }
  if (motionMq) {
    try {
      if (motionMq.removeEventListener) motionMq.removeEventListener('change', onMotionPrefChange)
      else if (motionMq.removeListener) motionMq.removeListener(onMotionPrefChange)
    } catch { /* ignore */ }
    motionMq = null
  }
  if (memoryMsgTimer) clearTimeout(memoryMsgTimer)
  window.removeEventListener('resize', onResize)
  window.removeEventListener('paste', onPaste)
  window.removeEventListener('xiaoji-run-done', onRunDone)
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

/* ===== 跨页任务进度环（2026-10-31）===== */
.xj-task-ring {
  position: absolute; right: -6px; top: -8px;
  width: 34px; height: 34px; border-radius: 50%;
  border: none; padding: 0; cursor: pointer; z-index: 2;
  pointer-events: auto;
  background: conic-gradient(var(--brand) var(--p), rgba(128, 128, 128, .18) 0);
  display: grid; place-items: center;
  box-shadow: 0 4px 14px rgba(0, 0, 0, .18);
}
.xj-ring-core {
  width: 26px; height: 26px; border-radius: 50%;
  background: var(--surface, #fff); color: var(--brand-bright);
  font-size: 12px; font-weight: 800;
  display: grid; place-items: center;
}

/* ===== 小基气泡里的任务列表 ===== */
.xj-run-list { display: flex; flex-direction: column; gap: 7px; margin: 8px 0 4px; }
.xj-run-item {
  border: 1px solid var(--line-soft); border-radius: 10px;
  padding: 8px 9px;
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
}
[data-theme="light"] .xj-run-item { background: rgba(15, 23, 42, .03); }
.xj-run-top { display: flex; align-items: center; gap: 8px; }
.xj-run-title {
  flex: 1; min-width: 0; font-size: 11.5px; color: var(--text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.xj-run-pct { font-size: 11px; font-weight: 700; color: var(--brand-bright); font-variant-numeric: tabular-nums; }
.xj-run-bar { height: 4px; border-radius: 2px; overflow: hidden; background: rgba(128, 128, 128, .14); margin-top: 6px; }
.xj-run-bar span {
  display: block; height: 100%; border-radius: 2px;
  background: linear-gradient(90deg, var(--brand), var(--brand-bright));
  transition: width .4s ease;
}
.xj-run-stage { margin: 5px 0 6px; font-size: 10.5px; color: var(--text-muted); }
.xj-run-actions { display: flex; gap: 6px; }
.xj-run-actions button {
  font-family: inherit; font-size: 10.5px; font-weight: 600; cursor: pointer;
  padding: 3px 8px; border-radius: 6px;
  border: 1px solid color-mix(in srgb, var(--brand) 34%, transparent);
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  color: var(--brand-bright);
}
.xj-run-actions button.ghost {
  border-color: var(--border-color); background: transparent; color: var(--text-secondary);
}
.xj-run-actions button:disabled { opacity: .5; cursor: not-allowed; }
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

/* ===== 记忆流（2026-11-04）===== */
.xj-memory {
  margin-top: 8px; padding: 8px 9px 7px;
  border-radius: 11px;
  border: 1px solid color-mix(in srgb, var(--brand) 24%, transparent);
  background: color-mix(in srgb, var(--brand) 6%, transparent);
}
.xj-memory .xj-section-label { margin-top: 0; }
.xj-memory-jump {
  display: flex; align-items: stretch; gap: 7px; width: 100%;
  padding: 7px 8px; border-radius: 9px; text-align: left;
  border: 1px solid color-mix(in srgb, var(--brand) 30%, transparent);
  background: color-mix(in srgb, var(--surface, #ffffff) 55%, transparent);
  color: var(--text-primary); font-family: inherit; cursor: pointer;
  transition: all .18s ease;
}
.xj-memory-jump + .xj-memory-jump { margin-top: 5px; }
.xj-memory-jump:hover:not(:disabled) {
  border-color: color-mix(in srgb, var(--brand) 52%, transparent);
  background: color-mix(in srgb, var(--brand) 11%, transparent);
}
.xj-memory-jump:disabled { opacity: .55; cursor: wait; }
.xj-memory-ic {
  flex: none; width: 17px; font-size: 13px; line-height: 1.4;
  color: var(--brand-bright); text-align: center;
}
.xj-memory-body { display: flex; flex-direction: column; min-width: 0; }
.xj-memory-body b {
  font-size: 12px; font-weight: 700; line-height: 1.35;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.xj-memory-body em {
  margin-top: 1px; font-style: normal; font-size: 10.5px;
  color: var(--text-muted);
}
.xj-memory-route {
  margin-top: 6px; font-size: 10.5px; line-height: 1.55;
  color: var(--text-muted); word-break: break-word;
}
.xj-memory-msg { margin: 6px 0 0; font-size: 10.5px; line-height: 1.5; color: var(--brand-bright); }
.xj-memory-foot { display: flex; gap: 12px; margin-top: 6px; }
.xj-memory-foot button {
  padding: 0; border: none; background: none; cursor: pointer;
  font-family: inherit; font-size: 10.5px; color: var(--text-muted);
}
.xj-memory-foot button:hover { color: var(--brand-bright); }
.xj-memory-learned {
  margin-top: 9px; padding-top: 7px;
  border-top: 1px solid var(--line-soft, rgba(128, 128, 128, .18));
}
[data-theme="light"] .xj-memory-jump { background: rgba(255, 255, 255, .62); }

/* ===== 我的路线：编辑器 ===== */
.xj-route-steps { display: flex; flex-direction: column; gap: 5px; margin: 8px 0; }
.xj-route-step {
  display: flex; align-items: center; gap: 4px;
  padding: 5px 6px; border-radius: 8px;
  border: 1px solid var(--border-color);
  background: color-mix(in srgb, var(--surface, #ffffff) 55%, transparent);
}
.xj-route-no {
  flex: none; width: 16px; height: 16px; border-radius: 50%;
  display: grid; place-items: center;
  background: var(--brand); color: #fff; font-size: 9.5px; font-weight: 700;
}
.xj-route-name {
  flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; font-size: 11.5px; color: var(--text-primary);
}
.xj-route-mini {
  flex: none; width: 18px; height: 18px; padding: 0;
  border: none; border-radius: 4px; background: transparent;
  color: var(--text-muted); font-family: inherit; font-size: 11px; line-height: 1;
  cursor: pointer;
}
.xj-route-mini:hover:not(:disabled) {
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  color: var(--text-primary);
}
.xj-route-mini:disabled { opacity: .25; cursor: default; }
.xj-route-del:hover { color: #e6a23c; }
.xj-route-add { display: flex; gap: 5px; margin: 8px 0; }
.xj-route-select {
  flex: 1; min-width: 0; height: 28px; padding: 0 5px;
  border-radius: 7px; border: 1px solid var(--border-color);
  background: var(--surface, #ffffff); color: var(--text-primary);
  font-family: inherit; font-size: 11.5px;
}
.xj-route-addbtn {
  flex: none; padding: 0 9px; border-radius: 7px;
  border: 1px solid color-mix(in srgb, var(--brand) 30%, transparent);
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  color: var(--text-primary); font-family: inherit; font-size: 11.5px;
  cursor: pointer;
}
.xj-route-addbtn:hover:not(:disabled) {
  background: color-mix(in srgb, var(--brand) 16%, transparent);
}
.xj-route-addbtn:disabled { opacity: .45; cursor: default; }
.xj-route-delete { margin-top: 8px; text-align: right; }
.xj-route-delete button {
  padding: 0; border: none; background: none;
  color: var(--text-muted); font-family: inherit; font-size: 10.5px;
  cursor: pointer;
}
.xj-route-delete button:hover { color: #e6a23c; }
[data-theme="light"] .xj-route-step { background: rgba(255, 255, 255, .62); }

/* ===== 新会话「接着上次」小提示（只在头像上方露一次） ===== */
.xj-resume-chip {
  position: absolute; right: 0; bottom: calc(100% + 6px);
  pointer-events: auto; z-index: 2;
  display: flex; align-items: center; gap: 6px;
  max-width: 230px; padding: 6px 8px 6px 10px;
  border-radius: 999px; cursor: pointer;
  border: 1px solid color-mix(in srgb, var(--brand) 30%, transparent);
  background: color-mix(in srgb, var(--surface, #ffffff) 92%, transparent);
  color: var(--text-primary); font-family: inherit; font-size: 11.5px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, .14);
  backdrop-filter: blur(18px) saturate(1.3);
  animation: xj-chip-in .22s ease;
}
.xj-resume-chip:hover { border-color: color-mix(in srgb, var(--brand) 55%, transparent); }
/* 小基被拖到窗口顶部时，提示翻到下方，和气泡的翻转规则一致 */
.xj-resume-chip.below { bottom: auto; top: calc(100% + 6px); }
.xj-resume-text { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.xj-resume-x {
  flex: none; width: 16px; height: 16px; border-radius: 50%;
  display: grid; place-items: center;
  font-size: 12px; color: var(--text-muted);
}
.xj-resume-x:hover { background: color-mix(in srgb, var(--brand) 12%, transparent); color: var(--text-primary); }
@keyframes xj-chip-in {
  from { opacity: 0; transform: translateY(4px) scale(.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
[data-theme="dark"] .xj-resume-chip {
  background: color-mix(in srgb, var(--surface, #0f172a) 88%, transparent);
}
@media (max-width: 640px) {
  .xj-resume-chip { max-width: 200px; font-size: 11px; }
}

/* ===== 页面事件反应（2026-11-11）=====
   只报一句，不展开气泡；pointer-events: none 保证不挡页面点击。 */
.xj-reaction-chip {
  position: absolute; right: 0; bottom: calc(100% + 6px);
  pointer-events: none; z-index: 1;
  max-width: 220px; padding: 6px 10px;
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--brand) 26%, transparent);
  background: color-mix(in srgb, var(--surface, #ffffff) 92%, transparent);
  color: var(--text-primary);
  font-size: 11.5px; line-height: 1.5;
  box-shadow: 0 6px 18px rgba(0, 0, 0, .14);
  backdrop-filter: blur(18px) saturate(1.3);
  animation: xj-chip-in .18s ease;
}
.xj-reaction-chip.below { bottom: auto; top: calc(100% + 6px); }
/* 「接着上次」也在头像上方时，反应往上再叠一层，别互相盖住 */
.xj-reaction-chip.stacked { bottom: calc(100% + 44px); }
.xj-reaction-chip.stacked.below { bottom: auto; top: calc(100% + 44px); }
[data-theme="dark"] .xj-reaction-chip {
  background: color-mix(in srgb, var(--surface, #0f172a) 88%, transparent);
}
@media (max-width: 640px) {
  .xj-reaction-chip { max-width: 190px; font-size: 11px; }
}
@media (prefers-reduced-motion: reduce) {
  .xj-reaction-chip { animation: none; }
}

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
