<template>
  <div class="search-page">
    <!-- ===== 顶栏 ===== -->
    <div class="search-nav">
      <el-button text class="nav-back" @click="router.back()">
        <i class="fas fa-arrow-left"></i>
      </el-button>
      <div class="search-box">
        <el-input
          ref="searchInputRef"
          v-model="keyword"
          placeholder="搜索聊天记录..."
          size="large"
          clearable
          @clear="onClear"
        >
          <template #prefix><i class="fas fa-search"></i></template>
        </el-input>
      </div>
      <span class="nav-cancel" @click="router.back()">取消</span>
    </div>

    <!-- ===== 搜索历史（抖音风） ===== -->
    <div v-if="!keyword.trim()" class="history-section">
      <template v-if="searchHistory.length">
        <div class="history-header">
          <span class="history-title">搜索历史</span>
          <button class="history-clear" @click="clearSearchHistory" title="清空搜索历史">
            <i class="fas fa-trash-alt"></i>
          </button>
        </div>
        <div class="history-tags">
          <span
            v-for="(kw, idx) in searchHistory"
            :key="idx"
            class="history-tag"
            @click="searchByKeyword(kw)"
          >{{ kw }}</span>
        </div>
      </template>
      <div v-else class="history-empty">暂无搜索历史</div>
    </div>

    <!-- ===== 搜索结果 ===== -->
    <div v-else class="result-section">
      <div v-if="searching" class="result-loading">
        <i class="fas fa-spinner fa-spin"></i> 搜索中...
      </div>
      <template v-else-if="results.length">
        <div class="result-count">共 {{ results.length }} 条记录</div>
        <div
          v-for="msg in results"
          :key="msg.id"
          class="result-item"
          @click="jumpToMessage(msg)"
        >
          <div class="result-avatar">
            <img
              v-if="msg.role === 'user'"
              :src="authStore.user?.avatar_url || '/default-avatar.png'"
              class="user-avatar-img"
            />
            <img v-else :src="avatarUrl" class="xiaoji-avatar-img" />
          </div>
          <div class="result-body">
            <div class="result-meta">
              <span class="result-role" :class="msg.role">{{ msg.role === 'user' ? '我' : '小基' }}</span>
              <span class="result-time">{{ formatDateTime(msg.created_at) }}</span>
            </div>
            <div class="result-content">{{ msg.content }}</div>
          </div>
        </div>
      </template>
      <div v-else class="result-empty">🔍 没有找到相关记录</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, nextTick, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getXiaojiMessages } from '@/api/xiaoji'
import { useXiaojiAvatar } from '@/composables/useXiaojiAvatar'

const router = useRouter()
const authStore = useAuthStore()
const { avatarUrl } = useXiaojiAvatar()

const keyword = ref('')
const results = ref([])
const searching = ref(false)
const searchInputRef = ref(null)

// ===== 搜索历史（本地持久化，与聊天页共享 key） =====
const SEARCH_HISTORY_KEY = 'jizhi-xiaoji-search-history'
const searchHistory = ref([])

function loadSearchHistory() {
  try {
    searchHistory.value = JSON.parse(localStorage.getItem(SEARCH_HISTORY_KEY) || '[]')
  } catch (e) {
    searchHistory.value = []
  }
}

function saveSearchKeyword(kw) {
  // 去重 + 最近优先，最多保留 10 条
  searchHistory.value = [kw, ...searchHistory.value.filter(k => k !== kw)].slice(0, 10)
  localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(searchHistory.value))
}

function clearSearchHistory() {
  searchHistory.value = []
  localStorage.removeItem(SEARCH_HISTORY_KEY)
}

// ===== 实时模糊搜索 =====
let debounceTimer = null
let searchSeq = 0

watch(keyword, (val) => {
  clearTimeout(debounceTimer)
  const kw = val.trim()
  if (!kw) {
    results.value = []
    searching.value = false
    return
  }
  debounceTimer = setTimeout(() => doSearch(kw), 350)
})

async function doSearch(kw) {
  clearTimeout(debounceTimer)
  const seq = ++searchSeq
  searching.value = true
  try {
    const res = await getXiaojiMessages(authStore.user.id, kw)
    if (seq !== searchSeq) return // 丢弃过期结果
    results.value = res.messages || []
  } catch (e) {
    if (seq !== searchSeq) return
    console.error('搜索失败:', e)
    results.value = []
  } finally {
    if (seq === searchSeq) searching.value = false
  }
}

function searchByKeyword(kw) {
  keyword.value = kw
  saveSearchKeyword(kw)
  doSearch(kw)
}

