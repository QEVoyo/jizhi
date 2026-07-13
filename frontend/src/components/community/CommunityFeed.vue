<template>
  <div class="community-feed">
    <!-- ===== 顶部标题 ===== -->
    <div class="feed-header">
      <h2>🏠 动态广场</h2>
      <span class="feed-subtitle">分享学习心得，发现志同道合的伙伴</span>
    </div>

    <el-divider />

    <!-- ===== 发布动态 ===== -->
    <div class="publish-section">
      <div class="publish-wrapper">
        <el-avatar :size="40" :src="authStore.user?.avatar_url || ''" class="publish-avatar">
          {{ authStore.user?.nickname?.[0] || 'U' }}
        </el-avatar>
        <div class="publish-input-wrapper">
          <el-input
            v-model="publishContent"
            type="textarea"
            :rows="2"
            placeholder="分享你的学习心得..."
            maxlength="500"
            show-word-limit
            class="publish-input"
            @focus="isPublishingFocused = true"
            @blur="isPublishingFocused = false"
          />
          <div class="publish-actions">
            <el-button type="primary" :loading="publishing" @click="handlePublish">
              <i class="fas fa-paper-plane"></i> 发布
            </el-button>
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

    <!-- ===== 动态列表 ===== -->
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

      <!-- 动态卡片 -->
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

// ===== 状态 =====
const posts = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const hasMore = ref(true)
const publishContent = ref('')
const publishing = ref(false)
const isPublishingFocused = ref(false)
const searchKeyword = ref('')
const activeFilter = ref('all')

const filterTabs = [
  { key: 'all', label: '全部' },
  { key: 'friends', label: '好友' }
]

// ===== 方法 =====
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

async function handlePublish() {
  if (!publishContent.value.trim()) {
    ElMessage.warning('请输入内容')
    return
  }
  publishing.value = true
  try {
    await createPost({
      user_id: authStore.user.id,
      content: publishContent.value.trim()
    })
    ElMessage.success('发布成功')
    publishContent.value = ''
    loadPosts(true)
  } catch (error) {
    console.error('发布失败:', error)
    ElMessage.error(error.response?.data?.detail || '发布失败')
  } finally {
    publishing.value = false
  }
}

async function handleLike(post) {
  try {
    if (post.is_liked) {
      await unlikePost(post.id, authStore.user.id)
      post.is_liked = false
      post.like_count--
    } else {
      await likePost(post.id, authStore.user.id)
      post.is_liked = true
      post.like_count++
    }
  } catch (error) {
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
.publish-input-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.publish-input :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 12px !important;
  color: var(--text-primary) !important;
  resize: none;
  transition: all 0.3s ease !important;
}
.publish-input :deep(.el-textarea__inner:focus) {
  border-color: rgba(64, 158, 255, 0.4) !important;
  box-shadow: 0 0 0 4px rgba(64, 158, 255, 0.06) !important;
}
.publish-actions {
  display: flex;
  justify-content: flex-end;
}
.publish-actions .el-button {
  border-radius: 10px !important;
  padding: 8px 24px !important;
  background: rgba(64, 158, 255, 0.10) !important;
  border: 1px solid rgba(64, 158, 255, 0.15) !important;
  color: #409eff !important;
  transition: all 0.3s ease !important;
}
.publish-actions .el-button:hover {
  background: rgba(64, 158, 255, 0.20) !important;
  transform: translateY(-2px);
}
.publish-actions .el-button:active {
  transform: translateY(0) scale(0.97);
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
  .publish-actions {
    width: 100%;
  }
  .publish-actions .el-button {
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