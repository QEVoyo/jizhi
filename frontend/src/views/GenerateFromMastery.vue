<template>
  <div class="generate-page">
    <div class="generate-container">
      <el-button text @click="goBack" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>
        返回掌握度看板
      </el-button>

      <h2>
        <el-icon><Edit /></el-icon>
        生成题目
      </h2>
      <p class="subtitle">针对「{{ topic }}」生成练习题</p >

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
          <el-input v-model="form.extra" type="textarea" :rows="2" placeholder="可选，补充额外要求..." />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" class="action-btn" @click="handleGenerate">
            <el-icon><MagicStick /></el-icon>
            生成题目
          </el-button>
        </el-form-item>

        <!-- ✅ 科幻进度条 -->
        <el-form-item v-if="loading" class="progress-form-item">
          <div class="scifi-progress-wrapper">
            <div class="progress-glow"></div>

            <!-- 流动粒子 -->
            <div class="flow-particles">
              <span
                v-for="i in 6"
                :key="i"
                class="flow-particle"
                :style="{ animationDelay: (i * 0.4) + 's', left: (i * 17) + '%' }"
              ></span>
            </div>

            <div class="progress-agent">
              <el-icon class="agent-icon"><Cpu /></el-icon>
              <span class="agent-name">生成 Agent</span>
              <span class="agent-status">{{ progressMessage }}</span>
            </div>

            <div class="progress-status">
              <span class="status-dot"></span>
              <span class="status-text">{{ progressMessage }}</span>
              <span class="status-percent">{{ Math.round(progress) }}%</span>
            </div>

            <div class="progress-track">
              <div class="progress-fill" :style="{ width: progress + '%' }">
                <div class="progress-shimmer"></div>
              </div>
              <div class="scan-line" :style="{ left: progress + '%' }"></div>
              <div class="ripple-effect" :style="{ left: progress + '%' }">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>

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

            <div class="glow-bar"></div>
          </div>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { generateQuestion, saveGenerationHistory } from '@/api/questions'
import { recordAction } from '@/api/career'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Edit, MagicStick, Cpu } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const topic = ref('')
const loading = ref(false)
const questionTypes = ['选择题', '填空题', '判断题', '简答题', '计算题', '论述题', '编程题']

const progress = ref(0)
const progressMessage = ref('准备生成...')
const dataStream = ref('')
const particles = ref([])
let progressInterval = null
let dataStreamInterval = null

const form = reactive({
  subTopic: '',
  questionType: '选择题',
  difficulty: '中等',
  extra: ''
})

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

async function handleGenerate() {
  loading.value = true

  progress.value = 0
  progressMessage.value = '启动生成引擎...'
  generateParticles()
  startProgress()
  startDataStream()

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

    sessionStorage.setItem('current_question', JSON.stringify(data))
    ElMessage.success('✅ 题目生成成功！')

    setTimeout(() => {
      router.push('/do-question')
    }, 500)

  } catch (error) {
    clearInterval(progressInterval)
    clearInterval(dataStreamInterval)
    ElMessage.error('生成失败: ' + error.message)
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

onUnmounted(() => {
  if (progressInterval) clearInterval(progressInterval)
  if (dataStreamInterval) clearInterval(dataStreamInterval)
})
</script>

<style scoped>
.generate-page {
  min-height: 100vh;
  padding: 20px;
  background: var(--bg-color);
  /* ✅ 关联资源库背景图 */
  background-image: url('@/assets/bg/resource_lib_bg.png');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
}

[data-theme="dark"] .generate-page {
  background-image: url('@/assets/bg/resource_lib_bl.jpg');
}

.generate-container {
  max-width: 700px;
  margin: 0 auto;
  padding: 24px 28px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.04);
}

[data-theme="dark"] .generate-container {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(255, 255, 255, 0.04);
}

.back-btn {
  color: var(--text-secondary) !important;
  transition: all 0.3s ease !important;
  display: flex;
  align-items: center;
  gap: 4px;
}
.back-btn:hover {
  color: var(--text-primary) !important;
  transform: translateX(-4px) scale(1.02);
}

.generate-container h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 22px;
  color: var(--text-primary);
  margin: 8px 0 2px;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  opacity: 0.6;
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

/* ======================================== */
/* 炫酷进度条 */
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

.progress-track {
  position: relative;
  height: 8px;
  border-radius: 4px;
  background: rgba(0, 212, 255, 0.06);
  overflow: visible;
  border: 1px solid rgba(0, 212, 255, 0.06);
  z-index: 2;
}

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