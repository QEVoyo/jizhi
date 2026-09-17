<template>
  <div class="agent-center">
    <!-- ===== 返回 ===== -->
    <button class="back-btn" @click="router.push('/home')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      返回主界面
    </button>

    <!-- ===== 页头 ===== -->
    <div class="ac-header">
      <div class="ac-header-left">
        <h1 class="ac-title">智能体中心</h1>
        <p class="ac-subtitle">5 个 AI 学习伙伴如何协同工作 · 点击卡片进入单个智能体的细节调节</p>
      </div>
      <!-- 数据范围筛选（一行，作用于下方所有内容） -->
      <div class="ac-filter">
        <button
          v-for="r in rangeOptions"
          :key="r.value"
          class="range-btn"
          :class="{ active: range === r.value }"
          @click="range = r.value"
        >{{ r.label }}</button>
      </div>
    </div>

    <!-- ===== 加载 / 错误 ===== -->
    <p v-if="loading" class="ac-loading">数据加载中…</p>
    <p v-else-if="error" class="ac-loading">{{ error }}</p>

    <!-- ===== KPI 行 ===== -->
    <div v-if="ov" class="kpi-row">
      <div class="kpi-tile" v-for="k in kpis" :key="k.label">
        <span class="kpi-label">{{ k.label }}</span>
        <div class="kpi-value-row">
          <span class="kpi-value">{{ k.value }}</span>
          <span v-if="k.delta" class="kpi-delta" :class="k.up ? 'up' : 'down'">{{ k.delta }}</span>
        </div>
        <svg v-if="k.spark" class="kpi-spark" viewBox="0 0 120 32" aria-hidden="true">
          <polyline :points="k.spark" fill="none" stroke="var(--viz-muted)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
          <circle :cx="k.endX" :cy="k.endY" r="3.5" fill="var(--viz-s1)" stroke="var(--viz-surface)" stroke-width="2" />
        </svg>
        <span v-else class="kpi-note">{{ k.note }}</span>
      </div>
    </div>

    <!-- ===== 学习协作闭环 ===== -->
    <section v-if="ov" class="ac-card">
      <div class="card-head">
        <h2 class="card-title">学习协作闭环</h2>
        <span class="card-head-note">近 30 天 · 5 智能体协作</span>
      </div>
      <p class="card-desc">你的学习在这条链路上流转——每个环节由一个智能体主导</p>
      <div class="loop-flow">
        <template v-for="(l, i) in collab.loop" :key="l.step">
          <div class="loop-node" :style="{ '--loop-c': agentColor(l.agent_key) }">
            <span class="loop-step">{{ l.step }}</span>
            <strong class="loop-text">{{ l.text }}</strong>
            <span class="loop-sub">{{ l.sub }}</span>
          </div>
          <div v-if="i < collab.loop.length - 1" class="loop-arrow">→</div>
        </template>
      </div>
      <p class="loop-note">{{ collab.xiaoji_line.text }} <span class="source-tag">数据源：{{ collab.xiaoji_line.source }}</span></p>
    </section>

    <!-- ===== 协同增益 ===== -->
    <section v-if="ov" class="ac-card">
      <div class="card-head">
        <h2 class="card-title">协同增益</h2>
        <span class="card-head-note">跨表联合分析</span>
      </div>
      <p class="card-desc">一个智能体的介入，如何改变另一个智能体的效果</p>
      <p class="analysis-summary">{{ collab.synergy_summary }}</p>
      <div class="syn-list">
        <div class="syn-row" v-for="s in collab.synergy" :key="s.metric + s.note">
          <span class="syn-pair">
            <b class="syn-chip" :style="{ color: agentColor(s.pair[0]) }">{{ agentName(s.pair[0]) }}</b>
            <span class="syn-x">×</span>
            <b class="syn-chip muted">{{ agentName(s.pair[1]) }}</b>
          </span>
          <span class="syn-metric">{{ s.metric }}</span>
          <span class="syn-bars">
            <span class="syn-bar-group">
              <span class="syn-bar-track"><span class="syn-bar base" :style="{ width: synBarW(s.base, s) }"></span></span>
              <span class="syn-bar-label">{{ fmtNum(s.base, s.unit) }}</span>
            </span>
            <span class="syn-bar-group">
              <span class="syn-bar-track"><span class="syn-bar boost" :style="{ width: synBarW(s.boost, s), background: agentColor(s.pair[0]) }"></span></span>
              <span class="syn-bar-label boost">{{ fmtNum(s.boost, s.unit) }}</span>
            </span>
          </span>
          <span v-if="s.delta != null" class="syn-delta">▲ {{ s.delta }}{{ s.unit }}</span>
          <span class="syn-note">{{ s.note }} · {{ s.source }}</span>
        </div>
      </div>
    </section>

    <!-- ===== 对话路由转化 ===== -->
    <section v-if="ov" class="ac-card">
      <div class="card-head">
        <h2 class="card-title">对话路由转化</h2>
        <span class="card-head-note">找瓶颈链路</span>
      </div>
      <p class="card-desc">对话 Agent 分流出去的请求，落地成了什么</p>
      <p class="analysis-summary">{{ collab.routing_summary }}</p>
      <div class="route-list">
        <div class="route-row" v-for="r in collab.routing" :key="r.agent_key">
          <img :src="agentImg(r.agent_key)" alt="" class="bar-icon">
          <span class="route-name">分流 {{ agentName(r.agent_key) }}</span>
          <span class="route-count">{{ r.uses }} 次</span>
          <span class="route-arrow">→</span>
          <span class="route-output">{{ r.output || '聊天内产出未独立记录' }}</span>
          <span v-if="r.rate != null" class="route-rate" :class="{ warn: r.warn }">{{ r.rate }}{{ r.rate_unit }}</span>
          <span class="route-source">{{ r.note }}</span>
        </div>
      </div>
    </section>

    <!-- ===== 智能体入口卡（压缩版，详情见细节调节页） ===== -->
    <section v-if="ov" class="agent-grid">
      <article
        v-for="a in agents"
        :key="a.key"
        class="ac-card agent-card clickable"
        :class="'agent-' + a.key"
        @click="goDetail(a.key)"
      >
        <div class="agent-head">
          <div class="agent-badge" :style="{ background: a.grad }"><img :src="a.img" alt="" class="agent-badge-img"></div>
          <div class="agent-id">
            <div class="agent-name-row">
              <h3 class="agent-name">{{ a.name }}</h3>
            </div>
            <span class="fit-chip" :style="{ color: a.color }">{{ a.tagline }}</span>
          </div>
        </div>
        <div class="agent-metric">
          <div class="metric-left">
            <span class="mini-label">{{ a.metric?.label }}</span>
            <div class="metric-val-row">
              <span class="mini-value">{{ fmtNum(a.metric?.value, a.metric?.unit) }}</span>
              <span v-if="a.metric?.delta" class="mini-delta" :class="a.metric.up ? 'up' : 'down'">{{ a.metric.delta }}</span>
            </div>
          </div>
          <svg class="mini-spark" viewBox="0 0 120 28" aria-hidden="true">
            <polyline :points="sparkPoints(a)" fill="none" :stroke="a.color" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
            <circle :cx="sparkEnd(a).x" :cy="sparkEnd(a).y" r="3" :fill="a.color" stroke="var(--viz-surface)" stroke-width="2" />
          </svg>
        </div>
        <div class="card-footer-hint">进入细节调节 →</div>
      </article>
    </section>

    <p class="ac-footnote">以上数据由你近期的真实学习行为汇总而成 · 参数调整与磨合记录会随使用自动更新</p>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { agents as agentsMeta } from '@/utils/mockAgents'
