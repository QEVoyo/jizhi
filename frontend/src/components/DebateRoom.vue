<template>
  <Teleport to="body">
    <Transition name="dr-fade">
      <div v-if="open" class="dr-mask" @click.self="close">
        <section class="dr-panel" role="dialog" aria-modal="true" aria-label="调参圆桌">
          <header class="dr-head">
            <div class="dr-title-wrap">
              <span class="dr-live" :class="{ on: isActive }" aria-hidden="true"></span>
              <div>
                <h2 class="dr-title">调参圆桌</h2>
                <p class="dr-sub">四个 Agent 会诊 · 主控裁决 · 每句都有证据</p>
              </div>
            </div>
            <div class="dr-head-right">
              <span v-if="run" class="dr-status" :class="run.status">{{ statusText(run.status) }}</span>
              <button class="dr-x" title="收起" @click="close">×</button>
            </div>
          </header>

          <p class="dr-desc">
            通常在信号矛盾或高风险时开，也可以手动复诊。四个角色先各说一段，
            主控再裁决；参数变更受范围、幅度、冷却期和用户锁定约束，
            越界的建议会原样列出。
          </p>

          <p v-if="error" class="dr-error">{{ error }}</p>

          <div v-if="!run" class="dr-empty">
            <div class="dr-empty-icon">◎</div>
            <p>还没有圆桌记录。开一场，让数据、规划、评估、小基四个视角看这次该不该调参。</p>
            <button class="dr-primary" :disabled="starting" @click="start">
              {{ starting ? '正在召集…' : '开一场圆桌' }}
            </button>
          </div>

          <template v-else>
            <div class="dr-agents">
              <article
                v-for="a in agentCards"
                :key="a.key"
                class="dr-agent"
                :class="[a.tone, a.status]"
              >
                <header class="dr-agent-head">
                  <span class="dr-avatar">{{ a.icon }}</span>
                  <div class="dr-agent-id">
                    <b>{{ a.name }}</b>
                    <em>{{ a.focus }}</em>
                  </div>
                  <span class="dr-dot" :class="a.status"></span>
                </header>

                <p v-if="a.status === 'running'" class="dr-thinking">正在从自己的视角看数据…</p>
                <p v-else-if="a.status === 'pending'" class="dr-muted">等待前面的步骤…</p>
                <p v-else-if="a.status === 'failed'" class="dr-agent-error">这一步没跑通：{{ a.error || '未知原因' }}</p>
                <template v-else-if="a.out">
                  <p class="dr-stance">{{ a.out.stance || '已发言' }}</p>
                  <ul v-if="a.out.points?.length" class="dr-points">
                    <li v-for="(p, i) in a.out.points" :key="i">{{ p }}</li>
                  </ul>
                  <div v-if="a.out.evidence_used?.length" class="dr-chips">
                    <span v-for="(e, i) in a.out.evidence_used" :key="i" class="dr-chip">{{ e }}</span>
                  </div>
                  <div v-if="a.out.confidence != null" class="dr-conf">
                    置信度 {{ pct(a.out.confidence) }}
                  </div>
                </template>
              </article>
            </div>

            <article class="dr-judge" :class="judgeStatus">
              <header class="dr-judge-head">
                <span class="dr-avatar judge">⚖</span>
                <div class="dr-agent-id">
                  <b>主控 Judge</b>
                  <em>权衡 · 边界 · 最终裁决</em>
                </div>
                <span class="dr-dot" :class="judgeStatus"></span>
              </header>

              <p v-if="run.status === 'queued'" class="dr-thinking">排队中，前面还有任务…</p>
              <p v-else-if="judgeStatus === 'running' || judgeStatus === 'pending'" class="dr-thinking">
                {{ judgeStatus === 'running' ? '四票已到齐，正在裁决…' : '等四票发言…' }}
              </p>
              <p v-else-if="judgeStatus === 'failed'" class="dr-agent-error">
                裁决失败：{{ judgeStep?.output?.error || run.error || '未知原因' }}
              </p>
              <p v-else-if="run.status === 'failed'" class="dr-agent-error">
                圆桌没跑完：{{ run.error || '未知原因' }}
              </p>
              <template v-else-if="judgeOut">
                <p class="dr-diagnosis">{{ judgeOut.diagnosis || '本轮没有形成诊断。' }}</p>

                <div v-if="changes.length" class="dr-block">
                  <span class="dr-label">已应用</span>
                  <div v-for="(c, i) in changes" :key="`c-${i}`" class="dr-change">
                    <b>{{ c.agent_key }}.{{ c.param_key }}</b>
                    <span>{{ fmt(c.old_value) }} → {{ fmt(c.new_value) }}</span>
                    <em v-if="c.reason">{{ c.reason }}</em>
                  </div>
                </div>

                <div v-if="skipped.length" class="dr-block">
                  <span class="dr-label">未应用（受边界约束）</span>
                  <div v-for="(s, i) in skipped" :key="`s-${i}`" class="dr-skip">
                    <b>{{ s.agent_key }}.{{ s.param_key }}</b>
                    <span>{{ s.reason }}</span>
                  </div>
                </div>

                <div v-if="judgeOut.rejected?.length" class="dr-block">
                  <span class="dr-label">被否决的方案</span>
                  <ul class="dr-rejected">
                    <li v-for="(r, i) in judgeOut.rejected" :key="`r-${i}`">{{ r }}</li>
                  </ul>
                </div>

                <p v-if="judgeOut.diary" class="dr-diary">{{ judgeOut.diary }}</p>

                <div class="dr-judge-foot">
                  <span v-if="judgeOut.confidence != null">置信度 {{ pct(judgeOut.confidence) }}</span>
                  <span v-if="judgeOut.decision_id" class="dr-muted">决策已记入调参日记</span>
                  <span v-else class="dr-muted">本轮没有可应用的变更</span>
                </div>
              </template>
            </article>

            <div v-if="messages.length" class="dr-msgs">
              <h3 class="dr-msgs-title">消息流</h3>
              <div class="dr-msg-list">
                <div v-for="m in messages" :key="m.id || m.seq" class="dr-msg">
                  <span class="dr-msg-from">{{ roleName(m.from_agent) }}</span>
                  <span class="dr-msg-arrow">→</span>
                  <span class="dr-msg-to">{{ roleName(m.to_agent) }}</span>
                  <span class="dr-msg-kind">{{ kindText(m.kind) }}</span>
                  <p class="dr-msg-text">{{ m.content }}</p>
                </div>
              </div>
            </div>

            <footer class="dr-foot">
              <button class="dr-primary" :disabled="starting || isActive" @click="start">
                {{ isActive ? '圆桌进行中…' : '再开一场' }}
              </button>
              <button class="dr-ghost" @click="close">收起</button>
              <span v-if="run.llm_calls != null" class="dr-muted dr-latency">
                {{ run.llm_calls }} 次调用<template v-if="run.cost"> · ¥{{ Number(run.cost).toFixed(3) }}</template>
                <template v-if="run.latency_ms"> · {{ (run.latency_ms / 1000).toFixed(1) }}s</template>
              </span>
            </footer>
          </template>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { getRun, listRuns, startDebate } from '@/api/agents'

