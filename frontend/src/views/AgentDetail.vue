<template>
  <div class="ad-page" v-if="detail && meta" :style="{ '--viz-s1': meta.color }">
    <!-- ===== 头部 Hero ===== -->
    <div class="ad-hero" :style="{ '--agent-grad': meta.grad }">
      <button class="back-btn" @click="goBack">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
        返回中心
      </button>
      <div class="hero-main">
        <div class="hero-badge" :style="{ background: meta.grad }"><img :src="meta.img" alt="" class="hero-badge-img"></div>
        <div class="hero-id">
          <div class="hero-name-row">
            <h1 class="hero-name">{{ meta.name }}</h1>
            <span class="fit-chip" :style="{ color: meta.color }">{{ meta.tagline }}</span>
          </div>
          <p class="hero-role">{{ meta.role }}</p>
          <p class="hero-desc">{{ source?.desc }}</p>
        </div>
      </div>
    </div>

    <!-- ===== 统计行 ===== -->
    <div class="stat-row">
      <div class="stat-tile" v-for="s in detail.stats" :key="s.label">
        <span class="stat-label">{{ s.label }}</span>
        <span class="stat-value">{{ s.value == null ? '—' : `${s.value}${s.unit ? ' ' + s.unit : ''}` }}</span>
      </div>
    </div>

    <!-- ===== 可行动建议（数据驱动 · 一键应用） ===== -->
    <section class="ad-card" v-if="meta && meta.suggestion">
      <div class="suggest-banner">
        <span class="suggest-text">💡 {{ suggestionText }}</span>
        <button class="suggest-btn" :class="{ applied }" @click="applySuggestion">
          {{ applied ? '已应用 ✓' : meta.action }}
        </button>
      </div>
    </section>

    <!-- ===== 主指标趋势 ===== -->
    <section class="ad-card">
      <div class="card-head">
        <h2 class="card-title">近 30 天「{{ detail.trend_label }}」趋势</h2>
        <div class="view-toggle">
          <button :class="{ active: trendView === 'chart' }" @click="trendView = 'chart'">图表</button>
          <button :class="{ active: trendView === 'table' }" @click="trendView = 'table'">表格</button>
        </div>
      </div>

      <!-- ECharts 折线图：平滑曲线 + 渐变面积 + 十字准线 + 磨合事件标注 -->
      <div v-show="trendView === 'chart'" ref="trendEl" class="trend-echart"></div>

      <!-- 表格视图 -->
      <div v-if="trendView === 'table'" class="trend-table-wrap">
        <table class="ac-table">
          <thead><tr><th>日期</th><th>{{ detail.trend_label }}（{{ detail.trend_unit }}）</th></tr></thead>
          <tbody>
            <tr v-for="(v, i) in [...detail.trend].reverse()" :key="i">
              <td>{{ trendDates[detail.trend.length - 1 - i] }}</td>
              <td class="num">{{ v }}{{ detail.trend_unit }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- ===== 特点面板（每个智能体专属 ×2，数据源标注） ===== -->
    <section class="ad-card" v-for="f in features" :key="f.title">
      <h2 class="card-title">特点 · {{ f.title }}</h2>
      <p class="card-desc">
        {{ f.desc }}
        <span class="source-tag">数据源：{{ f.source }}</span>
      </p>
      <div v-if="f.type === 'bars'" class="feat-bars">
        <div class="feat-row" v-for="it in f.items" :key="it.label">
          <span class="feat-label">{{ it.label }}</span>
          <div class="feat-track">
            <div class="feat-fill" :style="{ width: featPct(it, f.items) }"></div>
          </div>
          <span class="feat-value">{{ it.value }}{{ it.unit || '' }}</span>
        </div>
      </div>
      <div v-else class="feat-compare">
        <div
          class="feat-stat" v-for="(it, i) in f.items" :key="it.label"
          :style="{ borderColor: i === 0 ? 'var(--viz-s1)' : 'var(--viz-grid)' }"
        >
          <span class="feat-stat-label">{{ it.label }}</span>
          <span class="feat-stat-value" :style="{ color: i === 0 ? 'var(--viz-s1)' : 'var(--viz-muted)' }">
            {{ it.value }}<small> {{ it.unit }}</small>
          </span>
        </div>
      </div>
    </section>

    <!-- ===== 触点明细 ===== -->
    <section class="ad-card">
      <h2 class="card-title">触点明细</h2>
      <p class="card-desc">该智能体在你产品里每个出现位置的使用情况</p>
      <table class="ac-table">
        <thead>
          <tr><th>触点</th><th>场景</th><th>调用</th></tr>
        </thead>
        <tbody>
          <tr v-for="t in detail.touchpoints" :key="t.name">
            <td>{{ t.name }}</td>
            <td>{{ t.scene }}</td>
            <td class="num">{{ (t.count || 0).toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ===== 参数调节（核心） ===== -->
    <section class="ad-card">
      <div class="card-head">
        <h2 class="card-title">参数调节</h2>
        <div class="param-actions">
          <button class="ghost-btn" @click="resetParams">重置为出厂</button>
          <button class="save-btn" @click="saveParams">保存</button>
        </div>
      </div>
      <p class="card-desc">同一参数对所有触点生效。开启「自动托管」后，参数会随你的使用情况自动微调。</p>

      <div class="param-list">
        <div class="param-item" v-for="p in params" :key="p.key" :class="{ managed: p.auto }">
          <div class="param-top">
            <div class="param-id">
              <span class="param-label">{{ p.label }}</span>
              <span class="param-cur">{{ displayValue(p) }}</span>
              <span v-if="p.auto" class="managed-chip">自动托管</span>
            </div>
            <!-- 自动调整开关 -->
            <button class="auto-switch" :class="{ on: p.auto }" @click="p.auto = !p.auto" role="switch" :aria-checked="p.auto">
              <span class="auto-knob"></span>
              <span class="auto-text">{{ p.auto ? '自动' : '手动' }}</span>
            </button>
          </div>

          <!-- 控件 -->
          <div class="param-ctrl" :class="{ disabled: p.auto }">
            <!-- 分段选择 -->
            <div v-if="p.type === 'seg'" class="seg-group">
              <button
                v-for="opt in p.options" :key="opt"
                class="seg-btn" :class="{ active: p.value === opt }"
                :disabled="p.auto" @click="p.value = opt"
              >{{ opt }}</button>
            </div>
            <!-- 滑块 -->
            <div v-else-if="p.type === 'slider'" class="slider-group">
              <input
                type="range" class="viz-slider" :min="p.min" :max="p.max" :step="p.step || 1"
                v-model.number="p.value" :disabled="p.auto"
              />
              <div class="slider-scale">
                <span>{{ p.min }}{{ p.unit }}</span>
                <span>{{ p.max }}{{ p.unit }}</span>
              </div>
            </div>
            <!-- 开关 -->
            <button
              v-else-if="p.type === 'toggle'"
              class="toggle-switch" :class="{ on: p.value }"
              :disabled="p.auto" @click="p.value = !p.value"
            ><span class="toggle-knob"></span></button>
          </div>

          <!-- 规则说明 -->
          <div class="param-foot">
            <span class="rule-text">⚙️ {{ p.rule }}</span>
            <span v-if="p.lastTune" class="tune-note">上次调整：{{ p.lastTune }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== 磨合记录 ===== -->
    <section class="ad-card">
      <div class="card-head">
        <h2 class="card-title">磨合记录</h2>
        <button class="ghost-btn" :disabled="tuningBusy" @click="runTuning">
          {{ tuningBusy ? '评估中…' : '立即评估' }}
        </button>
      </div>
      <p class="card-desc">开启「自动托管」的参数会随你的使用自动微调——点「立即评估」立刻跑一次磨合规则</p>
      <div class="timeline">
        <div class="timeline-row" v-for="(t, i) in tuning" :key="i">
          <span class="tl-date">{{ fmtTlDate(t.created_at) }}</span>
          <span class="tl-dot"></span>
          <div class="tl-body">
            <span class="tl-text">{{ t.param_key }}：{{ fmtVal(t.old_value) }} → {{ fmtVal(t.new_value) }}</span>
            <span class="tl-effect">{{ t.reason || (t.source === 'auto' ? '自动调整' : '手动调整') }}</span>
          </div>
        </div>
        <p v-if="!tuning.length" class="tl-empty">暂无磨合记录——使用一段时间后，自动调整会在这里留下痕迹。</p>
      </div>
    </section>

    <p class="ad-footnote">以上数据由你的真实学习行为汇总而成 · 参数调整与磨合记录都会自动保存</p>
  </div>
  <p v-else class="ad-loading">数据加载中…</p>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { useAuthStore } from '@/stores/auth'
import { agents as agentsMeta, agentDetails as agentsDef, makeTrendDates } from '@/utils/mockAgents'
import { getAgentDetail, getAgentPrefs, saveAgentPrefs, getAgentTuning, postRunTuning } from '@/api/agentCenter'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const key = route.params.agentKey

// 静态元数据（图标/名称/特点/介绍/建议）+ 静态参数定义与规则
const meta = agentsMeta.find(a => a.key === key)
const source = agentsDef[key]

// 真实数据（/agent-center 聚合接口 + prefs/tuning 读写）
const detail = ref(null)
const prefs = ref([])
const tuning = ref([])
const loading = ref(false)

const trendDates = computed(() => makeTrendDates(detail.value?.trend?.length || 30))

// 参数控件 = 静态定义 + 已保存的 prefs（无记录用出厂默认）
const params = computed(() => {
  const defs = source?.params || []
  return defs.map(p => {
    const saved = prefs.value.find(x => x.param_key === p.key)
    return { ...p, value: saved ? saved.value : p.value, auto: saved ? !!saved.auto_managed : !!p.auto }
  })
})

async function loadTuning() {
  if (!authStore.user?.id) return
  tuning.value = await getAgentTuning(key, authStore.user.id)
}

async function load() {
  if (!authStore.user?.id) return
  loading.value = true
  try {
    detail.value = await getAgentDetail(key, authStore.user.id)
    prefs.value = await getAgentPrefs(key, authStore.user.id)
    await loadTuning()
  } catch (e) {
    console.error('[agent-center] detail:', e)
  } finally {
    loading.value = false
  }
}
onMounted(load)

// ===== 立即评估（磨合规则引擎） =====
const tuningBusy = ref(false)
async function runTuning() {
  if (!authStore.user?.id || tuningBusy.value) return
  tuningBusy.value = true
  try {
    const res = await postRunTuning(authStore.user.id)
    await loadTuning()
    if (res.applied?.length) {
      ElMessage.success(`磨合规则自动调整了 ${res.applied.length} 项参数`)
    } else {
      ElMessage.success('当前无需调整，参数保持现状')
    }
  } catch (e) {
    ElMessage.error('评估失败，请稍后重试')
  } finally {
    tuningBusy.value = false
  }
}

function goBack() { router.push('/agent-center') }

function setPref(paramKey, value, auto) {
  const ex = prefs.value.find(x => x.param_key === paramKey)
  if (ex) { ex.value = value; ex.auto_managed = auto }
  else prefs.value.push({ param_key: paramKey, value, auto_managed: auto })
}

// ===== 建议一键应用（本地演示，与下方参数调节联动） =====
const applied = ref(false)
const suggestionText = ref(meta?.suggestion || '')
function applySuggestion() {
  if (applied.value) return
  applied.value = true
  if (key === 'generate') {
    setPref('difficulty', 6, true)
    suggestionText.value = '难度已调至 6，下个周期观察 7-8 级题收录率是否回到 60%+。'
  } else if (key === 'plan') {
    setPref('tasks', 3, true)
    setPref('pace', '舒缓', true)
    suggestionText.value = '每日任务量已调至 3 个、节奏改「舒缓」，下个周期观察计划完成率。'
  } else if (key === 'xiaoji') {
    setPref('care', '高', false)
    suggestionText.value = '已提高主动关心频率，小基会更常来督促你。'
  } else {
    suggestionText.value = '已确认保持现状，下个周期继续观察。'
  }
  saveAgentPrefs(key, authStore.user.id, prefs.value).catch(() => {})
}

// ===== 趋势图（ECharts：渐变面积 + 十字准线 + 磨合事件 markLine） =====
const trendView = ref('chart')
const trendEl = ref(null)
let trendChart = null
let themeObserver = null

function cssVar(name, fallback) {
  const el = document.querySelector('.ad-page')
  const v = el ? getComputedStyle(el).getPropertyValue(name).trim() : ''
  return v || fallback
}

// 趋势值动态 y 轴范围
const tMin = computed(() => {
  const vals = detail.value?.trend || []
  if (!vals.length) return 0
  return Math.min(0, Math.floor(Math.min(...vals) * 0.9))
})
const tMax = computed(() => {
  const vals = detail.value?.trend || []
  if (!vals.length) return 1
  return Math.max(1, Math.ceil(Math.max(...vals) * 1.15))
})

function buildTrendOption() {
  const d = detail.value
  if (!d) return {}
  const s1 = cssVar('--viz-s1', '#2a78d6')
  const muted = cssVar('--viz-muted', '#898781')
  const grid = cssVar('--viz-grid', '#e1e0d9')
  const surface = cssVar('--viz-surface', '#fcfcfb')
  const warn = cssVar('--viz-warn', '#8a5a00')
  // 磨合事件 → 折线上标注竖虚线（证据链：调整点 vs 指标变化）
  const marks = tuning.value.map(t => {
    const m = (t.created_at || '').match(/^(\d{4})-(\d{2})-(\d{2})/)
    if (!m) return null
    const idx = trendDates.value.indexOf(`${Number(m[2])}/${Number(m[3])}`)
    if (idx < 0) return null
    const label = `${t.param_key} ${JSON.stringify(t.old_value ?? null)}→${JSON.stringify(t.new_value ?? null)}`
    return { xAxis: idx, label: label.length > 14 ? label.slice(0, 14) + '…' : label }
  }).filter(Boolean)
  return {
    animationDuration: 600,
    grid: { left: 46, right: 18, top: 34, bottom: 30 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(20,22,30,.92)',
      borderColor: 'rgba(255,255,255,.12)',
      textStyle: { color: '#e2e8f0', fontSize: 12 },
      formatter: ps => {
        const p = Array.isArray(ps) ? ps[0] : ps
        return `${trendDates.value[p.dataIndex]} · ${d.trend_label}<br/><strong>${p.value}${d.trend_unit || ''}</strong>`
      },
    },
    xAxis: {
      type: 'category', data: trendDates.value, boundaryGap: false,
      axisLine: { lineStyle: { color: grid } }, axisTick: { show: false },
      axisLabel: { color: muted, fontSize: 10, interval: 6 },
    },
    yAxis: {
      type: 'value', min: tMin.value, max: tMax.value,
      splitLine: { lineStyle: { color: grid } },
      axisLabel: { color: muted, fontSize: 10 },
    },
    series: [{
      name: d.trend_label, type: 'line', data: d.trend,
      smooth: 0.35, symbol: 'circle', symbolSize: 6, showSymbol: false,
      lineStyle: { color: s1, width: 2.5 },
      itemStyle: { color: s1, borderColor: surface, borderWidth: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: s1 + '42' }, { offset: 1, color: s1 + '05' },
        ]),
      },
      markLine: marks.length ? {
        symbol: 'none', silent: true,
        data: marks.map(mk => ({
          xAxis: mk.xAxis,
          lineStyle: { color: warn, type: 'dashed', width: 1, opacity: 0.7 },
          label: { show: true, formatter: mk.label, position: 'insideStartTop', color: warn, fontSize: 9 },
        })),
      } : undefined,
    }],
  }
}

function renderTrend() {
  if (trendView.value !== 'chart') return
  nextTick(() => {
    if (!trendEl.value) return
    if (trendChart) { trendChart.dispose(); trendChart = null }
    trendChart = echarts.init(trendEl.value)
    trendChart.setOption({ backgroundColor: 'transparent', ...buildTrendOption() })
  })
}
function onResize() { trendChart?.resize() }

onMounted(() => {
  renderTrend()
  window.addEventListener('resize', onResize)
  // 深浅主题切换时用新配色重建
  themeObserver = new MutationObserver(() => renderTrend())
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  themeObserver?.disconnect()
  if (trendChart) { trendChart.dispose(); trendChart = null }
})
watch(trendView, v => { if (v === 'chart') renderTrend() })
// 数据异步加载完成后首次渲染趋势图（挂载时 detail 还是 null）
watch(detail, d => { if (d) renderTrend() })

// ===== 特点面板（来自 API detail.features），条形宽度按各自最大值归一 =====
const features = computed(() => detail.value?.features || [])
function featPct(it, items) {
  const max = Math.max(...items.map(i => i.value))
  return ((it.value / max) * 100).toFixed(1) + '%'
}

// ===== 参数显示 =====
function displayValue(p) {
  if (p.type === 'toggle') return p.value ? '开' : '关'
  if (p.type === 'slider') return `${p.value} ${p.unit}`
  return p.value
}

function fmtVal(v) {
  if (v == null) return '—'
  if (typeof v === 'string') return v
  return JSON.stringify(v)
}

function fmtTlDate(s) {
  const m = (s || '').match(/^(\d{4})-(\d{2})-(\d{2})/)
  return m ? `${Number(m[2])}月${Number(m[3])}日` : (s || '').slice(0, 10)
}

function resetParams() {
  if (!source) return
  const defaults = source.params.map(p => ({ param_key: p.key, value: p.value, auto_managed: p.auto }))
  prefs.value = defaults
  saveAgentPrefs(key, authStore.user.id, defaults)
    .then(() => ElMessage.success('已重置为出厂参数'))
    .catch(() => ElMessage.error('重置失败，请稍后重试'))
}

function saveParams() {
  const payload = params.value.map(p => ({ param_key: p.key, value: p.value, auto_managed: p.auto }))
  saveAgentPrefs(key, authStore.user.id, payload)
    .then(() => ElMessage.success('参数已保存'))
    .catch(() => ElMessage.error('保存失败，请稍后重试'))
}
</script>

<style scoped>
/* ===== 图表变量（与中心页一致：浅色默认 / 深色覆盖） ===== */
.ad-page {
  --viz-s1: #2a78d6;
  --viz-good: #006300;
  --viz-warn: #8a5a00;
  --viz-crit: #d03b3b;
  --viz-ink: #0b0b0b;
  --viz-ink-2: #52514e;
  --viz-muted: #898781;
  --viz-grid: #e1e0d9;
  --viz-axis: #c3c2b7;
  --viz-surface: #fcfcfb;
  padding: 28px 34px 40px;
  max-width: 960px;
  margin: 0 auto;
}
[data-theme="dark"] .ad-page {
  --viz-s1: #3987e5;
  --viz-good: #0ca30c;
  --viz-warn: #fab219;
  --viz-crit: #e66767;
  --viz-ink: #ffffff;
  --viz-ink-2: #c3c2b7;
  --viz-muted: #898781;
  --viz-grid: #2c2c2a;
  --viz-axis: #383835;
  --viz-surface: #1a1a19;
}

/* ===== 建议横幅 ===== */
.suggest-banner {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  background: rgba(251,146,60,.07); border: 1px solid rgba(251,146,60,.18);
  border-radius: 10px; padding: 12px 16px;
}
[data-theme="light"] .suggest-banner { background: rgba(200,110,20,.05); border-color: rgba(200,110,20,.16); }
.suggest-text { font-size: 13px; color: var(--text-secondary); flex: 1; line-height: 1.5; }
.suggest-btn {
  padding: 6px 14px; border-radius: 8px; font-size: 12px; cursor: pointer; flex-shrink: 0;
  border: 1px solid rgba(251,146,60,.4); background: rgba(251,146,60,.14);
  color: color-mix(in srgb, #fbbf24 70%, var(--text-primary)); transition: all .2s ease; font-family: inherit; white-space: nowrap;
}
.suggest-btn:hover { background: rgba(251,146,60,.24); transform: translateY(-1px); }
.suggest-btn.applied { border-color: var(--viz-good); background: rgba(12,163,12,.12); color: var(--viz-good); cursor: default; }

/* ===== Hero ===== */
.ad-hero { margin-bottom: 18px; }
.back-btn {
  display: inline-flex; align-items: center; gap: 6px;
  background: transparent; border: none; color: var(--text-secondary);
  font-size: 13px; cursor: pointer; padding: 4px 8px; border-radius: 8px;
  transition: all .2s ease; font-family: inherit; margin-bottom: 14px;
}
.back-btn svg { width: 16px; height: 16px; }
.back-btn:hover { color: var(--text-primary); background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); transform: translateX(-2px); }
.hero-main { display: flex; align-items: flex-start; gap: 16px; }
.hero-badge {
  width: 62px; height: 62px; border-radius: 16px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(255,255,255,.12);
  overflow: hidden; position: relative;
}
.hero-badge-img { width: 72%; height: 72%; object-fit: contain; position: relative; }
/* 浅色主题下徽章渐变过浅，加暗色遮罩让白色图形可读 */
[data-theme="light"] .hero-badge::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(160deg, rgba(15,23,42,.32), rgba(15,23,42,.10));
}
.hero-name-row { display: flex; align-items: center; gap: 10px; }
.hero-name { font-size: 24px; font-weight: 700; color: var(--text-primary); margin: 0; }
.fit-chip { font-size: 12px; font-weight: 600; }
.hero-role { font-size: 13px; color: var(--text-secondary); margin: 4px 0 0; }
.hero-desc { font-size: 12px; color: var(--text-muted); margin: 8px 0 0; line-height: 1.6; max-width: 640px; }