import { getOverview } from '@/api/agentCenter'

const router = useRouter()
const authStore = useAuthStore()

// ===== 数据范围（作用于下方全部内容，后端按 days 聚合） =====
const range = ref('30d')
const rangeOptions = [
  { value: '7d', label: '近 7 天', days: 7 },
  { value: '30d', label: '近 30 天', days: 30 },
  { value: 'all', label: '全部（近一年）', days: 365 },
]
const loading = ref(false)
const error = ref('')
const ov = ref(null)

async function load() {
  if (!authStore.user?.id) return
  loading.value = true
  error.value = ''
  try {
    ov.value = await getOverview(authStore.user.id, rangeOptions.find(r => r.value === range.value).days)
  } catch (e) {
    error.value = '数据加载失败，请稍后重试'
    console.error('[agent-center] overview:', e)
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(range, load)

function goDetail(key) {
  router.push(`/agent-center/${key}`)
}

// ===== 静态元数据（图标/名称/特点） + 真实数据合并 =====
const agents = computed(() => {
  if (!ov.value) return []
  return agentsMeta.map(m => {
    const d = ov.value.agents.find(x => x.key === m.key) || {}
    return { ...m, calls: d.calls ?? 0, metric: d.metric || null, spark: d.trend || [] }
  })
})

function metaOf(key) { return agentsMeta.find(a => a.key === key) }
const pairNames = { practice: '练习', mastery: '掌握度' }
function agentName(key) { return metaOf(key)?.name || pairNames[key] || key }
function agentColor(key) { return metaOf(key)?.color || 'var(--viz-s1)' }
function agentImg(key) { return metaOf(key)?.img || '' }

function fmtNum(v, unit) { return v == null ? '—' : `${v}${unit || ''}` }
// ===== KPI（真实数据，来自 /agent-center/overview） =====
const kpis = computed(() => {
  if (!ov.value) return []
  const k = ov.value.kpi
  return [
    { label: '总调用次数', value: (k.total_calls ?? 0).toLocaleString(), note: `全部触点（近 ${ov.value.range_days} 天）` },
    { label: '活跃智能体', value: k.active_agents, note: '规划 · 生成 · 评估 · 对话 · 小基' },
    { label: '平均计划完成率', value: fmtNum(k.plan_completion, '%'), note: '统计自你的学习计划' },
    { label: '生成题目', value: fmtNum(k.generated_questions, '题'), note: '统计自你的生成记录' },
    { label: '批改题量', value: fmtNum(k.graded_questions, '题'), note: '统计自你的批改记录' },
    { label: '词条抓取', value: k.vocab_lookups == null ? '🆕 待建' : fmtNum(k.vocab_lookups, '个'), note: '词条功能建设中' },
  ]
})

// ===== 协作分析（跨智能体联合数据，来自 /agent-center/overview） =====
const collab = computed(() => ov.value || null)

// ===== 协同增益配对条形图 =====
function synNum(v) {
  const n = parseFloat(String(v).replace(/[^\d.]/g, ''))
  return isNaN(n) ? 0 : n
}
function synBarW(v, s) {
  const max = Math.max(synNum(s.base), synNum(s.boost))
  if (!max) return '0%'
  return (synNum(v) / max * 100).toFixed(1) + '%'
}

// ===== 迷你趋势 =====
function sparkPoints(a) {
  if (!a.spark || a.spark.length < 2) return ''
  const max = Math.max(...a.spark)
  const min = Math.min(...a.spark)
  return a.spark.map((v, i) => `${(i / (a.spark.length - 1)) * 120},${28 - ((v - min) / (max - min || 1)) * 22 - 3}`).join(' ')
}
function sparkEnd(a) {
  if (!a.spark || !a.spark.length) return { x: 120, y: 25 }
  const max = Math.max(...a.spark)
  const min = Math.min(...a.spark)
  const v = a.spark[a.spark.length - 1]
  return { x: 120, y: 28 - ((v - min) / (max - min || 1)) * 22 - 3 }
}
</script>

<style scoped>
/* ===== 图表变量：数据色只在图表内使用（参考调色板，浅色默认 / 深色覆盖） ===== */
.agent-center {
  --viz-s1: #2a78d6;
  --viz-s2: #eb6834;
  --viz-s3: #1baf7a;
  --viz-s4: #eda100;
  --viz-s5: #e87ba4;
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
  max-width: 1160px;
  margin: 0 auto;
}
[data-theme="dark"] .agent-center {
  --viz-s1: #3987e5;
  --viz-s2: #d95926;
  --viz-s3: #199e70;
  --viz-s4: #c98500;
  --viz-s5: #d55181;
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

/* ===== 返回按钮 ===== */
.back-btn {
  display: inline-flex; align-items: center; gap: 6px;
  background: transparent; border: none; color: var(--text-secondary);
  font-size: 13px; cursor: pointer; padding: 4px 8px; border-radius: 8px;
  transition: all .2s ease; font-family: inherit; margin-bottom: 14px;
}
.back-btn svg { width: 16px; height: 16px; }
.back-btn:hover { color: var(--text-primary); background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); transform: translateX(-2px); }
[data-theme="light"] .back-btn:hover { background: rgba(15,23,42,.05); }

/* ===== 页头 ===== */
.ac-header {
  display: flex; align-items: flex-end; justify-content: space-between;
  gap: 16px; flex-wrap: wrap; margin-bottom: 22px;
}
.ac-title { font-size: 26px; font-weight: 700; color: var(--text-primary); margin: 0; }
.ac-subtitle { font-size: 13px; color: var(--text-secondary); margin: 6px 0 0; }

.ac-filter { display: flex; gap: 6px; }
.range-btn {
  padding: 6px 14px; border-radius: 8px; font-size: 12px; cursor: pointer;
  border: 1px solid var(--border-color); background: transparent;
  color: var(--text-secondary); transition: all .2s ease; font-family: inherit;
}
.range-btn:hover { background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); color: var(--text-primary); }
.range-btn.active {
  background: color-mix(in srgb, var(--brand) 14%, transparent); border-color: color-mix(in srgb, var(--brand) 35%, transparent);
  color: var(--brand-bright); font-weight: 600;
}

/* ===== KPI 行 ===== */
.kpi-row {
  display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 18px;
}
.kpi-tile {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid rgba(255,255,255,.06);
  border-radius: 14px; padding: 14px 14px 10px; backdrop-filter: blur(20px);
  transition: transform .2s ease; min-width: 0;
}
.kpi-tile:hover { transform: translateY(-2px); }
[data-theme="dark"] .kpi-tile { background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent); }
.kpi-label { font-size: 12px; color: var(--text-secondary); }
.kpi-value-row { display: flex; align-items: baseline; gap: 8px; margin-top: 6px; }
.kpi-value { font-size: 26px; font-weight: 700; color: var(--viz-ink); }
.kpi-delta { font-size: 11px; }
.kpi-delta.up { color: var(--viz-good); }
.kpi-delta.down { color: var(--viz-crit); }
.kpi-spark { display: block; width: 100%; height: 32px; margin-top: 8px; }
.kpi-note { display: block; font-size: 11px; color: var(--text-muted); margin-top: 10px; }

