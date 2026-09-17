<template>
  <div class="vocab-card">
    <div v-if="loading" class="vc-loading">词条加载中…</div>
    <template v-else-if="entry">
      <div class="vc-head">
        <strong class="vc-word">{{ entry.word }}</strong>
        <span v-if="entry.phonetic" class="vc-phonetic">/{{ entry.phonetic }}/</span>
        <button class="vc-close" aria-label="关闭" @click="$emit('close')">×</button>
      </div>
      <div class="vc-meaning">{{ entry.meaning }}</div>
      <div v-if="entry.example" class="vc-example">{{ entry.example }}</div>
      <div class="vc-actions">
        <button class="vc-btn known" :class="{ done: lastKnown === true }" :disabled="rating" @click="rate(true)">
          {{ lastKnown === true ? '已认识 ✓' : '认识 ✓' }}
        </button>
        <button class="vc-btn unknown" :class="{ done: lastKnown === false }" :disabled="rating" @click="rate(false)">
          {{ lastKnown === false ? '已标记 ✗' : '不认识 ✗' }}
        </button>
        <span v-if="masteryScore != null" class="vc-score">熟练度 {{ masteryScore }}</span>
      </div>
    </template>
    <div v-else class="vc-loading">{{ error || '词条生成失败，请稍后重试' }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getVocabEntry, postVocabMastery, postVocabLookups } from '@/api/vocab'

const props = defineProps({
  word: { type: String, required: true },
  userId: { type: String, required: true },
  // 触点：chat_ask（对话问词义）/ xiaoji_vision（识图提词）/ wordbook（词条本复习）
  touchpoint: { type: String, default: 'chat_ask' },
})
const emit = defineEmits(['close', 'rated'])

const loading = ref(true)
const error = ref('')
const entry = ref(null)
const masteryScore = ref(null)
const lastKnown = ref(null)
const rating = ref(false)

onMounted(async () => {
  try {
    entry.value = await getVocabEntry(props.word)
    if (props.touchpoint !== 'wordbook') {
      postVocabLookups(props.userId, [props.word], props.touchpoint).catch(() => {})
    }
  } catch (e) {
    error.value = '词条加载失败'
  } finally {
    loading.value = false
  }
})

async function rate(known) {
  if (rating.value) return
  rating.value = true
  try {
    const res = await postVocabMastery(props.userId, props.word, known)
    masteryScore.value = res.mastery_score
    lastKnown.value = known
    emit('rated', known)
  } catch (e) {
    // 静默失败，卡片仍可用
  } finally {
    rating.value = false
  }
}
</script>

<style scoped>
.vocab-card {
  background: rgba(99,102,241,.06);
  border: 1px solid rgba(99,102,241,.22);
  border-radius: 12px;
  padding: 12px 14px;
  margin: 8px 0;
  max-width: 520px;
  font-size: 13px;
}
[data-theme="light"] .vocab-card { background: rgba(99,102,241,.05); border-color: rgba(99,102,241,.25); }
.vc-head { display: flex; align-items: baseline; gap: 8px; }
.vc-word { font-size: 16px; color: color-mix(in srgb, #818cf8 60%, var(--text-primary)); font-weight: 700; }
.vc-phonetic { font-size: 12px; color: var(--text-muted); }
.vc-close {
  margin-left: auto; background: transparent; border: none; cursor: pointer;
  color: var(--text-muted); font-size: 15px; padding: 0 4px; line-height: 1;
}
.vc-close:hover { color: var(--text-primary); }
.vc-meaning { color: var(--text-primary); margin-top: 6px; line-height: 1.6; }
.vc-example { color: var(--text-secondary); margin-top: 4px; line-height: 1.5; font-style: italic; }
.vc-actions { display: flex; align-items: center; gap: 8px; margin-top: 10px; }
.vc-btn {
  padding: 4px 12px; border-radius: 8px; font-size: 12px; cursor: pointer; font-family: inherit;
  transition: all .2s ease;
}
.vc-btn.known {
  border: 1px solid rgba(16,185,129,.4); background: rgba(16,185,129,.12); color: color-mix(in srgb, #34d399 65%, var(--text-primary));
}
.vc-btn.unknown {
  border: 1px solid rgba(239,68,68,.4); background: rgba(239,68,68,.12); color: #f87171;
}
.vc-btn:hover:not(:disabled) { transform: translateY(-1px); }
.vc-btn:disabled { cursor: not-allowed; opacity: .6; }
.vc-btn.done { opacity: .55; }
.vc-score { margin-left: auto; font-size: 11px; color: var(--text-muted); font-variant-numeric: tabular-nums; }
.vc-loading { color: var(--text-muted); padding: 4px 0; }
</style>
