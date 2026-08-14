<template>
  <div class="admin-reports">
    <div class="page-header">
      <h2 class="page-title">举报 &amp; 反馈审核</h2>
    </div>

    <!-- Tabs -->
    <div class="tab-bar">
      <button class="tab-btn" :class="{ active: tab === 'reports' }" @click="tab = 'reports'">
        <i class="fas fa-flag"></i> 举报 ({{ reportTotal }})
      </button>
      <button class="tab-btn" :class="{ active: tab === 'feedback' }" @click="tab = 'feedback'">
        <i class="fas fa-message"></i> 反馈 ({{ feedbackTotal }})
      </button>
      <button class="tab-btn" :class="{ active: tab === 'qa' }" @click="tab = 'qa'">
        <i class="fas fa-circle-question"></i> Q&A ({{ qaTotal }})
      </button>
    </div>

    <!-- 举报列表 -->
    <div class="table-wrap" v-if="tab === 'reports'">
      <AdminLoading :visible="loading" text="加载举报列表..." />
      <div class="filter-row">
        <el-select v-model="reportStatus" placeholder="状态筛选" size="small" @change="loadReports">
          <el-option label="全部" value="" />
          <el-option label="待处理" value="pending" />
          <el-option label="已处理" value="resolved" />
          <el-option label="已驳回" value="dismissed" />
        </el-select>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>举报人</th>
            <th>目标类型</th>
            <th>原因</th>
            <th>状态</th>
            <th>时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in reports" :key="r.id">
            <td>{{ r.reporter_nickname || '-' }}</td>
            <td>
              <span class="target-tag">{{ r.target_type === 'post' ? '帖子' : '评论' }}</span>
            </td>
            <td class="reason-cell">{{ r.reason || '-' }}</td>
            <td>
              <span class="status-tag" :class="r.status">{{ statusLabel(r.status) }}</span>
            </td>
            <td class="date-cell">{{ formatDate(r.created_at) }}</td>
            <td>
              <div class="action-btns" v-if="r.status === 'pending'">
                <el-button size="small" text type="success" @click="resolveReport(r, 'resolved')">通过</el-button>
                <el-button size="small" text type="danger" @click="resolveReport(r, 'dismissed')">驳回</el-button>
              </div>
              <span v-else class="done-text">已处理</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-if="!loading && reports.length === 0">暂无举报</div>
    </div>

    <!-- 反馈列表 -->
    <div class="table-wrap" v-if="tab === 'feedback'">
      <AdminLoading :visible="loading" text="加载反馈列表..." />
      <div class="filter-row">
        <el-select v-model="feedbackStatus" placeholder="状态筛选" size="small" @change="loadFeedback">
          <el-option label="全部" value="" />
          <el-option label="待处理" value="pending" />
          <el-option label="已处理" value="resolved" />
        </el-select>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>用户</th>
            <th>类型</th>
            <th>内容</th>
            <th>状态</th>
            <th>时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="f in feedbacks" :key="f.id">
            <td>{{ f.nickname || f.email || '-' }}</td>
            <td>
              <span class="type-tag">{{ feedbackTypeLabel(f.feedback_type) }}</span>
            </td>
            <td class="content-cell">{{ f.content }}</td>
            <td>
              <span class="status-tag" :class="f.status">{{ f.status === 'resolved' ? '已处理' : '待处理' }}</span>
            </td>
            <td class="date-cell">{{ formatDate(f.created_at) }}</td>
            <td>
              <el-button v-if="f.status === 'pending'" size="small" text type="success" @click="resolveFeedback(f)">标记已处理</el-button>
              <span v-else class="done-text">-</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-if="!loading && feedbacks.length === 0">暂无反馈</div>
    </div>

    <!-- Q&A 列表 -->
    <div class="table-wrap" v-if="tab === 'qa'">
      <AdminLoading :visible="loading" text="加载Q&A列表..." />
      <div class="filter-row">
        <el-select v-model="qaStatus" placeholder="状态筛选" size="small" @change="loadQA">
          <el-option label="全部" value="" />
          <el-option label="待处理" value="pending" />
          <el-option label="已处理" value="resolved" />
        </el-select>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>用户</th>
            <th>问题</th>
            <th>附件</th>
            <th>状态</th>
            <th>时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="q in qaList" :key="q.id">
            <td>{{ q.nickname || q.email || '-' }}</td>
            <td class="content-cell">{{ q.question }}</td>
            <td>
              <a v-if="q.image_url" :href="q.image_url" target="_blank" class="img-link">查看图片</a>
              <span v-else>-</span>
            </td>
            <td>
              <span class="status-tag" :class="q.status">{{ q.status === 'resolved' ? '已处理' : '待处理' }}</span>
            </td>
            <td class="date-cell">{{ formatDate(q.created_at) }}</td>
            <td>
              <el-button v-if="q.status === 'pending'" size="small" text type="success" @click="resolveQAItem(q)">标记已处理</el-button>
              <span v-else class="done-text">-</span>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="empty" v-if="!loading && qaList.length === 0">暂无 Q&A</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getReports, resolveReport, getFeedbacks, resolveFeedback, getQAList, resolveQA } from '@/api/admin'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import AdminLoading from '@/components/admin/AdminLoading.vue'

