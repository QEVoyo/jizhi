<template>
  <section class="kb-card">
    <header class="kb-head">
      <div>
        <h2 class="kb-title">知识库</h2>
        <p class="kb-sub">
          团队 Agent 检索的真实知识源。每个来源都有 key、字段、范围和引用格式，
          出题与校验的每条证据都能回指到这里。
        </p>
      </div>
      <span class="kb-count">{{ sources.length }} 个来源</span>
    </header>

    <div class="kb-grid">
      <article v-for="s in sources" :key="s.key" class="kb-item">
        <div class="kb-item-head">
          <h3>{{ s.name }}</h3>
          <span class="kb-kind">{{ s.kind }}</span>
        </div>
        <p class="kb-desc">{{ s.description }}</p>
        <div class="kb-meta">
          <span class="kb-key">{{ s.key }}</span>
          <span class="kb-num">{{ fmtCount(stats[s.key]) }} 条</span>
          <span class="kb-ref">{{ s.citation }}</span>
        </div>
      </article>
    </div>

    <div class="kb-search">
      <input
        v-model="query"
        class="kb-input"
        placeholder="搜一个知识点，例如：函数单调性"
        @keyup.enter="doSearch"
      >
      <button class="kb-btn" :disabled="searching || !query.trim()" @click="doSearch">
        {{ searching ? '检索中…' : '跨库检索' }}
      </button>
    </div>

    <div v-if="results.length" class="kb-results">
      <article v-for="r in results" :key="r.ref || r.id" class="kb-result">
        <div class="kb-result-head">
          <span class="kb-source">{{ r.source_name }}</span>
          <span class="kb-result-title">{{ r.title || r.ref }}</span>
          <span class="kb-score">{{ Math.round((r.score || 0) * 100) }}</span>
        </div>
        <p class="kb-snippet">{{ r.snippet }}</p>
        <span class="kb-ref-line">{{ r.ref }}</span>
      </article>
    </div>
    <p v-else-if="searched && !searching" class="kb-empty">没有检索到可用证据。</p>
  </section>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { getKnowledge, searchKnowledge } from '@/api/agents'

const props = defineProps({
  userId: { type: String, default: '' },
})

const sources = ref([])
const stats = ref({})
const query = ref('')
const results = ref([])
const searching = ref(false)
const searched = ref(false)

async function load() {
  if (!props.userId) return
  try {
    const data = await getKnowledge(props.userId)
    sources.value = data?.sources || []
    stats.value = data?.stats || {}
  } catch (e) {
    console.error('[knowledge] load:', e)
    sources.value = []
    stats.value = {}
  }
}

async function doSearch() {
  const q = query.value.trim()
  if (!q || !props.userId || searching.value) return
  searching.value = true
  searched.value = true
  try {
    const data = await searchKnowledge(props.userId, q)
    results.value = data?.items || []
  } catch (e) {
    console.error('[knowledge] search:', e)
    results.value = []
  } finally {
    searching.value = false
  }
}

function fmtCount(n) {
  if (n === null || n === undefined) return '—'
  return Number(n).toLocaleString()
}

onMounted(load)
watch(() => props.userId, load)
</script>

<style scoped>
.kb-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255, 255, 255, .06);
  border-radius: 16px;
  padding: 20px 22px;
  margin-top: 18px;
}
[data-theme="dark"] .kb-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
}
.kb-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.kb-title { font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 0; }
.kb-sub { font-size: 12px; color: var(--text-muted); margin: 6px 0 0; line-height: 1.6; max-width: 720px; }
.kb-count { font-size: 12px; color: var(--text-muted); white-space: nowrap; }

.kb-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 10px; margin-top: 14px;
}
.kb-item {
  border: 1px solid rgba(255, 255, 255, .06);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border-radius: 12px; padding: 12px 14px;
}
.kb-item-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.kb-item h3 { font-size: 13px; margin: 0; color: var(--text-primary); }
.kb-kind {
  font-size: 10px; color: var(--text-muted); background: rgba(128, 128, 128, .12);
  border-radius: 8px; padding: 1px 6px;
}
.kb-desc { font-size: 12px; color: var(--text-secondary); line-height: 1.6; margin: 8px 0; }
.kb-meta { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.kb-key, .kb-ref {
  font-size: 10.5px; color: var(--text-muted); font-family: ui-monospace, monospace;
  background: rgba(128, 128, 128, .08); border-radius: 6px; padding: 1px 6px;
}
.kb-num { font-size: 11px; color: var(--brand-bright); font-variant-numeric: tabular-nums; }

.kb-search { display: flex; gap: 8px; margin-top: 14px; }
.kb-input {
  flex: 1; min-width: 0; padding: 8px 12px; border-radius: 10px;
  border: 1px solid var(--border-color); background: transparent;
  color: var(--text-primary); font-size: 13px; font-family: inherit;
}
.kb-input:focus { outline: none; border-color: var(--brand); }
.kb-btn {
  padding: 8px 14px; border-radius: 10px; border: 1px solid var(--border-color);
  background: transparent; color: var(--text-secondary); font-size: 13px;
  cursor: pointer; font-family: inherit;
}
.kb-btn:hover:not(:disabled) { color: var(--text-primary); border-color: var(--brand); }
.kb-btn:disabled { opacity: .45; cursor: not-allowed; }

.kb-results { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.kb-result {
  border: 1px solid rgba(255, 255, 255, .06);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border-radius: 10px; padding: 10px 12px;
}
.kb-result-head { display: flex; align-items: center; gap: 8px; }
.kb-source {
  font-size: 10.5px; color: var(--brand-bright);
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  border-radius: 8px; padding: 1px 7px;
}
.kb-result-title { font-size: 12.5px; color: var(--text-primary); font-weight: 600; }
.kb-score { margin-left: auto; font-size: 11px; color: var(--text-muted); font-variant-numeric: tabular-nums; }
.kb-snippet { font-size: 12px; color: var(--text-secondary); line-height: 1.6; margin: 6px 0 4px; }
.kb-ref-line { font-size: 10.5px; color: var(--text-muted); font-family: ui-monospace, monospace; }
.kb-empty { font-size: 12px; color: var(--text-muted); margin-top: 10px; }
</style>
