<template>
  <!-- ===== 1. stages: 阶段式（保留，你认可的） ===== -->
  <div v-if="variant === 'stages'" class="ls-stages">
    <div v-for="(s, i) in stageList" :key="i" class="stage-row" :class="stageClass(i)">
      <div class="stage-dot">
        <span v-if="i < currentStage" class="stage-check">✓</span>
        <span v-else-if="i === currentStage" class="stage-active" />
        <span v-else class="stage-pending" />
      </div>
      <span class="stage-label">{{ s.label }}</span>
      <span v-if="i === currentStage && s.hint" class="stage-hint">{{ s.hint }}</span>
    </div>
    <div class="stage-line-track"><div class="stage-line-fill" :style="{ height: linePercent + '%' }" /></div>
  </div>

  <!-- ===== 2. typewriter: 打字机效果 ===== -->
  <div v-else-if="variant === 'typewriter'" class="ls-typewriter">
    <div class="tw-window">
      <div class="tw-header">
        <span class="tw-dot tw-dot-red" />
        <span class="tw-dot tw-dot-yellow" />
        <span class="tw-dot tw-dot-green" />
        <span class="tw-title">基智 AI</span>
      </div>
      <div class="tw-body">
        <div class="tw-lines">
          <div v-for="(line, i) in typedLines" :key="i" class="tw-line" :class="{ 'tw-cursor': i === typingLine }">
            <span class="tw-prefix">{{ i === 0 ? '> ' : '  ' }}</span>
            <span>{{ line }}</span>
            <span v-if="i === typingLine" class="tw-cursor-blink">▌</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ===== 3. constellation: 星座连线 ===== -->
  <div v-else-if="variant === 'constellation'" class="ls-constellation">
    <div class="cs-canvas">
      <svg viewBox="0 0 200 160" class="cs-svg">
        <!-- 连线 -->
        <line v-for="(edge, ei) in visibleEdges" :key="'e'+ei"
          :x1="edge.x1" :y1="edge.y1" :x2="edge.x2" :y2="edge.y2"
          class="cs-line" :class="{ 'cs-line-on': ei < connectedEdges }"
        />
        <!-- 星点 -->
        <circle v-for="(star, si) in stars" :key="'s'+si"
          :cx="star.x" :cy="star.y" r="3"
          class="cs-star" :class="{ 'cs-star-on': si < visibleStars, 'cs-star-core': si === visibleStars - 1 && si >= 0 }"
        />
      </svg>
    </div>
    <p class="cs-label">{{ currentTip }}</p>
  </div>

  <!-- ===== 4. orbit: 电子轨道 ===== -->
  <div v-else-if="variant === 'orbit'" class="ls-orbit">
    <div class="ob-atom" :style="{ width: size + 'px', height: size + 'px' }">
      <div class="ob-nucleus" />
      <div class="ob-ring ob-ring-1"><div class="ob-electron ob-e-1" /></div>
      <div class="ob-ring ob-ring-2"><div class="ob-electron ob-e-2" /></div>
      <div class="ob-ring ob-ring-3"><div class="ob-electron ob-e-3" /></div>
    </div>
    <p class="ls-text">{{ currentTip }}</p>
  </div>

  <!-- ===== 5. breathe: 呼吸形态 ===== -->
  <div v-else-if="variant === 'breathe'" class="ls-breathe">
    <div class="br-core">
      <div class="br-shape" />
      <div class="br-ring br-ring-1" />
      <div class="br-ring br-ring-2" />
      <div class="br-ring br-ring-3" />
    </div>
    <p class="ls-text">{{ currentTip }}</p>
  </div>

  <!-- ===== 6. cards: 卡片翻牌 ===== -->
  <div v-else-if="variant === 'cards'" class="ls-cards">
    <div class="cd-deck">
      <div v-for="i in 3" :key="i" class="cd-card" :class="{ 'cd-dealt': i <= dealtCards }" :style="{ animationDelay: (i-1)*0.25 + 's' }">
        <div class="cd-card-inner">
          <div class="cd-card-back"><span>?</span></div>
          <div class="cd-card-front"><span>{{ cardSymbols[i-1] }}</span></div>
        </div>
      </div>
    </div>
    <p class="ls-text">{{ currentTip }}</p>
  </div>

  <!-- ===== 7. pulse-ring: SVG 进度环 ===== -->
  <div v-else-if="variant === 'pulse-ring'" class="ls-pulse-ring">
    <div class="pr-container" :style="{ width: size + 'px', height: size + 'px' }">
      <svg class="pr-svg" viewBox="0 0 100 100">
        <defs>
          <linearGradient id="pr-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#4a6cf7" />
            <stop offset="100%" stop-color="#a78bfa" />
          </linearGradient>
        </defs>
        <circle class="pr-track" cx="50" cy="50" r="42" />
        <circle class="pr-fill" cx="50" cy="50" r="42"
          :stroke-dasharray="dashArray" :stroke-dashoffset="dashOffset" />
      </svg>
      <div class="pr-center">
        <span class="pr-count">{{ displayCount }}</span>
        <span v-if="text" class="pr-label">{{ text }}</span>
      </div>
    </div>
  </div>

  <!-- ===== 8. dots: 跳动点 + 文字轮换 ===== -->
  <div v-else-if="variant === 'dots'" class="ls-dots-tip">
    <div class="dt-dots"><span v-for="i in 3" :key="i" /></div>
    <p class="dt-tip">{{ currentTip }}</p>
  </div>

  <!-- ===== 9. flow: 进度条（保留作简单场景） ===== -->
  <div v-else-if="variant === 'flow'" class="ls-flow">
    <div class="flow-bar-wrap">
      <div class="flow-bar"><div class="flow-fill" :style="{ width: flowProgress + '%' }"><div class="flow-shine" /></div></div>
      <span class="flow-percent">{{ flowProgress }}%</span>
    </div>
    <p class="flow-tip">{{ currentTip }}</p>
  </div>

  <!-- ===== 10. ring: 双环 ===== -->
  <div v-else class="ls-ring">
    <div class="ring-spinner" :style="{ width: size + 'px', height: size + 'px' }">
      <div class="ring-outer" /><div class="ring-inner" /><div class="ring-core" />
    </div>
    <p v-if="text" class="ls-text">{{ text }}</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  variant: { type: String, default: 'ring' },
  text: { type: String, default: '' },
  size: { type: Number, default: 80 },
  stages: { type: Array, default: () => [
    { label: '准备数据', hint: '正在连接服务...' },
    { label: '分析处理', hint: '正在计算指标...' },
    { label: '生成内容', hint: '正在渲染页面...' },
    { label: '完成加载', hint: '' },
  ]},
  stageDuration: { type: Number, default: 800 },
  flowSteps: { type: Array, default: () => ['正在连接服务...', '正在读取数据...', '正在分析处理...', '正在渲染页面...'] },
  flowSpeed: { type: Number, default: 40 },
  countEnd: { type: Number, default: 100 },
  countSpeed: { type: Number, default: 30 },
})

