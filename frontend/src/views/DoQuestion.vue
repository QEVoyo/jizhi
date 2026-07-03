<template>
  <div class="question-page">
    <div class="question-container">
      <!-- 返回 -->
      <div class="question-topbar">
        <el-button text @click="goBack" class="back-btn">
          <i class="fas fa-arrow-left"></i> 返回
        </el-button>
        <h2>📝 练习</h2>
      </div>

      <!-- 题目信息 -->
      <div class="question-meta">
        <div class="difficulty-ring">
          <svg viewBox="0 0 60 60" class="ring-svg">
            <circle cx="30" cy="30" r="25" fill="none" stroke="rgba(128,128,128,0.12)" stroke-width="5"/>
            <circle
              cx="30"
              cy="30"
              r="25"
              fill="none"
              :stroke="diffColor"
              stroke-width="5"
              stroke-linecap="round"
              :stroke-dasharray="157.08"
              :stroke-dashoffset="157.08 * (1 - difficultyScore / 10)"
              transform="rotate(-90 30 30)"
            />
          </svg>
          <div class="ring-label">
            <span class="ring-score">{{ difficultyScore.toFixed(1) }}</span>
            <span class="ring-text">难度</span>
          </div>
        </div>

        <div class="meta-right">
          <div class="meta-item">
            <span class="meta-label">分类</span>
            <span class="meta-value">{{ question.category || '未分类' }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">知识点</span>
            <span class="meta-value">{{ question.normalized_topic || question.topic || '未知' }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">题型</span>
            <span class="meta-value">{{ getTypeDisplay(question.question_type) }}</span>
          </div>
        </div>
      </div>

      <el-divider />

      <!-- 题目内容 -->
      <div class="question-content">
        <h3>{{ question.title }}</h3>
      </div>

      <!-- 答题区 -->
      <div class="answer-area">
        <!-- 选择题 -->
        <el-radio-group v-if="question.question_type === 'choice'" v-model="userAnswer" class="choice-group">
          <el-radio
            v-for="(opt, key) in question.options"
            :key="key"
            :label="key"
            class="choice-item"
          >
            {{ key }}. {{ opt }}
          </el-radio>
        </el-radio-group>

        <!-- 判断题 -->
        <el-radio-group v-else-if="question.question_type === 'judge'" v-model="userAnswer" class="judge-group">
          <el-radio label="正确" class="judge-item">正确</el-radio>
          <el-radio label="错误" class="judge-item">错误</el-radio>
        </el-radio-group>

        <!-- 填空题 -->
        <el-input
          v-else-if="question.question_type === 'fill'"
          v-model="userAnswer"
          placeholder="请输入答案..."
          size="large"
        />

        <!-- 简答题/论述题 -->
        <el-input
          v-else-if="question.question_type === 'essay'"
          v-model="userAnswer"
          type="textarea"
          :rows="5"
          placeholder="请输入你的回答..."
        />

        <!-- 编程题 -->
        <el-input
          v-else-if="question.question_type === 'coding'"
          v-model="userAnswer"
          type="textarea"
          :rows="6"
          :placeholder="question.starter_code || '# 请在这里编写代码'"
        />

        <!-- 计算题 -->
        <el-input
          v-else-if="question.question_type === 'calculation'"
          v-model="userAnswer"
          type="textarea"
          :rows="4"
          placeholder="请写出计算过程和答案..."
        />

        <!-- 默认 -->
        <el-input v-else v-model="userAnswer" placeholder="请输入答案..." size="large" />
      </div>

      <el-divider />

      <!-- 评估结果 -->
      <div v-if="evaluated && evaluationResult" class="evaluation">
        <div v-if="evaluationResult.is_correct" class="correct">
          <i class="fas fa-check-circle"></i> 回答正确！
        </div>
        <div v-else class="incorrect">
          <i class="fas fa-times-circle"></i> 回答错误
        </div>

        <!-- ===== 新增：正确答案 ===== -->
        <div class="correct-answer">
          <span class="label">✅ 正确答案：</span>
          <span class="answer">{{ evaluationResult.correct_answer || '无' }}</span>
        </div>

        <!-- ===== 新增：用户答案 ===== -->
        <div class="user-answer-display">
          <span class="label">📝 你的答案：</span>
          <span class="answer">{{ userAnswer || '未作答' }}</span>
        </div>

        <div class="mastery-section">
          <span class="mastery-label">掌握程度</span>
          <div class="mastery-bar">
            <div
              class="mastery-fill"
              :style="{
                width: (evaluationResult.mastery_score || 50) + '%',
                background: getColor(evaluationResult.mastery_score || 50)
              }"
            />
          </div>
          <span class="mastery-score">{{ evaluationResult.mastery_score || 50 }}%</span>
        </div>

        <!-- ===== 新增：详细解析 ===== -->
        <div v-if="evaluationResult.detailed_analysis" class="detail-analysis">
          <div class="analysis-title">📖 详细解析</div>
          <div class="analysis-content">{{ evaluationResult.detailed_analysis }}</div>
        </div>

        <div class="eval-text">
          <strong>📝 评估：</strong>{{ evaluationResult.evaluation }}
        </div>
        <div class="eval-text">
          <strong>💡 建议：</strong>{{ evaluationResult.suggestion }}
        </div>

        <!-- ===== 新增：视频推荐 ===== -->
        <div v-if="videos.length > 0" class="video-section">
          <div class="video-header">
            <span class="video-title">📺 相关视频讲解</span>
            <a
              :href="`https://search.bilibili.com/all?keyword=${encodeURIComponent(searchKeyword)}`"
              target="_blank"
              class="more-link"
            >
              查看更多 →
            </a>
          </div>
          <div class="video-grid">
            <div
              v-for="video in videos"
              :key="video.bvid"
              class="video-card"
              @click="openVideo(video)"
            >
              <img :src="video.pic" :alt="video.title" loading="lazy"referrerpolicy="no-referrer"/>
              <div class="video-info">
                <div class="video-title-text">{{ video.title }}</div>
                <div class="video-meta">
                  <span>{{ video.author }}</span>
                  <span>👁 {{ formatNumber(video.play) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else-if="videoSearched && !videoLoading && !videos.length" class="video-empty">
          📺 暂无相关视频推荐
        </div>

        <el-button type="primary" @click="resetEvaluation">继续练习 →</el-button>
      </div>

      <!-- 按钮区 -->
      <div v-else class="action-buttons">
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          <i class="fas fa-paper-plane"></i> 提交
        </el-button>
        <el-button :loading="regenerating" @click="handleRegenerate">
          <i class="fas fa-sync"></i> 重新生成
        </el-button>
        <el-button @click="showAddToSet = true">
          <i class="fas fa-folder-plus"></i> 加入题集
        </el-button>
        <el-button @click="showChangeType = true">
          <i class="fas fa-arrows-rotate"></i> 换题型
        </el-button>
        <el-button @click="showHint">
          <i class="fas fa-lightbulb"></i> 提示
        </el-button>
      </div>
    </div>

    <!-- ===== 换题型弹窗 ===== -->
    <el-dialog v-model="showChangeType" title="🔄 换题型" width="420px" destroy-on-close>
      <div class="change-type-dialog">
        <p class="dialog-tip">选择换题方式</p>
        <el-radio-group v-model="changeMode" class="change-mode-group">
          <el-radio label="random">🎲 从选中的题型中随机</el-radio>
          <el-radio label="specify">📋 指定一个题型</el-radio>
        </el-radio-group>

        <div v-if="changeMode === 'random'" class="random-types">
          <p class="sub-tip">勾选要参与随机的题型（至少选一个）</p>
          <div class="type-checkboxes">
            <el-checkbox
              v-for="t in availableTypes"
              :key="t"
              v-model="selectedTypes"
              :label="t"
            />
          </div>
          <p v-if="!selectedTypes.length" class="warning-tip">⚠️ 请至少选择一个题型</p>
        </div>

        <div v-else class="specify-type">
          <el-select v-model="targetType" placeholder="选择题型" style="width:100%">
            <el-option
              v-for="t in availableTypes"
              :key="t"
              :label="t"
              :value="t"
            />
          </el-select>
        </div>
      </div>
      <template #footer>
        <el-button @click="showChangeType = false">取消</el-button>
        <el-button type="primary" :loading="changingType" @click="handleChangeType">
          确认换题
        </el-button>
      </template>
    </el-dialog>

    <!-- ===== 加入题集弹窗 ===== -->
    <el-dialog v-model="showAddToSet" title="📁 加入题集" width="440px" destroy-on-close>
      <div class="add-to-set-dialog">
        <p class="dialog-tip">将当前题目加入以下题集</p>
        <div v-if="!questionSets.length" class="empty-state">
          <p>📭 你还没有创建题集</p>
          <el-button type="primary" size="small" @click="goCreateSet">前往创建题集</el-button>
        </div>
        <div v-else>
          <div
            v-for="s in questionSets"
            :key="s.id"
            class="set-item"
            :class="{ already: s.question_ids?.includes(question.id) }"
          >
            <div class="set-info">
              <span class="set-name">{{ s.name }}</span>
              <span class="set-count">{{ s.question_ids?.length || 0 }} 道题</span>
            </div>
            <el-button
              v-if="s.question_ids?.includes(question.id)"
              size="small"
              disabled
            >
              ✅ 已加入
            </el-button>
            <el-button
              v-else
              size="small"
              type="primary"
              :loading="addingSetId === s.id"
              @click="handleAddToSetConfirm(s.id)"
            >
              加入
            </el-button>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showAddToSet = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- ===== 新增：视频播放弹窗 ===== -->
    <el-dialog
      v-model="videoDialogVisible"
      :title="currentVideo?.title || '视频播放'"
      width="800px"
      class="video-dialog"
      destroy-on-close
      :close-on-click-modal="true"
    >
      <div v-if="currentVideo" class="video-player-container">
        <div class="video-wrapper">
          <iframe
            :src="`https://player.bilibili.com/player.html?bvid=${currentVideo.bvid}&page=1&autoplay=0&high_quality=1`"
            frameborder="0"
            allowfullscreen
            class="video-iframe"
          />
        </div>
        <div class="video-detail-info">
          <div class="video-detail-title">{{ currentVideo.title }}</div>
          <div class="video-detail-meta">
            <span>👤 {{ currentVideo.author }}</span>
            <span>👁 {{ formatNumber(currentVideo.play) }}</span>
            <span>❤️ {{ formatNumber(currentVideo.like) }}</span>
          </div>
          <a
            :href="currentVideo.url"
            target="_blank"
            class="goto-bilibili-btn"
          >
            去B站观看 ↗
          </a>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  evaluateAnswer,
  generateQuestion,
  getQuestionSets,
  addQuestionToSet
} from '@/api/questions'
import { searchBilibili } from '@/api/video'
import { recordAction } from '@/api/career'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const question = ref({})
const userAnswer = ref('')
const evaluated = ref(false)
const evaluationResult = ref(null)
const submitting = ref(false)
const regenerating = ref(false)
const changingType = ref(false)
const addingSetId = ref(null)

// 换题型
const showChangeType = ref(false)
const changeMode = ref('random')
const selectedTypes = ref([])
const targetType = ref('')
const availableTypes = ref([])

// 加入题集
const showAddToSet = ref(false)
const questionSets = ref([])

// ===== 新增：视频相关 =====
const videos = ref([])
const videoLoading = ref(false)
const videoSearched = ref(false)
const searchKeyword = ref('')
const videoDialogVisible = ref(false)
const currentVideo = ref(null)

const difficultyScore = computed(() => question.value.difficulty_score || 5)

const diffColor = computed(() => {
  const s = difficultyScore.value / 10
  if (s < 0.2) return '#00CC66'
  if (s < 0.4) return '#6BCB77'
  if (s < 0.6) return '#FFD93D'
  if (s < 0.8) return '#FFB74D'
  return '#FF6B6B'
})

const typeDisplayMap = {
  choice: '选择题',
  fill: '填空题',
  judge: '判断题',
  essay: '简答题/论述题',
  calculation: '计算题',
  coding: '编程题'
}

const allTypes = ['选择题', '填空题', '判断题', '简答题', '计算题', '编程题']

function getTypeDisplay(type) {
  return typeDisplayMap[type] || type || '未知'
}

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

// ===== 新增：格式化数字 =====
function formatNumber(num) {
  if (!num) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  return num.toString()
}

function loadQuestion() {
  const stored = sessionStorage.getItem('current_question')
  if (stored) {
    try {
      question.value = JSON.parse(stored)
      const currentType = question.value.question_type || 'choice'
      const displayType = typeDisplayMap[currentType] || '选择题'
      availableTypes.value = allTypes.filter(t => t !== displayType)
      selectedTypes.value = [...availableTypes.value]
      if (availableTypes.value.length) {
        targetType.value = availableTypes.value[0]
      }
    } catch {
      ElMessage.error('加载题目失败')
      router.back()
    }
  } else {
    ElMessage.warning('没有找到题目')
    router.back()
  }
}

async function loadQuestionSets() {
  try {
    questionSets.value = await getQuestionSets(authStore.user.id)
  } catch {
    questionSets.value = []
  }
}

// ===== 新增：搜索视频 =====
async function searchVideos(keyword) {
  if (!keyword) return
  videoLoading.value = true
  videoSearched.value = false
  try {
    const res = await searchBilibili(keyword, 1, 4)
    if (res.success) {
      videos.value = res.videos || []
    } else {
      videos.value = []
    }
  } catch (error) {
    console.error('搜索视频失败:', error)
    videos.value = []
  } finally {
    videoLoading.value = false
    videoSearched.value = true
  }
}

// ===== 新增：打开视频弹窗 =====
function openVideo(video) {
  currentVideo.value = video
  videoDialogVisible.value = true
}

async function handleSubmit() {
  console.log('=== handleSubmit 被调用 ===')  // 👈 加这行
  if (!userAnswer.value) {
    ElMessage.warning('请先作答')
    return
  }

  submitting.value = true
  try {
    const result = await evaluateAnswer({
      question: question.value,
      user_answer: userAnswer.value,
      user_id: authStore.user.id
    })

    if (sessionStorage.getItem('from_mistake_book') === 'true' && result.mastery_score >= 60) {
      await recordAction(authStore.user.id, 'conquer_mistake')
    }

    evaluationResult.value = result
    evaluated.value = true

    // ===== 新增：评估完成后搜索视频 =====
    const knowledgePoints = result.knowledge_points || []
    const topic = question.value.normalized_topic || question.value.topic || ''
    const searchTerms = [...knowledgePoints]
    if (topic && !searchTerms.includes(topic)) {
      searchTerms.push(topic)
    }
    const typeName = getTypeDisplay(question.value.question_type)
    const keyword = searchTerms.length > 0
      ? searchTerms[0] + (typeName ? ' ' + typeName : '')
      : topic || '学习'

    searchKeyword.value = keyword
    await searchVideos(keyword)

  } catch (error) {
    ElMessage.error('评估失败: ' + error.message)
  } finally {
    submitting.value = false
  }
}

function resetEvaluation() {
  evaluated.value = false
  evaluationResult.value = null
  userAnswer.value = ''
  // ===== 新增：重置视频状态 =====
  videos.value = []
  videoSearched.value = false
  videoLoading.value = false
}

async function handleRegenerate() {
  const { category, topic, question_type, difficulty_score } = question.value
  regenerating.value = true
  try {
    const diffMap = { 2: '简单', 6: '中等', 8.5: '困难' }
    const diff = diffMap[difficulty_score] || '中等'
    const typeMap = {
      choice: '选择题', fill: '填空题', judge: '判断题',
      essay: '简答题', calculation: '计算题', coding: '编程题'
    }
    const newQuestion = await generateQuestion({
      user_id: authStore.user.id,
      category: category || '通用',
      topic: topic || '',
      question_type: typeMap[question_type] || '选择题',
      difficulty: diff,
      extra: ''
    })
    sessionStorage.setItem('current_question', JSON.stringify(newQuestion))
    question.value = newQuestion
    resetEvaluation()
    const currentType = newQuestion.question_type || 'choice'
    const displayType = typeDisplayMap[currentType] || '选择题'
    availableTypes.value = allTypes.filter(t => t !== displayType)
    selectedTypes.value = [...availableTypes.value]
    if (availableTypes.value.length) {
      targetType.value = availableTypes.value[0]
    }
    ElMessage.success('已重新生成')
  } catch (error) {
    ElMessage.error('重新生成失败: ' + error.message)
  } finally {
    regenerating.value = false
  }
}

async function handleChangeType() {
  if (changeMode.value === 'random' && !selectedTypes.value.length) {
    ElMessage.warning('请至少选择一个题型')
    return
  }
  if (changeMode.value === 'specify' && !targetType.value) {
    ElMessage.warning('请选择题型')
    return
  }

  const newType = changeMode.value === 'random'
    ? selectedTypes.value[Math.floor(Math.random() * selectedTypes.value.length)]
    : targetType.value

  changingType.value = true
  try {
    const { category, topic, difficulty_score } = question.value
    const diffMap = { 2: '简单', 6: '中等', 8.5: '困难' }
    const diff = diffMap[difficulty_score] || '中等'

    const newQuestion = await generateQuestion({
      user_id: authStore.user.id,
      category: category || '通用',
      topic: topic || '',
      question_type: newType,
      difficulty: diff,
      extra: ''
    })

    sessionStorage.setItem('current_question', JSON.stringify(newQuestion))
    question.value = newQuestion
    resetEvaluation()

    const currentType = newQuestion.question_type || 'choice'
    const displayType = typeDisplayMap[currentType] || '选择题'
    availableTypes.value = allTypes.filter(t => t !== displayType)
    selectedTypes.value = [...availableTypes.value]
    if (availableTypes.value.length) {
      targetType.value = availableTypes.value[0]
    }

    showChangeType.value = false
    ElMessage.success(`已切换为 ${newType}`)
  } catch (error) {
    ElMessage.error('换题型失败: ' + error.message)
  } finally {
    changingType.value = false
  }
}

function handleAddToSet() {
  showAddToSet.value = true
  loadQuestionSets()
}

async function handleAddToSetConfirm(setId) {
  addingSetId.value = setId
  try {
    await addQuestionToSet(setId, question.value.id)
    await recordAction(authStore.user.id, 'add_to_set')
    ElMessage.success('已加入题集')
    await loadQuestionSets()
  } catch (error) {
    ElMessage.error('加入失败')
  } finally {
    addingSetId.value = null
  }
}

function goCreateSet() {
  showAddToSet.value = false
  router.push('/resource-lib')
}

function showHint() {
  if (question.value.hint) {
    ElMessage.info('💡 ' + question.value.hint)
  } else {
    ElMessage.info('暂无提示')
  }
}

function goBack() {
  const fromMistake = sessionStorage.getItem('from_mistake_book')
  if (fromMistake === 'true') {
    sessionStorage.removeItem('from_mistake_book')
    router.push('/resource-lib')
  } else {
    router.back()
  }
}

onMounted(loadQuestion)
</script>

<style scoped>
.question-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px 32px;
}

.question-container {
  max-width: 1000px;
  width: 100%;
  padding: 40px 48px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.question-container:hover {
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.06);
}

[data-theme="dark"] .question-container {
  background: rgba(0, 0, 0, 0.25);
  border-color: rgba(255, 255, 255, 0.04);
}
[data-theme="dark"] .question-container:hover {
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.2);
}