function onClear() {
  results.value = []
  searching.value = false
}

// ===== 点击结果 → 跳回聊天页定位并高亮 =====
function jumpToMessage(msg) {
  const kw = keyword.value.trim()
  if (kw) saveSearchKeyword(kw)
  if (!msg.id) return
  router.push({ path: '/home', query: { highlight: msg.id } })
}

// ===== 时间格式化 =====
function formatDateTime(iso) {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const now = new Date()
  const pad = n => String(n).padStart(2, '0')
  const hm = `${pad(d.getHours())}:${pad(d.getMinutes())}`
  const isSameDay = (a, b) =>
    a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
  if (isSameDay(d, now)) return `今天 ${hm}`
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (isSameDay(d, yesterday)) return `昨天 ${hm}`
  if (d.getFullYear() === now.getFullYear()) return `${d.getMonth() + 1}月${d.getDate()}日 ${hm}`
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${hm}`
}

onMounted(() => {
  loadSearchHistory()
  nextTick(() => searchInputRef.value?.focus())
})

onUnmounted(() => {
  clearTimeout(debounceTimer)
})
</script>

<style scoped>
.search-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-color);
  color: var(--text-primary);
  overflow: hidden;
}

/* ===== 顶栏 ===== */
.search-nav {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-color);
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  backdrop-filter: blur(12px);
}
.nav-back {
  font-size: 18px;
  color: var(--text-secondary) !important;
}
.nav-back:hover {
  color: var(--text-primary) !important;
}
.search-box {
  flex: 1;
  max-width: 480px;
}
.search-box :deep(.el-input__wrapper) {
  background: rgba(128,128,128,0.04);
  border-color: var(--border-color);
  border-radius: 12px;
}
.nav-cancel {
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  flex-shrink: 0;
}
.nav-cancel:hover {
  color: var(--text-primary);
}

/* ===== 搜索历史 ===== */
.history-section {
  padding: 20px 24px;
}
.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.history-title {
  font-size: 14px;
  color: var(--text-muted);
}
.history-clear {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 14px;
  padding: 2px 6px;
  border-radius: 6px;
  transition: all 0.2s ease;
}
.history-clear:hover {
  color: #f56c6c;
  background: rgba(245,108,108,0.08);
}
.history-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.history-tag {
  padding: 6px 16px;
  border-radius: 16px;
  font-size: 14px;
  color: var(--text-secondary);
  background: rgba(128,128,128,0.06);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s ease;
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.history-tag:hover {
  background: color-mix(in srgb, var(--brand) 8%, transparent);
  border-color: color-mix(in srgb, var(--brand) 20%, transparent);
  color: var(--brand);
}
.history-empty {
  text-align: center;
  color: var(--text-muted);
  padding: 40px 0;
  font-size: 14px;
  opacity: 0.6;
}

/* ===== 搜索结果 ===== */
.result-section {
  flex: 1;
  overflow-y: auto;
  padding: 14px 24px;
}
.result-section::-webkit-scrollbar {
  width: 3px;
}
.result-section::-webkit-scrollbar-thumb {
  background: rgba(128,128,128,0.12);
  border-radius: 2px;
}
.result-loading,
.result-empty {
  text-align: center;
  color: var(--text-muted);
  padding: 40px 0;
  font-size: 14px;
  opacity: 0.7;
}
.result-count {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 10px;
}
.result-item {
  display: flex;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  cursor: pointer;
  margin-bottom: 8px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.2s ease;
}
.result-item:hover {
  background: color-mix(in srgb, var(--brand) 6%, transparent);
  border-color: color-mix(in srgb, var(--brand) 15%, transparent);
  transform: translateY(-1px);
}
.result-avatar {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 50%;
  overflow: hidden;
}
.user-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}
.xiaoji-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}
.result-body {
  flex: 1;
  min-width: 0;
}
.result-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.result-role {
  font-size: 12px;
  padding: 1px 8px;
  border-radius: 8px;
  font-weight: 500;
}
.result-role.user {
  background: color-mix(in srgb, var(--brand) 10%, transparent);
  color: var(--brand);
}
.result-role.assistant {
  background: rgba(139,92,246,0.1);
  color: color-mix(in srgb, #8b5cf6 60%, var(--text-primary));
}
.result-time {
  font-size: 12px;
  color: var(--text-muted);
}
.result-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  word-break: break-word;
}

@media (max-width: 640px) {
  .history-section,
  .result-section {
    padding: 12px 14px;
  }
}
</style>
