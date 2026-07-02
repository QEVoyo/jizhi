<template>
  <div class="mastery-page">
    <!-- 顶部 -->
    <div class="mastery-topbar">
      <el-button text @click="goBack" class="back-btn">
        <i class="fas fa-arrow-left"></i> 返回资源库
      </el-button>
      <h1>📊 掌握度看板</h1>
      <p class="subtitle">查看各知识点的掌握程度，针对性强化薄弱环节</p>
    </div>

    <!-- ===== 统计摘要（实时联动） ===== -->
    <div class="stats-row">
      <div
        class="stat-card weak"
        :class="{ active: activeFilter === 'weak' }"
        @click="activeFilter = 'weak'"
      >
        <span class="stat-number">{{ weakCount }}</span>
        <span class="stat-label">🔴 薄弱</span>
        <span class="stat-desc">需要重点攻克</span>
      </div>
      <div
        class="stat-card consolidate"
        :class="{ active: activeFilter === 'consolidate' }"
        @click="activeFilter = 'consolidate'"
      >
        <span class="stat-number">{{ consolidateCount }}</span>
        <span class="stat-label">🟡 待巩固</span>
        <span class="stat-desc">需要加强练习</span>
      </div>
      <div
        class="stat-card strong"
        :class="{ active: activeFilter === 'strong' }"
        @click="activeFilter = 'strong'"
      >
        <span class="stat-number">{{ strongCount }}</span>
        <span class="stat-label">🟢 优势</span>
        <span class="stat-desc">保持状态</span>
      </div>
      <div
        class="stat-card total"
        :class="{ active: activeFilter === 'all' }"
        @click="activeFilter = 'all'"
      >
        <span class="stat-number">{{ totalCount }}</span>
        <span class="stat-label">📚 总计</span>
        <span class="stat-desc">全部知识点</span>
      </div>
    </div>

    <!-- ===== 颜色图例 ===== -->
    <div class="color-legend">
      <span>0%</span>
      <div class="legend-bar" />
      <span>100%</span>
      <span class="legend-hint">薄弱 &lt;60% &nbsp;|&nbsp; 待巩固 60-80% &nbsp;|&nbsp; 优势 ≥80%</span>
    </div>

    <!-- ===== 搜索和排序 ===== -->
    <div class="filter-row">
      <el-input
        v-model="searchQuery"
        placeholder="🔍 搜索知识点"
        style="max-width:300px;"
        clearable
        class="filter-input"
      />
      <div class="select-wrapper">
        <div class="custom-select" @click.stop="sortMenuVisible = !sortMenuVisible" ref="sortRef">
          <span class="select-display">{{ sortLabel }}</span>
          <i class="fas fa-chevron-down select-arrow" :class="{ rotated: sortMenuVisible }"></i>
        </div>
        <div v-if="sortMenuVisible" class="custom-select-dropdown" @click.stop>
          <div
            v-for="opt in sortOptions"
            :key="opt.value"
            class="select-option"
            :class="{ active: sortType === opt.value }"
            @click="selectSort(opt.value)"
          >
            {{ opt.label }}
          </div>
        </div>
      </div>
      <el-button text @click="resetFilters" style="color:var(--text-muted);">
        <i class="fas fa-undo"></i> 重置
      </el-button>
    </div>

    <!-- ===== 三类卡片 ===== -->
    <div v-if="loading" class="loading-text">加载中...</div>
    <div v-else-if="displayData.length" class="sections">
      <!-- 薄弱 -->
      <div v-if="displayWeak.length && showSection('weak')" class="section">
        <div class="section-header">
          <span class="section-title weak-title">🔴 薄弱</span>
          <span class="section-count">{{ displayWeak.length }} 个知识点需要攻克</span>
        </div>
        <div class="card-grid">
          <div
            v-for="p in displayWeak"
            :key="p.topic"
            class="topic-card weak-card"
            :style="{
              background: `linear-gradient(145deg, ${getColor(p.mastery_score)}, ${getColorDark(p.mastery_score)})`,
              boxShadow: `0 4px 20px ${getColor(p.mastery_score)}50`
            }"
          >
            <span class="topic-name">{{ p.topic }}</span>
            <span class="topic-score">{{ p.mastery_score }}%</span>
            <span class="topic-badge">🔴 薄弱</span>
            <el-button size="small" class="card-btn" @click="goPractice(p.topic)">
              🎯 练习
            </el-button>
          </div>
        </div>
      </div>

      <!-- 待巩固 -->
      <div v-if="displayConsolidate.length && showSection('consolidate')" class="section">
        <div class="section-header">
          <span class="section-title consolidate-title">🟡 待巩固</span>
          <span class="section-count">{{ displayConsolidate.length }} 个知识点需要巩固</span>
        </div>
        <div class="card-grid">
          <div
            v-for="p in displayConsolidate"
            :key="p.topic"
            class="topic-card consolidate-card"
            :style="{
              background: `linear-gradient(145deg, ${getColor(p.mastery_score)}, ${getColorDark(p.mastery_score)})`,
              boxShadow: `0 4px 20px ${getColor(p.mastery_score)}50`
            }"
          >
            <span class="topic-name">{{ p.topic }}</span>
            <span class="topic-score">{{ p.mastery_score }}%</span>
            <span class="topic-badge">🟡 待巩固</span>
            <el-button size="small" class="card-btn" @click="goPractice(p.topic)">
              📝 练习
            </el-button>
          </div>
        </div>
      </div>

      <!-- 优势 -->
      <div v-if="displayStrong.length && showSection('strong')" class="section">
        <div class="section-header">
          <span class="section-title strong-title">🟢 优势</span>
          <span class="section-count">{{ displayStrong.length }} 个知识点已掌握</span>
        </div>
        <div class="card-grid">
          <div
            v-for="p in displayStrong"
            :key="p.topic"
            class="topic-card strong-card"
            :style="{
              background: `linear-gradient(145deg, ${getColor(p.mastery_score)}, ${getColorDark(p.mastery_score)})`,
              boxShadow: `0 4px 20px ${getColor(p.mastery_score)}50`
            }"
          >
            <span class="topic-name">{{ p.topic }}</span>
            <span class="topic-score">{{ p.mastery_score }}%</span>
            <span class="topic-badge">🟢 优势</span>
            <el-button size="small" class="card-btn" @click="goPractice(p.topic)">
              📖 复习
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">📭 没有匹配的知识点</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getMastery } from '@/api/questions'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const masteryData = ref([])
const searchQuery = ref('')
const sortType = ref('low')
const activeFilter = ref('all')
const loading = ref(true)

