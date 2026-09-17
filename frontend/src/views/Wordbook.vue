<template>
  <div class="wordbook-page">
    <button class="back-btn" @click="router.push('/home')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6"/></svg>
      返回主界面
    </button>

    <div class="wb-header">
      <h1 class="wb-title">词条本</h1>
      <p class="wb-subtitle">从对话和小基识图收集的生词，在这里复习巩固</p>
    </div>

    <!-- 统计 -->
    <div class="wb-stats">
      <div class="wb-stat">
        <span class="ws-label">总词条</span>
        <strong class="ws-value">{{ stats?.total ?? '—' }}</strong>
      </div>
      <div class="wb-stat">
        <span class="ws-label">已掌握（≥80）</span>
        <strong class="ws-value good">{{ stats?.mastered ?? '—' }}</strong>
      </div>
      <div class="wb-stat">
        <span class="ws-label">薄弱（&lt;60）</span>
        <strong class="ws-value warn">{{ stats?.weak ?? '—' }}</strong>
      </div>
      <div class="wb-stat">
        <span class="ws-label">平均熟练度</span>
        <strong class="ws-value">{{ stats?.avg ?? '—' }}</strong>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="wb-toolbar">
      <div class="wb-filters">
        <button
          v-for="f in filters" :key="f.value"
          class="wb-filter" :class="{ active: filter === f.value }"
          @click="setFilter(f.value)"
        >{{ f.label }}</button>
      </div>
      <div class="wb-actions">
        <button class="wb-btn primary" :disabled="!weakWords.length || generating" @click="generatePractice">
          {{ generating ? '出题中…' : `薄弱词出题（${weakWords.length}）` }}
        </button>
        <button class="wb-btn" :disabled="!weakWords.length" @click="startReview">
          {{ reviewMode ? '退出复习' : '复习薄弱词' }}
        </button>
      </div>
    </div>

    <!-- 复习模式 -->
    <div v-if="reviewMode" class="wb-review">
      <p v-if="!reviewQueue.length" class="wb-empty">
        复习完成 🎉 <button class="wb-btn" @click="reviewMode = false">返回列表</button>
      </p>
      <div v-else class="review-wrap">
        <p class="review-progress">{{ reviewTotal - reviewQueue.length + 1 }} / {{ reviewTotal }}</p>
        <VocabCard :word="reviewQueue[0]" :user-id="uid" touchpoint="wordbook" @rated="onRated" />
      </div>
    </div>

    <!-- 列表模式 -->
    <div v-else class="wb-list">
      <!-- 从全局搜索跳转（?q=词）的提示条 -->
      <div v-if="highlightWord" class="wb-highlight-banner">
        从全局搜索跳转：正在查看「{{ highlightWord }}」
        <button class="wb-banner-clear" @click="clearHighlight">清除</button>
      </div>
      <p v-if="!items.length" class="wb-empty">
        词条本还是空的——在对话里问词义（比如发「abandon 什么意思」），或用小基识图拍题提取生词，就会自动收进来。
      </p>
      <div
        v-for="it in items" :key="it.word"
        class="wb-item" :data-word="it.word"
        :class="{ highlighted: highlightWord && it.word === highlightWord }"
      >
        <div class="wi-left">
          <strong class="wi-word">{{ it.word }}</strong>
          <span class="wi-meaning">{{ it.entry?.meaning || '暂无释义，复习时生成' }}</span>
          <span v-if="it.entry?.phonetic" class="wi-phonetic">/{{ it.entry.phonetic }}/</span>
        </div>
        <div class="wi-mastery">
          <div class="wi-bar">
            <div class="wi-fill" :style="{ width: (it.mastery_score || 0) + '%', background: barColor(it.mastery_score) }"></div>
          </div>
          <span class="wi-score" :style="{ color: barColor(it.mastery_score) }">{{ it.mastery_score }}</span>
        </div>
        <div class="wi-counts">{{ it.correct_count }}/{{ it.total_count }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getVocabStats, getWordbook, postVocabPracticeSet } from '@/api/vocab'
import VocabCard from '@/components/VocabCard.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const uid = computed(() => authStore.user?.id || '')

// 从全局搜索跳转（/wordbook?q=词）的目标词
const highlightWord = ref(route.query.q ? String(route.query.q) : '')

