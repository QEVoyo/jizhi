import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/resource-lib',
    name: 'ResourceLib',
    component: () => import('@/views/ResourceLib.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/career',
    name: 'Career',
    component: () => import('@/views/Career.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/career/rank',
    name: 'CareerRank',
    component: () => import('@/views/CareerRank.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/career/tasks',
    name: 'CareerTasks',
    component: () => import('@/views/CareerTasks.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/career/achievements',
    name: 'CareerAchievements',
    component: () => import('@/views/CareerAchievements.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/do-question',
    name: 'DoQuestion',
    component: () => import('@/views/DoQuestion.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/mastery-board',
    name: 'MasteryBoard',
    component: () => import('@/views/MasteryBoard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/set-detail',
    name: 'SetDetail',
    component: () => import('@/views/SetDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/generate-from-mastery',
    name: 'GenerateFromMastery',
    component: () => import('@/views/GenerateFromMastery.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && authStore.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router