/* ===== 卡片通用 ===== */
.ac-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid rgba(255,255,255,.06);
  border-radius: 16px; padding: 20px 22px; backdrop-filter: blur(20px); margin-bottom: 18px;
}
[data-theme="dark"] .ac-card { background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent); }
.card-head { display: flex; align-items: center; justify-content: space-between; }
.card-title { font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 0; }
.card-desc { font-size: 12px; color: var(--text-muted); margin: 6px 0 16px; }

/* ===== 卡片头备注 / 数据源标签 ===== */
.card-head-note { font-size: 11px; color: var(--text-muted); flex-shrink: 0; }
.source-tag {
  font-size: 11px; color: var(--text-muted); margin-left: 8px;
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent); border: 1px solid var(--line-soft);
  padding: 1px 8px; border-radius: 8px; white-space: nowrap;
}
[data-theme="light"] .source-tag { background: rgba(15,23,42,.04); border-color: rgba(15,23,42,.06); }
.bar-icon { width: 17px; height: 17px; object-fit: contain; flex-shrink: 0; }

/* ===== 协作闭环 ===== */
.loop-flow { display: flex; align-items: stretch; gap: 8px; margin-bottom: 10px; }
.loop-node {
  flex: 1; min-width: 0;
  border: 1px solid var(--line-soft);
  border-left: 3px solid var(--loop-c, var(--viz-s1));
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); border-radius: 10px;
  padding: 12px 14px; display: flex; flex-direction: column; gap: 4px;
}
[data-theme="light"] .loop-node {
  background: rgba(15,23,42,.02); border-color: rgba(15,23,42,.08);
  border-left-color: var(--loop-c, var(--viz-s1));
}
.loop-step { font-size: 11px; color: var(--text-muted); }
.loop-text { font-size: 14px; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.loop-sub { font-size: 10px; color: var(--text-muted); line-height: 1.4; word-break: break-all; }
.loop-arrow { align-self: center; color: var(--viz-muted); font-size: 16px; flex-shrink: 0; }
.loop-note { font-size: 12px; color: var(--text-secondary); margin: 2px 0 0; line-height: 1.6; }

/* ===== 协同增益 ===== */
.syn-list { display: flex; flex-direction: column; gap: 8px; }
.syn-row {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  padding: 10px 12px; border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); border: 1px solid rgba(255,255,255,.05);
  transition: background .15s ease;
}
[data-theme="light"] .syn-row { background: rgba(15,23,42,.02); border-color: rgba(15,23,42,.06); }
.syn-row:hover { background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); }
[data-theme="light"] .syn-row:hover { background: rgba(15,23,42,.04); }
.syn-pair { display: inline-flex; align-items: center; gap: 6px; min-width: 150px; }
.syn-chip { font-size: 12px; font-weight: 600; }
.syn-chip.muted { color: var(--text-secondary); }
.syn-x { color: var(--text-muted); font-size: 11px; }
.syn-metric { font-size: 13px; color: var(--text-primary); min-width: 90px; }
.syn-bars { flex: 1; min-width: 180px; display: flex; flex-direction: column; gap: 3px; }
.syn-bar-group { display: flex; align-items: center; gap: 8px; }
.syn-bar-track { flex: 1; height: 10px; border-radius: 5px; background: rgba(128,128,128,.10); overflow: hidden; }
.syn-bar { display: block; height: 100%; border-radius: 5px; transition: width .5s cubic-bezier(.4,0,.2,1); }
.syn-bar.base { background: var(--viz-muted); opacity: .5; }
.syn-bar.boost { background: var(--viz-s1); }
.syn-bar-label { font-size: 11px; color: var(--text-muted); width: 62px; flex-shrink: 0; font-variant-numeric: tabular-nums; }
.syn-bar-label.boost { color: var(--viz-ink); font-weight: 700; }
.syn-delta {
  font-size: 12px; font-weight: 700; color: var(--viz-good);
  background: rgba(12,163,12,.10); padding: 2px 8px; border-radius: 8px;
}
.syn-note { font-size: 11px; color: var(--text-muted); margin-left: auto; }

