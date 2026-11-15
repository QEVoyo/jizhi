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
      <span v-if="metrics.active" class="m-chip">进行中 <b>{{ metrics.active }}</b></span>
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
        <div v-if="w.key === 'tuning_debate'" class="wf-nodes">
          <span class="wf-node">取证</span>
          <span class="wf-arrow">→</span>
          <span class="wf-node wf-node-fan">四路并行</span>
          <span class="wf-arrow">→</span>
          <span class="wf-node">主控裁决</span>
        </div>
        <div v-else class="wf-nodes">
          <template v-for="(n, i) in w.nodes" :key="n.key">
            <span class="wf-node" :class="nodeClass(w.key, n.key)">{{ nodeLabel(n.key) }}</span>
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
        <button
          v-if="w.key === 'question_gen' || w.key === 'question_gen_quick'"
          class="wf-run wf-real"
          :disabled="running"
          @click="startRealRun(w)"
        >
          {{ w.key === 'question_gen_quick' ? '真实快速出题' : '真实团队出题' }}
        </button>
        <button
          v-if="businessLink(w)"
          class="wf-run wf-real"
          @click="openResult(businessLink(w).to)"
        >
          {{ businessLink(w).label }}
        </button>
        <button
          v-if="w.key === 'tuning_debate'"
          class="wf-run wf-room"
          @click="openDebateRoom"
        >
          打开真实圆桌
        </button>
      </article>
    </div>

    <!-- 实时轨迹 -->
    <div v-if="run" class="wf-live">
      <div class="live-head">
        <span class="live-title">{{ run.run.title || ('运行 ' + shortId(run.run.run_id || run.run.id)) }}</span>
        <span class="live-status" :class="run.run.status">{{ statusText(run.run.status) }}</span>
        <span v-if="run.run.progress != null" class="live-meta">{{ run.run.progress }}%</span>
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
      <p v-if="run.run.error" class="live-error">{{ run.run.error }}</p>
      <p v-if="run.run.output?.message" class="live-final">{{ run.run.output.message }}</p>
      <p v-if="run.run.status === 'completed' && run.run.output?.set_id" class="live-final">
        已加入资源库「我的题集」，刷新资源库即可看到。
      </p>
      <div v-if="run.run.link" class="live-actions">
        <button class="primary" @click="openResult(run.run.link)">{{ resultLabel }}</button>
        <button v-if="run.run.output?.set_id" class="ghost" @click="openResult('/resource-lib')">
          去资源库
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getWorkflows, createRun, getRun, getRunMetrics } from '@/api/agents'
import { openAgentPanel } from '@/stores/agentPanel'

const props = defineProps({
  userId: { type: String, default: '' },
  focusRunId: { type: String, default: '' },
})

const router = useRouter()
const workflows = ref([])
const metrics = ref(null)
const running = ref(false)
const run = ref(null)
let timer = null
let pollToken = 0

const messages = computed(() => (run.value?.messages || []).slice(-12))
const resultLabel = computed(() => {
  const link = String(run.value?.run?.link || '')
  return link.includes('/set-detail') ? '打开题集' : '查看结果'
})

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
// 任务页点击某条 run 时，复用这里的轨迹视图（不再造第二套详情页）。
// 历史任务打开时不再重复弹「任务完成」——只在本次亲眼看到它从未结束变成结束时才弹。
watch(() => props.focusRunId, (id) => {
  if (id && props.userId) poll(id, { label: '任务', notify: false })
})
onBeforeUnmount(() => {
  pollToken += 1
  if (timer) clearInterval(timer)
  timer = null
})

function openDebateRoom() {
  window.dispatchEvent(new CustomEvent('open-debate-room'))
}

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
    openAgentPanel(created.run_id)
    poll(created.run_id)
  } catch (e) {
    running.value = false
    ElMessage.error(e?.response?.data?.detail || '试跑失败（先执行 agent_orchestration.sql）')
  }
}

async function startRealRun(w) {
  if (!props.userId || running.value) return
  const quick = w.key === 'question_gen_quick'
  const count = quick ? 2 : 3
  const label = quick ? '快速出题' : '团队出题'
  let topic = ''
  try {
    const res = await ElMessageBox.prompt(
      `输入要出的知识点。会真实调用模型、写入题库并生成资源库题集，预计 ${quick ? '2–4' : '5–8'} 次调用。`,
      quick ? '真实快速出题' : '真实团队出题',
      {
        inputValue: '函数单调性',
        confirmButtonText: '下一步',
        cancelButtonText: '取消',
        inputPattern: /\S+/,
        inputErrorMessage: '请输入知识点',
      },
    )
    topic = String(res.value || '').trim()
  } catch { return }
  if (!topic) return
  try {
    await ElMessageBox.confirm(
      (quick
        ? `快速模式：跳过规划与检索，围绕「${topic}」出 ${count} 道选择题。`
        : `围绕「${topic}」出 ${count} 道选择题，团队会规划、检索、校验并修复。`)
      + '会真实调用模型、写入题库并生成资源库题集，确定开始？',
      '确认真实运行',
      { type: 'warning', confirmButtonText: '开始', cancelButtonText: '取消' },
    )
  } catch { return }

  running.value = true
  run.value = null
  try {
    const created = await createRun({
      workflow_key: w.key,
      mode: quick ? 'quick' : 'auto',
      input: {
        topic,
        count,
        question_type: '选择题',
        difficulty: '中等',
        // 智能体中心出的题也要能在资源库找到：
        // run 收尾时后端把这些题打包成题集，并写 output.set_id / run.link。
        create_set: true,
        set_name: `${label} · ${topic}`,
        set_description: `智能体中心 · ${w.name} · ${count} 道`,
      },
    }, props.userId)
    openAgentPanel(created.run_id)
    poll(created.run_id, { label })
  } catch (e) {
    running.value = false
    ElMessage.error(e?.response?.data?.detail || '启动失败（先执行 agent_orchestration.sql）')
  }
}