// ===== stages =====
const currentStage = ref(0)
const stageTimer = ref(null)
const stageList = computed(() => props.stages)
const stageClass = (i) => ({ 'stage-done': i < currentStage.value, 'stage-now': i === currentStage.value, 'stage-wait': i > currentStage.value })
const linePercent = computed(() => {
  const t = stageList.value.length - 1
  return t <= 0 ? 0 : Math.min(100, (currentStage.value / t) * 100)
})

// ===== flow =====
const flowProgress = ref(0)
const flowTimer = ref(null)

// ===== typewriter =====
const typedLines = ref([])
const typingLine = ref(0)
const twTimer = ref(null)
const twContent = ref([])

// ===== constellation =====
const stars = [
  { x: 100, y: 20 }, { x: 30, y: 50 }, { x: 170, y: 50 },
  { x: 50, y: 100 }, { x: 150, y: 100 }, { x: 20, y: 140 },
  { x: 100, y: 145 }, { x: 180, y: 140 },
]
const edges = [
  { x1: 100, y1: 20, x2: 30, y2: 50 }, { x1: 100, y1: 20, x2: 170, y2: 50 },
  { x1: 30, y1: 50, x2: 50, y2: 100 }, { x1: 170, y1: 50, x2: 150, y2: 100 },
  { x1: 50, y1: 100, x2: 20, y2: 140 }, { x1: 50, y1: 100, x2: 100, y2: 145 },
  { x1: 150, y1: 100, x2: 100, y2: 145 }, { x1: 150, y1: 100, x2: 180, y2: 140 },
]
const visibleStars = ref(0)
const visibleEdges = ref(0)
const connectedEdges = ref(0)
const csTimer = ref(null)

