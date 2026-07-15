<template>
  <div class="learning-plan-page">
    <div class="plan-container">
      <!-- ===== 顶部 ===== -->
      <div class="plan-header">
        <div class="header-left">
          <button class="glass-btn back-btn" @click="goBack">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5M12 19l-7-7 7-7"/>
            </svg>
            返回
          </button>
          <h1>学习规划</h1>
          <span class="plan-count">{{ plans.length }} 个规划</span>
        </div>
        <div class="header-actions">
          <button class="glass-btn primary" @click="openCreateDialog">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 5v14M5 12h14"/>
            </svg>
            新建规划
          </button>
          <button class="glass-btn" @click="loadPlans" :disabled="loading">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spinning: loading }">
              <path d="M23 4v6h-6M1 20v-6h6"/>
              <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="divider"></div>

      <!-- ===== 加载状态 ===== -->
      <div v-if="loading" class="loading-state">
        <div class="loader"></div>
        <span>加载中...</span>
      </div>

      <!-- ===== 规划列表 ===== -->
      <div v-else class="plan-grid">
        <div v-for="plan in plans" :key="plan.id" class="plan-card" :data-status="plan.status">
          <div class="plan-card-glow"></div>
          <div class="plan-card-header">
            <span class="plan-status-indicator" :data-status="plan.status"></span>
            <span class="plan-name">{{ plan.name }}</span>
            <span class="plan-status-tag" :data-status="plan.status">
              {{ plan.status === 'active' ? '进行中' : plan.status === 'pending' ? '待开始' : '已完成' }}
            </span>
          </div>
          <div class="plan-card-meta">
            <span>🎯 难度 {{ plan.difficulty || 5 }}</span>
            <span>📚 {{ plan.tasks?.length || 0 }} 个任务</span>
            <span>📅 {{ plan.start_date }} → {{ plan.end_date }}</span>
          </div>
          <div class="plan-card-desc">{{ plan.keywords || '无关键词' }}</div>
          <div class="plan-card-progress">
            <div class="progress-track">
              <div class="progress-fill" :style="{ width: (plan.progress || 0) + '%' }"></div>
            </div>
            <span class="progress-text">{{ plan.progress || 0 }}%</span>
          </div>
          <div class="plan-card-actions">
            <button class="glass-btn primary small" @click="viewPlan(plan.id)">查看</button>
            <button class="glass-btn small" @click="continuePlan(plan.id)" v-if="plan.status === 'active'">继续</button>
            <button class="glass-btn danger small" @click="deletePlan(plan.id)">删除</button>
          </div>
        </div>

        <div v-if="!plans.length" class="empty-state">
          <div class="empty-icon">📋</div>
          <div class="empty-text">暂无学习规划</div>
          <div class="empty-hint">点击「新建规划」开始创建</div>
        </div>
      </div>

      <!-- ===== 自定义毛玻璃弹窗（居中） ===== -->
      <div v-if="showCreateDialog" class="dialog-overlay" @click.self="closeCreateDialog">
        <div class="dialog-glass">
          <div class="dialog-header">
            <h2>新建学习规划</h2>
            <button class="dialog-close" @click="closeCreateDialog">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <div class="dialog-body">
            <div class="dialog-tip">
              <svg class="tip-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 16v-4M12 8h.01"/>
              </svg>
              <span>填写信息后，AI 将自动生成每日学习任务</span>
            </div>

            <div class="form-row">
              <div class="form-group half">
                <label>规划名称</label>
                <input class="glass-input" v-model="newPlan.name" placeholder="如：Python 基础提升" />
              </div>
              <div class="form-group half">
                <label>方向</label>
                <input class="glass-input" v-model="newPlan.major" placeholder="如：编程、数学、英语" />
              </div>
            </div>

            <div class="form-row">
              <div class="form-group half">
                <label>学习阶段</label>
                <select class="glass-input" v-model="newPlan.stage" @change="onStageChange">
                  <option value="小学">小学</option>
                  <option value="初中">初中</option>
                  <option value="高中">高中</option>
                  <option value="大学">大学</option>
                  <option value="研究生">研究生</option>
                  <option value="职场">职场</option>
                </select>
              </div>
              <div class="form-group half">
                <label>年级</label>
                <select class="glass-input" v-model="newPlan.grade">
                  <option v-for="g in gradeOptions" :key="g" :value="g">{{ g }}</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group half">
                <label>难度基数 <span class="hint">(1-20)</span></label>
                <input class="glass-input" type="number" v-model="newPlan.difficulty" min="1" max="20" />
              </div>
              <div class="form-group half">
                <label>每日时长 (分钟)</label>
                <select class="glass-input" v-model="newPlan.dailyMinutes">
                  <option :value="15">15 分钟</option>
                  <option :value="30">30 分钟</option>
                  <option :value="45">45 分钟</option>
                  <option :value="60">60 分钟</option>
                  <option :value="90">90 分钟</option>
                </select>
              </div>
            </div>

            <div class="form-row">
              <div class="form-group half">
                <label>开始日期</label>
                <input class="glass-input" type="date" v-model="newPlan.startDate" />
              </div>
              <div class="form-group half">
                <label>结束日期</label>
                <input class="glass-input" type="date" v-model="newPlan.endDate" />
              </div>
            </div>

            <div class="form-group">
              <label>知识点</label>
              <input class="glass-input" v-model="newPlan.keywords" placeholder="如：哈希表" />
            </div>

            <div class="form-group" v-if="hasDiagnosisData">
              <button class="glass-btn primary" @click="importFromDiagnosis" style="width:100%;">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8M16 6l-4-4-4 4M12 2v13"/>
                </svg>
                从诊断导入
              </button>
            </div>
          </div>

          <div class="dialog-footer">
            <button class="glass-btn" @click="closeCreateDialog">取消</button>
            <button class="glass-btn primary" @click="createPlan" :disabled="creating">
              <span v-if="creating" class="loader-small"></span>
              <span v-else>生成规划</span>
            </button>
          </div>
        </div>
      </div>

      <!-- ===== Agent 调用指示器 ===== -->
      <div v-if="agentCalling" class="agent-indicator">
        <div class="agent-spinner"></div>
        <span>正在调用规划 Agent...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getPlans, deletePlan as apiDeletePlan } from '@/api/learningPlan'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const creating = ref(false)