function stopPoll(token) {
  if (token !== pollToken) return
  pollToken += 1
  if (timer) clearInterval(timer)
  timer = null
}

function poll(runId, { label = 'dry-run', notify = true } = {}) {
  if (timer) clearInterval(timer)
  timer = null
  const token = ++pollToken
  let sawActive = false

  const tick = async () => {
    if (token !== pollToken) return
    try {
      const bundle = await getRun(runId, props.userId)
      if (token !== pollToken) return
      run.value = bundle
      const status = bundle?.run?.status
      if (!['completed', 'failed', 'cancelled'].includes(status)) sawActive = true
      if (['completed', 'failed', 'cancelled'].includes(status)) {
        stopPoll(token)
        running.value = false
        loadMetrics()
        if (notify && sawActive) {
          if (status === 'completed') ElMessage.success(`${label}完成`)
          else if (status === 'failed') {
            ElMessage.error(bundle.run.error || `${label}失败`)
          }
        }
      }
    } catch (e) {
      if (token !== pollToken) return
      stopPoll(token)
      running.value = false
      ElMessage.error('读取运行状态失败')
    }
  }
  tick()
  timer = setInterval(tick, 1000)
}

function openResult(link) {
  if (link) router.push(link)
}

// 这些工作流的真实入口在业务页，不在智能体中心重复造一套表单。
// 给一个明确的业务页按钮，避免「只有 dry-run，找不到真入口」。
const BUSINESS_LINKS = {
  exam_analysis: { to: '/subject-plan', label: '去真题卷交卷' },
  exam_gen: { to: '/subject-plan', label: '去考纲页 AI 出卷' },
  exam_video: { to: '/subject-plan', label: '交卷后生成讲评' },
}

function businessLink(w) {
  return BUSINESS_LINKS[w.key] || null
}

const NODE_LABELS = {
  plan: '规划',
  retrieve: '检索',
  generate: '生成',
  verify: '校验',
  verify_semantic: '语义复核',
  repair: '修复',
  verify_retry: '复检',
  persist: '落库',
  aggregate: '汇总',
  parse: '解析',
  evaluate: '评估',
  evidence: '取证',
  data: '数据',
  judge: '裁决',
  xiaoji: '小基',
}

function nodeLabel(key) {
  return NODE_LABELS[key] || key
}

function nodeClass(wfKey, nodeKey) {
  if (!run.value || run.value.run?.workflow_key !== wfKey) return ''
  const s = (run.value.steps || []).find(x => x.node_key === nodeKey)
  return s ? s.status : ''
}

function statusText(s) {
  return {
    queued: '排队中', paused: '已暂停', running: '运行中',
    awaiting_confirm: '待确认', confirmed: '已确认',
    completed: '已完成', failed: '失败', cancelled: '已取消',
  }[s] || s
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
.wf-node-fan { color: #d48806; background: rgba(250, 178, 25, .12); }
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
.wf-room {
  margin-top: 6px;
  border-color: color-mix(in srgb, #f2c94c 46%, transparent);
  background: color-mix(in srgb, #f2c94c 12%, transparent);
}
.wf-room:hover { background: color-mix(in srgb, #f2c94c 22%, transparent); }
.wf-real {
  margin-top: 6px;
  border-color: color-mix(in srgb, #30d158 44%, transparent);
  background: color-mix(in srgb, #30d158 11%, transparent);
}
.wf-real:hover { background: color-mix(in srgb, #30d158 20%, transparent); }

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
.live-error {
  margin-top: 10px; font-size: 12.5px; color: #f56c6c; line-height: 1.55;
  background: rgba(245, 108, 108, .08); border-radius: 10px; padding: 8px 12px;
}
.live-actions { margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; }
.live-actions button {
  font-size: 12px; font-family: inherit; cursor: pointer; font-weight: 600;
  padding: 6px 14px; border-radius: 8px; color: var(--brand-bright);
  border: 1px solid color-mix(in srgb, var(--brand) 40%, transparent);
  background: color-mix(in srgb, var(--brand) 13%, transparent);
}
</style>
