<template>
  <div class="question-sets">
    <h3>📁 我的题集</h3>

    <!-- 创建题集 - 改成普通展开区域 -->
    <div class="create-section">
      <div class="create-header" @click="createOpen = !createOpen">
        <span>➕ 创建新题集</span>
        <i class="fas fa-chevron-down" :class="{ rotated: createOpen }"></i>
      </div>
      <div v-if="createOpen" class="create-body">
        <div class="create-row">
          <el-input
            v-model="newSetName"
            placeholder="题集名称"
            class="create-input"
          />
          <el-input
            v-model="newSetDesc"
            placeholder="描述（可选）"
            class="create-input"
          />
          <el-button type="primary" class="create-btn" @click="handleCreateSet">
            ✨ 创建
          </el-button>
        </div>
      </div>
    </div>

    <el-divider />

    <!-- 搜索 -->
    <el-input
      v-model="searchQuery"
      placeholder="🔍 搜索题集"
      style="max-width:300px; margin-bottom:12px;"
      class="search-input"
    />

    <!-- 题集列表 -->
    <div v-if="sets.length" class="set-list">
      <div v-for="set in filteredSets" :key="set.id" class="set-item">
        <div class="set-info">
          <div class="set-name">{{ set.name }}</div>
          <div class="set-meta">{{ set.description || '无描述' }} · 📅 {{ formatDate(set.created_at) }} · 📝 {{ set.question_ids?.length || 0 }} 道题</div>
          <el-progress
            :percentage="set.avg_mastery || 0"
            :color="getColor(set.avg_mastery)"
            :stroke-width="6"
          />
        </div>
        <div class="set-actions">
          <el-button size="small" class="view-btn" @click="viewSet(set.id)">📖 查看</el-button>
          <el-button size="small" type="danger" class="delete-btn" @click="deleteSet(set.id)">🗑️ 删除</el-button>
          <el-button
            v-if="set.question_ids?.length"
            size="small"
            type="success"
            class="practice-set-btn"
            @click="practiceSet(set)"
          >
            🎯 练习
          </el-button>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">📭 暂无题集，点击上方创建</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getQuestionSets, createQuestionSet, deleteQuestionSet, getQuestionDetail } from '@/api/questions'
import { recordAction } from '@/api/career'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'

const router = useRouter()
const authStore = useAuthStore()

const sets = ref([])
const loading = ref(false)
const createOpen = ref(false)
const newSetName = ref('')
const newSetDesc = ref('')
const searchQuery = ref('')

const filteredSets = computed(() => {
  if (!searchQuery.value) return sets.value
  return sets.value.filter(s => s.name.toLowerCase().includes(searchQuery.value.toLowerCase()))
})

function formatDate(date) {
  if (!date) return '未知时间'
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

function getColor(score) {
  if (!score) return '#909399'
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

async function calculateAvgMastery(set) {
  const questionIds = set.question_ids || []
  if (!questionIds.length) {
    set.avg_mastery = 0
    return
  }
  let total = 0
  let count = 0
  for (const qId of questionIds) {
    try {
      const q = await getQuestionDetail(qId)
      if (q && q.mastery_score !== undefined) {
        total += q.mastery_score
        count++
      }
    } catch (e) {}
  }
  set.avg_mastery = count > 0 ? Math.round(total / count) : 0
}

async function loadSets() {
  loading.value = true
  try {
    const data = await getQuestionSets(authStore.user.id)
    for (const set of data) {
      await calculateAvgMastery(set)
    }
    sets.value = data
  } catch (error) {
    ElMessage.error('加载题集失败')
  } finally {
    loading.value = false
  }
}

watch(sets, (newVal) => {
  console.log('题集已更新，重新计算加权平均')
}, { deep: true })

async function handleCreateSet() {
  if (!newSetName.value) {
    ElMessage.warning('请输入题集名称')
    return
  }
  try {
    await createQuestionSet(authStore.user.id, {
      name: newSetName.value,
      description: newSetDesc.value
    })
    await recordAction(authStore.user.id, 'create_set')
    ElMessage.success(`✅ 题集「${newSetName.value}」创建成功`)
    newSetName.value = ''
    newSetDesc.value = ''
    createOpen.value = false
    await loadSets()
  } catch (error) {
    ElMessage.error('创建失败')
  }
}

async function deleteSet(id) {
  try {
    await ElMessageBox.confirm('确定要删除这个题集吗？', '确认删除', {
      type: 'warning'
    })
    await deleteQuestionSet(id)
    ElMessage.success('已删除')
    await loadSets()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function viewSet(id) {
  router.push({ path: '/set-detail', query: { id } })
}

function practiceSet(set) {
  sessionStorage.setItem('practice_set', JSON.stringify(set))
  router.push('/do-question')
}

onMounted(loadSets)
</script>

<style scoped>
.question-sets {
  padding: 4px 0;
}

/* ===== 创建题集 - 普通展开 ===== */
.create-section {
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: rgba(255, 255, 255, 0.04);
  overflow: hidden;
  margin-bottom: 16px;
}
[data-theme="dark"] .create-section {
  background: rgba(255, 255, 255, 0.02);
}

.create-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.3s ease;
}
.create-header:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
}
.create-header .fa-chevron-down {
  transition: transform 0.3s ease;
  font-size: 12px;
  color: var(--text-muted);
}
.create-header .fa-chevron-down.rotated {
  transform: rotate(180deg);
}

.create-body {
  padding: 0 16px 16px;
}
.create-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.create-input {
  flex: 1;
  min-width: 160px;
}
.create-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-color);
}
[data-theme="dark"] .create-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.03);
}
.create-input :deep(.el-input__inner) {
  color: var(--text-primary);
}
.create-btn {
  transition: all 0.3s ease !important;
  border-radius: 10px !important;
}
.create-btn:hover {
  transform: translateY(-2px) scale(1.03) !important;
}
.create-btn:active {
  transform: scale(0.95) !important;
}

/* ===== 搜索框 ===== */
.search-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-color);
}
[data-theme="dark"] .search-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.03);
}
.search-input :deep(.el-input__inner) {
  color: var(--text-primary);
}

/* ===== 题集列表 ===== */
.set-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.set-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  background: var(--card-bg);
  transition: all 0.3s ease;
  gap: 12px;
  flex-wrap: wrap;
}
.set-item:hover {
  transform: translateY(-3px) scale(1.01);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.06);
  border-color: rgba(128, 128, 128, 0.15);
}
[data-theme="dark"] .set-item:hover {
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.3);
}

.set-info {
  flex: 1;
  min-width: 200px;
}
.set-name {
  font-weight: 600;
  color: var(--text-primary);
}
.set-meta {
  font-size: 12px;
  color: var(--text-muted);
  margin: 4px 0 6px;
}

.set-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.set-actions .el-button {
  transition: all 0.3s ease !important;
}
.set-actions .el-button:hover {
  transform: translateY(-2px) scale(1.05);
}
.set-actions .el-button:active {
  transform: scale(0.95);
}

.empty-state {
  color: var(--text-muted);
  padding: 20px 0;
  text-align: center;
}

[data-theme="dark"] .set-item {
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.06);
}
[data-theme="dark"] .set-item:hover {
  border-color: rgba(255, 255, 255, 0.12);
}

@media (max-width: 640px) {
  .set-item {
    flex-direction: column;
    align-items: flex-start;
  }
  .set-actions {
    width: 100%;
  }
  .set-actions .el-button {
    flex: 1;
  }
  .create-row {
    flex-direction: column;
  }
  .create-input {
    min-width: unset;
  }
}
</style>