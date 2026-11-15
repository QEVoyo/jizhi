<template>
  <section class="ep-panel">
    <div class="ep-head">
      <div>
        <h3 class="ep-title">试卷</h3>
        <p class="ep-sub">真题套卷和你生成的 AI 仿真卷都在这里；交卷、解析走同一条链路。</p>
      </div>
      <div class="ep-filters">
        <button
          v-for="f in filters"
          :key="f.value"
          class="ep-filter"
          :class="{ active: filter === f.value }"
          @click="setFilter(f.value)"
        >{{ f.label }}</button>
      </div>
    </div>

    <SkeletonScreen v-if="loading" variant="cards" :count="3" />

    <div v-else-if="error" class="ep-empty">
      <p>{{ error }}</p>
      <el-button @click="load">重试</el-button>
    </div>

    <div v-else-if="!visiblePapers.length" class="ep-empty">
      <p class="ep-empty-title">
        {{ filter === 'simulation' ? '还没有生成过 AI 仿真卷' : '还没有试卷' }}
      </p>
      <p class="ep-empty-sub">
        {{ filter === 'simulation'
          ? '去考纲页点「AI 出卷」，生成后会出现在这里。'
          : '去考纲页选择考纲，或用 AI 出卷生成一份。' }}
      </p>
      <el-button type="primary" @click="goSyllabus">去考纲页</el-button>
    </div>

    <div v-else class="ep-grid">
      <article
        v-for="p in visiblePapers"
        :key="p.paper_id"
        class="ep-card"
        @click="openPaper(p)"
      >
        <div class="ep-card-top">
          <span class="ep-badge" :class="p.paper_type">
            {{ p.paper_type === 'simulation' ? 'AI 仿真卷' : '真题卷' }}
          </span>
          <span class="ep-syllabus">{{ p.syllabus_name || p.syllabus_id }}</span>
        </div>
        <h4 class="ep-name">{{ p.name }}</h4>
        <div class="ep-meta">
          <span>{{ p.question_count || 0 }} 题</span>
          <span>{{ p.section_count || 0 }} 个分区</span>
          <span>{{ p.total_score || p.available_score || 0 }} 分</span>
          <span v-if="p.year">{{ p.year }}<template v-if="p.month">.{{ String(p.month).padStart(2, '0') }}</template></span>
        </div>
        <div class="ep-foot">
          <span v-if="p.paper_type === 'simulation'">{{ fmtGenerated(p.generated_at) }}</span>
          <span v-else>国家考试真题</span>
          <span class="ep-go">去做题 →</span>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listAllExamPapers, listExamPapers, listSyllabi } from '@/api/subjectPlan'
import SkeletonScreen from '@/components/SkeletonScreen.vue'

const props = defineProps({
  userId: { type: String, default: '' },
})

const router = useRouter()
const papers = ref([])
const loading = ref(true)
const error = ref('')
const filter = ref('all')

const filters = [
  { value: 'all', label: '全部' },
  { value: 'simulation', label: 'AI 仿真卷' },
  { value: 'real', label: '真题卷' },
]

const visiblePapers = computed(() => {
  if (filter.value === 'all') return papers.value
  return papers.value.filter(p => p.paper_type === filter.value)
})

async function load() {
  if (!props.userId) {
    loading.value = false
    return
  }
  loading.value = true
  error.value = ''
  try {
    const data = await listAllExamPapers(props.userId, 'all')
    papers.value = data?.papers || []
  } catch (e) {
    // 后端还没更新到 /subject-plan/exam-papers 时，退回逐个考纲聚合。
    // 现有考纲接口已经把生成卷并进 exam_papers，功能不会因为后端版本而空白。
    console.warn('[exam-papers] all endpoint unavailable, fallback:', e)
    try {
      await loadFallback()
    } catch (e2) {
      console.error('[exam-papers] fallback failed:', e2)
      papers.value = []
      error.value = '试卷加载失败，请稍后重试'
    }
  } finally {
    loading.value = false
  }
}

