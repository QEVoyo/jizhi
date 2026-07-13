<template>
  <div class="profile-card-page">
    <div class="profile-container">
      <!-- ===== 顶部 ===== -->
      <div class="profile-header">
        <div class="header-left">
          <el-button text class="back-btn" @click="goBack">
            <i class="fas fa-arrow-left"></i> 返回
          </el-button>
          <h1>六维画像</h1>
          <el-tag size="small" type="info">{{ generateDate }}</el-tag>
        </div>
        <el-button size="small" type="primary" @click="refreshData" :loading="loading">
          <i class="fas fa-sync"></i> 刷新
        </el-button>
      </div>

      <el-divider />

      <div v-if="loading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> 加载中...
      </div>

      <div v-else class="profile-content">
        <!-- ===== 1. 知识基础 ===== -->
        <div class="dimension-section">
          <div class="section-title">
            <span class="section-icon">K</span> 知识基础
          </div>
          <div class="section-body">
            <div v-if="!dimData.knowledge_base?.list?.length" class="empty-tip">
              暂无数据
            </div>
            <div v-else>
              <div
                v-for="item in dimData.knowledge_base.list"
                :key="item.name"
                class="topic-progress"
              >
                <span class="topic-name">{{ item.name }}</span>
                <div class="progress-track">
                  <div
                    class="progress-fill"
                    :style="{
                      width: item.score + '%',
                      background: getColor(item.score)
                    }"
                  ></div>
                </div>
                <span class="topic-score">{{ item.score }}%</span>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 2. 认知风格（饼图） ===== -->
        <div class="dimension-section">
          <div class="section-title">
            <span class="section-icon">C</span> 认知风格
          </div>
          <div class="section-body">
            <div v-if="!Object.keys(dimData.cognitive_style?.distribution || {}).length" class="empty-tip">
              暂无数据
            </div>
            <div v-else class="pie-wrapper">
              <div ref="pieChartRef" style="width: 100%; height: 260px;"></div>
              <div class="pie-label">
                {{ dimData.cognitive_style?.label || '未分析' }}
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 3. 易错偏好 ===== -->
        <div class="dimension-section">
          <div class="section-title">
            <span class="section-icon">E</span> 易错偏好
          </div>
          <div class="section-body">
            <div v-if="dimData.mistake_pattern?.total === 0" class="empty-tip">
              暂无错题
            </div>
            <div v-else>
              <div class="mistake-stats">
                <span class="stat-item">
                  <span class="stat-dot learning"></span> 未攻克：{{ dimData.mistake_pattern.learning?.length || 0 }}
                </span>
                <span class="stat-item">
                  <span class="stat-dot conquered"></span> 已攻克：{{ dimData.mistake_pattern.conquered?.length || 0 }}
                </span>
                <span class="stat-item">
                  攻克率：{{ dimData.mistake_pattern.conquered_rate || 0 }}%
                </span>
              </div>
              <div v-if="dimData.mistake_pattern.learning?.length" class="mistake-list">
                <span class="mistake-tag learning" v-for="t in dimData.mistake_pattern.learning" :key="t">
                  {{ t }}
                </span>
              </div>
              <div v-if="dimData.mistake_pattern.conquered?.length" class="mistake-list">
                <span class="mistake-tag conquered" v-for="t in dimData.mistake_pattern.conquered" :key="t">
                  {{ t }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 4. 学习目标 ===== -->
        <div class="dimension-section">
          <div class="section-title">
            <span class="section-icon">G</span> 学习目标
          </div>
          <div class="section-body">
            <div v-if="!dimData.learning_goal?.sets?.length" class="empty-tip">
              暂无题集
            </div>
            <div v-else>
              <div v-for="s in dimData.learning_goal.sets" :key="s.name" class="set-item">
                <span class="set-name">{{ s.name }}</span>
                <span class="set-count">{{ s.question_count }} 题</span>
              </div>
              <div class="set-summary">
                共 {{ dimData.learning_goal.total_sets }} 个题集，{{ dimData.learning_goal.total_questions }} 道题目
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 5. 学习进度 ===== -->
        <div class="dimension-section">
          <div class="section-title">
            <span class="section-icon">P</span> 学习进度
          </div>
          <div class="section-body">
            <div v-if="!dimData.learning_progress?.total_questions" class="empty-tip">
              暂无数据
            </div>
            <div v-else>
              <div class="progress-item">
                总题目：<strong>{{ dimData.learning_progress.total_questions }}</strong> 道
              </div>
              <div class="progress-item">
                平均掌握度：<strong>{{ dimData.learning_progress.avg_mastery || 0 }}%</strong>
              </div>
              <div class="progress-track big">
                <div
                  class="progress-fill"
                  :style="{
                    width: (dimData.learning_progress.avg_mastery || 0) + '%',
                    background: getColor(dimData.learning_progress.avg_mastery || 0)
                  }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 6. 兴趣领域 ===== -->
        <div class="dimension-section">
          <div class="section-title">
            <span class="section-icon">I</span> 兴趣领域
          </div>
          <div class="section-body">
            <div v-if="!dimData.interest_field?.list?.length" class="empty-tip">
              暂无数据
            </div>
            <div v-else class="interest-cloud">
              <span
                v-for="t in dimData.interest_field.list"
                :key="t.name"
                class="interest-tag"
                :style="{
                  fontSize: (14 + t.count * 2) + 'px',
                  color: getRandomColor(),
                  background: getRandomColor() + '15',
                  borderColor: getRandomColor()
                }"
              >
                {{ t.name }}
                <span class="tag-count">{{ t.count }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- ===== 学习建议 ===== -->
        <div class="advice-section">
          <div class="advice-header">
            <span class="advice-icon">A</span> 针对性建议
          </div>
          <div v-if="adviceLoading" class="advice-loading">
            <i class="fas fa-spinner fa-spin"></i> 生成中...
          </div>
          <div v-else-if="adviceContent" class="advice-content">
            {{ adviceContent }}
          </div>
          <div v-else class="advice-empty">
            <el-button type="primary" @click="generateAdvice">
              <i class="fas fa-magic"></i> 生成建议
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const adviceLoading = ref(false)
const generateDate = ref('')
const adviceContent = ref('')
const pieChartRef = ref(null)
let pieChart = null

const dimData = ref({
  knowledge_base: { list: [] },
  cognitive_style: { distribution: {} },
  mistake_pattern: { total: 0, learning: [], conquered: [], conquered_rate: 0 },
  learning_goal: { sets: [], total_sets: 0, total_questions: 0 },
  learning_progress: { total_questions: 0, avg_mastery: 0 },
  interest_field: { list: [] }
})

const masteryColors = [
  '#FF0000', '#FF1A00', '#FF3300', '#FF4D00', '#FF6600',
  '#FF8000', '#FF9900', '#FFB300', '#FFCC00', '#FFE600',
  '#D4E000', '#A8D500', '#7DCC00', '#52C200', '#26B800',
  '#00AD00', '#00A300', '#009900', '#008000', '#006600'
]

const colorPalette = [
  '#409EFF', '#8B5CF6', '#F59E0B', '#22C55E', '#EC4899',
  '#06B6D4', '#F472B6', '#34D399', '#FB923C', '#A78BFA',
  '#60A5FA', '#F87171', '#2DD4BF', '#F97316', '#818CF8',
  '#34D399', '#F472B6', '#E879F9'
]

function getColor(score) {
  const index = Math.min(Math.floor(score / 5), 19)
  return masteryColors[index] || '#888'
}

function getRandomColor() {
  return colorPalette[Math.floor(Math.random() * colorPalette.length)]
}

function loadPieChart() {
  if (!pieChartRef.value) return
  if (pieChart) { pieChart.dispose(); pieChart = null }

  const dist = dimData.value.cognitive_style?.distribution || {}
  const data = Object.entries(dist).map(([name, value]) => ({ name, value }))
  if (!data.length) return

  pieChart = echarts.init(pieChartRef.value)
  const colors = ['#409EFF', '#8B5CF6', '#F59E0B', '#22C55E', '#EC4899', '#06B6D4']

  pieChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} 道 ({d}%)',
      backgroundColor: 'rgba(0,0,0,0.7)',
      borderColor: 'rgba(255,255,255,0.1)',
      textStyle: { color: '#fff' }
    },
    color: colors,
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      avoidLabelOverlap: true,
      itemStyle: {
        borderRadius: 8,
        borderColor: 'rgba(255,255,255,0.08)',
        borderWidth: 2
      },
      label: {
        color: 'rgba(255,255,255,0.8)',
        fontSize: 13,
        formatter: '{b}\n{d}%'
      },
      labelLine: {
        lineStyle: { color: 'rgba(255,255,255,0.12)' }
      },
      data: data,
      animationDuration: 800
    }]
  })
  pieChart.resize()
}