const props = defineProps({
  open: { type: Boolean, default: false },
  userId: { type: String, default: '' },
})
const emit = defineEmits(['update:open'])

const bundle = ref(null)
const runId = ref('')
const starting = ref(false)
const error = ref('')
let timer = null
let token = 0

const run = computed(() => bundle.value?.run || null)
const steps = computed(() => bundle.value?.steps || [])
const messages = computed(() =>
  (bundle.value?.messages || []).slice().sort((a, b) => (a.seq || 0) - (b.seq || 0)))
const isActive = computed(() =>
  !!run.value && !['completed', 'failed', 'cancelled'].includes(run.value.status))
const stepsByKey = computed(() =>
  Object.fromEntries(steps.value.map(s => [s.node_key, s])))

const AGENT_META = [
  { key: 'data', name: '数据 Agent', tone: 'blue', icon: '▦', focus: '事实与趋势' },
  { key: 'plan', name: '规划 Agent', tone: 'amber', icon: '◈', focus: '任务量与节奏' },
  { key: 'evaluate', name: '评估 Agent', tone: 'purple', icon: '◎', focus: '目标与标准' },
  { key: 'xiaoji', name: '小基 Agent', tone: 'green', icon: '☺', focus: '感受与沟通' },
]

const agentCards = computed(() => AGENT_META.map(a => {
  const step = stepsByKey.value[a.key]
  const out = step?.output || null
  return {
    ...a,
    status: step?.status || 'pending',
    out,
    error: out?.error || '',
  }
}))

const judgeStep = computed(() => stepsByKey.value.judge)
const judgeOut = computed(() => {
  const ro = run.value?.output
  if (ro && typeof ro === 'object' && Object.keys(ro).length) return ro
  return judgeStep.value?.output || null
})
const judgeStatus = computed(() =>
  judgeStep.value?.status || (isActive.value ? 'pending' : 'skipped'))