const agentCalling = ref(false)
const showCreateDialog = ref(false)
const plans = ref([])

const newPlan = ref({
  name: '',
  major: '',
  stage: '大学',
  grade: '大一',
  difficulty: 13,
  dailyMinutes: 30,
  startDate: '',
  endDate: '',
  keywords: ''
})

const gradeOptions = ref(['大一', '大二', '大三', '大四'])

const stageGradeMap = {
  '小学': ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级'],
  '初中': ['初一', '初二', '初三'],
  '高中': ['高一', '高二', '高三'],
  '大学': ['大一', '大二', '大三', '大四'],
  '研究生': ['研一', '研二', '研三'],
  '职场': ['初级', '中级', '高级']
}

const hasDiagnosisData = computed(() => route.query.weaknesses || route.query.strengths)

function onStageChange() {
  gradeOptions.value = stageGradeMap[newPlan.value.stage] || ['大一', '大二', '大三', '大四']
  newPlan.value.grade = gradeOptions.value[0] || ''
}

function importFromDiagnosis() {
  if (route.query.weaknesses) {
    newPlan.value.keywords = route.query.weaknesses.split('、')[0] || ''
    newPlan.value.name = `攻克 ${newPlan.value.keywords || '薄弱点'}`
  }
  ElMessage.success('已导入诊断数据')
}
// 在 script setup 中新增
function goPractice(taskId) {
  router.push(`/do-question/${taskId}`)
}
async function loadPlans() {
  loading.value = true
  try {
    const data = await getPlans(authStore.user.id)
    plans.value = data.plans || []
  } catch (error) {
    console.error('加载规划失败:', error)
    ElMessage.error('加载规划失败')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  const user = authStore.user
  if (user) {
    newPlan.value.stage = user.learning_stage || '大学'
    newPlan.value.grade = user.grade || '大一'
    newPlan.value.major = user.major || ''
    onStageChange()
  }
  newPlan.value.startDate = new Date().toISOString().slice(0, 10)
  const end = new Date()
  end.setDate(end.getDate() + 7)
  newPlan.value.endDate = end.toISOString().slice(0, 10)
  showCreateDialog.value = true
  if (hasDiagnosisData.value) importFromDiagnosis()
}

function closeCreateDialog() {
  showCreateDialog.value = false
  newPlan.value = { name: '', major: '', stage: '大学', grade: '大一', difficulty: 13, dailyMinutes: 30, startDate: '', endDate: '', keywords: '' }
}

async function createPlan() {
  if (!newPlan.value.name.trim()) { ElMessage.warning('请输入规划名称'); return }
  if (!newPlan.value.keywords.trim()) { ElMessage.warning('请输入知识点'); return }
  if (!newPlan.value.startDate || !newPlan.value.endDate) { ElMessage.warning('请选择时间周期'); return }

  const params = new URLSearchParams({
    name: newPlan.value.name,
    stage: newPlan.value.stage,
    grade: newPlan.value.grade,
    major: newPlan.value.major || '',
    difficulty: newPlan.value.difficulty,
    dailyMinutes: newPlan.value.dailyMinutes,
    startDate: newPlan.value.startDate,
    endDate: newPlan.value.endDate,
    keywords: newPlan.value.keywords
  })
  closeCreateDialog()
  router.push(`/plan-preview?${params.toString()}`)
}

async function deletePlan(id) {
  ElMessageBox.confirm('确定要删除这个规划吗？', '确认删除')
    .then(async () => {
      await apiDeletePlan(id)
      await loadPlans()
      ElMessage.success('已删除')
    })
    .catch(() => {})
}

function viewPlan(id) {
  router.push(`/plan-detail/${id}`)
}

function continuePlan(id) {
  router.push(`/plan-detail/${id}`)
}

function goBack() {
  router.push('/evaluation-center')
}

onMounted(() => {
  loadPlans()
})
</script>

<style scoped>
.learning-plan-page {
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
[data-theme="light"] .learning-plan-page {
  background-image: url('/assets/bg/resource_lib_bg.jpg');
}
[data-theme="dark"] .learning-plan-page {
  background-image: url('/assets/bg/resource_lib_bl.jpg');
}

.plan-container {
  max-width: 900px;
  width: 100%;
  padding: 28px 36px;
  border-radius: 20px;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.06);
  box-shadow: 0 8px 48px rgba(0,0,0,0.08);
}
[data-theme="dark"] .plan-container {
  background: rgba(0,0,0,0.30);
}

.plan-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.header-left h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}
.plan-count {
  font-size: 13px;
  color: var(--text-muted);
  padding: 2px 12px;
  border-radius: 12px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.04);
}
.header-actions { display: flex; gap: 8px; }

