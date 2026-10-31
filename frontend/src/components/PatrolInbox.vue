<template>
  <section v-if="events.length" class="patrol-card">
    <div class="patrol-head">
      <span class="patrol-ic">🔔</span>
      <span class="patrol-title">小基提醒</span>
      <span v-if="events.length > 1" class="patrol-count">{{ events.length }}</span>
    </div>

    <article v-for="e in events.slice(0, 2)" :key="e.id" class="patrol-item">
      <p class="patrol-item-title">{{ e.title }}</p>
      <p class="patrol-item-content">{{ e.content }}</p>
      <div class="patrol-actions">
        <button class="patrol-btn ghost" :disabled="busy === e.id" @click="snooze(e)">晚点</button>
        <button class="patrol-btn ghost" :disabled="busy === e.id" @click="dismiss(e)">不用了</button>
        <button class="patrol-btn primary" :disabled="busy === e.id" @click="act(e)">去做</button>
      </div>
    </article>
  </section>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  getPatrolInbox, actPatrolEvent, dismissPatrolEvent, snoozePatrolEvent,
} from '@/api/patrol'

const props = defineProps({
  userId: { type: String, default: '' },
})

const router = useRouter()
const events = ref([])
const busy = ref('')

async function reload() {
  if (!props.userId) return
  try {
    const res = await getPatrolInbox(props.userId)
    events.value = res?.events || []
  } catch (e) {
    console.error('[patrol] inbox:', e)
    events.value = []
  }
}

onMounted(reload)
watch(() => props.userId, reload)
defineExpose({ reload })

function linkOf(e) {
  const ev = e?.evidence || {}
  return ev.link || ev.url || ''
}

async function act(e) {
  if (busy.value) return
  busy.value = e.id
  try {
    await actPatrolEvent(e.id, props.userId)
    events.value = events.value.filter(x => x.id !== e.id)
    const link = linkOf(e)
    if (link) router.push(link)
    else ElMessage.success('好，去做吧')
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '操作失败')
  } finally {
    busy.value = ''
  }
}

async function dismiss(e) {
  if (busy.value) return
  busy.value = e.id
  try {
    await dismissPatrolEvent(e.id, props.userId)
    events.value = events.value.filter(x => x.id !== e.id)
    ElMessage.success('好，这次不打扰你')
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '操作失败')
  } finally {
    busy.value = ''
  }
}

async function snooze(e) {
  if (busy.value) return
  busy.value = e.id
  try {
    await snoozePatrolEvent(e.id, props.userId, 4)
    events.value = events.value.filter(x => x.id !== e.id)
    ElMessage.success('4 小时后再提醒你')
  } catch (err) {
    ElMessage.error(err?.response?.data?.detail || '操作失败')
  } finally {
    busy.value = ''
  }
}
</script>

<style scoped>
.patrol-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid rgba(255, 255, 255, .06);
  border-radius: 14px;
  padding: 12px 14px;
  backdrop-filter: blur(20px);
  margin-bottom: 14px;
}
[data-theme="dark"] .patrol-card {
  background: color-mix(in srgb, var(--surface, #ffffff) 2%, transparent);
}
.patrol-head { display: flex; align-items: center; gap: 7px; margin-bottom: 8px; }
.patrol-ic { font-size: 14px; }
.patrol-title { font-size: 13px; font-weight: 700; color: var(--text-primary); }
.patrol-count {
  margin-left: auto; font-size: 11px; color: var(--brand-bright);
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  padding: 1px 7px; border-radius: 8px;
}
.patrol-item + .patrol-item { margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,.06); }
.patrol-item-title { font-size: 13px; font-weight: 600; color: var(--text-primary); margin: 0 0 3px; }
.patrol-item-content { font-size: 12px; line-height: 1.65; color: var(--text-secondary); margin: 0 0 9px; }
.patrol-actions { display: flex; gap: 7px; justify-content: flex-end; }
.patrol-btn {
  padding: 4px 11px; border-radius: 8px; font-size: 12px; cursor: pointer;
  font-family: inherit; border: 1px solid var(--border-color);
  background: transparent; color: var(--text-secondary); transition: all .2s ease;
}
.patrol-btn:hover:not(:disabled) { background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); color: var(--text-primary); }
.patrol-btn.primary {
  border-color: color-mix(in srgb, var(--brand) 40%, transparent);
  background: color-mix(in srgb, var(--brand) 14%, transparent);
  color: var(--brand-bright); font-weight: 600;
}
.patrol-btn:disabled { opacity: .45; cursor: not-allowed; }
</style>
