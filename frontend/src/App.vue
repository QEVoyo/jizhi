<template>
  <div class="app-container" :style="bgStyle">
    <router-view v-slot="{ Component, route }">
      <Transition :name="route.meta.transition || 'page-fade'" mode="out-in">
        <component :is="Component" :key="route.path" />
      </Transition>
    </router-view>
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
  const p = route.path
  // 精确匹配
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
    '/message': 'message',
    '/subject-plan': 'subject_plan',
    '/subject-plan/diagnosis': 'subject_plan_diagnosis',
  }
  if (map[p]) return map[p]
  // 动态路由前缀匹配
  if (p.startsWith('/subject-plan/') && p.endsWith('/practice')) return 'subject_practice'
  if (p.startsWith('/subject-plan/') && p.includes('/exam/')) return 'subject_practice'
  if (p.startsWith('/subject-plan/')) return 'subject_plan_detail'
  if (p.startsWith('/do-question/')) return 'do_question'
  if (p.startsWith('/community/')) return 'community'
  return 'main'
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