.question-topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.question-topbar h2 {
  margin: 0;
  font-size: 22px;
  color: var(--text-primary);
}
.back-btn {
  color: var(--text-secondary) !important;
  transition: all 0.3s ease !important;
}
.back-btn:hover {
  color: var(--text-primary) !important;
  transform: translateX(-2px);
}

/* ===== 难度圆环 + 信息 ===== */
.question-meta {
  display: flex;
  align-items: center;
  gap: 32px;
  flex-wrap: wrap;
  padding: 8px 0;
}

.difficulty-ring {
  position: relative;
  width: 72px;
  height: 72px;
  flex-shrink: 0;
  transition: transform 0.3s ease;
}
.difficulty-ring:hover {
  transform: scale(1.05);
}
.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.ring-label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  line-height: 1.2;
}
.ring-score {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}
.ring-text {
  display: block;
  font-size: 9px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.meta-right {
  display: flex;
  flex-wrap: wrap;
  gap: 20px 40px;
  flex: 1;
}
.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.meta-label {
  font-size: 11px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.meta-value {
  font-size: 15px;
  color: var(--text-primary);
  font-weight: 500;
}

/* ===== 题目内容 ===== */
.question-content h3 {
  font-size: 20px;
  line-height: 1.8;
  color: var(--text-primary);
  font-weight: 500;
}

/* ===== 答题区 ===== */
.answer-area {
  margin: 20px 0;
}

.choice-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-start;
  width: 100%;
}
.choice-item {
  padding: 12px 18px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  width: 100%;
  cursor: pointer;
  font-size: 15px;
}
.choice-item:hover {
  background: rgba(128, 128, 128, 0.06);
  border-color: rgba(128, 128, 128, 0.2);
  transform: translateX(4px);
}
.choice-item.is-checked {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.06);
  transform: translateX(4px);
}

