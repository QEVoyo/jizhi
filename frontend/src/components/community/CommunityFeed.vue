<template>
  <div class="community-feed">
    <!-- ===== 顶部标题 ===== -->
    <div class="feed-header">
      <h2>🏠 动态广场</h2>
      <span class="feed-subtitle">分享学习心得，发现志同道合的伙伴</span>
    </div>

    <el-divider />

    <!-- ===== 发布动态（多行表单结构） ===== -->
    <div class="publish-section">
      <div class="publish-wrapper">
        <el-avatar :size="40" :src="authStore.user?.avatar_url || ''" class="publish-avatar">
          {{ authStore.user?.nickname?.[0] || 'U' }}
        </el-avatar>

        <div class="publish-form">
          <!-- 1. 标题 -->
          <el-input
            v-model="publishTitle"
            placeholder="标题（选填）..."
            class="publish-title"
          />

          <!-- 2. 正文内容 -->
          <el-input
            v-model="publishContent"
            type="textarea"
            :rows="3"
            placeholder="分享你的学习心得或问题..."
            maxlength="500"
            show-word-limit
            class="publish-textarea"
          />

          <!-- 3. 底部工具栏：标签 + 图片 + 发布 -->
          <div class="publish-toolbar">
            <!-- 左侧：标签和图片 -->
            <div class="publish-left">
              <el-input
                v-model="publishTags"
                placeholder="标签（逗号分隔）"
                size="small"
                style="width: 160px;"
                clearable
              />
              <el-upload
                ref="uploadRef"
                action="#"
                :auto-upload="false"
                :limit="1"
                accept="image/*"
                :on-change="handleImageSelect"
                :on-remove="handleImageRemove"
                :show-file-list="false"
              >
                <el-button size="small" :type="uploadedImage ? 'success' : 'default'">
                  <i class="fas fa-image"></i> 图片
                </el-button>
              </el-upload>
            </div>

            <!-- 右侧：发布按钮 -->
            <el-button type="primary" :loading="publishing" @click="handlePublish" size="small">
              <i class="fas fa-paper-plane"></i> 发布
            </el-button>
          </div>

          <!-- 4. 图片预览 -->
          <div v-if="uploadedImage" class="upload-preview-box">
            <img :src="uploadedImage" alt="预览" />
            <i class="fas fa-times remove-img-icon" @click="removeImage"></i>
          </div>
        </div>
      </div>
    </div>

    <el-divider />

    <!-- ===== 搜索 + 筛选 ===== -->
    <div class="toolbar">
      <div class="search-wrapper">
        <i class="fas fa-search search-icon"></i>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索动态..."
          size="small"
          clearable
          @input="handleSearch"
        />
      </div>
      <div class="filter-tabs">
        <button
          v-for="tab in filterTabs"
          :key="tab.key"
          class="filter-tab"
          :class="{ active: activeFilter === tab.key }"
          @click="switchFilter(tab.key)"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>

    <!-- ===== 动态列表（此处用 PostCard 循环渲染，所有格式由 PostCard 控制） ===== -->
    <div class="post-list">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i> 加载中...
      </div>

      <!-- 空状态 -->
      <div v-else-if="!posts.length" class="empty-state">
        <i class="fas fa-comments" style="font-size: 48px; opacity: 0.3;"></i>
        <p>暂无动态</p >
        <span>成为第一个发布动态的人吧！</span>
      </div>

      <!-- 👇 这里使用 PostCard.vue 组件渲染每一条动态，最终显示效果取决于 PostCard.vue -->
      <PostCard
        v-for="post in posts"
        :key="post.id"
        :post="post"
        @like="handleLike"
        @collect="handleCollect"
        @comment="toggleComment"
        @user-click="goUserProfile"
        @report="handleReport"
        @delete="handleDelete"
      />

      <!-- 加载更多 -->
      <div v-if="posts.length && hasMore" class="load-more">
        <el-button text @click="loadMore" :loading="loadingMore">
          加载更多
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import PostCard from './PostCard.vue'
import {
  getPosts,
  createPost,
  likePost,
  unlikePost,
  collectPost,
  uncollectPost,
  reportContent,
  deletePost
} from '@/api/community'

