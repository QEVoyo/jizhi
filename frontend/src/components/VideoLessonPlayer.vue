<template>
  <!-- 模板化讲解播放器（2026-09-05 重写呈现管线：
       画面无条件立即渲染——不再用全屏遮罩盖住画面，加载/出错/被拦全部改为
       画面之上的角标/横幅/半透明层；舞台高度用 padding-top 兜底，不依赖
       aspect-ratio；不依赖 canplay 才退场。彻底消除「有声音没画面」类故障） -->
  <div class="vlp" :class="['tpl-' + tplKey, { playing, exporting }]">
    <!-- 舞台：视觉模板（16:9 由 .vlp-frame padding-top 保证，任何浏览器都有高度） -->
    <div class="vlp-frame">
      <div ref="stageRef" class="vlp-stage" :class="['mood-' + curMood, bgClass, 'skin-' + activeSkin]">
        <div class="vlp-stage-bg"></div>

        <!-- 模板一：板书流 chalkboard（旧版 sections 脚本） -->
        <template v-if="!isStoryboard && tplKey === 'chalkboard'">
          <div class="vlp-board">
            <div class="vlp-board-topline">
              <span class="vlp-sec-chip">{{ MOOD_LABELS[curMood] }} · {{ secIndex + 1 }}/{{ sections.length }}</span>
              <span class="vlp-board-dots">
                <i v-for="(s, i) in sections" :key="i" :class="{ on: i === secIndex, done: i < secIndex }"></i>
              </span>
            </div>
            <transition name="vlp-head-pop" mode="out-in">
              <div :key="secIndex" class="vlp-board-title">
                <span>{{ section.heading }}</span>
                <i class="vlp-board-underline"></i>
              </div>
            </transition>
            <div class="vlp-board-lines">
              <div v-for="(line, i) in section.lines" :key="secIndex + '-' + i"
                   class="vlp-chalk-line"
                   :class="{ on: i === activeLine, done: i < activeLine }"
                   v-if="lineVisible(i)">
                <b>{{ '①②③④⑤'[i] || '·' }}</b>
                <span class="vlp-tw">
                  <template v-if="lineFullyTyped(i)">
                    <span v-for="(p, pi) in lineParts(line)" :key="pi" :class="{ 'vlp-kw': p.kw }">{{ p.t }}</span>
                  </template>
                  <template v-else>
                    <span class="vlp-tw-visible">{{ line.slice(0, typedCount(i)) }}</span>
                    <span class="vlp-tw-hidden">{{ line.slice(typedCount(i)) }}</span>
                  </template>
                  <i v-if="i === activeLine && playing" class="vlp-caret"></i>
                </span>
              </div>
            </div>
            <div class="vlp-board-foot">—— 基智自营视频库 · {{ anglName }} ——</div>
          </div>
        </template>

        <!-- 模板二：卡片流 cards（旧版 sections 脚本） -->
        <template v-else-if="!isStoryboard">
          <div class="vlp-cards">
            <transition name="vlp-card" mode="out-in">
              <div :key="secIndex" class="vlp-card">
                <div class="vlp-card-head">
                  {{ section.heading }}
                  <span class="vlp-card-sec">{{ secIndex + 1 }} / {{ sections.length }}</span>
                </div>
                <div class="vlp-card-lines">
                  <div v-for="(line, i) in section.lines" :key="i"
                       class="vlp-card-line"
                       :class="{ on: i === activeLine }"
                       v-if="lineVisible(i)">
                    <i class="vlp-card-bullet"></i>
                    <span class="vlp-tw">
                      <template v-if="lineFullyTyped(i)">
                        <span v-for="(p, pi) in lineParts(line)" :key="pi" :class="{ 'vlp-kw': p.kw }">{{ p.t }}</span>
                      </template>
                      <template v-else>
                        <span class="vlp-tw-visible">{{ line.slice(0, typedCount(i)) }}</span>
                        <span class="vlp-tw-hidden">{{ line.slice(typedCount(i)) }}</span>
                      </template>
                    </span>
                  </div>
                </div>
                <div class="vlp-card-dots">
                  <i v-for="(s, i) in sections" :key="i" :class="{ on: i === secIndex, done: i < secIndex }"></i>
                </div>
              </div>
            </transition>
          </div>
        </template>

        <!-- 分镜演出台（画面主体 = 图形演示构件，文字只做批注） -->
        <div v-else class="vlp-storyboard">
          <!-- 钩子屏（首个镜头前） -->
          <transition name="vlp-fade">
            <div v-if="showStoryHook" class="sb-hook">
              <span class="sb-hook-q">{{ script.hook || '' }}</span>
            </div>
          </transition>

          <template v-if="!showStoryHook && scene">
            <!-- point：文字批注 -->
            <div v-if="widgetKind === 'point'" class="sb-point">
              <span class="sb-point-text" :style="{ opacity: Math.min(1, sceneProgress * 3) }">{{ wParams.text || '讲解要点' }}</span>
            </div>

            <!-- array：数组演示（真·演示动画：指针连续滑行 / 数字飞出相加 / 和值滚动 / 判定批注） -->
            <div v-else-if="widgetKind === 'array'" class="sb-array">
              <div v-if="wParams.title" class="sb-caption">{{ wParams.title }}</div>
              <div class="sb-cells">
                <span v-for="(v, i) in (wParams.values || [])" :key="i" class="sb-cell"
                      :class="{ path: alongPath(i), l: i === framePair.l, r: i === framePair.r, hit: hitCells(i) }"
                      :style="{ '--delay': trailDelay(i) + 's' }">{{ v }}</span>
              </div>
              <div class="sb-stage-line">
                <div class="sb-pointer l" :style="{ left: cellXf(lerped.l).toFixed(1) + '%' }">
                  <span class="sp-label">左指针</span>
                  <span class="sp-stem"></span>
                  <span class="sp-head"></span>
                </div>
                <div class="sb-pointer r" :style="{ left: cellXf(lerped.r).toFixed(1) + '%' }">
                  <span class="sp-label">右指针</span>
                  <span class="sp-stem"></span>
                  <span class="sp-head"></span>
                </div>
              </div>
              <!-- 相加气泡：两个数字从格子飞出，+ 号按下，和值滚动，与目标比较 -->
              <transition name="vlp-fade">
                <div v-if="showCompute" class="sb-compute" :class="{ good: isSumHit, bad: verTarg === 'big' }">
                  <span class="sb-num l">{{ framePair.lv }}</span>
                  <span class="sb-plus">+</span>
                  <span class="sb-num r">{{ framePair.rv }}</span>
                  <span class="sb-eq">=</span>
                  <span class="sb-sum">{{ rolledSum }}</span>
                  <span class="sb-verdict">{{ verdictText }}</span>
                </div>
              </transition>
              <div class="sb-note-row">
                <div v-if="curMove.note" class="sb-note" :class="{ good: isHitNote(curMove.note) }">{{ curMove.note }}</div>
                <div v-if="wParams.target !== undefined" class="sb-target">目标 {{ wParams.target }}</div>
              </div>
            </div>

            <!-- balance：易错对比 -->
            <div v-else-if="widgetKind === 'balance'" class="sb-balance">
              <div class="sb-bal">
                <div class="sb-bal-left" :class="{ dodge: sceneProgress > 0.55 }">
                  <div class="sb-bal-title">{{ (wParams.left || {}).title }}</div>
                  <div v-for="(l, i) in ((wParams.left || {}).lines || [])" :key="i" class="sb-bal-line">{{ l }}</div>
                  <span class="sb-stamp bad">✗</span>
                </div>
                <span class="sb-bal-vs">VS</span>
                <div class="sb-bal-right" :class="{ win: sceneProgress > 0.55 }">
                  <div class="sb-bal-title">{{ (wParams.right || {}).title }}</div>
                  <div v-for="(l, i) in ((wParams.right || {}).lines || [])" :key="i" class="sb-bal-line">{{ l }}</div>
                  <span class="sb-stamp ok">✓</span>
                </div>
              </div>
            </div>

            <!-- example：例题演算台 -->
            <div v-else-if="widgetKind === 'example'" class="sb-example">
              <div class="sb-ex-stem">{{ wParams.stem }}</div>
              <div class="sb-ex-work">
                <div v-for="(w, i) in (wParams.work || []).slice(0, workReveal)" :key="i" class="sb-ex-step"
                     :class="{ last: i === workReveal - 1 }">{{ w }}</div>
              </div>
              <transition name="vlp-stamp-in">
                <div v-if="sceneProgress > 0.88 && wParams.answer" class="sb-ex-answer">
                  <b>{{ wParams.answer }}</b>
                </div>
              </transition>
            </div>

            <!-- phrase：收束金句 -->
            <div v-else-if="widgetKind === 'phrase'" class="sb-phrase">
              <span v-for="(c, i) in String(wParams.text || '').split('')" :key="i" class="sb-phrase-char"
                    :style="{ opacity: sceneProgress * 8 > i * 0.35 ? 1 : 0.15, transform: (sceneProgress * 8 > i * 0.35 ? '' : 'translateY(10px)') }">{{ c }}</span>
            </div>
          </template>
        </div>

        <!-- 生成主（作者）chip（片头期间隐藏，让位标题屏） -->
        <div v-if="video.author_name && !showIntro" class="vlp-author" :title="'生成主：' + video.author_name">
          <img v-if="video.author_avatar" :src="video.author_avatar" alt="" @error="e => e.target.style.display = 'none'" />
          <span>{{ video.author_name }}</span>
        </div>

        <!-- 片头标题屏（像视频的开场卡） -->
        <transition name="vlp-fade">
          <div v-if="showIntro" class="vlp-intro" :class="'tpl-' + tplKey">
            <div class="vlp-intro-tag">基智自营视频库 · {{ anglName }}</div>
            <h1>{{ video.title || video.knowledge_name }}</h1>
            <div class="vlp-intro-sub">
              <img v-if="video.author_avatar" :src="video.author_avatar" alt="" />
              {{ video.author_name || '基智' }} 出品
            </div>
          </div>
        </transition>

        <!-- 片尾小结屏（最后 3.2s：金句回放 + 收尾） -->
        <transition name="vlp-fade">
          <div v-if="showOutro" class="vlp-outro" :class="'tpl-' + tplKey">
            <div class="vlp-outro-title">本节小结</div>
            <div class="vlp-outro-lines">
              <div v-for="(l, i) in outroLines" :key="i">{{ l }}</div>
            </div>
            <div class="vlp-outro-foot">基智 · 让每个知识点讲得清</div>
          </div>
        </transition>

        <div class="vlp-letterbox top"></div>
        <div class="vlp-letterbox bot"></div>
        <div class="vlp-vignette"></div>
        <div class="vlp-grain"></div>

        <!-- 句级字幕（单行大字） -->
        <div v-if="subs.length" class="vlp-subs">
          <div class="sub-line cur">
            <span class="sub-cur-text">{{ currentSubChars }}</span>
          </div>
        </div>

        <!-- 加载角标：画面永远可见，音轨预热只在右下角说明（2026-09-05 重写） -->
        <transition name="vlp-fade">
          <div v-if="!audioReady && !audioError" class="vlp-load-pill">
            <span class="vlp-load-spin"></span>
            <span>讲解音频准备中…</span>
          </div>
        </transition>

        <!-- 音轨出错横幅：不盖画面，提示 + 重试（2026-09-05 重写） -->
        <transition name="vlp-fade">
          <div v-if="audioError" class="vlp-audio-banner">
            <span class="vlp-err-ico">!</span>
            <div class="vlp-err-text">
              <b>音轨加载失败</b>
              <i>网络可能不太稳定，检查网络后重试</i>
            </div>
            <button class="vlp-retry" @click.stop="retryAudio">↻ 重新加载</button>
          </div>
        </transition>

        <!-- 自动播放被拦：半透明大播钮，画面仍可见（2026-09-05 重写） -->
        <transition name="vlp-fade">
          <div v-if="blocked && !audioError" class="vlp-blocked" @click="startByTap">
            <button class="vlp-big-play">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
            </button>
            <div class="vlp-blocked-text">点击开始讲解</div>
          </div>
        </transition>

        <!-- 缓冲角标 -->
        <transition name="vlp-fade">
          <div v-if="buffering && audioReady && !audioError" class="vlp-buff">
            <span class="vlp-buff-spin"></span>缓冲中…
          </div>
        </transition>

        <!-- 视频导出进度（2026-09-05：画面+声音合成 webm） -->
        <div v-if="exporting" class="vlp-exporting">
          <span class="vlp-exporting-spin"></span>
          🎬 正在导出视频 {{ exportPct }}%
        </div>
      </div>
    </div>

    <!-- 控制条（2026-09-05 改名 vlp-ctlbar，与骨架条类名解耦） -->
    <div class="vlp-ctlbar">
      <button class="vlp-btn play" @click="toggle" :title="playing ? '暂停' : '播放'">
        <svg v-if="!playing" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
        <svg v-else viewBox="0 0 24 24" fill="currentColor"><path d="M7 5h4v14H7zM13 5h4v14h-4z"/></svg>
      </button>
      <div class="vlp-progress" @click="seek">
        <i :style="{ width: pct + '%' }"></i>
        <span v-for="(s, i) in sections" :key="i" class="vlp-dot"
              :class="{ on: i === secIndex }"
              :style="{ left: dotPos(i) + '%' }"></span>
      </div>
      <span class="vlp-time">{{ fmt(cur) }} / {{ fmt(dur) }}</span>
      <button class="vlp-btn" @click="cycleSpeed" title="播放速度">{{ speed }}x</button>
      <button class="vlp-btn" @click="replay" title="重播">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 12a9 9 0 109-9 9.75 9.75 0 00-6.74 2.74L3 8"/>
          <path d="M3 3v5h5"/>
        </svg>
      </button>
    </div>

    <audio
      ref="audioEl"
      :src="video.audio_url"
      preload="auto"
      @play="onPlay"
      @pause="onPause"
      @loadedmetadata="onMeta"
      @ended="onEnded"
      @canplay="onCanplay"
      @playing="onPlaying"
      @timeupdate="onTimeUpdate"
      @waiting="onWaiting"
      @error="onAudioError"
    ></audio>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { drawFrame } from '@/utils/videoRender'
