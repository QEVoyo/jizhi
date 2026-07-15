<template>
  <div class="resource-page">
    <!-- 顶部 -->
    <div class="resource-topbar">
      <el-button text @click="goHome" class="back-home">
        <i class="fas fa-arrow-left"></i> 返回主界面
      </el-button>
      <h1>📚 资源库</h1>
      <p class="subtitle">生成题目 · 管理题集 · 错题本 · 薄弱点巩固</p >
    </div>

    <!-- ===== 掌握度看板 ===== -->
    <div class="mastery-panel">
      <div class="mastery-header">
        <span class="mastery-title">📊 掌握度看板</span>
        <span class="mastery-stats">
          🔴 薄弱 {{ weakCount }} &nbsp;|&nbsp; 🟡 待巩固 {{ consolidateCount }} &nbsp;|&nbsp; 🟢 优势 {{ strongCount }}
        </span>
      </div>

      <div class="color-legend">
        <span class="legend-label">0%</span>
        <div class="legend-bar"></div>
        <span class="legend-label">100%</span>
        <span class="legend-hint">薄弱 &lt;60%</span>
      </div>

      <div v-if="loadingMastery" class="loading-text">加载中...</div>
      <div v-else-if="weakPoints.length" class="mastery-cards">
        <div
          v-for="(wp, idx) in weakPoints.slice(0, 4)"
          :key="idx"
          class="mastery-card"
          :style="{
            background: `linear-gradient(135deg, ${getColor(wp.mastery_score)}, ${getColorDark(wp.mastery_score)})`,
            boxShadow: `0 4px 20px ${getColor(wp.mastery_score)}40`
          }"
        >
          <span class="card-topic">{{ wp.topic }}</span>
          <span class="card-score">{{ wp.mastery_score }}%</span>
          <el-button size="small" class="card-btn" @click="goPractice(wp.topic)">
            🎯 攻克
          </el-button>
        </div>
        <el-button class="view-all-btn" @click="goMastery">
          📋 查看全部知识点
        </el-button>
      </div>
      <div v-else class="empty-state">🎉 暂无薄弱点，继续保持！</div>
    </div>

    <!-- ===== Tabs ===== -->
    <el-tabs v-model="activeTab" class="resource-tabs" @tab-click="handleTabClick">
      <el-tab-pane label="🤖 生成题目" name="generate">
        <GenerateForm @success="onGenerateSuccess" />
      </el-tab-pane>
      <el-tab-pane label="📁 我的题集" name="sets">
        <QuestionSets />
      </el-tab-pane>
      <el-tab-pane label="📖 错题本" name="mistakes">
        <MistakeBook />
      </el-tab-pane>
      <el-tab-pane label="📜 生成历史" name="history">
        <GenerationHistory ref="historyRef" />
      </el-tab-pane>
      <el-tab-pane label="📊 评估中心" name="evaluation">
        <div class="evaluation-placeholder">
          <div class="evaluation-grid">
            <div class="evaluation-card" @click="goReport">
              <div class="card-icon">📈</div>
              <div class="card-title">学情报告</div>
              <div class="card-desc">查看学习进度、掌握度变化趋势</div>
            </div>
            <div class="evaluation-card" @click="goProfile">
              <div class="card-icon">🧠</div>
              <div class="card-title">六维画像</div>
              <div class="card-desc">知识基础、认知风格、易错点偏好等</div>
            </div>
            <div class="evaluation-card" @click="goAssessment">
              <div class="card-icon">📋</div>
              <div class="card-title">评估表</div>
              <div class="card-desc">知识点掌握度评估与建议</div>
            </div>
            <div class="evaluation-card" @click="goAdvice">
              <div class="card-icon">💡</div>
              <div class="card-title">学习建议</div>
              <div class="card-desc">AI 生成个性化学习建议</div>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import GenerateForm from '@/components/GenerateForm.vue'
import QuestionSets from '@/components/QuestionSets.vue'
import MistakeBook from '@/components/MistakeBook.vue'
import GenerationHistory from '@/components/GenerationHistory.vue'
import { getMastery } from '@/api/questions'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('generate')
const masteryData = ref([])
const loadingMastery = ref(false)
const historyRef = ref(null)

const weakPoints = computed(() =>
  masteryData.value.filter(p => p.mastery_score < 60).sort((a, b) => a.mastery_score - b.mastery_score)
)
const weakCount = computed(() => weakPoints.value.length)
const consolidateCount = computed(() =>
  masteryData.value.filter(p => p.mastery_score >= 60 && p.mastery_score < 80).length
)
const strongCount = computed(() =>
  masteryData.value.filter(p => p.mastery_score >= 80).length
)

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

async function loadMastery() {
  loadingMastery.value = true
  try {
    masteryData.value = await getMastery(authStore.user.id)
  } catch (error) {
    console.error('加载掌握度失败', error)
    ElMessage.error('加载掌握度失败')
  } finally {
    loadingMastery.value = false
  }
}

// ==========================================
// ✅ 生成成功回调（接收参数）
// ==========================================
function onGenerateSuccess(result) {
  // 1. 刷新掌握度看板
  loadMastery()

  // 2. 刷新生成历史
  if (historyRef.value && typeof historyRef.value.refresh === 'function') {
    historyRef.value.refresh()
  }

  // 3. 关键：只有拿到了完整数据，才跳转做题
  if (result && result.id) {
    console.log('✅ 生成成功，准备跳转做题:', result)
    sessionStorage.setItem('current_question', JSON.stringify(result))
    router.push('/do-question')
  } else {
    console.warn('⚠️ 生成成功但数据不完整:', result)
    ElMessage.success('✅ 题目已生成并保存，可在生成历史中查看！')
  }
}