const router = useRouter()
const authStore = useAuthStore()

const posts = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const hasMore = ref(true)

// 发布相关
const publishTitle = ref('')
const publishContent = ref('')
const publishTags = ref('')
const uploadedImage = ref(null)
const uploadRef = ref(null)
const publishing = ref(false)

const searchKeyword = ref('')
const activeFilter = ref('all')
const filterTabs = [
  { key: 'all', label: '全部' },
  { key: 'friends', label: '好友' }
]

// ===== 图片处理 =====
const handleImageSelect = (uploadFile) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImage.value = e.target.result
  }
  reader.readAsDataURL(uploadFile.raw)
}

const removeImage = () => {
  uploadedImage.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

const handleImageRemove = () => {
  removeImage()
}

// ===== 核心发布 =====
async function handlePublish() {
  if (!publishContent.value.trim() && !uploadedImage.value) {
    ElMessage.warning('请输入内容或添加图片')
    return
  }

  publishing.value = true
  try {
    // 将标签字符串转为数组
    const tags = publishTags.value.split(',').map(t => t.trim()).filter(Boolean)

    // 构造要传给后端的数据对象
    const postData = {
  user_id: authStore.user.id,
  title: publishTitle.value.trim(),
  content: publishContent.value.trim(),
  tags: tags.length > 0 ? JSON.stringify(tags) : null,
  images: uploadedImage.value ? JSON.stringify([uploadedImage.value]) : null  // ✅ 改成字符串
}

    await createPost(postData)

    ElMessage.success('发布成功')
    publishTitle.value = ''
    publishContent.value = ''
    publishTags.value = ''
    uploadedImage.value = null
    loadPosts(true)
  } catch (error) {
    console.error('发布失败:', error)
    ElMessage.error(error.response?.data?.detail || '发布失败')
  } finally {
    publishing.value = false
  }
}

// ===== 基础功能 =====
async function loadPosts(reset = true) {
  if (reset) {
    page.value = 1
    posts.value = []
    hasMore.value = true
  }
  if (!hasMore.value) return

  loading.value = reset
  loadingMore.value = !reset

  try {
    const res = await getPosts({
      user_id: authStore.user.id,
      page: page.value,
      page_size: 20,
      search: searchKeyword.value,
      filter_type: activeFilter.value
    })
    if (reset) {
      posts.value = res.posts || []
    } else {
      posts.value = [...posts.value, ...(res.posts || [])]
    }
    hasMore.value = (res.posts || []).length === 20
    page.value++
  } catch (error) {
    console.error('加载动态失败:', error)
    ElMessage.error('加载动态失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() {
  loadPosts(false)
}

function switchFilter(key) {
  activeFilter.value = key
  loadPosts(true)
}

function handleSearch() {
  loadPosts(true)
}

async function handleLike(post) {
  try {
    if (post.is_liked) {
      await unlikePost(post.id, authStore.user.id)
      post.is_liked = false
      post.like_count = Math.max(0, (post.like_count || 0) - 1)
    } else {
      await likePost(post.id, authStore.user.id)
      post.is_liked = true
      post.like_count = (post.like_count || 0) + 1
    }
  } catch (error) {
    console.error('操作失败:', error)
    ElMessage.error('操作失败')
  }
}

async function handleCollect(post) {
  try {
    if (post.is_collected) {
      await uncollectPost(post.id, authStore.user.id)
      post.is_collected = false
      post.collect_count--
    } else {
      await collectPost(post.id, authStore.user.id)
      post.is_collected = true
      post.collect_count++
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

function toggleComment(postId) {
  // 由 PostCard 组件处理
}

function goUserProfile(userId) {
  router.push(`/community/user/${userId}`)
}

function handleReport(post) {
  ElMessageBox.prompt('请输入举报理由', '举报动态', {
    confirmButtonText: '提交',
    cancelButtonText: '取消',
    inputType: 'textarea',
    inputPlaceholder: '请描述举报原因...'
  }).then(async ({ value }) => {
    if (value) {
      try {
        await reportContent({
          user_id: authStore.user.id,
          target_type: 'post',
          target_id: post.id,
          reason: value
        })
        ElMessage.success('举报已提交，我们会尽快处理')
      } catch {
        ElMessage.error('举报失败')
      }
    }
  }).catch(() => {})
}

function handleDelete(post) {
  ElMessageBox.confirm('确定要删除这条动态吗？', '确认删除')
    .then(async () => {
      try {
        await deletePost(post.id, authStore.user.id)
        ElMessage.success('删除成功')
        posts.value = posts.value.filter(p => p.id !== post.id)
      } catch {
        ElMessage.error('删除失败')
      }
    })
    .catch(() => {})
}

// ===== 生命周期 =====
onMounted(() => {
  loadPosts(true)
})
</script>

<style scoped>
.community-feed {
  padding: 0 4px;
}

.feed-header {
  display: flex;
  align-items: center;
  gap: 16px;
}
.feed-header h2 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
}
.feed-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  opacity: 0.6;
}

.el-divider {
  margin: 12px 0;
}

/* ===== 发布 ===== */
.publish-section {
  margin-bottom: 4px;
}
.publish-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.publish-avatar {
  flex-shrink: 0;
}
.publish-form {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.publish-title :deep(.el-input__wrapper),
.publish-textarea :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 10px !important;
  color: var(--text-primary) !important;
}
.publish-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.publish-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.publish-left .el-button {
  border-radius: 8px !important;
}
.publish-toolbar .el-button--primary {
  border-radius: 8px !important;
  padding: 8px 20px !important;
  background: rgba(64, 158, 255, 0.10) !important;
  border: 1px solid rgba(64, 158, 255, 0.15) !important;
  color: #409eff !important;
  transition: all 0.3s ease !important;
}
.publish-toolbar .el-button--primary:hover {
  background: rgba(64, 158, 255, 0.20) !important;
  transform: translateY(-2px);
}

.upload-preview-box {
  position: relative;
  display: inline-block;
  margin-top: 4px;
}
.upload-preview-box img {
  max-width: 120px;
  max-height: 120px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.remove-img-icon {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(0,0,0,0.6);
  color: #fff;
  padding: 4px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 12px;
}
.remove-img-icon:hover {
  background: rgba(0,0,0,0.8);
}

/* ===== 工具栏 ===== */
.toolbar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.search-wrapper {
  position: relative;
  flex: 1;
  min-width: 150px;
}
.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 12px;
  z-index: 1;
}
.search-wrapper :deep(.el-input__wrapper) {
  padding-left: 30px;
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 10px !important;
  transition: all 0.3s ease !important;
}
.search-wrapper :deep(.el-input__wrapper:hover) {
  border-color: rgba(255, 255, 255, 0.15) !important;
}
.search-wrapper :deep(.el-input__wrapper.is-focus) {
  border-color: rgba(64, 158, 255, 0.4) !important;
  box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.06) !important;
}

.filter-tabs {
  display: flex;
  gap: 4px;
}
.filter-tab {
  padding: 4px 14px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.filter-tab:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateY(-2px);
}
.filter-tab.active {
  background: rgba(64, 158, 255, 0.10);
  border-color: rgba(64, 158, 255, 0.2);
  color: #409eff;
}

/* ===== 动态列表 ===== */
.post-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 4px;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
}
.empty-state p {
  font-size: 16px;
  color: var(--text-secondary);
  margin: 4px 0;
}
.empty-state span {
  font-size: 14px;
  opacity: 0.6;
}

.load-more {
  text-align: center;
  padding: 8px 0;
}
.load-more .el-button {
  color: var(--text-muted) !important;
  font-size: 13px;
}
.load-more .el-button:hover {
  color: var(--text-primary) !important;
}

/* ===== 响应式 ===== */
@media (max-width: 640px) {
  .feed-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  .feed-header h2 {
    font-size: 18px;
  }
  .publish-wrapper {
    flex-direction: column;
  }
  .publish-avatar {
    align-self: flex-start;
  }
  .publish-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }
  .publish-left {
    width: 100%;
    flex-wrap: wrap;
  }
  .publish-left .el-input {
    flex: 1;
    min-width: 120px;
  }
  .publish-toolbar .el-button--primary {
    width: 100%;
  }
  .toolbar {
    flex-direction: column;
  }
  .filter-tabs {
    justify-content: center;
  }
}
</style>