.glass-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.04);
  cursor: pointer;
  transition: all 0.3s ease;
}
.glass-btn:hover {
  background: rgba(255,255,255,0.08);
  border-color: rgba(255,255,255,0.10);
  transform: translateY(-2px);
}
.glass-btn:active { transform: scale(0.97); }
.glass-btn.primary {
  color: #409EFF;
  background: rgba(64,158,255,0.08);
  border-color: rgba(64,158,255,0.10);
}
.glass-btn.primary:hover {
  background: rgba(64,158,255,0.14);
  border-color: rgba(64,158,255,0.20);
}
.glass-btn.danger {
  color: #f56c6c;
  background: rgba(245,108,108,0.06);
  border-color: rgba(245,108,108,0.06);
}
.glass-btn.danger:hover {
  background: rgba(245,108,108,0.12);
  border-color: rgba(245,108,108,0.12);
}
.glass-btn .icon { width: 18px; height: 18px; }
.glass-btn.small { padding: 4px 12px; font-size: 12px; }
.back-btn .icon { width: 20px; height: 20px; }
.glass-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }
.spinning { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
  margin: 16px 0 20px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 60px 20px;
  color: var(--text-muted);
}
.loader {
  width: 32px;
  height: 32px;
  border: 2px solid rgba(64,158,255,0.12);
  border-top-color: #409EFF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.plan-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.plan-card {
  position: relative;
  padding: 20px 22px;
  border-radius: 14px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.4s ease;
  overflow: hidden;
}
.plan-card:hover {
  transform: translateY(-4px);
  border-color: rgba(255,255,255,0.08);
}
.plan-card[data-status="active"] {
  border-color: rgba(64,158,255,0.12);
  background: rgba(64,158,255,0.04);
}
.plan-card[data-status="pending"] {
  border-color: rgba(245,158,11,0.08);
  background: rgba(245,158,11,0.03);
}
.plan-card[data-status="completed"] {
  border-color: rgba(34,197,94,0.08);
  background: rgba(34,197,94,0.03);
  opacity: 0.6;
}
.plan-card-glow {
  position: absolute;
  top: -40%;
  right: -20%;
  width: 60%;
  height: 120%;
  background: radial-gradient(ellipse, rgba(64,158,255,0.03), transparent 70%);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.6s ease;
}
.plan-card:hover .plan-card-glow { opacity: 1; }