/* ===== 统计行 ===== */
.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 18px; }
.stat-tile {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid rgba(255,255,255,.06);
  border-radius: 14px; padding: 14px 18px; backdrop-filter: blur(20px);
}
[data-theme="dark"] .stat-tile { background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent); }
.stat-label { font-size: 12px; color: var(--text-secondary); display: block; }
.stat-value { font-size: 22px; font-weight: 700; color: var(--viz-ink); margin-top: 4px; display: block; }
.stat-value.warn { color: var(--viz-warn); }

/* ===== 卡片通用 ===== */
.ad-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid rgba(255,255,255,.06);
  border-radius: 16px; padding: 20px 22px; backdrop-filter: blur(20px); margin-bottom: 18px;
}
[data-theme="dark"] .ad-card { background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent); }
.card-head { display: flex; align-items: center; justify-content: space-between; }
.card-title { font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 0; }
.card-desc { font-size: 12px; color: var(--text-muted); margin: 6px 0 16px; }

.view-toggle { display: flex; gap: 4px; }
.view-toggle button {
  padding: 4px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; font-family: inherit;
  border: 1px solid var(--border-color); background: transparent; color: var(--text-secondary);
  transition: all .2s ease;
}
.view-toggle button.active { background: color-mix(in srgb, var(--brand) 14%, transparent); border-color: color-mix(in srgb, var(--brand) 35%, transparent); color: var(--brand-bright); }

