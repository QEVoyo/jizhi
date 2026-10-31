<template>
  <section class="memory-card">
    <div class="mem-head">
      <h2 class="mem-title">小基记得的事</h2>
      <span class="mem-count">{{ rows.length }} 条</span>
    </div>
    <p class="mem-desc">
      不是聊天记录，是「从行为里沉淀下来的判断」：薄弱点、偏好、哪种做法对你有效。
      置信度会随证据上升或下降；你可以随时删掉。
    </p>

    <div v-if="loading" class="mem-empty">加载中…</div>
    <div v-else-if="!rows.length" class="mem-empty">
      还没有记忆——做过几道题、或告诉小基一个偏好，这里就会长出来。
    </div>

    <div v-else class="mem-groups">
      <div v-if="weaknesses.length" class="mem-group">
        <div class="mem-group-title">薄弱点</div>
        <div v-for="r in weaknesses" :key="r.id" class="mem-item">
          <div class="mem-item-main">
            <span class="mem-key">{{ r.value?.kp || r.key.replace('kp:', '') }}</span>
            <span class="mem-sub">
              错 {{ r.value?.wrong_count || 0 }} · 对 {{ r.value?.correct_count || 0 }}
            </span>
          </div>
          <span class="mem-conf" :class="confClass(r.confidence)">
            {{ Math.round((r.confidence || 0) * 100) }}%
          </span>
          <button class="mem-del" title="忘掉这条" @click="remove(r)">✕</button>
        </div>
      </div>

      <div v-if="preferences.length" class="mem-group">
        <div class="mem-group-title">偏好</div>
        <div v-for="r in preferences" :key="r.id" class="mem-item">
          <div class="mem-item-main">
            <span class="mem-key">{{ prefLabel(r.value?.dimension) }}</span>
            <span class="mem-sub">{{ r.value?.value }} · {{ r.value?.source === 'explicit' ? '你亲口说的' : '行为推断' }}</span>
          </div>
          <span class="mem-conf" :class="confClass(r.confidence)">
            {{ Math.round((r.confidence || 0) * 100) }}%
          </span>
          <button class="mem-del" title="忘掉这条" @click="remove(r)">✕</button>
        </div>
      </div>

      <div v-if="strategies.length" class="mem-group">
        <div class="mem-group-title">有效做法</div>
        <div v-for="r in strategies" :key="r.id" class="mem-item">
          <div class="mem-item-main">
            <span class="mem-key">{{ strategyLabel(r.scope) }}</span>
            <span class="mem-sub">
              跑 {{ r.value?.runs || 0 }} 次 · 成功率
              {{ Math.round((r.value?.success_rate || 0) * 100) }}%
            </span>
          </div>
          <span class="mem-conf" :class="confClass(r.confidence)">
            {{ Math.round((r.confidence || 0) * 100) }}%
          </span>
          <button class="mem-del" title="忘掉这条" @click="remove(r)">✕</button>
        </div>
      </div>
    </div>

    <div class="mem-form">
      <span class="mem-form-title">告诉小基一个偏好</span>
      <div class="mem-form-row">
        <select v-model="dimension" class="mem-select">
          <option v-for="d in dimensions" :key="d.key" :value="d.key">{{ d.label }}</option>
        </select>
        <input v-model.trim="value" class="mem-input" maxlength="40"
               placeholder="例如：多给视频，少给大段文字" @keyup.enter="savePref" />
        <button class="mem-btn" :disabled="busy || !value" @click="savePref">记住</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getMemory, postPreference, deleteMemory } from '@/api/agents'

const props = defineProps({
  userId: { type: String, default: '' },
})

const rows = ref([])
const loading = ref(false)
const busy = ref(false)
const dimension = ref('format')
const value = ref('')

const dimensions = [
  { key: 'format', label: '讲解形式' },
  { key: 'pace', label: '学习节奏' },
  { key: 'difficulty', label: '难度偏好' },
  { key: 'explain', label: '讲解方式' },
  { key: 'feedback', label: '反馈风格' },
  { key: 'time', label: '学习时间' },
  { key: 'notify', label: '打扰方式' },
]

const weaknesses = computed(() => rows.value.filter(r => ['weakness', 'misconception'].includes(r.kind)))
const preferences = computed(() => rows.value.filter(r => r.kind === 'preference'))
const strategies = computed(() => rows.value.filter(r => r.kind === 'strategy'))

