<template>
  <Teleport to="body">
    <Transition name="acp-fade">
      <div v-if="agentPanelState.open" class="acp-mask" @click.self="close">
        <section class="acp-panel" role="dialog" aria-modal="true" aria-label="小队协作">
          <header class="acp-head">
            <div class="acp-title-wrap">
              <span class="acp-live" :class="{ on: isActive }" aria-hidden="true"></span>
              <div>
                <h2 class="acp-title">{{ title }}</h2>
                <p class="acp-sub">
                  {{ workflowName }}<template v-if="run?.stage"> · {{ stageText(run.stage) }}</template>
                </p>
              </div>
            </div>
            <div class="acp-head-right">
              <span v-if="run" class="acp-status" :class="run.status">{{ statusText(run.status) }}</span>
              <button class="acp-x" title="收起" @click="close">×</button>
            </div>
          </header>

          <p v-if="error" class="acp-error">{{ error }}</p>

          <div v-if="loading && !run" class="acp-empty">
            <div class="acp-spinner"></div>
            <p>正在读取运行记录…</p>
          </div>

          <div v-else-if="!run" class="acp-empty">
            <div class="acp-empty-icon">◎</div>
            <p>当前没有可看的运行记录。去任务页看看，或者从工作流发起一次真实运行。</p>
            <button class="acp-primary" @click="goCenter">去任务页</button>
          </div>

          <template v-else>
            <div class="acp-metrics">
              <span class="acp-metric">进度 <b>{{ run.progress || 0 }}%</b></span>
              <span v-if="run.llm_calls != null" class="acp-metric">调用 <b>{{ run.llm_calls }}</b></span>
              <span v-if="run.tokens" class="acp-metric">Token <b>{{ run.tokens }}</b></span>
              <span v-if="run.cost" class="acp-metric">成本 <b>¥{{ Number(run.cost).toFixed(4) }}</b></span>
              <span v-if="run.latency_ms" class="acp-metric">耗时 <b>{{ (run.latency_ms / 1000).toFixed(1) }}s</b></span>
              <span class="acp-metric acp-metric-grow">
                <span class="acp-bar"><span :style="{ width: Math.max(0, Math.min(100, run.progress || 0)) + '%' }"></span></span>
              </span>
            </div>

            <div class="acp-body">
              <div class="acp-graph-wrap">
                <div v-if="graph.nodes.length" class="acp-graph-scroll">
                  <svg class="acp-graph" :viewBox="`0 0 ${graph.width} ${graph.height}`"
                       :style="{ width: graph.width + 'px', height: graph.height + 'px' }"
                       role="img" aria-label="工作流节点图">
                    <path v-for="e in graph.edges" :key="e.key" :d="e.d" class="acp-edge" :class="e.status" />
                    <g v-for="n in graph.nodes" :key="n.key" class="acp-node" :class="[n.status, { selected: selectedKey === n.key }]"
                       @click="selectedKey = n.key">
                      <rect :x="n.x" :y="n.y" :width="NW" :height="NH" rx="10" />
                      <circle :cx="n.x + 14" :cy="n.y + 18" r="4" class="acp-node-dot" />
                      <text :x="n.x + 24" :y="n.y + 22" class="acp-node-key">{{ nodeLabel(n.key) }}</text>
                      <text :x="n.x + 14" :y="n.y + 42" class="acp-node-agent">{{ agentLabel(n) }}</text>
                    </g>
                  </svg>
                </div>
                <p v-else class="acp-muted">这次运行还没有节点轨迹。</p>
              </div>

              <aside class="acp-detail">
                <template v-if="selectedNode">
                  <div class="acp-detail-head">
                    <b>{{ nodeLabel(selectedNode.key) }}</b>
                    <span class="acp-detail-key">{{ selectedNode.key }}</span>
                    <span class="acp-detail-agent">{{ agentLabel(selectedNode) }}</span>
                    <span class="acp-detail-status" :class="selectedNode.status">{{ statusText(selectedNode.status) }}</span>
                  </div>
                  <p v-if="selectedStep?.output?.summary" class="acp-detail-summary">{{ selectedStep.output.summary }}</p>
                  <p v-if="selectedStep?.verification?.error" class="acp-detail-error">{{ selectedStep.verification.error }}</p>
                  <div v-if="selectedStep" class="acp-kv">
                    <span v-if="selectedStep.created_at">开始 {{ fmtTime(selectedStep.created_at) }}</span>
                    <span v-if="selectedStep.ended_at">结束 {{ fmtTime(selectedStep.ended_at) }}</span>
                  </div>
                  <details v-if="selectedStep?.input" class="acp-json" open>
                    <summary>输入</summary>
                    <pre>{{ pretty(selectedStep.input) }}</pre>
                  </details>
                  <details v-if="selectedStep?.output" class="acp-json" open>
                    <summary>输出</summary>
                    <pre>{{ pretty(selectedStep.output) }}</pre>
                  </details>
                  <p v-if="!selectedStep" class="acp-muted">这个节点还没开始。</p>
                </template>
                <template v-else>
                  <p class="acp-muted">点一个节点看输入/输出。</p>
                </template>

                <div v-if="run.error" class="acp-run-error">
                  <b>运行失败</b>
                  <p>{{ run.error }}</p>
                </div>
                <div v-else-if="run.output" class="acp-run-out">
                  <b>运行产物</b>
                  <p>{{ runSummary }}</p>
                </div>
              </aside>
            </div>

            <div class="acp-msgs">
              <div class="acp-msgs-head">
                <h3>消息流</h3>
                <span class="acp-muted">{{ messages.length ? `${messages.length} 条 A2A 消息` : '本次运行没有 A2A 消息' }}</span>
              </div>
              <div v-if="messages.length" class="acp-msg-list">
                <div v-for="m in messages" :key="m.id || m.seq" class="acp-msg">
                  <span class="acp-msg-from">{{ roleName(m.from_agent) }}</span>
                  <span class="acp-msg-arrow">→</span>
                  <span class="acp-msg-to">{{ roleName(m.to_agent) }}</span>
                  <span class="acp-msg-kind">{{ kindText(m.kind) }}</span>
                  <p class="acp-msg-text">{{ m.content }}</p>
                </div>
              </div>
            </div>

            <footer class="acp-foot">
              <span class="acp-muted">
                {{ run.workflow_key }} · {{ run.id ? String(run.id).slice(0, 8) : '' }}
              </span>
              <button class="acp-ghost" @click="goCenter">智能体中心</button>
              <button class="acp-primary" @click="close">收起</button>
            </footer>
          </template>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getRun, getWorkflows, listRuns } from '@/api/agents'