/* ===== 趋势图 ===== */
.trend-echart { width: 100%; height: 260px; }
.trend-table-wrap { max-height: 320px; overflow-y: auto; }

/* ===== 表格 ===== */
.ac-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.ac-table th {
  text-align: left; padding: 8px 10px; color: var(--text-muted); font-weight: 600;
  border-bottom: 1px solid var(--viz-grid); font-size: 12px; white-space: nowrap;
}
.ac-table td { padding: 9px 10px; color: var(--text-secondary); border-bottom: 1px solid var(--viz-grid); }
.ac-table .num { font-variant-numeric: tabular-nums; color: var(--viz-ink); }
.effect-cell { font-size: 12px; color: var(--viz-ink-2); }

/* ===== 参数调节 ===== */
.param-actions { display: flex; gap: 8px; }
.ghost-btn {
  padding: 6px 14px; border-radius: 8px; font-size: 12px; cursor: pointer; font-family: inherit;
  border: 1px solid var(--border-color); background: transparent; color: var(--text-secondary);
  transition: all .2s ease;
}
.ghost-btn:hover { background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); color: var(--text-primary); }
.save-btn {
  padding: 6px 18px; border-radius: 8px; font-size: 12px; cursor: pointer; font-family: inherit;
  border: 1px solid color-mix(in srgb, var(--brand) 40%, transparent); background: color-mix(in srgb, var(--brand) 15%, transparent); color: var(--brand-bright);
  transition: all .2s ease; font-weight: 600;
}
.save-btn:hover { background: color-mix(in srgb, var(--brand) 25%, transparent); transform: translateY(-1px); }