const changes = computed(() => judgeOut.value?.applied || [])
const skipped = computed(() => judgeOut.value?.skipped || [])

const STATUS_TEXT = {
  queued: '排队中', running: '进行中', paused: '已暂停',
  completed: '已结束', failed: '失败', cancelled: '已取消',
}
function statusText(s) { return STATUS_TEXT[s] || s || '' }
const KIND_TEXT = {
  proposal: '提议', critique: '质疑', verdict: '裁决', result: '汇总', task: '任务',
}
function kindText(k) { return KIND_TEXT[k] || k || '' }
const ROLE_TEXT = {
  debate_context: '证据', debate_data: '数据', debate_plan: '规划',
  debate_eval: '评估', debate_xiaoji: '小基', debate_judge: '主控',
  conductor: '队长',
}
function roleName(k) { return ROLE_TEXT[k] || k || '' }
function pct(v) {
  const n = Number(v)
  return Number.isFinite(n) ? `${Math.round(n * 100)}%` : '—'
}
function fmt(v) {
  if (v === true) return '开'
  if (v === false) return '关'
  if (v === null || v === undefined) return '—'
  return String(v)
}

function stop() {
  token += 1
  if (timer) clearTimeout(timer)
  timer = null
}

async function fetchOnce() {
  if (!runId.value || !props.userId) return
  const b = await getRun(runId.value, props.userId)
  bundle.value = b
  if (!b?.run || ['completed', 'failed', 'cancelled'].includes(b.run.status)) {
    stop()
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
      error.value = e?.response?.data?.detail || '读取圆桌状态失败'
      stop()
    }
  }
  tick()
}

