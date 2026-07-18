<template>
  <div class="generate-form">
    <h3>
      <el-icon><Cpu /></el-icon>
      生成新题目
    </h3>
    <el-form :model="form" label-width="100px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="学科/领域">
            <el-input
              v-model="form.category"
              placeholder="例如：数学、物理、编程、经济学..."
              class="form-input"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="具体知识点">
            <el-input
              v-model="form.topic"
              placeholder="例如：微积分、数据结构、古典经济学..."
              class="form-input"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="题型">
            <div class="select-wrapper">
              <div class="custom-select" @click.stop="questionTypeMenuVisible = !questionTypeMenuVisible" ref="typeRef">
                <span class="select-display">{{ questionTypeLabel }}</span>
                <el-icon class="select-arrow" :class="{ rotated: questionTypeMenuVisible }">
                  <ArrowDown />
                </el-icon>
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
                <el-icon class="select-arrow" :class="{ rotated: difficultyMenuVisible }">
                  <ArrowDown />
                </el-icon>
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
        <el-input
          v-model="form.extra"
          type="textarea"
          :rows="2"
          placeholder="例如：结合生活中的例子、可以包含图表说明..."
          class="form-input"
        />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="loading" class="action-btn" @click="handleGenerate">
          <el-icon><MagicStick /></el-icon>
          一键生成
        </el-button>
      </el-form-item>

      <!-- 炫酷进度条 -->
      <el-form-item v-if="loading" class="progress-form-item">
        <div class="scifi-progress-wrapper">

          <!-- 光晕 -->
          <div class="progress-glow"></div>

          <!-- 流动粒子背景 -->
          <div class="flow-particles">
            <span
              v-for="i in 6"
              :key="i"
              class="flow-particle"
              :style="{ animationDelay: (i * 0.4) + 's', left: (i * 17) + '%' }"
            ></span>
          </div>

          <!-- Agent 状态 -->
          <div class="progress-agent">
            <el-icon class="agent-icon"><Cpu /></el-icon>
            <span class="agent-name">生成 Agent</span>
            <span class="agent-status">{{ progressMessage }}</span>
          </div>

          <!-- 进度主体 -->
          <div class="progress-status">
            <span class="status-dot"></span>
            <span class="status-text">{{ progressMessage }}</span>
            <span class="status-percent">{{ Math.round(progress) }}%</span>
          </div>

          <!-- 进度轨道（带波纹） -->
          <div class="progress-track">
            <div class="progress-fill" :style="{ width: progress + '%' }">
              <div class="progress-shimmer"></div>
            </div>
            <div class="scan-line" :style="{ left: progress + '%' }"></div>
            <!-- 波纹 -->
            <div class="ripple-effect" :style="{ left: progress + '%' }">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>

          <!-- 底部粒子 + 数据流 -->
          <div class="progress-footer">
            <div class="particle-container">
              <span
                v-for="(p, i) in particles"
                :key="i"
                class="particle"
                :style="{ left: p.x + '%', top: p.y + '%', animationDelay: p.delay + 's' }"
              ></span>
            </div>
            <div class="data-stream">{{ dataStream }}</div>
          </div>

          <!-- 底部发光条 -->
          <div class="glow-bar"></div>
        </div>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { recordAction } from '@/api/career'
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { generateQuestion, saveGenerationHistory } from '@/api/questions'
import { ElMessage } from 'element-plus'
import { Cpu, MagicStick, ArrowDown } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const questionTypes = ['选择题', '填空题', '判断题', '简答题', '计算题', '论述题', '编程题']
const difficultyOptions = ['简单', '中等', '困难']

const questionTypeMenuVisible = ref(false)
const difficultyMenuVisible = ref(false)
const typeRef = ref(null)
const diffRef = ref(null)

const progress = ref(0)
const progressMessage = ref('准备生成...')
const dataStream = ref('')
const particles = ref([])
let progressInterval = null
let dataStreamInterval = null

const form = reactive({
  category: '',
  topic: '',
  questionType: '选择题',
  difficulty: '中等',
  extra: ''
})

const questionTypeLabel = computed(() => form.questionType)

function generateParticles() {
  const count = 40
  particles.value = []
  for (let i = 0; i < count; i++) {
    particles.value.push({
      x: Math.random() * 100,
      y: Math.random() * 100,
      delay: Math.random() * 2.5
    })
  }
}

