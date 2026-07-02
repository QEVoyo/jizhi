<template>
  <div class="app-layout">
    <aside class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="sidebar-toggle" @click="toggleSidebar">
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
import { ref, provide } from 'vue'

const isCollapsed = ref(false)
provide('sidebarCollapsed', isCollapsed)

function toggleSidebar() {
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

.sidebar {
  width: 260px;
  min-height: 100vh;
  height: 100vh;
  background: var(--card-bg);
  backdrop-filter: blur(16px);
  border-right: 1px solid var(--border-color);
  padding: 16px 14px 70px 14px;
  flex-shrink: 0;
  overflow-y: auto;
  transition: width 0.3s ease, padding 0.3s ease;
  position: relative;
  display: flex;
  flex-direction: column;
}

.sidebar::-webkit-scrollbar {
  width: 3px;
}
.sidebar::-webkit-scrollbar-thumb {
  background: rgba(128, 128, 128, 0.2);
  border-radius: 2px;
}

.sidebar.collapsed {
  width: 64px;
  padding: 16px 10px 53px 10px;
  overflow-y: hidden;
}

.sidebar.collapsed::-webkit-scrollbar {
  width: 0;
}

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
}
.sidebar.collapsed .sidebar-toggle {
  right: 50%;
  transform: translateX(50%);
}

.main-content {
  flex: 1;
  padding: 20px 28px;
  overflow-y: auto;
  min-height: 100vh;
  height: 100vh;
  transition: padding 0.3s ease;
}

.main-content::-webkit-scrollbar {
  width: 4px;
}
.main-content::-webkit-scrollbar-thumb {
  background: rgba(128, 128, 128, 0.2);
  border-radius: 2px;
}

.main-content.expanded {
  padding: 20px 32px;
}

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
  }
  .main-content.expanded {
    padding: 12px 16px;
  }
}
</style>