.param-list { display: flex; flex-direction: column; gap: 12px; }
.param-item {
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); border: 1px solid rgba(255,255,255,.06);
  border-radius: 12px; padding: 14px 16px;
  transition: border-color .2s ease, opacity .2s ease;
}
[data-theme="dark"] .param-item { background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent); }
.param-item.managed { border-color: rgba(12,163,12,.18); }
.param-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.param-id { display: flex; align-items: center; gap: 10px; }
.param-label { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.param-cur {
  font-size: 12px; color: var(--viz-s1); background: color-mix(in srgb, var(--brand) 10%, transparent);
  padding: 2px 10px; border-radius: 10px; font-weight: 600;
}
.managed-chip {
  font-size: 11px; color: var(--viz-good); background: rgba(12,163,12,.10);
  padding: 2px 8px; border-radius: 10px;
}

/* 自动调整开关 */
.auto-switch {
  display: inline-flex; align-items: center; gap: 7px;
  background: transparent; border: none; cursor: pointer; font-family: inherit; padding: 2px;
}
.auto-knob {
  width: 34px; height: 18px; border-radius: 9px; position: relative;
  background: rgba(128,128,128,.25); transition: background .2s ease;
}
.auto-knob::after {
  content: ''; position: absolute; top: 2px; left: 2px;
  width: 14px; height: 14px; border-radius: 50%; background: #fff;
  transition: transform .2s ease; box-shadow: 0 1px 3px rgba(0,0,0,.3);
}
.auto-switch.on .auto-knob { background: rgba(12,163,12,.55); }
.auto-switch.on .auto-knob::after { transform: translateX(16px); }
.auto-text { font-size: 11px; color: var(--text-muted); width: 26px; text-align: left; }

/* 分段选择 */
.seg-group { display: inline-flex; gap: 6px; flex-wrap: wrap; }
.seg-btn {
  padding: 6px 16px; border-radius: 8px; font-size: 13px; cursor: pointer; font-family: inherit;
  border: 1px solid var(--border-color); background: transparent; color: var(--text-secondary);
  transition: all .2s ease;
}
.seg-btn:hover:not(:disabled) { background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); color: var(--text-primary); }
.seg-btn.active {
  background: color-mix(in srgb, var(--brand) 14%, transparent); border-color: color-mix(in srgb, var(--brand) 40%, transparent); color: var(--brand-bright); font-weight: 600;
}
.seg-btn:disabled { cursor: not-allowed; opacity: .5; }

