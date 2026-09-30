<template>
  <div class="community-page">
    <AppLayout locked>
      <template #sidebar>
        <CommunitySidebar />
      </template>
      <template #main>
        <router-view />
      </template>
    </AppLayout>
  </div>
</template>

<script setup>
import AppLayout from '@/components/AppLayout.vue'
import CommunitySidebar from '@/components/community/CommunitySidebar.vue'
</script>

<style scoped>
/* ⚠️ 这里**不能**用 min-height（「至少一屏」）。
   AppLayout 内部已经是「定高外壳 + overflow:hidden + 内层自滚」（见其 .main-content），
   外层包装壳再声明一次「一屏」，两层叠加 = 文档高两屏 ——
   滚动必然跑回窗口，而内层那套滚动完全失效。
   包装壳只是给 AppLayout 一个挂载点，不该参与高度计算。
   （2026-09-30 修；同一天 AdminLayout 也是同一个毛病。） */
.community-page {
  height: calc(100vh - var(--jz-top, 0px));
  overflow: hidden;
}
</style>