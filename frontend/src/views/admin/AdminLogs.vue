<template>
  <div class="admin-logs">
    <div class="page-header">
      <h2 class="page-title">操作日志</h2>
      <el-select v-model="actionFilter" placeholder="操作类型" size="small" clearable @change="loadLogs" class="filter-select">
        <el-option label="封禁用户" value="ban_user" />
        <el-option label="解封用户" value="unban_user" />
        <el-option label="设为管理" value="set_admin" />
        <el-option label="取消管理" value="remove_admin" />
        <el-option label="删除题目" value="delete_question" />
        <el-option label="编辑题目" value="edit_question" />
        <el-option label="新增题目" value="create_question" />
      </el-select>
    </div>

    <div class="table-wrap">
      <AdminLoading :visible="loading" text="加载操作日志..." />
      <table class="data-table">
        <thead>
          <tr>
            <th>管理员</th>
            <th>操作</th>
            <th>目标类型</th>
            <th>目标 ID</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in logs" :key="log.id">
            <td>{{ log.admin_nickname || log.admin_id?.slice(0, 8) }}</td>
            <td>
              <span class="action-tag" :class="log.action">{{ actionLabel(log.action) }}</span>
            </td>
            <td>{{ log.target_type || '-' }}</td>
            <td class="mono-cell">{{ log.target_id ? log.target_id.slice(0, 12) + '...' : '-' }}</td>
            <td class="date-cell">{{ formatDate(log.created_at) }}</td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-if="!loading && logs.length === 0">暂无操作日志</div>

      <div class="pagination" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadLogs"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAuditLogs } from '@/api/admin'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import AdminLoading from '@/components/admin/AdminLoading.vue'

const loading = ref(false)
const logs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(30)
const actionFilter = ref('')

async function loadLogs() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (actionFilter.value) params.action = actionFilter.value
    const data = await getAuditLogs(params)
    logs.value = data.items || []
    total.value = data.total || 0
  } catch (e) { ElMessage.error('加载日志失败') }
  finally { loading.value = false }
}

function actionLabel(a) {
  const map = {
    ban_user: '封禁用户', unban_user: '解封用户',
    set_admin: '设为管理', remove_admin: '取消管理',
    create_question: '新增题目', edit_question: '编辑题目', delete_question: '删除题目',
    import_questions: '批量导入', resolve_report: '处理举报', resolve_feedback: '处理反馈',
    create_announcement: '发布公告', update_announcement: '更新公告', delete_announcement: '删除公告'
  }
  return map[a] || a
}

function formatDate(d) { return d ? dayjs(d).format('YYYY-MM-DD HH:mm:ss') : '-' }

onMounted(loadLogs)
</script>

<style scoped>
.admin-logs { max-width: 1000px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}
.page-title { font-size: 20px; font-weight: 600; color: #e0e0e0; margin: 0; }
.filter-select { width: 160px; }

.table-wrap {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  overflow: hidden;
}

.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 11px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.3);
  text-transform: uppercase;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
.data-table td {
  padding: 11px 16px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  border-bottom: 1px solid rgba(255, 255, 255, 0.02);
}

.mono-cell { font-family: monospace; font-size: 12px; color: rgba(255, 255, 255, 0.3); }
.date-cell { font-size: 12px; color: rgba(255, 255, 255, 0.3); white-space: nowrap; }

.action-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.5);
}
.action-tag.ban_user, .action-tag.delete_question { background: rgba(245, 108, 108, 0.12); color: #f56c6c; }
.action-tag.unban_user, .action-tag.create_question { background: rgba(103, 194, 58, 0.1); color: #67c23a; }
.action-tag.set_admin, .action-tag.remove_admin { background: rgba(230, 162, 60, 0.1); color: #e6a23c; }

.empty { padding: 48px; text-align: center; color: rgba(255, 255, 255, 0.2); font-size: 14px; }
.pagination { display: flex; justify-content: center; padding: 16px; }

:deep(.el-select .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}
:deep(.el-select .el-input__inner) { color: #e0e0e0 !important; }
</style>
