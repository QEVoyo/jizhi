<template>
  <div class="mistake-book">
    <h3>📖 错题本</h3>
    <div class="stats">
      <span>📚 学习中：{{ learningCount }}</span>
      <span>✅ 已攻克：{{ conqueredCount }}</span>
    </div>

    <el-divider />

    <el-tabs v-model="mistakeTab">
      <el-tab-pane label="📖 学习中" name="learning">
        <div v-if="learningMistakes.length">
          <div v-for="m in learningMistakes" :key="m.id" class="mistake-item">
            <div class="mistake-info">
              <div class="mistake-title">{{ m.title }}</div>
              <div class="mistake-meta">
                题型：{{ getTypeDisplay(m.question_type) }} · 加入时间：{{ formatDate(m.mistake_added_at) }}
              </div>
              <el-progress
                :percentage="m.mastery_score || 0"
                :color="getColor(m.mastery_score)"
                :stroke-width="6"
              />
            </div>
            <el-button type="primary" size="small" class="review-btn" @click="reviewMistake(m)">
              📝 复习
            </el-button>
          </div>
        </div>
        <div v-else class="empty-state">🎉 没有学习中的错题，继续加油！</div>
      </el-tab-pane>

      <el-tab-pane label="✅ 已攻克" name="conquered">
        <div v-if="conqueredMistakes.length">
          <div v-for="m in conqueredMistakes" :key="m.id" class="mistake-item">
            <div class="mistake-info">
              <div class="mistake-title">{{ m.title }}</div>
              <div class="mistake-meta">题型：{{ getTypeDisplay(m.question_type) }}</div>
              <el-progress
                :percentage="m.mastery_score || 0"
                :color="getColor(m.mastery_score)"
                :stroke-width="6"
              />
            </div>
            <el-button type="primary" size="small" class="review-btn" @click="reviewMistake(m)">
              📝 复习
            </el-button>
          </div>
        </div>
        <div v-else class="empty-state">📭 暂无已攻克的错题</div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getMistakes } from '@/api/questions'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const router = useRouter()
const authStore = useAuthStore()

const mistakes = ref([])
const mistakeTab = ref('learning')

const learningMistakes = computed(() =>
  mistakes.value.filter(m => m.mistake_status === 'learning')
)
const conqueredMistakes = computed(() =>
  mistakes.value.filter(m => m.mistake_status === 'conquered')
)
const learningCount = computed(() => learningMistakes.value.length)
const conqueredCount = computed(() => conqueredMistakes.value.length)

const typeDisplayMap = {
  choice: '选择题',
  fill: '填空题',
  judge: '判断题',
  essay: '简答题/论述题',
  calculation: '计算题',
  coding: '编程题'
}

function getTypeDisplay(type) {
  return typeDisplayMap[type] || type || '未知'
}

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

async function loadMistakes() {
  try {
    mistakes.value = await getMistakes(authStore.user.id)
  } catch (error) {
    ElMessage.error('加载错题失败')
  }
}

function reviewMistake(mistake) {
  // ✅ 直接带 ID 跳转，绝不生成新题
  router.push(`/do-question/${mistake.id}`)
}

onMounted(loadMistakes)
</script>

<style scoped>
.mistake-book {
  padding: 4px 0;
}

.stats {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: var(--text-secondary);
}

.mistake-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-radius: 12px;
  border: 1px solid var(--border-color);
  margin-bottom: 10px;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: default;
  background: var(--card-bg);
}
.mistake-item:hover {
  transform: translateY(-3px) scale(1.01);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.06);
  border-color: rgba(128, 128, 128, 0.15);
}
[data-theme="dark"] .mistake-item:hover {
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.3);
}

.mistake-info {
  flex: 1;
}
.mistake-title {
  font-weight: 500;
  color: var(--text-primary);
}
.mistake-meta {
  font-size: 12px;
  color: var(--text-muted);
  margin: 4px 0 6px;
}

.review-btn {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
  flex-shrink: 0;
}
.review-btn:hover {
  transform: translateY(-2px) scale(1.05);
}
.review-btn:active {
  transform: scale(0.95);
}

.empty-state {
  color: var(--text-muted);
  padding: 24px 0;
  text-align: center;
}

[data-theme="dark"] .mistake-item {
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.06);
}
[data-theme="dark"] .mistake-item:hover {
  border-color: rgba(255, 255, 255, 0.12);
}

@media (max-width: 640px) {
  .mistake-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  .review-btn {
    width: 100%;
  }
}
</style>