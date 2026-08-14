<template>
  <div class="hub-page">
    <div class="hub-bg"></div>
    <div class="hub-container">
      <div class="hub-topbar">
        <button class="back-btn" @click="$router.push('/home')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          <span>返回首页</span>
        </button>
      </div>

      <div class="hub-hero">
        <h1>学科计划</h1>
        <p>选择考纲，AI 为你生成针对性备考方案</p>
      </div>

      <!-- ===== 搜索 + 筛选 + 收藏入口 ===== -->
      <div class="hub-toolbar">
        <div class="search-wrap">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
          <input
            v-model="searchQuery"
            class="search-input"
            placeholder="搜索考纲名称或描述..."
            @input="onSearch"
          />
          <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''; onSearch()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
        </div>

        <div class="filter-pills">
          <button
            class="pill"
            :class="{ active: activeFilter === 'all' }"
            @click="activeFilter = 'all'"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
            全部<span class="pill-count">{{ syllabi.length }}</span>
          </button>
          <button
            class="pill"
            :class="{ active: activeFilter === 'favorites' }"
            @click="activeFilter = 'favorites'"
          >
            <svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
            已收藏<span class="pill-count">{{ favoriteCount }}</span>
          </button>
          <button
            class="pill"
            :class="{ active: activeFilter === 'available' }"
            @click="activeFilter = 'available'"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            可用考纲<span class="pill-count">{{ availableCount }}</span>
          </button>
        </div>
      </div>

      <!-- 加载 -->
      <div v-if="loading" class="hub-loading">
        <div class="loading-pulse"></div>
        <span>加载考纲列表...</span>
      </div>

      <!-- ===== 考纲网格 ===== -->
      <div v-else-if="filteredSyllabi.length" class="syllabi-grid">
        <div
          v-for="s in filteredSyllabi"
          :key="s.id"
          class="syllabus-card"
          :class="{ disabled: !s.question_count }"
          @click="enterSyllabus(s)"
        >
          <div class="card-glow" :style="{ '--glow-color': s.color || '#6c8cff' }"></div>
          <div class="card-badge" :style="{ background: s.color || '#6c8cff' }">
            {{ s.abbr || s.name?.charAt(0) }}
          </div>
          <div class="card-body">
            <div class="card-title">{{ s.name }}</div>
            <div class="card-desc">{{ s.description }}</div>
          </div>
          <div class="card-right">
            <!-- 收藏按钮 -->
            <button
              class="fav-btn"
              :class="{ favorited: isFavorited(s.id) }"
              @click.stop="toggleFavorite(s.id)"
              :title="isFavorited(s.id) ? '取消收藏' : '收藏考纲'"
            >
              <svg viewBox="0 0 24 24" :fill="isFavorited(s.id) ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
            </button>
            <div class="card-stats">
              <span v-if="s.question_count" class="stat-count">{{ s.question_count }} 题</span>
              <span v-else class="stat-pending">待配置</span>
              <span v-if="s.has_plan" class="stat-plan active">已生成</span>
              <span v-else-if="s.question_count" class="stat-plan">未开始</span>
            </div>
            <svg class="card-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </div>
        </div>
      </div>

      <!-- 空态 -->
      <div v-else class="hub-empty glass-panel">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
        </div>
        <h3 v-if="activeFilter === 'favorites'">暂无收藏</h3>
        <h3 v-else>没有匹配的考纲</h3>
        <p v-if="activeFilter === 'favorites'">点击考纲卡片右侧的心形图标收藏</p>
        <p v-else>尝试其他搜索词或筛选条件</p>
        <button v-if="activeFilter !== 'all'" class="btn-ghost" @click="activeFilter = 'all'; searchQuery = ''">查看全部考纲</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { listSyllabi } from '@/api/subjectPlan'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const syllabi = ref([])
const loading = ref(true)
const searchQuery = ref('')
const activeFilter = ref('all')
const favorites = ref(loadFavorites())

// 从 localStorage 读写收藏
const FAV_KEY = 'jizhi-fav-syllabi'
function loadFavorites() {
  try { return new Set(JSON.parse(localStorage.getItem(FAV_KEY) || '[]')) }
  catch { return new Set() }
}
function saveFavorites() {
  localStorage.setItem(FAV_KEY, JSON.stringify([...favorites.value]))
}

function isFavorited(id) { return favorites.value.has(id) }
function toggleFavorite(id) {
  if (favorites.value.has(id)) { favorites.value.delete(id) }
  else { favorites.value.add(id) }
  saveFavorites()
}

const favoriteCount = computed(() => favorites.value.size)
const availableCount = computed(() => syllabi.value.filter(s => s.question_count).length)

// 搜索 + 筛选
let searchTimer = null
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {}, 0)
}