// ===== orbit =====
// (纯 CSS 动画，JS 只控制文字轮换)

// ===== breathe =====
// (纯 CSS 动画)

// ===== cards =====
const dealtCards = ref(0)
const cardSymbols = ['📖', '🧠', '✨']
const cdTimer = ref(null)

// ===== pulse-ring =====
const displayCount = ref(0)
const countTimer = ref(null)
const circumference = 2 * Math.PI * 42
const dashArray = computed(() => circumference)
const dashOffset = computed(() => circumference - (displayCount.value / 100) * circumference)

// ===== 共用文字轮换 =====
const currentTip = ref('')
const tipTimer = ref(null)

onMounted(() => {
  switch (props.variant) {
    case 'stages': startStages(); break
    case 'flow': startFlow(); break
    case 'typewriter': startTypewriter(); break
    case 'constellation': startConstellation(); break
    case 'orbit': startTips(); break
    case 'breathe': startTips(); break
    case 'cards': startCards(); break
    case 'pulse-ring': startPulseRing(); break
    case 'dots': startTips(); break
  }
})

onUnmounted(() => clearAllTimers())
watch(() => props.variant, (v, old) => {
  clearAllTimers()
  currentStage.value = 0; flowProgress.value = 0; displayCount.value = 0
  dealtCards.value = 0; visibleStars.value = 0; visibleEdges.value = 0; connectedEdges.value = 0
  typedLines.value = []; typingLine.value = 0
  if (v !== old) onMounted()
})

// ---- stages ----
function startStages() {
  const total = stageList.value.length
  stageTimer.value = setInterval(() => { if (currentStage.value < total - 1) currentStage.value++ }, props.stageDuration)
}

// ---- flow ----
function startFlow() {
  currentTip.value = props.flowSteps[0] || ''
  let ti = 0
  flowTimer.value = setInterval(() => {
    if (flowProgress.value < 95) { flowProgress.value += Math.random() * 15 + 3; if (flowProgress.value > 95) flowProgress.value = 95 }
  }, props.flowSpeed + 200)
  tipTimer.value = setInterval(() => { ti = (ti + 1) % props.flowSteps.length; currentTip.value = props.flowSteps[ti] }, props.flowSpeed * 5)
}

// ---- typewriter ----
function startTypewriter() {
  twContent.value = props.flowSteps && props.flowSteps.length ? props.flowSteps : ['正在分析数据...', '正在匹配模式...', '正在生成结果...']
  typedLines.value = ['']
  typingLine.value = 0
  let charIdx = 0
  const line = twContent.value[0]

  twTimer.value = setInterval(() => {
    if (charIdx < line.length) {
      typedLines.value[0] = line.substring(0, charIdx + 1)
      charIdx++
    } else {
      // 当前行打完，换下一行
      if (typingLine.value < twContent.value.length - 1) {
        typingLine.value++
        typedLines.value.push('')
        charIdx = 0
      } else {
        clearInterval(twTimer.value)
        typedLines.value[typedLines.value.length] = '✓ 完成'
        typingLine.value = -1
      }
    }
  }, 80 + Math.random() * 80) // 随机速度模拟真人打字
}

