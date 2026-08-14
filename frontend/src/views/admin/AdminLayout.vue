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
        <router-link to="/admin/reports" class="admin-nav-item" :class="{ active: isActive('/admin/reports') }">
          <i class="fas fa-shield-halved"></i>
          <span>举报审核</span>
        </router-link>
        <router-link to="/admin/feedback" class="admin-nav-item" :class="{ active: isActive('/admin/feedback') }">
          <i class="fas fa-message"></i>
          <span>反馈 &amp; Q&A</span>
        </router-link>
        <router-link to="/admin/questions" class="admin-nav-item" :class="{ active: isActive('/admin/questions') }">
          <i class="fas fa-book"></i>
          <span>题库管理</span>
        </router-link>
        <router-link to="/admin/announcements" class="admin-nav-item" :class="{ active: isActive('/admin/announcements') }">
          <i class="fas fa-bullhorn"></i>
          <span>公告管理</span>
        </router-link>
        <router-link to="/admin/logs" class="admin-nav-item" :class="{ active: isActive('/admin/logs') }">
          <i class="fas fa-clock-rotate-left"></i>
          <span>操作日志</span>
        </router-link>
      </nav>

      <div class="admin-sidebar-footer">
        <router-link to="/home" class="back-link">
          <i class="fas fa-arrow-left"></i> 返回前台
        </router-link>
      </div>
    </aside>

    <!-- 内容区 -->
    <main class="admin-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

function isActive(path) {
  if (path === '/admin') return route.path === '/admin'
  return route.path.startsWith(path)
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: #0a0e17;
}

/* ===== 侧边栏 ===== */
.admin-sidebar {
  width: 220px;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
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
  color: #e0e0e0;
  letter-spacing: 0.5px;
}

/* ===== 导航 ===== */
.admin-nav {
  flex: 1;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.admin-nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.5);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.25s ease;
}
.admin-nav-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.8);
  transform: translateX(2px);
}
.admin-nav-item.active {
  background: rgba(64, 158, 255, 0.12);
  color: #409eff;
}
.admin-nav-item i {
  width: 18px;
  text-align: center;
}

/* ===== 底部 ===== */
.admin-sidebar-footer {
  padding: 14px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.back-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.4);
  text-decoration: none;
  font-size: 13px;
  transition: color 0.3s;
}
.back-link:hover { color: rgba(255, 255, 255, 0.7); }

/* ===== 主内容区 ===== */
.admin-main {
  flex: 1;
  padding: 28px 32px;
  overflow-y: auto;
  min-width: 0;
}
</style>
