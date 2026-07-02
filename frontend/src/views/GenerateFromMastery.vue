<template>
  <div class="generate-page">
    <div class="generate-container">
      <el-button text @click="goBack">← 返回掌握度看板</el-button>

      <h2>📝 生成题目</h2>
      <p class="subtitle">针对「{{ topic }}」生成练习题</p>

      <el-divider />

      <el-form :model="form" label-width="100px">
        <el-form-item label="方向">
          <el-input :value="topic" disabled />
        </el-form-item>
        <el-form-item label="细化知识点">
          <el-input v-model="form.subTopic" placeholder="可选，进一步细分..." />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="题型">
              <el-select v-model="form.questionType" style="width:100%">
                <el-option
                  v-for="t in questionTypes"
                  :key="t"
                  :label="t"
                  :value="t"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="难度">
              <el-select v-model="form.difficulty" style="width:100%">
                <el-option label="简单" value="简单" />
                <el-option label="中等" value="中等" />
                <el-option label="困难" value="困难" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="补充说明">
          <el-input v-model="form.extra" type="textarea" :rows="2" placeholder="例：需要包含实际代码示例..." />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleGenerate">
            ✨ 生成题目
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { generateQuestion, saveGenerationHistory } from '@/api/questions'
import { recordAction } from '@/api/career'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const topic = ref('')
const loading = ref(false)
const questionTypes = ['选择题', '填空题', '判断题', '简答题', '计算题', '论述题', '编程题']

const form = reactive({
  subTopic: '',
  questionType: '选择题',
  difficulty: '中等',
  extra: ''
})

async function handleGenerate() {
  loading.value = true
  try {
    const finalTopic = topic.value + (form.subTopic ? ` - ${form.subTopic}` : '')
    const data = await generateQuestion({
      user_id: authStore.user.id,
      category: topic.value,
      topic: finalTopic,
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
    ElMessage.success('✅ 题目生成成功！')
    router.push('/do-question')
  } catch (error) {
    ElMessage.error('生成失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/mastery-board')
}

onMounted(() => {
  topic.value = route.query.topic || ''
  if (!topic.value) {
    ElMessage.warning('未指定知识点方向')
    router.back()
  }
})
</script>

<style scoped>
.generate-page {
  min-height: 100vh;
  padding: 20px;
  background: var(--bg-color);
}
.generate-container {
  max-width: 700px;
  margin: 0 auto;
  padding: 24px 28px;
  border-radius: 16px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
}
.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  opacity: 0.6;
}
</style>