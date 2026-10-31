<template>
  <section class="decision-card">
    <div class="card-head">
      <h2 class="card-title">调参日记</h2>
      <span class="diary-count">{{ decisions.length }} 条</span>
    </div>
    <p class="card-desc">
      每次自动调整，系统都会写下「看到了什么、为什么这么调、否决了什么」。
      不认同可以回滚；也可以让它别再自动改这几个参数。
    </p>

    <div class="decision-list">
      <article v-for="d in decisions" :key="d.id" class="decision">
        <header class="d-head">
          <span class="d-date">{{ fmtDate(d.created_at) }}</span>
          <span class="d-badge" :class="statusClass(d)">{{ statusText(d) }}</span>
          <span v-if="d.fallback" class="d-fallback" title="大模型不可用，已回落规则文案">规则回落</span>
          <span v-if="num(d.confidence) != null" class="d-conf">
            置信 {{ Math.round(num(d.confidence) * 100) }}%
          </span>
          <span v-if="d.agrees === false" class="d-disagree" title="模型认为本次规则调整不一定最优">
            模型有不同意见
          </span>
        </header>

        <p class="d-diagnosis">{{ d.diagnosis || '（本次调整没有附加诊断）' }}</p>
        <p v-if="d.diary" class="d-diary">{{ d.diary }}</p>

        <div v-if="list(d.changes).length" class="d-changes">
          <span v-for="(c, i) in list(d.changes)" :key="i" class="d-change">
            {{ c.agent_key }}.{{ c.param_key }}
            <b>{{ fmtVal(c.old_value) }}</b>
            <span class="d-arrow">→</span>
            <b>{{ fmtVal(c.new_value) }}</b>
          </span>
        </div>

        <details v-if="hasEvidence(d.evidence)" class="d-evidence">
          <summary>为什么这么判断（证据）</summary>
          <pre>{{ pretty(d.evidence) }}</pre>
        </details>

        <p v-if="list(d.rejected).length" class="d-note d-rejected">
          <span class="d-label">否决了：</span>{{ list(d.rejected).join('；') }}
        </p>
        <p v-if="d.suggestion" class="d-note d-suggestion">
          <span class="d-label">更好的做法：</span>{{ d.suggestion }}
        </p>

        <p v-if="lastFeedback(d)" class="d-note d-feedback">
          <span class="d-label">你的反馈：</span>{{ lastFeedback(d) }}
        </p>

        <footer class="d-actions">
          <button :disabled="busy === d.id" @click="feedback(d, 'agree')">认同</button>
          <button :disabled="busy === d.id" @click="feedback(d, 'disagree')">不认同</button>
          <button :disabled="busy === d.id" @click="feedback(d, 'lock')">别再自动改</button>
          <button
            class="danger"
            :disabled="busy === d.id || d.status === 'reverted'"
            @click="revert(d)"
          >
            {{ d.status === 'reverted' ? '已回滚' : '回滚本次调整' }}
          </button>
        </footer>
      </article>

      <p v-if="!decisions.length && !loading" class="tl-empty">
        还没有调参日记——触发一次自动调整后，这里会出现「为什么这么调」。
      </p>
      <p v-if="loading" class="tl-empty">加载中…</p>
    </div>
  </section>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getDecisions,
  postDecisionFeedback,
  postDecisionRevert,
} from '@/api/agentCenter'

const props = defineProps({
  userId: { type: String, default: '' },
})

const decisions = ref([])
const loading = ref(false)
const busy = ref('')

async function reload() {
  if (!props.userId) return
  loading.value = true
  try {
    decisions.value = await getDecisions(props.userId)
  } catch (e) {
    console.error('[decision-timeline] load:', e)
    decisions.value = []
  } finally {
    loading.value = false
  }
}

onMounted(reload)
watch(() => props.userId, reload)
defineExpose({ reload })

function list(v) {
  if (Array.isArray(v)) return v
  if (typeof v === 'string' && v.trim()) {
    try {
      const p = JSON.parse(v)
      return Array.isArray(p) ? p : []
    } catch { return [] }
  }
  return []
}

function hasEvidence(v) {
  if (!v) return false
  if (typeof v === 'object') return Object.keys(v).length > 0
  return String(v).trim().length > 0
}