/* ===== 路由转化 ===== */
.route-list { display: flex; flex-direction: column; gap: 8px; }
.route-row {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 10px 12px; border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); border: 1px solid rgba(255,255,255,.05);
}
[data-theme="light"] .route-row { background: rgba(15,23,42,.02); border-color: rgba(15,23,42,.06); }
.route-name { font-size: 13px; color: var(--text-primary); }
.route-count { font-size: 13px; color: var(--viz-ink-2); font-variant-numeric: tabular-nums; }
.route-arrow { color: var(--viz-muted); }
.route-output { font-size: 13px; color: var(--text-secondary); }
.route-rate {
  font-size: 12px; font-weight: 700; color: var(--viz-good);
  background: rgba(12,163,12,.10); padding: 2px 8px; border-radius: 8px;
}
.route-rate.warn { color: var(--viz-warn); background: rgba(250,178,25,.12); }
.route-source { font-size: 11px; color: var(--text-muted); margin-left: auto; }

/* ===== 智能体入口卡网格（压缩版） ===== */
.agent-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 14px; }

.agent-card { padding: 16px 16px 12px; }
.agent-card.clickable {
  cursor: pointer;
  transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
}
.agent-card.clickable:hover {
  transform: translateY(-3px);
  border-color: var(--line);
  box-shadow: 0 10px 32px rgba(0,0,0,.18);
}
.agent-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.agent-badge {
  width: 44px; height: 44px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(255,255,255,.10);
  overflow: hidden; position: relative;
}
.agent-badge-img { width: 72%; height: 72%; object-fit: contain; position: relative; }
/* 浅色主题下徽章渐变过浅，加暗色遮罩让白色图形可读 */
[data-theme="light"] .agent-badge::before {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(160deg, rgba(15,23,42,.32), rgba(15,23,42,.10));
}
.agent-id { flex: 1; min-width: 0; }
.agent-name-row { display: flex; align-items: center; gap: 8px; }
.agent-name { font-size: 15px; font-weight: 700; color: var(--text-primary); margin: 0; }
.fit-chip { font-size: 11px; font-weight: 600; }
.fit-chip { font-size: 11px; font-weight: 600; display: block; margin-top: 2px; }

