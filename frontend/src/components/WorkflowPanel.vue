<template>
  <section class="wf-card">
    <div class="card-head">
      <h2 class="card-title">工作流编排</h2>
      <span class="card-head-note">Agent 团队 · DAG · 校验 · 轨迹</span>
    </div>
    <p class="card-desc">
      三条模板共用同一个执行器：依赖完成即启动，不等整层；每步都写轨迹与 A2A 消息。
      下面可以用 dry-run 跑一遍，不花钱、不写题。
    </p>

    <!-- 运行指标 -->
    <div v-if="metrics" class="metric-row">
      <span class="m-chip">近 {{ metrics.days }} 天 run <b>{{ metrics.total }}</b></span>
      <span class="m-chip">成功率 <b>{{ metrics.success_rate == null ? '—' : metrics.success_rate + '%' }}</b></span>
      <span class="m-chip">P95 <b>{{ metrics.p95_latency_ms == null ? '—' : metrics.p95_latency_ms + 'ms' }}</b></span>
      <span class="m-chip">成本 <b>¥{{ metrics.cost }}</b></span>
    </div>

    <!-- 工作流卡片 -->
    <div class="wf-grid">
      <article v-for="w in workflows" :key="w.key" class="wf-item" :class="{ planned: w.status !== 'ready' }">
        <header class="wf-head">
          <div>
            <h3 class="wf-name">{{ w.name }}</h3>
            <span class="wf-key">{{ w.key }}</span>
          </div>
          <span class="wf-status" :class="w.status">{{ w.status === 'ready' ? '可运行' : '规划中' }}</span>
        </header>
        <p class="wf-desc">{{ w.description }}</p>
        <div class="wf-nodes">
          <template v-for="(n, i) in w.nodes" :key="n.key">
            <span class="wf-node" :class="nodeClass(w.key, n.key)">{{ n.key }}</span>
            <span v-if="i < w.nodes.length - 1" class="wf-arrow">→</span>
          </template>
        </div>
        <button
          v-if="w.status === 'ready'"
          class="wf-run"
          :disabled="running"
          @click="startDryRun(w)"
        >
          {{ running ? '运行中…' : 'dry-run 跑一遍' }}
        </button>
      </article>
    </div>

    <!-- 实时轨迹 -->
    <div v-if="run" class="wf-live">
      <div class="live-head">
        <span class="live-title">运行 {{ shortId(run.run.run_id || run.run.id) }}</span>
        <span class="live-status" :class="run.run.status">{{ statusText(run.run.status) }}</span>
        <span v-if="run.run.latency_ms" class="live-meta">{{ run.run.latency_ms }}ms</span>
      </div>
      <div class="live-steps">
        <div v-for="s in run.steps" :key="s.id" class="live-step" :class="s.status">
          <span class="dot"></span>
          <span class="s-key">{{ s.node_key }}</span>
          <span class="s-agent">{{ s.agent_key }}</span>
          <span class="s-status">{{ s.status }}</span>
        </div>
        <p v-if="!run.steps.length" class="live-empty">等待节点启动…</p>
      </div>
      <div v-if="messages.length" class="live-msgs">
        <div v-for="m in messages" :key="m.id || m.seq" class="live-msg">
          <b>{{ m.from_agent }}</b>
          <span class="msg-kind">{{ m.kind }}</span>
          <span class="msg-text">{{ m.content }}</span>
        </div>
      </div>
      <p v-if="run.run.output?.message" class="live-final">{{ run.run.output.message }}</p>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getWorkflows, createRun, getRun, getRunMetrics } from '@/api/agents'

const props = defineProps({ userId: { type: String, default: '' } })

const workflows = ref([])
const metrics = ref(null)
const running = ref(false)
const run = ref(null)
let timer = null

const messages = computed(() => (run.value?.messages || []).slice(-12))

async function load() {
  try {
    workflows.value = await getWorkflows()
  } catch (e) {
    console.error('[workflow] workflows:', e)
  }
  await loadMetrics()
}

async function loadMetrics() {
  if (!props.userId) return
  try {
    metrics.value = await getRunMetrics(props.userId)
  } catch (e) {
    metrics.value = null
  }
}

onMounted(load)
watch(() => props.userId, (v) => { if (v) loadMetrics() })
onBeforeUnmount(() => { if (timer) clearInterval(timer) })

async function startDryRun(w) {
  if (!props.userId || running.value) return
  running.value = true
  run.value = null
  try {
    const created = await createRun({
      workflow_key: w.key,
      mode: 'auto',
      input: { topic: '函数单调性', count: 3, dry_run: true },
    }, props.userId)
    poll(created.run_id)
  } catch (e) {
    running.value = false
    ElMessage.error(e?.response?.data?.detail || '试跑失败（先执行 agent_orchestration.sql）')
  }
}

function poll(runId) {
  if (timer) clearInterval(timer)
  const tick = async () => {
    try {
      const bundle = await getRun(runId, props.userId)
      run.value = bundle
      if (['completed', 'failed', 'cancelled'].includes(bundle?.run?.status)) {
        clearInterval(timer)
        timer = null
        running.value = false
        loadMetrics()
        if (bundle.run.status === 'completed') ElMessage.success('dry-run 完成')
        else ElMessage.error(bundle.run.error || '运行失败')
      }
    } catch (e) {
      clearInterval(timer)
      timer = null
      running.value = false
      ElMessage.error('读取运行状态失败')
    }
  }
  tick()
  timer = setInterval(tick, 1000)
}

