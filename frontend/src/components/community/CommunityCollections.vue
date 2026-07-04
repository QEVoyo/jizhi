<template>
  <div class="community-collections">
    <div class="collections-header">
      <h2>⭐ 我的收藏</h2>
      <span class="collections-subtitle">收藏的精彩动态</span>
    </div>

    <el-divider />

    <div v-if="loading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i> 加载中...
    </div>

    <div v-else-if="!collections.length" class="empty-state">
      <i class="fas fa-star" style="font-size: 48px; opacity: 0.3;"></i>
      <p>暂无收藏</p >
      <span>看到喜欢的动态，点击收藏吧！</span>
    </div>

    <div v-else class="collection-list">
      <div v-for="item in collections" :key="item.id" class="collection-card">
        <PostCard
          :post="item.posts"
          @user-click="goUserProfile"
          @post-click="goPostDetail"
        />
      </div>
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
import { getCollections } from '@/api/community'

const router = useRouter()
const authStore = useAuthStore()

const collections = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const page = ref(1)
const hasMore = ref(true)

async function loadData(reset = true) {
  if (reset) {
    page.value = 1
    collections.value = []
    hasMore.value = true
  }
  if (!hasMore.value) return

  loading.value = reset
  loadingMore.value = !reset

  try {
    const res = await getCollections(authStore.user.id, page.value)
    const items = res.collections || []
    if (reset) {
      collections.value = items
    } else {
      collections.value = [...collections.value, ...items]
    }
    hasMore.value = items.length === 20
    page.value++
  } catch {
    ElMessage.error('加载收藏失败')
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

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.community-collections {
  padding: 0 4px;
}

.collections-header {
  display: flex;
  align-items: center;
  gap: 16px;
}
.collections-header h2 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
}
.collections-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  opacity: 0.6;
}

.el-divider {
  margin: 12px 0;
}

.collection-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.collection-card {
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  background: rgba(255, 255, 255, 0.02);
  overflow: hidden;
}
.collection-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
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