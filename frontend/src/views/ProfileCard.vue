<template>
  <div class="du-root">
    <!-- 3D 太阳系背景画布 -->
    <div ref="hub3dRef" class="hub-3d"></div>

    <!-- 顶栏 -->
    <div class="du-topbar">
      <h1>维度宇宙</h1>
      <button class="g-btn" @click="loadData" :disabled="loading">
        <el-icon :class="{ spin: loading }"><Refresh /></el-icon>
      </button>
    </div>

    <!-- 维度清单：九个维度各自的关键数值与数据状态（点星球之外的第二条入口） -->
    <div class="du-panel" v-if="!activeDim">
      <div class="du-panel-head">
        <span>学习维度</span>
        <em>{{ dimensionList.filter(x => x.has).length }} / 9 有数据</em>
      </div>
      <button
        v-for="dim in dimensionList"
        :key="dim.key"
        class="du-item"
        :class="{ 'is-empty': !dim.has }"
        @click="enterDimension(dim.key)"
      >
        <i class="du-dot" :style="{ background: dim.color, boxShadow: `0 0 8px ${dim.color}` }"></i>
        <span class="du-name">{{ dim.label }}</span>
        <span class="du-stat">{{ dim.has ? dim.stat : '暂无数据' }}</span>
      </button>
    </div>

    <!-- 底栏提示 -->
    <div class="du-bottombar" v-if="!activeDim">
      <span><el-icon><Mouse /></el-icon> 拖拽旋转</span>
      <span><el-icon><ZoomIn /></el-icon> 滚轮缩放</span>
      <span>点击星球进入维度</span>
      <span>点中央黑洞退出</span>
    </div>

    <!-- 维度信息浮层（跟随光标，只留名字/说明） -->
    <Transition name="fade">
      <div v-if="hoveredPlanet && !activeDim" class="planet-tooltip" :style="tooltipStyle">
        <div class="tt-name">{{ hoveredPlanet.label }}</div>
        <div class="tt-sub">{{ hoveredPlanet.sub }}</div>
      </div>
    </Transition>

    <!-- 坐标读数：右上角常驻面板，字号放大到一眼能读 -->
    <div class="du-hud" v-if="!activeDim">
      <div class="hud-head">
        <span class="hud-dot" :style="hudDim ? { background: hudDim.color, boxShadow: `0 0 10px ${hudDim.color}` } : {}"></span>
        <span class="hud-title">{{ hudDim?.label || '天体坐标' }}</span>
      </div>
      <template v-if="hoverCoord">
        <div class="hud-row"><span>轨道半径 R</span><b>{{ hoverCoord.r }}</b></div>
        <div class="hud-row"><span>相位角 θ</span><b>{{ hoverCoord.deg }}°</b></div>
        <div class="hud-row"><span>轨道倾角 i</span><b>{{ hoverCoord.incl }}°</b></div>
        <div class="hud-row"><span>离面高度 y</span><b>{{ hoverCoord.y }}</b></div>
      </template>
      <div v-else class="hud-idle">悬停任意星球查看坐标</div>
    </div>

    <!-- 退出转场全程在 3D 里完成（行星吸入 → 涌来一股粒子 → 切主页），不盖 DOM 遮罩 -->

    <!-- ====== 详情面板 ====== -->
    <Transition name="detail">
      <div v-if="activeDim" class="detail-overlay">
      <div class="detail-panel">
        <div class="dp-header">
          <button class="g-btn" @click="closeDetail"><el-icon><ArrowLeft /></el-icon> 返回宇宙</button>
          <h2 :style="{ color: currentDim?.color || '#fff' }">{{ currentDim?.label || '' }}</h2>
        </div>
        <div class="dp-body">
          <!-- 知识星系 -->
          <div v-if="activeDim === 'knowledge'" class="dim-card">
            <template v-if="hasKnowledge">
              <div class="dim-stats">
                <div class="stat"><b>{{ kbStats.count }}</b><span>知识点</span></div>
                <div class="stat"><b>{{ kbStats.avg }}</b><span>平均掌握度</span></div>
                <div class="stat stat-good"><b>{{ kbStats.strong }}</b><span>已掌握 ≥80</span></div>
                <div class="stat stat-weak"><b>{{ kbStats.weak }}</b><span>待加强 &lt;60</span></div>
              </div>
              <div ref="knowledgeRef" class="chart-box"></div>
              <p class="dim-hint">每根射线是一个知识点 · 长度与颜色代表掌握度 · 取掌握度最高的 18 个</p>
            </template>
            <div v-else class="empty-dim">完成一些题目后，知识星系将为你点亮，展示各知识点的掌握度分布</div>
          </div>

          <!-- 能力雷达 -->
          <div v-else-if="activeDim === 'ability'" class="dim-card">
            <template v-if="hasAbility">
              <div class="dim-stats">
                <div class="stat"><b>{{ abilityStats.dims }}</b><span>能力维度</span></div>
                <div class="stat"><b>{{ abilityStats.samples }}</b><span>计入题目</span></div>
                <div class="stat stat-good" v-if="abilityStats.best"><b>{{ abilityStats.bestScore }}</b><span>最强 · {{ abilityStats.best }}</span></div>
              </div>
              <div ref="radarRef" class="chart-box"></div>
              <p class="dim-hint">按题型归算：选择/判断→概念理解，填空→记忆能力，计算/编程→计算能力，简答→逻辑推理</p>
            </template>
            <div v-else class="empty-dim">完成题目后，能力雷达将从多个维度分析你的学习能力</div>
          </div>

          <!-- 学习节奏 -->
          <div v-else-if="activeDim === 'rhythm'" class="dim-card">
            <template v-if="hasRhythm">
              <div class="dim-stats">
                <div class="stat"><b>{{ data.learning_rhythm?.current_streak || 0 }}</b><span>当前连续(天)</span></div>
                <div class="stat"><b>{{ data.learning_rhythm?.max_streak || 0 }}</b><span>最长连续(天)</span></div>
                <div class="stat"><b>{{ data.learning_rhythm?.total_active_days || 0 }}</b><span>活跃天数</span></div>
                <div class="stat" v-if="rhythmPeak"><b>{{ rhythmPeak }}</b><span>活跃时段</span></div>
              </div>
              <div ref="calendarRef" class="chart-box"></div>
              <p class="dim-hint">近 90 天学习热力 · 颜色越亮当天活动越多</p>
            </template>
            <div v-else class="empty-dim">开始学习后，这里会展示你的学习热力日历和活跃分析</div>
          </div>

          <!-- 认知偏好 -->
          <div v-else-if="activeDim === 'cognitive'" class="dim-card">
            <template v-if="hasCognitive">
              <div class="dim-stats">
                <div class="stat"><b>{{ cogStats.total }}</b><span>生成题目</span></div>
                <div class="stat"><b>{{ cogStats.kinds }}</b><span>题型数</span></div>
                <div class="stat" v-if="cogStats.top"><b>{{ cogStats.topPct }}%</b><span>偏好 · {{ cogStats.top }}</span></div>
              </div>
              <div ref="cognitiveBarRef" class="chart-box" style="height:300px"></div>
              <p class="dim-hint">{{ data.cognitive_preference?.detail || '' }}</p>
            </template>
            <div v-else class="empty-dim">使用 AI 生成题目后，这里会展示你的题型偏好和知识点兴趣分布</div>
          </div>

          <!-- 易错地图 -->
          <div v-else-if="activeDim === 'mistake'" class="dim-card">
            <template v-if="hasMistakes">
              <div class="dim-stats">
                <div class="stat"><b>{{ mistakeStats.total }}</b><span>错题总数</span></div>
                <div class="stat"><b>{{ mistakeStats.kinds }}</b><span>涉及知识点</span></div>
                <div class="stat" :class="mistakeStats.rate >= 50 ? 'stat-good' : 'stat-weak'"><b>{{ mistakeStats.rate }}%</b><span>攻克率</span></div>
              </div>
              <div ref="treemapRef" class="chart-box"></div>
              <p class="dim-hint">方块越大该知识点错题越多 · 绿色为已攻克</p>
            </template>
            <div v-else class="empty-dim">做题后如果产生了错题，这里会用树图展示你的易错知识点分布</div>
          </div>

          <!-- 成长轨迹 -->
          <div v-else-if="activeDim === 'growth'" class="dim-card">
            <template v-if="hasGrowth">
              <div class="dim-stats">
                <div class="stat"><b>{{ growthStats.last }}</b><span>最新掌握度</span></div>
                <div class="stat" :class="growthStats.delta >= 0 ? 'stat-good' : 'stat-weak'">
                  <b>{{ growthStats.delta >= 0 ? '+' : '' }}{{ growthStats.delta }}</b><span>较起始变化</span>
                </div>
                <div class="stat"><b>{{ growthStats.days }}</b><span>记录天数</span></div>
              </div>
              <div ref="growthRef" class="chart-box"></div>
              <p class="dim-hint">按每个学习日的平均掌握度绘制 · 只统计已作答的题</p>
            </template>
            <div v-else class="empty-dim">持续学习后，这里会展示你掌握度的变化轨迹</div>
          </div>

          <!-- 学习人格 -->
          <div v-else-if="activeDim === 'personality'" class="personality-card">
            <div class="pc-glow"></div>
            <div class="pc-type">{{ data.personality?.type || '探索型学习者' }}</div>
            <div class="pc-tags"><span v-for="t in data.personality?.tags||['数据采集中']" :key="t" class="pc-tag">{{ t }}</span></div>
            <p class="pc-desc">{{ data.personality?.description || '完成更多学习任务后，AI 将为你生成详细的个性化学习人格画像。' }}</p>
          </div>

          <!-- 兴趣星云 -->
          <div v-else-if="activeDim === 'interest'" class="dim-card">
            <template v-if="hasInterest">
              <div class="dim-stats">
                <div class="stat"><b>{{ interestStats.count }}</b><span>探索领域</span></div>
                <div class="stat" v-if="interestStats.top"><b>{{ interestStats.topCount }}</b><span>最多 · {{ interestStats.top }}</span></div>
              </div>
              <div ref="interest3dRef" class="int-3d"></div>
              <p class="dim-hint">球体越大代表该领域生成题目越多 · 可拖拽旋转</p>
            </template>
            <div v-else class="empty-dim">生成题目后，兴趣星云将展示你的知识探索领域分布，可拖拽旋转的 3D 球体</div>
          </div>

          <!-- AI 洞见：不是复述数字，而是「一条洞察 + 可执行的下一步」 -->
          <div v-else-if="activeDim === 'summary'" class="dim-card">
            <div class="sb-quote">“</div>
            <p class="sb-text">{{ displaySummary }}<span v-if="typing" class="sb-cursor">|</span></p>
            <div v-if="aiActions.length" class="sb-actions">
              <div class="sb-actions-title">下一步做什么</div>
              <div v-for="(a, i) in aiActions" :key="i" class="sb-action">
                <span class="sb-action-idx">{{ i + 1 }}</span>
                <div class="sb-action-body">
                  <b>{{ a.title }}</b>
                  <em v-if="a.reason">{{ a.reason }}</em>
                </div>
              </div>
            </div>
            <div class="sb-foot">{{ data.generated_at ? '生成于 ' + String(data.generated_at).slice(0, 16).replace('T', ' ') : '' }}</div>
          </div>
        </div>
      </div>
      </div>
    </Transition>

    <!-- 加载层已移除：进场推进动画本身就是加载过程，再盖一层「扫描维度中」是重复且跳戏 -->
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore, hexToRgb } from '@/stores/theme'
import { ArrowLeft, Refresh, Mouse, ZoomIn } from '@element-plus/icons-vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { CSS3DRenderer, CSS3DObject } from 'three/addons/renderers/CSS3DRenderer.js'
import * as echarts from 'echarts'
import {
  PLANET_SPECS, makePlanetSurface, makeCloudTexture,
  makeRingTexture, getPlaceholderTexture,
} from '@/utils/planetTexture'
import { createBlackHole, createStardust, HORIZON_R } from '@/utils/blackHole'
import { clamp, smooth } from '@/utils/procedural'
import 'echarts-gl'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const themeStore = useThemeStore()
// ECharts canvas 不认 CSS var()/color-mix——品牌色半透明需 JS 解析成 rgba（2026-09-02 主题定制）
function brandSoft(alpha) {
  const c = hexToRgb(themeStore.brandColor) || { r: 64, g: 158, b: 255 }
  return `rgba(${c.r}, ${c.g}, ${c.b}, ${alpha})`
}

