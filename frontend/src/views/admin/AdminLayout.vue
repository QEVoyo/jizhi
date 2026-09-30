<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <aside class="admin-sidebar">
      <div class="admin-brand" @click="$router.push('/home')">
        <img src="/logo.png" alt="基智" class="admin-logo" />
        <span class="admin-title">管理后台</span>
      </div>

      <nav class="admin-nav">
        <router-link to="/admin" exact class="admin-nav-item" :class="{ active: isActive('/admin') }">
          <i class="fas fa-th-large"></i>
          <span>主面板</span>
        </router-link>
        <router-link to="/admin/users" class="admin-nav-item" :class="{ active: isActive('/admin/users') }">
          <i class="fas fa-users"></i>
          <span>用户管理</span>
        </router-link>
        <!-- 举报 / 反馈 / Q&A 原先是「举报审核」+「反馈 & Q&A」两项，
             后者指向 /admin/feedback 但组件标签写死为 reports —— 点了没反应。
             现在三项与页内三个标签一一对应。 -->
        <router-link to="/admin/reports" class="admin-nav-item" :class="{ active: isActive('/admin/reports') }">
          <i class="fas fa-shield-halved"></i>
          <span>举报审核</span>
        </router-link>
        <router-link to="/admin/feedback" class="admin-nav-item" :class="{ active: isActive('/admin/feedback') }">
          <i class="fas fa-message"></i>
          <span>用户反馈</span>
        </router-link>
        <router-link to="/admin/qa" class="admin-nav-item" :class="{ active: isActive('/admin/qa') }">
          <i class="fas fa-circle-question"></i>
          <span>Q&A 帮助</span>
        </router-link>
        <router-link to="/admin/questions" class="admin-nav-item" :class="{ active: isActive('/admin/questions') }">
          <i class="fas fa-book"></i>
          <span>题库管理</span>
        </router-link>
        <router-link to="/admin/announcements" class="admin-nav-item" :class="{ active: isActive('/admin/announcements') }">
          <i class="fas fa-bullhorn"></i>
          <span>公告管理</span>
        </router-link>
        <router-link to="/admin/videos" class="admin-nav-item" :class="{ active: isActive('/admin/videos') }">
          <i class="fas fa-clapperboard"></i>
          <span>视频库管理</span>
        </router-link>
        <router-link to="/admin/logs" class="admin-nav-item" :class="{ active: isActive('/admin/logs') }">
          <i class="fas fa-clock-rotate-left"></i>
          <span>操作日志</span>
        </router-link>
        <router-link to="/admin/settings" class="admin-nav-item" :class="{ active: isActive('/admin/settings') }">
          <i class="fas fa-gear"></i>
          <span>系统信息</span>
        </router-link>
      </nav>

      <div class="admin-sidebar-footer">
        <!-- 当前管理员身份：原先整个后台看不到"我是谁"，
             点危险操作（封禁/提权）时没有任何身份提示。 -->
        <div class="admin-who">
          <img
            class="admin-avatar"
            :src="authStore.user?.avatar_url || '/logo.png'"
            :alt="displayName"
            @error="onAvatarError"
          />
          <div class="admin-who-text">
            <span class="admin-who-name" :title="displayName">{{ displayName }}</span>
            <span class="admin-role-badge" :class="roleClass">{{ roleLabel }}</span>
          </div>
        </div>

        <router-link to="/home" class="back-link">
          <i class="fas fa-arrow-left"></i> 返回前台
        </router-link>
        <button class="back-link logout-btn" @click="handleLogout">
          <i class="fas fa-right-from-bracket"></i> 退出登录
        </button>
      </div>
    </aside>

    <!-- 内容区 -->
    <main class="admin-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const displayName = computed(
  () => authStore.user?.nickname || authStore.user?.user_account || authStore.user?.email || '管理员'
)

const ROLE_LABEL = { super_admin: '超级管理员', admin: '管理员' }
const roleLabel = computed(() => ROLE_LABEL[authStore.user?.role] || '管理员')
const roleClass = computed(() => (authStore.user?.role === 'super_admin' ? 'super' : 'normal'))

// 头像加载失败时退回站标，避免裂图
function onAvatarError(e) { e.target.src = '/logo.png' }

// 与其他入口一致：先确认再退出
function handleLogout() {
  ElMessageBox.confirm('确定要退出登录吗？', '确认退出')
    .then(async () => {
      await authStore.logout()
      ElMessage.success('已退出')
      await new Promise(r => setTimeout(r, 100))
      router.push('/login')
    })
    .catch(() => {})
}