// ===== 排序下拉 =====
const sortMenuVisible = ref(false)
const sortRef = ref(null)
const sortOptions = [
  { value: 'low', label: '掌握度（低→高）' },
  { value: 'high', label: '掌握度（高→低）' },
  { value: 'az', label: '名称（A→Z）' },
  { value: 'za', label: '名称（Z→A）' }
]
const sortLabel = computed(() => {
  const found = sortOptions.find(o => o.value === sortType.value)
  return found ? found.label : '排序方式'
})

function selectSort(value) {
  sortType.value = value
  sortMenuVisible.value = false
}

function handleClickOutside(event) {
  if (sortRef.value && !sortRef.value.contains(event.target)) {
    sortMenuVisible.value = false
  }
}

// ===== 三组原始数据 =====
const weakData = computed(() =>
  masteryData.value.filter(p => p.mastery_score < 60)
)
const consolidateData = computed(() =>
  masteryData.value.filter(p => p.mastery_score >= 60 && p.mastery_score < 80)
)
const strongData = computed(() =>
  masteryData.value.filter(p => p.mastery_score >= 80)
)

// ===== 搜索过滤 =====
function filterData(data) {
  if (!searchQuery.value) return data
  return data.filter(p =>
    p.topic.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
}

// ===== 排序 =====
function sortData(data) {
  const sorted = [...data]
  if (sortType.value === 'low') {
    sorted.sort((a, b) => a.mastery_score - b.mastery_score)
  } else if (sortType.value === 'high') {
    sorted.sort((a, b) => b.mastery_score - a.mastery_score)
  } else if (sortType.value === 'az') {
    sorted.sort((a, b) => a.topic.localeCompare(b.topic))
  } else if (sortType.value === 'za') {
    sorted.sort((a, b) => b.topic.localeCompare(a.topic))
  }
  return sorted
}

// ===== 最终显示数据（搜索 + 排序） =====
const displayWeak = computed(() => sortData(filterData(weakData.value)))
const displayConsolidate = computed(() => sortData(filterData(consolidateData.value)))
const displayStrong = computed(() => sortData(filterData(strongData.value)))
const displayData = computed(() =>
  [...displayWeak.value, ...displayConsolidate.value, ...displayStrong.value]
)

// ===== 统计数字（实时联动） =====
const weakCount = computed(() => displayWeak.value.length)
const consolidateCount = computed(() => displayConsolidate.value.length)
const strongCount = computed(() => displayStrong.value.length)
const totalCount = computed(() => displayData.value.length)

// ===== 显示分区 =====
function showSection(type) {
  if (activeFilter.value === 'all') return true
  return activeFilter.value === type
}

// ===== 重置 =====
function resetFilters() {
  searchQuery.value = ''
  sortType.value = 'low'
  activeFilter.value = 'all'
}

// ===== 20种颜色 =====
function getColor(score) {
  if (score < 5) return '#FF0000'
  if (score < 10) return '#FF1A00'
  if (score < 15) return '#FF3300'
  if (score < 20) return '#FF4D00'
  if (score < 25) return '#FF6600'
  if (score < 30) return '#FF8000'
  if (score < 35) return '#FF9900'
  if (score < 40) return '#FFB300'
  if (score < 45) return '#FFCC00'
  if (score < 50) return '#FFE600'
  if (score < 55) return '#D4E000'
  if (score < 60) return '#A8D500'
  if (score < 65) return '#7DCC00'
  if (score < 70) return '#52C200'
  if (score < 75) return '#26B800'
  if (score < 80) return '#00AD00'
  if (score < 85) return '#00A300'
  if (score < 90) return '#009900'
  if (score < 95) return '#008000'
  return '#006600'
}

function getColorDark(score) {
  if (score < 5) return '#CC0000'
  if (score < 10) return '#CC1500'
  if (score < 15) return '#CC2A00'
  if (score < 20) return '#CC3E00'
  if (score < 25) return '#CC5200'
  if (score < 30) return '#CC6600'
  if (score < 35) return '#CC7A00'
  if (score < 40) return '#CC8F00'
  if (score < 45) return '#CCA300'
  if (score < 50) return '#CCB800'
  if (score < 55) return '#A9B300'
  if (score < 60) return '#86AA00'
  if (score < 65) return '#64A100'
  if (score < 70) return '#419800'
  if (score < 75) return '#1E8F00'
  if (score < 80) return '#008A00'
  if (score < 85) return '#008200'
  if (score < 90) return '#007A00'
  if (score < 95) return '#006600'
  return '#005200'
}

async function loadData() {
  loading.value = true
  try {
    masteryData.value = await getMastery(authStore.user.id)
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

function goPractice(topic) {
  router.push({ path: '/generate-from-mastery', query: { topic } })
}

function goBack() {
  router.push('/resource-lib')
}

onMounted(() => {
  loadData()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.mastery-page {
  min-height: 100vh;
  padding: 24px 32px 120px 32px;
}

.mastery-topbar {
  margin-bottom: 24px;
}
.mastery-topbar h1 {
  font-size: 28px;
  color: var(--text-primary);
  margin: 4px 0 2px;
}
.mastery-topbar .subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  opacity: 0.6;
}
.back-btn {
  color: var(--text-secondary) !important;
  transition: all 0.3s ease !important;
  padding-left: 0 !important;
}
.back-btn:hover {
  color: var(--text-primary) !important;
  transform: translateX(-4px) scale(1.02);
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  padding: 18px 16px;
  border-radius: 14px;
  text-align: center;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  border: 2px solid transparent;
  transition: all 0.4s ease;
  cursor: pointer;
}
.stat-card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.08);
}
.stat-card:active {
  transform: scale(0.97);
}
.stat-card.active {
  border-color: var(--text-primary);
  background: rgba(255, 255, 255, 0.10);
}
[data-theme="dark"] .stat-card {
  background: rgba(0, 0, 0, 0.2);
  border-color: transparent;
}
[data-theme="dark"] .stat-card:hover {
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.3);
}
[data-theme="dark"] .stat-card.active {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.15);
}