import { agentPanelState, closeAgentPanel } from '@/stores/agentPanel'

const NW = 150
const NH = 56
const GX = 58
const GY = 18
const PAD = 18

const router = useRouter()
const authStore = useAuthStore()
const userId = computed(() => authStore.user?.id || '')

const bundle = ref(null)
const workflows = ref([])
const loading = ref(false)
const error = ref('')
const selectedKey = ref('')
let timer = null
let token = 0
let currentRunId = ''

const run = computed(() => bundle.value?.run || null)
const steps = computed(() => bundle.value?.steps || [])
const messages = computed(() =>
  (bundle.value?.messages || []).slice().sort((a, b) => (a.seq || 0) - (b.seq || 0)))
const stepsByKey = computed(() =>
  Object.fromEntries(steps.value.map(s => [s.node_key, s])))
const isActive = computed(() =>
  !!run.value && !['completed', 'failed', 'cancelled'].includes(run.value.status))

const workflow = computed(() =>
  workflows.value.find(w => w.key === run.value?.workflow_key) || null)
const workflowName = computed(() =>
  workflow.value?.name || run.value?.workflow_key || '运行')
const title = computed(() =>
  run.value?.title || workflow.value?.name || '小队协作')

const nodes = computed(() => {
  if (workflow.value?.nodes?.length) return workflow.value.nodes
  // 未知工作流：按步骤出现的顺序串成一条线，至少能看进度
  const seen = []
  for (const s of steps.value) {
    if (!s.node_key || seen.some(n => n.key === s.node_key)) continue
    seen.push({ key: s.node_key, agent: s.agent_key, tool: '', deps: seen.length ? [seen[seen.length - 1].key] : [] })
  }
  return seen
})

