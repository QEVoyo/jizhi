<template>
  <div class="home-page" :style="backgroundStyle">
    <AppLayout>
      <template #sidebar>
        <Sidebar />
      </template>
      <template #main>
        <ChatArea />
      </template>
    </AppLayout>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { BG_MAP } from '@/utils/constants'
import AppLayout from '@/components/AppLayout.vue'
import Sidebar from '@/components/Sidebar.vue'
import ChatArea from '@/components/ChatArea.vue'

const themeStore = useThemeStore()

// ===== 背景图计算 =====
const backgroundStyle = computed(() => {
  const mode = themeStore.currentTheme === 'dark' ? 'dark' : 'light'
  const bgMap = BG_MAP[mode]
  const bgKey = 'main'
  const bg = bgMap[bgKey] || bgMap.main || bgMap.landing

  return {
    backgroundImage: `url(${bg})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundAttachment: 'fixed',
    minHeight: '100vh'
  }
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  width: 100%;
  display: block;
  position: relative;
}
</style>