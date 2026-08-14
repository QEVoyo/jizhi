import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import CommunityFriends from '@/components/community/CommunityFriends.vue'
import XiaojiSettings from '@/components/XiaojiSettings.vue'
import XiaojiCall from '@/components/XiaojiCall.vue'

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
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('@/views/Onboarding.vue'),
    meta: { requiresAuth: true }
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
  {
    path: '/do-question/:taskId',
    name: 'DoQuestion',
    component: () => import('@/views/DoQuestion.vue'),
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/do-question',
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
  {
    path: '/xiaoji/settings',
    name: 'XiaojiSettings',
    component: XiaojiSettings,
    meta: { requiresAuth: true }
  },
  {
    path: '/xiaoji/call',
    name: 'XiaojiCall',
    component: XiaojiCall,
    meta: { requiresAuth: true }
  },
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
        component: CommunityFriends
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
  {
    path: '/qa',
    name: 'QAPage',
    component: () => import('@/components/QAPage.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/message',
    name: 'MessageCenter',
    component: () => import('@/components/MessageCenter.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/api-center',
    name: 'ApiCenter',
    component: () => import('@/views/ApiCenter.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/open-source',
    name: 'OpenSource',
    component: () => import('@/views/OpenSource.vue'),
    meta: { requiresAuth: true }
  },
  // ===== 学科计划（考纲架构）=====
  {
    path: '/subject-plan',
    name: 'SyllabusHub',
    component: () => import('@/views/SyllabusHub.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/subject-plan/:syllabusId',
    name: 'SyllabusDetail',
    component: () => import('@/views/SyllabusDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/subject-plan/:syllabusId/practice',
    name: 'SubjectPractice',
    component: () => import('@/views/SubjectPractice.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/subject-plan/:syllabusId/exam/:paperId',
    name: 'ExamPaper',
    component: () => import('@/views/ExamPaper.vue'),
    meta: { requiresAuth: true }
  },
  // ===== 管理后台 =====
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', name: 'AdminDashboard', component: () => import('@/views/admin/AdminDashboard.vue') },
      { path: 'users', name: 'AdminUsers', component: () => import('@/views/admin/AdminUsers.vue') },
      { path: 'reports', name: 'AdminReports', component: () => import('@/views/admin/AdminReports.vue') },
      { path: 'feedback', name: 'AdminFeedback', component: () => import('@/views/admin/AdminReports.vue') },
      { path: 'questions', name: 'AdminQuestions', component: () => import('@/views/admin/AdminQuestions.vue') },
      { path: 'announcements', name: 'AdminAnnouncements', component: () => import('@/views/admin/AdminAnnouncements.vue') },
      { path: 'logs', name: 'AdminLogs', component: () => import('@/views/admin/AdminLogs.vue') },
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    }
    // 同层级路由切换（如 Tab 切换）不强制回到顶部
    // 这里按约定：路径前缀相同（同模块内部切换）保持在原位置
    if (from && to.path.split('/').slice(0, 3).join('/') === from.path.split('/').slice(0, 3).join('/')) {
      return false  // 保持原位（如 Tab 切换）
    }
    return { top: 0 }
  }
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 未登录访问受保护页面 → 去登录（带 redirect 参数）
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  }
  // 已登录但不是管理员访问管理后台 → 去首页
  else if (to.meta.requiresAdmin && !authStore.user?.is_admin && authStore.user?.role === 'user') {
    next('/home')
  }
  // 已登录但访问登录页 → 去首页（但要先检查是否需要引导）
  else if (to.path === '/login' && authStore.isLoggedIn) {
    next(authStore.needsOnboarding ? '/onboarding' : '/home')
  }
  // 已登录访问首页 → 同上
  else if (to.path === '/' && authStore.isLoggedIn) {
    next(authStore.needsOnboarding ? '/onboarding' : '/home')
  }
  // 已登录且首次进入首页 → 优先引导
  else if (to.path === '/home' && authStore.needsOnboarding) {
    next('/onboarding')
  }
  // 引导页 → 如果不需要引导就跳过（编辑模式除外）
  else if (to.path === '/onboarding' && !authStore.needsOnboarding && to.query.edit !== 'true') {
    next('/home')
  }
  else {
    next()
  }
})

export default router