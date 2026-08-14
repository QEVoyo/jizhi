<template>
  <div class="app-layout">
    <aside class="sidebar" :class="{ collapsed: isCollapsed }">
      <!-- 收起/展开按钮（锁定状态隐藏） -->
      <div v-if="!locked" class="sidebar-toggle" @click="toggleSidebar">
        <i :class="isCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left'"></i>
      </div>
      <slot name="sidebar" />
    </aside>
    <main class="main-content" :class="{ expanded: isCollapsed }">
      <slot name="main" />
    </main>
  </div>
</template>

<script setup>
import { ref, provide, watch } from 'vue'

const props = defineProps({
  locked: {
    type: Boolean,
    default: false
  }
})

const isCollapsed = ref(props.locked)
provide('sidebarCollapsed', isCollapsed)

function toggleSidebar() {
  if (props.locked) return
  isCollapsed.value = !isCollapsed.value
}
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
  height: 100vh;
  overflow: hidden;
}

/* ===== 侧边栏 — 毛玻璃 ===== */
.sidebar {
  width: 260px;
  min-height: 100vh;
  height: 100vh;
  background: linear-gradient(170deg,
    rgba(139,92,246,.15) 0%,
    rgba(108,140,255,.10) 25%,
    rgba(6,182,212,.06) 55%,
    rgba(16,185,129,.10) 80%,
    rgba(139,92,246,.12) 100%
  );
  backdrop-filter: blur(24px) saturate(1.2);
  -webkit-backdrop-filter: blur(24px) saturate(1.2);
  border-right: 1px solid rgba(255,255,255,.06);
  padding: 16px 14px 10px 14px;
  flex-shrink: 0;
  overflow: hidden;           /* 由内部 sidebar-scroll 处理滚动 */
  transition: width 0.3s ease, padding 0.3s ease;
  position: relative;
  display: flex;
  flex-direction: column;
}
/* 毛玻璃微光 — 右侧边缘的高光线 */
.sidebar::before {
  content: ''; position: absolute; top: 0; right: 0; bottom: 0; width: 1px;
  background: linear-gradient(180deg,
    rgba(255,255,255,.1) 0%,
    rgba(255,255,255,.04) 40%,
    transparent 70%,
    rgba(255,255,255,.04) 100%
  );
  pointer-events: none; z-index: 99;
}

.sidebar.collapsed {
  width: 64px;
  padding: 16px 8px 10px 8px;
}

/* ===== 收起/展开按钮 ===== */
.sidebar-toggle {
  position: absolute;
  top: 12px;
  right: 10px;
  cursor: pointer;
  color: var(--text-muted);
  padding: 4px 6px;
  border-radius: 6px;
  font-size: 14px;
  transition: all 0.3s ease;
  z-index: 10;
  background: rgba(255, 255, 255, 0.04);
}
.sidebar-toggle:hover {
  background: rgba(255, 255, 255, 0.10);
  color: var(--text-primary);
  transform: scale(1.08);
}
.sidebar-toggle:active {
  transform: scale(0.95);
}
.sidebar.collapsed .sidebar-toggle {
  right: 50%;
  transform: translateX(50%);
}
.sidebar.collapsed .sidebar-toggle:hover {
  transform: translateX(50%) scale(1.08);
}
.sidebar.collapsed .sidebar-toggle:active {
  transform: translateX(50%) scale(0.95);
}

/* ===== 主内容 ===== */
.main-content {
  flex: 1;
  padding: 20px 28px;
  overflow-y: auto;
  min-height: 100vh;
  height: 100vh;
  transition: padding 0.3s ease, margin-left 0.3s ease;
}

.main-content::-webkit-scrollbar {
  width: 4px;
}
.main-content::-webkit-scrollbar-thumb {
  background: rgba(128, 128, 128, 0.2);
  border-radius: 2px;
}
.main-content::-webkit-scrollbar-thumb:hover {
  background: rgba(128, 128, 128, 0.3);
}

.main-content.expanded {
  padding: 20px 32px;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .app-layout {
    flex-direction: column;
    height: auto;
    overflow: visible;
  }
  .sidebar {
    width: 100% !important;
    min-height: auto;
    height: auto;
    max-height: 260px;
    border-right: none;
    border-bottom: 1px solid var(--border-color);
    padding: 12px 14px 60px 14px;
    overflow-y: auto;
  }
  .sidebar.collapsed {
    max-height: 56px;
    overflow: hidden;
    padding: 8px 12px 40px 12px;
  }
  .sidebar-toggle {
    top: 8px;
    right: 12px;
  }
  .main-content {
    padding: 12px 16px;
    height: auto;
    min-height: auto;
    overflow: visible;
    background: transparent !important; /* 👈 加这行 */
  }
  .main-content.expanded {
    padding: 12px 16px;
  }
}
</style>