async function loadData() {
  loading.value = true
  try {
    const res = await fetch(
      `${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/evaluation/profile-data?user_id=${authStore.user.id}`,
      { headers: { Authorization: `Bearer ${authStore.token}` } }
    )
    dimData.value = await res.json()
    generateDate.value = new Date().toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    })
    await nextTick()
    setTimeout(() => loadPieChart(), 300)
  } catch (error) {
    console.error('加载失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

async function refreshData() {
  await loadData()
  ElMessage.success('已刷新')
}

function goBack() {
  router.push('/evaluation-center')
}

async function generateAdvice() {
  adviceLoading.value = true
  try {
    const dims = [
      { name: '知识基础', score: dimData.value.knowledge_base?.avg_score || 0 },
      { name: '认知风格', score: 50 },
      { name: '易错偏好', score: dimData.value.mistake_pattern?.conquered_rate || 0 },
      { name: '学习目标', score: dimData.value.learning_goal?.total_sets ? 60 : 0 },
      { name: '学习进度', score: dimData.value.learning_progress?.avg_mastery || 0 },
      { name: '兴趣领域', score: dimData.value.interest_field?.list?.length ? 60 : 0 }
    ]
    const weak = dims.filter(d => d.score < 60).map(d => d.name)
    const strong = dims.filter(d => d.score >= 80).map(d => d.name)

    const prompt = `
根据以下六维学习画像数据生成个性化学习建议：
${dims.map(d => `${d.name}：${d.score}%`).join('\n')}
薄弱维度：${weak.length ? weak.join('、') : '无'}
优势维度：${strong.length ? strong.join('、') : '无'}
请给出具体、可操作的学习建议，重点针对薄弱维度，200字以内。`

    const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/chat/advice`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`
      },
      body: JSON.stringify({ prompt, user_id: authStore.user.id })
    })
    const result = await response.json()
    adviceContent.value = result.advice || '建议重点关注薄弱维度，制定专项提升计划。'
  } catch {
    adviceContent.value = '生成建议失败，请稍后重试。'
  } finally {
    adviceLoading.value = false
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.profile-card-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 30px 20px;
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  background-repeat: no-repeat;
}
[data-theme="light"] .profile-card-page {
  background-image: url('/assets/bg/resource_lib_bg.jpg');
}
[data-theme="dark"] .profile-card-page {
  background-image: url('/assets/bg/resource_lib_bl.jpg');
}

