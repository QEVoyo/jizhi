<template>
  <div class="community-sidebar">
    <!-- Logo -->
    <div class="sidebar-logo" @click="goHome">
      <img src="/logo.png" alt="基智" />
    </div>

    <!-- 导航 -->
    <nav class="sidebar-nav">
      <div
        v-for="item in navItems"
        :key="item.key"
        class="nav-item"
        :class="{ active: activeTab === item.key }"
        :title="item.label"
        @click="switchTab(item.key)"
      >
        <i :class="item.icon"></i>
        <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getFriendRequests, getUnreadCount } from '@/api/community'

const unreadCount = ref(0)  // 新增
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const friendRequestCount = ref(0)

const navItems = computed(() => [
  { key: 'feed', label: '动态广场', icon: 'fas fa-home', path: '/community' },
  { key: 'friends', label: '好友', icon: 'fas fa-users', path: '/community/friends', badge: friendRequestCount.value > 0 ? friendRequestCount.value : null },
  { key: 'rank', label: '排行榜', icon: 'fas fa-trophy', path: '/community/rank' },  // ← 新增
  { key: 'collections', label: '收藏', icon: 'fas fa-star', path: '/community/collections' },
  { key: 'my-posts', label: '我的发布', icon: 'fas fa-pen', path: '/community/my-posts' },
  { key: 'profile-card', label: '资料卡', icon: 'fas fa-id-card', path: '/community/profile-card' },
  { key: 'home', label: '返回主界面', icon: 'fas fa-arrow-left', path: '/home' }
])

const activeTab = computed(() => {
  const path = route.path
  if (path.startsWith('/community/chat/')) return null
  if (path.startsWith('/community/user/')) return null
  if (path === '/community' || path === '/community/') return 'feed'
  if (path.startsWith('/community/friends')) return 'friends'
  if (path.startsWith('/community/rank')) return 'rank'  // ← 新增
  if (path.startsWith('/community/collections')) return 'collections'
  if (path.startsWith('/community/my-posts')) return 'my-posts'
  if (path.startsWith('/community/profile-card')) return 'profile-card'
  if (path === '/home') return 'home'
  return null
})

async function loadBadges() {
  try {
    const [requestsRes, unreadRes] = await Promise.all([
      getFriendRequests(authStore.user.id),
      getUnreadCount(authStore.user.id)
    ])
    friendRequestCount.value = requestsRes.requests?.length || 0
    unreadCount.value = unreadRes.count || 0
  } catch {
    friendRequestCount.value = 0
    unreadCount.value = 0
  }
}

function switchTab(key) {
  if (key === 'home') {
    router.push('/home')
    return
  }
  const item = navItems.value.find(i => i.key === key)
  if (item) {
    router.push(item.path)
  }
}

function goHome() {
  router.push('/home')
}

onMounted(() => {
  loadBadges()
})
</script>

<style scoped>
.community-sidebar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 16px 0 20px;
  height: 100%;
  width: 100%;
  background: transparent;
}

.sidebar-logo {
  cursor: pointer;
  padding: 4px 0 8px;
  transition: all 0.3s ease;
}
.sidebar-logo img {
  width: 32px;
  height: 32px;
  object-fit: contain;
}
.sidebar-logo:hover {
  transform: scale(1.05);
  opacity: 0.7;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  width: 100%;
  flex: 1;
}

.nav-item {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 44px;
  border-radius: 12px;
  color: var(--text-secondary);
  font-size: 18px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: transparent;
}
.nav-item:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.06);
  transform: translateX(2px);
}
.nav-item.active {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.06);
}

.nav-badge {
  position: absolute;
  top: 4px;
  right: 8px;
  background: rgba(128, 128, 128, 0.3);
  color: var(--text-secondary);
  font-size: 10px;
  font-weight: 600;
  min-width: 18px;
  height: 18px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
  line-height: 1;
}
[data-theme="dark"] .nav-badge {
  background: rgba(255, 255, 255, 0.10);
}
.nav-item.active .nav-badge {
  background: rgba(255, 255, 255, 0.15);
}

@media (max-width: 768px) {
  .community-sidebar {
    flex-direction: row;
    padding: 8px 12px;
    height: auto;
    gap: 4px;
  }
  .sidebar-logo {
    display: none;
  }
  .sidebar-nav {
    flex-direction: row;
    justify-content: space-around;
  }
  .nav-item {
    height: 38px;
    width: auto;
    padding: 0 10px;
    font-size: 16px;
  }
  .nav-badge {
    top: 2px;
    right: 2px;
    font-size: 8px;
    min-width: 14px;
    height: 14px;
  }
}
</style>