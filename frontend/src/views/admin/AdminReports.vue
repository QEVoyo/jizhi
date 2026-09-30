<template>
  <div class="admin-reports">
    <div class="page-header">
      <h2 class="page-title">{{ pageTitle }}</h2>
    </div>

    <!-- Tabs：点击即切路由，标签 / 地址 / 侧边栏高亮三者保持一致 -->
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
            <th>被举报内容</th>
            <th>被举报人</th>
            <th>原因</th>
            <th>状态</th>
            <th>时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in reports" :key="r.id">
            <td>{{ r.reporter_nickname || '-' }}</td>
            <td class="snapshot-cell">
              <span class="target-tag">{{ r.target_type === 'post' ? '帖子' : '评论' }}</span>
              <span class="snapshot-text">{{ r.target_snapshot || '（无快照）' }}</span>
            </td>
            <td>{{ r.target_author_nickname || '-' }}</td>
            <td class="reason-cell">{{ r.reason || '-' }}</td>
            <td>
              <span class="status-tag" :class="r.status">{{ statusLabel(r.status) }}</span>
            </td>
            <td class="date-cell">{{ formatDate(r.created_at) }}</td>
            <td>
              <div class="action-btns" v-if="r.status === 'pending'">
                <el-button size="small" text @click="resolveReportItem(r, { action: 'dismiss' })">驳回</el-button>
                <!-- 处置动作一步到位：判定 + 处罚 + 留痕，不用再跳去用户管理页手动搜人 -->
                <el-dropdown trigger="click" @command="cmd => onDispose(r, cmd)">
                  <el-button size="small" text type="danger">处置<el-icon><arrow-down /></el-icon></el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="warn">警告并通知</el-dropdown-item>
                      <el-dropdown-item command="delete_content">删除该内容</el-dropdown-item>
                      <el-dropdown-item command="mute:1">禁言 1 天</el-dropdown-item>
                      <el-dropdown-item command="mute:7">禁言 7 天</el-dropdown-item>
                      <el-dropdown-item command="mute:30">禁言 30 天</el-dropdown-item>
                      <el-dropdown-item command="mute:0">永久禁言</el-dropdown-item>
                      <el-dropdown-item command="ban" divided>封禁账号</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
              <span v-else class="done-text">{{ actionTakenLabel(r.action_taken) }}</span>
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
              <el-button v-if="f.status === 'pending'" size="small" text type="success" @click="resolveFeedbackItem(f)">标记已处理</el-button>
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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getReports, resolveReport, getFeedbacks, resolveFeedback, getQAList, resolveQA } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import AdminLoading from '@/components/admin/AdminLoading.vue'

// ⚠️ 标签页由**路由**决定，不能是本地状态。
//    原先写死 `const tab = ref('reports')`，而侧边栏「反馈 & Q&A」指向 /admin/feedback ——
//    地址变了、侧边栏高亮也跟着变了，页面却仍停在「举报」标签，看起来就是点了没反应。
//    更麻烦的是 /admin/reports 与 /admin/feedback 用的是**同一个组件**，
//    Vue Router 会复用实例、连重新挂载都不会发生，所以这个错位是永久性的。
//    现在三者各有各的路由，标签、地址、侧边栏高亮三者永远一致。
const route = useRoute()
const router = useRouter()
const TAB_PATH = { reports: '/admin/reports', feedback: '/admin/feedback', qa: '/admin/qa' }
const PATH_TAB = { '/admin/reports': 'reports', '/admin/feedback': 'feedback', '/admin/qa': 'qa' }

const tab = computed({
  get: () => PATH_TAB[route.path] || 'reports',
  set: (v) => { const p = TAB_PATH[v]; if (p && p !== route.path) router.push(p) },
})

const PAGE_TITLE = {
  reports: '举报审核',
  feedback: '用户反馈',
  qa: 'Q&A 帮助中心',
}
const pageTitle = computed(() => PAGE_TITLE[tab.value] || '举报 & 反馈审核')

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

