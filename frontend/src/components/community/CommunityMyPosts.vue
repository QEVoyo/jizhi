<template>
  <div class="community-my-posts">
    <div class="my-posts-header">
      <h2>📝 我的发布</h2>
      <span class="my-posts-subtitle">管理你发布的所有动态</span>
    </div>

    <el-divider />

    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> 加载中...
    </div>

    <div v-else-if="!posts.length" class="empty-state">
      <i class="fas fa-pen" style="font-size: 48px; opacity: 0.3;"></i>
      <p>暂无发布</p >
      <span>去发布你的第一条动态吧！</span>
    </div>

    <div v-else class="post-list">
      <PostCard
        v-for="post in posts"
        :key="post.id"
        :post="post"
        @user-click="goUserProfile"
        @post-click="goPostDetail"
        @delete="handleDelete"
      />
      <div v-if="hasMore" class="load-more">
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
import { ElMessage } from 'element-plus'
import PostCard from './PostCard.vue'
import { getMyPosts, deletePost } from '@/api/community'

const router = useRouter()
const authStore = useAuthStore()

const posts = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const hasMore = ref(true)

async function loadData(reset = true) {
  if (reset) {
    page.value = 1
    posts.value = []
    hasMore.value = true
  }
  if (!hasMore.value) return

  loading.value = reset
  loadingMore.value = !reset

  try {
    const res = await getMyPosts(authStore.user.id, page.value)
    const items = res.posts || []
    if (reset) {
      posts.value = items
    } else {
      posts.value = [...posts.value, ...items]
    }
    hasMore.value = items.length === 20
    page.value++
  } catch {
    ElMessage.error('加载发布失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

function loadMore() {
  loadData(false)
}

function goUserProfile(userId) {
  router.push(`/community/user/${userId}`)
}

function goPostDetail(postId) {
  router.push(`/post/${postId}`)
}

function handleDelete(post) {
  posts.value = posts.value.filter(p => p.id !== post.id)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.community-my-posts {
  padding: 0 4px;
}

.my-posts-header {
  display: flex;
  align-items: center;
  gap: 16px;
}
.my-posts-header h2 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
}
.my-posts-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  opacity: 0.6;
}

.el-divider {
  margin: 12px 0;
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 20px;
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
</style>