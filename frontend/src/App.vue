<template>
  <div class="app-container" :style="bgStyle">
    <router-view />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useThemeStore } from '@/stores/theme'
import { BG_MAP } from '@/utils/constants'

const route = useRoute()
const themeStore = useThemeStore()

const bgKey = computed(() => {
  const map = {
    '/': 'landing',
    '/login': 'login',
    '/home': 'main',
    '/profile': 'profile',
    '/resource-lib': 'resource_lib',
    '/career': 'career',
    '/career/rank': 'rank',
    '/career/tasks': 'tasks',
    '/career/achievements': 'achievements',
    '/do-question': 'do_question',
    '/mastery-board': 'mastery_board',
    '/set-detail': 'set_detail',
    '/generate-from-mastery': 'generate',
    '/community': 'community',
    '/qa': 'qa',
    '/message': 'message'
  }
  return map[route.path] || 'main'
})

const bgImage = computed(() => {
  const theme = themeStore.currentTheme
  return BG_MAP[theme]?.[bgKey.value] || BG_MAP[theme]?.main || ''
})

const overlayColor = computed(() => {
  return themeStore.currentTheme === 'dark'
    ? 'rgba(0, 0, 0, 0.5)'
    : 'rgba(255, 255, 255, 0.15)'
})

const bgStyle = computed(() => {
  const image = bgImage.value
  return {
    backgroundImage: `linear-gradient(${overlayColor.value}, ${overlayColor.value}), url(${image})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundAttachment: 'fixed',
    minHeight: '100vh',
    backgroundRepeat: 'no-repeat'
  }
})
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