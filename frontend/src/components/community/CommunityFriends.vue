<template>
  <div class="community-friends">
    <!-- ===== 顶部标题 ===== -->
    <div class="friends-header">
      <h2>👥 好友</h2>
      <span class="friends-subtitle">管理你的好友和好友请求</span>
    </div>

    <el-divider />

    <!-- ===== Tab 切换 ===== -->
    <div class="friends-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="friends-tab"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        {{ tab.label }}
        <span v-if="tab.badge" class="tab-badge">{{ tab.badge }}</span>
      </button>
    </div>

    <!-- ===== 搜索好友 ===== -->
    <div class="search-section">
      <div class="search-wrapper">
        <i class="fas fa-search search-icon"></i>
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户..."
          size="small"
          clearable
          @input="handleSearch"
        />
      </div>
      <el-button size="small" type="primary" @click="handleSearch">
        搜索
      </el-button>
    </div>

    <el-divider />

    <!-- ===== 内容 ===== -->
    <div class="friends-content">
      <!-- 好友列表 -->
      <div v-if="activeTab === 'list'">
        <div v-if="loading" class="loading-state">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>
        <div v-else-if="!friends.length" class="empty-state">
          <i class="fas fa-user-friends" style="font-size: 48px; opacity: 0.3;"></i>
          <p>暂无好友</p >
          <span>去认识一些志同道合的学习伙伴吧！</span>
        </div>
        <div v-else class="friend-list">
          <div v-for="friend in friends" :key="friend.id" class="friend-card">
            <div class="friend-info" @click="goUserProfile(friend.id)">
              <el-avatar :size="44" :src="friend.avatar_url || ''" class="friend-avatar">
                {{ friend.nickname?.[0] || 'U' }}
              </el-avatar>
              <div class="friend-detail">
                <span class="friend-name">{{ friend.nickname || '用户' }}</span>
                <span class="friend-account">{{ friend.account || '' }}</span>
              </div>
            </div>
            <div class="friend-actions">
              <el-button size="small" @click="goChat(friend.id)">
                <i class="fas fa-comment"></i> 聊天
              </el-button>
              <el-button size="small" type="danger" plain @click="removeFriend(friend.id)">
                <i class="fas fa-user-minus"></i>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 好友请求 -->
      <div v-if="activeTab === 'requests'">
        <div v-if="loading" class="loading-state">
          <i class="fas fa-spinner fa-spin"></i> 加载中...
        </div>
        <div v-else-if="!requests.length" class="empty-state">
          <i class="fas fa-inbox" style="font-size: 48px; opacity: 0.3;"></i>
          <p>暂无好友请求</p >
          <span>等待好友申请吧</span>
        </div>
        <div v-else class="request-list">
          <div v-for="req in requests" :key="req.id" class="request-card">
            <div class="request-info" @click="goUserProfile(req.id)">
              <el-avatar :size="44" :src="req.avatar_url || ''" class="request-avatar">
                {{ req.nickname?.[0] || 'U' }}
              </el-avatar>
              <div class="request-detail">
                <span class="request-name">{{ req.nickname || '用户' }}</span>
                <span class="request-account">{{ req.account || '' }}</span>
                <span class="request-time">{{ formatTime(req.created_at) }}</span>
              </div>
            </div>
            <div class="request-actions">
              <el-button size="small" type="success" @click="handleRequest(req, 'accept')">
                <i class="fas fa-check"></i> 接受
              </el-button>
              <el-button size="small" type="danger" plain @click="handleRequest(req, 'reject')">
                <i class="fas fa-times"></i>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 搜索用户 -->
      <div v-if="activeTab === 'search'">
        <div v-if="searchResults.length" class="search-results">
          <div v-for="user in searchResults" :key="user.id" class="search-result-card">
            <div class="result-info" @click="goUserProfile(user.id)">
              <el-avatar :size="44" :src="user.avatar_url || ''" class="result-avatar">
                {{ user.nickname?.[0] || 'U' }}
              </el-avatar>
              <div class="result-detail">
                <span class="result-name">{{ user.nickname || '用户' }}</span>
                <span class="result-account">{{ user.account || '' }}</span>
              </div>
            </div>
            <el-button
              v-if="user.friend_status === 'friend'"
              size="small"
              disabled
            >
              已是好友
            </el-button>
            <el-button
              v-else-if="user.friend_status === 'pending'"
              size="small"
              disabled
            >
              已发送
            </el-button>
            <el-button
              v-else
              size="small"
              type="primary"
              @click="sendRequest(user.id)"
            >
              <i class="fas fa-user-plus"></i> 添加
            </el-button>
          </div>
        </div>
        <div v-else-if="searchKeyword && !searchLoading" class="empty-state">
          <p>未找到用户</p >
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getFriends,
  getFriendRequests,
  searchUsers,
  sendFriendRequest,
  handleFriendRequest,
  deleteFriend
} from '@/api/community'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('list')
const loading = ref(false)
const searchLoading = ref(false)
const searchKeyword = ref('')
const friends = ref([])
const requests = ref([])
const searchResults = ref([])