async function loadFallback() {
  const data = await listSyllabi(props.userId)
  const all = []
  for (const s of data?.syllabi || []) {
    try {
      const d = await listExamPapers(s.id, props.userId)
      for (const p of d?.papers || []) {
        all.push({
          ...p,
          syllabus_id: s.id,
          syllabus_name: s.name || s.id,
          link: `/subject-plan/${s.id}/exam/${p.paper_id}?syllabus_id=${s.id}&mode=practice`,
        })
      }
    } catch {}
  }
  const seen = new Set()
  papers.value = all.filter(p => {
    if (seen.has(p.paper_id)) return false
    seen.add(p.paper_id)
    return true
  }).sort((a, b) => {
    if (a.paper_type !== b.paper_type) return a.paper_type === 'simulation' ? -1 : 1
    return String(b.paper_id).localeCompare(String(a.paper_id))
  })
}

function setFilter(v) {
  filter.value = v
}

function openPaper(p) {
  if (p.link) router.push(p.link)
}

function goSyllabus() {
  router.push('/subject-plan')
}

function fmtGenerated(iso) {
  if (!iso) return 'AI 生成'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return 'AI 生成'
  return `${d.getMonth() + 1} 月 ${d.getDate()} 日生成`
}

onMounted(load)
watch(() => props.userId, load)
</script>

<style scoped>
.ep-panel { padding: 6px 0 12px; }
.ep-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 16px; flex-wrap: wrap; margin-bottom: 14px;
}
.ep-title { margin: 0; font-size: 16px; color: var(--text-primary); }
.ep-sub { margin: 4px 0 0; font-size: 12px; color: var(--text-muted); line-height: 1.6; }
.ep-filters { display: flex; gap: 6px; flex-wrap: wrap; }
.ep-filter {
  padding: 5px 11px; border-radius: 8px; cursor: pointer;
  font-family: inherit; font-size: 11.5px;
  color: var(--text-secondary);
  border: 1px solid rgba(128, 128, 128, .18);
  background: transparent;
}
.ep-filter.active {
  color: var(--brand-bright);
  border-color: color-mix(in srgb, var(--brand) 40%, transparent);
  background: color-mix(in srgb, var(--brand) 12%, transparent);
}

.ep-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 12px;
}
.ep-card {
  padding: 14px 16px;
  border-radius: 14px;
  cursor: pointer;
  border: 1px solid rgba(128, 128, 128, .16);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
}
.ep-card:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--brand) 34%, transparent);
  box-shadow: 0 10px 26px rgba(0, 0, 0, .12);
}
.ep-card-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.ep-badge {
  font-size: 10px; padding: 2px 8px; border-radius: 10px; letter-spacing: .4px;
}
.ep-badge.simulation { color: #b45309; background: rgba(245, 158, 11, .14); }
.ep-badge.real { color: #1d4ed8; background: rgba(59, 130, 246, .12); }
.ep-syllabus { font-size: 10.5px; color: var(--text-muted); }
.ep-name {
  margin: 9px 0 8px; font-size: 13.5px; line-height: 1.45;
  color: var(--text-primary); font-weight: 700;
}
.ep-meta { display: flex; gap: 10px; flex-wrap: wrap; font-size: 11px; color: var(--text-muted); }
.ep-foot {
  display: flex; align-items: center; justify-content: space-between;
  margin-top: 12px; padding-top: 10px;
  border-top: 1px dashed rgba(128, 128, 128, .14);
  font-size: 10.5px; color: var(--text-muted);
}
.ep-go { color: var(--brand-bright); font-weight: 600; }

.ep-empty {
  padding: 28px 16px; text-align: center;
  border-radius: 14px; border: 1px dashed rgba(128, 128, 128, .22);
}
.ep-empty-title { margin: 0 0 4px; font-size: 14px; color: var(--text-primary); }
.ep-empty-sub { margin: 0 0 14px; font-size: 12px; color: var(--text-muted); }
</style>