/* ===== 卡片内迷你指标 ===== */
.mini-kpis { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }
.mini-kpi {
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); border: 1px solid rgba(255,255,255,.05);
  border-radius: 10px; padding: 10px 12px 8px;
}
.mini-label { font-size: 11px; color: var(--text-muted); display: block; }
.mini-value { font-size: 18px; font-weight: 700; color: var(--viz-ink); margin-right: 6px; }
.mini-value.warn { color: var(--viz-warn); }
.mini-delta { font-size: 11px; }
.mini-delta.up { color: var(--viz-good); }
.mini-delta.down { color: var(--viz-crit); }
.mini-spark { display: block; width: 100%; height: 28px; margin-top: 6px; }

/* ===== 区块标题 ===== */
.block-title { font-size: 12px; font-weight: 700; color: var(--text-muted); margin: 0 0 8px; letter-spacing: .04em; }

/* ===== 触点明细 ===== */
.tp-block { margin-bottom: 14px; }
.tp-stack {
  display: flex; height: 6px; border-radius: 3px; overflow: hidden;
  gap: 1px; background: rgba(128,128,128,.10); margin-bottom: 8px;
}
.tp-stack-seg { height: 100%; border-radius: 1px; transition: opacity .15s ease; }
.tp-row {
  display: flex; align-items: center; gap: 10px; padding: 6px 8px;
  border-radius: 6px; transition: background .15s ease;
}
.tp-row:hover { background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); }
.tp-name { font-size: 13px; color: var(--text-primary); flex-shrink: 0; }
.tp-scene { font-size: 12px; color: var(--text-muted); flex: 1; }
.tp-count { font-size: 12px; color: var(--viz-ink-2); font-variant-numeric: tabular-nums; }