// ===== 详情面板图表统一样式（所有维度共用一套视觉语言）=====
const TIP = {
  backgroundColor: 'rgba(14,16,26,0.94)',
  borderColor: 'rgba(255,255,255,0.12)',
  borderWidth: 1,
  padding: [9, 13],
  textStyle: { color: '#e8eaf2', fontSize: 12 },
  extraCssText: 'border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.5);backdrop-filter:blur(6px);'
}
const AXIS_LABEL = { color: 'rgba(255,255,255,0.45)', fontSize: 11 }
const SPLIT_LINE = { lineStyle: { color: 'rgba(255,255,255,0.07)', type: [4, 4] } }
const loading = ref(false)
const activeDim = ref(null)
const hoveredPlanet = ref(null)
const hoverCoord = ref(null)   // 悬停时的实时极坐标读数
let warping = false, warpStart = 0
const WARP_DUR = 1250          // 出场总时长：吸行星 → 涌来一股粒子 → 直接切主页
let warpBase = null            // 出场淡出用的基准不透明度（见 anim 里的说明）
const tooltipStyle = ref({})
const data = ref({ knowledge_base:{}, ability_radar:{}, learning_rhythm:{}, cognitive_preference:{}, mistake_map:{}, growth_trajectory:{}, personality:{}, interest_field:{}, ai_summary:'' })
const displaySummary = ref('')
const typing = ref(false)

// incl=轨道倾角、node=升交点：真实星系不是共面的，纯平面看着很假
const dimensions = [
  { key:'knowledge',  label:'知识星系', sub:'掌握度 · 星爆图',   color: themeStore.brandColor, orbit:2.8, speed:0.15, size:1.4, incl:2,  node:0 },
  { key:'ability',    label:'能力雷达', sub:'多维度 · 雷达图',   color:'#8b5cf6', orbit:3.6, speed:0.12, size:1.1, incl:-6, node:40 },
  { key:'rhythm',     label:'学习节奏', sub:'活跃度 · 热力日历', color:'#10b981', orbit:4.4, speed:0.10, size:1.0, incl:9,  node:95 },
  { key:'cognitive',  label:'认知偏好', sub:'题型分布 · 条形图', color:'#f59e0b', orbit:5.2, speed:0.09, size:1.0, incl:-4, node:150 },
  { key:'mistake',    label:'易错地图', sub:'错题分析 · 树图',   color:'#ef4444', orbit:6.0, speed:0.08, size:1.2, incl:13, node:205 },
  { key:'growth',     label:'成长轨迹', sub:'趋势 · 渐近线',     color:'#06b6d4', orbit:6.8, speed:0.07, size:1.0, incl:-11, node:260 },
  { key:'personality',label:'学习人格', sub:'AI 画像 · 深度洞察',color:'#ec4899', orbit:7.6, speed:0.06, size:1.3, incl:6,  node:315 },
  { key:'interest',   label:'兴趣星云', sub:'知识领域 · 3D 球体',color:'#f97316', orbit:8.4, speed:0.05, size:1.1, incl:-16, node:20 },
  { key:'summary',    label:'AI 洞见',  sub:'洞察 + 行动建议',   color:'#a78bfa', orbit:9.2, speed:0.04, size:1.0, incl:18, node:75 },
]
const currentDim = computed(() => dimensions.find(d => d.key === activeDim.value))

// 数据存在性检查
const hasKnowledge = computed(() => (data.value.knowledge_base?.list || []).length > 0)
const hasAbility = computed(() => Object.keys(data.value.ability_radar || {}).length > 0 && data.value.knowledge_base?.list?.length > 0)
const hasRhythm = computed(() => (data.value.learning_rhythm?.total_active_days || 0) > 0)
const hasCognitive = computed(() => (data.value.cognitive_preference?.types || []).length > 0)
const hasMistakes = computed(() => (data.value.mistake_map?.list || []).length > 0)
const hasGrowth = computed(() => (data.value.growth_trajectory?.points || []).length > 1)
const hasInterest = computed(() => (data.value.interest_field?.list || []).length > 0)

// ===== 详情面板 KPI（全部来自真实数据，不编数） =====
const kbStats = computed(() => {
  const kb = data.value.knowledge_base || {}
  const l = kb.list || []
  const scores = l.map(x => x.score || 0)
  return {
    count: kb.topic_count || l.length,
    avg: kb.avg_score || 0,
    strong: scores.filter(s => s >= 80).length,
    weak: scores.filter(s => s < 60).length
  }
})
const abilityStats = computed(() => {
  const rd = data.value.ability_radar || {}
  const ks = Object.keys(rd)
  const sorted = [...ks].sort((a, b) => (rd[b]?.score || 0) - (rd[a]?.score || 0))
  const best = sorted[0]
  return {
    dims: ks.length,
    samples: ks.reduce((s, k) => s + (rd[k]?.sample || 0), 0),
    best, bestScore: best ? rd[best]?.score || 0 : 0
  }
})
const rhythmPeak = computed(() => {
  const p = (data.value.learning_rhythm?.peak_hours || [])[0]
  return p && p.count ? `${String(p.hour).padStart(2, '0')}:00` : ''
})
const cogStats = computed(() => {
  const t = data.value.cognitive_preference?.types || []
  const total = t.reduce((s, x) => s + (x.value || 0), 0)
  const top = [...t].sort((a, b) => (b.value || 0) - (a.value || 0))[0]
  return {
    total, kinds: t.length,
    top: top?.name || '', topPct: total && top ? Math.round(top.value / total * 100) : 0
  }
})
const mistakeStats = computed(() => {
  const m = data.value.mistake_map || {}
  return { total: m.total || 0, kinds: (m.list || []).length, rate: m.conquered_rate ?? 0 }
})
const growthStats = computed(() => {
  const p = data.value.growth_trajectory?.points || []
  if (!p.length) return { first: 0, last: 0, delta: 0, days: 0 }
  return {
    first: p[0].score || 0, last: p[p.length - 1].score || 0,
    delta: (p[p.length - 1].score || 0) - (p[0].score || 0), days: p.length
  }
})
const interestStats = computed(() => {
  const l = data.value.interest_field?.list || []
  const top = [...l].sort((a, b) => (b.count || 0) - (a.count || 0))[0]
  return { count: l.length, top: top?.name || '', topCount: top?.count || 0 }
})

const hudDim = computed(() => hoveredPlanet.value || dimensions[0])

const aiActions = computed(() => (data.value.ai_actions || []).filter(a => a && a.title))

// 侧栏维度清单：九个维度各带真实关键数值 + 有无数据，点进去与点星球同一条路径
const dimensionList = computed(() => {
  const d = data.value
  const kb = kbStats.value, ab = abilityStats.value, cg = cogStats.value
  const ms = mistakeStats.value, gr = growthStats.value, it = interestStats.value
  const lr = d.learning_rhythm || {}
  const summary = d.ai_summary || ''
  return [
    { key: 'knowledge', label: '知识星系', color: 'var(--brand)', has: hasKnowledge.value, stat: `${kb.count} 个知识点 · 均 ${kb.avg}` },
    { key: 'ability', label: '能力雷达', color: '#8b5cf6', has: hasAbility.value, stat: ab.dims ? `${ab.dims} 个维度 · 共 ${ab.samples} 题` : '' },
    { key: 'rhythm', label: '学习节奏', color: '#10b981', has: hasRhythm.value, stat: lr.total_active_days ? `活跃 ${lr.total_active_days} 天 · 最长连 ${lr.max_streak}` : '' },
    { key: 'cognitive', label: '认知偏好', color: '#f59e0b', has: hasCognitive.value, stat: cg.kinds ? `${cg.kinds} 种题型 · 偏好${cg.top}` : '' },
    { key: 'mistake', label: '易错地图', color: '#ef4444', has: hasMistakes.value, stat: ms.total ? `${ms.total} 道错题 · 攻克 ${ms.rate}%` : '' },
    { key: 'growth', label: '成长轨迹', color: '#06b6d4', has: hasGrowth.value, stat: gr.days ? `${gr.days} 天记录 · 最新 ${gr.last}` : '' },
    { key: 'personality', label: '学习人格', color: '#ec4899', has: !!d.personality?.type, stat: d.personality?.type || '' },
    { key: 'interest', label: '兴趣星云', color: '#f97316', has: hasInterest.value, stat: it.count ? `${it.count} 个领域 · 最多${it.top}` : '' },
    { key: 'summary', label: 'AI 洞见', color: '#a78bfa', has: summary.length > 20 || aiActions.value.length > 0,
      stat: aiActions.value.length ? `建议 · ${aiActions.value[0].title}` : (summary ? summary.slice(0, 14) + '…' : '') }
  ]
})