function num(v) {
  if (v === null || v === undefined || v === '') return null
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

function fmtVal(v) {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

function pretty(v) {
  try {
    return typeof v === 'string' ? v : JSON.stringify(v, null, 2)
  } catch {
    return String(v)
  }
}

function fmtDate(s) {
  if (!s) return ''
  const d = new Date(s)
  if (Number.isNaN(d.getTime())) return String(s).slice(0, 10)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function statusText(d) {
  if (d.status === 'reverted') return '已回滚'
  if (d.status === 'proposed') return '待确认'
  if (d.status === 'rejected') return '已否决'
  return '已生效'
}

function statusClass(d) {
  if (d.status === 'reverted') return 'reverted'
  if (d.status === 'proposed') return 'proposed'
  return 'applied'
}

function lastFeedback(d) {
  const fb = list(d.feedback)
  if (!fb.length) return ''
  const last = fb[fb.length - 1] || {}
  const map = { agree: '认同', disagree: '不认同', lock: '别再自动改' }
  const note = last.note ? `（${last.note}）` : ''
  return (map[last.action] || last.action || '') + note
}

async function feedback(d, action) {
  if (busy.value === d.id) return
  busy.value = d.id
  try {
    await postDecisionFeedback(d.id, props.userId, action)
    if (action === 'lock') {
      ElMessage.success('已暂停这些参数的自动托管')
    } else if (action === 'agree') {
      ElMessage.success('已记录：认同这次调整')
    } else {
      ElMessage.success('已记录：不认同这次调整')
    }
    await reload()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '反馈保存失败')
  } finally {
    busy.value = ''
  }
}

async function revert(d) {
  if (busy.value === d.id) return
  try {
    await ElMessageBox.confirm(
      '回滚会把本次调整的参数恢复成调整前的值，并暂停这些参数的自动托管。继续吗？',
      '回滚调参',
      { type: 'warning', confirmButtonText: '回滚', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  busy.value = d.id
  try {
    const res = await postDecisionRevert(d.id, props.userId)
    ElMessage.success(res?.reverted ? `已回滚 ${res.reverted} 项参数` : '已回滚')
    await reload()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '回滚失败')
  } finally {
    busy.value = ''
  }
}
</script>

<style scoped>
.decision-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255, 255, 255, .06);
  border-radius: 16px;
  padding: 20px 22px;
  backdrop-filter: blur(20px);
  margin-bottom: 18px;
}
[data-theme="dark"] .decision-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
}
.card-head { display: flex; align-items: center; justify-content: space-between; }
.card-title { font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 0; }
.diary-count { font-size: 12px; color: var(--text-muted); }
.card-desc { font-size: 12px; color: var(--text-muted); margin: 6px 0 16px; line-height: 1.6; }

.decision-list { display: flex; flex-direction: column; gap: 14px; }
.decision {
  border: 1px solid rgba(255, 255, 255, .06);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border-radius: 14px;
  padding: 14px 16px;
}
[data-theme="dark"] .decision {
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
}
.d-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.d-date { font-size: 12px; color: var(--text-muted); font-variant-numeric: tabular-nums; }
.d-badge {
  font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600;
}
.d-badge.applied { color: #0ca30c; background: rgba(12, 163, 12, .10); }
.d-badge.reverted { color: var(--text-muted); background: rgba(128, 128, 128, .12); }
.d-badge.proposed { color: #d48806; background: rgba(250, 178, 25, .12); }
.d-fallback { font-size: 11px; color: var(--text-muted); background: rgba(128, 128, 128, .10); padding: 2px 8px; border-radius: 10px; }
.d-conf { font-size: 11px; color: var(--viz-s1); background: color-mix(in srgb, var(--brand) 10%, transparent); padding: 2px 8px; border-radius: 10px; }
.d-disagree { font-size: 11px; color: #d48806; background: rgba(250, 178, 25, .10); padding: 2px 8px; border-radius: 10px; }

.d-diagnosis { font-size: 14px; font-weight: 600; color: var(--text-primary); margin: 10px 0 6px; line-height: 1.6; }
.d-diary { font-size: 13px; color: var(--text-secondary); margin: 0 0 10px; line-height: 1.75; white-space: pre-wrap; }
.d-changes { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
.d-change {
  font-size: 12px; color: var(--text-secondary);
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  border-radius: 8px; padding: 4px 10px;
}
.d-change b { color: var(--text-primary); font-variant-numeric: tabular-nums; }
.d-arrow { margin: 0 3px; color: var(--text-muted); }

.d-evidence { margin: 8px 0; }
.d-evidence summary { font-size: 12px; color: var(--text-muted); cursor: pointer; }
.d-evidence pre {
  margin: 8px 0 0; padding: 10px 12px; border-radius: 10px;
  background: rgba(15, 23, 42, .05); color: var(--text-secondary);
  font-size: 11.5px; line-height: 1.6; max-height: 240px; overflow: auto;
  white-space: pre-wrap; word-break: break-word;
}
[data-theme="dark"] .d-evidence pre { background: rgba(255, 255, 255, .04); }

.d-note { font-size: 12px; color: var(--text-secondary); margin: 6px 0; line-height: 1.6; }
.d-label { color: var(--text-muted); }
.d-rejected { color: var(--text-muted); }
.d-suggestion { color: var(--viz-warn); }
.d-feedback { color: var(--viz-s1); }

.d-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.d-actions button {
  padding: 5px 12px; border-radius: 8px; font-size: 12px; cursor: pointer;
  font-family: inherit; border: 1px solid var(--border-color);
  background: transparent; color: var(--text-secondary);
  transition: all .2s ease;
}
.d-actions button:hover:not(:disabled) {
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  color: var(--text-primary);
}
.d-actions button.danger { color: #e6a23c; border-color: rgba(230, 162, 60, .35); }
.d-actions button.danger:hover:not(:disabled) { background: rgba(230, 162, 60, .10); }
.d-actions button:disabled { opacity: .45; cursor: not-allowed; }

.tl-empty { font-size: 12px; color: var(--text-muted); padding: 8px 0; }
</style>