// 统一的处置出口。opts 形如 { action, status?, mute_days?, mute_scope?, admin_note? }
async function doResolve(r, opts, okText) {
  try {
    const res = await resolveReport(r.id, opts)
    r.status = res?.status || opts.status || 'resolved'
    r.action_taken = res?.action || opts.action || ''
    ElMessage.success(okText || res?.message || '已处理')
  } catch (e) {
    // 后端现在会把真实原因放在 detail 里（例如「处置记录未写入」、
    // 「查不到被举报人」），透出来比笼统的"操作失败"有用得多
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

// 「驳回」和 Q&A/反馈两个 Tab 走同一个形状
function resolveReportItem(r, opts) {
  if (typeof opts === 'string') opts = { status: opts }      // 兼容旧调用
  const action = opts.action || 'mark'
  return doResolve(r, { ...opts, action },
    action === 'dismiss' ? '已驳回' : '已处理')
}

// 处置下拉：命令形如 warn / delete_content / mute:7 / mute:0 / ban
async function onDispose(r, cmd) {
  const [kind, arg] = String(cmd).split(':')
  const opts = { action: kind }
  let okText = ''
  let confirmText = ''

  if (kind === 'warn') {
    opts.status = 'resolved'; okText = '已警告并通知对方'
    confirmText = `确定向「${r.target_author_nickname || '该用户'}」发出警告？会同时发送站内通知。`
  } else if (kind === 'delete_content') {
    opts.status = 'resolved'; okText = '已删除被举报内容'
    confirmText = '确定删除这条被举报内容？该内容将不再对用户可见（软删除，可追溯）。'
  } else if (kind === 'mute') {
    opts.mute_days = Number(arg || 0)
    opts.mute_scope = 'all'
    opts.status = 'resolved'
    okText = opts.mute_days > 0 ? `已禁言 ${opts.mute_days} 天` : '已永久禁言'
    confirmText = `确定对「${r.target_author_nickname || '该用户'}」执行${
      opts.mute_days > 0 ? `禁言 ${opts.mute_days} 天` : '永久禁言'}？`
  } else if (kind === 'ban') {
    opts.status = 'resolved'; okText = '已封禁'
    confirmText = `确定封禁「${r.target_author_nickname || '该用户'}」？` +
                  '对方将无法登录、发帖、评论。'
  }

  // 处罚类动作一律二次确认 —— 这类操作误点代价高，且此前暖库那种"点了就跑"是记过档的问题
  try {
    await ElMessageBox.confirm(confirmText, '确认处置', {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning',
    })
  } catch { return }   // 用户取消

  return doResolve(r, opts, okText)
}

const ACTION_TAKEN_LABEL = {
  dismiss: '已驳回', mark: '已处理', warn: '已警告',
  delete_content: '已删内容', mute: '已禁言', ban: '已封禁',
}
function actionTakenLabel(a) { return ACTION_TAKEN_LABEL[a] || '已处理' }

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
.page-title { font-size: 20px; font-weight: 600; color: var(--text-primary); margin: 0; }

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
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  border: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent);
  border-radius: 10px;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.25s;
}
.tab-btn:hover { background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); color: var(--text-primary); }
.tab-btn.active {
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  border-color: color-mix(in srgb, var(--brand) 20%, transparent);
  color: var(--brand);
}

/* ===== 表格 ===== */
.table-wrap {
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  backdrop-filter: blur(12px);
  border: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent);
  border-radius: 14px;
  overflow: hidden;
}

.filter-row {
  padding: 12px 16px;
  border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 4%, transparent);
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
  color: var(--text-muted);
  text-transform: uppercase;
  border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 4%, transparent);
}

.data-table td {
  padding: 10px 14px;
  font-size: 13px;
  color: var(--text-secondary);
  border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 2%, transparent);
}

.reason-cell, .content-cell { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* 被举报内容快照：管理员审核时要先看清"被举报的是什么"，
   所以这里给足宽度并允许换行（与只会截断的 reason-cell 不同） */
.snapshot-cell { max-width: 320px; }
.snapshot-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}
.date-cell { font-size: 12px; color: var(--text-muted); white-space: nowrap; }

.target-tag, .type-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent);
  color: var(--text-secondary);
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
.done-text { color: var(--text-muted); font-size: 12px; }
.img-link { color: var(--brand); font-size: 12px; text-decoration: none; }
.img-link:hover { text-decoration: underline; }

.empty {
  padding: 48px;
  text-align: center;
  color: var(--text-muted);
  font-size: 14px;
}

/* ===== Element 覆盖 ===== */
:deep(.el-select .el-input__wrapper) {
  background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent) !important;
  border: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent) !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}
:deep(.el-select .el-input__inner) { color: var(--text-primary) !important; }
</style>