.judge-group {
  display: flex;
  gap: 20px;
  align-items: flex-start;
  flex-wrap: wrap;
}
.judge-item {
  padding: 12px 28px;
  border-radius: 10px;
  border: 1px solid var(--border-color);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
  font-size: 15px;
}
.judge-item:hover {
  background: rgba(128, 128, 128, 0.06);
  border-color: rgba(128, 128, 128, 0.2);
  transform: translateY(-2px) scale(1.02);
}
.judge-item.is-checked {
  border-color: #409eff;
  background: rgba(64, 158, 255, 0.06);
}

/* ===== 评估结果 ===== */
.evaluation {
  padding: 24px 28px;
  border-radius: 14px;
  background: rgba(128, 128, 128, 0.04);
  transition: all 0.3s ease;
}
.evaluation:hover {
  background: rgba(128, 128, 128, 0.06);
}

.correct {
  color: #6BCB77;
  font-weight: 600;
  font-size: 20px;
}
.incorrect {
  color: #FF6B6B;
  font-weight: 600;
  font-size: 20px;
}

/* ===== 新增：正确答案 & 用户答案 ===== */
.correct-answer,
.user-answer-display {
  margin: 8px 0;
  padding: 10px 14px;
  border-radius: 8px;
  background: rgba(128, 128, 128, 0.04);
}
.correct-answer .label,
.user-answer-display .label {
  font-weight: 500;
  color: var(--text-secondary);
}
.correct-answer .answer {
  color: #6BCB77;
  font-weight: 600;
}
.user-answer-display .answer {
  color: var(--text-primary);
  font-weight: 600;
}