/* 滑块 */
.slider-group { max-width: 420px; }
.viz-slider {
  -webkit-appearance: none; appearance: none; width: 100%; height: 6px; border-radius: 3px;
  background: color-mix(in srgb, var(--brand) 25%, transparent); outline: none;
}
.viz-slider::-webkit-slider-thumb {
  -webkit-appearance: none; appearance: none; width: 18px; height: 18px; border-radius: 50%;
  background: var(--viz-s1); border: 2px solid var(--viz-surface); cursor: pointer;
  box-shadow: 0 1px 4px rgba(0,0,0,.3);
}
.viz-slider::-moz-range-thumb {
  width: 18px; height: 18px; border-radius: 50%;
  background: var(--viz-s1); border: 2px solid var(--viz-surface); cursor: pointer;
}
.viz-slider:disabled { opacity: .45; cursor: not-allowed; }
.viz-slider:disabled::-webkit-slider-thumb { cursor: not-allowed; }
.slider-scale { display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); margin-top: 4px; }

/* 开关控件 */
.toggle-switch {
  width: 46px; height: 24px; border-radius: 12px; position: relative;
  background: rgba(128,128,128,.25); border: none; cursor: pointer;
  transition: background .2s ease; font-family: inherit;
}
.toggle-switch.on { background: color-mix(in srgb, var(--brand) 55%, transparent); }
.toggle-knob {
  position: absolute; top: 3px; left: 3px; width: 18px; height: 18px;
  border-radius: 50%; background: #fff; transition: transform .2s ease;
  box-shadow: 0 1px 3px rgba(0,0,0,.3);
}
.toggle-switch.on .toggle-knob { transform: translateX(22px); }
.toggle-switch:disabled { opacity: .5; cursor: not-allowed; }

