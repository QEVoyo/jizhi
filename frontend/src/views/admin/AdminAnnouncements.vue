<template>
  <div class="admin-announcements">
    <div class="page-header">
      <h2 class="page-title">公告管理</h2>
      <el-button size="default" @click="showCreate">
        <i class="fas fa-plus"></i> 新建公告
      </el-button>
    </div>

    <div class="table-wrap">
      <AdminLoading :visible="loading" text="加载公告中..." />

      <template v-if="!loading">
        <table class="data-table" v-if="announcements.length > 0">
          <thead>
            <tr>
              <th>标题</th>
              <th>内容</th>
              <th>图片</th>
              <th>状态</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in announcements" :key="a.id">
              <td class="title-cell">{{ a.title }}</td>
              <td class="content-cell">{{ truncate(a.content, 50) }}</td>
              <td>
                <img v-if="a.image_url" :src="a.image_url" class="thumb-img" @click="previewImage = a.image_url" />
                <span v-else class="no-img">-</span>
              </td>
              <td>
                <span class="status-tag" :class="{ active: a.is_active }">
                  {{ a.is_active ? '发布中' : '已下架' }}
                </span>
              </td>
              <td class="date-cell">{{ formatDate(a.created_at) }}</td>
              <td>
                <div class="action-btns">
                  <el-button size="small" text @click="toggleActive(a)">
                    {{ a.is_active ? '下架' : '发布' }}
                  </el-button>
                  <el-button size="small" text @click="editItem(a)">编辑</el-button>
                  <el-button size="small" text type="danger" @click="deleteItem(a)">删除</el-button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="empty" v-else>暂无公告，点击上方按钮发布第一条</div>
      </template>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑公告' : '新建公告'" width="560px" class="admin-dialog" @closed="resetForm">
      <el-form :model="form" label-position="top">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="公告标题..." />
        </el-form-item>
        <el-form-item label="封面图片">
          <ImageUpload v-model="form.image_url" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input v-model="form.content" type="textarea" :rows="4" placeholder="公告正文内容..." />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="立即发布" inactive-text="暂存草稿" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">
          <i class="fas fa-check" v-if="!saving"></i> {{ editingId ? '保存' : '发布' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 图片放大预览 -->
    <Teleport to="body">
      <div class="image-overlay" v-if="previewImage" @click="previewImage = null">
        <img :src="previewImage" @click.stop />
        <button class="close-btn" @click="previewImage = null"><i class="fas fa-times"></i></button>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getAnnouncements, createAnnouncement, updateAnnouncement, deleteAnnouncement } from '@/api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import AdminLoading from '@/components/admin/AdminLoading.vue'
import ImageUpload from '@/components/admin/ImageUpload.vue'

const loading = ref(false)
const announcements = ref([])
const previewImage = ref(null)

const dialogVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = reactive({ title: '', content: '', image_url: '', is_active: true })

async function loadAnnouncements() {
  loading.value = true
  try {
    const data = await getAnnouncements()
    announcements.value = Array.isArray(data) ? data : (data?.items || data || [])
  } catch (e) { ElMessage.error('加载公告失败'); announcements.value = [] }
  finally { loading.value = false }
}

function resetForm() {
  editingId.value = null
  form.title = ''
  form.content = ''
  form.image_url = ''
  form.is_active = true
}

function showCreate() { resetForm(); dialogVisible.value = true }

function editItem(a) {
  editingId.value = a.id
  form.title = a.title
  form.content = a.content || ''
  form.image_url = a.image_url || ''
  form.is_active = a.is_active
  dialogVisible.value = true
}

async function save() {
  if (!form.title.trim()) { ElMessage.warning('请输入公告标题'); return }
  saving.value = true
  try {
    const payload = {
      title: form.title.trim(),
      content: form.content.trim(),
      image_url: form.image_url,
      is_active: form.is_active
    }
    if (editingId.value) {
      await updateAnnouncement(editingId.value, payload)
      ElMessage.success('公告已更新')
    } else {
      const res = await createAnnouncement(payload)
      ElMessage.success(res?.message || '公告已发布')
    }
    dialogVisible.value = false
    loadAnnouncements()
  } catch (e) {
    const msg = e?.response?.data?.detail || e?.message || '保存失败'
    ElMessage.error(msg)
  }
  finally { saving.value = false }
}

async function toggleActive(a) {
  try {
    await updateAnnouncement(a.id, { is_active: !a.is_active })
    a.is_active = !a.is_active
    ElMessage.success(a.is_active ? '已发布' : '已下架')
  } catch (e) { ElMessage.error('操作失败') }
}

async function deleteItem(a) {
  try {
    await ElMessageBox.confirm('确定删除此公告？', '删除确认', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'
    })
    await deleteAnnouncement(a.id)
    ElMessage.success('已删除')
    loadAnnouncements()
  } catch (e) { /* cancelled */ }
}

function truncate(s, max) { return s && s.length > max ? s.slice(0, max) + '...' : s || '-' }
function formatDate(d) { return d ? dayjs(d).format('YYYY-MM-DD HH:mm') : '-' }

onMounted(loadAnnouncements)
</script>

<style scoped>
.admin-announcements { max-width: 960px; }

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}
.page-title { font-size: 20px; font-weight: 600; color: #e0e0e0; margin: 0; }

.table-wrap {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  overflow: hidden;
  min-height: 200px;
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
  padding: 12px 16px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.65);
  border-bottom: 1px solid rgba(255, 255, 255, 0.02);
}

.title-cell { color: #e0e0e0; font-weight: 500; }
.content-cell { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: rgba(255, 255, 255, 0.4); }
.date-cell { font-size: 12px; color: rgba(255, 255, 255, 0.3); white-space: nowrap; }
.action-btns { display: flex; gap: 4px; }

/* 缩略图 */
.thumb-img {
  width: 48px;
  height: 32px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: transform 0.2s;
}
.thumb-img:hover { transform: scale(2.5); z-index: 10; position: relative; }
.no-img { color: rgba(255, 255, 255, 0.15); }

.status-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  background: rgba(144, 147, 153, 0.12);
  color: #909399;
}
.status-tag.active { background: rgba(103, 194, 58, 0.12); color: #67c23a; }

.empty { padding: 60px 20px; text-align: center; color: rgba(255, 255, 255, 0.2); font-size: 14px; }

/* 图片放大 */
.image-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-out;
}
.image-overlay img {
  max-width: 90vw;
  max-height: 90vh;
  border-radius: 12px;
  cursor: default;
}
.close-btn {
  position: absolute;
  top: 20px;
  right: 24px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}
.close-btn:hover { background: rgba(255, 255, 255, 0.2); transform: scale(1.1); }

/* Dialog */
:deep(.admin-dialog) { background: #111827 !important; border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 16px !important; }
:deep(.admin-dialog .el-dialog__header) { border-bottom: 1px solid rgba(255, 255, 255, 0.06); padding: 18px 24px; }
:deep(.admin-dialog .el-dialog__title) { color: #e0e0e0 !important; }
:deep(.admin-dialog .el-dialog__body) { padding: 24px; }
:deep(.admin-dialog .el-dialog__close) { color: rgba(255, 255, 255, 0.4) !important; }
:deep(.el-form-item__label) { color: rgba(255, 255, 255, 0.5) !important; }
:deep(.el-input__wrapper), :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}
:deep(.el-input__inner), :deep(.el-textarea__inner) { color: #e0e0e0 !important; }
</style>