.mastery-section {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 16px 0;
}
.mastery-label {
  font-size: 14px;
  color: var(--text-secondary);
  white-space: nowrap;
}
.mastery-bar {
  flex: 1;
  height: 10px;
  border-radius: 5px;
  background: rgba(128, 128, 128, 0.15);
  overflow: hidden;
}
.mastery-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.8s ease;
}
.mastery-score {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 48px;
  text-align: right;
}

/* ===== 新增：详细解析 ===== */
.detail-analysis {
  margin: 12px 0;
  padding: 14px 16px;
  border-radius: 10px;
  background: rgba(64, 158, 255, 0.04);
  border-left: 3px solid #409eff;
}
.analysis-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
  font-size: 14px;
}
.analysis-content {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.eval-text {
  margin: 8px 0;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.7;
}
.eval-text strong {
  color: var(--text-primary);
}

/* ===== 新增：视频推荐 ===== */
.video-section {
  margin: 16px 0;
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(128, 128, 128, 0.03);
}
.video-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.video-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
}
.more-link {
  font-size: 13px;
  color: #409eff;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s ease;
}
.more-link:hover {
  color: #66b1ff;
  transform: translateX(2px);
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
@media (max-width: 768px) {
  .video-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 480px) {
  .video-grid {
    grid-template-columns: 1fr;
  }
}

.video-card {
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.video-card:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: rgba(255, 255, 255, 0.12);
}
.video-card img {
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
  display: block;
}
.video-info {
  padding: 8px 10px;
}
.video-title-text {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}
.video-meta {
  font-size: 11px;
  color: var(--text-muted);
  display: flex;
  gap: 10px;
  margin-top: 4px;
}
.video-empty {
  padding: 12px 0;
  color: var(--text-muted);
  font-size: 14px;
  text-align: center;
}

/* ===== 按钮区 ===== */
.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.action-buttons .el-button {
  border-radius: 10px;
  padding: 10px 20px;
  font-size: 14px;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) !important;
}
.action-buttons .el-button:hover {
  transform: translateY(-2px) scale(1.02);
}
.action-buttons .el-button:active {
  transform: translateY(0px) scale(0.98);
}
.action-buttons .el-button--primary {
  background: rgba(64, 158, 255, 0.12) !important;
  border-color: rgba(64, 158, 255, 0.2) !important;
  color: #409eff !important;
}
.action-buttons .el-button--primary:hover {
  background: rgba(64, 158, 255, 0.2) !important;
}