// ===== Three.js 太阳系 =====
const hub3dRef = ref(null)
function createGlowTexture() {
  const c = document.createElement('canvas'); c.width = 64; c.height = 64
  const ctx = c.getContext('2d')
  const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32)
  g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(0.05, 'rgba(255,255,255,0.8)')
  g.addColorStop(0.3, 'rgba(180,200,255,0.3)'); g.addColorStop(0.7, 'rgba(100,130,200,0.03)')
  g.addColorStop(1, 'rgba(0,0,0,0)')
  ctx.fillStyle = g; ctx.fillRect(0, 0, 64, 64)
  return new THREE.CanvasTexture(c)
}

let scene, camera, renderer, controls, flyAnimId
let planets = []
let planetMeshes = [], animationId
let planetTextures = []        // 程序化生成的贴图，销毁时要一起 dispose
let texRunToken = 0            // 地表贴图逐颗生成的任务令牌，销毁场景时自增作废在途任务
let blackHole = null           // 中央黑洞（点它退出宇宙，被吸进去）
let holeCore = null            // 事件视界球体，出场的放大与点击射线都打在它身上
let stardust = null            // 出场时被吸进去的星尘粒子
const raycaster = new THREE.Raycaster()
const mouse = new THREE.Vector2()

function initSolarSystem() {
  const el = hub3dRef.value; if (!el) return
  const W = el.clientWidth, H = el.clientHeight

  scene = new THREE.Scene()
  // 电影级深空背景 — 极暗，微偏蓝
  scene.background = new THREE.Color(0x020210)
  scene.fog = new THREE.FogExp2(0x020210, 0.00008)

  camera = new THREE.PerspectiveCamera(55, W / H, 1, 4000)   // far 原为 60，大于 60 的东西全被裁掉，远处出发时是空白而非远景
  camera.position.set(0, 12, 18)
  camera.lookAt(0, 0, 0)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
  renderer.setSize(W, H); renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.shadowMap.enabled = true
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.2
  el.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true; controls.dampingFactor = 0.08
  controls.minDistance = 6; controls.maxDistance = 35
  controls.target.set(0, 0, 0)
  camera.position.set(0, 96, 190)   // 初始在极远处，由进场动画推进
  controls.autoRotate = true; controls.autoRotateSpeed = 0.3

  // 远层微星 — 铺满整个虚空：范围 ±1600 是为了让机位能落在星空内部（从外面看会看到
  // 体积的轮廓，从里面看只有满天星、没有边界）。sizeAttenuation 关掉，否则远处的星
  // 会按距离缩到亚像素、等于消失。
  const bgStarsGeo = new THREE.BufferGeometry()
  const bgp = new Float32Array(18000 * 3)
  for (let i = 0; i < 18000 * 3; i++) bgp[i] = (Math.random() - 0.5) * 3200
  bgStarsGeo.setAttribute('position', new THREE.BufferAttribute(bgp, 3))
  scene.add(new THREE.Points(bgStarsGeo, new THREE.PointsMaterial({ color: 0xccddff, size: 1.3, sizeAttenuation: false, transparent: true, opacity: 0.65 })))

  // 填充层 — 同上，铺满虚空、恒定屏幕尺寸
  const fillGeo = new THREE.BufferGeometry()
  const fp2 = new Float32Array(10000 * 3)
  for (let i = 0; i < 10000 * 3; i++) fp2[i] = (Math.random() - 0.5) * 2400
  fillGeo.setAttribute('position', new THREE.BufferAttribute(fp2, 3))
  scene.add(new THREE.Points(fillGeo, new THREE.PointsMaterial({ color: 0x8899bb, size: 1.0, sizeAttenuation: false, transparent: true, opacity: 0.5 })))

  // 中层银河带 — 2000颗，集中在水平面
  const midStarsGeo = new THREE.BufferGeometry()
  const mp = new Float32Array(2000 * 3)
  for (let i = 0; i < 2000; i++) {
    const a = Math.random() * Math.PI * 2
    const r = 8 + Math.random() * 38
    mp[i*3] = Math.cos(a) * r + (Math.random()-0.5)*8
    mp[i*3+1] = (Math.random()-0.5) * 3.5
    mp[i*3+2] = Math.sin(a) * r + (Math.random()-0.5)*8
  }
  midStarsGeo.setAttribute('position', new THREE.BufferAttribute(mp, 3))
  scene.add(new THREE.Points(midStarsGeo, new THREE.PointsMaterial({ color: 0xeeeeff, size: 0.05, transparent: true, opacity: 0.45, blending: THREE.AdditiveBlending, depthWrite: false })))

  // 近层亮星 — 300颗，白/蓝白
  const nearStarsGeo = new THREE.BufferGeometry()
  const nsp = new Float32Array(300 * 3); const ncol = new Float32Array(300 * 3)
  for (let i = 0; i < 300; i++) {
    nsp[i*3] = (Math.random()-0.5) * 55; nsp[i*3+1] = (Math.random()-0.5) * 30; nsp[i*3+2] = (Math.random()-0.5) * 55
    const temp = 0.7 + Math.random() * 0.3
    ncol[i*3] = temp; ncol[i*3+1] = temp * (0.85 + Math.random() * 0.1); ncol[i*3+2] = 0.9 + Math.random() * 0.1
  }
  nearStarsGeo.setAttribute('position', new THREE.BufferAttribute(nsp, 3))
  nearStarsGeo.setAttribute('color', new THREE.BufferAttribute(ncol, 3))
  scene.add(new THREE.Points(nearStarsGeo, new THREE.PointsMaterial({ size: 0.13, vertexColors: true, transparent: true, opacity: 0.55, blending: THREE.AdditiveBlending, depthWrite: false, map: createGlowTexture() })))

  // 暗尘带 — 极淡的深灰粒子，在银河面附近
  for (let l = 0; l < 2; l++) {
    const dustGeo = new THREE.BufferGeometry()
    const dp = []; const r = 16 + l * 8
    for (let i = 0; i < 3000; i++) {
      const a = Math.random() * Math.PI * 2; const rr = r - 2 + Math.random() * 4
      dp.push(Math.cos(a) * rr, (Math.random()-0.5) * 1.2, Math.sin(a) * rr)
    }
    dustGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(dp), 3))
    scene.add(new THREE.Points(dustGeo, new THREE.PointsMaterial({ color: 0x1a1a2e, size: 0.06, transparent: true, opacity: 0.25 - l * 0.08, depthWrite: false })))
  }

  // 远处微星云 — just 2 subtle blobs
  for (let n = 0; n < 2; n++) {
    const nebGeo = new THREE.BufferGeometry()
    const np2 = []
    const cx = (n === 0 ? -12 : 10); const cz = (n === 0 ? -8 : 12)
    for (let i = 0; i < 150; i++) {
      np2.push(cx + (Math.random()-0.5)*10, (Math.random()-0.5)*3, cz + (Math.random()-0.5)*10)
    }
    nebGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(np2), 3))
    scene.add(new THREE.Points(nebGeo, new THREE.PointsMaterial({ color: 0x1a1a3a, size: 0.2, transparent: true, opacity: 0.06, blending: THREE.AdditiveBlending, depthWrite: false })))
  }

  // 中央黑洞 —— 点它退出宇宙（被吸进去）。
  // 原本这里是颗白热恒星 + 三层日冕；改成黑洞后配色仍跟随用户「外观色」：
  // 视界按物理就该是黑的，主题色落在吸积盘与光子环上，09-12 那条「联动外观色」依然成立。
  blackHole = createBlackHole(themeStore.brandColor)
  scene.add(blackHole.group)
  holeCore = blackHole.horizon      // 事件视界：点击退出的射线目标
  // 星尘平时是隐形的（activeFrac=0，全部 alpha 为 0），只在出场动画里放出来
  stardust = createStardust(themeStore.brandColor)
  scene.add(stardust.points)

  // 轨道环：每条轨道一个带倾角的坐标系（行星也挂进去，才会真沿倾斜轨道走）
  const orbitGroups = dimensions.map(d => {
    const g = new THREE.Group()
    g.rotation.y = THREE.MathUtils.degToRad(d.node || 0)
    g.rotation.x = THREE.MathUtils.degToRad(d.incl || 0)
    scene.add(g)
    const orbitPts = []
    for (let i = 0; i <= 128; i++) { const a = (i / 128) * Math.PI * 2; orbitPts.push(Math.cos(a) * d.orbit, 0, Math.sin(a) * d.orbit) }
    const orbitGeo = new THREE.BufferGeometry()
    orbitGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(orbitPts), 3))
    g.add(new THREE.Line(orbitGeo, new THREE.LineBasicMaterial({ color: new THREE.Color(d.color), transparent: true, opacity: 0.09, depthWrite: false })))
    return g
  })

  // ===== 星图坐标系：同心刻度环 + 12 条辐射线 =====
  // 只有几个球在飘会显得空；加上极坐标网格后是一张「星图」，也方便读出行星的方位。
  // 注：曾用 3D 文字精灵标角度/半径刻度，但它会随机让整屏糊成灰色（材质写了深度缓冲
  // + 首帧纹理未就绪），已移除；具体数值由右上角坐标面板承担。
  const outerR = 10.4
  const gridGroup = new THREE.Group()
  scene.add(gridGroup)
  const gridMat = (o) => new THREE.LineBasicMaterial({ color: 0x5b7bd0, transparent: true, opacity: o, depthWrite: false })
  for (let r = 1.2; r <= outerR + 0.01; r += 1.2) {
    const pts = []
    for (let i = 0; i <= 128; i++) { const a = i / 128 * Math.PI * 2; pts.push(Math.cos(a) * r, 0, Math.sin(a) * r) }
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pts), 3))
    // 每 3 圈加粗一档，形成主/次刻度
    gridGroup.add(new THREE.Line(g, gridMat(Math.abs(r % 3.6) < 0.01 ? 0.16 : 0.06)))
  }
  for (let k = 0; k < 12; k++) {
    const a = k / 12 * Math.PI * 2
    const g = new THREE.BufferGeometry()
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array([
      Math.cos(a) * 1.0, 0, Math.sin(a) * 1.0, Math.cos(a) * outerR, 0, Math.sin(a) * outerR,
    ]), 3))
    gridGroup.add(new THREE.Line(g, gridMat(0.07)))
  }

  // 创建行星
  planetMeshes = []
  planetTextures = []
  warpBase = null                // 上一轮场景的基准不透明度不能带到这一轮
  const placeholder = getPlaceholderTexture()
  planets = dimensions.map((d, i) => {
    const spec = PLANET_SPECS[d.key] || PLANET_SPECS.knowledge
    const R = d.size * 0.5
    const group = new THREE.Group()
    // 球体：先挂主题色 + 占位贴图，真地表随后逐颗算好换上（见下方 texJobs）。
    // emissive 仍保留（09-12 加它是因为中心点光源照不到外圈、星球看着像「没数据」），
    // 但有地表贴图后要压低，否则不受光的自发光会把明暗和地形细节一起冲平。
    const pMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(d.color),
      emissive: new THREE.Color(d.color),
      emissiveIntensity: 0.55,
      roughness: 1.0,          // 交给 roughnessMap 调制：海面反光、陆地哑光
      metalness: 0.06,
      map: placeholder, bumpMap: placeholder, bumpScale: 0.03,
      roughnessMap: placeholder, emissiveMap: placeholder
    })
    const mesh = new THREE.Mesh(new THREE.SphereGeometry(R, 64, 48), pMat)
    mesh.userData = { dimKey: d.key, dimIndex: i }
    group.add(mesh)
    // 云层：单独一层球，转得比地表快一点就有视差。opacity 从 0 起，贴图算好再显形
    let cloud = null
    if (spec.cloud > 0.05) {
      cloud = new THREE.Mesh(
        new THREE.SphereGeometry(R * 1.015, 48, 32),
        new THREE.MeshStandardMaterial({
          map: placeholder, transparent: true, depthWrite: false,
          roughness: 1, metalness: 0, opacity: 0
        })
      )
      group.add(cloud)
    }
    // 光环：径向分带贴图
    let ring = null
    if (spec.ring) {
      const rg = new THREE.RingGeometry(R * 1.35, R * spec.ring, 128, 1)
      rg.rotateX(-Math.PI / 2)
      ring = new THREE.Mesh(rg, new THREE.MeshBasicMaterial({
        map: placeholder, transparent: true, side: THREE.DoubleSide,
        depthWrite: false, opacity: 0
      }))
      ring.rotation.z = THREE.MathUtils.degToRad(10)   // 环面略微不共面，免得看着像贴纸
      group.add(ring)
    }
    // Sprite 标签（随距离缩放）
    const canvas = document.createElement('canvas')
    canvas.width = 256; canvas.height = 64
    const ctx = canvas.getContext('2d')
    ctx.font = 'bold 28px -apple-system, sans-serif'
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    ctx.fillStyle = 'rgba(255,255,255,0.7)'; ctx.fillText(d.label, 128, 32)
    const tex = new THREE.CanvasTexture(canvas); tex.minFilter = THREE.LinearFilter
    // 侧栏已列出全部维度，星标签退居次要：压暗压小，避免和外圈行星挤在一起互相压
    const spriteMat = new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.42, depthTest: false })
    const sprite = new THREE.Sprite(spriteMat)
    sprite.scale.set(d.size * 1.3, d.size * 0.32, 1)
    sprite.position.y = d.size * 0.9
    group.add(sprite)

    orbitGroups[i].add(group)   // 挂到倾斜轨道组：局部坐标 (cos,0,sin) 即可沿倾角轨道走
    planetMeshes.push(mesh)
    return { group, mesh, cloud, ring, data: d, angle: Math.random() * Math.PI * 2 }
  })

  // 地表是在运行时算出来的（九颗合计约 0.5s）。同步算会白屏卡住首帧，
  // 所以先让星球以主题色出场，之后一次算一颗、算好一颗换一颗——
  // 进场动画本来就有 3.4s，换完的时候用户还在从虚空往里飞。
  const texJobs = planets.map((p, i) => () => {
    const d = dimensions[i]
    const spec = PLANET_SPECS[d.key] || PLANET_SPECS.knowledge
    const maps = makePlanetSurface(d.color, spec)
    const mat = p.mesh.material
    mat.map = maps.color
    mat.bumpMap = maps.data
    mat.roughnessMap = maps.data
    mat.bumpScale = 0.03
    if (maps.emissive) {
      // 熔岩星：让裂缝自己发光，而不是整颗均匀发亮
      mat.emissiveMap = maps.emissive
      mat.emissive.setHex(0xffffff)
      mat.emissiveIntensity = 1.5
      planetTextures.push(maps.emissive)
    } else {
      // 拿颜色图当自发光图：远处星球仍保留 09-12 要的那份「一眼看出是什么维度」的亮度，
      // 但自发光跟着地表明暗走。若用纯色自发光（占位图就是纯白），会把刚做出来的纹理冲平。
      mat.emissiveMap = maps.color
      mat.emissive.setHex(0xffffff)
      mat.emissiveIntensity = 0.26
    }
    planetTextures.push(maps.color, maps.data)
    if (p.cloud) {
      const ct = makeCloudTexture(d.color, spec)
      p.cloud.material.map = ct
      p.cloud.material.opacity = 1
      planetTextures.push(ct)
    }
    if (p.ring) {
      const rt = makeRingTexture(d.color, spec.seed)
      p.ring.material.map = rt
      p.ring.material.opacity = 1
      planetTextures.push(rt)
    }
  })
  let texJobI = 0
  const myToken = ++texRunToken
  const runTexJob = () => {
    // 令牌对不上说明已经切走/重建过场景：再跑下去会把纹理挂到已 dispose 的材质上，
    // 而且推不进已被清空的 planetTextures，那些显存就再也回收不掉了。
    if (myToken !== texRunToken || texJobI >= texJobs.length) return
    texJobs[texJobI++]()
    setTimeout(runTexJob, 0)
  }
  setTimeout(runTexJob, 80)     // 先让第一帧画出来再开始算

  // 灯光 — 中央换成黑洞后这盏灯保留：黑洞本身不发光，但吸积盘极亮，
  // 行星仍该被中心照亮，否则 09-12 修好的「外圈星球沉进黑里」会当场回归。
  // （环境光抬亮 + 衰减放缓）
  scene.add(new THREE.AmbientLight(0x3a4670, 1.0))
  const sunLight = new THREE.PointLight(0xfff8ee, 3.5, 60, 0.9)
  sunLight.position.set(0, 0, 0)
  scene.add(sunLight)
  const fillLight = new THREE.PointLight(0x6b7fb0, 1.6, 70, 0.7)
  fillLight.position.set(0, 18, 0)
  scene.add(fillLight)

  // 进场：从极远处推进，先什么都看不见，星系逐渐浮现
  let entryStart = performance.now()
  const ENTRY_DUR = 3400                 // 缓缓靠近
  controls.maxDistance = 6000            // 进场期间放开距离上限（默认 35 会把相机拽回来）
  const CAM_END = { y: 12, z: 18 }

  // 动画循环
  let hudTick = 0
  let lastFrameT = performance.now()
  const _wv = new THREE.Vector3()
  function anim() {
    animationId = requestAnimationFrame(anim)
    const now = performance.now()
    // 上限 50ms：从后台标签页切回来时 delta 会是个很大的值，粒子会一帧瞬移过去
    const dt = Math.min(0.05, (now - lastFrameT) / 1000)
    lastFrameT = now
    // 出场：先吸九颗行星，再吸星尘（粒子越聚越多），最后整屏化作用户的外观色。
    // 黑洞本身不放大——放大它会盖掉吸入的过程。
    if (warping) {
      const t = Math.min(1, (performance.now() - warpStart) / WARP_DUR)
      // 网格与轨道要淡出，基准不透明度只抓一次：逐帧 *= 是帧率相关的，掉帧时淡出会明显变慢
      if (!warpBase) {
        warpBase = {
          grid: gridGroup ? gridGroup.children.map(l => l.material.opacity) : [],
          orbit: orbitGroups.map(g => (g.children[0] && g.children[0].material) ? g.children[0].material.opacity : 0),
        }
      }
      planets.forEach((p, i) => {
        // 内圈先落、外圈依次跟上：错开启动才有「被一个个吸进去」的层次
        const s = clamp((t - i * 0.03) / 0.52, 0, 1)
        // 1.3 次方：起步就看得见在动，越接近中心越快。用 s² 的话前三分之一几乎没位移，
        // 观感上就是「干等了半秒才开始吸」
        const fall = Math.pow(s, 1.3)
        const r = dimensions[i].orbit * (1 - fall)
        // 角速度随半径缩小而暴涨——这一项才是「旋转吸入」与「被直线拽进去」的区别。
        // 少了它，行星只是沿半径笔直滑向中心，看着像掉下去而不是被卷进去。
        const spin = p.angle + (1 / Math.pow(Math.max(0.05, 1 - fall), 1.2) - 1) * 0.85
        p.group.position.set(Math.cos(spin) * r, 0, Math.sin(spin) * r)
        // 尺寸跟着半径走，而不是跟着时间走：行星半径和视界差不多大，
        // 不在贴近时收掉的话，画面上是行星盖住黑洞，而不是黑洞把行星吃掉。
        p.group.scale.setScalar(Math.max(0.001, smooth(HORIZON_R, HORIZON_R * 3.0, r)))
      })
      // 行星落得差不多时粒子接上：从远处不断旋转着涌来一股。
      // 只放出一部分（约 45%），够看出「东西被吸进去」就切走——不做填满屏幕那一套。
      const dust = clamp((t - 0.40) / 0.60, 0, 1)
      if (stardust) stardust.update(dt, Math.pow(dust, 0.8) * 0.45)
      if (gridGroup) gridGroup.children.forEach((l, i) => { l.material.opacity = warpBase.grid[i] * (1 - t) })
      orbitGroups.forEach((grp, i) => {
        const line = grp.children[0]
        if (line && line.material) line.material.opacity = warpBase.orbit[i] * (1 - t)
      })
    } else {
      planets.forEach((p, i) => {
        p.angle += dimensions[i].speed * 0.02
        const a = p.angle; const r = dimensions[i].orbit
        p.group.position.set(Math.cos(a) * r, 0, Math.sin(a) * r)
        p.mesh.rotation.y += 0.01
        if (p.cloud) p.cloud.rotation.y += 0.016   // 云比地表快 → 拉开视差
      })
      if (blackHole) blackHole.disk.rotation.y += 0.0022   // 吸积盘缓慢自转
    }
    // 右上角坐标读数：悬停时读那颗，否则读第一颗——让面板始终有活数据在跳
    if (++hudTick % 6 === 0) {
      const kd = hoveredPlanet.value || dimensions[0]
      const grp = planets.find(x => x.data.key === kd.key)?.group
      if (grp) {
        grp.getWorldPosition(_wv)
        const deg = ((Math.atan2(_wv.z, _wv.x) * 180 / Math.PI) + 360) % 360
        hoverCoord.value = {
          key: kd.key,
          r: kd.orbit.toFixed(1), deg: deg.toFixed(0),
          incl: (kd.incl > 0 ? '+' : '') + kd.incl,
          y: _wv.y.toFixed(1)
        }
      }
    }
    // 进场推进（进出场同时发生时以出场为准，避免打架）
    if (entryStart) {
      const t = Math.min(1, (performance.now() - entryStart) / ENTRY_DUR)
      // 对数插值：按「距离等比缩小」推进。线性插值时视张角按 1/d 变化，
      // 前 80% 时间几乎没动静、最后 15% 猛扑进来，观感就成了硬切而不是靠近。
      const e = -(Math.cos(Math.PI * t) - 1) / 2
      const D0 = 1100, D1 = Math.hypot(CAM_END.y, CAM_END.z)
      const D = D0 * Math.pow(D1 / D0, e)
      const dirY = CAM_END.y / D1, dirZ = CAM_END.z / D1
      const ty = dirY * D
      const tz = dirZ * D
      if (warping) entryStart = 0
      else {
        camera.position.y = ty
        camera.position.z = tz
        // 从虚空浮现：亮度随推进一起升起来，而不是一上来就全亮
        renderer.toneMappingExposure = 0.06 + 1.14 * Math.min(1, t * 1.55)
        if (t >= 1) {
          entryStart = 0
          renderer.toneMappingExposure = 1.2
          controls.maxDistance = 35        // 抵达后交还给 OrbitControls 的正常范围
        }
      }
    }
    controls.update()
    renderer.render(scene, camera)
  }
  // 先填一次读数：rAF 在后台标签页/无头环境可能不触发，面板不至于空着
  {
    const kd = dimensions[0]
    const grp = planets.find(x => x.data.key === kd.key)?.group
    if (grp) {
      grp.getWorldPosition(_wv)
      const deg = ((Math.atan2(_wv.z, _wv.x) * 180 / Math.PI) + 360) % 360
      hoverCoord.value = { key: kd.key, r: kd.orbit.toFixed(1), deg: deg.toFixed(0),
        incl: (kd.incl > 0 ? '+' : '') + kd.incl, y: _wv.y.toFixed(1) }
    }
  }
  anim()
  // 兜底：rAF 不触发（后台标签页/降帧）时，进场动画永远走不完，
  // 必须到点直接把相机拍到位，否则用户会一直盯着「什么都没有」的远景。
  setTimeout(() => {
    if (!entryStart) return
    entryStart = 0
    camera.position.set(0, CAM_END.y, CAM_END.z)
    renderer.toneMappingExposure = 1.2
    controls.maxDistance = 35
  }, ENTRY_DUR + 200)

  // 点击检测
  el.addEventListener('click', onHubClick)
  el.addEventListener('mousemove', onHubMove)
  // 响应式
  stardust.setViewport(renderer.domElement.height, camera.fov)
  new ResizeObserver(() => {
    const w = el.clientWidth, h = el.clientHeight
    if (w > 0 && h > 0) {
      camera.aspect = w / h; camera.updateProjectionMatrix(); renderer.setSize(w, h)
      // 点尺寸按物理像素算，改窗口后不重算的话粒子会跟着一起放大缩小
      stardust.setViewport(renderer.domElement.height, camera.fov)
    }
  }).observe(el)
}