const stats = ref(null)
const items = ref([])
const filter = ref('all')
const filters = [
  { value: 'all', label: '全部' },
  { value: 'weak', label: '薄弱（<60）' },
  { value: 'mastered', label: '已掌握（≥80）' },
]
const generating = ref(false)
const reviewMode = ref(false)
const reviewQueue = ref([])
const reviewTotal = ref(0)

const weakWords = computed(() => items.value.filter(it => (it.mastery_score || 0) < 60).map(it => it.word))

async function load() {
  if (!uid.value) return
  try {
    stats.value = await getVocabStats(uid.value)
    items.value = await getWordbook(uid.value, filter.value)
    focusWord()
  } catch (e) {
    console.error('[wordbook] load:', e)
  }
}
onMounted(load)

// ===== 从全局搜索跳转（?q=词）：定位并高亮 =====
function focusWord() {
  if (!highlightWord.value) return
  nextTick(() => {
    try {
      document
        .querySelector(`.wb-item[data-word="${CSS.escape(highlightWord.value)}"]`)
        ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    } catch { /* 选择器异常时忽略 */ }
  })
}

// 已在词条本页时再次搜索跳转（同一组件不重挂载，靠 watch 生效）
watch(() => route.query.q, (q) => {
  if (q) {
    highlightWord.value = String(q)
    if (filter.value !== 'all') setFilter('all') // 切回全部，保证词条在列表中
    else focusWord()
  } else {
    highlightWord.value = ''
  }
})

function clearHighlight() {
  highlightWord.value = ''
  router.replace({ path: '/wordbook' })
}

function setFilter(f) {
  filter.value = f
  reviewMode.value = false
  load()
}

function barColor(score) {
  if (score == null) return 'var(--viz-muted)'
  if (score >= 80) return 'var(--viz-good)'
  if (score >= 60) return 'var(--viz-warn)'
  return 'var(--viz-crit)'
}

// ===== 复习 =====
function startReview() {
  if (reviewMode.value) { reviewMode.value = false; return }
  reviewQueue.value = [...weakWords.value]
  reviewTotal.value = reviewQueue.value.length
  reviewMode.value = true
}
function onRated() {
  reviewQueue.value.shift()
  load()  // 同步统计与列表
}

// ===== 薄弱词定向出题 =====
async function generatePractice() {
  if (!weakWords.value.length || generating.value) return
  generating.value = true
  try {
    const res = await postVocabPracticeSet(uid.value, weakWords.value.slice(0, 10))
    ElMessage.success(`已生成 ${res.created?.length || 0} 道词条练习，去「资源库 → 生成历史」练习`)
    setTimeout(() => router.push('/resource-lib'), 1200)
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '出题失败，请稍后重试')
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.wordbook-page {
  padding: 28px 34px 40px;
  max-width: 960px;
  margin: 0 auto;
  --viz-good: #006300; --viz-warn: #8a5a00; --viz-crit: #d03b3b; --viz-muted: #898781;
}
[data-theme="dark"] .wordbook-page {
  --viz-good: #0ca30c; --viz-warn: #fab219; --viz-crit: #e66767; --viz-muted: #898781;
}
.back-btn {
  display: inline-flex; align-items: center; gap: 6px;
  background: transparent; border: none; color: var(--text-secondary);
  font-size: 13px; cursor: pointer; padding: 4px 8px; border-radius: 8px;
  transition: all .2s ease; font-family: inherit; margin-bottom: 14px;
}
.back-btn svg { width: 16px; height: 16px; }
.back-btn:hover { color: var(--text-primary); background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); transform: translateX(-2px); }
[data-theme="light"] .back-btn:hover { background: rgba(15,23,42,.05); }

.wb-title { font-size: 26px; font-weight: 700; color: var(--text-primary); margin: 0; }
.wb-subtitle { font-size: 13px; color: var(--text-secondary); margin: 6px 0 20px; }