/* ===== 弹窗样式 ===== */
.change-type-dialog {
  padding: 4px 0;
}
.dialog-tip {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 12px;
}
.sub-tip {
  color: var(--text-muted);
  font-size: 13px;
  margin: 8px 0;
}
.change-mode-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.random-types {
  margin-top: 12px;
}
.type-checkboxes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin: 8px 0;
}
.warning-tip {
  color: #f56c6c;
  font-size: 13px;
  margin: 4px 0;
}
.specify-type {
  margin-top: 12px;
}

.set-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border-color);
  margin-bottom: 8px;
  transition: all 0.3s ease;
}
.set-item:hover {
  background: rgba(128, 128, 128, 0.04);
}
.set-item.already {
  opacity: 0.6;
}
.set-info {
  display: flex;
  gap: 12px;
  align-items: center;
}
.set-name {
  font-weight: 500;
  color: var(--text-primary);
}
.set-count {
  font-size: 12px;
  color: var(--text-muted);
}
.empty-state {
  text-align: center;
  padding: 20px 0;
  color: var(--text-muted);
}
.empty-state p {
  margin-bottom: 12px;
}

/* ===== 新增：视频弹窗 ===== */
.video-dialog :deep(.el-dialog) {
  background: rgba(255, 255, 255, 0.06) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 16px !important;
}
[data-theme="dark"] .video-dialog :deep(.el-dialog) {
  background: rgba(0, 0, 0, 0.35) !important;
}
.video-dialog :deep(.el-dialog__title) {
  color: var(--text-primary) !important;
  font-weight: 600;
}
.video-dialog :deep(.el-dialog__body) {
  padding: 12px 20px 20px;
}
.video-dialog :deep(.el-dialog__header) {
  padding: 16px 20px 0;
}