/* 参数底部规则 */
.param-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 10px; flex-wrap: wrap; }
.rule-text { font-size: 11px; color: var(--text-muted); line-height: 1.5; }
.tune-note {
  font-size: 11px; color: var(--viz-warn); background: rgba(250,178,25,.08);
  padding: 2px 8px; border-radius: 8px; white-space: nowrap;
}

/* ===== 磨合记录时间线 ===== */
.timeline { display: flex; flex-direction: column; }
.timeline-row { display: flex; align-items: flex-start; gap: 12px; padding: 8px 0; }
.tl-date { width: 74px; flex-shrink: 0; font-size: 12px; color: var(--text-muted); font-variant-numeric: tabular-nums; padding-top: 2px; }
.tl-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 6px;
  background: var(--viz-s1); box-shadow: 0 0 0 3px color-mix(in srgb, var(--brand) 15%, transparent);
}
.tl-body { display: flex; flex-direction: column; gap: 3px; }
.tl-text { font-size: 13px; color: var(--text-primary); }
.tl-effect { font-size: 12px; color: var(--viz-good); font-variant-numeric: tabular-nums; }
.tl-effect.pending { color: var(--text-muted); }
.tl-empty { font-size: 12px; color: var(--text-muted); padding: 8px 0; }
.ad-loading { text-align: center; font-size: 13px; color: var(--text-muted); padding: 48px 0; }

