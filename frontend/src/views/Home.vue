<template>
  <div class="home-page">
    <XiaojiCall />
  </div>
</template>

<script setup>
// 主界面 = 小基（2026-08-25）：登录后直达小基主页。
// 独立侧边栏已撤，导航内容（用户/搜索/图标/工具）并入小基页左栏（Sidebar 组件），
// 右栏为小基推荐/关心/日志；学程与社区页仍使用 AppLayout 侧边栏布局。
import XiaojiCall from '@/components/XiaojiCall.vue'
</script>

<style scoped>
.home-page {
  width: 100%;
  height: 100vh;
}
</style>