const tabs = computed(() => [
  { key: 'list', label: '好友列表', badge: null },
  { key: 'requests', label: '好友请求', badge: requests.value.length || 0 },
  { key: 'search', label: '搜索用户', badge: null }
])

function formatTime(time) {
  if (!time) return ''
  const t = new Date(time)
  return t.toLocaleDateString()
}

async function loadData() {
  loading.value = true
  try {
    const [friendsRes, requestsRes] = await Promise.all([
      getFriends(authStore.user.id),
      getFriendRequests(authStore.user.id)
    ])
    friends.value = friendsRes.friends || []
    requests.value = requestsRes.requests || []
  } catch {
    ElMessage.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

async function handleSearch() {
  if (!searchKeyword.value.trim()) {
    searchResults.value = []
    return
  }
  searchLoading.value = true
  try {
    const res = await searchUsers(searchKeyword.value, authStore.user.id)
    searchResults.value = res.users || []
    // 检查好友状态
    for (const user of searchResults.value) {
      if (friends.value.find(f => f.id === user.id)) {
        user.friend_status = 'friend'
      } else if (requests.value.find(r => r.user_id === user.id)) {
        user.friend_status = 'pending'
      } else {
        user.friend_status = 'none'
      }
    }
  } catch {
    ElMessage.error('搜索失败')
  } finally {
    searchLoading.value = false
  }
}

async function sendRequest(userId) {
  try {
    await sendFriendRequest(authStore.user.id, userId)
    ElMessage.success('好友请求已发送')
    await loadData()
    handleSearch()
  } catch {
    ElMessage.error('发送失败')
  }
}

async function handleRequest(req, action) {
  try {
    await handleFriendRequest(req.id, action, authStore.user.id)
    ElMessage.success(action === 'accept' ? '已接受' : '已拒绝')
    await loadData()
  } catch {
    ElMessage.error('操作失败')
  }
}

function removeFriend(friendId) {
  ElMessageBox.confirm('确定要删除这个好友吗？', '确认删除')
    .then(async () => {
      try {
        await deleteFriend(authStore.user.id, friendId)
        ElMessage.success('已删除')
        await loadData()
      } catch {
        ElMessage.error('删除失败')
      }
    })
    .catch(() => {})
}

function switchTab(key) {
  activeTab.value = key
  if (key === 'search') {
    searchResults.value = []
    searchKeyword.value = ''
  }
}

function goUserProfile(userId) {
  router.push(`/community/user/${userId}`)
}

function goChat(friendId) {
  router.push(`/community/chat/${friendId}`)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.community-friends {
  padding: 0 4px;
}

.friends-header {
  display: flex;
  align-items: center;
  gap: 16px;
}
.friends-header h2 {
  font-size: 22px;
  color: var(--text-primary);
  margin: 0;
}
.friends-subtitle {
  font-size: 14px;
  color: var(--text-muted);
  opacity: 0.6;
}

.el-divider {
  margin: 12px 0;
}

.friends-tabs {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
}
.friends-tab {
  padding: 6px 18px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}
.friends-tab:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateY(-2px);
}
.friends-tab.active {
  background: rgba(64, 158, 255, 0.10);
  border-color: rgba(64, 158, 255, 0.2);
  color: #409eff;
}
.tab-badge {
  background: rgba(128, 128, 128, 0.15);
  color: var(--text-secondary);
  font-size: 11px;
  padding: 0 8px;
  border-radius: 10px;
}

.search-section {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}
.search-wrapper {
  position: relative;
  flex: 1;
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
}

.friend-list,
.request-list,
.search-results {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.friend-card,
.request-card,
.search-result-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  background: rgba(255, 255, 255, 0.02);
  transition: all 0.3s ease;
}
.friend-card:hover,
.request-card:hover,
.search-result-card:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}

.friend-info,
.request-info,
.result-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  flex: 1;
}
.friend-avatar,
.request-avatar,
.result-avatar {
  flex-shrink: 0;
}
.friend-detail,
.request-detail,
.result-detail {
  display: flex;
  flex-direction: column;
}
.friend-name,
.request-name,
.result-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.friend-account,
.request-account,
.result-account {
  font-size: 12px;
  color: var(--text-muted);
}
.request-time {
  font-size: 11px;
  color: var(--text-muted);
}

.friend-actions,
.request-actions {
  display: flex;
  gap: 6px;
}
.friend-actions .el-button,
.request-actions .el-button {
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}
.friend-actions .el-button:hover,
.request-actions .el-button:hover {
  transform: translateY(-2px);
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
</style>