const graph = computed(() => {
  const list = nodes.value
  if (!list.length) return { nodes: [], edges: [], width: 0, height: 0 }
  const byKey = new Map(list.map(n => [n.key, n]))
  const depth = new Map()
  const visiting = new Set()
  function visit(key) {
    if (depth.has(key)) return depth.get(key)
    const n = byKey.get(key)
    if (!n || !n.deps?.length || visiting.has(key)) {
      depth.set(key, 0)
      return 0
    }
    visiting.add(key)
    const d = 1 + Math.max(...n.deps.map(dep => visit(dep)))
    visiting.delete(key)
    depth.set(key, d)
    return d
  }
  list.forEach(n => visit(n.key))

  const groups = new Map()
  for (const n of list) {
    const l = depth.get(n.key) || 0
    if (!groups.has(l)) groups.set(l, [])
    groups.get(l).push(n)
  }
  const maxCount = Math.max(...[...groups.values()].map(g => g.length))
  const placed = []
  for (const [l, group] of [...groups.entries()].sort((a, b) => a[0] - b[0])) {
    const offset = ((maxCount - group.length) * (NH + GY)) / 2
    group.forEach((n, i) => {
      placed.push({
        ...n,
        x: PAD + l * (NW + GX),
        y: PAD + offset + i * (NH + GY),
        status: stepsByKey.value[n.key]?.status || 'pending',
      })
    })
  }
  const pos = new Map(placed.map(n => [n.key, n]))
  const edges = []
  for (const n of placed) {
    for (const dep of (n.deps || [])) {
      const s = pos.get(dep)
      if (!s) continue
      const x1 = s.x + NW
      const y1 = s.y + NH / 2
      const x2 = n.x
      const y2 = n.y + NH / 2
      const mx = (x1 + x2) / 2
      edges.push({
        key: `${dep}->${n.key}`,
        status: n.status,
        d: `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`,
      })
    }
  }
  const width = Math.max(...placed.map(n => n.x + NW)) + PAD
  const height = Math.max(...placed.map(n => n.y + NH)) + PAD
  return { nodes: placed, edges, width, height }
})

const selectedNode = computed(() =>
  graph.value.nodes.find(n => n.key === selectedKey.value) || null)
const selectedStep = computed(() => stepsByKey.value[selectedKey.value] || null)

const runSummary = computed(() => {
  const o = run.value?.output
  if (!o) return ''
  if (typeof o === 'string') return o
  return o.message || o.summary || o.diagnosis
    || (o.questions?.length ? `生成 ${o.questions.length} 道题` : '') || pretty(o, 800)
})

const STATUS_TEXT = {
  pending: '等待', queued: '排队中', running: '进行中', paused: '已暂停',
  completed: '已完成', failed: '失败', skipped: '跳过', cancelled: '已取消',
  awaiting_confirm: '待确认', confirmed: '已确认',
}
function statusText(s) { return STATUS_TEXT[s] || s || '' }
const KIND_TEXT = {
  task: '任务', proposal: '提议', critique: '质疑', verdict: '裁决',
  result: '汇总', escalation: '升级',
}
function kindText(k) { return KIND_TEXT[k] || k || '' }
const ROLE_TEXT = {
  planner: '规划', retriever: '检索', generator: '生成', verifier: '校验',
  conductor: '队长', evaluator: '评估', debate_context: '取证', debate_data: '数据',
  debate_plan: '规划', debate_eval: '评估', debate_xiaoji: '小基',
  debate_judge: '主控', 'docs.parse': '解析',
}
function roleName(k) { return ROLE_TEXT[k] || k || '' }
const AGENT_TEXT = {
  planner: '规划 Agent', retriever: '检索 Agent', generator: '生成 Agent',
  verifier: '校验 Agent', conductor: '队长', evaluator: '评估 Agent',
  'docs.parse': '文档解析', 'bank.persist': '落库',
  debate_context: '证据节点', debate_data: '数据 Agent',
  debate_plan: '规划 Agent', debate_eval: '评估 Agent', debate_xiaoji: '小基 Agent',
  debate_judge: '主控 Judge',
}
const NODE_TEXT = {
  plan: '规划', retrieve: '检索', generate: '生成', verify: '校验',
  repair: '修复', verify_retry: '复检', persist: '落库', aggregate: '汇总',
  verify_semantic: '语义复核',
  parse: '解析', evaluate: '评估', evidence: '取证', data: '数据',
  judge: '裁决', xiaoji: '小基',
}
function agentLabel(n) {
  return AGENT_TEXT[n.agent] || AGENT_TEXT[n.tool] || n.agent || n.tool || '节点'
}
function nodeLabel(key) {
  return NODE_TEXT[key] || key
}
function stageText(s) { return STATUS_TEXT[s] || s || '' }
function fmtTime(s) {
  if (!s) return ''
  try {
    const d = new Date(s)
    if (Number.isNaN(d.getTime())) return String(s).slice(0, 19)
    return d.toLocaleTimeString('zh-CN', { hour12: false })
  } catch { return String(s).slice(0, 19) }
}
function pretty(v, max = 4000) {
  if (v == null) return ''
  try {
    const s = typeof v === 'string' ? v : JSON.stringify(v, null, 2)
    return s.length > max ? s.slice(0, max) + '\n…' : s
  } catch {
    return String(v).slice(0, max)
  }
}