function onHubMove(e) {
  mouse.x = (e.clientX / window.innerWidth) * 2 - 1
  mouse.y = -(e.clientY / window.innerHeight) * 2 + 1
  raycaster.setFromCamera(mouse, camera)
  // 悬停黑洞：手型提示可点击退出
  if (holeCore && raycaster.intersectObject(holeCore, false).length) {
    hoveredPlanet.value = null
    document.body.style.cursor = 'pointer'
    return
  }
  const hits = raycaster.intersectObjects(planetMeshes)
  if (hits.length) {
    const d = dimensions[hits[0].object.userData.dimIndex]
    hoveredPlanet.value = d
    // 实时极坐标读数（行星在动，所以每次悬停现算）
    const grp = planets.find(x => x.data.key === d.key)?.group
    if (grp) {
      const w = new THREE.Vector3(); grp.getWorldPosition(w)
      const deg = ((Math.atan2(w.z, w.x) * 180 / Math.PI) + 360) % 360
      hoverCoord.value = {
        r: d.orbit.toFixed(1), deg: deg.toFixed(0),
        incl: (d.incl > 0 ? '+' : '') + d.incl,
        y: w.y.toFixed(1)
      }
    }
    document.body.style.cursor = 'pointer'
  } else {
    hoveredPlanet.value = null
    document.body.style.cursor = ''
  }
}