/* 统计 */
.wb-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.wb-stat {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent); border: 1px solid rgba(255,255,255,.06);
  border-radius: 14px; padding: 14px 16px; display: flex; flex-direction: column; gap: 4px;
}
[data-theme="light"] .wb-stat { background: color-mix(in srgb, var(--surface, #ffffff) 92%, transparent); border-color: rgba(15,23,42,.09); }
.ws-label { font-size: 12px; color: var(--text-secondary); }
.ws-value { font-size: 22px; font-weight: 700; color: var(--text-primary); font-variant-numeric: tabular-nums; }
.ws-value.good { color: var(--viz-good); }
.ws-value.warn { color: var(--viz-warn); }

/* 工具栏 */
.wb-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.wb-filters { display: flex; gap: 6px; }
.wb-filter {
  padding: 6px 14px; border-radius: 8px; font-size: 12px; cursor: pointer; font-family: inherit;
  border: 1px solid var(--border-color); background: transparent; color: var(--text-secondary);
  transition: all .2s ease;
}
.wb-filter.active { background: color-mix(in srgb, var(--brand) 14%, transparent); border-color: color-mix(in srgb, var(--brand) 35%, transparent); color: var(--brand-bright); font-weight: 600; }
.wb-actions { display: flex; gap: 8px; }
.wb-btn {
  padding: 6px 14px; border-radius: 8px; font-size: 12px; cursor: pointer; font-family: inherit;
  border: 1px solid var(--border-color); background: transparent; color: var(--text-secondary);
  transition: all .2s ease;
}
.wb-btn:hover:not(:disabled) { background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); color: var(--text-primary); }
.wb-btn.primary {
  border: 1px solid color-mix(in srgb, var(--brand) 40%, transparent); background: color-mix(in srgb, var(--brand) 15%, transparent); color: var(--brand-bright); font-weight: 600;
}
.wb-btn:disabled { opacity: .5; cursor: not-allowed; }

/* 复习 */
.wb-review { padding: 12px 0; }
.review-wrap { max-width: 520px; }
.review-progress { font-size: 12px; color: var(--text-muted); margin: 0 0 6px; }

/* 列表 */
.wb-list { display: flex; flex-direction: column; gap: 8px; }
.wb-empty { font-size: 13px; color: var(--text-muted); padding: 40px 0; text-align: center; line-height: 1.8; }
.wb-item {
  display: flex; align-items: center; gap: 14px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent); border: 1px solid rgba(255,255,255,.05);
  border-radius: 12px; padding: 10px 14px;
}
[data-theme="light"] .wb-item { background: rgba(15,23,42,.02); border-color: rgba(15,23,42,.06); }
.wi-left { flex: 1; min-width: 0; display: flex; align-items: baseline; gap: 10px; flex-wrap: wrap; }
.wi-word { font-size: 15px; color: color-mix(in srgb, #818cf8 60%, var(--text-primary)); font-weight: 700; }
.wi-meaning { font-size: 12px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 320px; }
.wi-phonetic { font-size: 11px; color: var(--text-muted); }
.wi-mastery { display: flex; align-items: center; gap: 8px; width: 160px; flex-shrink: 0; }
.wi-bar { flex: 1; height: 8px; border-radius: 4px; background: rgba(128,128,128,.12); overflow: hidden; }
.wi-fill { height: 100%; border-radius: 4px; transition: width .4s ease; }
.wi-score { font-size: 12px; font-weight: 700; width: 30px; text-align: right; font-variant-numeric: tabular-nums; }
.wi-counts { font-size: 11px; color: var(--text-muted); width: 52px; text-align: right; font-variant-numeric: tabular-nums; }

/* ===== 搜索跳转高亮 ===== */
.wb-highlight-banner {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 10px 14px; border-radius: 10px; font-size: 12.5px;
  background: color-mix(in srgb, var(--brand) 10%, transparent); border: 1px solid color-mix(in srgb, var(--brand) 25%, transparent); color: var(--brand-bright);
  margin-bottom: 10px;
}
.wb-banner-clear {
  background: transparent; border: none; color: var(--brand-bright); font-size: 12px;
  cursor: pointer; font-family: inherit; text-decoration: underline;
}
.wb-item.highlighted {
  border-color: color-mix(in srgb, var(--brand) 45%, transparent);
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  animation: wb-flash 2.4s ease 1;
}
@keyframes wb-flash {
  0%, 60% { box-shadow: 0 0 0 2px color-mix(in srgb, var(--brand) 35%, transparent); }
  100% { box-shadow: 0 0 0 2px transparent; }
}

@media (max-width: 700px) {
  .wordbook-page { padding: 20px 16px 32px; }
  .wb-stats { grid-template-columns: repeat(2, 1fr); }
  .wi-mastery { width: 100px; }
}
</style>
