<template>
  <div class="generate-form">
    <h3>🤖 生成新题目</h3>
    <el-form :model="form" label-width="100px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="学科/领域">
            <el-input v-model="form.category" placeholder="例：Python、数学..." class="form-input" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="具体知识点">
            <el-input v-model="form.topic" placeholder="例：列表推导式..." class="form-input" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="题型">
            <div class="select-wrapper">
              <div class="custom-select" @click.stop="questionTypeMenuVisible = !questionTypeMenuVisible" ref="typeRef">
                <span class="select-display">{{ questionTypeLabel }}</span>
                <i class="fas fa-chevron-down select-arrow" :class="{ rotated: questionTypeMenuVisible }"></i>
              </div>
              <div v-if="questionTypeMenuVisible" class="custom-select-dropdown" @click.stop>
                <div
                  v-for="t in questionTypes"
                  :key="t"
                  class="select-option"
                  :class="{ active: form.questionType === t }"
                  @click="selectQuestionType(t)"
                >
                  {{ t }}
                </div>
              </div>
            </div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="难度">
            <div class="select-wrapper">
              <div class="custom-select" @click.stop="difficultyMenuVisible = !difficultyMenuVisible" ref="diffRef">
                <span class="select-display">{{ form.difficulty }}</span>
                <i class="fas fa-chevron-down select-arrow" :class="{ rotated: difficultyMenuVisible }"></i>
              </div>
              <div v-if="difficultyMenuVisible" class="custom-select-dropdown" @click.stop>
                <div
                  v-for="d in difficultyOptions"
                  :key="d"
                  class="select-option"
                  :class="{ active: form.difficulty === d }"
                  @click="selectDifficulty(d)"
                >
                  {{ d }}
                </div>
              </div>
            </div>
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="补充说明">
        <el-input v-model="form.extra" type="textarea" :rows="2" placeholder="例：需要包含实际代码示例..." class="form-input" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" class="action-btn" @click="handleGenerate">
          ✨ 一键生成
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { generateQuestion, saveGenerationHistory } from '@/api/questions'
import { recordAction } from '@/api/career'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const questionTypes = ['选择题', '填空题', '判断题', '简答题', '计算题', '论述题', '编程题']
const difficultyOptions = ['简单', '中等', '困难']

const questionTypeMenuVisible = ref(false)
const difficultyMenuVisible = ref(false)
const typeRef = ref(null)
const diffRef = ref(null)

const form = reactive({
  category: '',
  topic: '',
  questionType: '选择题',
  difficulty: '中等',
  extra: ''
})

const questionTypeLabel = computed(() => form.questionType)

function selectQuestionType(value) {
  form.questionType = value
  questionTypeMenuVisible.value = false
}

function selectDifficulty(value) {
  form.difficulty = value
  difficultyMenuVisible.value = false
}

function handleClickOutside(event) {
  if (typeRef.value && !typeRef.value.contains(event.target)) {
    questionTypeMenuVisible.value = false
  }
  if (diffRef.value && !diffRef.value.contains(event.target)) {
    difficultyMenuVisible.value = false
  }
}

async function handleGenerate() {
  if (!form.topic) {
    ElMessage.warning('请填写具体知识点')
    return
  }

  loading.value = true
  try {
    const data = await generateQuestion({
      user_id: authStore.user.id,
      category: form.category || '通用',
      topic: form.topic,
      question_type: form.questionType,
      difficulty: form.difficulty,
      extra: form.extra
    })

    await saveGenerationHistory({
      user_id: authStore.user.id,
      question_id: data.id,
      title: data.title,
      question_type: data.type,
      category: data.category,
      topic: data.topic
    })

    await recordAction(authStore.user.id, 'generate_question')

    sessionStorage.setItem('current_question', JSON.stringify(data))
    router.push('/do-question')
  } catch (error) {
    ElMessage.error('生成失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.generate-form {
  padding: 8px 0;
}
.generate-form h3 {
  margin-bottom: 16px;
  color: var(--text-primary);
}

.form-input {
  transition: all 0.3s ease;
}
.form-input:hover {
  transform: scale(1.01);
}
.form-input:focus-within {
  transform: scale(1.01);
}

.select-wrapper {
  position: relative;
  display: inline-block;
  width: 100%;
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
  max-height: 220px;      /* 限制最大高度 */
  overflow-y: auto;       /* 内容超出时滚动 */
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

.action-btn {
  transition: all 0.3s ease !important;
}
.action-btn:hover {
  transform: translateY(-2px) scale(1.03) !important;
}
.action-btn:active {
  transform: scale(0.95) !important;
}

:deep(.el-form-item__label) {
  color: var(--text-secondary) !important;
}
:deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.04) !important;
  border-color: var(--border-color) !important;
  color: var(--text-primary) !important;
  border-radius: 10px !important;
  transition: all 0.3s ease !important;
}
:deep(.el-textarea__inner:hover) {
  border-color: rgba(255, 255, 255, 0.12) !important;
}
:deep(.el-textarea__inner:focus) {
  border-color: rgba(255, 255, 255, 0.18) !important;
}
[data-theme="dark"] :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.03) !important;
}
</style>