function startProgress() {
  progress.value = 0
  const steps = [
    { progress: 10, message: '解析知识点...' },
    { progress: 25, message: '调用 AI 引擎...' },
    { progress: 45, message: '生成题目内容...' },
    { progress: 65, message: '验证题目逻辑...' },
    { progress: 80, message: '构建题目标签...' },
    { progress: 95, message: '保存到资源库...' },
  ]

  let stepIndex = 0
  progressInterval = setInterval(() => {
    if (stepIndex < steps.length) {
      const target = steps[stepIndex].progress
      const increment = (target - progress.value) / 8
      if (progress.value < target - 1) {
        progress.value += increment
      } else {
        progress.value = target
        progressMessage.value = steps[stepIndex].message
        stepIndex++
      }
    } else if (progress.value < 99) {
      progress.value += 0.5
    }
  }, 150)
}

function startDataStream() {
  const chars = 'ABCDEF0123456789'
  dataStreamInterval = setInterval(() => {
    let stream = ''
    for (let i = 0; i < 40; i++) {
      stream += chars[Math.floor(Math.random() * chars.length)]
      if (i % 8 === 7) stream += ' '
    }
    dataStream.value = stream
  }, 300)
}

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

  progress.value = 0
  progressMessage.value = '启动生成引擎...'
  generateParticles()
  startProgress()
  startDataStream()

  try {
    const data = await generateQuestion({
      user_id: authStore.user.id,
      category: form.category || '通用',
      topic: form.topic,
      question_type: form.questionType,
      difficulty: form.difficulty,
      extra: form.extra
    })

    progress.value = 100
    progressMessage.value = '生成完成！'
    clearInterval(progressInterval)
    clearInterval(dataStreamInterval)

    await saveGenerationHistory({
      user_id: authStore.user.id,
      question_id: data.id,
      title: data.title,
      question_type: data.type,
      category: data.category,
      topic: data.topic
    })

    await recordAction(authStore.user.id, 'generate_question')

    setTimeout(() => {
      sessionStorage.setItem('current_question', JSON.stringify(data))
      router.push('/do-question')
    }, 500)

  } catch (error) {
    clearInterval(progressInterval)
    clearInterval(dataStreamInterval)
    ElMessage.error('生成失败: ' + error.message)
    loading.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  if (progressInterval) clearInterval(progressInterval)
  if (dataStreamInterval) clearInterval(dataStreamInterval)
})
</script>

<style scoped>
.generate-form {
  padding: 8px 0;
}
.generate-form h3 {
  margin-bottom: 16px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
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
  max-height: 220px;
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

.action-btn {
  transition: all 0.3s ease !important;
  display: flex;
  align-items: center;
  gap: 6px;
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

/* ======================================== */
/* 炫酷进度条（带波纹 + 流动粒子） */
/* ======================================== */
.progress-form-item {
  margin-top: 4px;
  margin-bottom: 0;
  width: 100%;
}
.progress-form-item :deep(.el-form-item__content) {
  margin-left: 0 !important;
  width: 100% !important;
}

.scifi-progress-wrapper {
  position: relative;
  width: 100%;
  background: rgba(0, 20, 40, 0.7);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 16px;
  padding: 16px 20px;
  overflow: hidden;
  backdrop-filter: blur(12px);
  box-shadow: 0 0 50px rgba(0, 212, 255, 0.06), inset 0 0 80px rgba(0, 212, 255, 0.02);
}

/* 背景光晕 */
.progress-glow {
  position: absolute;
  top: -60%;
  left: -60%;
  width: 220%;
  height: 220%;
  background: radial-gradient(ellipse at center, rgba(0, 212, 255, 0.04) 0%, transparent 70%);
  animation: glowPulse 3s ease-in-out infinite;
  pointer-events: none;
}
@keyframes glowPulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.15); }
}

/* 流动粒子 */
.flow-particles {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}
.flow-particle {
  position: absolute;
  bottom: -10px;
  width: 4px;
  height: 4px;
  background: rgba(0, 212, 255, 0.25);
  border-radius: 50%;
  animation: flowUp 4s ease-in-out infinite;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.1);
}
@keyframes flowUp {
  0% { transform: translateY(0) scale(0); opacity: 0; }
  30% { opacity: 0.8; transform: scale(1); }
  70% { opacity: 0.5; }
  100% { transform: translateY(-200px) scale(0); opacity: 0; }
}

