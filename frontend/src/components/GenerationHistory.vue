<template>
  <div class="generation-history">
    <h3>📜 生成历史</h3>

    <div class="filter-row">
      <el-input
        v-model="searchQuery"
        placeholder="🔍 搜索题目"
        style="max-width:300px;"
        class="form-input"
      />
      <div class="select-wrapper">
        <div class="custom-select" @click.stop="filterMenuVisible = !filterMenuVisible" ref="filterRef">
          <span class="select-display">{{ typeFilterLabel }}</span>
          <i class="fas fa-chevron-down select-arrow" :class="{ rotated: filterMenuVisible }"></i>
        </div>
        <div v-if="filterMenuVisible" class="custom-select-dropdown" @click.stop>
          <div
            v-for="t in filterOptions"
            :key="t.value"
            class="select-option"
            :class="{ active: typeFilter === t.value }"
            @click="selectTypeFilter(t.value)"
          >
            {{ t.label }}
          </div>
        </div>
      </div>
    </div>

    <div v-if="filteredHistory.length">
      <div v-for="h in filteredHistory" :key="h.id || h.created_at" class="history-item">
        <div class="history-info">
          <div class="history-title">{{ h.title }}</div>
          <div class="history-meta">
            {{ getTypeDisplay(h.question_type) }} · {{ h.category || '未分类' }} · {{ h.topic || '' }}
          </div>
        </div>
        <div class="history-right">
          <div class="history-time">{{ formatDate(h.created_at) }}</div>
          <div class="history-status">{{ getStatus(h.status) }}</div>
          <el-button size="small" type="primary" class="practice-btn" @click="practiceHistory(h)">
            📝 练习
          </el-button>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">📭 暂无生成记录，去生成一道题目吧！</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getGenerationHistory, getQuestionDetail } from '@/api/questions'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const router = useRouter()
const authStore = useAuthStore()

const history = ref([])
const searchQuery = ref('')
const typeFilter = ref('all')
const filterMenuVisible = ref(false)
const filterRef = ref(null)
const loading = ref(false)

const filterOptions = [
  { value: 'all', label: '全部' },
  { value: 'choice', label: '选择题' },
  { value: 'fill', label: '填空题' },
  { value: 'judge', label: '判断题' },
  { value: 'essay', label: '简答题' },
  { value: 'calculation', label: '计算题' },
  { value: 'coding', label: '编程题' }
]

const typeFilterLabel = computed(() => {
  const found = filterOptions.find(o => o.value === typeFilter.value)
  return found ? found.label : '全部题型'
})

function selectTypeFilter(value) {
  typeFilter.value = value
  filterMenuVisible.value = false
}

const filteredHistory = computed(() => {
  let result = history.value
  if (searchQuery.value) {
    result = result.filter(h =>
      h.title?.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  if (typeFilter.value !== 'all') {
    result = result.filter(h => h.question_type === typeFilter.value)
  }
  return result
})

const typeDisplayMap = {
  choice: '选择题',
  fill: '填空题',
  judge: '判断题',
  essay: '简答题',
  calculation: '计算题',
  coding: '编程题'
}

function getTypeDisplay(type) {
  return typeDisplayMap[type] || type || '未知'
}

function formatDate(date) {
  if (!date) return ''
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

function getStatus(status) {
  const map = {
    pending: '🔄 待练习',
    practiced: '📖 已练习',
    mastered: '✅ 已掌握'
  }
  return map[status] || '🔄 待练习'
}

async function loadHistory() {
  loading.value = true
  try {
    history.value = await getGenerationHistory(authStore.user.id)
  } catch (error) {
    ElMessage.error('加载历史失败')
  } finally {
    loading.value = false
  }
}

async function practiceHistory(h) {
  try {
    const question = await getQuestionDetail(h.question_id)
    sessionStorage.setItem('current_question', JSON.stringify(question))
    router.push('/do-question')
  } catch (error) {
    ElMessage.error('加载题目失败')
  }
}

function handleClickOutside(event) {
  if (filterRef.value && !filterRef.value.contains(event.target)) {
    filterMenuVisible.value = false
  }
}

onMounted(() => {
  loadHistory()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.generation-history {
  padding: 4px 0;
}
.generation-history h3 {
  margin-bottom: 12px;
  color: var(--text-primary);
}

.filter-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  align-items: center;
}

.form-input {
  transition: all 0.3s ease;
}
.form-input:hover {
  transform: scale(1.01);
}

.select-wrapper {
  position: relative;
  display: inline-block;
  min-width: 130px;
}

.custom-select {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-secondary);
  font-size: 14px;
  user-select: none;
  min-height: 40px;
  position: relative;
}
.custom-select:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
}
[data-theme="dark"] .custom-select {
  background: rgba(255, 255, 255, 0.03);
}

.select-display {
  color: var(--text-primary);
}

.select-arrow {
  font-size: 12px;
  color: var(--text-muted);
  transition: transform 0.3s ease;
}
.select-arrow.rotated {
  transform: rotate(180deg);
}

.custom-select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  min-width: 100%;
  background: rgba(255, 255, 255, 0.10);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 4px 0;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}
[data-theme="dark"] .custom-select-dropdown {
  background: rgba(0, 0, 0, 0.35);
}

.select-option {
  padding: 8px 14px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all 0.2s ease;
  border-radius: 6px;
  margin: 2px 4px;
}
.select-option:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-primary);
}
.select-option.active {
  background: rgba(255, 255, 255, 0.10);
  color: var(--text-primary);
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  margin-bottom: 10px;
  transition: all 0.3s ease;
  gap: 12px;
  flex-wrap: wrap;
  background: var(--card-bg);
}
.history-item:hover {
  transform: translateY(-3px) scale(1.01);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.06);
  border-color: rgba(128, 128, 128, 0.15);
}
[data-theme="dark"] .history-item:hover {
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.3);
}

.history-info {
  flex: 1;
  min-width: 150px;
}
.history-title {
  font-weight: 500;
  color: var(--text-primary);
}
.history-meta {
  font-size: 12px;
  color: var(--text-muted);
}

.history-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.history-time {
  font-size: 12px;
  color: var(--text-muted);
}
.history-status {
  font-size: 13px;
}

.practice-btn {
  transition: all 0.3s ease !important;
}
.practice-btn:hover {
  transform: translateY(-2px) scale(1.05);
}
.practice-btn:active {
  transform: scale(0.95);
}

.empty-state {
  color: var(--text-muted);
  padding: 24px 0;
  text-align: center;
}

[data-theme="dark"] .history-item {
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.06);
}
[data-theme="dark"] .history-item:hover {
  border-color: rgba(255, 255, 255, 0.12);
}

@media (max-width: 640px) {
  .history-item {
    flex-direction: column;
    align-items: flex-start;
  }
  .history-right {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>