// ---- constellation ----
function startConstellation() {
  currentTip.value = '正在探索知识星空...'
  let step = 0
  const maxStep = stars.length + edges.length + 3 // stars appear, then edges connect, then pause

  csTimer.value = setInterval(() => {
    step++
    if (step <= stars.length) {
      // 星点逐个出现
      visibleStars.value = step
    } else if (step <= stars.length + edges.length) {
      // 连线逐个出现
      visibleEdges.value = step - stars.length
      // 核心星点（最后出现的）pulse
    } else if (step <= stars.length + edges.length + 1) {
      // 所有连线亮起
      connectedEdges.value = edges.length
      currentTip.value = '星座已连接，正在解读...'
    } else if (step >= maxStep) {
      // 循环
      step = 0; visibleStars.value = 0; visibleEdges.value = 0; connectedEdges.value = 0
      currentTip.value = '正在探索知识星空...'
    }
  }, 400)
}

// ---- cards ----
function startCards() {
  const tips = (props.flowSteps && props.flowSteps.length >= 3)
    ? props.flowSteps
    : ['正在整理信息...', '正在核对数据...', '准备就绪！']
  currentTip.value = tips[0]
  cdTimer.value = setInterval(() => {
    if (dealtCards.value < 3) {
      dealtCards.value++
      currentTip.value = tips[dealtCards.value - 1]
    } else {
      clearInterval(cdTimer.value)
    }
  }, 600)
}

// ---- pulse-ring ----
function startPulseRing() {
  const step = Math.max(1, Math.floor(props.countEnd / (2000 / props.countSpeed)))
  countTimer.value = setInterval(() => {
    if (displayCount.value < props.countEnd) displayCount.value = Math.min(props.countEnd, displayCount.value + step)
  }, props.countSpeed)
}

// ---- 共用文字轮换 ----
function startTips() {
  const tips = props.flowSteps || ['加载中...']
  currentTip.value = tips[0]
  let i = 0
  tipTimer.value = setInterval(() => { i = (i + 1) % tips.length; currentTip.value = tips[i] }, 1500)
}

function clearAllTimers() {
  [stageTimer, flowTimer, twTimer, csTimer, cdTimer, countTimer, tipTimer].forEach(t => {
    if (t.value) { clearInterval(t.value); t.value = null }
  })
}

defineExpose({
  advanceStage() { if (currentStage.value < stageList.value.length - 1) currentStage.value++ },
  setFlowProgress(v) { flowProgress.value = Math.min(100, Math.max(0, v)) },
  complete() {
    currentStage.value = stageList.value.length - 1; flowProgress.value = 100
    displayCount.value = props.countEnd; dealtCards.value = 3
  },
})
</script>

<style scoped>
/* ===== 通用 ===== */
.ls-text { margin: 0; font-size: 14px; color: var(--text-muted); animation: text-fade 2s ease-in-out infinite; }
@keyframes text-fade { 0%,100%{opacity:.4} 50%{opacity:1} }

/* ============================================================
   1. stages 阶段式
   ============================================================ */