const tab = ref('reports')
const loading = ref(false)

// Reports
const reports = ref([])
const reportTotal = ref(0)
const reportStatus = ref('')

// Feedback
const feedbacks = ref([])
const feedbackTotal = ref(0)
const feedbackStatus = ref('')

// QA
const qaList = ref([])
const qaTotal = ref(0)
const qaStatus = ref('')

async function loadReports() {
  loading.value = true
  try {
    const params = {}
    if (reportStatus.value) params.status = reportStatus.value
    const data = await getReports(params)
    reports.value = data.items || []
    reportTotal.value = data.total || 0
  } catch (e) { ElMessage.error('加载举报失败') }
  finally { loading.value = false }
}

async function loadFeedback() {
  loading.value = true
  try {
    const params = {}
    if (feedbackStatus.value) params.status = feedbackStatus.value
    const data = await getFeedbacks(params)
    feedbacks.value = data.items || []
    feedbackTotal.value = data.total || 0
  } catch (e) { ElMessage.error('加载反馈失败') }
  finally { loading.value = false }
}

async function loadQA() {
  loading.value = true
  try {
    const params = {}
    if (qaStatus.value) params.status = qaStatus.value
    const data = await getQAList(params)
    qaList.value = data.items || []
    qaTotal.value = data.total || 0
  } catch (e) { ElMessage.error('加载 Q&A 失败') }
  finally { loading.value = false }
}

async function resolveReportItem(r, status) {
  try {
    await resolveReport(r.id, { status })
    r.status = status
    ElMessage.success(status === 'resolved' ? '已通过' : '已驳回')
  } catch (e) { ElMessage.error('操作失败') }
}

async function resolveFeedbackItem(f) {
  try {
    await resolveFeedback(f.id, { status: 'resolved' })
    f.status = 'resolved'
    ElMessage.success('已标记为处理')
  } catch (e) { ElMessage.error('操作失败') }
}

async function resolveQAItem(q) {
  try {
    await resolveQA(q.id, { status: 'resolved' })
    q.status = 'resolved'
    ElMessage.success('已标记为处理')
  } catch (e) { ElMessage.error('操作失败') }
}

function statusLabel(s) {
  const map = { pending: '待处理', resolved: '已处理', dismissed: '已驳回' }
  return map[s] || s
}

function feedbackTypeLabel(t) {
  const map = { bug: 'Bug', suggestion: '建议', other: '其他' }
  return map[t] || t || '其他'
}

function formatDate(d) { return d ? dayjs(d).format('MM-DD HH:mm') : '-' }

onMounted(() => { loadReports(); loadFeedback(); loadQA() })
</script>

<style scoped>
.admin-reports { max-width: 1100px; }

.page-header { margin-bottom: 18px; }
.page-title { font-size: 20px; font-weight: 600; color: #e0e0e0; margin: 0; }

/* ===== Tab ===== */
.tab-bar {
  display: flex;
  gap: 6px;
  margin-bottom: 18px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.45);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s;
}
.tab-btn:hover { background: rgba(255, 255, 255, 0.06); color: rgba(255, 255, 255, 0.7); }
.tab-btn.active {
  background: rgba(64, 158, 255, 0.12);
  border-color: rgba(64, 158, 255, 0.2);
  color: #409eff;
}

/* ===== 表格 ===== */
.table-wrap {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  overflow: hidden;
}

.filter-row {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 10px 14px;
  font-size: 11px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.3);
  text-transform: uppercase;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.data-table td {
  padding: 10px 14px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.65);
  border-bottom: 1px solid rgba(255, 255, 255, 0.02);
}

.reason-cell, .content-cell { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.date-cell { font-size: 12px; color: rgba(255, 255, 255, 0.3); white-space: nowrap; }

.target-tag, .type-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.5);
}

.status-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}
.status-tag.pending { background: rgba(230, 162, 60, 0.12); color: #e6a23c; }
.status-tag.resolved { background: rgba(103, 194, 58, 0.1); color: #67c23a; }
.status-tag.dismissed { background: rgba(144, 147, 153, 0.12); color: #909399; }

.action-btns { display: flex; gap: 4px; }
.done-text { color: rgba(255, 255, 255, 0.2); font-size: 12px; }
.img-link { color: #409eff; font-size: 12px; text-decoration: none; }
.img-link:hover { text-decoration: underline; }

.empty {
  padding: 48px;
  text-align: center;
  color: rgba(255, 255, 255, 0.2);
  font-size: 14px;
}

/* ===== Element 覆盖 ===== */
:deep(.el-select .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.06) !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}
:deep(.el-select .el-input__inner) { color: #e0e0e0 !important; }
</style>