/* Agent 状态 */
.progress-agent {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  padding: 6px 14px;
  background: rgba(0, 212, 255, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.08);
  position: relative;
  z-index: 2;
}
.agent-icon {
  font-size: 18px;
  color: #00d4ff;
}
.agent-name {
  font-size: 13px;
  font-weight: 600;
  color: #00d4ff;
  font-family: 'Courier New', monospace;
  letter-spacing: 1px;
}
.agent-status {
  font-size: 13px;
  color: #b0d4ff;
  margin-left: auto;
  font-family: 'Courier New', monospace;
}

/* 进度主体 */
.progress-status {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  position: relative;
  z-index: 2;
}
.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #00d4ff;
  box-shadow: 0 0 20px #00d4ff, 0 0 60px rgba(0, 212, 255, 0.3);
  animation: dotPulse 1.2s ease-in-out infinite;
}
@keyframes dotPulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.3; transform: scale(0.7); }
}
.status-text {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: #b0d4ff;
  letter-spacing: 0.5px;
  font-family: 'Courier New', monospace;
}
.status-percent {
  font-size: 22px;
  font-weight: 700;
  color: #00d4ff;
  font-family: 'Courier New', monospace;
  text-shadow: 0 0 30px rgba(0, 212, 255, 0.4);
}

/* 进度轨道 */
.progress-track {
  position: relative;
  height: 8px;
  border-radius: 4px;
  background: rgba(0, 212, 255, 0.06);
  overflow: visible;
  border: 1px solid rgba(0, 212, 255, 0.06);
  z-index: 2;
}

/* 进度填充 */
.progress-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #00d4ff, #7b2ffc, #ff6fd8, #00ff88);
  background-size: 300% 100%;
  animation: shimmer 2s linear infinite;
  position: relative;
  transition: width 0.3s ease;
  box-shadow: 0 0 40px rgba(0, 212, 255, 0.25);
}
@keyframes shimmer {
  0% { background-position: 0% 0%; }
  100% { background-position: 300% 0%; }
}
.progress-shimmer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: shimmerSweep 1.2s ease-in-out infinite;
}
@keyframes shimmerSweep {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}

/* 扫描线 */
.scan-line {
  position: absolute;
  top: -6px;
  bottom: -6px;
  width: 2px;
  background: #00d4ff;
  box-shadow: 0 0 30px #00d4ff, 0 0 60px rgba(0, 212, 255, 0.25);
  transition: left 0.3s ease;
  z-index: 3;
  border-radius: 2px;
}

/* 波纹效果 */
.ripple-effect {
  position: absolute;
  top: -8px;
  bottom: -8px;
  width: 30px;
  transform: translateX(-50%);
  transition: left 0.3s ease;
  z-index: 4;
  pointer-events: none;
}
.ripple-effect span {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(0, 212, 255, 0.8);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: ripple 1.8s ease-out infinite;
}
.ripple-effect span:nth-child(2) {
  animation-delay: 0.6s;
}
.ripple-effect span:nth-child(3) {
  animation-delay: 1.2s;
}
@keyframes ripple {
  0% { width: 12px; height: 12px; opacity: 0.8; }
  100% { width: 50px; height: 50px; opacity: 0; }
}

/* 底部 */
.progress-footer {
  position: relative;
  height: 22px;
  margin-top: 8px;
  z-index: 2;
  overflow: hidden;
}
.particle-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
.particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: #00d4ff;
  border-radius: 50%;
  opacity: 0;
  animation: particleFloat 2s ease-in-out infinite;
  box-shadow: 0 0 8px rgba(0, 212, 255, 0.6);
}
@keyframes particleFloat {
  0% { opacity: 0; transform: translateY(8px) scale(0); }
  30% { opacity: 1; transform: translateY(-4px) scale(1); }
  70% { opacity: 0.6; transform: translateY(-14px) scale(0.8); }
  100% { opacity: 0; transform: translateY(-24px) scale(0); }
}
.data-stream {
  position: absolute;
  right: 0;
  bottom: 0;
  font-size: 11px;
  font-family: 'Courier New', monospace;
  color: rgba(0, 212, 255, 0.3);
  letter-spacing: 2px;
  animation: dataFade 3s ease-in-out infinite;
}
@keyframes dataFade {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.9; }
}

/* 底部发光条 */
.glow-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00d4ff, #7b2ffc, #ff6fd8, #00ff88, transparent);
  opacity: 0.5;
  animation: glowBarMove 4s linear infinite;
  z-index: 5;
}
@keyframes glowBarMove {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
</style>