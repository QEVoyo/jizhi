<template>
  <div class="app-container">
    <router-view v-slot="{ Component, route }">
      <!-- 显式 :duration：即使浏览器丢了 transitionend，也会到点强制结束过渡，
           绝不把新页面卡死在 enter-from(opacity:0)（2026-09-05 修「整页空白」） -->
      <Transition :name="route.meta.transition || 'page-fade'" mode="out-in" :duration="220">
        <component :is="Component" :key="route.path" />
      </Transition>
    </router-view>
    <!-- 全局搜索（登录后的主应用页面；落地页/登录/引导/管理后台不显示） -->
    <GlobalSearch v-if="showGlobalSearch" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import GlobalSearch from '@/components/GlobalSearch.vue'

const route = useRoute()

const showGlobalSearch = computed(() =>
  !!route.meta.requiresAuth &&
  !route.path.startsWith('/admin') &&
  route.path !== '/onboarding'
)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  width: 100%;
  min-height: 100vh;
}

.app-container {
  min-height: 100vh;
  position: relative;
}

/* ===== 页面路由过渡 ===== */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* 横向滑动变体（用于同层级子页） */
.page-slide-enter-active,
.page-slide-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.page-slide-enter-from {
  opacity: 0;
  transform: translateX(16px);
}
.page-slide-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(128, 128, 128, 0.3);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(128, 128, 128, 0.5);
}
</style>