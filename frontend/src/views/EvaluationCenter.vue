<template>
  <div class="evaluation-center-page">
    <div class="evaluation-container">
      <!-- ===== 顶部 ===== -->
      <div class="evaluation-header">
        <div class="header-left">
          <el-button text class="back-btn" @click="goBack">
            <i class="fas fa-arrow-left"></i> 返回
          </el-button>
          <h1>📊 评估中心</h1>
        </div>
      </div>

      <el-divider />

      <!-- ===== 内容 ===== -->
      <div class="evaluation-content">
        <div class="evaluation-grid">
          <!-- 1. 学情报告 -->
          <div class="evaluation-card" @click="goReport">
            <div class="card-icon">📈</div>
            <div class="card-title">学情报告</div>
            <div class="card-desc">查看学习进度、掌握度变化趋势</div>
          </div>

          <!-- 2. 六维画像 -->
          <div class="evaluation-card" @click="goProfile">
            <div class="card-icon">🧠</div>
            <div class="card-title">六维画像</div>
            <div class="card-desc">知识基础、认知风格、易错点偏好等</div>
          </div>

          <!-- 3. 评估表 -->
          <div class="evaluation-card" @click="goAssessment">
            <div class="card-icon">📋</div>
            <div class="card-title">评估表</div>
            <div class="card-desc">知识点掌握度评估与建议</div>
          </div>

          <!-- 4. 学习规划 -->
          <div class="evaluation-card" @click="goPlan">
            <div class="card-icon">🚀</div>
            <div class="card-title">学习规划</div>
            <div class="card-desc">基于诊断生成个性化学习规划</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goBack() {
  router.push('/resource-lib')
}

function goReport() {
  router.push('/evaluation-report')
}

function goProfile() {
  router.push('/profile-card')
}

function goAssessment() {
  router.push('/evaluation-table')
}

function goPlan() {
  router.push('/learning-plan')
}
</script>

<style scoped>
.evaluation-center-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding: 30px 20px;
  background: transparent;
}

[data-theme="light"] .evaluation-center-page {
  background-image: url('/assets/bg/resource_lib_bg.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}
[data-theme="dark"] .evaluation-center-page {
  background-image: url('/assets/bg/resource_lib_bl.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.evaluation-container {
  max-width: 820px;
  width: 100%;
  padding: 28px 36px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
}

[data-theme="dark"] .evaluation-container {
  background: rgba(0, 0, 0, 0.30);
}

.evaluation-header {
  display: flex;
  align-items: center;
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
  background: rgba(255, 255, 255, 0.06);
}
.evaluation-header h1 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
}

.el-divider {
  margin: 12px 0;
}

.evaluation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
  padding: 8px 0;
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

@media (max-width: 640px) {
  .evaluation-container {
    padding: 16px 14px;
  }
  .evaluation-header h1 {
    font-size: 18px;
  }
  .evaluation-grid {
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }
  .evaluation-card {
    padding: 16px 12px;
  }
  .card-icon {
    font-size: 28px;
  }
  .card-title {
    font-size: 14px;
  }
  .card-desc {
    font-size: 12px;
  }
}
</style>