// 点击黑洞 = 退出宇宙：整个黑洞涨大把画面吞掉，比逐帧推相机顺得多
function enterHome() {
  if (warping) return
  warping = true
  warpStart = performance.now()
  // 全程在 3D 里演完再跳：行星吸进去占前段，粒子涌来占后段，到点直接切主页。
  // 没有 DOM 遮罩兜底，所以时序要跟 WARP_DUR 对齐。
  setTimeout(() => router.push('/home'), WARP_DUR + 60)
  // 自愈兜底：万一跳转没发生（或被拦），撤销收拢状态，别把用户卡在原地
  setTimeout(() => { warping = false }, WARP_DUR + 1200)
}

function onHubClick() {
  // 先看是不是点到了黑洞
  raycaster.setFromCamera(mouse, camera)
  if (holeCore && raycaster.intersectObject(holeCore, false).length) { enterHome(); return }
  if (!hoveredPlanet.value) return
  enterDimension(hoveredPlanet.value.key)
}

/** 打开维度详情面板（幂等：飞行结束与兜底定时器都会调） */
let enterDimTimer = null
function openDim(key) {
  if (activeDim.value === key) return
  activeDim.value = key
  setTimeout(() => renderDetail(key), 120)
}

/** 进入某维度：相机飞过去 → 打开详情面板（点星球与点侧栏清单共用这一条路径） */
function enterDimension(key) {
  const d = dimensions.find(x => x.key === key)
  if (!d) return
  // 飞行动画：相机靠近行星
  const planet = planets.find(p => p.data.key === d.key)
  if (!planet) { openDim(d.key); return }
  const target = new THREE.Vector3()
  planet.group.getWorldPosition(target)
  const start = { x: camera.position.x, y: camera.position.y, z: camera.position.z, tx: controls.target.x, ty: controls.target.y, tz: controls.target.z }
  const end = { x: target.x + 3, y: target.y + 1.5, z: target.z + 3, tx: target.x, ty: target.y, tz: target.z }
  const dur = 600; const st = performance.now()
  function fly(now) {
    const p = Math.min(1, (now - st) / dur)
    const e = 1 - Math.pow(1 - p, 3)
    camera.position.set(start.x + (end.x - start.x) * e, start.y + (end.y - start.y) * e, start.z + (end.z - start.z) * e)
    controls.target.set(start.tx + (end.tx - start.tx) * e, start.ty + (end.ty - start.ty) * e, start.tz + (end.tz - start.tz) * e)
    if (p < 1) flyAnimId = requestAnimationFrame(fly)
    else openDim(d.key)
  }
  flyAnimId = requestAnimationFrame(fly)
  // 兜底：收尾动作原本只挂在 rAF 飞行循环里，rAF 不触发（后台标签页/降帧/无头）时
  // 相机会停在半路、面板永远不开。加一个定时器保证面板一定打开。
  clearTimeout(enterDimTimer)
  enterDimTimer = setTimeout(() => openDim(d.key), dur + 300)
}

function closeDetail() {
  activeDim.value = null
  controls.target.set(0, 0, 0)
  camera.position.set(0, 12, 18)
  camera.lookAt(0, 0, 0)
}

function destroySolar() {
  if (animationId) cancelAnimationFrame(animationId)
  if (flyAnimId) cancelAnimationFrame(flyAnimId)
  texRunToken++                  // 作废还在排队的地表贴图生成任务
  // 程序化地表是运行时现算的大纹理（九颗合计约 5MB），不 dispose 的话
  // 在路由之间来回切换会一直往显存里堆。占位贴图不在这个列表里，它要跨次复用。
  planetTextures.forEach(t => t.dispose())
  planetTextures = []
  if (blackHole) { blackHole.textures.forEach(t => t.dispose()); blackHole = null }
  holeCore = null
  stardust = null                // 几何与材质由上面的 scene.traverse 一并 dispose
  if (scene) {
    scene.traverse(o => {
      if (o.geometry) o.geometry.dispose()
      if (o.material) (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => m.dispose())
    })
  }
  if (renderer) { renderer.dispose(); renderer = null }
  if (hub3dRef.value) hub3dRef.value.innerHTML = ''
}