async function reload() {
  if (!props.userId) return
  loading.value = true
  try {
    const res = await getMemory(props.userId)
    rows.value = res?.rows || []
  } catch (e) {
    console.error('[memory] load:', e)
    rows.value = []
  } finally {
    loading.value = false
  }
}

onMounted(reload)
watch(() => props.userId, reload)

const labelMap = {
  format: '讲解形式', pace: '学习节奏', difficulty: '难度偏好',
  explain: '讲解方式', feedback: '反馈风格', time: '学习时间', notify: '打扰方式',
}
function prefLabel(k) { return labelMap[k] || k || '偏好' }
function strategyLabel(scope) {
  const s = String(scope || '')
  if (s.startsWith('workflow:')) return `工作流 ${s.slice(9)}`
  if (s.startsWith('agent:')) return `智能体 ${s.slice(6)}`
  return '做法'
}
function confClass(v) {
  const n = Number(v) || 0
  if (n >= 0.8) return 'high'
  if (n >= 0.55) return 'mid'
  return 'low'
}

async function remove(r) {
  try {
    await deleteMemory(props.userId, r.id)
    rows.value = rows.value.filter(x => x.id !== r.id)
    ElMessage.success('已忘掉这条')
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
  }
}

async function savePref() {
  if (!value.value) return
  busy.value = true
  try {
    await postPreference(props.userId, dimension.value, value.value, 'explicit')
    value.value = ''
    ElMessage.success('记住了')
    await reload()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.memory-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255, 255, 255, .06);
  border-radius: 16px;
  padding: 20px 22px;
  backdrop-filter: blur(20px);
  margin-bottom: 18px;
}
[data-theme="dark"] .memory-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
}
.mem-head { display: flex; align-items: center; justify-content: space-between; }
.mem-title { font-size: 16px; font-weight: 700; color: var(--text-primary); margin: 0; }
.mem-count { font-size: 12px; color: var(--text-muted); }
.mem-desc { font-size: 12px; line-height: 1.65; color: var(--text-muted); margin: 6px 0 16px; }
.mem-empty { font-size: 12px; color: var(--text-muted); padding: 10px 0; }

.mem-groups { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }
.mem-group-title { font-size: 12px; font-weight: 700; color: var(--text-secondary); margin-bottom: 8px; }
.mem-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 10px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  margin-bottom: 6px;
}
[data-theme="dark"] .mem-item { background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent); }
.mem-item-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.mem-key { font-size: 13px; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mem-sub { font-size: 11px; color: var(--text-muted); }
.mem-conf {
  flex: none; font-size: 11px; font-weight: 600; padding: 2px 7px; border-radius: 8px;
  font-variant-numeric: tabular-nums;
}
.mem-conf.high { color: #0ca30c; background: rgba(12, 163, 12, .10); }
.mem-conf.mid { color: #d48806; background: rgba(250, 178, 25, .12); }
.mem-conf.low { color: var(--text-muted); background: rgba(128, 128, 128, .10); }
.mem-del {
  flex: none; border: none; background: transparent; color: var(--text-muted);
  cursor: pointer; font-size: 12px; padding: 2px 4px; border-radius: 6px;
}
.mem-del:hover { background: rgba(230, 162, 60, .12); color: #e6a23c; }

.mem-form { margin-top: 16px; padding-top: 14px; border-top: 1px solid rgba(255, 255, 255, .06); }
.mem-form-title { font-size: 12px; color: var(--text-muted); display: block; margin-bottom: 8px; }
.mem-form-row { display: flex; gap: 8px; flex-wrap: wrap; }
.mem-select, .mem-input {
  padding: 7px 10px; border-radius: 8px; font-size: 12px; font-family: inherit;
  border: 1px solid var(--border-color); background: transparent; color: var(--text-primary);
  outline: none;
}
.mem-select { min-width: 110px; }
.mem-select option { background: var(--surface, #fff); color: #111; }
.mem-input { flex: 1; min-width: 180px; }
.mem-btn {
  padding: 7px 16px; border-radius: 8px; font-size: 12px; font-weight: 600;
  font-family: inherit; cursor: pointer; border: 1px solid color-mix(in srgb, var(--brand) 40%, transparent);
  background: color-mix(in srgb, var(--brand) 14%, transparent); color: var(--brand-bright);
}
.mem-btn:disabled { opacity: .45; cursor: not-allowed; }
</style>