.ls-stages { position: relative; display: flex; flex-direction: column; gap: 20px; padding: 8px 0 8px 48px; }
.stage-line-track { position: absolute; left: 19px; top: 16px; bottom: 16px; width: 2px; background: rgba(255,255,255,.06); border-radius: 1px; overflow: hidden; }
.stage-line-fill { width: 100%; background: linear-gradient(180deg, #4a6cf7, #6c8cff); border-radius: 1px; transition: height .6s cubic-bezier(.4,0,.2,1); }
.stage-row { display: flex; align-items: center; gap: 12px; position: relative; z-index: 1; }
.stage-dot { width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: all .4s ease; }
.stage-done .stage-dot { background: rgba(74,108,247,.2); border: 2px solid #4a6cf7; }
.stage-check { color: #4a6cf7; font-size: 12px; font-weight: bold; }
.stage-done .stage-label { color: var(--text-secondary); }
.stage-now .stage-dot { background: rgba(74,108,247,.15); border: 2px solid #6c8cff; }
.stage-active { width: 10px; height: 10px; border-radius: 50%; background: #6c8cff; box-shadow: 0 0 12px rgba(74,108,247,.6); animation: active-blink .8s ease-in-out infinite; }
@keyframes active-blink { 0%,100%{opacity:.4;transform:scale(.8)} 50%{opacity:1;transform:scale(1.1)} }
.stage-now .stage-label { color: #6c8cff; font-weight: 600; font-size: 15px; }
.stage-hint { font-size: 12px; color: var(--text-muted); margin-left: 4px; animation: text-fade 1.5s ease-in-out infinite; }
.stage-wait .stage-dot { background: transparent; border: 2px solid rgba(255,255,255,.08); }
.stage-pending { width: 6px; height: 6px; border-radius: 50%; background: rgba(255,255,255,.1); }
.stage-wait .stage-label { color: rgba(255,255,255,.2); }

/* ============================================================
   2. typewriter 打字机
   ============================================================ */
.ls-typewriter { padding: 8px 0; }
.tw-window { background: rgba(0,0,0,.35); border: 1px solid rgba(255,255,255,.08); border-radius: 10px; overflow: hidden; min-width: 300px; max-width: 420px; box-shadow: 0 8px 32px rgba(0,0,0,.3); }
.tw-header { display: flex; align-items: center; gap: 6px; padding: 10px 14px; background: rgba(255,255,255,.03); border-bottom: 1px solid rgba(255,255,255,.05); }
.tw-dot { width: 10px; height: 10px; border-radius: 50%; }
.tw-dot-red { background: #ff5f57; }
.tw-dot-yellow { background: #febc2e; }
.tw-dot-green { background: #28c840; }
.tw-title { margin-left: 8px; font-size: 12px; color: var(--text-muted); letter-spacing: .5px; }
.tw-body { padding: 14px 16px; font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace; font-size: 13px; line-height: 1.8; color: #a8d8a8; min-height: 80px; }
.tw-line { display: flex; }
.tw-prefix { color: #6c8cff; margin-right: 4px; flex-shrink: 0; }
.tw-cursor-blink { animation: cursor-blink .8s step-end infinite; color: #6c8cff; }
@keyframes cursor-blink { 0%,100%{opacity:1} 50%{opacity:0} }

/* ============================================================
   3. constellation 星座连线
   ============================================================ */
.ls-constellation { display: flex; flex-direction: column; align-items: center; gap: 16px; padding: 12px; }
.cs-canvas { width: 200px; height: 160px; }
.cs-svg { width: 100%; height: 100%; }
.cs-star { fill: rgba(255,255,255,.08); transition: all .5s ease; }
.cs-star-on { fill: rgba(200,210,255,.7); filter: drop-shadow(0 0 4px rgba(140,160,255,.5)); }
.cs-star-core { fill: #fff; filter: drop-shadow(0 0 8px rgba(140,180,255,.8)); animation: star-pulse 1.2s ease-in-out infinite; }
@keyframes star-pulse { 0%,100%{r:3;opacity:.8} 50%{r:4.5;opacity:1} }
.cs-line { stroke: rgba(255,255,255,.03); stroke-width: 1; transition: all .6s ease; }
.cs-line-on { stroke: rgba(140,180,255,.4); stroke-width: 1.5; filter: drop-shadow(0 0 3px rgba(140,160,255,.3)); }
.cs-label { margin: 0; font-size: 13px; color: var(--text-muted); animation: text-fade 2s ease-in-out infinite; }

/* ============================================================
   4. orbit 电子轨道
   ============================================================ */
.ls-orbit { display: flex; flex-direction: column; align-items: center; gap: 20px; padding: 20px; }
.ob-atom { position: relative; display: flex; align-items: center; justify-content: center; }
.ob-nucleus { width: 14px; height: 14px; border-radius: 50%; background: radial-gradient(circle, #a78bfa, #4a6cf7); box-shadow: 0 0 20px rgba(74,108,247,.6), 0 0 40px rgba(74,108,247,.2); animation: nucleus-pulse 2s ease-in-out infinite; }
@keyframes nucleus-pulse { 0%,100%{transform:scale(1);box-shadow:0 0 20px rgba(74,108,247,.6)} 50%{transform:scale(1.2);box-shadow:0 0 35px rgba(74,108,247,.9)} }
.ob-ring { position: absolute; inset: 0; border: 1px solid rgba(255,255,255,.06); border-radius: 50%; }
.ob-ring-1 { animation: orbit-spin 3s linear infinite; }
.ob-ring-2 { animation: orbit-spin 4s linear infinite reverse; transform: rotateX(60deg); }
.ob-ring-3 { animation: orbit-spin 5s linear infinite; transform: rotateX(-60deg); }
@keyframes orbit-spin { to { transform: rotate(360deg); } }
.ob-ring-2 { animation: orbit-spin-2 4s linear infinite; }
@keyframes orbit-spin-2 { to { transform: rotateX(60deg) rotate(360deg); } }
.ob-ring-3 { animation: orbit-spin-3 5s linear infinite; }
@keyframes orbit-spin-3 { to { transform: rotateX(-60deg) rotate(360deg); } }
.ob-electron { width: 6px; height: 6px; border-radius: 50%; background: #6c8cff; box-shadow: 0 0 8px rgba(108,140,255,.7); position: absolute; top: -3px; left: 50%; margin-left: -3px; }

/* ============================================================
   5. breathe 呼吸形态
   ============================================================ */
.ls-breathe { display: flex; flex-direction: column; align-items: center; gap: 28px; padding: 24px; }
.br-core { position: relative; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; }
.br-shape { width: 24px; height: 24px; background: linear-gradient(135deg, #4a6cf7, #a78bfa); animation: shape-morph 4s ease-in-out infinite; }
@keyframes shape-morph {
  0%   { border-radius: 50%; transform: scale(1) rotate(0deg); }
  25%  { border-radius: 30%; transform: scale(1.3) rotate(45deg); }
  50%  { border-radius: 4px; transform: scale(1) rotate(90deg); }
  75%  { border-radius: 30%; transform: scale(1.3) rotate(135deg); }
  100% { border-radius: 50%; transform: scale(1) rotate(180deg); }
}
.br-ring { position: absolute; inset: 0; border: 1px solid rgba(74,108,247,.15); border-radius: 50%; animation: br-expand 2s ease-out infinite; }
.br-ring-1 { animation-delay: 0s; }
.br-ring-2 { animation-delay: .6s; }
.br-ring-3 { animation-delay: 1.2s; }
@keyframes br-expand { 0%{transform:scale(.6);opacity:.6} 100%{transform:scale(2.5);opacity:0} }

/* ============================================================
   6. cards 卡片翻牌
   ============================================================ */
.ls-cards { display: flex; flex-direction: column; align-items: center; gap: 20px; padding: 16px; }
.cd-deck { display: flex; gap: 12px; perspective: 800px; }
.cd-card { width: 52px; height: 72px; opacity: 0; transform: translateY(20px) rotateY(90deg); transition: all .5s cubic-bezier(.34,1.56,.64,1); }
.cd-card.cd-dealt { opacity: 1; transform: translateY(0) rotateY(0); }
.cd-card-inner { width: 100%; height: 100%; position: relative; transform-style: preserve-3d; animation: card-flip .6s ease-out forwards; }
.cd-card.cd-dealt .cd-card-inner { animation: none; }
.cd-card-back, .cd-card-front { position: absolute; inset: 0; border-radius: 8px; display: flex; align-items: center; justify-content: center; backface-visibility: hidden; }
.cd-card-back { background: linear-gradient(135deg, rgba(74,108,247,.3), rgba(108,140,255,.15)); border: 1px solid rgba(108,140,255,.2); }
.cd-card-back span { font-size: 22px; color: rgba(255,255,255,.3); font-weight: bold; }
.cd-card-front { background: linear-gradient(135deg, rgba(74,108,247,.4), rgba(167,139,250,.3)); border: 1px solid rgba(167,139,250,.3); transform: rotateY(180deg); }
.cd-card-front span { font-size: 22px; }
@keyframes card-flip { 0%{transform:rotateY(0)} 100%{transform:rotateY(180deg)} }

/* ============================================================
   7. pulse-ring SVG 进度环
   ============================================================ */
.ls-pulse-ring { display: flex; flex-direction: column; align-items: center; gap: 12px; }
.pr-container { position: relative; flex-shrink: 0; }
.pr-svg { transform: rotate(-90deg); width: 100%; height: 100%; }
.pr-track { fill: none; stroke: rgba(255,255,255,.06); stroke-width: 4; }
.pr-fill { fill: none; stroke: url(#pr-grad); stroke-width: 4; stroke-linecap: round; transition: stroke-dashoffset .3s ease; }
.pr-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.pr-count { font-size: 24px; font-weight: 700; color: #6c8cff; font-variant-numeric: tabular-nums; line-height: 1; }
.pr-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

/* ============================================================
   8. dots 跳动点
   ============================================================ */
.ls-dots-tip { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 16px; }
.dt-dots { display: flex; gap: 6px; align-items: center; }
.dt-dots span { width: 10px; height: 10px; border-radius: 50%; background: var(--text-muted); animation: dot-bounce 1.4s ease-in-out infinite both; }
.dt-dots span:nth-child(1){animation-delay:-.32s} .dt-dots span:nth-child(2){animation-delay:-.16s} .dt-dots span:nth-child(3){animation-delay:0s}
@keyframes dot-bounce { 0%,80%,100%{transform:scale(.4);opacity:.3} 40%{transform:scale(1);opacity:1} }
.dt-tip { margin: 0; font-size: 13px; color: var(--text-muted); animation: text-fade 2s ease-in-out infinite; }

/* ============================================================
   9. flow 进度条
   ============================================================ */
.ls-flow { display: flex; flex-direction: column; align-items: center; gap: 16px; padding: 24px 32px; min-width: 280px; }
.flow-bar-wrap { display: flex; align-items: center; gap: 12px; width: 100%; }
.flow-bar { flex: 1; height: 8px; background: rgba(255,255,255,.05); border-radius: 8px; overflow: hidden; }
.flow-fill { height: 100%; border-radius: 8px; background: linear-gradient(90deg,#4a6cf7,#6c8cff 40%,#a78bfa 80%); background-size: 200% 100%; animation: flow-gradient 2s linear infinite; transition: width .4s ease; position: relative; overflow: hidden; }
@keyframes flow-gradient { 0%{background-position:200% 0} 100%{background-position:0 0} }
.flow-shine { position: absolute; right: 0; top: 0; width: 20px; height: 100%; background: linear-gradient(90deg,transparent,rgba(255,255,255,.6)); border-radius: 0 8px 8px 0; animation: shine-pulse 1s ease-in-out infinite; }
@keyframes shine-pulse { 0%,100%{opacity:.3} 50%{opacity:1} }
.flow-percent { font-size: 18px; font-weight: 700; color: #6c8cff; min-width: 42px; text-align: right; font-variant-numeric: tabular-nums; }
.flow-tip { margin: 0; font-size: 13px; color: var(--text-muted); animation: text-fade 2s ease-in-out infinite; }

/* ============================================================
   10. ring 双环
   ============================================================ */
.ls-ring { display: flex; flex-direction: column; align-items: center; gap: 16px; padding: 40px 20px; }
.ring-spinner { position: relative; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.ring-outer { position: absolute; inset: 0; border: 2px solid transparent; border-top-color: #4a6cf7; border-right-color: rgba(74,108,247,.3); border-radius: 50%; animation: ring-spin 1.2s linear infinite; }
.ring-inner { position: absolute; inset: 8px; border: 2px solid transparent; border-bottom-color: rgba(108,140,255,.6); border-left-color: rgba(108,140,255,.2); border-radius: 50%; animation: ring-spin 1.8s linear infinite reverse; }
.ring-core { width: 30%; height: 30%; background: radial-gradient(circle,#4a6cf7,rgba(74,108,247,.4)); border-radius: 50%; box-shadow: 0 0 16px rgba(74,108,247,.5); animation: core-pulse 1.5s ease-in-out infinite; }
@keyframes ring-spin { to{transform:rotate(360deg)} }
@keyframes core-pulse { 0%,100%{transform:scale(.9);opacity:.6} 50%{transform:scale(1.15);opacity:1} }
</style>