import { exportStoryboardVideo, supportsFastExport } from '@/utils/videoExport'
import { ANGLE_LABELS } from '@/utils/videoLib'

const props = defineProps({
  video: { type: Object, required: true },   // video_library 行
  autoplay: { type: Boolean, default: true },
})

const audioEl = ref(null)
const stageRef = ref(null)
const exporting = ref(false)   // 视频导出中（画面+声音合成 webm）
const exportPct = ref(0)
const playing = ref(false)
const cur = ref(0)          // 播放位置（playing 期间 rAF 高频刷新，打字机才顺滑）
const dur = ref(0)
const speedIdx = ref(0)
const speeds = [1, 1.25, 1.5]
const playedOnce = ref(false)
let rafId = null
let autoPlayTimer = null
let revealTimer = null       // 骨架角标最长停留时间（2026-09-05）

// 加载管线四态（2026-09-05 重写：全部不再遮挡画面，只是提示）
const audioReady = ref(false)   // 音轨可播（canplay / playing / timeupdate / readyState 任一信号）
const audioError = ref(false)   // 音轨拉取/解码失败 → 底部横幅提示
const buffering = ref(false)    // 播放中网络欠载 → 缓冲角标
const blocked = ref(false)      // 自动播放被浏览器拦下 → 画面之上半透明大播钮
const stopped = ref(false)      // 弹窗已关（stop 闸门）→ 兜底定时器不复活音频

const speed = computed(() => speeds[speedIdx.value])
// 模板皮肤（2026-09-05：10 套；旧键兼容 cards → glass）
const SKINS = ['chalkboard', 'paper', 'whiteboard', 'chat', 'qa', 'fun', 'neon', 'mindmap', 'glass', 'compare']
const tplKey = computed(() => {
  const k = props.video.template_key
  if (SKINS.includes(k)) return k
  if (k === 'cards') return 'glass'
  return 'glass'
})
// 双皮肤交替（2026-09-05 用户定调：一个视频不要一套模板走到底）——
// 每条视频 = 主模板 + 配对副模板；钩子用副皮肤开场反差，此后每镜主/副交替换（快剪节奏）
const SKIN_PAIRS = {
  chalkboard: 'paper', paper: 'chalkboard',
  whiteboard: 'mindmap', mindmap: 'whiteboard',
  chat: 'qa', qa: 'fun', fun: 'paper',
  neon: 'glass', glass: 'neon', compare: 'glass',
}
const skinPair = computed(() => SKIN_PAIRS[tplKey.value] || 'glass')
const activeSkin = computed(() => {
  if (!isStoryboard.value || !showStoryHook.value) return (sceneIdx.value % 2 === 0) ? tplKey.value : skinPair.value
  return skinPair.value   // 钩子开场：副皮肤反差
})
const anglName = computed(() => ANGLE_LABELS[props.video.angle] || '知识点讲解')

const sections = computed(() => {
  const list = (props.video.script && props.video.script.sections) || []
  if (!list.length) {
    return [{ heading: props.video.title || props.video.knowledge_name || '知识点讲解', lines: [] }]
  }
  return list.map(s => ({
    heading: s.heading || '',
    lines: (Array.isArray(s.lines) ? s.lines : []).filter(l => String(l || '').trim()),
  }))
})

// ===== 全局时间轴（千问 7 档语速 ≈ 6.2 字/秒，与后端同一口径）=====
const totalDur = computed(() => dur.value || props.video.audio_duration || 90)
const totalWeight = computed(() => sections.value.reduce((s, x) => s + Math.max(1, x.lines.length), 0) || 1)
const secBoundaries = computed(() => {
  let acc = 0
  return sections.value.map(s => {
    const w = Math.max(1, s.lines.length)
    acc += (w / totalWeight.value) * totalDur.value
    return acc
  })
})
const secIndex = computed(() => {
  const t = cur.value
  let i = 0
  while (i < secBoundaries.value.length - 1 && t >= secBoundaries.value[i]) i++
  return i
})
const section = computed(() => sections.value[secIndex.value] || sections.value[0])

// 全片行时间轴 [{si, li, text, start, end}]
const lineTimeline = computed(() => {
  const out = []
  sections.value.forEach((sec, si) => {
    const secStart = si === 0 ? 0 : secBoundaries.value[si - 1]
    const secEnd = secBoundaries.value[si]
    const span = Math.max(0.1, secEnd - secStart)
    const chars = sec.lines.map(l => Math.max(2, String(l).length))
    const total = chars.reduce((a, b) => a + b, 0) || 1
    let acc = 0
    sec.lines.forEach((text, li) => {
      const s = secStart + (acc / total) * span
      acc += chars[li]
      out.push({ si, li, text, start: s, end: secStart + (acc / total) * span })
    })
  })
  return out
})
const curSectionLines = computed(() => lineTimeline.value.filter(l => l.si === secIndex.value))

function lineVisible(i) {
  const t = curSectionLines.value[i]
  return !!t && cur.value >= t.start
}

const activeLine = computed(() => {
  const list = curSectionLines.value
  let idx = -1
  for (let i = 0; i < list.length; i++) {
    if (cur.value >= list[i].start) idx = i
  }
  return idx
})

// 打字机：行出现后按每秒约 12 字匀速打字
const TYPE_RATE = 12
function typedCount(i) {
  const t = curSectionLines.value[i]
  if (!t) return 0
  const chars = Math.floor((cur.value - t.start) * TYPE_RATE * speed.value)
  return Math.max(0, Math.min(String(section.value.lines[i]).length, chars))
}

// ===== 氛围切换 + 关键词高亮 + 背景池 =====
const MOOD_LABELS = { lecture: '严谨讲解', story: '轻松比喻', highlight: '重点强调', demo: '例题示范' }
function inferMood(sec) {
  const h = (sec && sec.heading) || ''
  if (/例|示范/.test(h)) return 'demo'
  if (/口诀|记住|重点|必背|强调/.test(h)) return 'highlight'
  if (/比喻|故事|身边|生活|打比方/.test(h)) return 'story'
  return 'lecture'
}
function hashStr(s) {
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0
  return Math.abs(h)
}
const bgClass = computed(() => {
  const seed = `${props.video.subject}:${props.video.knowledge_key}:${props.video.angle}`
  return ['bg-cosmos', 'bg-embers', 'bg-jade', 'bg-aurora'][hashStr(seed) % 4]
})

// 关键词「」切分解析
function lineParts(line) {
  const out = []
  const re = /「([^」]*)」/g
  let last = 0
  let m
  while ((m = re.exec(line))) {
    if (m.index > last) out.push({ t: line.slice(last, m.index), kw: false })
    out.push({ t: m[1], kw: true })
    last = m.index + m[0].length
  }
  if (last < line.length) out.push({ t: line.slice(last), kw: false })
  return out.length ? out : [{ t: line, kw: false }]
}
function lineFullyTyped(i) {
  return typedCount(i) >= String(section.value.lines[i]).length
}

// ===== 分镜演出引擎（scenes 驱动图形演示）=====
const script = computed(() => props.video.script || {})
const isStoryboard = computed(() => Array.isArray(script.value.scenes) && script.value.scenes.length > 0)
const storyScenes = computed(() => (isStoryboard.value ? script.value.scenes : []))

const sceneTimes = computed(() => {
  const list = storyScenes.value
  if (!list.length) return []
  const chars = list.map(s => Math.max(1, String(s.narration || '').length))
  const total = chars.reduce((a, b) => a + b, 0)
  const full = totalDur.value
  let acc = 0
  return chars.map(c => {
    const start = (acc / total) * full
    acc += c
    return { start, end: (acc / total) * full }
  })
})
const sceneIdx = computed(() => {
  const t = cur.value
  let i = 0
  while (i < sceneTimes.value.length - 1 && t >= sceneTimes.value[i].end) i++
  return i
})
const scene = computed(() => storyScenes.value[sceneIdx.value] || null)
const sceneProgress = computed(() => {
  const t = sceneTimes.value[sceneIdx.value]
  if (!t) return 0
  return Math.max(0, Math.min(1, (cur.value - t.start) / Math.max(0.1, t.end - t.start)))
})
const widgetKind = computed(() => (scene.value && scene.value.widget) || 'point')
const wParams = computed(() => {
  const p = scene.value && scene.value.params
  return p && typeof p === 'object' ? p : {}
})

// 钩子与收束
const showStoryHook = computed(() => isStoryboard.value && cur.value < 2.2)
const finalPhrase = computed(() => {
  const ph = [...storyScenes.value].reverse().find(s => s.widget === 'phrase')
  return (ph && ph.params && ph.params.text) || ''
})
const outroLines = computed(() =>
  isStoryboard.value ? (finalPhrase.value ? [finalPhrase.value] : [])
    : keepLines.value.items.slice(-4))

// 分镜 mood 覆盖全局氛围（优雅退化：无 mood 用该镜旁白推断）
const curMood = computed(() => {
  if (isStoryboard.value && scene.value) {
    const m = scene.value.mood
    if (MOOD_LABELS[m]) return m
    const n = String(scene.value.narration || '')
    if (/口诀|记住|重点|强调/.test(n)) return 'highlight'
    if (/比喻|就像|打比方|故事|想象/.test(n)) return 'story'
    if (/例题|例如|这道|算一算/.test(n)) return 'demo'
    return 'lecture'
  }
  const sec = section.value
  const m = sec && sec.mood
  return MOOD_LABELS[m] ? m : inferMood(sec)
})

