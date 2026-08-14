<template>
  <div class="admin-users">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <div class="header-actions">
        <el-input
          v-model="search"
          placeholder="搜索昵称/邮箱..."
          size="default"
          prefix-icon="Search"
          clearable
          @input="onSearch"
          class="search-input"
        />
        <el-select v-model="statusFilter" placeholder="状态" size="default" @change="loadUsers" class="status-select">
          <el-option label="全部用户" value="" />
          <el-option label="正常" value="active" />
          <el-option label="已封禁" value="banned" />
        </el-select>
      </div>
    </div>

    <div class="table-wrap">
      <AdminLoading :visible="loading" text="加载用户列表..." />
      <table class="data-table">
        <thead>
          <tr>
            <th>用户</th>
            <th>邮箱</th>
            <th>学段</th>
            <th>角色</th>
            <th>权限</th>
            <th>状态</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" @click="showDetail(u)" class="clickable-row">
            <td>
              <div class="user-cell">
                <el-avatar :size="32" :src="u.avatar_url">{{ u.nickname?.[0] || 'U' }}</el-avatar>
                <div>
                  <div class="user-name">{{ u.nickname || '未设置' }}</div>
                  <div class="user-account">{{ u.user_account }}</div>
                </div>
              </div>
            </td>
            <td class="email-cell">{{ u.email }}</td>
            <td>{{ u.learning_stage || '-' }}</td>
            <td>
              <span class="role-badge" :class="u.role || 'user'">{{ roleLabel(u.role) }}</span>
            </td>
            <td>
              <span v-if="u.role === 'super_admin'" class="perm-tag super">超级管理</span>
              <span v-else-if="u.role === 'admin'" class="perm-tag admin">管理员</span>
              <span v-else class="perm-tag user">普通用户</span>
            </td>
            <td>
              <span class="status-tag" :class="{ banned: !u.is_active }">
                {{ u.is_active !== false ? '正常' : '已封禁' }}
              </span>
            </td>
            <td class="date-cell">{{ formatDate(u.created_at) }}</td>
            <td @click.stop>
              <div class="action-btns">
                <el-button size="small" text @click="showDetail(u)">详情</el-button>
                <!-- 仅超级管理员可设/撤管理员 -->
                <template v-if="isSuperAdmin && u.role !== 'super_admin'">
                  <el-button v-if="u.role !== 'admin'" size="small" text type="warning" @click="toggleAdmin(u, true)">设为管理</el-button>
                  <el-button v-else size="small" text @click="toggleAdmin(u, false)">撤管理</el-button>
                </template>
                <el-button
                  v-if="u.is_active !== false"
                  size="small"
                  text
                  type="danger"
                  @click="toggleBan(u, false)"
                >封禁</el-button>
                <el-button
                  v-else
                  size="small"
                  text
                  type="success"
                  @click="toggleBan(u, true)"
                >解封</el-button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div class="empty" v-if="!loading && users.length === 0">暂无用户数据</div>

      <div class="pagination" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadUsers"
        />
      </div>
    </div>

    <!-- 用户详情弹窗 -->
    <el-dialog v-model="detailVisible" :title="detailUser?.nickname + ' 的详细信息'" width="560px" class="admin-dialog">
      <div class="detail-grid" v-if="detailUser">
        <div class="detail-item"><label>用户 ID</label><span>{{ detailUser.id }}</span></div>
        <div class="detail-item"><label>昵称</label><span>{{ detailUser.nickname }}</span></div>
        <div class="detail-item"><label>账号</label><span>{{ detailUser.user_account }}</span></div>
        <div class="detail-item"><label>邮箱</label><span>{{ detailUser.email }}</span></div>
        <div class="detail-item"><label>学段</label><span>{{ detailUser.learning_stage || '-' }}</span></div>
        <div class="detail-item"><label>年级</label><span>{{ detailUser.grade || '-' }}</span></div>
        <div class="detail-item"><label>专业</label><span>{{ detailUser.major || '-' }}</span></div>
        <div class="detail-item"><label>角色</label>
          <span>
            <span class="role-badge" :class="detailUser.role || 'user'">{{ roleLabel(detailUser.role) }}</span>
            <template v-if="isSuperAdmin && detailUser.role !== 'super_admin'">
              <el-switch
                :model-value="detailUser.role === 'admin'"
                @change="(v) => toggleAdmin(detailUser, v)"
                active-text="管理员"
                inactive-text="普通用户"
                style="margin-left: 12px"
              />
            </template>
          </span>
        </div>
        <div class="detail-item"><label>状态</label>
          <span>
            <el-switch
              :model-value="detailUser.is_active !== false"
              @change="(v) => toggleBan(detailUser, v)"
              active-text="正常"
              inactive-text="封禁"
            />
          </span>
        </div>
        <div class="detail-item"><label>学习计划</label><span>{{ detailStats.plan_count || 0 }} 个</span></div>
        <div class="detail-item"><label>做题记录</label><span>{{ detailStats.question_count || 0 }} 次</span></div>
        <div class="detail-item"><label>注册时间</label><span>{{ formatDate(detailUser.created_at) }}</span></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getUsers, getUserDetail, updateUserStatus, updateUserAdmin } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import AdminLoading from '@/components/admin/AdminLoading.vue'

const authStore = useAuthStore()
const isSuperAdmin = computed(() => authStore.user?.role === 'super_admin')

