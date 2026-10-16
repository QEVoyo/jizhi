<template>
  <div class="dashboard">
    <h2 class="page-title">管理主面板</h2>
    <p class="page-subtitle">基智学习助手 · 系统概览</p>

    <!-- 统计卡片 -->
    <AdminLoading :visible="loading" text="加载仪表盘..." />
    <!-- 每张卡都能点进对应的详情页。落点见各卡上的 go-* 属性，
         全部集中在下面这段——卡片散落在 10 个 div 里，路由改起来最容易漏。 -->
    <div class="stat-grid" v-if="!loading">
      <div class="stat-card" @click="$router.push('/admin/users')">
        <div class="stat-icon users">
          <i class="fas fa-users"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.total_users || 0 }}</div>
          <div class="stat-label">总用户数</div>
        </div>
        <i class="fas fa-arrow-right card-go"></i>
      </div>

      <div class="stat-card" @click="$router.push('/admin/users?days=1')">
        <div class="stat-icon new-users">
          <i class="fas fa-user-plus"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.today_new_users || 0 }}</div>
          <div class="stat-label">今日新增</div>
        </div>
        <i class="fas fa-arrow-right card-go"></i>
      </div>

      <!-- 做题数（总/今日）2026-10-16 撤掉：数据源 question_records 几乎没在写，
           面板上长期是「7 / 0」，看着像坏了、也说明不了任何事。 -->

      <div class="stat-card warning" @click="$router.push('/admin/reports')">
        <div class="stat-icon reports">
          <i class="fas fa-flag"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.pending_reports || 0 }}</div>
          <div class="stat-label">待处理举报</div>
        </div>
        <i class="fas fa-arrow-right card-go"></i>
      </div>

      <div class="stat-card" @click="$router.push('/admin/feedback')">
        <div class="stat-icon feedback">
          <i class="fas fa-message"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.pending_feedback || 0 }}</div>
          <div class="stat-label">待处理反馈</div>
        </div>
        <i class="fas fa-arrow-right card-go"></i>
      </div>

      <div class="stat-card" @click="$router.push('/admin/plans')">
        <div class="stat-icon plans">
          <i class="fas fa-list-check"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.total_plans || 0 }}</div>
          <div class="stat-label">学习计划数</div>
        </div>
        <i class="fas fa-arrow-right card-go"></i>
      </div>

      <div class="stat-card" @click="$router.push('/admin/questions')">
        <div class="stat-icon bank">
          <i class="fas fa-database"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ stats.question_bank_count || 0 }}</div>
          <div class="stat-label">题库总量</div>
        </div>
        <i class="fas fa-arrow-right card-go"></i>
      </div>

      <!-- ===== AI 生成审计（2026-10-16 新增）=====
           埋点在 agents/ 的客户端层，所以这里数的是**真的打给模型的每一次调用**，
           不区分走没走安全网关。 -->
      <div class="stat-card" @click="$router.push('/admin/security?tab=genaudit')">
        <div class="stat-icon ai">
          <i class="fas fa-robot"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ metric('AI 调用总数', stats.ai_calls_total) }}</div>
          <div class="stat-label">AI 调用总数</div>
        </div>
        <i class="fas fa-arrow-right card-go"></i>
      </div>

      <div class="stat-card" @click="$router.push('/admin/security?tab=genaudit')">
        <div class="stat-icon ai-today">
          <i class="fas fa-bolt"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ metric('AI 今日调用', stats.ai_calls_today) }}</div>
          <div class="stat-label">今日 AI 调用</div>
        </div>
        <i class="fas fa-arrow-right card-go"></i>
      </div>

      <div class="stat-card" @click="$router.push('/admin/security?tab=genaudit')">
        <div class="stat-icon rate">
          <i class="fas fa-heart-pulse"></i>
        </div>
        <div class="stat-body">
          <!-- 一次调用都没有时不是 0%，是"无从谈起" —— 显示 — 而不是 0%，
               否则面板会假装"成功率是 0"，那比没有数字更容易误导。 -->
          <div class="stat-value">{{ successRate === null ? '—' : successRate + '%' }}</div>
          <div class="stat-label">AI 成功率</div>
        </div>
        <i class="fas fa-arrow-right card-go"></i>
      </div>

      <div class="stat-card" @click="$router.push('/admin/security?tab=genaudit')">
        <div class="stat-icon coverage">
          <i class="fas fa-plug-circle-check"></i>
        </div>
        <div class="stat-body">
          <div class="stat-value">{{ coverageText }}</div>
          <div class="stat-label">已接入生成点</div>
        </div>
        <i class="fas fa-arrow-right card-go"></i>
      </div>
    </div>

    <!-- 取不到的指标。后端 errors 就是为这个留的 —— 不摆出来的话，
         「查询失败」和「业务上真的是 0」在面板上长得一模一样。 -->
    <div v-if="errorList.length" class="err-banner">
      <i class="fas fa-triangle-exclamation"></i>
      <div>
        <strong>下面这些数取不到</strong>（面板里显示为 —，不是 0）：
        <span v-for="e in errorList" :key="e.label" class="err-item">
          {{ e.label }}（{{ e.reason }}）
        </span>
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
import { ref, computed, onMounted } from 'vue'
import { getDashboard } from '@/api/admin'
import { ElMessage } from 'element-plus'
import AdminLoading from '@/components/admin/AdminLoading.vue'