async function loadLatest() {
  if (!props.userId) return
  error.value = ''
  try {
    const runs = await listRuns(props.userId, 10, { workflowKey: 'tuning_debate' })
    if (runs?.length) {
      runId.value = runs[0].id
      await fetchOnce()
      if (isActive.value) schedule()
    } else {
      runId.value = ''
      bundle.value = null
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || '读取圆桌记录失败'
  }
}

async function start() {
  if (!props.userId || starting.value) return
  starting.value = true
  error.value = ''
  try {
    const res = await startDebate(props.userId)
    runId.value = res.run_id
    await fetchOnce()
    if (isActive.value) schedule()
  } catch (e) {
    error.value = e?.response?.data?.detail || '圆桌没开成，请稍后再试'
  } finally {
    starting.value = false
  }
}

function close() {
  stop()
  emit('update:open', false)
}

watch(() => props.open, (v) => {
  if (v) loadLatest()
  else stop()
})
watch(() => props.userId, () => {
  if (props.open) loadLatest()
})
onBeforeUnmount(stop)
</script>

<style scoped>
.dr-mask {
  position: fixed; inset: 0; z-index: 9600;
  display: grid; place-items: center;
  padding: 20px;
  background: rgba(4, 8, 18, .58);
  backdrop-filter: blur(6px);
}
.dr-panel {
  width: min(1060px, 100%);
  max-height: 90vh;
  overflow-y: auto;
  padding: 20px 22px 18px;
  border-radius: 18px;
  background: var(--surface, #0f172a);
  border: 1px solid color-mix(in srgb, var(--brand) 26%, transparent);
  box-shadow: 0 30px 80px rgba(0, 0, 0, .42);
  color: var(--text-primary);
}
.dr-head { display: flex; align-items: flex-start; gap: 12px; }
.dr-title-wrap { display: flex; align-items: center; gap: 10px; flex: 1; }
.dr-live {
  width: 9px; height: 9px; border-radius: 50%;
  background: var(--text-muted);
}
.dr-live.on {
  background: #30d158;
  box-shadow: 0 0 0 5px color-mix(in srgb, #30d158 22%, transparent);
  animation: dr-pulse 1.6s ease-in-out infinite;
}
@keyframes dr-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .45; }
}
.dr-title { margin: 0; font-size: 19px; letter-spacing: .5px; }
.dr-sub { margin: 3px 0 0; font-size: 11.5px; color: var(--text-muted); }
.dr-head-right { display: flex; align-items: center; gap: 10px; }
.dr-status {
  padding: 3px 9px; border-radius: 999px;
  font-size: 11px; font-weight: 700;
  background: color-mix(in srgb, var(--brand) 14%, transparent);
  color: var(--brand-bright);
}
.dr-status.completed { background: rgba(48, 209, 88, .14); color: #30d158; }
.dr-status.failed { background: rgba(255, 69, 58, .14); color: #ff6b61; }
.dr-x {
  width: 28px; height: 28px; border-radius: 8px;
  border: 1px solid var(--border-color); background: transparent;
  color: var(--text-muted); font-size: 16px; cursor: pointer;
}
.dr-x:hover { color: var(--text-primary); border-color: var(--brand); }
.dr-desc {
  margin: 12px 0 14px; padding: 9px 11px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--brand) 6%, transparent);
  border: 1px solid color-mix(in srgb, var(--brand) 16%, transparent);
  font-size: 12px; line-height: 1.65; color: var(--text-secondary);
}
.dr-error {
  margin: 10px 0; padding: 9px 11px; border-radius: 9px;
  border: 1px solid rgba(230, 162, 60, .4);
  background: rgba(230, 162, 60, .1);
  color: #e6a23c; font-size: 12px;
}
.dr-empty {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
  padding: 34px 16px 30px; text-align: center;
  color: var(--text-secondary); font-size: 12.5px; line-height: 1.7;
}
.dr-empty-icon { font-size: 38px; color: var(--brand-bright); opacity: .8; }
.dr-empty p { max-width: 520px; margin: 0; }

.dr-agents {
  display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
.dr-agent {
  --tone: var(--brand);
  position: relative;
  min-height: 152px;
  padding: 11px 11px 10px;
  border-radius: 13px;
  border: 1px solid var(--border-color);
  background: color-mix(in srgb, var(--tone) 5%, transparent);
  transition: border-color .2s ease, box-shadow .2s ease;
}
.dr-agent.blue { --tone: #4f8cff; }
.dr-agent.amber { --tone: #e6a23c; }
.dr-agent.purple { --tone: #a06bff; }
.dr-agent.green { --tone: #30d158; }
.dr-agent.running {
  border-color: color-mix(in srgb, var(--tone) 62%, transparent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--tone) 12%, transparent);
}
.dr-agent.completed { border-color: color-mix(in srgb, var(--tone) 36%, transparent); }
.dr-agent.failed { border-color: rgba(255, 69, 58, .45); }
.dr-agent-head { display: flex; align-items: center; gap: 8px; }
.dr-avatar {
  flex: none; width: 30px; height: 30px; border-radius: 9px;
  display: grid; place-items: center;
  background: color-mix(in srgb, var(--tone, var(--brand)) 16%, transparent);
  color: var(--tone, var(--brand-bright));
  font-size: 15px; font-weight: 700;
}
.dr-avatar.judge { --tone: #f2c94c; }
.dr-agent-id { min-width: 0; flex: 1; }
.dr-agent-id b { display: block; font-size: 12.5px; }
.dr-agent-id em { display: block; margin-top: 1px; font-style: normal; font-size: 10.5px; color: var(--text-muted); }
.dr-dot {
  flex: none; width: 7px; height: 7px; border-radius: 50%;
  background: var(--text-muted); opacity: .5;
}
.dr-dot.running { background: var(--tone, var(--brand)); opacity: 1; animation: dr-pulse 1.4s infinite; }
.dr-dot.completed { background: #30d158; opacity: 1; }
.dr-dot.failed { background: #ff453a; opacity: 1; }
.dr-thinking { margin: 12px 0 0; font-size: 11.5px; color: var(--text-muted); }
.dr-muted { margin: 12px 0 0; font-size: 11px; color: var(--text-muted); }
.dr-stance { margin: 11px 0 5px; font-size: 12px; font-weight: 700; line-height: 1.55; }
.dr-points { margin: 0; padding-left: 15px; font-size: 11px; line-height: 1.6; color: var(--text-secondary); }
.dr-points li + li { margin-top: 3px; }
.dr-chips { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; }
.dr-chip {
  padding: 2px 6px; border-radius: 999px;
  background: color-mix(in srgb, var(--tone, var(--brand)) 10%, transparent);
  color: var(--text-secondary); font-size: 9.5px;
}
.dr-conf { margin-top: 8px; font-size: 10px; color: var(--text-muted); font-variant-numeric: tabular-nums; }
.dr-agent-error { margin: 11px 0 0; font-size: 11px; line-height: 1.55; color: #ff6b61; }

.dr-judge {
  margin-top: 10px; padding: 13px 14px 12px;
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, #f2c94c 34%, transparent);
  background: color-mix(in srgb, #f2c94c 5%, transparent);
}
.dr-judge.running { border-color: color-mix(in srgb, #f2c94c 66%, transparent); }
.dr-judge.failed { border-color: rgba(255, 69, 58, .45); }
.dr-judge-head { display: flex; align-items: center; gap: 8px; }
.dr-diagnosis { margin: 11px 0 8px; font-size: 13px; font-weight: 700; line-height: 1.6; }
.dr-block { margin-top: 9px; }
.dr-label {
  display: block; margin-bottom: 4px;
  font-size: 10px; letter-spacing: .4px; color: var(--text-muted);
}
.dr-change, .dr-skip {
  display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px;
  padding: 5px 8px; border-radius: 8px;
  background: color-mix(in srgb, var(--surface, #fff) 40%, transparent);
  font-size: 11px;
}
.dr-change + .dr-change, .dr-skip + .dr-skip { margin-top: 4px; }
.dr-change b, .dr-skip b { color: var(--brand-bright); }
.dr-change span { font-variant-numeric: tabular-nums; }
.dr-change em { font-style: normal; color: var(--text-muted); }
.dr-skip span { color: #e6a23c; }
.dr-rejected { margin: 0; padding-left: 15px; font-size: 11px; line-height: 1.6; color: var(--text-secondary); }
.dr-diary {
  margin: 10px 0 0; padding: 8px 10px; border-radius: 9px;
  background: color-mix(in srgb, #f2c94c 7%, transparent);
  font-size: 11.5px; line-height: 1.7; color: var(--text-secondary);
  white-space: pre-wrap;
}
.dr-judge-foot { display: flex; gap: 12px; margin-top: 9px; font-size: 10.5px; color: var(--text-muted); }

.dr-msgs { margin-top: 12px; }
.dr-msgs-title { margin: 0 0 6px; font-size: 12px; }
.dr-msg-list { max-height: 170px; overflow-y: auto; }
.dr-msg {
  padding: 6px 8px; border-radius: 8px;
  border: 1px solid var(--border-color);
  font-size: 10.5px;
}
.dr-msg + .dr-msg { margin-top: 4px; }
.dr-msg-from { font-weight: 700; color: var(--brand-bright); }
.dr-msg-arrow { margin: 0 4px; color: var(--text-muted); }
.dr-msg-to { color: var(--text-secondary); }
.dr-msg-kind {
  margin-left: 6px; padding: 1px 5px; border-radius: 5px;
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  color: var(--text-muted); font-size: 9.5px;
}
.dr-msg-text { margin: 3px 0 0; line-height: 1.55; color: var(--text-secondary); }

.dr-foot { display: flex; align-items: center; gap: 9px; margin-top: 14px; }
.dr-primary {
  padding: 8px 15px; border-radius: 9px;
  border: 1px solid color-mix(in srgb, var(--brand) 50%, transparent);
  background: color-mix(in srgb, var(--brand) 16%, transparent);
  color: var(--text-primary); font-family: inherit; font-size: 12px; font-weight: 700;
  cursor: pointer;
}
.dr-primary:hover:not(:disabled) { background: color-mix(in srgb, var(--brand) 24%, transparent); }
.dr-primary:disabled { opacity: .55; cursor: not-allowed; }
.dr-ghost {
  padding: 8px 12px; border-radius: 9px;
  border: 1px solid var(--border-color); background: transparent;
  color: var(--text-secondary); font-family: inherit; font-size: 12px; cursor: pointer;
}
.dr-ghost:hover { color: var(--text-primary); }
.dr-latency { margin-left: auto; }

.dr-fade-enter-active, .dr-fade-leave-active { transition: opacity .18s ease; }
.dr-fade-enter-from, .dr-fade-leave-to { opacity: 0; }

[data-theme="light"] .dr-mask { background: rgba(15, 23, 42, .35); }
[data-theme="light"] .dr-change,
[data-theme="light"] .dr-skip { background: rgba(255, 255, 255, .7); }

@media (max-width: 900px) {
  .dr-agents { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 560px) {
  .dr-mask { padding: 10px; }
  .dr-panel { padding: 16px 14px; max-height: 94vh; }
  .dr-agents { grid-template-columns: 1fr; }
  .dr-title { font-size: 17px; }
}
@media (prefers-reduced-motion: reduce) {
  .dr-live.on, .dr-dot.running { animation: none; }
  .dr-fade-enter-active, .dr-fade-leave-active { transition: none; }
}
</style>