.stat-card.weak { border-left: 4px solid #FF4444; }
.stat-card.consolidate { border-left: 4px solid #FFB74D; }
.stat-card.strong { border-left: 4px solid #6BCB77; }
.stat-card.total { border-left: 4px solid #409eff; }
.stat-card.weak.active { border: 2px solid #FF4444; }
.stat-card.consolidate.active { border: 2px solid #FFB74D; }
.stat-card.strong.active { border: 2px solid #6BCB77; }
.stat-card.total.active { border: 2px solid #409eff; }

.stat-number {
  display: block;
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
}
.stat-label {
  display: block;
  font-size: 15px;
  font-weight: 500;
  margin-top: 2px;
}
.stat-desc {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}
.stat-card.weak .stat-label { color: #FF4444; }
.stat-card.consolidate .stat-label { color: #FFB74D; }
.stat-card.strong .stat-label { color: #6BCB77; }
.stat-card.total .stat-label { color: #409eff; }

.color-legend {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
  padding: 10px 16px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.05);
}
[data-theme="dark"] .color-legend {
  background: rgba(0, 0, 0, 0.15);
}
.color-legend span {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}
.legend-bar {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  background: linear-gradient(to right,
    #FF0000, #FF1A00, #FF4400, #FF6E00, #FF9900,
    #FFC400, #D4E000, #A8D500, #66CC33, #00CC66
  );
}
.legend-hint {
  font-size: 12px !important;
  color: var(--text-muted) !important;
}

.filter-row {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: center;
}
.filter-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-color);
}
[data-theme="dark"] .filter-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.03);
}
.filter-input :deep(.el-input__inner) {
  color: var(--text-primary);
}

.select-wrapper {
  position: relative;
  display: inline-block;
  min-width: 180px;
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
  max-height: 200px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.10);
  backdrop-filter: blur(20px);
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

.sections {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.section-title {
  font-size: 18px;
  font-weight: 600;
}
.section-title.weak-title { color: #FF4444; }
.section-title.consolidate-title { color: #FFB74D; }
.section-title.strong-title { color: #6BCB77; }
.section-count {
  font-size: 13px;
  color: var(--text-muted);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 16px;
}

.topic-card {
  padding: 18px 14px;
  border-radius: 14px;
  color: white;
  text-align: center;
  transition: all 0.4s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  min-height: 130px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.topic-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, rgba(255,255,255,0.12) 0%, transparent 100%);
  pointer-events: none;
  border-radius: 14px;
}
.topic-card:hover {
  transform: translateY(-6px) scale(1.03);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2) !important;
}
.topic-card:active {
  transform: scale(0.97);
}

.topic-name {
  font-size: 15px;
  font-weight: 500;
  text-shadow: 0 1px 8px rgba(0,0,0,0.15);
  position: relative;
  z-index: 1;
}
.topic-score {
  font-size: 30px;
  font-weight: 700;
  text-shadow: 0 1px 8px rgba(0,0,0,0.15);
  margin: 4px 0;
  position: relative;
  z-index: 1;
}
.topic-badge {
  font-size: 12px;
  opacity: 0.85;
  text-shadow: 0 1px 4px rgba(0,0,0,0.15);
  position: relative;
  z-index: 1;
}
.card-btn {
  margin-top: 8px;
  color: white !important;
  border-color: rgba(255,255,255,0.3) !important;
  background: rgba(255,255,255,0.1) !important;
  transition: all 0.3s ease !important;
  position: relative;
  z-index: 1;
}
.card-btn:hover {
  background: rgba(255,255,255,0.25) !important;
  transform: scale(1.08) translateY(-2px);
}
.card-btn:active {
  transform: scale(0.95);
}

.empty-state {
  color: var(--text-muted);
  padding: 40px 0;
  text-align: center;
  font-size: 16px;
}
.loading-text {
  color: var(--text-muted);
  padding: 40px 0;
  text-align: center;
}

@media (max-width: 768px) {
  .mastery-page {
    padding: 16px 14px 100px 14px;
  }
  .mastery-topbar h1 {
    font-size: 22px;
  }
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .card-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
  .filter-row {
    flex-direction: column;
  }
  .filter-row :deep(.el-input) {
    max-width: 100% !important;
    width: 100%;
  }
  .select-wrapper {
    width: 100%;
    min-width: unset;
  }
  .custom-select {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .stats-row {
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
  .stat-card {
    padding: 12px 10px;
  }
  .stat-number {
    font-size: 24px;
  }
  .card-grid {
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
  .topic-card {
    min-height: 110px;
    padding: 14px 10px;
  }
  .topic-score {
    font-size: 24px;
  }
}
</style>