const filteredSyllabi = computed(() => {
  let list = syllabi.value

  // 筛选
  if (activeFilter.value === 'favorites') {
    list = list.filter(s => favorites.value.has(s.id))
  } else if (activeFilter.value === 'available') {
    list = list.filter(s => s.question_count)
  }

  // 搜索
  if (searchQuery.value.trim()) {
    const kw = searchQuery.value.trim().toLowerCase()
    list = list.filter(s =>
      s.name.toLowerCase().includes(kw) ||
      (s.description || '').toLowerCase().includes(kw)
    )
  }

  return list
})

onMounted(async () => {
  try {
    const res = await listSyllabi(authStore.user?.id || '')
    syllabi.value = res.syllabi || []
  } catch (e) { console.error(e) }
  finally { loading.value = false }
})

function enterSyllabus(s) {
  if (!s.question_count) return
  router.push(`/subject-plan/${s.id}`)
}
</script>

<style scoped>
/* ===== 页面基底 ===== */
.hub-page {
  min-height: 100vh; position: relative; display: flex; justify-content: center;
  padding: 40px 24px 80px;
  background: linear-gradient(135deg, #0a0e17 0%, #111827 40%, #0d1520 100%);
  color: #e2e8f0;
}
.hub-bg {
  position: fixed; inset: 0;
  background:
    radial-gradient(ellipse 60% 50% at 50% -10%, rgba(108,140,255,.06) 0%, transparent 70%),
    radial-gradient(ellipse 40% 60% at 80% 80%, rgba(139,92,246,.04) 0%, transparent 70%);
  pointer-events: none;
}

/* ===== 容器 ===== */
.hub-container { width: 100%; max-width: 960px; position: relative; z-index: 1; }

/* ===== 顶栏 ===== */
.hub-topbar { margin-bottom: 8px; }
.back-btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 8px 14px;
  border-radius: 10px; border: 1px solid rgba(255,255,255,.06);
  background: rgba(255,255,255,.03); color: #94a3b8; font-size: 13px; cursor: pointer;
  backdrop-filter: blur(12px); transition: all .25s;
}
.back-btn:hover { background: rgba(255,255,255,.06); color: #e2e8f0; border-color: rgba(255,255,255,.1); }
.back-btn svg { width: 14px; height: 14px; }

/* ===== 头部 ===== */
.hub-hero { margin-bottom: 24px; }
.hub-hero h1 { font-size: 28px; font-weight: 700; margin: 0 0 6px; letter-spacing: -.02em; }
.hub-hero p { font-size: 14px; color: #64748b; margin: 0; }

/* ===== 搜索 + 筛选工具栏 ===== */
.hub-toolbar { margin-bottom: 24px; display: flex; flex-direction: column; gap: 12px; }
.search-wrap { position: relative; }
.search-icon {
  position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
  width: 16px; height: 16px; color: #475569; pointer-events: none; z-index: 1;
}
.search-input {
  width: 100%; padding: 12px 42px 12px 42px; border-radius: 12px;
  border: 1px solid rgba(255,255,255,.06); background: rgba(255,255,255,.025);
  color: #e2e8f0; font-size: 14px; font-family: inherit; outline: none;
  backdrop-filter: blur(16px); transition: all .25s;
}
.search-input::placeholder { color: #475569; }
.search-input:focus { border-color: rgba(108,140,255,.25); background: rgba(255,255,255,.035); }
.search-clear {
  position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
  width: 22px; height: 22px; display: flex; align-items: center; justify-content: center;
  border-radius: 6px; border: none; background: rgba(255,255,255,.04); color: #64748b;
  cursor: pointer; transition: all .2s; z-index: 1;
}
.search-clear:hover { background: rgba(255,255,255,.08); color: #e2e8f0; }
.search-clear svg { width: 12px; height: 12px; }

.filter-pills { display: flex; gap: 8px; }
.pill {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 14px; border-radius: 20px; border: 1px solid rgba(255,255,255,.05);
  background: rgba(255,255,255,.02); color: #64748b; font-size: 13px;
  cursor: pointer; font-family: inherit; backdrop-filter: blur(12px);
  transition: all .25s;
}
.pill:hover { color: #94a3b8; border-color: rgba(255,255,255,.08); background: rgba(255,255,255,.04); }
.pill.active { color: #6c8cff; border-color: rgba(108,140,255,.2); background: rgba(108,140,255,.08); }
.pill svg { width: 14px; height: 14px; }
.pill-count {
  font-size: 11px; padding: 1px 6px; border-radius: 8px;
  background: rgba(255,255,255,.05); font-variant-numeric: tabular-nums;
}
.pill.active .pill-count { background: rgba(108,140,255,.12); }

/* ===== 加载态 ===== */
.hub-loading { display: flex; flex-direction: column; align-items: center; gap: 16px; padding: 80px 0; }
.loading-pulse {
  width: 40px; height: 40px; border-radius: 50%;
  background: rgba(108,140,255,.15); animation: pulse-glow 1.5s ease-in-out infinite;
}
@keyframes pulse-glow { 0%,100%{transform:scale(1);opacity:.5} 50%{transform:scale(1.3);opacity:1} }
.hub-loading span { font-size: 13px; color: #64748b; }

/* ===== 空态 ===== */
.hub-empty { text-align: center; padding: 60px 30px; }
.empty-icon { width: 48px; height: 48px; margin: 0 auto 14px; border-radius: 50%; background: rgba(255,255,255,.03); display: flex; align-items: center; justify-content: center; color: #475569; }
.empty-icon svg { width: 22px; height: 22px; }
.hub-empty h3 { font-size: 16px; margin: 0 0 6px; color: #94a3b8; }
.hub-empty p { font-size: 13px; color: #64748b; margin: 0 0 16px; }

.btn-ghost {
  display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px;
  border-radius: 10px; border: 1px solid rgba(255,255,255,.06);
  background: rgba(255,255,255,.03); color: #94a3b8; font-size: 13px;
  cursor: pointer; font-family: inherit; backdrop-filter: blur(12px); transition: all .25s;
}
.btn-ghost:hover { background: rgba(255,255,255,.06); color: #e2e8f0; border-color: rgba(255,255,255,.1); }

/* ===== 卡片网格 ===== */
.syllabi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 14px; }

/* ===== 考纲卡片 ===== */
.syllabus-card {
  position: relative; display: flex; align-items: center; gap: 16px;
  padding: 20px 22px; border-radius: 16px; cursor: pointer;
  background: rgba(255,255,255,.025); border: 1px solid rgba(255,255,255,.05);
  backdrop-filter: blur(20px); transition: all .3s cubic-bezier(.4,0,.2,1); overflow: hidden;
}
.syllabus-card:hover {
  transform: translateY(-2px); background: rgba(255,255,255,.045);
  border-color: rgba(255,255,255,.1);
  box-shadow: 0 8px 32px rgba(0,0,0,.3), 0 0 0 1px rgba(108,140,255,.08) inset;
}
.syllabus-card:active { transform: translateY(0); }
.syllabus-card.disabled { opacity: .35; cursor: not-allowed; filter: grayscale(.6); }
.syllabus-card.disabled:hover { transform: none; box-shadow: none; background: rgba(255,255,255,.025); border-color: rgba(255,255,255,.05); }

/* 卡片光晕 */
.card-glow {
  position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
  background: radial-gradient(circle at center, var(--glow-color) 0%, transparent 70%);
  opacity: 0; transition: opacity .4s; pointer-events: none;
}
.syllabus-card:hover .card-glow { opacity: .06; }

/* 缩写标 */
.card-badge {
  width: 46px; height: 46px; border-radius: 12px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 17px; font-weight: 700; color: #fff;
  box-shadow: 0 4px 12px rgba(0,0,0,.2); transition: transform .3s;
}
.syllabus-card:hover .card-badge { transform: scale(1.05); }

/* 正文 */
.card-body { flex: 1; min-width: 0; }
.card-title { font-size: 16px; font-weight: 600; margin-bottom: 4px; letter-spacing: -.01em; }
.card-desc { font-size: 12px; color: #64748b; line-height: 1.5; }

/* 右侧 */
.card-right { display: flex; flex-direction: column; align-items: flex-end; gap: 10px; flex-shrink: 0; }

/* 收藏按钮 */
.fav-btn {
  width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;
  border-radius: 8px; border: 1px solid rgba(255,255,255,.04); background: rgba(255,255,255,.02);
  color: #475569; cursor: pointer; transition: all .3s; flex-shrink: 0;
}
.fav-btn:hover { color: #ef4444; border-color: rgba(239,68,68,.15); background: rgba(239,68,68,.06); transform: scale(1.1); }
.fav-btn.favorited { color: #ef4444; border-color: rgba(239,68,68,.15); background: rgba(239,68,68,.06); }
.fav-btn.favorited:hover { color: #dc2626; transform: scale(1.1); }
.fav-btn svg { width: 14px; height: 14px; transition: transform .3s; }
.fav-btn.favorited svg { animation: heart-pop .35s ease; }
@keyframes heart-pop { 0%{transform:scale(1)} 30%{transform:scale(1.3)} 60%{transform:scale(.9)} 100%{transform:scale(1)} }

.card-stats { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.stat-count { font-size: 12px; color: #94a3b8; padding: 2px 8px; border-radius: 6px; background: rgba(255,255,255,.04); }
.stat-pending { font-size: 11px; color: #f59e0b; padding: 2px 8px; border-radius: 6px; background: rgba(245,158,11,.08); }
.stat-plan { font-size: 11px; padding: 2px 8px; border-radius: 6px; color: #94a3b8; background: rgba(255,255,255,.03); }
.stat-plan.active { color: #22c55e; background: rgba(34,197,94,.1); }
.card-arrow { width: 18px; height: 18px; color: #475569; transition: all .3s; }
.syllabus-card:hover .card-arrow { color: #94a3b8; transform: translateX(3px); }
</style>
