<template>
  <div class="app-container">
    <!-- 桌面版窗口控制（悬浮右上角，无横栏）：网页版 isDesktop=false，这一行不渲染 -->
    <DesktopWindowControls v-if="isDesktop" />

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
import DesktopWindowControls from '@/desktop/DesktopWindowControls.vue'
import { isDesktop } from '@/desktop'

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

/* ===== 桌面壳：为右上角的窗口控制键让出一条高度 =====
   那 6 个键（返回/前进/刷新 ｜ 最小化/最大化/关闭）是 position:fixed 悬浮的
   （top:10px right:20px，高 32px）—— 直接压在页面内容上。
   这里由应用层统一让出 --jz-top：下面的 .app-container 加这段 padding，
   各页面的「满屏高度」也都写成 calc(100vh - var(--jz-top)) 一起扣掉，
   否则加了 padding 会让满屏页多出 44px、把滚动条又推回窗口。

   网页版没有 jz-desktop 这个类（由 desktop/index.js 在桌面壳里加到 <html>），
   --jz-top 保持 0px，渲染结果与改动前完全一致。 */
:root { --jz-top: 0px; }
/* ⚠️ 必须除以 --jz-scale 做反向补偿，理由和窗口按钮本身一样（见 DesktopWindowControls.vue）：
   按钮写的是 calc(32px / var(--jz-scale))，为的是缩放后**物理尺寸恒定**。
   留白如果写死 44px，窗口一缩小（zoom < 1）留白的物理高度跟着缩、
   而按钮物理高度不变 —— 又会压回内容上。这里同步补偿。 */
html.jz-desktop { --jz-top: calc(48px / var(--jz-scale, 1)); }

.app-container {
  min-height: 100vh;
  position: relative;
}
html.jz-desktop .app-container {
  padding-top: var(--jz-top);
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