/* ===== 共享参数 ===== */
.param-block { margin-bottom: 14px; }
.param-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.param-chip {
  font-size: 12px; color: var(--text-secondary); padding: 4px 10px;
  border-radius: 20px; background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid rgba(255,255,255,.07);
}
.param-chip b { color: var(--text-primary); font-weight: 600; margin-left: 2px; }

/* ===== 建议横幅 ===== */
.suggest-banner {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  background: rgba(251,146,60,.07); border: 1px solid rgba(251,146,60,.18);
  border-radius: 10px; padding: 10px 14px; margin-bottom: 14px;
}
.suggest-text { font-size: 12px; color: var(--text-secondary); flex: 1; line-height: 1.5; }
.suggest-btn {
  padding: 6px 14px; border-radius: 8px; font-size: 12px; cursor: pointer; flex-shrink: 0;
  border: 1px solid rgba(251,146,60,.4); background: rgba(251,146,60,.14);
  color: color-mix(in srgb, #fbbf24 70%, var(--text-primary)); transition: all .2s ease; font-family: inherit; white-space: nowrap;
}
.suggest-btn:hover { background: rgba(251,146,60,.24); transform: translateY(-1px); }
.suggest-btn.applied { border-color: var(--viz-good); background: rgba(12,163,12,.12); color: var(--viz-good); cursor: default; }

/* ===== 磨合时间线 ===== */
.timeline-entry {
  display: flex; align-items: center; gap: 10px; padding: 6px 8px;
  border-radius: 6px; font-size: 12px;
}
.tl-date { color: var(--text-muted); flex-shrink: 0; font-variant-numeric: tabular-nums; }
.tl-text { color: var(--text-primary); flex: 1; }
.tl-effect { color: var(--viz-good); flex-shrink: 0; font-variant-numeric: tabular-nums; }
.tl-effect.pending { color: var(--text-muted); }

/* ===== 卡片底部提示 ===== */
.card-footer-hint {
  margin-top: 10px; text-align: right; font-size: 11px; color: var(--text-muted);
  opacity: .7; transition: opacity .2s ease, transform .2s ease;
}
.agent-card.clickable:hover .card-footer-hint { opacity: 1; transform: translateX(-4px); }

/* ===== 页脚注 / 加载态 ===== */
.ac-footnote { text-align: center; font-size: 12px; color: var(--text-muted); margin: 8px 0 0; }
.ac-loading { text-align: center; font-size: 13px; color: var(--text-muted); padding: 48px 0; }

/* ===== 浅色主题：毛玻璃暗色设计在浅色底上无对比，换白底卡片 + 深色细边框 ===== */
[data-theme="light"] .agent-center .ac-card,
[data-theme="light"] .agent-center .kpi-tile {
  background: color-mix(in srgb, var(--surface, #ffffff) 92%, transparent);
  border-color: rgba(15,23,42,.09);
  box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 6px 20px rgba(15,23,42,.05);
}
[data-theme="light"] .agent-center .mini-kpi {
  background: rgba(15,23,42,.03);
  border-color: rgba(15,23,42,.06);
}
[data-theme="light"] .agent-center .param-chip {
  background: rgba(15,23,42,.04);
  border-color: rgba(15,23,42,.09);
}
[data-theme="light"] .agent-center .range-btn:hover {
  background: rgba(15,23,42,.05);
  color: var(--text-primary);
}
[data-theme="light"] .agent-center .tp-row:hover {
  background: rgba(15,23,42,.04);
}

/* ===== 响应式 ===== */
@media (max-width: 860px) {
  .agent-center { padding: 20px 16px 32px; }
  .kpi-row { grid-template-columns: repeat(3, 1fr); }
  .loop-flow { flex-direction: column; }
  .loop-arrow { transform: rotate(90deg); align-self: center; }
  .syn-note, .route-source { margin-left: 0; }
}
@media (max-width: 560px) {
  .kpi-row { grid-template-columns: repeat(2, 1fr); }
  .agent-grid { grid-template-columns: 1fr; }
  .syn-pair { min-width: 0; }
}
</style>