// ===== 数据 =====
async function loadData() {
  loading.value = true
  try {
    const res = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/evaluation/profile-data?user_id=${authStore.user.id}`,
      { headers: { Authorization: `Bearer ${authStore.token}` } })
    data.value = await res.json()
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

// ===== 详情图表 =====
const charts = {}
function getChart(k, ref, opts) {
  if (charts[k]) { charts[k].dispose(); charts[k] = null }
  if (!ref.value) return
  charts[k] = echarts.init(ref.value)
  charts[k].setOption({ backgroundColor: 'transparent', ...opts })
}

function renderDetail(key) {
  const d = data.value
  // 仅当数据存在时才渲染图表
  if (key === 'knowledge' && !hasKnowledge.value) return
  if (key === 'ability' && !hasAbility.value) return
  if (key === 'rhythm' && !hasRhythm.value) return
  if (key === 'cognitive' && !hasCognitive.value) return
  if (key === 'mistake' && !hasMistakes.value) return
  if (key === 'growth' && !hasGrowth.value) return
  if (key === 'interest' && !hasInterest.value) return
  switch (key) {
    case 'knowledge': {
      const list = d.knowledge_base?.list || []
      if (!list.length) return
      // 旧版是 force 布局 + Math.random() 生成的假连线（连线无语义、纯噪声），
      // 节点按掌握度放大到 50px 后在环形里叠成一团、标签互相压。
      // 改成极坐标星爆：每个知识点一根射线，长度=掌握度、颜色=档位，标签绕圈排布不重叠。
      const top = [...list].sort((a, b) => b.score - a.score).slice(0, 18)
      getChart('knowledge', knowledgeRef, {
        tooltip: { ...TIP, formatter: p => `${p.name}<br/><b style="color:${scoreColor(p.value)}">掌握度 ${p.value}</b>` },
        polar: { radius: ['16%', '68%'], center: ['50%', '50%'] },
        angleAxis: {
          type: 'category', data: top.map(x => x.name), startAngle: 90,
          axisLabel: {
            color: 'rgba(255,255,255,0.62)', fontSize: 10, interval: 0,
            formatter: v => v.length > 5 ? v.slice(0, 5) + '…' : v
          },
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
          axisTick: { show: false }
        },
        radiusAxis: {
          max: 100, axisLabel: { show: false }, axisLine: { show: false }, z: 10,
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)', type: [3, 4] } }
        },
        series: [{
          type: 'bar', coordinateSystem: 'polar', barWidth: '62%', roundCap: true,
          data: top.map(x => ({
            name: x.name, value: x.score,
            itemStyle: { color: scoreColor(x.score), shadowBlur: 14, shadowColor: scoreColor(x.score) + '66', borderRadius: [3, 3, 0, 0] }
          })),
          emphasis: { itemStyle: { shadowBlur: 24 } }
        }]
      })
      break
    }
    case 'ability': {
      const rd = d.ability_radar || {}; const ks = Object.keys(rd)
      if (!ks.length) return
      // 少于 3 个轴时雷达图退化成一条线，看不出东西 → 改用条形列表（练的题型多了会自动长回 radar）
      if (ks.length < 3) {
        getChart('radar', radarRef, {
          tooltip: { ...TIP, formatter: p => `${p.name}<br/><b>${p.value} 分</b>` },
          grid: { left: '26%', right: '16%', top: 24, bottom: 24 },
          xAxis: { type: 'value', max: 100, axisLabel: { ...AXIS_LABEL }, splitLine: { ...SPLIT_LINE } },
          yAxis: { type: 'category', data: ks, axisLabel: { ...AXIS_LABEL, fontSize: 12, fontWeight: 600 }, axisLine: { show: false }, axisTick: { show: false } },
          series: [{
            type: 'bar', data: ks.map(k => rd[k]?.score || 0), barWidth: 18,
            itemStyle: {
              borderRadius: [9, 9, 9, 9],
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#8b5cf655' }, { offset: 1, color: '#8b5cf6' }])
            },
            label: { show: true, position: 'right', color: 'rgba(255,255,255,0.75)', fontSize: 12, fontWeight: 600, formatter: p => `${p.value} 分` }
          }]
        })
        break
      }
      getChart('radar', radarRef, {
        tooltip: { ...TIP },
        radar: {
          indicator: ks.map(k => ({ name: k, max: 100 })),
          center: ['50%', '54%'], radius: '64%',
          axisName: { color: 'rgba(255,255,255,0.7)', fontSize: 12, fontWeight: 600 },
          splitArea: { areaStyle: { color: ['rgba(139,92,246,0.035)', 'rgba(139,92,246,0.075)'] } },
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.10)' } },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } }
        },
        series: [{
          type: 'radar', symbolSize: 5,
          data: [{
            value: ks.map(k => rd[k]?.score || 0), name: '能力',
            areaStyle: { color: new echarts.graphic.RadialGradient(0.5, 0.5, 0.8, [{ offset: 0, color: 'rgba(139,92,246,0.05)' }, { offset: 1, color: 'rgba(139,92,246,0.34)' }]) },
            lineStyle: { color: '#a78bfa', width: 2.5, shadowBlur: 12, shadowColor: 'rgba(139,92,246,0.6)' },
            itemStyle: { color: '#c4b5fd', borderColor: '#8b5cf6', borderWidth: 1.5 }
          }]
        }]
      })
      break
    }
    case 'rhythm': {
      const cal = d.learning_rhythm?.calendar || []
      if (!cal.length) return
      const maxAct = Math.max(...cal.map(c => c.count), 1)
      getChart('calendar', calendarRef, {
        tooltip: { ...TIP, formatter: p => `${p.value[0]}<br/><b>${p.value[1]} 次</b>学习活动` },
        visualMap: {
          min: 0, max: maxAct, orient: 'horizontal', left: 'center', bottom: 4, itemWidth: 12, itemHeight: 90,
          inRange: { color: ['rgba(255,255,255,0.05)', '#0d9488', '#10b981', '#6ee7b7'] },
          textStyle: { color: 'rgba(255,255,255,0.45)', fontSize: 11 }, text: ['多', '少']
        },
        calendar: {
          range: cal.length > 30 ? [cal[0].date, cal[cal.length - 1].date] : undefined,
          cellSize: ['auto', 15],
          itemStyle: { borderColor: 'rgba(10,12,20,0.9)', borderWidth: 2, borderRadius: 3 },
          dayLabel: { color: 'rgba(255,255,255,0.4)', fontSize: 11, nameMap: 'ZH' },
          monthLabel: { color: 'rgba(255,255,255,0.55)', fontSize: 11, nameMap: 'ZH' },
          yearLabel: { show: false },
          splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
        },
        series: [{
          type: 'heatmap', coordinateSystem: 'calendar',
          data: cal.map(c => [c.date, c.count]),
          emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(16,185,129,0.8)' } }
        }]
      })
      break
    }
    case 'cognitive': {
      const ts = [...(d.cognitive_preference?.types || [])].sort((a, b) => a.value - b.value)
      if (!ts.length) return
      const tot = ts.reduce((s, x) => s + (x.value || 0), 0) || 1
      getChart('cogBar', cognitiveBarRef, {
        tooltip: { ...TIP, formatter: p => `${p.name}<br/><b>${p.value} 道</b> · 占比 ${Math.round(p.value / tot * 100)}%` },
        grid: { left: '22%', right: '18%', top: 16, bottom: 16 },
        xAxis: { type: 'value', axisLabel: { ...AXIS_LABEL }, splitLine: { ...SPLIT_LINE } },
        yAxis: {
          type: 'category', data: ts.map(t => t.name),
          axisLabel: { ...AXIS_LABEL, fontSize: 12, fontWeight: 600 },
          axisLine: { show: false }, axisTick: { show: false }
        },
        series: [{
          type: 'bar', data: ts.map(t => t.value), barWidth: 16,
          itemStyle: {
            borderRadius: [8, 8, 8, 8],
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#f59e0b44' }, { offset: 1, color: '#fbbf24' }])
          },
          label: {
            show: true, position: 'right', color: 'rgba(255,255,255,0.7)', fontSize: 11, fontWeight: 600,
            formatter: p => `${p.value} · ${Math.round(p.value / tot * 100)}%`
          }
        }]
      })
      break
    }
    case 'mistake': {
      const ml = (d.mistake_map?.list || []).slice(0, 16)
      if (!ml.length) return
      // 色相表「攻克情况」，明度表「错题多少」：只按攻克率上色时，攻克率低的账号会糊成
      // 一堵一模一样的红墙，看不出哪个知识点更严重。取前 16 个也让方块够大、标签不被切。
      const mx = Math.max(...ml.map(m => m.total), 1)
      const data_ = ml.map(m => {
        const rate = m.total ? (m.conquered || 0) / m.total : 0
        const alpha = (0.34 + 0.5 * (m.total / mx)).toFixed(2)
        const rgb = rate >= 0.6 ? '16,185,129' : rate >= 0.2 ? '251,191,36' : '239,68,68'
        return {
          name: m.name, value: m.total,
          itemStyle: { color: `rgba(${rgb},${alpha})`, borderRadius: 8, borderColor: 'rgba(10,12,20,0.9)', borderWidth: 2 }
        }
      })
      getChart('treemap', treemapRef, {
        tooltip: { ...TIP, formatter: p => `${p.name}<br/>错题 <b>${p.value}</b> 道` },
        series: [{
          type: 'treemap', data: data_, roam: false, nodeClick: false, breadcrumb: { show: false },
          label: {
            show: true, color: '#fff', fontSize: 12, fontWeight: 600, lineHeight: 15, overflow: 'truncate',
            formatter: p => `${p.name.length > 6 ? p.name.slice(0, 6) + '…' : p.name}\n${p.value} 道`
          },
          upperLabel: { show: false },
          itemStyle: { gapWidth: 2 },
          levels: [{ itemStyle: { borderWidth: 0, gapWidth: 2 } }],
          emphasis: { itemStyle: { shadowBlur: 14, shadowColor: 'rgba(0,0,0,0.5)' } }
        }]
      })
      break
    }
    case 'growth': {
      const pts = d.growth_trajectory?.points || []
      if (!pts.length) return
      const scores = pts.map(p => p.score)
      const avg = Math.round(scores.reduce((s, x) => s + x, 0) / scores.length)
      getChart('growth', growthRef, {
        tooltip: { ...TIP, trigger: 'axis', formatter: p => `${p[0].axisValue}<br/><b>${p[0].data} 分</b>` },
        grid: { left: 46, right: 24, top: 26, bottom: 34 },
        xAxis: {
          type: 'category', data: pts.map(p => p.date.slice(5)), boundaryGap: false,
          axisLabel: { ...AXIS_LABEL, fontSize: 10, rotate: 0, hideOverlap: true },
          axisLine: { lineStyle: { color: 'rgba(255,255,255,0.12)' } }, axisTick: { show: false }
        },
        yAxis: {
          type: 'value', min: 0, max: 100, interval: 25,
          axisLabel: { ...AXIS_LABEL, formatter: '{value}' },
          splitLine: { ...SPLIT_LINE }
        },
        series: [{
          type: 'line', data: scores, smooth: 0.35, symbol: 'circle', symbolSize: 7,
          lineStyle: { color: '#22d3ee', width: 2.5, shadowBlur: 14, shadowColor: 'rgba(34,211,238,0.5)' },
          itemStyle: { color: '#0e7490', borderColor: '#67e8f9', borderWidth: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(34,211,238,0.38)' },
              { offset: 1, color: 'rgba(34,211,238,0.02)' }
            ])
          },
          markLine: {
            silent: true, symbol: 'none',
            lineStyle: { color: 'rgba(255,255,255,0.22)', type: 'dashed', width: 1 },
            label: { color: 'rgba(255,255,255,0.45)', fontSize: 10, formatter: `均值 ${avg}` },
            data: [{ yAxis: avg }]
          },
          emphasis: { scale: 1.6, itemStyle: { shadowBlur: 16, shadowColor: 'rgba(34,211,238,0.9)' } }
        }]
      })
      break
    }
    case 'interest': initInterest3D(); break
    case 'summary': typeSummary(); break
  }
}

// 兴趣 3D 球体
let intrScene, intrCam, intrRenderer, intrLabel, intrCtrl, intrAnim
function initInterest3D() {
  destroyIntr3D()
  const el = interest3dRef.value; if (!el) return
  const W = el.clientWidth || 400, H = el.clientHeight || 340
  intrScene = new THREE.Scene(); intrScene.background = new THREE.Color(0x020210)
  intrCam = new THREE.PerspectiveCamera(45, W/H, 1, 600); intrCam.position.z = 260
  intrRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true }); intrRenderer.setSize(W, H); intrRenderer.setPixelRatio(1.5)
  el.appendChild(intrRenderer.domElement)
  intrLabel = new CSS3DRenderer(); intrLabel.setSize(W, H); intrLabel.domElement.style.cssText = 'position:absolute;top:0;left:0;pointer-events:none'
  el.appendChild(intrLabel.domElement)
  intrCtrl = new OrbitControls(intrCam, intrRenderer.domElement); intrCtrl.enableDamping = true; intrCtrl.autoRotate = true; intrCtrl.autoRotateSpeed = 1

  const bgGeo = new THREE.BufferGeometry(); const bp = new Float32Array(800 * 3)
  for (let i = 0; i < 800; i++) {
    const _r = 60 + Math.random() * 140, _t = Math.random() * Math.PI * 2, _p = Math.acos(2 * Math.random() - 1)
    bp[i*3] = _r * Math.sin(_p) * Math.cos(_t); bp[i*3+1] = _r * Math.sin(_p) * Math.sin(_t); bp[i*3+2] = _r * Math.cos(_p)
  }
  bgGeo.setAttribute('position', new THREE.BufferAttribute(bp, 3))
  intrScene.add(new THREE.Points(bgGeo, new THREE.PointsMaterial({ color: 0x445588, size: 0.8, transparent: true, opacity: 0.5 })))

  const list = data.value.interest_field?.list || []
  if (!list.length) return
  const maxC = Math.max(...list.map(t => t.count), 1); const R = 100
  const clrs = [themeStore.brandColor,'#8b5cf6','#f59e0b','#22c55e','#ec4899','#06b6d4','#f97316','#a78bfa','#60a5fa','#f472b6','#2dd4bf','#818cf8']
  list.forEach((item, i) => {
    const phi = Math.acos(1 - 2 * (i + 0.5) / list.length)
    const theta = Math.PI * (1 + Math.sqrt(5)) * i
    const x = R * Math.sin(phi) * Math.cos(theta), y = R * Math.cos(phi), z = R * Math.sin(phi) * Math.sin(theta)
    const div = document.createElement('div')
    div.textContent = item.name
    const sz = 13 + (item.count / maxC) * 12
    div.style.cssText = `color:#fff;font-size:${sz}px;font-weight:600;padding:3px 14px;border-radius:16px;border:1px solid ${clrs[i%clrs.length]}44;background:rgba(0,0,0,0.4);white-space:nowrap;text-shadow:0 0 6px ${clrs[i%clrs.length]}44`
    const lbl = new CSS3DObject(div); lbl.position.set(x, y, z); lbl.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1), new THREE.Vector3(x,y,z).normalize())
    intrScene.add(lbl)
  })
  intrScene.add(new THREE.Mesh(new THREE.SphereGeometry(R*0.96, 20, 14), new THREE.MeshBasicMaterial({ color: 0x334466, wireframe: true, transparent: true, opacity: 0.02 })))
  function anim() { intrAnim = requestAnimationFrame(anim); intrCtrl.update(); intrRenderer.render(intrScene, intrCam); intrLabel.render(intrScene, intrCam) }
  anim()
}
function destroyIntr3D() {
  if (intrAnim) { cancelAnimationFrame(intrAnim); intrAnim = null }
  if (intrRenderer && typeof intrRenderer.dispose === 'function') { intrRenderer.dispose(); intrRenderer = null }
  if (intrLabel && typeof intrLabel.dispose === 'function') { intrLabel.dispose(); intrLabel = null }
  if (interest3dRef.value) interest3dRef.value.innerHTML = ''
}