// array 构件·连续演示动画派生状态
const arrVals = computed(() => (wParams.value.values || []).map(v => Number(v)))
const arrMoves = computed(() => (wParams.value.moves || []))
const arrTarget = computed(() => Number(wParams.value.target))
const K = computed(() => arrMoves.value.length || 1)
const frameRaw = computed(() => sceneProgress.value * K.value)          // 连续帧坐标
const frameK = computed(() => Math.min(Math.floor(frameRaw.value), K.value - 1))
const frameFrac = computed(() => Math.min(1, frameRaw.value - frameK.value))
const curMove = computed(() => arrMoves.value[frameK.value] || { l: -1, r: -1, note: '' })
const framePair = computed(() => {
  const m = curMove.value
  const vals = arrVals.value
  return {
    l: m.l ?? -1, r: m.r ?? -1,
    lv: vals[m.l] ?? '', rv: vals[m.r] ?? '',
  }
})
// 指针滑行：帧内后 65% 从本帧位置插值滑向下一帧位置
const lerped = computed(() => {
  const from = curMove.value
  const p = frameFrac.value
  const t = Math.max(0, Math.min(1, (p - 0.35) / 0.65))
  const ease = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2     // easeInOutQuad
  if (frameK.value >= K.value - 1) return { l: from.l ?? -1, r: from.r ?? -1 }
  const to = arrMoves.value[frameK.value + 1] || from
  return {
    l: (from.l ?? -1) + ((to.l ?? (from.l ?? -1)) - (from.l ?? -1)) * ease,
    r: (from.r ?? -1) + ((to.r ?? (from.r ?? -1)) - (from.r ?? -1)) * ease,
  }
})
// 计算相处（帧内 0~35%）：两数飞出相加，和值从 0 滚动到真值
const showCompute = computed(() => frameFrac.value < 0.35 && curMove.value.l !== undefined && arrTarget.value !== undefined && isFinite(arrTarget.value))
const computeT = computed(() => Math.max(0, Math.min(1, frameFrac.value / 0.35)))
const trueSum = computed(() => (framePair.value.lv || 0) + (framePair.value.rv || 0))
const rolledSum = computed(() => Math.floor(trueSum.value * computeT.value))
const isSumHit = computed(() => arrTarget.value !== undefined && isFinite(arrTarget.value) && trueSum.value === arrTarget.value)
const verTarg = computed(() => isSumHit.value ? 'hit' : (arrTarget.value !== undefined && isFinite(arrTarget.value) && trueSum.value > arrTarget.value ? 'big' : 'small'))
const verdictText = computed(() =>
  isSumHit.value ? '中了!' : (verTarg.value === 'big' ? '太大 右指针左移' : '太小 左指针右移'))
function alongPath(i) {
  const l = lerped.value.l, r = lerped.value.r
  return (i === Math.round(l) || i === Math.round(r)) ? false
    : (l > -1 && r > -1 && i > Math.min(l, r) && i < Math.max(l, r))
}
function trailDelay(i) {
  const l = Math.min(lerped.value.l, lerped.value.r)
  return Math.max(0, (i - l) * 0.25)
}
function cellXf(f) {
  const n = arrVals.value.length
  if (f < 0) return -10
  if (n <= 1) return 50
  return 6 + (f / (n - 1)) * 88
}
function isHitNote(note) {
  return /中|成功|找到|正确|成了/.test(String(note || ''))
}
function hitCells(i) {
  const moves = wParams.value.moves || []
  const last = moves[moves.length - 1]
  return !!last && frameK.value >= moves.length - 1 && isSumHit.value && (last.l === i || last.r === i)
}
const workReveal = computed(() => {
  const work = wParams.value.work || []
  if (!work.length) return 0
  return Math.min(work.length, Math.max(1, Math.ceil(sceneProgress.value * (work.length + 1.2))))
})

// 片头标题屏（2.2s 前，仅旧 sections 脚本）/ 片尾小结屏（最后 3.2s）
const showIntro = computed(() => cur.value < 2.2 && !isStoryboard.value)
const showOutro = computed(() => dur.value > 0 && (dur.value - cur.value) < 3.2)

// ===== 要点板：讲过的重点句常驻屏幕 =====
const keepLines = computed(() => {
  const passed = lineTimeline.value.filter(l => cur.value >= l.start + 0.15)
  if (!passed.length) return { items: [], hidden: 0 }
  const hidden = Math.max(0, passed.length - 6)
  return { items: passed.slice(-6), hidden }
})

// ===== 句级字幕：讲稿按句切分 → 逐句时间轴 =====
const subs = computed(() => {
  const narration = String(
    (props.video.script && props.video.script.narration) || props.video.script_text || ''
  ).trim()
  if (!narration) return []
  const pieces = narration.split(/(?<=[，,。！？!?；;：:、])/).map(s => s.trim()).filter(Boolean)
  const out = []
  let buf = ''
  for (const p of pieces) {
    buf += p
    const endsSentence = /[。！？!?]$/.test(p)
    if (endsSentence || buf.length >= 14) {
      if (buf.length > 20 && !endsSentence) {
        const cut = buf.lastIndexOf('，', 18)
        if (cut > 4) {
          out.push(buf.slice(0, cut + 1))
          buf = buf.slice(cut + 1)
          continue
        }
      }
      out.push(buf)
      buf = ''
    }
  }
  if (buf.trim()) out.push(buf)
  return out.filter(s => s.length > 1)
})
const subTimes = computed(() => {
  const list = subs.value
  if (!list.length) return []
  const chars = list.map(s => Math.max(1, s.length))
  const total = chars.reduce((a, b) => a + b, 0)
  const full = dur.value || props.video.audio_duration || 90
  let acc = 0
  return chars.map(c => {
    const start = (acc / total) * full
    acc += c
    return { start, end: (acc / total) * full }
  })
})
const subIdx = computed(() => {
  const t = cur.value
  let i = 0
  while (i < subTimes.value.length - 1 && t >= subTimes.value[i].end) i++
  return i
})
const currentSubChars = computed(() =>
  (subs.value[subIdx.value] || '').replace(/[，。！？；：、,.!?;:]+\s*$/, ''))

const pct = computed(() => (dur.value ? Math.min(100, (cur.value / dur.value) * 100) : 0))

function dotPos(i) {
  if (!dur.value || !secBoundaries.value.length) return 0
  return Math.min(99, (secBoundaries.value[i] / dur.value) * 100)
}

function fmt(t) {
  if (!t || !isFinite(t)) return '0:00'
  const m = Math.floor(t / 60), s = Math.floor(t % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

// ===== 播放驱动（rAF 高频同步 cur）=====
function onPlay() {
  playing.value = true
  blocked.value = false
  buffering.value = false
  audioReady.value = true
  const tick = () => {
    if (audioEl.value) cur.value = audioEl.value.currentTime
    rafId = requestAnimationFrame(tick)
  }
  tick()
}
function onPause() {
  playing.value = false
  if (rafId) { cancelAnimationFrame(rafId); rafId = null }
  if (audioEl.value) cur.value = audioEl.value.currentTime
}
function onMeta() {
  if (audioEl.value) dur.value = audioEl.value.duration || props.video.audio_duration || 90
}
function onEnded() {
  onPause()
  cur.value = dur.value
  playedOnce.value = true
}

// ===== 加载管线（2026-09-05 重写）：画面永不被遮挡；
// 音轨就绪 = canplay / playing / timeupdate / readyState 任一信号，多路兜底 =====
function settleLoading() {
  if (revealTimer) { clearTimeout(revealTimer); revealTimer = null }
  if (autoPlayTimer) { clearTimeout(autoPlayTimer); autoPlayTimer = null }
}
function markReady() {
  if (stopped.value) return
  audioReady.value = true
  settleLoading()
}
function tryAutoPlay() {
  const a = audioEl.value
  if (!a || !props.autoplay || audioError.value || stopped.value) return
  if (a.readyState >= 3) {
    markReady()
    a.play().catch(() => { blocked.value = true })
    return
  }
  // 未就绪：等 canplay；部分机型事件缺失，4s 兜底强开（浏览器会缓冲到可播）
  if (revealTimer) clearTimeout(revealTimer)
  revealTimer = setTimeout(() => {
    if (!audioReady.value && !audioError.value) {
      markReady()
      a.play().catch(() => { blocked.value = true })
    }
  }, 4000)
}
function onCanplay() { markReady(); tryAutoPlay() }
function onPlaying() { buffering.value = false; markReady() }
function onTimeUpdate() { if (!audioReady.value && !stopped.value) markReady() }
function onWaiting() { if (playing.value) buffering.value = true }
function onAudioError() {
  audioError.value = true
  buffering.value = false
  settleLoading()
}
function startByTap() {
  const a = audioEl.value
  if (!a) return
  blocked.value = false
  a.play().catch(() => { blocked.value = true })
}
function retryAudio() {
  const a = audioEl.value
  if (!a) return
  audioError.value = false
  audioReady.value = false
  blocked.value = false
  a.load()
  tryAutoPlay()
}

function toggle() {
  const a = audioEl.value
  if (!a) return
  if (audioError.value) { retryAudio(); return }
  if (blocked.value) blocked.value = false
  if (playedOnce.value) { playedOnce.value = false; a.currentTime = 0; cur.value = 0 }
  if (a.paused) a.play().catch(() => { blocked.value = true })
  else a.pause()
}

function replay() {
  const a = audioEl.value
  if (!a) return
  if (audioError.value) { retryAudio(); return }
  a.currentTime = 0
  cur.value = 0
  playedOnce.value = false
  a.play().catch(() => { blocked.value = true })
}

function seek(e) {
  const a = audioEl.value
  if (!a || !dur.value) return
  const rect = e.currentTarget.getBoundingClientRect()
  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  a.currentTime = ratio * dur.value
  cur.value = a.currentTime
}

function cycleSpeed() {
  speedIdx.value = (speedIdx.value + 1) % speeds.length
  if (audioEl.value) audioEl.value.playbackRate = speed.value
}

function stop() {
  const a = audioEl.value
  if (a) { a.pause(); a.currentTime = 0 }
  settleLoading()
  stopped.value = true
  blocked.value = false
  onPause()
  cur.value = 0
}

// 组件挂载后自动开播（音轨就绪即开；缓存命中秒开）
onMounted(() => {
  const a = audioEl.value
  if (!props.autoplay || !a) return
  if (a.readyState >= 3) {
    markReady()
    a.play().catch(() => { blocked.value = true })
  } else {
    tryAutoPlay()
  }
})

onUnmounted(() => {
  settleLoading()
  if (rafId) { cancelAnimationFrame(rafId); rafId = null }
})

// 换视频：src 已换，加载管线整条重走
watch(() => props.video.id, (nid, oid) => {
  if (!nid || nid === oid) return
  stop()
  audioReady.value = false
  audioError.value = false
  buffering.value = false
  blocked.value = false
  stopped.value = false
  tryAutoPlay()
})

// 二次进入（弹窗不销毁、实例复用）：从头自动开播
function start() {
  if (!audioEl.value) return
  onPause()
  cur.value = 0
  playedOnce.value = false
  stopped.value = false
  tryAutoPlay()
}

// ===== 导出视频（2026-09-05 用户定调：WebCodecs 离线快编——渲染一帧交一帧，
// 编码器满载跑，45 秒视频十几秒出片；老浏览器兜底 MediaRecorder 实时录制）=====
async function downloadVideo() {
  const url = props.video.audio_url
  if (!url || exporting.value) throw new Error(url ? '正在导出中，请稍候' : '音轨还没生成')
  exporting.value = true
  exportPct.value = 0
  try {
    let blob
    if (supportsFastExport()) {
      blob = await exportStoryboardVideo(props.video, {
        onProgress: (p) => { exportPct.value = p },
      })
    } else {
      blob = await recordRealtimeFallback(props.video, (p) => { exportPct.value = p })
    }
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `${props.video.title || props.video.knowledge_name || '讲解视频'}.webm`
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(a.href), 4000)
  } finally {
    exporting.value = false
    exportPct.value = 0
  }
}

// 兜底：不支持 WebCodecs 的浏览器走 MediaRecorder 实时录制（耗时≈视频时长，画质同管线）
async function recordRealtimeFallback(video, onProgress) {
  const resp = await fetch(video.audio_url)
  if (!resp.ok) throw new Error('音轨拉取失败 HTTP ' + resp.status)
  const AC = window.AudioContext || window.webkitAudioContext
  const ac = new AC()
  const audioData = await ac.decodeAudioData(await resp.arrayBuffer())
  const dur = audioData.duration
  const W = 1280, H = 720
  const canvas = document.createElement('canvas')
  canvas.width = W; canvas.height = H
  const ctx = canvas.getContext('2d')
  const stream = canvas.captureStream(30)
  const srcNode = ac.createBufferSource()
  srcNode.buffer = audioData
  const dest = ac.createMediaStreamDestination()
  srcNode.connect(dest)
  const mime = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm']
    .find((m) => typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(m)) || ''
  const rec = new MediaRecorder(
    new MediaStream([...stream.getVideoTracks(), ...dest.stream.getAudioTracks()]),
    mime ? { mimeType: mime, videoBitsPerSecond: 3_000_000 } : undefined,
  )
  const chunks = []
  rec.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data) }
  const doneP = new Promise((res) => { rec.onstop = res })
  const rv = { ...video, audio_duration: dur }
  const t0 = performance.now() + 150
  srcNode.start()
  rec.start(250)
  await new Promise((resolve, reject) => {
    const draw = () => {
      const t = Math.min(dur, (performance.now() - t0) / 1000)
      try { drawFrame(ctx, rv, t, W, H) } catch (e) { console.error('drawFrame:', e) }
      onProgress && onProgress(Math.round((t / dur) * 100))
      if (t >= dur) {
        try { srcNode.stop() } catch {}
        try { rec.stop(); resolve() } catch (e) { reject(e) }
        return
      }
      requestAnimationFrame(draw)
    }
    requestAnimationFrame(draw)
  })
  await doneP
  return new Blob(chunks, { type: 'video/webm' })
}