function stop() {
  token += 1
  if (timer) clearTimeout(timer)
  timer = null
}

async function loadDefs() {
  if (workflows.value.length) return
  try { workflows.value = await getWorkflows() } catch { workflows.value = [] }
}

async function resolveRunId() {
  if (agentPanelState.runId) return agentPanelState.runId
  if (!userId.value) return ''
  try {
    const runs = await listRuns(userId.value, 12)
    const active = runs.find(r => ['queued', 'running', 'paused', 'awaiting_confirm', 'confirmed'].includes(r.status))
    return (active || runs[0])?.id || ''
  } catch { return '' }
}

async function fetchOnce() {
  if (!currentRunId || !userId.value) return
  const b = await getRun(currentRunId, userId.value)
  bundle.value = b
  if (!b?.run) return
  if (selectedKey.value && !graph.value.nodes.some(n => n.key === selectedKey.value)) {
    selectedKey.value = ''
  }
  if (!selectedKey.value) {
    const target = graph.value.nodes.find(n => n.status === 'running')
      || graph.value.nodes.find(n => n.status === 'failed')
      || graph.value.nodes[0]
    selectedKey.value = target?.key || ''
  }
}

function schedule() {
  stop()
  const my = token
  const tick = async () => {
    if (my !== token) return
    try {
      await fetchOnce()
      if (my !== token) return
      if (isActive.value) timer = setTimeout(tick, 1000)
    } catch (e) {
      if (my !== token) return
      error.value = e?.response?.data?.detail || '读取运行记录失败'
      stop()
    }
  }
  tick()
}

async function openPanel() {
  if (!agentPanelState.open) return
  error.value = ''
  loading.value = true
  try {
    await loadDefs()
    const id = await resolveRunId()
    if (!id) {
      bundle.value = null
      currentRunId = ''
      return
    }
    if (id !== currentRunId) {
      currentRunId = id
      bundle.value = null
      selectedKey.value = ''
    }
    await fetchOnce()
    if (isActive.value) schedule()
    else stop()
  } catch (e) {
    error.value = e?.response?.data?.detail || '读取运行记录失败'
  } finally {
    loading.value = false
  }
}

function close() {
  stop()
  closeAgentPanel()
}

function goCenter() {
  close()
  router.push('/agent-center')
}

watch(() => agentPanelState.open, (v) => {
  if (v) openPanel()
  else stop()
})
watch(userId, (v) => {
  if (v && agentPanelState.open) openPanel()
})
onMounted(() => {
  // 异步组件可能在 openAgentPanel 之后才挂载；补一次初始检查
  if (agentPanelState.open) openPanel()
})
onBeforeUnmount(stop)
</script>