function typeSummary() {
  typing.value = true; displaySummary.value = ''
  const text = data.value.ai_summary || '完成更多题目后，AI 将为你生成深度画像总结。'
  let i = 0; const t = setInterval(() => { displaySummary.value += text[i]; i++; if (i >= text.length) { clearInterval(t); typing.value = false } }, 40)
}

function scoreColor(s) { if (s >= 80) return '#22c55e'; if (s >= 60) return '#eab308'; if (s >= 40) return '#f97316'; return '#ef4444' }
// 退出维度宇宙回主界面（此前跳到评估中心，不是用户要的去处）
function goBack() { router.push('/home') }

const knowledgeRef=ref(null),radarRef=ref(null),calendarRef=ref(null),cognitiveBarRef=ref(null),treemapRef=ref(null),growthRef=ref(null),interest3dRef=ref(null)

onMounted(async () => {
  setTimeout(initSolarSystem, 200)
  await loadData()
  // 深链：/profile-card?dim=knowledge 直接进某个维度（可分享、可刷新保持）
  const want = route.query.dim
  if (want && dimensions.some(x => x.key === want)) {
    setTimeout(() => enterDimension(String(want)), 500)
  }
})
onBeforeUnmount(() => { destroySolar(); destroyIntr3D(); Object.values(charts).forEach(c => c?.dispose()) })
</script>

<style scoped>
.du-root { width: 100vw; height: 100vh; overflow: hidden; position: relative; background: #060610; }
.hub-3d { width: 100%; height: 100%; position: absolute; inset: 0; }

.du-topbar { position: absolute; top: 0; left: 0; right: 0; z-index: 10; display: flex; justify-content: space-between; align-items: center; padding: 14px 22px; pointer-events: none; }
.du-topbar > * { pointer-events: auto; }
.du-topbar h1 { font-size: 18px; font-weight: 600; color: rgba(255,255,255,0.7); margin: 0; letter-spacing: 2px; }
.du-bottombar { position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 10; display: flex; gap: 24px; font-size: 10px; color: rgba(255,255,255,0.2); letter-spacing: 0.5px; }
.du-bottombar span { display: flex; align-items: center; gap: 5px; }

/* ===== 右上角坐标读数面板 ===== */
.du-hud {
  position: absolute; top: 68px; right: 22px; z-index: 13;
  min-width: 208px; padding: 14px 16px 12px; border-radius: 14px;
  background: linear-gradient(165deg, rgba(20,24,42,0.82), rgba(10,12,24,0.88));
  backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 1px 0 rgba(255,255,255,0.05) inset, 0 14px 38px rgba(0,0,0,0.42);
}
.hud-head { display: flex; align-items: center; gap: 8px; padding-bottom: 10px; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.07); }
.hud-dot { width: 9px; height: 9px; border-radius: 50%; background: rgba(255,255,255,0.2); transition: background .2s; }
.hud-title { font-size: 13px; font-weight: 700; color: rgba(255,255,255,0.82); letter-spacing: .5px; }
.hud-row { display: flex; align-items: baseline; justify-content: space-between; padding: 4px 0; }
.hud-row span { font-size: 11.5px; color: rgba(255,255,255,0.45); }
.hud-row b {
  font-size: 16px; font-weight: 700; color: #9db4ff;
  font-family: ui-monospace, SFMono-Regular, monospace; letter-spacing: .5px;
  text-shadow: 0 0 12px rgba(120,150,255,0.45);
}
.hud-idle { font-size: 11.5px; color: rgba(255,255,255,0.32); padding: 6px 0 2px; }

/* 出场没有任何 DOM 遮罩：从头到尾都在 3D 里完成。
   早先那版在末尾盖了一层平铺的外观色渐变，但它和粒子是脱节的——
   看着像"闪了一下色卡"，而不是粒子本身把画面填满。 */
@media (max-width: 900px) { .du-hud { display: none; } }

/* ===== 维度清单侧栏：让九个维度的数据状态一眼可见 ===== */
.du-panel {
  position: absolute; top: 50%; left: 20px; transform: translateY(-50%);
  z-index: 12; width: 248px; max-height: 78vh; overflow-y: auto;
  padding: 14px 12px 12px; border-radius: 16px;
  background: linear-gradient(165deg, rgba(20,24,42,0.82), rgba(10,12,24,0.88));
  backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 1px 0 rgba(255,255,255,0.05) inset, 0 16px 44px rgba(0,0,0,0.45);
}
.du-panel::-webkit-scrollbar { width: 3px; }
.du-panel::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 2px; }
.du-panel-head {
  display: flex; align-items: baseline; justify-content: space-between;
  padding: 0 6px 10px; margin-bottom: 6px;
  border-bottom: 1px solid rgba(255,255,255,0.07);
}
.du-panel-head span { font-size: 12px; font-weight: 700; color: rgba(255,255,255,0.72); letter-spacing: 1px; }
.du-panel-head em { font-style: normal; font-size: 11px; color: rgba(255,255,255,0.38); }
.du-item {
  display: grid; grid-template-columns: 8px 1fr; grid-template-rows: auto auto;
  column-gap: 9px; row-gap: 1px; width: 100%; text-align: left;
  padding: 8px 9px; margin-bottom: 2px; border: none; border-radius: 10px;
  background: transparent; cursor: pointer; transition: background .18s;
}
.du-item:hover { background: rgba(255,255,255,0.06); }
.du-item.is-empty { opacity: .42; }
.du-dot { grid-row: 1 / 3; align-self: center; width: 8px; height: 8px; border-radius: 50%; }
.du-name { font-size: 12.5px; font-weight: 600; color: rgba(255,255,255,0.86); }
.du-stat {
  grid-column: 2; font-size: 10.5px; color: rgba(255,255,255,0.42);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
@media (max-width: 900px) {
  .du-panel { display: none; }
}

.g-btn { display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; font-size: 11px; font-weight: 500; color: rgba(255,255,255,0.4); background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent); border: 1px solid rgba(255,255,255,0.04); border-radius: 6px; cursor: pointer; transition: all 0.3s; font-family: inherit; }
.g-btn:hover { background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); color: rgba(255,255,255,0.7); border-color: rgba(255,255,255,0.1); }