defineExpose({ stop, start, downloadVideo })
</script>

<style scoped>
.vlp {
  display: flex;
  flex-direction: column;
  gap: 10px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(128, 128, 128, 0.18);
  background: #0d1117;
}

/* ===== 16:9 画框（2026-09-05：padding-top 兜底，不依赖 aspect-ratio）===== */
.vlp-frame {
  position: relative;
  width: 100%;
  padding-top: 56.25%;
}
.vlp-stage {
  position: absolute;
  inset: 0;
  overflow: hidden;
}

/* ===== 氛围四态 ===== */
.vlp-stage { --vx-accent: #5ed0ff; }
.mood-lecture { --vx-accent: #5ed0ff; }
.mood-story { --vx-accent: #ffb84d; }
.mood-highlight { --vx-accent: #ff5c7a; }
.mood-demo { --vx-accent: #b48cff; }
.mood-highlight .vlp-vignette { animation: vx-vig-pulse 1.5s ease-in-out infinite; }
@keyframes vx-vig-pulse { 0%, 100% { opacity: 1; } 50% { opacity: .55; } }
.mood-story .vlp-stage::after {
  content: "";
  position: absolute; inset: 0;
  pointer-events: none;
  background:
    radial-gradient(7px 7px at 76% 24%, rgba(255, 184, 77, .5), transparent 66%),
    radial-gradient(5px 5px at 18% 70%, rgba(255, 184, 77, .42), transparent 62%),
    radial-gradient(4px 4px at 62% 82%, rgba(255, 184, 77, .35), transparent 60%);
  animation: vx-bob 3s ease-in-out infinite alternate;
}
@keyframes vx-bob { from { transform: translateY(2px); } to { transform: translateY(-8px); } }

/* ===== 背景池 v1：四套程序化氛围背景（按视频身份稳定抽取）===== */
.bg-cosmos .vlp-stage-bg {
  background:
    radial-gradient(55% 70% at 82% -8%, rgba(94, 208, 255, .22), transparent 60%),
    radial-gradient(60% 70% at 5% 108%, rgba(80, 96, 235, .20), transparent 55%),
    radial-gradient(35% 45% at 30% 50%, rgba(94, 208, 255, .06), transparent 70%);
}
.bg-embers .vlp-stage-bg {
  background:
    radial-gradient(55% 70% at 82% -8%, rgba(255, 148, 84, .24), transparent 60%),
    radial-gradient(60% 70% at 5% 108%, rgba(255, 84, 130, .18), transparent 55%),
    radial-gradient(35% 45% at 30% 50%, rgba(255, 196, 110, .07), transparent 70%);
}
.bg-jade .vlp-stage-bg {
  background:
    radial-gradient(55% 70% at 82% -8%, rgba(52, 224, 170, .20), transparent 60%),
    radial-gradient(60% 70% at 5% 108%, rgba(64, 160, 255, .18), transparent 55%),
    radial-gradient(35% 45% at 30% 50%, rgba(52, 224, 170, .05), transparent 70%);
}
.bg-aurora .vlp-stage-bg {
  background:
    radial-gradient(55% 70% at 82% -8%, rgba(180, 140, 255, .24), transparent 60%),
    radial-gradient(60% 70% at 5% 108%, rgba(255, 110, 200, .18), transparent 55%),
    radial-gradient(35% 45% at 30% 50%, rgba(120, 220, 255, .06), transparent 70%);
}
.vlp-stage-bg {
  position: absolute; inset: -6%;
  background:
    radial-gradient(55% 70% at 82% -8%, rgba(64, 158, 255, 0.20), transparent 60%),
    radial-gradient(60% 70% at 5% 108%, rgba(139, 92, 246, 0.14), transparent 55%),
    radial-gradient(35% 45% at 30% 50%, rgba(94, 208, 255, 0.06), transparent 70%);
  animation: vlp-bg-drift 16s ease-in-out infinite alternate;
}
.vlp.playing .vlp-stage-bg { animation-play-state: running; }
.vlp:not(.playing) .vlp-stage-bg { animation-play-state: paused; }
@keyframes vlp-bg-drift {
  from { transform: translate3d(-2%, -1%, 0) scale(1); }
  to { transform: translate3d(2%, 2%, 0) scale(1.06); }
}

/* ===== 电影黑边 / 暗角 / 颗粒 ===== */
.vlp-letterbox {
  position: absolute; left: 0; right: 0; height: 3.2%;
  background: #000;
  z-index: 5;
  pointer-events: none;
}
.vlp-letterbox.top { top: 0; }
.vlp-letterbox.bot { bottom: 0; }
.vlp-vignette {
  position: absolute; inset: 0; z-index: 4;
  pointer-events: none;
  background: radial-gradient(120% 105% at 50% 45%, transparent 58%, rgba(0, 0, 0, .42) 100%);
}
.vlp-grain {
  position: absolute; inset: 0; z-index: 4;
  pointer-events: none;
  opacity: .5;
  background-image:
    radial-gradient(rgba(255,255,255,.028) 1px, transparent 1.3px);
  background-size: 3px 3px;
}

/* 摄影机缓推（只作用于画面模板） */
.vlp-board, .vlp-cards {
  animation: vlp-cam-zoom 22s ease-in-out infinite alternate;
}
.vlp.playing .vlp-board, .vlp.playing .vlp-cards { animation-play-state: running; }
.vlp:not(.playing) .vlp-board, .vlp:not(.playing) .vlp-cards { animation-play-state: paused; }
@keyframes vlp-cam-zoom {
  from { transform: scale(1.015); }
  to { transform: scale(1.055); }
}

/* ===== 打字机通用 ===== */
.vlp-tw { position: relative; white-space: pre-wrap; }
.vlp-tw-hidden { visibility: hidden; }
.vlp-kw {
  color: var(--vx-accent, #5ed0ff);
  font-weight: 700;
}
.tpl-cards .vlp-kw {
  color: #22335c;
  background: rgba(47, 111, 224, .12);
  border-radius: 5px;
  padding: 0 5px;
  margin: 0 1px;
}
.vlp-caret {
  display: inline-block; width: 2px; height: 1em;
  margin-left: 3px; vertical-align: -0.15em;
  background: var(--vx-accent, #5ed0ff);
  animation: vlp-caret-blink .8s steps(1) infinite;
}
@keyframes vlp-caret-blink { 50% { opacity: 0; } }

/* ===== 模板：板书流 ===== */
.vlp-board {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; justify-content: center; align-items: center;
  gap: clamp(8px, 2.4vh, 18px);
  padding: 4% 6%;
  background: linear-gradient(160deg, #0f1722 0%, #142030 55%, #101a28 100%);
  border: clamp(8px, 1.6vw, 16px) solid #2e241b;               /* 木质黑框 */
  box-shadow: inset 0 0 60px rgba(0, 0, 0, .45), inset 0 0 4px rgba(255, 255, 255, .05);
}
.vlp-board::after {                                             /* 粉笔灰纹理 */
  content: "";
  position: absolute; inset: 0;
  pointer-events: none;
  background:
    radial-gradient(2px 2px at 18% 26%, rgba(255,255,255,.06), transparent 60%),
    radial-gradient(1.5px 1.5px at 64% 78%, rgba(255,255,255,.05), transparent 60%),
    radial-gradient(2px 2px at 82% 12%, rgba(255,255,255,.05), transparent 60%);
}
.vlp-board-topline {
  position: absolute; top: 12px; left: 16px; right: 16px;
  display: flex; align-items: center; justify-content: space-between;
}
.vlp-sec-chip {
  font-size: 10px; color: rgba(160, 200, 255, .55);
  padding: 2px 9px; border-radius: 999px;
  border: 1px solid rgba(160, 200, 255, .22);
}
.vlp-board-dots { display: flex; gap: 5px; }
.vlp-board-dots i { width: 6px; height: 6px; border-radius: 50%; background: rgba(160, 200, 255, .18); transition: all .3s ease; }
.vlp-board-dots i.done { background: rgba(94, 208, 255, .4); }
.vlp-board-dots i.on { background: var(--vx-accent, #5ed0ff); box-shadow: 0 0 8px var(--vx-accent, #5ed0ff); transform: scale(1.4); }

.vlp-board-title {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  font-size: clamp(18px, 4vw, 30px);
  font-weight: 700;
  color: #e8edf7;
  letter-spacing: 1px;
}
.vlp-board-underline {
  display: block; width: 100%; height: 2px;
  background: linear-gradient(90deg, transparent, var(--vx-accent, #5ed0ff), transparent);
  animation: vlp-underline-draw .8s ease both;
}
@keyframes vlp-underline-draw { from { transform: scaleX(0); opacity: 0; } to { transform: scaleX(1); opacity: 1; } }
.vlp-head-pop-enter-active { transition: all .45s cubic-bezier(.2, 1.4, .4, 1); }
.vlp-head-pop-leave-active { transition: all .2s ease; }
.vlp-head-pop-enter-from { opacity: 0; transform: translateY(-14px) scale(.9); }
.vlp-head-pop-leave-to { opacity: 0; transform: translateY(10px) scale(.95); }

.vlp-board-lines {
  display: flex; flex-direction: column; gap: clamp(6px, 1.6vh, 12px);
  width: 100%; max-width: 640px;
  min-height: clamp(70px, 12vh, 96px);
}
.vlp-chalk-line {
  display: flex; align-items: center; gap: 8px;
  font-size: clamp(13px, 2.4vw, 17px);
  color: #c9d6ea;
  animation: vlp-chalk-in .4s ease both;
  transition: opacity .35s ease, transform .35s ease, color .35s ease;
}
.vlp-chalk-line b { color: var(--vx-accent, #5ed0ff); font-weight: 700; flex: none; }
.vlp-chalk-line.on { color: #f2f7ff; transform: translateX(6px); }
.vlp-chalk-line.on b { text-shadow: 0 0 10px var(--vx-accent, #5ed0ff); }
.vlp-chalk-line.done { opacity: .55; }
@keyframes vlp-chalk-in {
  from { opacity: 0; transform: translateX(-12px); }
  to { opacity: 1; transform: none; }
}

.vlp-board-foot {
  margin-top: 4px;
  font-size: 11px;
  color: rgba(160, 200, 255, .45);
  letter-spacing: 2px;
}

/* ===== 模板：卡片流（工作室布光底） ===== */
.vlp-cards {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  padding: 4% 6%;
  background: linear-gradient(160deg, #f4f6fb 0%, #e9eef7 60%, #eef1f8 100%);
}
.vlp-cards::before {
  content: "";
  position: absolute; inset: 0;
  pointer-events: none;
  background:
    radial-gradient(30% 45% at 14% 12%, rgba(64, 158, 255, .14), transparent 70%),
    radial-gradient(34% 50% at 88% 88%, rgba(139, 92, 246, .12), transparent 70%);
}
.vlp-card {
  width: min(86%, 560px);
  padding: clamp(14px, 3.5vh, 26px) clamp(16px, 4vw, 30px);
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 14px 40px rgba(30, 50, 90, .16);
  border: 1px solid rgba(120, 140, 180, .14);
}
.vlp-card-head {
  display: flex; align-items: center; justify-content: space-between;
  font-size: clamp(16px, 3.2vw, 24px);
  font-weight: 700;
  color: #1c2b45;
  margin-bottom: 10px;
}
.vlp-card-sec { font-size: 11px; font-weight: 500; color: #8b9ab8; }
.vlp-card-lines { display: flex; flex-direction: column; gap: 9px; }
.vlp-card-line {
  display: flex; align-items: flex-start; gap: 8px;
  font-size: clamp(12px, 2.2vw, 15px);
  color: #45536e;
  transition: all .3s ease;
}
.vlp-card-bullet {
  flex: none; width: 7px; height: 7px; border-radius: 50%;
  margin-top: 6px;
  background: rgba(47, 111, 224, .35);
  transition: all .3s ease;
}
.vlp-card-line.on { color: #16233c; transform: translateX(5px); }
.vlp-card-line.on .vlp-card-bullet { background: var(--vx-accent, #2f6fe0); box-shadow: 0 0 0 4px rgba(47, 111, 224, .2); }
.vlp-card-dots { display: flex; gap: 5px; margin-top: 14px; }
.vlp-card-dots i { width: 7px; height: 7px; border-radius: 50%; background: rgba(120, 140, 180, .25); transition: all .3s ease; }
.vlp-card-dots i.on { background: var(--vx-accent, #2f6fe0); transform: scale(1.35); }
.vlp-card-dots i.done { background: rgba(47, 111, 224, .45); }
.vlp-card-enter-active, .vlp-card-leave-active { transition: all .35s ease; }
.vlp-card-enter-from { opacity: 0; transform: translateX(26px) rotate(1deg); }
.vlp-card-leave-to { opacity: 0; transform: translateX(-26px) rotate(-1deg); }

/* ===== 片头 / 片尾 ===== */
.vlp-fade-enter-active, .vlp-fade-leave-active { transition: opacity .5s ease; }
.vlp-fade-enter-from, .vlp-fade-leave-to { opacity: 0; }

.vlp-intro {
  position: absolute; inset: 0; z-index: 8;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px;
  text-align: center;
  padding: 0 8%;
}
.vlp-intro.tpl-chalkboard { background: #0d1220; }
.vlp-intro.tpl-cards { background: #f4f6fb; }
.vlp-intro-tag {
  font-size: 12px; letter-spacing: 2px;
  padding: 4px 14px; border-radius: 999px;
  color: var(--vx-accent, #5ed0ff);
  border: 1px solid rgba(94, 208, 255, .4);
  background: rgba(94, 208, 255, .08);
  animation: vlp-intro-pop .6s cubic-bezier(.2, 1.4, .4, 1) both;
}
.tpl-cards.vlp-intro .vlp-intro-tag { color: #2f6fe0; border-color: rgba(47, 111, 224, .4); background: rgba(47, 111, 224, .08); }
.vlp-intro h1 {
  font-size: clamp(22px, 4.4vw, 34px);
  font-weight: 800; letter-spacing: 1px;
  color: #eef3fb;
  animation: vlp-intro-pop .7s .15s cubic-bezier(.2, 1.4, .4, 1) both;
}
.tpl-cards.vlp-intro h1 { color: #1c2b45; }
.vlp-intro-sub {
  display: flex; align-items: center; gap: 7px;
  font-size: 12.5px; color: rgba(223, 231, 245, .6);
  animation: vlp-intro-pop .7s .3s cubic-bezier(.2, 1.4, .4, 1) both;
}
.tpl-cards.vlp-intro .vlp-intro-sub { color: rgba(69, 83, 110, .7); }
.vlp-intro-sub img { width: 20px; height: 20px; border-radius: 50%; object-fit: cover; background: #fff; }
.vlp-intro::after {
  content: "";
  position: absolute; inset: 0;
  pointer-events: none;
  background: radial-gradient(55% 60% at 50% 110%, rgba(64, 158, 255, .20), transparent 65%);
}
@keyframes vlp-intro-pop {
  from { opacity: 0; transform: translateY(14px) scale(.95); }
  to { opacity: 1; transform: none; }
}

.vlp-outro {
  position: absolute; inset: 0; z-index: 8;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px;
  text-align: center;
  padding: 0 8%;
}
.vlp-outro.tpl-chalkboard { background: #0d1220; }
.vlp-outro.tpl-cards { background: #f4f6fb; }
.vlp-outro-title {
  font-size: 13px; font-weight: 700; letter-spacing: 3px;
  color: #5ed0ff;
}
.tpl-cards.vlp-outro .vlp-outro-title { color: #2f6fe0; }
.vlp-outro-lines { display: flex; flex-direction: column; gap: 5px; max-width: 70%; }
.vlp-outro-lines div {
  font-size: 13px; color: #dfe7f5;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.tpl-cards.vlp-outro .vlp-outro-lines div { color: #45536e; }
.vlp-outro-foot { font-size: 11px; letter-spacing: 1px; color: rgba(160, 200, 255, .5); }
.tpl-cards.vlp-outro .vlp-outro-foot { color: rgba(120, 140, 180, .7); }

/* ===== 生成主 chip ===== */
.vlp-author {
  position: absolute; top: 10px; right: 12px; z-index: 2;
  display: flex; align-items: center; gap: 6px;
  padding: 4px 10px 4px 5px;
  border-radius: 999px;
  background: rgba(10, 14, 24, .7);
  border: 1px solid rgba(255, 255, 255, .14);
  font-size: 11px;
  color: #dfe7f5;
}
.vlp-author img { width: 20px; height: 20px; border-radius: 50%; object-fit: cover; background: #fff; }

/* ===== 句级字幕（单行） ===== */
.vlp-subs {
  position: absolute; left: 0; right: 0; bottom: 1.6%; z-index: 7;
  display: flex; align-items: center; justify-content: center;
  padding: 6px 16px;
  pointer-events: none;
}
.sub-line.cur {
  max-width: 94%;
  font-size: clamp(15px, 2.8vw, 19px);
  font-weight: 700;
  color: #ffffff;
  text-align: center;
  letter-spacing: .3px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, .85), 0 0 12px rgba(0, 0, 0, .5);
  animation: vlp-sub-in .3s ease both;
}
.sub-cur-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-height: 1.25em; }
@keyframes vlp-sub-in {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: none; }
}

/* ===== 分镜演出台（图形演示构件） ===== */
.vlp-storyboard {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  padding: 4% 8% 10%;
}
.sb-hook { text-align: center; padding: 0 10%; }
.sb-hook-q {
  font-size: clamp(17px, 3.4vw, 26px);
  font-weight: 800;
  color: #fff;
  line-height: 1.5;
  text-shadow: 0 2px 14px rgba(0,0,0,.55);
}
/* array 数组演示 */
.sb-array { width: 100%; display: flex; flex-direction: column; align-items: center; gap: 12px; }
.sb-caption { font-size: 14px; font-weight: 700; color: rgba(232, 237, 247, .95); letter-spacing: 1px; }
.sb-cells { display: flex; gap: 10px; }
.sb-cell {
  width: clamp(38px, 6vw, 58px); height: clamp(38px, 6vw, 58px);
  display: flex; align-items: center; justify-content: center;
  font-size: clamp(15px, 2.6vw, 22px); font-weight: 800;
  border-radius: 12px;
  background: rgba(255, 255, 255, .07);
  border: 2px solid rgba(255, 255, 255, .16);
  color: #dfe7f5;
  transition: all .35s cubic-bezier(.3, 1.4, .5, 1);
}
.sb-cell.l, .sb-cell.r { transform: translateY(-8px) scale(1.12); border-width: 3px; }
.sb-cell.l { border-color: #5ed0ff; color: #fff; box-shadow: 0 6px 22px rgba(94, 208, 255, .4); }
.sb-cell.r { border-color: #ffb84d; color: #fff; box-shadow: 0 6px 22px rgba(255, 184, 77, .4); }
.sb-cell.hit { border-color: #45e08a; background: rgba(69, 224, 138, .16); box-shadow: 0 8px 28px rgba(69, 224, 138, .55); animation: sb-hit-pop .5s cubic-bezier(.2, 1.6, .4, 1); }
@keyframes sb-hit-pop { 0% { transform: scale(.7); } 100% { transform: translateY(-8px) scale(1.15); } }
.sb-note {
  position: relative;
  font-size: clamp(12px, 2.2vw, 15px); font-weight: 700; color: #ffd9a1;
  padding: 4px 14px; border-radius: 999px;
  background: rgba(255, 184, 77, .12);
  border: 1px solid rgba(255, 184, 77, .3);
}
.sb-note.good { color: #9dffc2; background: rgba(69, 224, 138, .12); border-color: rgba(69, 224, 138, .4); }
.sb-target { font-size: 12px; color: rgba(223, 231, 245, .6); }
.sb-note-row { display: flex; align-items: center; gap: 10px; }
.sb-stage-line { position: relative; width: 72%; height: 18px; }
.sb-cell.path { background: rgba(94, 208, 255, .1); border-color: rgba(94, 208, 255, .4); animation: sb-trail .8s ease both; animation-delay: var(--delay, 0s); }
@keyframes sb-trail { 0% { box-shadow: 0 0 0 8px rgba(94, 208, 255, .2); } 100% { box-shadow: 0 0 0 0 rgba(94, 208, 255, 0); } }
.sb-compute {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 20px; border-radius: 18px;
  background: rgba(12, 16, 28, .85);
  border: 1px solid rgba(94, 208, 255, .4);
  box-shadow: 0 10px 34px rgba(0, 0, 0, .5);
}
.sb-num {
  font-size: clamp(18px, 3.4vw, 26px); font-weight: 900;
  padding: 4px 12px; border-radius: 10px;
  background: rgba(255,255,255,.08); border: 2px solid rgba(255,255,255,.18);
}
.sb-num.l { color: #7ee0ff; animation: sb-num-fly-l .5s ease both; }
.sb-num.r { color: #ffc98a; animation: sb-num-fly-r .5s ease both; }
@keyframes sb-num-fly-l { from { transform: translate(24px, -16px) scale(.6); opacity: 0; } to { transform: none; opacity: 1; } }
@keyframes sb-num-fly-r { from { transform: translate(-24px, -16px) scale(.6); opacity: 0; } to { transform: none; opacity: 1; } }
.sb-plus, .sb-eq { font-size: 18px; font-weight: 800; color: rgba(223,231,245,.8); }
.sb-sum {
  min-width: 34px; text-align: center;
  font-size: clamp(20px, 3.6vw, 28px); font-weight: 900;
  color: #fff; font-variant-numeric: tabular-nums;
  animation: sb-sum-pop .3s ease infinite alternate;
}
.sb-verdict {
  font-size: clamp(11px, 2vw, 13px); font-weight: 700;
  color: #ffb84d; padding-left: 8px; border-left: 1px solid rgba(255,255,255,.16);
}
.sb-compute.good .sb-sum { color: #45e08a; }
.sb-compute.good .sb-verdict { color: #45e08a; }
.sb-compute.bad .sb-sum { color: #ff6b81; }
.sb-compute.bad .sb-verdict { color: #ff6b81; }
@keyframes sb-sum-pop { from { transform: scale(1); } to { transform: scale(1.08); } }

.sb-stage-line { position: relative; width: 80%; height: 20px; margin-top: 2px; }
.sb-pointer {
  position: absolute; top: 0;
  display: flex; flex-direction: column; align-items: center;
  transform: translateX(-50%);
  transition: left .1s linear;
  z-index: 2;
}
.sb-pointer .sp-label {
  font-size: 11px; font-weight: 800; letter-spacing: 1px;
  padding: 1px 8px; border-radius: 999px;
}
.sb-pointer.l .sp-label { color: #06131f; background: #7ee0ff; box-shadow: 0 0 12px rgba(126, 224, 255, .7); }
.sb-pointer.r .sp-label { color: #241500; background: #ffc372; box-shadow: 0 0 12px rgba(255, 195, 114, .7); }
.sb-pointer .sp-stem { width: 3px; height: 18px; border-radius: 2px; }
.sb-pointer.l .sp-stem { background: #7ee0ff; box-shadow: 0 0 8px rgba(126, 224, 255, .8); }
.sb-pointer.r .sp-stem { background: #ffc372; box-shadow: 0 0 8px rgba(255, 195, 114, .8); }
.sb-pointer .sp-head {
  width: 0; height: 0;
  border-left: 8px solid transparent;
  border-right: 8px solid transparent;
  border-top: 10px solid;
  animation: sp-bounce .8s ease-in-out infinite alternate;
}
.sb-pointer.l .sp-head { border-top-color: #7ee0ff; }
.sb-pointer.r .sp-head { border-top-color: #ffc372; }
@keyframes sp-bounce { from { transform: translateY(0); } to { transform: translateY(4px); } }

/* balance 对比 */
.sb-balance { width: 100%; }
.sb-bal { display: grid; grid-template-columns: 1fr auto 1fr; gap: 14px; align-items: stretch; }
.sb-bal-left, .sb-bal-right {
  display: flex; flex-direction: column; gap: 6px;
  padding: 16px; border-radius: 16px; position: relative;
  background: rgba(255, 255, 255, .06);
  border: 1px solid rgba(255, 255, 255, .12);
  transition: all .5s ease;
}
.sb-bal-title { font-size: 15px; font-weight: 800; color: #fff; }
.sb-bal-line { font-size: 12.5px; color: rgba(223, 231, 245, .75); }
.sb-bal-left.dodge { opacity: .55; transform: rotate(-1.5deg) translateY(6px); }
.sb-bal-right.win { border-color: rgba(69, 224, 138, .55); background: rgba(69, 224, 138, .1); box-shadow: 0 10px 34px rgba(69, 224, 138, .25); transform: translateY(-6px); }
.sb-bal-vs { align-self: center; font-size: 13px; font-weight: 800; color: rgba(223, 231, 245, .5); }
.sb-stamp {
  position: absolute; top: 10px; right: 12px;
  width: 30px; height: 30px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 17px; font-weight: 800;
  border: 2px solid; opacity: 0; transform: scale(2) rotate(-14deg);
  transition: all .4s cubic-bezier(.2, 1.6, .4, 1);
}
.sb-stamp.bad { color: #ff6b81; border-color: #ff6b81; }
.sb-stamp.ok { color: #45e08a; border-color: #45e08a; }
.sb-bal-left.dodge .sb-stamp.bad { opacity: 1; transform: scale(1) rotate(-10deg); }
.sb-bal-right.win .sb-stamp.ok { opacity: 1; transform: scale(1) rotate(-6deg); }
/* example 演算台 */
.sb-example { width: 100%; max-width: 560px; display: flex; flex-direction: column; gap: 10px; }
.sb-ex-stem {
  font-size: clamp(14px, 2.6vw, 18px); font-weight: 700; color: #fff;
  padding: 14px 18px; border-radius: 14px;
  background: rgba(255, 255, 255, .07);
  border: 1px solid rgba(255, 255, 255, .14);
  border-left: 4px solid var(--vx-accent, #b48cff);
}
.sb-ex-work { display: flex; flex-direction: column; gap: 8px; }
.sb-ex-step {
  font-size: clamp(13px, 2.4vw, 16px); color: #dfe7f5;
  padding: 9px 14px; border-radius: 12px;
  background: rgba(255, 255, 255, .05);
  border: 1px solid rgba(255, 255, 255, .1);
  animation: sb-step-in .45s cubic-bezier(.2, 1.3, .4, 1) both;
}
.sb-ex-step.last { border-color: rgba(69, 224, 138, .4); color: #b9ffd8; }
@keyframes sb-step-in { from { opacity: 0; transform: translateX(-18px); } to { opacity: 1; transform: none; } }
.sb-ex-answer {
  align-self: center;
  font-size: clamp(19px, 3.6vw, 27px);
  padding: 8px 26px; border-radius: 16px;
  color: #123a24; background: linear-gradient(135deg, #5df0a1, #2fce7b);
  box-shadow: 0 8px 30px rgba(69, 224, 138, .45);
}
.vlp-stamp-in-enter-active { transition: all .45s cubic-bezier(.2, 1.6, .4, 1); }
.vlp-stamp-in-enter-from { opacity: 0; transform: scale(2.2) rotate(-8deg); }
/* phrase 金句 */
.sb-phrase { display: flex; flex-wrap: wrap; justify-content: center; gap: 4px; padding: 0 8%; }
.sb-phrase-char {
  font-size: clamp(24px, 5vw, 40px); font-weight: 900; color: #fff;
  text-shadow: 0 2px 18px rgba(0,0,0,.5);
  transition: all .28s ease;
}
/* point 文字批注 */
.sb-point { display: flex; justify-content: center; }
.sb-point-text { font-size: clamp(17px, 3.2vw, 24px); font-weight: 800; color: #fff; transition: opacity .3s ease; }

/* ===== 控制条（vlp-ctlbar，与骨架条解耦 2026-09-05） ===== */
.vlp-ctlbar {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px 12px;
  background: #0d1117;
}
.vlp-btn {
  flex: none;
  min-width: 34px; height: 30px;
  padding: 0 8px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, .12);
  background: rgba(255, 255, 255, .06);
  color: #e8edf7;
  font-size: 13px;
  cursor: pointer;
  transition: all .2s ease;
  font-family: inherit;
}
.vlp-btn:hover { background: rgba(255, 255, 255, .13); border-color: rgba(94, 208, 255, .4); }
.vlp-btn svg { width: 15px; height: 15px; display: block; }
.vlp-time { flex: none; font-size: 11px; color: rgba(232, 237, 247, .65); font-variant-numeric: tabular-nums; }
.vlp-progress {
  position: relative;
  flex: 1;
  height: 6px;
  border-radius: 3px;
  background: rgba(255, 255, 255, .14);
  cursor: pointer;
}
.vlp-progress i {
  position: absolute; left: 0; top: 0; bottom: 0;
  border-radius: 3px;
  background: linear-gradient(90deg, #4d8dff, #5ed0ff);
  transition: width .15s linear;
}
.vlp-dot {
  position: absolute; top: 50%; transform: translate(-50%, -50%);
  width: 7px; height: 7px; border-radius: 50%;
  background: #3a4660;
  transition: all .2s ease;
  pointer-events: none;
}
.vlp-dot.on { background: #5ed0ff; transform: translate(-50%, -50%) scale(1.5); }

/* ===== 加载角标 / 出错横幅 / 被拦层 / 缓冲（2026-09-05 重写：都不遮挡画面） ===== */
.vlp-load-pill {
  position: absolute; right: 12px; bottom: 14%; z-index: 9;
  display: flex; align-items: center; gap: 7px;
  padding: 6px 13px; border-radius: 999px;
  font-size: 11.5px; color: #dfe7f5;
  background: rgba(10, 14, 24, .82);
  border: 1px solid rgba(255, 255, 255, .16);
  pointer-events: none;
}
.vlp-load-spin {
  width: 13px; height: 13px; border-radius: 50%;
  border: 2px solid rgba(148, 205, 255, .16);
  border-top-color: #5ed0ff;
  animation: vlp-spin .9s linear infinite;
}

/* ===== 视频导出进度（2026-09-05：画面+声音合成 webm）===== */
.vlp-exporting {
  position: absolute; left: 50%; top: 10px; transform: translateX(-50%); z-index: 13;
  display: flex; align-items: center; gap: 8px;
  padding: 7px 18px; border-radius: 999px;
  font-size: 12.5px; font-weight: 700; color: #04121f;
  background: linear-gradient(135deg, #7ee0ff, #4d8dff);
  box-shadow: 0 8px 26px rgba(94, 208, 255, .45);
}
.vlp-exporting-spin {
  width: 12px; height: 12px; border-radius: 50%;
  border: 2px solid rgba(4, 18, 31, .25);
  border-top-color: #04121f;
  animation: vlp-spin .8s linear infinite;
}
/* 导出期间收起遮挡层，保证每帧画面干净 */
.vlp.exporting .vlp-blocked, .vlp.exporting .vlp-load-pill,
.vlp.exporting .vlp-audio-banner, .vlp.exporting .vlp-buff,
.vlp.exporting .vlp-author { display: none; }
@keyframes vlp-spin { to { transform: rotate(360deg); } }

.vlp-audio-banner {
  position: absolute; left: 50%; bottom: 10%; transform: translateX(-50%);
  z-index: 9;
  display: flex; align-items: center; gap: 10px;
  max-width: 92%;
  padding: 8px 12px 8px 14px;
  border-radius: 14px;
  background: rgba(18, 10, 12, .9);
  border: 1px solid rgba(255, 107, 129, .45);
  box-shadow: 0 10px 30px rgba(0, 0, 0, .45);
}
.vlp-err-ico {
  width: 26px; height: 26px; border-radius: 50%;
  flex: none;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 800; color: #ff6b81;
  border: 2px solid rgba(255, 107, 129, .5);
  background: rgba(255, 107, 129, .1);
}
.vlp-err-text { display: flex; flex-direction: column; gap: 1px; }
.vlp-err-text b { font-size: 12.5px; color: #ffe9ec; }
.vlp-err-text i { font-style: normal; font-size: 10.5px; color: rgba(255, 226, 231, .6); }
.vlp-retry {
  flex: none;
  padding: 7px 16px; border-radius: 999px;
  font-size: 12px; font-weight: 700; color: #03121f;
  background: linear-gradient(135deg, #7ee0ff, #4d8dff);
  border: none; cursor: pointer; font-family: inherit;
  transition: transform .2s ease, box-shadow .2s ease;
}
.vlp-retry:hover { transform: translateY(-1px); box-shadow: 0 8px 26px rgba(94, 208, 255, .45); }

.vlp-blocked {
  position: absolute; inset: 0; z-index: 12;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px;
  background: rgba(9, 12, 20, .42);
  cursor: pointer;
}
.vlp-big-play {
  width: 66px; height: 66px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  border: none; color: #fff; cursor: pointer;
  background: radial-gradient(circle at 35% 28%, #7ee0ff, #4d8dff 78%);
  box-shadow: 0 12px 40px rgba(77, 141, 255, .55);
  animation: vlp-play-pulse 1.8s ease-in-out infinite;
}
.vlp-big-play svg { width: 26px; height: 26px; margin-left: 3px; }
.vlp-blocked-text {
  font-size: 13px; font-weight: 700; color: #fff;
  text-shadow: 0 1px 6px rgba(0, 0, 0, .8);
}
@keyframes vlp-play-pulse {
  0%, 100% { transform: scale(1); box-shadow: 0 12px 40px rgba(77, 141, 255, .55); }
  50% { transform: scale(1.07); box-shadow: 0 14px 56px rgba(77, 141, 255, .8); }
}

.vlp-buff {
  position: absolute; top: 10px; left: 12px; z-index: 9;
  display: flex; align-items: center; gap: 7px;
  padding: 5px 12px; border-radius: 999px;
  font-size: 11px; color: #dfe7f5;
  background: rgba(10, 14, 24, .82);
  border: 1px solid rgba(255, 255, 255, .14);
  pointer-events: none;
}
.vlp-buff-spin {
  width: 11px; height: 11px; border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, .25);
  border-top-color: #5ed0ff;
  animation: vlp-spin .8s linear infinite;
}

@media (prefers-reduced-motion: reduce) {
  .vlp-stage-bg, .vlp-caret, .vlp-board-underline,
  .vlp-load-spin, .vlp-buff-spin, .vlp-big-play { animation: none !important; }
}

/* ============================================================ */
/* ===== 模板皮肤 10 套（2026-09-05 用户拍板·参考短视频形式）===== */
/* 皮肤 = 舞台底色 + 装饰层(::before) + 构件换肤 + 字幕样式 */
/* 浅色系皮肤统一把默认白字构件压成深墨色（末段共享组）           */
/* ============================================================ */

/* --- ① chalkboard 黑板听讲：绿黑板 + 木质框 + 粉笔字 --- */
.vlp-stage.skin-chalkboard {
  background: radial-gradient(130% 110% at 50% 0%, #1c5136 0%, #123527 55%, #0c251a 100%);
  border: clamp(8px, 1.5vw, 14px) solid #6b4a2a;
  box-shadow: inset 0 0 90px rgba(0, 0, 0, .55), inset 0 0 4px rgba(255, 255, 255, .06);
}
.vlp-stage.skin-chalkboard::before {
  content: "";
  position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(2px 2px at 18% 26%, rgba(255,255,255,.10), transparent 60%),
    radial-gradient(1.5px 1.5px at 64% 78%, rgba(255,255,255,.08), transparent 60%),
    radial-gradient(2px 2px at 82% 12%, rgba(255,255,255,.08), transparent 60%);
}
.vlp-stage.skin-chalkboard .vlp-stage-bg { display: none; }
.vlp-stage.skin-chalkboard .vlp-storyboard { font-family: KaiTi, STKaiti, '楷体', 'Kaiti SC', 'SimSun', serif; }
.vlp-stage.skin-chalkboard .sb-caption, .vlp-stage.skin-chalkboard .sb-point-text,
.vlp-stage.skin-chalkboard .sb-bal-title, .vlp-stage.skin-chalkboard .sb-ex-stem,
.vlp-stage.skin-chalkboard .sb-ex-step, .vlp-stage.skin-chalkboard .sb-phrase-char,
.vlp-stage.skin-chalkboard .sb-hook-q { color: #f2f7e8; text-shadow: 0 1px 8px rgba(0,0,0,.4); }
.vlp-stage.skin-chalkboard .sb-bal-line, .vlp-stage.skin-chalkboard .sb-target { color: rgba(232, 240, 218, .72); }
.vlp-stage.skin-chalkboard .sb-cell {
  background: rgba(255, 255, 255, .06); color: #eef3e0;
  border: 2px solid rgba(240, 246, 228, .65); box-shadow: none;
}
.vlp-stage.skin-chalkboard .sb-cell.l { border-color: #ffd94d; color: #fff8dd; }
.vlp-stage.skin-chalkboard .sb-cell.r { border-color: #7ee0ff; color: #e7f9ff; }
.vlp-stage.skin-chalkboard .sb-ex-stem { border-left: 4px solid #ffd94d; background: rgba(255, 255, 255, .07); }
.vlp-stage.skin-chalkboard .sb-ex-step { background: rgba(255, 255, 255, .05); border: 1px dashed rgba(240, 246, 228, .35); }
.vlp-stage.skin-chalkboard .sb-ex-answer { color: #123a24; background: linear-gradient(135deg, #a8f0c4, #4cc98a); }
.vlp-stage.skin-chalkboard .sub-line.cur { color: #fff5d1; text-shadow: 0 1px 6px rgba(0,0,0,.9); }
.vlp-stage.skin-chalkboard .vlp-kw { color: #ffd94d; background: rgba(255, 217, 77, .12); padding: 1px 5px; border-radius: 4px; }

/* --- ② paper 手写笔记：米白纸纹 + 行线 + 荧光笔划重点 --- */
.vlp-stage.skin-paper {
  background:
    linear-gradient(rgba(58, 50, 38, .08) 1px, transparent 1px) 0 0 / 100% 32px,
    linear-gradient(160deg, #faf4e8 0%, #f2ead6 60%, #f7f1e2 100%);
}
.vlp-stage.skin-paper::before {
  content: "";
  position: absolute; left: 6.5%; top: 0; bottom: 0; width: 2px;
  background: rgba(229, 120, 120, .45); pointer-events: none;
}
.vlp-stage.skin-paper .vlp-stage-bg { display: none; }
.vlp-stage.skin-paper .vlp-storyboard { font-family: KaiTi, STKaiti, '楷体', 'Kaiti SC', serif; }
.vlp-stage.skin-paper .sb-caption, .vlp-stage.skin-paper .sb-point-text,
.vlp-stage.skin-paper .sb-bal-title, .vlp-stage.skin-paper .sb-ex-stem,
.vlp-stage.skin-paper .sb-ex-step, .vlp-stage.skin-paper .sb-hook-q,
.vlp-stage.skin-paper .sb-phrase-char { color: #3a3226; text-shadow: none; }
.vlp-stage.skin-paper .sb-bal-line { color: rgba(58, 50, 38, .72); }
.vlp-stage.skin-paper .sb-target { color: rgba(58, 50, 38, .55); }
.vlp-stage.skin-paper .sb-bal-left, .vlp-stage.skin-paper .sb-bal-right,
.vlp-stage.skin-paper .sb-ex-step {
  background: rgba(255, 252, 240, .78); border: 1px solid #d8c9a8;
  border-radius: 6px; box-shadow: 0 5px 14px rgba(120, 90, 40, .14);
}
.vlp-stage.skin-paper .sb-ex-stem {
  background: #fff8d6; border: 1px solid #ecd98a; border-left: 4px solid #e0b94a;
  transform: rotate(-1.1deg); color: #3a3226;
}
.vlp-stage.skin-paper .sb-cell {
  width: clamp(38px, 6vw, 58px); height: clamp(38px, 6vw, 58px);
  background: #fffdf4; border: 2px solid #cbc188; color: #4a3a26; box-shadow: 0 3px 10px rgba(120, 90, 40, .16);
}
.vlp-stage.skin-paper .sb-cell.l { border-color: #3b6fd4; }
.vlp-stage.skin-paper .sb-cell.r { border-color: #d97a2b; }
.vlp-stage.skin-paper .sb-ex-answer { color: #fff; background: linear-gradient(135deg, #7cae5a, #4c8c3c); }
.vlp-stage.skin-paper .sb-bal-right.win { background: rgba(232, 244, 232, .9); }
.vlp-stage.skin-paper .vlp-kw { color: inherit; background: #ffec9e; padding: 1px 5px; border-radius: 3px; }
.vlp-stage.skin-paper .sub-line.cur { color: #3a3226; text-shadow: 0 1px 2px rgba(255,255,255,.8); }

/* --- ③ whiteboard 白板手绘：马克笔粗线 + 涂鸦风 --- */
.vlp-stage.skin-whiteboard { background: linear-gradient(165deg, #f6f9fd 0%, #eef3fa 70%, #f4f7fc 100%); }
.vlp-stage.skin-whiteboard::before {
  content: "";
  position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(220px 120px at 88% 12%, rgba(47, 111, 224, .10), transparent 70%),
    radial-gradient(200px 120px at 6% 92%, rgba(255, 90, 95, .08), transparent 70%);
}
.vlp-stage.skin-whiteboard .vlp-stage-bg { display: none; }
.vlp-stage.skin-whiteboard .sb-caption, .vlp-stage.skin-whiteboard .sb-point-text,
.vlp-stage.skin-whiteboard .sb-bal-title, .vlp-stage.skin-whiteboard .sb-hook-q,
.vlp-stage.skin-whiteboard .sb-phrase-char { color: #1d2c4c; text-shadow: none; }
.vlp-stage.skin-whiteboard .sb-ex-stem, .vlp-stage.skin-whiteboard .sb-ex-step,
.vlp-stage.skin-whiteboard .sb-bal-left, .vlp-stage.skin-whiteboard .sb-bal-right {
  background: #ffffff; border: 2px solid #b9cdf0; border-radius: 10px;
  color: #23365c; box-shadow: 0 5px 0 rgba(185, 205, 240, .55); text-shadow: none;
}
.vlp-stage.skin-whiteboard .sb-bal-line { color: rgba(35, 54, 92, .75); }
.vlp-stage.skin-whiteboard .sb-ex-stem { border-left-width: 5px; border-left-color: #2f6fe0; }
.vlp-stage.skin-whiteboard .sb-ex-step.last { border-color: #57c183; color: #1f6e45; }
.vlp-stage.skin-whiteboard .sb-ex-answer { background: #2f9e63; box-shadow: 0 6px 0 rgba(47, 158, 99, .4); }
.vlp-stage.skin-whiteboard .sb-cell {
  background: #fff; border: 2px solid #7ba3e8; color: #12294f;
  box-shadow: 0 4px 0 rgba(123, 163, 232, .5);
}
.vlp-stage.skin-whiteboard .sb-cell.l { border-color: #2f6fe0; }
.vlp-stage.skin-whiteboard .sb-cell.r { border-color: #ff5a5f; }
.vlp-stage.skin-whiteboard .sb-target { color: rgba(29, 44, 76, .6); }
.vlp-stage.skin-whiteboard .vlp-kw { color: #2f6fe0; font-weight: 800; }
.vlp-stage.skin-whiteboard .sub-line.cur { color: #16263f; text-shadow: 0 1px 2px rgba(255,255,255,.9); }

/* --- ④ chat 聊天流：微信风气泡对话 --- */
.vlp-stage.skin-chat { background: linear-gradient(170deg, #e9edf3 0%, #dfe5ee 100%); }
.vlp-stage.skin-chat::before {
  content: "";
  position: absolute; top: 0; left: 0; right: 0; height: 4px;
  background: #4d8dff; pointer-events: none;
}
.vlp-stage.skin-chat .vlp-stage-bg { display: none; }
.vlp-stage.skin-chat .sb-caption, .vlp-stage.skin-chat .sb-point-text,
.vlp-stage.skin-chat .sb-bal-title, .vlp-stage.skin-chat .sb-ex-answer { color: #1f2733; text-shadow: none; }
.vlp-stage.skin-chat .sb-point-text, .vlp-stage.skin-chat .sb-caption {
  background: #ffffff; padding: 12px 18px; border-radius: 16px 16px 16px 4px;
  box-shadow: 0 4px 12px rgba(40, 60, 100, .10); font-weight: 700;
}
.vlp-stage.skin-chat .sb-example { max-width: 640px; }
.vlp-stage.skin-chat .sb-ex-stem {
  background: #ffffff; color: #1f2733; border-left: 4px solid #4d8dff;
  border-radius: 15px 15px 15px 4px; box-shadow: 0 4px 12px rgba(40, 60, 100, .10);
}
.vlp-stage.skin-chat .sb-ex-work { align-items: flex-end; }
.vlp-stage.skin-chat .sb-ex-step {
  background: #b9dcff; color: #0c2c4a; border-radius: 15px 15px 4px 15px;
  border: none; box-shadow: 0 3px 10px rgba(40, 60, 100, .10); max-width: 86%;
}
.vlp-stage.skin-chat .sb-ex-step.last { background: #c9f2da; color: #0f4a2b; }
.vlp-stage.skin-chat .sb-bal-left, .vlp-stage.skin-chat .sb-bal-right {
  background: #ffffff; border: none; border-radius: 16px; box-shadow: 0 4px 12px rgba(40, 60, 100, .10);
}
.vlp-stage.skin-chat .sb-bal-title { color: #1f2733; }
.vlp-stage.skin-chat .sb-bal-line { color: rgba(31, 39, 51, .75); }
.vlp-stage.skin-chat .sb-bal-vs { color: rgba(31, 39, 51, .45); background: rgba(120, 140, 170, .15); padding: 2px 8px; border-radius: 8px; }
.vlp-stage.skin-chat .sb-bal-right.win { background: #e9fbf0; }
.vlp-stage.skin-chat .sb-cell {
  background: #ffffff; border: none; color: #1f2733; box-shadow: 0 4px 10px rgba(40, 60, 100, .12);
}
.vlp-stage.skin-chat .sb-hook-q { color: #ffffff; background: #4d8dff; display: inline-block; padding: 16px 22px; border-radius: 18px 18px 18px 4px; box-shadow: 0 8px 20px rgba(77, 141, 255, .35); }
.vlp-stage.skin-chat .sb-target, .vlp-stage.skin-chat .sb-note { color: #5b6b85; }
.vlp-stage.skin-chat .sb-note { background: rgba(120, 140, 170, .18); border: none; }
.vlp-stage.skin-chat .sb-note.good { background: rgba(47, 158, 99, .16); color: #1f6e45; }
.vlp-stage.skin-chat .sub-line.cur { color: #ffffff; text-shadow: 0 1px 3px rgba(0,0,0,.55); }

/* --- ⑤ qa 问答反转：深夜抢答，大卡片揭晓 --- */
.vlp-stage.skin-qa { background: radial-gradient(120% 120% at 70% 0%, #241b52 0%, #160f38 55%, #0d0926 100%); }
.vlp-stage.skin-qa::before {
  content: "?";
  position: absolute; right: 4%; top: 2%; pointer-events: none;
  font-size: clamp(120px, 26vw, 240px); font-weight: 900; line-height: 1;
  color: rgba(255, 255, 255, .055);
}
.vlp-stage.skin-qa .vlp-stage-bg { display: none; }
.vlp-stage.skin-qa .sb-ex-stem {
  background: linear-gradient(135deg, #8b5cff 0%, #4d8dff 100%);
  border: none; color: #fff; box-shadow: 0 12px 34px rgba(77, 141, 255, .4);
}
.vlp-stage.skin-qa .sb-ex-step {
  background: rgba(255, 224, 168, .14); border: 1px solid rgba(255, 217, 161, .45);
  color: #ffe1a8; box-shadow: none;
}
.vlp-stage.skin-qa .sb-ex-step.last { border-color: #ffd35e; color: #ffefc4; }
.vlp-stage.skin-qa .sb-ex-answer {
  color: #3a2600; background: linear-gradient(135deg, #ffd35e, #ffb020);
  box-shadow: 0 10px 40px rgba(255, 176, 32, .5);
}
.vlp-stage.skin-qa .sb-bal-left, .vlp-stage.skin-qa .sb-bal-right,
.vlp-stage.skin-qa .sb-cell {
  background: rgba(255, 255, 255, .07); border: 1px solid rgba(255, 255, 255, .22); color: #efeaff;
}
.vlp-stage.skin-qa .sb-phrase-char { color: #ffe9a8; }
.vlp-stage.skin-qa .sb-hook-q { text-shadow: 0 0 22px rgba(139, 92, 255, .8); }
.vlp-stage.skin-qa .sub-line.cur { color: #fff; text-shadow: 0 0 14px rgba(139, 92, 255, .9); }

/* --- ⑥ fun 弹幕贴纸：糖果马卡龙 + 贴纸 + 活泼弹跳 --- */
.vlp-stage.skin-fun { background: linear-gradient(135deg, #ffe9c7 0%, #ffd9e8 55%, #d8efff 100%); }
.vlp-stage.skin-fun::before {
  content: "✨";
  position: absolute; right: 6%; top: 5%; pointer-events: none;
  font-size: clamp(48px, 9vw, 84px); opacity: .5; transform: rotate(14deg);
}
.vlp-stage.skin-fun .vlp-stage-bg { display: none; }
.vlp-stage.skin-fun .sb-caption, .vlp-stage.skin-fun .sb-point-text,
.vlp-stage.skin-fun .sb-bal-title, .vlp-stage.skin-fun .sb-hook-q,
.vlp-stage.skin-fun .sb-phrase-char { color: #4a2f55; text-shadow: none; }
.vlp-stage.skin-fun .sb-point-text { background: #fff; padding: 10px 18px; border-radius: 14px; border: 3px solid #7c5cff; transform: rotate(-1.6deg); box-shadow: 0 6px 0 rgba(124, 92, 255, .3); }
.vlp-stage.skin-fun .sb-ex-stem, .vlp-stage.skin-fun .sb-ex-step,
.vlp-stage.skin-fun .sb-bal-left, .vlp-stage.skin-fun .sb-bal-right {
  background: #ffffff; border: 3px solid #7c5cff; border-radius: 16px;
  color: #3d2a55; box-shadow: 0 6px 0 rgba(124, 92, 255, .28); text-shadow: none;
}
.vlp-stage.skin-fun .sb-ex-step:nth-child(odd) { transform: rotate(-1.4deg); border-color: #ff7eb0; box-shadow: 0 6px 0 rgba(255, 126, 176, .3); }
.vlp-stage.skin-fun .sb-ex-step:nth-child(even) { transform: rotate(1.2deg); border-color: #43b8ff; box-shadow: 0 6px 0 rgba(67, 184, 255, .3); }
.vlp-stage.skin-fun .sb-ex-answer { background: linear-gradient(135deg, #ff8fab, #ffb84d); box-shadow: 0 8px 24px rgba(255, 143, 171, .5); }
.vlp-stage.skin-fun .sb-bal-left { border-color: #ff7eb0; box-shadow: 0 6px 0 rgba(255, 126, 176, .3); }
.vlp-stage.skin-fun .sb-bal-right { border-color: #43b8ff; box-shadow: 0 6px 0 rgba(67, 184, 255, .3); }
.vlp-stage.skin-fun .sb-cell {
  background: #ffffff; border: 3px solid #43b8ff; color: #2b3a66; box-shadow: 0 5px 0 rgba(67, 184, 255, .35);
}
.vlp-stage.skin-fun .sb-bal-line { color: rgba(61, 42, 85, .75); }
.vlp-stage.skin-fun .sb-target { color: #8b6f9c; }
.vlp-stage.skin-fun .vlp-kw { color: #e64980; background: #ffe3ef; padding: 1px 5px; border-radius: 6px; }
.vlp-stage.skin-fun .sub-line.cur { color: #4a2f55; text-shadow: 0 1px 2px rgba(255,255,255,.85); }

/* --- ⑦ neon 赛博霓虹：黑底发光 + 网格扫描线 --- */
.vlp-stage.skin-neon { background: #04060f; }
.vlp-stage.skin-neon::before {
  content: "";
  position: absolute; inset: 0; pointer-events: none;
  background:
    repeating-linear-gradient(0deg, rgba(94, 208, 255, .045) 0 1px, transparent 1px 44px),
    repeating-linear-gradient(90deg, rgba(94, 208, 255, .045) 0 1px, transparent 1px 44px),
    repeating-linear-gradient(0deg, rgba(0, 0, 0, .22) 0 2px, transparent 2px 5px);
}
.vlp-stage.skin-neon .vlp-stage-bg { display: none; }
.vlp-stage.skin-neon .sb-caption, .vlp-stage.skin-neon .sb-point-text,
.vlp-stage.skin-neon .sb-bal-title, .vlp-stage.skin-neon .sb-hook-q,
.vlp-stage.skin-neon .sb-ex-stem, .vlp-stage.skin-neon .sb-ex-step,
.vlp-stage.skin-neon .sb-phrase-char { color: #d9f6ff; text-shadow: 0 0 10px rgba(94, 208, 255, .75); }
.vlp-stage.skin-neon .sb-bal-line, .vlp-stage.skin-neon .sb-target { color: rgba(160, 220, 240, .66); }
.vlp-stage.skin-neon .sb-ex-stem, .vlp-stage.skin-neon .sb-ex-step,
.vlp-stage.skin-neon .sb-bal-left, .vlp-stage.skin-neon .sb-bal-right,
.vlp-stage.skin-neon .sb-cell {
  background: rgba(8, 18, 30, .85); border: 1px solid rgba(94, 208, 255, .5);
  box-shadow: 0 0 16px rgba(94, 208, 255, .22), inset 0 0 18px rgba(94, 208, 255, .06);
  color: #d9f6ff;
}
.vlp-stage.skin-neon .sb-ex-stem { border-left: 4px solid #5ed0ff; }
.vlp-stage.skin-neon .sb-bal-right.win { border-color: rgba(69, 224, 138, .6); box-shadow: 0 0 22px rgba(69, 224, 138, .3); }
.vlp-stage.skin-neon .sb-bal-left.dodge { border-color: rgba(255, 107, 129, .55); box-shadow: 0 0 20px rgba(255, 107, 129, .22); }
.vlp-stage.skin-neon .sb-sum { text-shadow: 0 0 14px rgba(94, 208, 255, .9); }
.vlp-stage.skin-neon .sb-phrase-char { text-shadow: 0 0 16px rgba(180, 140, 255, .8); }
.vlp-stage.skin-neon .sub-line.cur { text-shadow: 0 0 12px rgba(94, 208, 255, .85); }

/* --- ⑧ mindmap 思维导图：中心词 + 分支节点 --- */
.vlp-stage.skin-mindmap { background: linear-gradient(160deg, #f6f8f3 0%, #eef3ea 70%, #f4f7f0 100%); }
.vlp-stage.skin-mindmap::before {
  content: "";
  position: absolute; left: 12%; top: 50%; width: 76%; height: 76%; pointer-events: none;
  transform: translateY(-50%);
  background:
    linear-gradient(90deg, rgba(63, 140, 88, .35) 0 3px, transparent 3px),
    radial-gradient(circle at left center, rgba(63, 140, 88, .28) 0 12px, transparent 13px),
    linear-gradient(155deg, transparent 46%, rgba(63, 140, 88, .22) 50%, transparent 54%),
    linear-gradient(25deg, transparent 46%, rgba(63, 140, 88, .22) 50%, transparent 54%);
}
.vlp-stage.skin-mindmap .vlp-stage-bg { display: none; }
.vlp-stage.skin-mindmap .sb-caption, .vlp-stage.skin-mindmap .sb-point-text,
.vlp-stage.skin-mindmap .sb-bal-title, .vlp-stage.skin-mindmap .sb-hook-q,
.vlp-stage.skin-mindmap .sb-phrase-char { color: #2c4233; text-shadow: none; }
.vlp-stage.skin-mindmap .sb-bal-title, .vlp-stage.skin-mindmap .sb-caption {
  background: #fff; border: 2px solid #7fb98c; border-radius: 999px; padding: 6px 18px; display: inline-block;
}
.vlp-stage.skin-mindmap .sb-ex-stem, .vlp-stage.skin-mindmap .sb-ex-step,
.vlp-stage.skin-mindmap .sb-bal-left, .vlp-stage.skin-mindmap .sb-bal-right {
  position: relative; background: #ffffff; border: 2px solid #7fb98c; border-radius: 14px;
  color: #2c4233; box-shadow: 0 4px 12px rgba(63, 140, 88, .16); text-shadow: none;
}
.vlp-stage.skin-mindmap .sb-ex-step::before, .vlp-stage.skin-mindmap .sb-bal-line::before {
  content: ""; display: inline-block; width: 8px; height: 8px; border-radius: 50%;
  background: #3f8c58; margin-right: 8px; vertical-align: 2px;
}
.vlp-stage.skin-mindmap .sb-bal-line { color: rgba(44, 66, 51, .78); }
.vlp-stage.skin-mindmap .sb-ex-answer { background: #2f9e63; box-shadow: 0 6px 18px rgba(47, 158, 99, .4); }
.vlp-stage.skin-mindmap .sb-cell { background: #fff; border: 2px solid #7fb98c; color: #2c4233; box-shadow: 0 3px 8px rgba(63, 140, 88, .2); }
.vlp-stage.skin-mindmap .sb-target { color: rgba(44, 66, 51, .6); }
.vlp-stage.skin-mindmap .vlp-kw { color: #1f6e45; }
.vlp-stage.skin-mindmap .sub-line.cur { color: #22382a; text-shadow: 0 1px 2px rgba(255,255,255,.9); }

/* --- ⑨ glass 玻璃流光：默认氛围 + 玻璃拟态（品牌一致） --- */
.vlp-stage.skin-glass::before {
  content: "";
  position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(118deg, transparent 40%, rgba(255, 255, 255, .07) 50%, transparent 60%);
}
.vlp-stage.skin-glass .sb-ex-stem, .vlp-stage.skin-glass .sb-ex-step,
.vlp-stage.skin-glass .sb-bal-left, .vlp-stage.skin-glass .sb-bal-right,
.vlp-stage.skin-glass .sb-cell {
  background: rgba(255, 255, 255, .10); border: 1px solid rgba(255, 255, 255, .24);
  backdrop-filter: blur(8px);
}
.vlp-stage.skin-glass .sb-ex-step { background: rgba(255, 255, 255, .08); }

/* --- ⑩ compare 左右擂台：错 vs 对分屏对决 --- */
.vlp-stage.skin-compare::before {
  content: "";
  position: absolute; inset: 0; pointer-events: none;
  background:
    radial-gradient(50% 100% at 0% 50%, rgba(255, 90, 95, .16), transparent 55%),
    radial-gradient(50% 100% at 100% 50%, rgba(69, 224, 138, .14), transparent 55%),
    linear-gradient(90deg, transparent 49.6%, rgba(255, 255, 255, .22) 50%, transparent 50.4%);
}
.vlp-stage.skin-compare .sb-bal { gap: 22px; }
.vlp-stage.skin-compare .sb-bal-left, .vlp-stage.skin-compare .sb-bal-right { border-radius: 18px; }
.vlp-stage.skin-compare .sb-bal-left.dodge {
  border-color: rgba(255, 107, 129, .65); background: rgba(255, 90, 95, .08);
  box-shadow: 0 10px 34px rgba(255, 90, 95, .25);
}
.vlp-stage.skin-compare .sb-bal-right.win {
  border-color: rgba(69, 224, 138, .7);
  box-shadow: 0 12px 40px rgba(69, 224, 138, .3);
}
.vlp-stage.skin-compare .sb-bal-vs {
  font-size: 15px; padding: 4px 12px; border-radius: 999px;
  background: rgba(255, 255, 255, .1); border: 1px solid rgba(255, 255, 255, .3);
}

/* ===== 浅色皮肤共享修正：默认白字一律压成深墨 ===== */
.vlp-stage.skin-paper .sb-ex-answer, .vlp-stage.skin-whiteboard .sb-ex-answer,
.vlp-stage.skin-fun .sb-ex-answer, .vlp-stage.skin-mindmap .sb-ex-answer,
.vlp-stage.skin-chat .sb-ex-answer, .vlp-stage.skin-chalkboard .sb-ex-answer { color: #fff; }
/* 浅色皮肤的点批注/例题/标题不再用发光白字 */
.vlp-stage.skin-paper .sb-bal-right.win, .vlp-stage.skin-whiteboard .sb-bal-right.win,
.vlp-stage.skin-fun .sb-bal-right.win, .vlp-stage.skin-mindmap .sb-bal-right.win,
.vlp-stage.skin-chat .sb-bal-right.win { color: inherit; }
.vlp-stage.skin-paper .sb-note, .vlp-stage.skin-whiteboard .sb-note,
.vlp-stage.skin-fun .sb-note, .vlp-stage.skin-mindmap .sb-note,
.vlp-stage.skin-chat .sb-note { color: #7a5c24; }
/* 浅色皮肤下方黑边太硬：压淡 */
.vlp-stage.skin-paper .vlp-letterbox, .vlp-stage.skin-whiteboard .vlp-letterbox,
.vlp-stage.skin-chat .vlp-letterbox, .vlp-stage.skin-fun .vlp-letterbox,
.vlp-stage.skin-mindmap .vlp-letterbox { background: rgba(0, 0, 0, .45); }
</style>