/* ===== 特点面板 ===== */
.source-tag {
  font-size: 11px; color: var(--text-muted); margin-left: 8px;
  background: rgba(15,23,42,.04); border: 1px solid rgba(15,23,42,.06);
  padding: 1px 8px; border-radius: 8px; white-space: nowrap;
}
[data-theme="dark"] .source-tag { background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent); border-color: var(--line-soft); }
.feat-bars { display: flex; flex-direction: column; gap: 10px; }
.feat-row { display: flex; align-items: center; gap: 12px; }
.feat-label {
  width: 150px; flex-shrink: 0; font-size: 13px; color: var(--text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.feat-track { flex: 1; height: 20px; background: rgba(128,128,128,.08); border-radius: 5px; overflow: hidden; }
.feat-fill {
  height: 100%; border-radius: 5px; background: var(--viz-s1);
  transition: width .5s cubic-bezier(.4,0,.2,1); min-width: 3px;
}
.feat-value { width: 60px; text-align: right; font-size: 13px; color: var(--viz-ink); font-variant-numeric: tabular-nums; flex-shrink: 0; }
.feat-compare { display: flex; gap: 14px; }
.feat-stat {
  flex: 1; border: 1px solid var(--viz-grid); border-radius: 12px;
  padding: 14px 16px; display: flex; flex-direction: column; gap: 6px;
}
.feat-stat-label { font-size: 12px; color: var(--text-muted); }
.feat-stat-value { font-size: 24px; font-weight: 700; }
.feat-stat-value small { font-size: 12px; font-weight: 400; color: var(--text-muted); }

/* ===== 页脚 ===== */
.ad-footnote { text-align: center; font-size: 12px; color: var(--text-muted); margin: 8px 0 0; }

/* ===== 浅色主题：白底卡片 + 深色细边框（暗色毛玻璃设计在浅色下无对比） ===== */
[data-theme="light"] .ad-page .ad-card,
[data-theme="light"] .ad-page .stat-tile {
  background: color-mix(in srgb, var(--surface, #ffffff) 92%, transparent);
  border-color: rgba(15,23,42,.09);
  box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 6px 20px rgba(15,23,42,.05);
}
[data-theme="light"] .ad-page .param-item {
  background: rgba(15,23,42,.02);
  border-color: rgba(15,23,42,.07);
}
[data-theme="light"] .ad-page .back-btn:hover,
[data-theme="light"] .ad-page .ghost-btn:hover,
[data-theme="light"] .ad-page .seg-btn:hover:not(:disabled) {
  background: rgba(15,23,42,.05);
  color: var(--text-primary);
}

/* ===== 响应式 ===== */
@media (max-width: 860px) {
  .ad-page { padding: 20px 16px 32px; }
  .stat-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 560px) {
  .stat-row { grid-template-columns: 1fr; }
  .param-foot { flex-direction: column; align-items: flex-start; }
}
</style>
