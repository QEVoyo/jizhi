<template>
  <section class="policy-card">
    <header class="policy-head">
      <div>
        <h2 class="policy-title">编排策略台账</h2>
        <p class="policy-sub">
          快速模式与团队模式不是写死的 if-else：分数来自真实 run 的质检通过率、
          成本与延迟；样本少的策略仍保留探索机会。
        </p>
      </div>
      <span class="policy-total">{{ data.degraded && !data.total_runs ? '台账暂时读不到' : `${data.total_runs || 0} 次策略样本` }}</span>
    </header>

    <p v-if="data.degraded" class="policy-warn">
      台账读取不完整{{ failedLabels }}：数据服务暂时未响应，下面的分数可能不是最新；
      读数恢复后会自动按最新样本重算。
    </p>

    <div class="policy-arms">
      <article
        v-for="a in data.arms || []"
        :key="a.key"
        class="policy-arm"
        :class="[a.key, { chosen: chosenKey === a.key }]"
      >
        <div class="arm-head">
          <div>
            <h3>{{ a.label }}</h3>
            <span class="arm-key">{{ a.workflow_key }}</span>
          </div>
          <span v-if="chosenKey === a.key" class="arm-chosen">上次选择</span>
        </div>
        <div class="arm-score">{{ fmt(a.score) }}</div>
        <div class="arm-bar">
          <span :style="{ width: barWidth(a) }"></span>
        </div>
        <div class="arm-stats">
          <span>运行 <b>{{ a.runs }}</b></span>
          <span>质检通过 <b>{{ pct(a.pass_avg != null ? a.pass_avg : a.success_rate) }}</b></span>
          <span>成本 <b>{{ money(a.cost_avg) }}</b></span>
          <span>延迟 <b>{{ latency(a.latency_avg_ms) }}</b></span>
        </div>
        <p class="arm-desc">{{ a.description }}</p>
      </article>
    </div>

    <div v-if="latest" class="policy-latest">
      <span class="latest-label">上次路由依据</span>
      <b>{{ latestPolicyLabel }}</b>
      <span class="latest-reason">{{ latest.reason }}</span>
    </div>
    <p v-else-if="!data.total_runs && !data.degraded" class="policy-empty">
      还没有策略样本。先跑几次「真实团队出题」，这里会按质检通过率长出分数；
      之后同类小任务会自动比较快速模式与团队模式。
    </p>

    <p class="policy-formula">{{ data.formula }}</p>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { getPolicy } from '@/api/agents'

const props = defineProps({
  userId: { type: String, default: '' },
})

const EMPTY = {
  arms: [], total_runs: 0, latest_routing: null, formula: '',
  degraded: false, failed_arms: [],
}

const data = ref({ ...EMPTY })

async function load() {
  if (!props.userId) return
  try {
    data.value = await getPolicy(props.userId)
  } catch (e) {
    console.error('[policy] load:', e)
    // 读失败不能显示成「0 次样本」——那会把服务不可用说成冷启动
    data.value = { ...EMPTY, degraded: true }
  }
}

const latest = computed(() => data.value.latest_routing || null)
const failedLabels = computed(() => {
  const names = { quick: '快速模式', team: '团队模式' }
  const list = (data.value.failed_arms || []).map(k => names[k] || k)
  return list.length ? `（${list.join('、')}）` : ''
})
const chosenKey = computed(() => {
  const p = latest.value?.policy
  return p === 'quick' || p === 'team' ? p : ''
})
const latestPolicyLabel = computed(() => {
  const p = latest.value?.policy
  if (p === 'quick') return '快速模式'
  if (p === 'team') return '团队模式'
  return '—'
})
const maxScore = computed(() => {
  const scores = (data.value.arms || []).map(a => Number(a.score) || 0)
  return Math.max(0.01, ...scores)
})