.plan-card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.plan-status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.plan-status-indicator[data-status="active"] { background: #409EFF; box-shadow: 0 0 12px rgba(64,158,255,0.3); }
.plan-status-indicator[data-status="pending"] { background: #F59E0B; box-shadow: 0 0 12px rgba(245,158,11,0.3); }
.plan-status-indicator[data-status="completed"] { background: #22C55E; box-shadow: 0 0 12px rgba(34,197,94,0.3); }
.plan-name { font-size: 16px; font-weight: 600; color: var(--text-primary); flex: 1; }
.plan-status-tag {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 500;
}
.plan-status-tag[data-status="active"] { background: rgba(64,158,255,0.10); color: #409EFF; }
.plan-status-tag[data-status="pending"] { background: rgba(245,158,11,0.10); color: #F59E0B; }
.plan-status-tag[data-status="completed"] { background: rgba(34,197,94,0.10); color: #22C55E; }

.plan-card-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
  flex-wrap: wrap;
}
.plan-card-desc {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 10px;
  line-height: 1.6;
}
.plan-card-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}
.progress-track {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: rgba(255,255,255,0.04);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, #409EFF, #8B5CF6);
  transition: width 0.8s ease;
}
.progress-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  min-width: 36px;
  text-align: right;
}
.plan-card-actions { display: flex; gap: 6px; }

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}
.empty-icon { font-size: 48px; margin-bottom: 12px; opacity: 0.3; }
.empty-text { font-size: 18px; font-weight: 600; color: var(--text-secondary); }
.empty-hint { font-size: 14px; margin-top: 4px; opacity: 0.5; }

/* ===== 弹窗 - 居中 ===== */
.dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(4px);
  animation: fadeIn 0.3s ease;
}

.dialog-glass {
  max-width: 560px;
  width: 92%;
  max-height: 90vh;
  overflow-y: auto;
  padding: 28px 32px;
  border-radius: 20px;
  background: rgba(30,30,60,0.85);
  backdrop-filter: blur(32px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 16px 64px rgba(0,0,0,0.3);
  animation: scaleIn 0.3s ease;
  margin-top: 300px;          /* ← 往下挪 60px */
}
@keyframes fadeIn {
  0% { opacity: 0; }
  100% { opacity: 1; }
}

.dialog-glass {
  max-width: 560px;
  width: 92%;
  max-height: 90vh;
  overflow-y: auto;
  padding: 28px 32px;
  border-radius: 20px;
  background: rgba(30,30,60,0.85);
  backdrop-filter: blur(32px);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 16px 64px rgba(0,0,0,0.3);
  animation: scaleIn 0.3s ease;
}
@keyframes scaleIn {
  0% { opacity: 0; transform: scale(0.92); }
  100% { opacity: 1; transform: scale(1); }
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.dialog-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin: 0;
}
.dialog-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.04);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.3s ease;
}
.dialog-close:hover {
  background: rgba(255,255,255,0.08);
  color: #fff;
}
.dialog-close svg { width: 18px; height: 18px; }

.dialog-body { display: flex; flex-direction: column; gap: 12px; }
.dialog-tip {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(64,158,255,0.04);
  border: 1px solid rgba(64,158,255,0.04);
}
.tip-icon { width: 18px; height: 18px; flex-shrink: 0; color: #409EFF; margin-top: 1px; }
.dialog-tip span { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }

.form-row { display: flex; gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 4px; flex: 1; }
.form-group.half { flex: 0.5; }
.form-group label { font-size: 13px; font-weight: 500; color: var(--text-secondary); }
.glass-input {
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary);
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
  transition: all 0.3s ease;
  outline: none;
  font-family: inherit;
}
.glass-input::placeholder { color: var(--text-muted); opacity: 0.4; }
.glass-input:focus {
  border-color: rgba(64,158,255,0.15);
  background: rgba(255,255,255,0.06);
  box-shadow: 0 0 0 4px rgba(64,158,255,0.04);
}
select.glass-input { cursor: pointer; appearance: none; }
select.glass-input option { background: #1a1a2e; color: #fff; }

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255,255,255,0.04);
}
.loader-small {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.12);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.agent-indicator {
  position: fixed;
  bottom: 30px;
  right: 30px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  border-radius: 14px;
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.04);
  box-shadow: 0 8px 32px rgba(0,0,0,0.12);
  z-index: 999;
  animation: slideUp 0.4s ease;
}
.agent-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(64,158,255,0.12);
  border-top-color: #409EFF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
.agent-indicator span { font-size: 14px; color: var(--text-secondary); }
@keyframes slideUp { 0% { opacity: 0; transform: translateY(20px); } 100% { opacity: 1; transform: translateY(0); } }

@media (max-width: 640px) {
  .plan-container { padding: 16px; }
  .plan-header { flex-direction: column; align-items: stretch; }
  .plan-grid { grid-template-columns: 1fr; }
  .header-left h1 { font-size: 20px; }
  .form-row { flex-direction: column; gap: 8px; }
  .form-group.half { flex: 1; }
  .dialog-glass { padding: 20px; max-width: 95%; }
}
</style>