function nodeClass(wfKey, nodeKey) {
  if (!run.value || run.value.run?.workflow_key !== wfKey) return ''
  const s = (run.value.steps || []).find(x => x.node_key === nodeKey)
  return s ? s.status : ''
}

function statusText(s) {
  return { queued: '排队中', running: '运行中', completed: '已完成', failed: '失败', cancelled: '已取消' }[s] || s
}

function shortId(id) {
  return id ? String(id).slice(0, 8) : '—'
}
</script>

<style scoped>
.wf-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255, 255, 255, .06);
  border-radius: 16px;
  padding: 20px 22px;
  backdrop-filter: blur(20px);
  margin-bottom: 18px;
}
[data-theme="dark"] .wf-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
}
.card-head { display: flex; align-items: center; justify-content: space-between; }
.card-title { font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 0; }
.card-head-note { font-size: 11px; color: var(--text-muted); }
.card-desc { font-size: 12px; color: var(--text-muted); margin: 6px 0 14px; line-height: 1.6; }

.metric-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }
.m-chip {
  font-size: 11.5px; color: var(--text-secondary);
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  border: 1px solid rgba(255, 255, 255, .06);
  padding: 4px 10px; border-radius: 10px;
}
.m-chip b { color: var(--text-primary); font-variant-numeric: tabular-nums; }

.wf-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
.wf-item {
  border: 1px solid rgba(255, 255, 255, .06);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border-radius: 14px; padding: 14px 16px;
}
.wf-item.planned { opacity: .62; }
.wf-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
.wf-name { font-size: 14px; font-weight: 700; color: var(--text-primary); margin: 0; }
.wf-key { font-size: 11px; color: var(--text-muted); font-family: ui-monospace, monospace; }
.wf-status { font-size: 11px; padding: 2px 8px; border-radius: 10px; }
.wf-status.ready { color: #0ca30c; background: rgba(12, 163, 12, .10); }
.wf-status.planned { color: var(--text-muted); background: rgba(128, 128, 128, .12); }
.wf-desc { font-size: 12px; color: var(--text-muted); margin: 8px 0 10px; line-height: 1.55; }
.wf-nodes { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.wf-node {
  font-size: 11px; padding: 2px 8px; border-radius: 8px;
  color: var(--text-secondary); background: rgba(128, 128, 128, .10);
}
.wf-node.running { color: #d48806; background: rgba(250, 178, 25, .14); }
.wf-node.completed { color: #0ca30c; background: rgba(12, 163, 12, .12); }
.wf-node.failed { color: #f56c6c; background: rgba(245, 108, 108, .12); }
.wf-arrow { font-size: 11px; color: var(--text-muted); }
.wf-run {
  margin-top: 12px; padding: 6px 14px; border-radius: 8px; font-size: 12px;
  cursor: pointer; font-family: inherit; font-weight: 600;
  border: 1px solid color-mix(in srgb, var(--brand) 40%, transparent);
  background: color-mix(in srgb, var(--brand) 15%, transparent);
  color: var(--brand-bright); transition: all .2s ease;
}
.wf-run:hover:not(:disabled) { background: color-mix(in srgb, var(--brand) 25%, transparent); }
.wf-run:disabled { opacity: .5; cursor: not-allowed; }

.wf-live {
  margin-top: 14px; border-top: 1px solid rgba(255, 255, 255, .07);
  padding-top: 12px;
}
.live-head { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.live-title { font-size: 13px; font-weight: 600; color: var(--text-primary); font-family: ui-monospace, monospace; }
.live-status { font-size: 11px; padding: 2px 8px; border-radius: 10px; background: rgba(128, 128, 128, .12); color: var(--text-secondary); }
.live-status.running { color: #d48806; background: rgba(250, 178, 25, .14); }
.live-status.completed { color: #0ca30c; background: rgba(12, 163, 12, .12); }
.live-status.failed { color: #f56c6c; background: rgba(245, 108, 108, .12); }
.live-meta { font-size: 11px; color: var(--text-muted); }
.live-steps { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; }
.live-step { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-secondary); }
.live-step .dot { width: 7px; height: 7px; border-radius: 50%; background: rgba(128, 128, 128, .4); }
.live-step.running .dot { background: #d48806; box-shadow: 0 0 0 3px rgba(250, 178, 25, .18); }
.live-step.completed .dot { background: #0ca30c; }
.live-step.failed .dot { background: #f56c6c; }
.s-key { width: 80px; font-family: ui-monospace, monospace; color: var(--text-primary); }
.s-agent { width: 90px; color: var(--text-muted); }
.s-status { color: var(--text-muted); }
.live-empty { font-size: 12px; color: var(--text-muted); }
.live-msgs { margin-top: 10px; display: flex; flex-direction: column; gap: 5px; }
.live-msg { font-size: 12px; color: var(--text-secondary); line-height: 1.55; }
.live-msg b { color: var(--text-primary); margin-right: 6px; }
.msg-kind {
  font-size: 10px; color: var(--text-muted); background: rgba(128, 128, 128, .1);
  padding: 1px 6px; border-radius: 6px; margin-right: 6px;
}
.msg-text { color: var(--text-secondary); }
.live-final {
  margin-top: 10px; font-size: 13px; color: var(--text-primary);
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  border-radius: 10px; padding: 8px 12px;
}
</style>
