import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: () => import('@/views/Landing.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/home',
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
    path: '/evaluation-center',
    name: 'EvaluationCenter',
    component: () => import('@/views/EvaluationCenter.vue'),
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
  // ================== 做题路由（必须两条都写） ==================
  {
    // 带 ID 的路径（用于从错题本、历史、题集、规划详情点进去）
    path: '/do-question/:taskId',
    name: 'DoQuestion',
    component: () => import('@/views/DoQuestion.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    // 不带 ID 的路径（用于从资源库点击“生成题目”后直接跳转做题）
    path: '/do-question',
    component: () => import('@/views/DoQuestion.vue'),
    meta: { requiresAuth: true }
  },
  // ============================================================
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
  },
  {
    path: '/evaluation-report',
    name: 'EvaluationReport',
    component: () => import('@/views/EvaluationReport.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/evaluation-table',
    name: 'EvaluationTable',
    component: () => import('@/views/EvaluationTable.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/learning-plan',
    name: 'LearningPlan',
    component: () => import('@/views/LearningPlan.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile-card',
    name: 'ProfileCard',
    component: () => import('@/views/ProfileCard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/plan-preview',
    name: 'PlanPreview',
    component: () => import('@/views/PlanPreview.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/plan-detail/:id',
    name: 'PlanDetail',
    component: () => import('@/views/PlanDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/animation-demo',
    name: 'AnimationDemo',
    component: () => import('@/views/AnimationDemo.vue')
  },
  // ===== 社区 =====
  {
    path: '/community',
    name: 'Community',
    component: () => import('@/views/Community.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'CommunityFeed',
        component: () => import('@/components/community/CommunityFeed.vue')
      },
      {
        path: 'friends',
        name: 'CommunityFriends',
        component: () => import('@/components/community/CommunityFriends.vue')
      },
      {
        path: 'rank',
        name: 'CommunityRank',
        component: () => import('@/components/community/Rank.vue')
      },
      {
        path: 'collections',
        name: 'CommunityCollections',
        component: () => import('@/components/community/CommunityCollections.vue')
      },
      {
        path: 'my-posts',
        name: 'CommunityMyPosts',
        component: () => import('@/components/community/CommunityMyPosts.vue')
      },
      {
        path: 'profile-card',
        name: 'CommunityProfileCard',
        component: () => import('@/components/community/CommunityProfileCard.vue')
      },
      {
        path: 'chat/:friendId',
        name: 'CommunityChat',
        component: () => import('@/components/community/CommunityChat.vue')
      },
      {
        path: 'user/:userId',
        name: 'CommunityUserProfile',
        component: () => import('@/components/community/CommunityUserProfile.vue')
      }
    ]
  },
  // ===== Q&A =====
  {
    path: '/qa',
    name: 'QAPage',
    component: () => import('@/components/QAPage.vue'),
    meta: { requiresAuth: true }
  },
  // ===== 消息中心 =====
  {
    path: '/message',
    name: 'MessageCenter',
    component: () => import('@/components/MessageCenter.vue'),
    meta: { requiresAuth: true }
  },
  // ===== API管理 =====
  {
    path: '/api-center',
    name: 'ApiCenter',
    component: () => import('@/views/ApiCenter.vue'),
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
    next('/home')
  } else if (to.path === '/' && authStore.isLoggedIn) {
    next('/home')
  } else {
    next()
  }
})

export default router