function goPractice(topic) {
  router.push({ path: '/generate-from-mastery', query: { topic } })
}

function goMastery() {
  router.push('/mastery-board')
}

function goHome() {
  router.push('/')
}

function handleTabClick(tab) {
  if (tab.paneName === 'evaluation') {
    router.push('/evaluation-center')
  }
}

function goReport() {
  router.push('/home')
}

function goProfile() {
  router.push('/profile')
}

function goAssessment() {
  ElMessage.info('评估表功能开发中')
}

function goAdvice() {
  ElMessage.info('学习建议功能开发中')
}

onMounted(loadMastery)
</script>

<style scoped>
.resource-page {
  min-height: 100vh;
  padding: 24px 32px 120px 32px;
  background: transparent !important;
}

.resource-topbar {
  margin-bottom: 24px;
}
.resource-topbar h1 {
  font-size: 28px;
  color: var(--text-primary);
  margin: 4px 0 2px;
}
.resource-topbar .subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  opacity: 0.6;
}
.back-home {
  color: var(--text-secondary) !important;
  transition: all 0.3s ease !important;
  padding-left: 0 !important;
}
.back-home:hover {
  color: var(--text-primary) !important;
  transform: translateX(-4px) scale(1.02);
}

.mastery-panel {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 24px;
  transition: all 0.4s ease;
}
.mastery-panel:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  transform: translateY(-2px);
}
[data-theme="dark"] .mastery-panel {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(255, 255, 255, 0.04);
}

.mastery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.mastery-title {
  font-weight: 600;
  font-size: 16px;
  color: var(--text-primary);
}
.mastery-stats {
  font-size: 13px;
  color: var(--text-muted);
}

.color-legend {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}
.legend-label {
  font-size: 11px;
  color: var(--text-muted);
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
  font-size: 11px;
  color: var(--text-muted);
  margin-left: 6px;
}

.mastery-cards {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  align-items: center;
}

.mastery-card {
  padding: 16px 20px;
  border-radius: 14px;
  color: white;
  text-align: center;
  min-width: 130px;
  flex: 1;
  max-width: 200px;
  transition: all 0.4s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.mastery-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, rgba(255,255,255,0.15) 0%, transparent 100%);
  pointer-events: none;
  border-radius: 14px;
}
.mastery-card:hover {
  transform: translateY(-8px) scale(1.03);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15) !important;
}
.mastery-card:active {
  transform: scale(0.97);
}

.card-topic {
  display: block;
  font-size: 13px;
  font-weight: 500;
  text-shadow: 0 1px 8px rgba(0,0,0,0.15);
  position: relative;
  z-index: 1;
}
.card-score {
  display: block;
  font-size: 28px;
  font-weight: 700;
  text-shadow: 0 1px 8px rgba(0,0,0,0.15);
  margin: 4px 0;
  position: relative;
  z-index: 1;
}
.card-btn {
  margin-top: 4px;
  color: white !important;
  border-color: rgba(255,255,255,0.25) !important;
  background: rgba(255,255,255,0.08) !important;
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

.view-all-btn {
  border: 1px solid var(--border-color) !important;
  border-radius: 12px !important;
  background: rgba(128, 128, 128, 0.04) !important;
  color: var(--text-secondary) !important;
  transition: all 0.3s ease !important;
  padding: 12px 20px;
}
.view-all-btn:hover {
  background: rgba(128, 128, 128, 0.10) !important;
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}
.view-all-btn:active {
  transform: scale(0.97);
}

.empty-state {
  color: var(--text-muted);
  padding: 12px 0;
  text-align: center;
  font-size: 14px;
}
.loading-text {
  color: var(--text-muted);
  padding: 8px 0;
}

.resource-tabs {
  margin-top: 4px;
  overflow: visible !important;
}
.resource-tabs :deep(.el-tabs__header) {
  border-bottom: 1px solid var(--border-color);
}
.resource-tabs :deep(.el-tabs__item) {
  color: var(--text-secondary);
  font-size: 15px;
  transition: all 0.3s ease !important;
}
.resource-tabs :deep(.el-tabs__item:hover) {
  color: var(--text-primary);
  transform: translateY(-2px);
}
.resource-tabs :deep(.el-tabs__item.is-active) {
  color: var(--text-primary);
}
.resource-tabs :deep(.el-tabs__active-bar) {
  background: var(--text-primary);
}
.resource-tabs :deep(.el-tabs__content) {
  padding-top: 16px;
  padding-bottom: 80px;
  overflow: visible !important;
  max-height: none !important;
}

/* ===== 评估中心 ===== */
.evaluation-placeholder {
  padding: 8px 0;
}
.evaluation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}
.evaluation-card {
  padding: 24px 20px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}
.evaluation-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
}
.card-icon {
  font-size: 36px;
  margin-bottom: 10px;
}
.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
.card-desc {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}

[data-theme="dark"] .mastery-panel {
  background: rgba(0, 0, 0, 0.25);
}
[data-theme="dark"] .view-all-btn {
  background: rgba(255, 255, 255, 0.03);
}
[data-theme="dark"] .view-all-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

@media (max-width: 768px) {
  .resource-page {
    padding: 16px 14px 100px 14px;
  }
  .resource-topbar h1 {
    font-size: 22px;
  }
  .mastery-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
  .mastery-stats {
    font-size: 12px;
  }
  .mastery-cards {
    flex-direction: column;
  }
  .mastery-card {
    max-width: 100%;
    width: 100%;
    min-width: unset;
  }
  .color-legend {
    flex-wrap: wrap;
  }
  .evaluation-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>