function isActive(path) {
  if (route.path === path) return true
  // ⚠️ 必须按**路径段**比较，不能直接 startsWith：
  //    '/admin/questions'（题库管理）也以 '/admin/qa' 开头，
  //    用 startsWith 会让进题库时「Q&A 帮助」同时高亮。
  return route.path.startsWith(path + '/')
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  /* ⚠️ 必须用固定高 + overflow:hidden，**不能**用 min-height。
     「固定高」在这里写作 calc(100vh - var(--jz-top))：--jz-top 是桌面壳里
     给右上角 6 个窗口控制键让出的那条高度，网页版为 0px、效果不变。
     min-height 会让容器随内容长高，内层 .admin-main 的 overflow-y:auto 就永远不会生效
     —— 滚动落到窗口上：无边框桌面壳里滚动条贴着窗口最外缘，和应用是两截。
     这是本项目「两种滚动写法」的老问题（2026-09-28 设置页已改过一次）：
       AppLayout 式：外层定高 + 内层自滚 → 滚动条在应用内     ← 要的是这个
       普通页式    ：min-height → 窗口滚                     ← 后台原先就是这样
     顶栏/侧边栏因此天然固定，不需要 position:sticky。 */
  height: calc(100vh - var(--jz-top, 0px));
  overflow: hidden;
  background: var(--bg-color);
}

/* ===== 侧边栏 ===== */
.admin-sidebar {
  width: 220px;
  background: color-mix(in srgb, var(--surface, #ffffff) 3%, transparent);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid color-mix(in srgb, var(--text-primary) 6%, transparent);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.admin-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 18px 16px;
  cursor: pointer;
  border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 5%, transparent);
  transition: opacity 0.3s;
}
.admin-brand:hover { opacity: 0.8; }

.admin-logo {
  width: 28px;
  height: 28px;
  object-fit: contain;
}

.admin-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

/* ===== 导航 ===== */
.admin-nav {
  flex: 1;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  /* min-height:0 让 flex 子项能被压缩，overflow 才会生效 ——
     否则菜单一长就顶破 100vh 的容器，又把滚动推回窗口。
     导航变长时滚动发生在侧边栏内部，品牌区和底部身份区保持固定。 */
  min-height: 0;
  overflow-y: auto;
}
.admin-nav::-webkit-scrollbar { width: 6px; }
.admin-nav::-webkit-scrollbar-thumb {
  background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent);
  border-radius: 3px;
}

.admin-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.25s ease;
}
.admin-nav-item:hover {
  background: color-mix(in srgb, var(--surface, #ffffff) 5%, transparent);
  color: var(--text-primary);
  transform: translateX(2px);
}
.admin-nav-item.active {
  background: color-mix(in srgb, var(--brand) 12%, transparent);
  color: var(--brand);
}
.admin-nav-item i {
  width: 18px;
  text-align: center;
}

/* ===== 底部 ===== */
.admin-sidebar-footer {
  padding: 14px 18px;
  border-top: 1px solid color-mix(in srgb, var(--text-primary) 5%, transparent);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ===== 当前管理员 ===== */
.admin-who {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 8px 12px;
  margin-bottom: 2px;
  border-bottom: 1px solid color-mix(in srgb, var(--text-primary) 4%, transparent);
}
.admin-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  background: color-mix(in srgb, var(--surface, #ffffff) 8%, transparent);
}
.admin-who-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.admin-who-name {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.admin-role-badge {
  align-self: flex-start;
  font-size: 10px;
  line-height: 1.6;
  padding: 0 6px;
  border-radius: 8px;
}
.admin-role-badge.super {
  background: rgba(230, 162, 60, 0.14);
  color: #e6a23c;
}
.admin-role-badge.normal {
  background: color-mix(in srgb, var(--brand) 14%, transparent);
  color: var(--brand);
}

.back-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 13px;
  transition: color 0.3s;
}
.back-link:hover { color: var(--text-primary); }

/* 退出登录是个按钮，得清掉浏览器默认样式才和「返回前台」看着是一对 */
.logout-btn {
  background: none;
  border: none;
  padding: 0;
  font: inherit;
  cursor: pointer;
  text-align: left;
}
.logout-btn:hover { color: #f56c6c; }

/* ===== 主内容区 ===== */
.admin-main {
  flex: 1;
  padding: 28px 32px;
  overflow-y: auto;
  min-width: 0;
}
</style>