.profile-container {
  max-width: 860px;
  width: 100%;
  margin: 0 auto;
  padding: 28px 36px;
  border-radius: 18px;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 8px 32px rgba(0,0,0,0.06);
}
[data-theme="dark"] .profile-container {
  background: rgba(0,0,0,0.30);
}

.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.back-btn {
  color: var(--text-secondary) !important;
  font-size: 15px;
  padding: 4px 8px;
  transition: all 0.3s ease !important;
}
.back-btn:hover {
  color: var(--text-primary) !important;
  transform: translateX(-2px);
  background: rgba(255,255,255,0.06);
}
.profile-header h1 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
}

.el-divider { margin: 12px 0; }
.loading-state { text-align: center; padding: 60px 20px; color: var(--text-muted); }

.dimension-section {
  margin-bottom: 20px;
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255,255,255,0.02);
}
.section-title {
  padding: 12px 18px;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.3px;
  color: var(--text-primary);
  background: rgba(255,255,255,0.02);
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.section-icon {
  display: inline-block;
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  border-radius: 6px;
  background: rgba(64,158,255,0.08);
  color: #409EFF;
  margin-right: 10px;
}
.section-body { padding: 14px 18px; }
.empty-tip { color: var(--text-muted); font-size: 13px; text-align: center; padding: 8px 0; }

.topic-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.topic-progress:last-child { margin-bottom: 0; }
.topic-name {
  font-size: 13px;
  color: var(--text-secondary);
  min-width: 80px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.progress-track {
  flex: 1;
  height: 5px;
  border-radius: 3px;
  background: rgba(255,255,255,0.06);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}
.topic-score {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 40px;
  text-align: right;
}
.progress-track.big { height: 8px; }

.pie-wrapper { position: relative; }
.pie-label {
  text-align: center;
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 6px;
  letter-spacing: 0.5px;
}

.mistake-stats {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.stat-item { display: flex; align-items: center; gap: 6px; }
.stat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.stat-dot.learning { background: #EF4444; }
.stat-dot.conquered { background: #22C55E; }

.mistake-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
.mistake-tag {
  font-size: 12px;
  padding: 3px 12px;
  border-radius: 12px;
  font-weight: 500;
}
.mistake-tag.learning {
  background: rgba(239,68,68,0.12);
  color: #EF4444;
}
.mistake-tag.conquered {
  background: rgba(34,197,94,0.12);
  color: #22C55E;
}

.set-item {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  font-size: 13px;
  color: var(--text-secondary);
  border-bottom: 1px solid rgba(255,255,255,0.03);
}
.set-item:last-child { border-bottom: none; }
.set-name { font-weight: 500; color: var(--text-primary); }
.set-count { color: var(--text-muted); font-size: 12px; }
.set-summary {
  margin-top: 10px;
  padding-top: 10px;
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
  border-top: 1px solid rgba(255,255,255,0.04);
}

.progress-item { font-size: 13px; color: var(--text-secondary); margin-bottom: 4px; }
.progress-item strong { color: var(--text-primary); }

.interest-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  padding: 4px 0;
}
.interest-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 14px;
  border-radius: 16px;
  border: 1px solid transparent;
  transition: all 0.25s ease;
  cursor: default;
  font-weight: 500;
}
.interest-tag:hover {
  transform: scale(1.05);
  opacity: 0.85;
}
.tag-count {
  font-size: 10px;
  opacity: 0.6;
}

.advice-section {
  margin-top: 8px;
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 12px;
  padding: 16px 20px;
  background: rgba(255,255,255,0.02);
}
.advice-header {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}
.advice-icon {
  display: inline-block;
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  font-size: 12px;
  font-weight: 700;
  border-radius: 6px;
  background: rgba(64,158,255,0.08);
  color: #409EFF;
  margin-right: 10px;
}
.advice-loading { color: var(--text-muted); padding: 8px 0; }
.advice-content {
  padding: 12px 16px;
  border-radius: 8px;
  background: rgba(64,158,255,0.05);
  border-left: 3px solid #409EFF;
  line-height: 1.8;
  color: var(--text-primary);
  font-size: 14px;
  white-space: pre-wrap;
}
.advice-empty { text-align: center; padding: 8px 0; }

@media (max-width: 640px) {
  .profile-container { padding: 16px 14px; }
  .profile-header { flex-direction: column; align-items: stretch; }
  .topic-name { min-width: 60px; font-size: 12px; }
  .mistake-stats { gap: 12px; font-size: 12px; }
}
</style>