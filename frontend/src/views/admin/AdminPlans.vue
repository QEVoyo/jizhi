<template>
  <div class="admin-plans">
    <div class="page-header">
      <h2 class="page-title">学习计划</h2>
      <div class="header-actions">
        <el-input v-model="search" placeholder="搜索计划名 / 学科 / 考纲..."
                  size="default" prefix-icon="Search" clearable
                  @input="onSearch" class="search-input" />
        <el-select v-model="statusFilter" placeholder="状态" size="default"
                   @change="load(1)" class="filter-select">
          <el-option label="全部状态" value="" />
          <el-option v-for="s in STATUSES" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>
      </div>
    </div>

    <div class="table-wrap">
      <AdminLoading :visible="loading" text="加载学习计划..." />
      <table class="data-table">
        <thead>
          <tr>
            <th>计划</th>
            <th>用户</th>
            <th>学科</th>
            <th>周期</th>
            <th>进度</th>
            <th>状态</th>
            <th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in plans" :key="p.id">
            <td>
              <div class="plan-name">{{ p.name || '（未命名）' }}</div>
              <div class="plan-sub">
                {{ p.syllabus_id || p.subject || '-' }}
                <template v-if="p.goal_score"> · 目标 {{ p.goal_score }} 分</template>
              </div>
            </td>
            <td>
              <!-- 点用户能跳进用户详情 —— 计划列表最常被问的下一个问题就是「这是谁」 -->
              <a v-if="p.user_id" class="user-link" :title="p.user_id"
                 @click="$router.push(`/admin/users?search=${encodeURIComponent(p.nickname || p.email || '')}`)">
                {{ p.nickname || p.email || p.user_id.slice(0, 8) + '…' }}
              </a>
              <span v-else class="date-cell">用户已删</span>
            </td>
            <td>{{ p.subject || '-' }}</td>
            <td class="date-cell">{{ p.period_days ? p.period_days + ' 天' : '-' }}</td>
            <td>
              <!-- 进度两个字段都可能为 0（很多计划建完还没开始跑），
                   所以显示成 "0/0" 会看着像坏了 —— 分母为 0 时直接显示 — -->
              <div v-if="p.total_days" class="progress">
                {{ p.completed_days || 0 }} / {{ p.total_days }} 天
              </div>
              <div v-else class="date-cell">—</div>
              <div v-if="p.total_questions" class="plan-sub">
                {{ p.completed_questions || 0 }} / {{ p.total_questions }} 题
              </div>
            </td>
            <td>
              <span class="status-tag" :class="p.status">{{ statusLabel(p.status) }}</span>
            </td>
            <td class="date-cell">{{ formatDate(p.created_at) }}</td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-if="!loading && !plans.length">
        {{ search || statusFilter ? '没有匹配的学习计划' : '还没有学习计划' }}
      </div>
    </div>

    <div class="pagination" v-if="total > pageSize">
      <el-pagination small layout="prev, pager, next, total"
                     :total="total" :page-size="pageSize"
                     :current-page="page" @current-change="load" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPlans } from '@/api/admin'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import AdminLoading from '@/components/admin/AdminLoading.vue'

// 与后端 routers/admin.py 的 _PLAN_STATUSES 对齐。
// ⚠️ 后端是**白名单**：传了名单外的值会被忽略（返回全部）而不是报错，
//    所以这里多写一个不存在的状态不会炸，只会筛不出东西。
const STATUSES = [
  { value: 'active', label: '进行中' },
  { value: 'completed', label: '已完成' },
  { value: 'paused', label: '已暂停' },
  { value: 'archived', label: '已归档' },
  { value: 'abandoned', label: '已放弃' },
]
const STATUS_LABEL = Object.fromEntries(STATUSES.map(s => [s.value, s.label]))

const loading = ref(false)
const plans = ref([])
const search = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

function statusLabel(s) { return STATUS_LABEL[s] || s || '-' }
function formatDate(d) { return d ? dayjs(d).format('YYYY-MM-DD HH:mm') : '-' }

let searchTimer = null
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => load(1), 400)
}

async function load(p) {
  if (typeof p === 'number') page.value = p
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (search.value.trim()) params.search = search.value.trim()
    if (statusFilter.value) params.status = statusFilter.value
    const d = await getPlans(params)
    plans.value = d.items || []
    total.value = d.total || 0
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '加载学习计划失败')
    plans.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(() => load(1))
</script>

<style scoped>
.admin-plans { max-width: 1100px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  gap: 12px;
  flex-wrap: wrap;
}
.page-title { font-size: 20px; font-weight: 600; color: var(--text-primary); margin: 0; }
.header-actions { display: flex; gap: 10px; align-items: center; }
.search-input { width: 240px; }
.filter-select { width: 140px; }

.table-wrap {
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  backdrop-filter: blur(12px);
  border: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent);
  border-radius: 14px;
  overflow: hidden;
}

.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-muted);
  text-transform: uppercase;
  border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 4%, transparent);
}
.data-table td {
  padding: 11px 16px;
  font-size: 13px;
  color: var(--text-secondary);
  border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 2%, transparent);
  vertical-align: top;
}

.plan-name { color: var(--text-primary); font-weight: 500; }
.plan-sub { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.progress { font-family: monospace; font-size: 12px; }
.date-cell { font-size: 12px; color: var(--text-muted); white-space: nowrap; }

.user-link { color: var(--brand); cursor: pointer; }
.user-link:hover { text-decoration: underline; }

.status-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  color: var(--text-secondary);
}
.status-tag.active { background: rgba(103, 194, 58, 0.12); color: #67c23a; }
.status-tag.completed { background: color-mix(in srgb, var(--brand) 14%, transparent); color: var(--brand); }
.status-tag.abandoned { background: rgba(245, 108, 108, 0.12); color: #f56c6c; }
.status-tag.paused { background: rgba(230, 162, 60, 0.12); color: #e6a23c; }

.empty { padding: 48px; text-align: center; color: var(--text-muted); font-size: 14px; }
.pagination { display: flex; justify-content: center; padding: 16px; }

:deep(.el-select .el-input__wrapper),
:deep(.el-input .el-input__wrapper) {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent) !important;
  border: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent) !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}
:deep(.el-select .el-input__inner),
:deep(.el-input .el-input__inner) { color: var(--text-primary) !important; }
</style>
