<template>
  <div class="admin-logs">
    <div class="page-header">
      <h2 class="page-title">操作日志</h2>
      <!-- 选项与后端 write_audit_log 实际写入的 action 值逐条对齐。
           原先「编辑题目」写的是 edit_question，而后端写的是 update_question ——
           这个筛选永远返回 0 条。 -->
      <el-select v-model="actionFilter" placeholder="操作类型" size="small" clearable
                 filterable @change="loadLogs" class="filter-select">
        <el-option-group label="用户">
          <el-option label="封禁用户" value="ban_user" />
          <el-option label="解封用户" value="unban_user" />
          <el-option label="设为管理" value="set_admin" />
          <el-option label="取消管理" value="remove_admin" />
        </el-option-group>
        <el-option-group label="题库">
          <el-option label="新增题目" value="create_question" />
          <el-option label="编辑题目" value="update_question" />
          <el-option label="删除题目" value="delete_question" />
          <el-option label="批量导入" value="import_questions" />
        </el-option-group>
        <el-option-group label="审核">
          <el-option label="举报·通过" value="resolve_report_resolved" />
          <el-option label="举报·驳回" value="resolve_report_dismissed" />
          <el-option label="处理反馈" value="resolve_feedback" />
          <el-option label="处理 Q&A" value="resolve_qa" />
        </el-option-group>
        <el-option-group label="公告 / 上传">
          <el-option label="发布公告" value="create_announcement" />
          <el-option label="更新公告" value="update_announcement" />
          <el-option label="删除公告" value="delete_announcement" />
          <el-option label="上传图片" value="upload_image" />
        </el-option-group>
        <el-option-group label="视频库">
          <el-option label="视频审核" value="video_review" />
          <el-option label="视频重试" value="video_retry" />
          <el-option label="视频删除" value="video_delete" />
          <el-option label="视频举报处理" value="video_report_handle" />
          <el-option label="批量暖库" value="video_warm" />
        </el-option-group>
      </el-select>
    </div>

    <div class="table-wrap">
      <AdminLoading :visible="loading" text="加载操作日志..." />
      <table class="data-table">
        <thead>
          <tr>
            <th>管理员</th>
            <th>操作</th>
            <th>详情</th>
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
            <td class="detail-cell">{{ detailText(log.detail) || '-' }}</td>
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

// 与后端 write_audit_log 的 action 取值逐条对齐。
// 之前这里写的是 edit_question / resolve_report 等**后端从不写入**的值，
// 导致这些日志显示成原始英文（或错误映射）。
const ACTION_LABEL = {
  ban_user: '封禁用户', unban_user: '解封用户',
  set_admin: '设为管理', remove_admin: '取消管理',
  create_question: '新增题目', update_question: '编辑题目', delete_question: '删除题目',
  import_questions: '批量导入',
  resolve_report_resolved: '举报·通过', resolve_report_dismissed: '举报·驳回',
  resolve_feedback: '处理反馈', resolve_qa: '处理 Q&A',
  create_announcement: '发布公告', update_announcement: '更新公告', delete_announcement: '删除公告',
  upload_image: '上传图片',
  video_review: '视频审核', video_retry: '视频重试', video_delete: '视频删除',
  video_report_handle: '视频举报处理', video_warm: '批量暖库',
}

function actionLabel(a) {
  // 兜底到原始值，而不是显示 undefined —— 后端将来加了动作也不至于变成空白
  return ACTION_LABEL[a] || a || '-'
}

// 详情字段（detail JSONB）——后端一直在存，前端此前完全不展示，
// 于是"改了什么"看不到。这里把关键键翻成中文后拼成一行。
const DETAIL_LABEL = {
  status: '状态', admin_note: '备注', is_active: '启用', role: '角色',
  is_admin: '管理员', action: '动作', publish_status: '发布状态',
  enqueued: '入队', skipped: '跳过', planned: '计划', video_id: '视频',
}

function detailText(d) {
  if (!d || typeof d !== 'object') return ''
  const parts = []
  for (const [k, v] of Object.entries(d)) {
    if (v === null || v === undefined || v === '') continue
    const val = typeof v === 'boolean' ? (v ? '是' : '否') : String(v)
    parts.push(`${DETAIL_LABEL[k] || k}: ${val}`)
  }
  return parts.join(' · ')
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
.page-title { font-size: 20px; font-weight: 600; color: var(--text-primary); margin: 0; }
.filter-select { width: 160px; }

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
}

.mono-cell { font-family: monospace; font-size: 12px; color: var(--text-muted); }
.date-cell { font-size: 12px; color: var(--text-muted); white-space: nowrap; }

.action-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  color: var(--text-secondary);
}
.detail-cell { font-size: 12px; color: var(--text-secondary); max-width: 260px; }

/* 危险动作 */
.action-tag.ban_user, .action-tag.delete_question, .action-tag.delete_announcement,
.action-tag.video_delete, .action-tag.resolve_report_resolved {
  background: rgba(245, 108, 108, 0.12); color: #f56c6c;
}
/* 放行/新增动作 */
.action-tag.unban_user, .action-tag.create_question, .action-tag.create_announcement,
.action-tag.resolve_report_dismissed, .action-tag.video_review {
  background: rgba(103, 194, 58, 0.1); color: #67c23a;
}
/* 权限变更 */
.action-tag.set_admin, .action-tag.remove_admin {
  background: rgba(230, 162, 60, 0.1); color: #e6a23c;
}

.empty { padding: 48px; text-align: center; color: var(--text-muted); font-size: 14px; }
.pagination { display: flex; justify-content: center; padding: 16px; }

:deep(.el-select .el-input__wrapper) {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent) !important;
  border: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent) !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}
:deep(.el-select .el-input__inner) { color: var(--text-primary) !important; }
</style>