.video-player-container {
  width: 100%;
}
.video-wrapper {
  position: relative;
  width: 100%;
  padding-bottom: 56.25%;
  background: #000;
  border-radius: 10px;
  overflow: hidden;
}
.video-iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
}
.video-detail-info {
  padding: 12px 4px 4px;
}
.video-detail-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
.video-detail-meta {
  font-size: 13px;
  color: var(--text-muted);
  display: flex;
  gap: 16px;
  margin: 4px 0 10px;
}
.goto-bilibili-btn {
  display: inline-block;
  padding: 6px 18px;
  border-radius: 8px;
  background: rgba(64, 158, 255, 0.12);
  border: 1px solid rgba(64, 158, 255, 0.2);
  color: #409eff;
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s ease;
}
.goto-bilibili-btn:hover {
  background: rgba(64, 158, 255, 0.2);
  transform: translateY(-2px);
}

/* ===== 输入框深色适配 ===== */
[data-theme="dark"] :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
}
[data-theme="dark"] :deep(.el-input__wrapper:hover) {
  border-color: rgba(255, 255, 255, 0.14) !important;
}
[data-theme="dark"] :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.05) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  color: var(--text-primary) !important;
}
[data-theme="dark"] :deep(.el-textarea__inner:hover) {
  border-color: rgba(255, 255, 255, 0.14) !important;
}
[data-theme="dark"] :deep(.el-textarea__inner:focus) {
  border-color: rgba(255, 255, 255, 0.18) !important;
}