<style scoped>
.acp-mask {
  position: fixed; inset: 0; z-index: 9550;
  display: grid; place-items: center;
  padding: 18px;
  background: rgba(4, 8, 18, .58);
  backdrop-filter: blur(6px);
}
.acp-panel {
  width: min(1180px, 100%);
  max-height: 92vh;
  overflow-y: auto;
  padding: 18px 20px 16px;
  border-radius: 18px;
  background: var(--surface, #0f172a);
  border: 1px solid color-mix(in srgb, var(--brand) 26%, transparent);
  box-shadow: 0 30px 80px rgba(0, 0, 0, .42);
  color: var(--text-primary);
}
.acp-head { display: flex; align-items: flex-start; gap: 12px; }
.acp-title-wrap { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
.acp-live { width: 9px; height: 9px; border-radius: 50%; background: var(--text-muted); flex: none; }
.acp-live.on {
  background: #30d158;
  box-shadow: 0 0 0 5px color-mix(in srgb, #30d158 22%, transparent);
  animation: acp-pulse 1.6s ease-in-out infinite;
}
@keyframes acp-pulse { 0%, 100% { opacity: 1; } 50% { opacity: .45; } }
.acp-title { margin: 0; font-size: 18px; word-break: break-word; }
.acp-sub { margin: 3px 0 0; font-size: 11.5px; color: var(--text-muted); }
.acp-head-right { display: flex; align-items: center; gap: 10px; flex: none; }
.acp-status {
  padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 700;
  background: color-mix(in srgb, var(--brand) 14%, transparent);
  color: var(--brand-bright);
}
.acp-status.completed { background: rgba(48, 209, 88, .14); color: #30d158; }
.acp-status.failed { background: rgba(255, 69, 58, .14); color: #ff6b61; }
.acp-x {
  width: 28px; height: 28px; border-radius: 8px;
  border: 1px solid var(--border-color); background: transparent;
  color: var(--text-muted); font-size: 16px; cursor: pointer;
}
.acp-x:hover { color: var(--text-primary); border-color: var(--brand); }
.acp-error {
  margin: 10px 0; padding: 9px 11px; border-radius: 9px;
  border: 1px solid rgba(230, 162, 60, .4);
  background: rgba(230, 162, 60, .1);
  color: #e6a23c; font-size: 12px;
}
.acp-empty {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  padding: 38px 16px 30px; text-align: center;
  color: var(--text-secondary); font-size: 12.5px; line-height: 1.7;
}
.acp-empty-icon { font-size: 38px; color: var(--brand-bright); opacity: .8; }
.acp-empty p { max-width: 520px; margin: 0; }
.acp-spinner {
  width: 26px; height: 26px; border-radius: 50%;
  border: 3px solid color-mix(in srgb, var(--brand) 20%, transparent);
  border-top-color: var(--brand);
  animation: acp-spin .8s linear infinite;
}
@keyframes acp-spin { to { transform: rotate(360deg); } }

.acp-metrics {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  margin: 12px 0 12px; font-size: 11px; color: var(--text-muted);
}
.acp-metric b { color: var(--text-primary); font-variant-numeric: tabular-nums; }
.acp-metric-grow { flex: 1; min-width: 140px; }
.acp-bar {
  display: block; height: 6px; border-radius: 3px; overflow: hidden;
  background: rgba(128, 128, 128, .16);
}
.acp-bar span {
  display: block; height: 100%; border-radius: 3px;
  background: linear-gradient(90deg, var(--brand), var(--brand-bright));
  transition: width .4s ease;
}

.acp-body {
  display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 12px;
  align-items: start;
}
.acp-graph-wrap {
  min-width: 0; border: 1px solid var(--border-color); border-radius: 13px;
  background: color-mix(in srgb, var(--surface, #fff) 3%, transparent);
  padding: 8px;
}
.acp-graph-scroll { overflow-x: auto; }
.acp-graph { display: block; }
.acp-edge {
  fill: none; stroke: color-mix(in srgb, var(--text-muted) 50%, transparent);
  stroke-width: 1.6;
}
.acp-edge.completed { stroke: rgba(48, 209, 88, .55); }
.acp-edge.failed { stroke: rgba(255, 69, 58, .55); }
.acp-edge.running { stroke: #e6a23c; stroke-dasharray: 4 4; }
.acp-node { cursor: pointer; }
.acp-node rect {
  fill: color-mix(in srgb, var(--surface, #fff) 6%, transparent);
  stroke: var(--border-color); stroke-width: 1.2;
  transition: stroke .18s ease, fill .18s ease;
}
.acp-node:hover rect { stroke: color-mix(in srgb, var(--brand) 55%, transparent); }
.acp-node.selected rect { stroke: var(--brand); stroke-width: 2; }
.acp-node.running rect { stroke: #e6a23c; fill: rgba(230, 162, 60, .1); }
.acp-node.completed rect { stroke: rgba(48, 209, 88, .55); fill: rgba(48, 209, 88, .06); }
.acp-node.failed rect { stroke: rgba(255, 69, 58, .65); fill: rgba(255, 69, 58, .08); }
.acp-node.skipped rect { opacity: .55; }
.acp-node-dot { fill: var(--text-muted); }
.acp-node.running .acp-node-dot { fill: #e6a23c; }
.acp-node.completed .acp-node-dot { fill: #30d158; }
.acp-node.failed .acp-node-dot { fill: #ff453a; }
.acp-node-key { fill: var(--text-primary); font-size: 12px; font-weight: 700; }
.acp-node-agent { fill: var(--text-muted); font-size: 10.5px; }

.acp-detail {
  min-width: 0; max-height: 420px; overflow-y: auto;
  border: 1px solid var(--border-color); border-radius: 13px;
  padding: 11px 12px;
  background: color-mix(in srgb, var(--surface, #fff) 3%, transparent);
}
.acp-detail-head { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; }
.acp-detail-head b { font-size: 13px; }
.acp-detail-agent { font-size: 10.5px; color: var(--text-muted); }
.acp-detail-key {
  font-size: 10px; color: var(--text-muted); font-family: ui-monospace, monospace;
  background: rgba(128, 128, 128, .1); border-radius: 6px; padding: 1px 6px;
}
.acp-detail-status {
  margin-left: auto; padding: 2px 7px; border-radius: 999px;
  font-size: 10px; background: color-mix(in srgb, var(--brand) 10%, transparent);
  color: var(--text-muted);
}
.acp-detail-status.running { color: #e6a23c; }
.acp-detail-status.completed { color: #30d158; }
.acp-detail-status.failed { color: #ff6b61; }
.acp-detail-summary { margin: 8px 0 0; font-size: 11.5px; line-height: 1.6; color: var(--text-secondary); }
.acp-detail-error { margin: 8px 0 0; font-size: 11px; line-height: 1.55; color: #ff6b61; }
.acp-kv { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 7px; font-size: 10px; color: var(--text-muted); }
.acp-json { margin-top: 8px; }
.acp-json summary { cursor: pointer; font-size: 10.5px; color: var(--text-muted); }
.acp-json pre {
  margin: 5px 0 0; padding: 7px 8px; border-radius: 7px;
  background: rgba(128, 128, 128, .09);
  font-size: 10px; line-height: 1.5; white-space: pre-wrap; word-break: break-word;
  max-height: 220px; overflow-y: auto;
}
.acp-run-error, .acp-run-out {
  margin-top: 12px; padding: 8px 9px; border-radius: 9px;
  background: color-mix(in srgb, var(--brand) 6%, transparent);
  font-size: 11px;
}
.acp-run-error { background: rgba(255, 69, 58, .08); }
.acp-run-error b, .acp-run-out b { display: block; margin-bottom: 4px; }
.acp-run-error p, .acp-run-out p { margin: 0; line-height: 1.6; color: var(--text-secondary); }
.acp-muted { font-size: 11px; color: var(--text-muted); }

.acp-msgs { margin-top: 12px; }
.acp-msgs-head { display: flex; align-items: baseline; gap: 10px; }
.acp-msgs-head h3 { margin: 0 0 6px; font-size: 12px; }
.acp-msg-list { max-height: 180px; overflow-y: auto; }
.acp-msg {
  padding: 6px 8px; border-radius: 8px; border: 1px solid var(--border-color);
  font-size: 10.5px;
}
.acp-msg + .acp-msg { margin-top: 4px; }
.acp-msg-from { font-weight: 700; color: var(--brand-bright); }
.acp-msg-arrow { margin: 0 4px; color: var(--text-muted); }
.acp-msg-to { color: var(--text-secondary); }
.acp-msg-kind {
  margin-left: 6px; padding: 1px 5px; border-radius: 5px;
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  color: var(--text-muted); font-size: 9.5px;
}
.acp-msg-text { margin: 3px 0 0; line-height: 1.55; color: var(--text-secondary); }

.acp-foot { display: flex; align-items: center; gap: 9px; margin-top: 14px; }
.acp-foot .acp-muted { margin-right: auto; }
.acp-primary {
  padding: 8px 15px; border-radius: 9px;
  border: 1px solid color-mix(in srgb, var(--brand) 50%, transparent);
  background: color-mix(in srgb, var(--brand) 16%, transparent);
  color: var(--text-primary); font-family: inherit; font-size: 12px; font-weight: 700;
  cursor: pointer;
}
.acp-primary:hover { background: color-mix(in srgb, var(--brand) 24%, transparent); }
.acp-ghost {
  padding: 8px 12px; border-radius: 9px;
  border: 1px solid var(--border-color); background: transparent;
  color: var(--text-secondary); font-family: inherit; font-size: 12px; cursor: pointer;
}
.acp-ghost:hover { color: var(--text-primary); }

.acp-fade-enter-active, .acp-fade-leave-active { transition: opacity .18s ease; }
.acp-fade-enter-from, .acp-fade-leave-to { opacity: 0; }
[data-theme="light"] .acp-mask { background: rgba(15, 23, 42, .35); }

@media (max-width: 900px) {
  .acp-body { grid-template-columns: 1fr; }
  .acp-detail { max-height: none; }
}
@media (max-width: 560px) {
  .acp-mask { padding: 8px; }
  .acp-panel { padding: 14px 12px; max-height: 95vh; }
  .acp-title { font-size: 16px; }
}
@media (prefers-reduced-motion: reduce) {
  .acp-live.on, .acp-spinner { animation: none; }
  .acp-fade-enter-active, .acp-fade-leave-active { transition: none; }
}
</style>