const loading = ref(false)
const stats = ref({})

// 后端 errors = {指标名: 原因}。key 就是下面几个标签，两边必须对得上。
// 有它才能把「取不到」和「真的是 0」分开 —— 这正是后端留这个字段的目的，
// 之前前端压根没渲染过，等于白留。
const errorMap = computed(() => stats.value.errors || {})
const errorList = computed(() =>
  Object.entries(errorMap.value).map(([label, reason]) => ({ label, reason }))
)
function metric(label, value) {
  return label in errorMap.value ? '—' : (value ?? 0)
}

// 成功率：ok / 总数。
// ⚠️ 总数是 0 时返回 null 而不是 0 —— 一次都没调用过时，
//    「成功率 0%」是个假陈述（根本没有可失败的东西）。
const successRate = computed(() => {
  const total = stats.value.ai_calls_total
  if (!total) return null
  return Math.round((stats.value.ai_calls_ok || 0) / total * 100)
})

// 埋点覆盖率。⚠️ 分子分母都来自后端登记的常量，不是查库查出来的 ——
// 查库只能查出"已经记了多少"，那正是它要防的（见 utils/gen_audit.py）。
const coverageText = computed(() => {
  const c = stats.value.ai_entry_points
  if (!c || !c.total) return '—'
  return `${c.migrated} / ${c.total}`
})

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
  color: var(--text-primary);
  margin: 0 0 4px;
}

.page-subtitle {
  font-size: 13px;
  color: var(--text-muted);
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
  position: relative;          /* 给右上角的进入箭头定位 */
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  backdrop-filter: blur(12px);
  border: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent);
  border-radius: 14px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
  cursor: pointer;             /* 每张卡都能点进详情页 */
}

/* 进入箭头：默认很淡，悬停才亮。卡片本身已经有 hover 抬升，
   再给一个"点得进去"的显式提示 —— 光靠光标形状在触控板上看不出来。 */
.card-go {
  position: absolute;
  top: 12px;
  right: 14px;
  font-size: 11px;
  color: var(--text-muted);
  opacity: 0.35;
  transition: all 0.25s ease;
}
.stat-card:hover .card-go {
  opacity: 1;
  transform: translateX(2px);
}
.stat-card:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  transform: translateY(-2px);
  border-color: var(--text-muted);
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
.stat-icon.users     { background: color-mix(in srgb, var(--brand) 15%, transparent); color: var(--brand); }
.stat-icon.new-users { background: rgba(103, 194, 58, 0.15); color: #67c23a; }
.stat-icon.questions { background: rgba(230, 162, 60, 0.15); color: #e6a23c; }
.stat-icon.today-q   { background: rgba(245, 108, 108, 0.15); color: #f56c6c; }
.stat-icon.reports   { background: rgba(245, 108, 108, 0.18); color: #f56c6c; }
.stat-icon.feedback  { background: rgba(144, 147, 153, 0.15); color: #909399; }
.stat-icon.plans     { background: color-mix(in srgb, var(--brand) 12%, transparent); color: var(--brand); }
.stat-icon.bank      { background: rgba(20, 184, 166, 0.15); color: #14b8a6; }
.stat-icon.ai        { background: rgba(124, 58, 237, 0.15); color: #7c3aed; }
.stat-icon.ai-today  { background: rgba(124, 58, 237, 0.10); color: #8b5cf6; }
.stat-icon.rate      { background: rgba(103, 194, 58, 0.15); color: #67c23a; }
.stat-icon.coverage  { background: rgba(144, 147, 153, 0.15); color: #909399; }

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* ===== 取数失败提示 ===== */
.err-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin: -16px 0 28px;
  padding: 12px 16px;
  border-radius: 10px;
  background: rgba(230, 162, 60, 0.10);
  border: 1px solid rgba(230, 162, 60, 0.28);
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.6;
}
.err-banner i { color: #e6a23c; margin-top: 3px; }
.err-item { display: inline-block; margin-left: 10px; color: var(--text-muted); }

/* ===== 快捷操作 ===== */
.quick-actions h3 {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-secondary);
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
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent);
  border-radius: 10px;
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s ease;
}
.action-btn:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 7%, transparent);
  border-color: var(--text-muted);
  transform: translateY(-1px);
  color: var(--text-primary);
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