const loading = ref(false)
const users = ref([])
const search = ref('')
const statusFilter = ref('')
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)

const detailVisible = ref(false)
const detailUser = ref(null)
const detailStats = ref({})

let searchTimer = null

function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; loadUsers() }, 400)
}

async function loadUsers() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (search.value) params.search = search.value
    if (statusFilter.value) params.status = statusFilter.value
    const data = await getUsers(params)
    users.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

async function showDetail(u) {
  detailUser.value = u
  detailVisible.value = true
  try {
    const data = await getUserDetail(u.id)
    detailUser.value = { ...u, ...data }
    detailStats.value = data
  } catch (e) { /* ignore */ }
}

async function toggleBan(u, active) {
  const action = active ? '解封' : '封禁'
  try {
    await ElMessageBox.confirm(`确定要${action}用户 "${u.nickname}" 吗？`, `${action}确认`, {
      confirmButtonText: action,
      cancelButtonText: '取消',
      type: 'warning'
    })
    await updateUserStatus(u.id, active)
    u.is_active = active
    ElMessage.success(`已${action}`)
  } catch (e) { /* cancelled */ }
}

function roleLabel(role) {
  const map = { super_admin: '超级管理员', admin: '管理员', user: '用户' }
  return map[role] || '用户'
}

async function toggleAdmin(u, isAdmin) {
  const action = isAdmin ? '设为管理员' : '取消管理员'
  try {
    await ElMessageBox.confirm(`确定要${action} "${u.nickname}" 吗？`, `${action}确认`, {
      confirmButtonText: action,
      cancelButtonText: '取消',
      type: 'warning'
    })
    await updateUserAdmin(u.id, isAdmin)
    u.role = isAdmin ? 'admin' : 'user'
    u.is_admin = isAdmin
    ElMessage.success(`已${action}`)
  } catch (e) { /* cancelled */ }
}

function formatDate(d) {
  return d ? dayjs(d).format('YYYY-MM-DD HH:mm') : '-'
}

onMounted(loadUsers)
</script>

<style scoped>
.admin-users { max-width: 1100px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #e0e0e0;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-input { width: 220px; }
.status-select { width: 120px; }

/* ===== 表格 ===== */
.table-wrap {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.35);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.data-table td {
  padding: 10px 16px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.clickable-row { cursor: pointer; transition: background 0.2s; }
.clickable-row:hover { background: rgba(255, 255, 255, 0.03); }

.user-cell { display: flex; align-items: center; gap: 10px; }
.user-name { color: #e0e0e0; font-weight: 500; }
.user-account { font-size: 11px; color: rgba(255, 255, 255, 0.3); }
.email-cell { color: rgba(255, 255, 255, 0.5); font-size: 12px; }
.date-cell { font-size: 12px; color: rgba(255, 255, 255, 0.35); white-space: nowrap; }

/* 角色徽章 */
.role-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}
.role-badge.super_admin { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.role-badge.admin { background: rgba(64, 158, 255, 0.12); color: #409eff; }
.role-badge.user { background: rgba(255, 255, 255, 0.05); color: rgba(255, 255, 255, 0.4); }

/* 权限标签 */
.perm-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}
.perm-tag.super { background: rgba(245, 158, 11, 0.12); color: #f59e0b; }
.perm-tag.admin { background: rgba(64, 158, 255, 0.1); color: #409eff; }
.perm-tag.user { background: rgba(255, 255, 255, 0.04); color: rgba(255, 255, 255, 0.35); }

.status-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}
.status-tag { background: rgba(103, 194, 58, 0.1); color: #67c23a; }
.status-tag.banned { background: rgba(245, 108, 108, 0.1); color: #f56c6c; }

.action-btns { display: flex; gap: 4px; }

.empty {
  padding: 48px;
  text-align: center;
  color: rgba(255, 255, 255, 0.25);
  font-size: 14px;
}

.pagination {
  display: flex;
  justify-content: center;
  padding: 16px;
}

/* ===== 详情弹窗 ===== */
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.detail-item label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  text-transform: uppercase;
}
.detail-item span {
  font-size: 14px;
  color: #e0e0e0;
}

/* ===== Element Plus 覆盖 ===== */
:deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}
:deep(.el-input__inner) { color: #e0e0e0 !important; }
:deep(.el-input__prefix) { color: rgba(255, 255, 255, 0.3) !important; }
:deep(.el-select .el-input__wrapper) { background: rgba(255, 255, 255, 0.05) !important; }
:deep(.el-select .el-input__inner) { color: #e0e0e0 !important; }

:deep(.admin-dialog) {
  background: #111827 !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 16px !important;
}
:deep(.admin-dialog .el-dialog__header) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding: 18px 24px;
}
:deep(.admin-dialog .el-dialog__title) { color: #e0e0e0 !important; font-weight: 600; }
:deep(.admin-dialog .el-dialog__body) { padding: 24px; }
:deep(.admin-dialog .el-dialog__close) { color: rgba(255, 255, 255, 0.4) !important; }

:deep(.el-pagination button), :deep(.el-pager li) {
  color: rgba(255, 255, 255, 0.5) !important;
  background: transparent !important;
}
:deep(.el-pager li.is-active) {
  background: rgba(64, 158, 255, 0.15) !important;
  color: #409eff !important;
}
</style>
