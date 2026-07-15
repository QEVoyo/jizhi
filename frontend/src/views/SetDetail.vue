<template>
  <div class="set-detail-page">
    <div class="set-detail-container">
      <el-button text @click="goBack">← 返回</el-button>

      <div v-if="setData" class="set-header">
        <h2>📁 {{ setData.name }}</h2>
        <p>{{ setData.description || '无描述' }}</p >
        <div class="set-meta">
          <span>📅 {{ formatDate(setData.created_at) }}</span>
          <span>📝 {{ questionIds.length }} 道题</span>
        </div>
      </div>

      <el-divider />

      <!-- 题目列表 -->
      <div v-if="questions.length">
        <el-input v-model="searchQuery" placeholder="🔍 搜索题目" style="max-width:300px; margin-bottom:12px;" />

        <div v-for="q in filteredQuestions" :key="q.id" class="question-item">
          <div class="q-info">
            <div class="q-title">{{ q.title }}</div>
            <div class="q-meta">
              {{ getTypeDisplay(q.question_type) }} ·
              难度 {{ q.difficulty_score?.toFixed(1) || 5 }} ·
              掌握度 {{ q.mastery_score || 0 }}%
            </div>
            <el-progress
              :percentage="q.mastery_score || 0"
              :color="getColor(q.mastery_score)"
              :stroke-width="6"
              style="max-width:300px;"
            />
          </div>
          <div class="q-actions">
            <el-button size="small" type="primary" @click="practiceQuestion(q)">📝 练习</el-button>
            <el-button size="small" type="danger" @click="removeQuestion(q.id)">❌ 移除</el-button>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">📭 这个题集还没有题目</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getQuestionSetDetail, removeQuestionFromSet, getQuestionDetail } from '@/api/questions'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const setData = ref(null)
const questions = ref([])
const searchQuery = ref('')
const loading = ref(true)

const questionIds = computed(() => setData.value?.question_ids || [])

const filteredQuestions = computed(() => {
  if (!searchQuery.value) return questions.value
  return questions.value.filter(q =>
    q.title?.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

function formatDate(date) {
  if (!date) return '未知时间'
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

function getTypeDisplay(type) {
  const map = {
    choice: '选择题', fill: '填空题', judge: '判断题',
    essay: '简答题', calculation: '计算题', coding: '编程题'
  }
  return map[type] || type || '未知'
}

function getColor(score) {
  if (!score) return '#909399'
  if (score < 30) return '#FF4444'
  if (score < 50) return '#FF6B6B'
  if (score < 70) return '#FFB74D'
  if (score < 85) return '#FFD93D'
  return '#6BCB77'
}

async function loadData() {
  const id = route.query.id
  if (!id) {
    ElMessage.warning('没有找到题集')
    router.back()
    return
  }

  loading.value = true
  try {
    setData.value = await getQuestionSetDetail(id)
    const qs = []
    for (const qId of (setData.value.question_ids || [])) {
      try {
        const q = await getQuestionDetail(qId)
        if (q) qs.push(q)
      } catch {}
    }
    questions.value = qs
  } catch (error) {
    ElMessage.error('加载题集失败')
  } finally {
    loading.value = false
  }
}

async function removeQuestion(qId) {
  try {
    await ElMessageBox.confirm('确定要从题集中移除这道题吗？', '确认移除')
    await removeQuestionFromSet(setData.value.id, qId)
    questions.value = questions.value.filter(q => q.id !== qId)
    setData.value.question_ids = setData.value.question_ids.filter(id => id !== qId)
    ElMessage.success('已移除')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

// ✅ 核心修复：直接带 ID 跳转
function practiceQuestion(q) {
  sessionStorage.setItem('from_set_detail', 'true')
  router.push(`/do-question/${q.id}`)
}

function goBack() {
  router.push('/resource-lib')
}

onMounted(loadData)
</script>

<style scoped>
.set-detail-page {
  min-height: 100vh;
  padding: 20px;
  background: var(--bg-color);
}
.set-detail-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 28px;
  border-radius: 16px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
}
.set-header h2 {
  margin: 8px 0 4px;
}
.set-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--text-muted);
}
.question-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
  gap: 12px;
  flex-wrap: wrap;
}
.q-info {
  flex: 1;
}
.q-title {
  font-weight: 500;
}
.q-meta {
  font-size: 12px;
  color: var(--text-muted);
}
.q-actions {
  display: flex;
  gap: 6px;
}
.empty-state {
  color: var(--text-muted);
  padding: 24px 0;
  text-align: center;
}
</style>