function barWidth(a) {
  const s = Number(a.score) || 0
  return `${Math.max(4, Math.min(100, (s / maxScore.value) * 100))}%`
}
function fmt(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n.toFixed(2) : '—'
}
function pct(v) {
  const n = Number(v)
  return Number.isFinite(n) ? `${Math.round(n * 100)}%` : '—'
}
function money(v) {
  const n = Number(v)
  if (!Number.isFinite(n)) return '—'
  // 单次出题成本常在 0.001–0.05 元，两位小数会把差异抹平
  return n > 0 && n < 0.1 ? `¥${n.toFixed(4)}` : `¥${n.toFixed(2)}`
}
function latency(v) {
  const n = Number(v)
  return Number.isFinite(n) ? `${(n / 1000).toFixed(1)}s` : '—'
}

onMounted(load)
watch(() => props.userId, load)
</script>

<style scoped>
.policy-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255, 255, 255, .06);
  border-radius: 16px;
  padding: 20px 22px;
  margin-top: 18px;
}
[data-theme="dark"] .policy-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
}
.policy-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.policy-title { font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 0; }
.policy-sub { font-size: 12px; color: var(--text-muted); margin: 6px 0 0; line-height: 1.6; max-width: 760px; }
.policy-total { font-size: 12px; color: var(--text-muted); white-space: nowrap; }

.policy-warn {
  margin: 10px 0 0;
  font-size: 12px;
  line-height: 1.7;
  color: #d48806;
  background: rgba(250, 178, 25, .1);
  border: 1px solid rgba(250, 178, 25, .28);
  border-radius: 8px;
  padding: 8px 10px;
}

.policy-arms {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 10px; margin-top: 14px;
}
.policy-arm {
  border: 1px solid rgba(255, 255, 255, .06);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border-radius: 14px; padding: 14px 16px;
}
.policy-arm.team { border-color: color-mix(in srgb, var(--brand) 35%, transparent); }
.policy-arm.quick { border-color: rgba(230, 162, 60, .35); }
.policy-arm.chosen { box-shadow: 0 0 0 1px color-mix(in srgb, var(--brand) 45%, transparent); }
.arm-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
.arm-head h3 { font-size: 14px; margin: 0; color: var(--text-primary); }
.arm-key { font-size: 10.5px; color: var(--text-muted); font-family: ui-monospace, monospace; }
.arm-chosen {
  font-size: 10.5px; color: var(--brand-bright);
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  border-radius: 8px; padding: 2px 7px; white-space: nowrap;
}
.arm-score {
  font-size: 30px; font-weight: 800; color: var(--text-primary);
  font-variant-numeric: tabular-nums; line-height: 1.1; margin-top: 8px;
}
.arm-bar { height: 6px; border-radius: 6px; background: rgba(128, 128, 128, .12); margin: 8px 0 10px; overflow: hidden; }
.arm-bar span { display: block; height: 100%; border-radius: 6px; background: var(--brand); transition: width .4s ease; }
.policy-arm.quick .arm-bar span { background: #e6a23c; }
.arm-stats { display: flex; flex-wrap: wrap; gap: 10px; font-size: 11.5px; color: var(--text-muted); }
.arm-stats b { color: var(--text-primary); font-variant-numeric: tabular-nums; }
.arm-desc { font-size: 11.5px; color: var(--text-muted); line-height: 1.6; margin: 8px 0 0; }

.policy-latest {
  display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap;
  margin-top: 14px; padding: 10px 12px; border-radius: 12px;
  background: color-mix(in srgb, var(--brand) 7%, transparent);
  font-size: 12px; color: var(--text-secondary); line-height: 1.65;
}
.latest-label { color: var(--text-muted); }
.latest-reason { color: var(--text-secondary); }
.policy-empty { font-size: 12px; color: var(--text-muted); margin-top: 12px; line-height: 1.7; }
.policy-formula { font-size: 11px; color: var(--text-muted); margin: 12px 0 0; font-variant-numeric: tabular-nums; }
</style>
