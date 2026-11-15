<template>
  <button
    v-if="activeRuns.length && !agentPanelState.open"
    class="squad-dock"
    title="看协作进度"
    @click="openFirst"
  >
    <span class="squad-dot"></span>
    <span class="squad-text">协作进行中</span>
    <span class="squad-count">{{ activeRuns.length }}</span>
    <span class="squad-pct">{{ avgProgress }}%</span>
  </button>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { activeRuns, startRunPolling } from '@/stores/runStore'
import { agentPanelState, openAgentPanel } from '@/stores/agentPanel'

const authStore = useAuthStore()

const avgProgress = computed(() => {
  const xs = activeRuns.value.map(r => Number(r.progress) || 0)
  if (!xs.length) return 0
  return Math.round(xs.reduce((a, b) => a + b, 0) / xs.length)
})

function openFirst() {
  if (activeRuns.value.length) openAgentPanel(activeRuns.value[0].id)
}

onMounted(() => {
  if (authStore.user?.id) startRunPolling(authStore.user.id)
})
</script>

<style scoped>
.squad-dock {
  position: fixed; right: 128px; bottom: 22px; z-index: 8900;
  display: flex; align-items: center; gap: 7px;
  padding: 7px 11px 7px 9px; border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--brand) 34%, transparent);
  background: color-mix(in srgb, var(--surface, #ffffff) 92%, transparent);
  color: var(--text-primary); font-family: inherit; font-size: 11.5px;
  box-shadow: 0 8px 22px rgba(0, 0, 0, .16);
  backdrop-filter: blur(18px) saturate(1.3);
  cursor: pointer;
  transition: transform .18s ease, border-color .18s ease;
}
.squad-dock:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--brand) 58%, transparent);
}
.squad-dot {
  width: 8px; height: 8px; border-radius: 50%; flex: none;
  background: #30d158;
  box-shadow: 0 0 0 4px color-mix(in srgb, #30d158 18%, transparent);
  animation: squad-pulse 1.6s ease-in-out infinite;
}
@keyframes squad-pulse { 0%, 100% { opacity: 1; } 50% { opacity: .45; } }
.squad-text { font-weight: 600; }
.squad-count {
  min-width: 18px; padding: 1px 5px; border-radius: 999px;
  background: color-mix(in srgb, var(--brand) 14%, transparent);
  color: var(--brand-bright); font-size: 10px; font-weight: 700; text-align: center;
}
.squad-pct { color: var(--text-muted); font-size: 10.5px; font-variant-numeric: tabular-nums; }
[data-theme="dark"] .squad-dock {
  background: color-mix(in srgb, var(--surface, #0f172a) 88%, transparent);
}
@media (max-width: 640px) {
  .squad-dock { right: 92px; bottom: 14px; padding: 6px 9px 6px 8px; font-size: 11px; }
  .squad-text { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  .squad-dot { animation: none; }
  .squad-dock { transition: none; }
}
</style>