/* 行星提示 */
.tt-coord {
  margin-top: 5px; padding-top: 5px; font-size: 10.5px; letter-spacing: .3px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  color: rgba(150,178,255,0.72); border-top: 1px solid rgba(255,255,255,0.08);
}
.planet-tooltip { position: fixed; z-index: 15; pointer-events: none; text-align: center; }
.tt-name { font-size: 12px; font-weight: 600; color: rgba(255,255,255,0.8); letter-spacing: 0.5px; }
.tt-sub { font-size: 9px; color: rgba(255,255,255,0.35); margin-top: 3px; }

/* 详情面板 — 3D 立体 */
/* 居中交给 flex 遮罩层，面板本身不带定位/transform：
   1) 旧的 translate(-50%,-50%) 会被进场动画的 .detail-enter-from 整个覆盖 → 面板跑到右下角被切；
   2) 改用 position:fixed 也不行——路由过渡期间页面容器带 transform，会给 fixed 造新的包含块，
      且 inset:0 + height:fit-content 会塌成 0 高，overflow-y:auto 把内容全剪掉（DOM 有、屏幕没有）。*/
.detail-overlay {
  /* 用 absolute 相对全屏的 .du-root（它自己 position:relative）：
     fixed 会被路由过渡期间页面容器上的 transform 接管包含块，导致尺寸/位置判断失准。 */
  position: absolute; inset: 0; z-index: 20;
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.detail-panel {
  pointer-events: auto;
  width: 100%; max-width: 700px; max-height: 80vh; overflow-y: auto;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(20,20,50,0.9) 0%, rgba(8,8,25,0.94) 100%);
  backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow:
    0 2px 0 rgba(255,255,255,0.03) inset,
    0 8px 40px rgba(0,0,0,0.5),
    0 24px 80px rgba(0,0,0,0.4),
    0 0 0 1px rgba(255,255,255,0.03);
  transition: box-shadow 0.4s cubic-bezier(0.4,0,0.2,1);
}
.detail-panel:hover {
  box-shadow:
    0 2px 0 rgba(255,255,255,0.04) inset,
    0 12px 48px rgba(0,0,0,0.6),
    0 32px 96px rgba(0,0,0,0.5),
    0 0 0 1px rgba(255,255,255,0.05);
}
.detail-panel::-webkit-scrollbar { width: 3px; }
.detail-panel::-webkit-scrollbar-thumb { background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); border-radius: 2px; }

.dp-header {
  display: flex; align-items: center; gap: 16px; padding: 18px 24px;
  position: sticky; top: 0; z-index: 2;
  background: linear-gradient(180deg, rgba(15,15,40,0.85) 0%, rgba(10,10,30,0.4) 100%);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border-radius: 20px 20px 0 0;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  box-shadow: 0 1px 0 rgba(255,255,255,0.02) inset;
}
.dp-header h2 { font-size: 18px; margin: 0; text-shadow: 0 0 12px currentColor; }
.dp-body { padding: 18px 22px 26px; }

/* ===== 维度详情卡：所有维度共用的容器，图表不再裸浮在面板上 ===== */
.dim-card {
  border-radius: 16px;
  padding: 18px 20px 16px;
  background: linear-gradient(160deg, rgba(255,255,255,0.055) 0%, rgba(255,255,255,0.018) 55%, rgba(255,255,255,0.03) 100%);
  border: 1px solid rgba(255,255,255,0.075);
  box-shadow:
    0 1px 0 rgba(255,255,255,0.06) inset,
    0 10px 30px rgba(0,0,0,0.28);
}
/* KPI 摘要行 */
.dim-stats {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  gap: 10px;
  margin-bottom: 16px;
}
.stat {
  position: relative;
  padding: 12px 14px;
  border-radius: 12px;
  background: linear-gradient(150deg, rgba(255,255,255,0.06), rgba(255,255,255,0.015));
  border: 1px solid rgba(255,255,255,0.07);
  overflow: hidden;
}
.stat::before {
  content: ''; position: absolute; left: 0; top: 12%; bottom: 12%; width: 3px;
  border-radius: 3px; background: var(--brand); opacity: .55;
}
.stat b {
  display: block; font-size: 24px; font-weight: 800; line-height: 1.15;
  font-family: 'SF Mono', ui-monospace, monospace;
  color: #fff; letter-spacing: -0.5px;
}
.stat span {
  display: block; margin-top: 3px; font-size: 11px;
  color: rgba(255,255,255,0.5); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.stat-good::before { background: #10b981; } .stat-good b { color: #6ee7b7; }
.stat-weak::before { background: #f59e0b; } .stat-weak b { color: #fbbf24; }

.dim-hint {
  margin: 12px 2px 0; font-size: 11.5px; line-height: 1.6;
  color: rgba(255,255,255,0.38);
}

.chart-box { width: 100%; height: 340px; overflow: hidden; }
.int-3d {
  width: 100%; height: 320px; position: relative; overflow: hidden; border-radius: 12px;
  background: radial-gradient(ellipse at center, color-mix(in srgb, var(--brand) 4%, transparent), transparent 70%);
  box-shadow: 0 0 0 1px rgba(255,255,255,0.03) inset;
}

.personality-card { position: relative; text-align: center; padding: 48px 32px; border-radius: 20px; background: linear-gradient(135deg, rgba(236,72,153,0.04), rgba(139,92,246,0.04)); border: 1px solid rgba(236,72,153,0.08); overflow: hidden; }
.pc-glow { position: absolute; inset: 0; background: radial-gradient(ellipse at center, rgba(236,72,153,0.04), transparent 60%); animation: gp 3s infinite; }
@keyframes gp { 0%,100% { transform: scale(1); opacity: 0.5; } 50% { transform: scale(1.1); opacity: 1; } }
.pc-type { position: relative; font-size: 38px; font-weight: 800; background: linear-gradient(135deg, #ec4899, #8b5cf6, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-size: 200% 200%; animation: st 3s infinite; margin-bottom: 16px; }
@keyframes st { 0%,100% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } }
.pc-tags { position: relative; display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-bottom: 20px; }
.pc-tag { padding: 6px 20px; border-radius: 20px; font-size: 14px; font-weight: 600; background: rgba(236,72,153,0.08); color: #ec4899; border: 1px solid rgba(236,72,153,0.12); }
.pc-desc { position: relative; font-size: 15px; line-height: 1.8; color: rgba(255,255,255,0.6); max-width: 560px; margin: 0 auto; }

.summary-box {
  position: relative; padding: 40px 34px 30px; border-radius: 16px; text-align: center;
  background: linear-gradient(160deg, rgba(167,139,250,0.07), rgba(255,255,255,0.015) 60%);
  border: 1px solid rgba(167,139,250,0.16);
  box-shadow: 0 1px 0 rgba(255,255,255,0.06) inset, 0 10px 30px rgba(0,0,0,0.28);
}
.sb-quote {
  position: absolute; top: 6px; left: 22px; font-size: 68px; line-height: 1;
  font-family: Georgia, serif; color: rgba(167,139,250,0.22); pointer-events: none;
}
.sb-text { font-size: 19px; line-height: 2; color: rgba(255,255,255,0.86); display: inline; }
.sb-cursor { font-size: 19px; color: #a78bfa; animation: blink 0.8s step-end infinite; }
.sb-foot { margin-top: 18px; font-size: 11px; color: rgba(255,255,255,0.3); letter-spacing: .3px; }
.sb-actions {
  margin-top: 26px; padding-top: 18px; text-align: left;
  border-top: 1px solid rgba(167,139,250,0.16);
}
.sb-actions-title {
  font-size: 11px; font-weight: 700; letter-spacing: 1px;
  color: rgba(167,139,250,0.8); margin-bottom: 12px;
}
.sb-action {
  display: flex; gap: 12px; align-items: flex-start;
  padding: 11px 14px; margin-bottom: 8px; border-radius: 12px;
  background: linear-gradient(150deg, rgba(167,139,250,0.09), rgba(255,255,255,0.015));
  border: 1px solid rgba(167,139,250,0.14);
}
.sb-action-idx {
  flex: none; width: 20px; height: 20px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 800; color: #0b0d18;
  background: #a78bfa; box-shadow: 0 0 10px rgba(167,139,250,0.5);
}
.sb-action-body { display: flex; flex-direction: column; gap: 3px; }
.sb-action-body b { font-size: 13.5px; font-weight: 700; color: rgba(255,255,255,0.9); }
.sb-action-body em { font-style: normal; font-size: 11.5px; color: rgba(255,255,255,0.45); }
@keyframes blink { 50% { opacity: 0; } }

@keyframes spin { to { transform: rotate(360deg); } }

.empty-dim {
  text-align: center; padding: 56px 30px; border-radius: 14px;
  color: rgba(255,255,255,0.42); font-size: 13px; line-height: 1.9;
  background: linear-gradient(160deg, rgba(255,255,255,0.035), rgba(255,255,255,0.01));
  border: 1px dashed rgba(255,255,255,0.10);
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.detail-enter-active { transition: all 0.5s cubic-bezier(0.4,0,0.2,1); }
.detail-leave-active { transition: all 0.3s ease; }
.detail-enter-from { opacity: 0; transform: scale(1.05); }
.detail-leave-to { opacity: 0; }
</style>