[data-theme="dark"] .choice-item {
  border-color: rgba(255, 255, 255, 0.08);
}
[data-theme="dark"] .choice-item:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.15);
}
[data-theme="dark"] .judge-item {
  border-color: rgba(255, 255, 255, 0.08);
}
[data-theme="dark"] .judge-item:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.15);
}
[data-theme="dark"] .evaluation {
  background: rgba(255, 255, 255, 0.03);
}
[data-theme="dark"] .evaluation:hover {
  background: rgba(255, 255, 255, 0.05);
}
[data-theme="dark"] .set-item {
  border-color: rgba(255, 255, 255, 0.06);
}
[data-theme="dark"] .set-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

/* ===== 响应式 ===== */
@media (max-width: 640px) {
  .question-page {
    padding: 12px 10px;
    align-items: flex-start;
  }
  .question-container {
    padding: 20px 16px;
    margin-top: 4px;
  }
  .question-meta {
    gap: 16px;
  }
  .meta-right {
    gap: 12px 20px;
  }
  .action-buttons .el-button {
    flex: 1;
    min-width: 56px;
    font-size: 12px;
    padding: 8px 10px;
  }
  .difficulty-ring {
    width: 56px;
    height: 56px;
  }
  .ring-score {
    font-size: 14px;
  }
  .choice-group {
    gap: 6px;
  }
  .judge-group {
    gap: 10px;
  }
  .evaluation {
    padding: 14px;
  }
  .question-content h3 {
    font-size: 16px;
  }
  .question-topbar h2 {
    font-size: 18px;
  }
  .choice-item {
    font-size: 14px;
    padding: 10px 14px;
  }
  .judge-item {
    font-size: 14px;
    padding: 10px 18px;
  }
  .video-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 400px) {
  .video-grid {
    grid-template-columns: 1fr;
  }
}
</style>