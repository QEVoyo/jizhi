<template>
  <div class="dashboard">
    <h2 class="page-title">管理主面板</h2>
    <p class="page-subtitle">基智学习助手 · 系统概览</p>

    <!-- 统计卡片 -->
    <AdminLoading :visible="loading" text="加载仪表盘..." />
    <div class="stat-grid" v-if="!loading">
      <div class="stat-card">
        <div class="stat-icon users">
          <i class="fas fa-users"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.total_users || 0 }}</div>
          <div class="stat-label">总用户数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon new-users">
          <i class="fas fa-user-plus"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.today_new_users || 0 }}</div>
          <div class="stat-label">今日新增</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon questions">
          <i class="fas fa-pen-to-square"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.total_questions_done || 0 }}</div>
          <div class="stat-label">总做题数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon today-q">
          <i class="fas fa-fire"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.today_questions_done || 0 }}</div>
          <div class="stat-label">今日做题</div>
        </div>
      </div>

      <div class="stat-card warning" @click="$router.push('/admin/reports')">
        <div class="stat-icon reports">
          <i class="fas fa-flag"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.pending_reports || 0 }}</div>
          <div class="stat-label">待处理举报</div>
        </div>
      </div>

      <div class="stat-card" @click="$router.push('/admin/feedback')">
        <div class="stat-icon feedback">
          <i class="fas fa-message"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.pending_feedback || 0 }}</div>
          <div class="stat-label">待处理反馈</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon plans">
          <i class="fas fa-list-check"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.total_plans || 0 }}</div>
          <div class="stat-label">学习计划数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon bank">
          <i class="fas fa-database"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.question_bank_count || 0 }}</div>
          <div class="stat-label">题库总量</div>
        </div>
      </div>
    </div>

    <!-- 快捷入口 -->
    <div class="quick-actions">
      <h3>快捷操作</h3>
      <div class="action-grid">
        <button class="action-btn" @click="$router.push('/admin/users')">
          <i class="fas fa-users"></i> 用户管理
        </button>
        <button class="action-btn" @click="$router.push('/admin/reports')">
          <i class="fas fa-shield-halved"></i> 举报审核
          <span v-if="stats.pending_reports" class="badge">{{ stats.pending_reports }}</span>
        </button>
        <button class="action-btn" @click="$router.push('/admin/questions')">
          <i class="fas fa-book"></i> 题库管理
        </button>
        <button class="action-btn" @click="$router.push('/admin/announcements')">
          <i class="fas fa-bullhorn"></i> 发布公告
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDashboard } from '@/api/admin'
import { ElMessage } from 'element-plus'
import AdminLoading from '@/components/admin/AdminLoading.vue'

const loading = ref(false)
const stats = ref({})

async function loadStats() {
  loading.value = true
  try {
    stats.value = await getDashboard()
  } catch (e) {
    ElMessage.error('加载仪表盘失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadStats)
</script>

<style scoped>
.dashboard { max-width: 1100px; }

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #e0e0e0;
  margin: 0 0 4px;
}

.page-subtitle {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.35);
  margin: 0 0 28px;
}

/* ===== 统计卡片 ===== */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
  cursor: default;
}
.stat-card:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.1);
}
.stat-card.warning {
  cursor: pointer;
  border-color: rgba(245, 108, 108, 0.15);
}
.stat-card.warning:hover {
  border-color: rgba(245, 108, 108, 0.3);
  background: rgba(245, 108, 108, 0.06);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}
.stat-icon.users     { background: rgba(64, 158, 255, 0.15); color: #409eff; }
.stat-icon.new-users { background: rgba(103, 194, 58, 0.15); color: #67c23a; }
.stat-icon.questions { background: rgba(230, 162, 60, 0.15); color: #e6a23c; }
.stat-icon.today-q   { background: rgba(245, 108, 108, 0.15); color: #f56c6c; }
.stat-icon.reports   { background: rgba(245, 108, 108, 0.18); color: #f56c6c; }
.stat-icon.feedback  { background: rgba(144, 147, 153, 0.15); color: #909399; }
.stat-icon.plans     { background: rgba(64, 158, 255, 0.12); color: #409eff; }
.stat-icon.bank      { background: rgba(20, 184, 166, 0.15); color: #14b8a6; }

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #e0e0e0;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 2px;
}

/* ===== 快捷操作 ===== */
.quick-actions h3 {
  font-size: 15px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 14px;
}

.action-grid {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.action-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 22px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s ease;
}
.action-btn:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.12);
  transform: translateY(-1px);
  color: #fff;
}

.action-btn .badge {
  position: absolute;
  top: -6px;
  right: -6px;
  background: #f56c6c;
  color: #fff;
  font-size: 11px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}
</style>
