import { createRouter, createWebHistory } from 'vue-router'
import { readByRoute } from '@/api/messages'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import { isDesktop } from '@/desktop'

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
    // 自定义计划的「学习内容」完整正文页（2026-10-01）——
    // 计划详情里只露前两行，点进来才是详细教学
    path: '/plan-lesson/:taskId',
    name: 'PlanLesson',
    component: () => import('@/views/PlanLesson.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/animation-demo',
    name: 'AnimationDemo',
    component: () => import('@/views/AnimationDemo.vue')
  },
  {
    // 小基设置已并进 /settings（用户要「设置融合为一个」）。
    // 保留这条路由做重定向，老链接和浏览器书签不会断。
    path: '/xiaoji/settings',
    redirect: '/settings',
  },
  {
    path: '/xiaoji/call',
    name: 'XiaojiCall',
    redirect: '/home',   // 小基 = 主界面（2026-08-25），旧入口重定向
    meta: { requiresAuth: true }
  },
  {
    path: '/xiaoji/voice-call',
    name: 'XiaojiVoiceCall',
    component: () => import('@/views/XiaojiVoiceCall.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/xiaoji/search',
    name: 'XiaojiSearch',
    component: () => import('@/views/XiaojiSearch.vue'),
    meta: { requiresAuth: true }
  },
  {
    // 「小基能带你去的地方」—— 以它为根的功能树，叶子是页面，不到题目。
    // 入口在搜索页顶栏（见 XiaojiSearch.vue）。
    path: '/xiaoji/tree',
    name: 'XiaojiTree',
    component: () => import('@/views/XiaojiTree.vue'),
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
    meta: { requiresAuth: false }
  },
  {
    path: '/message',
    name: 'MessageCenter',
    component: () => import('@/components/MessageCenter.vue'),
    meta: { requiresAuth: true }
  },
  {
    // 每日学习推荐 · 学习页（2026-10-08 新建）。
    // **首页「小基推荐」卡片和消息中心那条都跳这里** —— 用户拍板用独立全屏页，
    // 不是 §六 原设计的就地弹层。
    // :id 可选：不带就取最新一条（`notify()` 是先 INSERT 才拿得到 row id，
    // link 在插入那一刻就得定，所以推荐消息里存的是不带 id 的 /daily-learn）。
    path: '/daily-learn/:id?',
    name: 'DailyLearn',
    component: () => import('@/views/DailyLearn.vue'),
    meta: { requiresAuth: true }
  },
  {
    // 动态详情（2026-10-07 新建）。
    // 收藏页与「我的帖子」一直在 push('/post/xxx')，而这个路由**原本不存在**
    // —— 点了没反应。它同时是「评论被回复 / 帖子被赞」这类消息的落点，
    // 支持 ?comment={id} 滚到那条评论并高亮。
    path: '/post/:id',
    name: 'PostDetail',
    component: () => import('@/views/PostDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/vlp-debug',
    name: 'VlpDebug',
    component: () => import('@/views/VlpDebug.vue'),
    meta: { requiresAuth: false }   // 临时调试页,复现后删除
  },
  {
    path: '/theme',
    name: 'ThemeShare',
    component: () => import('@/views/ThemeShare.vue'),
    meta: { requiresAuth: false }   // 外观码分享直达页：好友免登录预览 + 一键应用
  },
  // ===== 视频库（2026-09-04：轮盘一级模块）=====
  {
    path: '/video-square',
    name: 'VideoSquare',
    component: () => import('@/views/VideoSquare.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/video/:id',
    name: 'VideoDetail',
    component: () => import('@/views/VideoDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/api-center',
    name: 'ApiCenter',
    component: () => import('@/views/ApiCenter.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/agent-center',
    name: 'AgentCenter',
    component: () => import('@/views/AgentCenter.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/agent-center/:agentKey',
    name: 'AgentDetail',
    component: () => import('@/views/AgentDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/wordbook',
    name: 'Wordbook',
    component: () => import('@/views/Wordbook.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/guide',
    name: 'Guide',
    component: () => import('@/views/Guide.vue'),
    meta: { requiresAuth: true }
  },
  // ===== 法律文件（公开页，注册前也能读）=====
  {
    path: '/agreement',
    name: 'UserAgreement',
    component: () => import('@/views/LegalDoc.vue'),
    props: { type: 'service' },
    meta: { requiresAuth: false }
  },
  {
    path: '/privacy',
    name: 'PrivacyPolicy',
    component: () => import('@/views/LegalDoc.vue'),
    props: { type: 'privacy' },
    meta: { requiresAuth: false }
  },
  {
    path: '/open-source',
    name: 'OpenSource',
    component: () => import('@/views/OpenSource.vue'),
    meta: { requiresAuth: false }
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
      { path: 'plans', name: 'AdminPlans', component: () => import('@/views/admin/AdminPlans.vue') },
      // 举报 / 反馈 / Q&A 共用同一个组件（页内是三个标签），
      // 但**各有各的路径** —— 否则侧边栏点「反馈」时地址变了、页面却不动。
      // 组件内用 PATH_TAB 把路径映射成初始标签。
      { path: 'reports', name: 'AdminReports', component: () => import('@/views/admin/AdminReports.vue') },
      { path: 'feedback', name: 'AdminFeedback', component: () => import('@/views/admin/AdminReports.vue') },
      { path: 'qa', name: 'AdminQA', component: () => import('@/views/admin/AdminReports.vue') },
      { path: 'questions', name: 'AdminQuestions', component: () => import('@/views/admin/AdminQuestions.vue') },
      { path: 'announcements', name: 'AdminAnnouncements', component: () => import('@/views/admin/AdminAnnouncements.vue') },
      { path: 'videos', name: 'AdminVideos', component: () => import('@/views/admin/AdminVideos.vue') },
      { path: 'security', name: 'AdminSecurity', component: () => import('@/views/admin/AdminSecurity.vue') },
      { path: 'logs', name: 'AdminLogs', component: () => import('@/views/admin/AdminLogs.vue') },
      { path: 'settings', name: 'AdminSettings', component: () => import('@/views/admin/AdminSettings.vue') },
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

let themeRestored = false

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 会话已持久化：启动后首次导航拉取账号主题（2026-09-02；登录动作路径在 authStore.login 里）
  if (!themeRestored && authStore.isLoggedIn && authStore.user?.id) {
    themeRestored = true
    useThemeStore().loadFromAccount(authStore.user.id).catch(() => {})
  }

  // 桌面版：没有「落地页」这个概念 —— 营销页是给搜索引擎和陌生人看的，
  // 而装了客户端的人已经决定要用了，再给他看一遍「免费注册」很出戏。
  // 未登录直接进登录页；已登录落到下面已有的分支（引导页 / 首页）。
  // 网页版 isDesktop=false，这条永远不成立。
  if (isDesktop && to.path === '/' && !authStore.isLoggedIn) {
    next('/login')
  }
  // 未登录访问受保护页面 → 去登录（带 redirect 参数）
  else if (to.meta.requiresAuth && !authStore.isLoggedIn) {
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

// ============================================================
// 已读路径 B：走到目标页面 → 指向该页的未读消息自动已读
// （2026-10-07）
//
// ⚠️ 为什么挂在全局守卫上，而不是每个页面自己标：
//    全站有 66 个消息点，写 66 处「进页面就标记」必漏；挂这里**一处覆盖全部**，
//    以后加消息点也不用管。服务端按 link 匹配当前 url，
//    并且**排除 system / todo 两组** —— 去 /settings 改个主题不该把
//    「你被禁言了」顺手清掉，待办也必须由处理动作收尾。
//
// 失败一律静默：这是个副作用，不能因为它把路由跳转搞挂。
// ============================================================
router.afterEach((to) => {
  try {
    if (!to.meta?.requiresAuth) return
    const auth = useAuthStore()
    const uid = auth.user?.id
    if (!uid) return
    const url = to.fullPath
    // 等页面渲染完、浏览器空闲再发，避免和目标页的首屏请求抢带宽
    const markRead = () => readByRoute(uid, url).catch(() => {})
    if (window.requestIdleCallback) window.requestIdleCallback(markRead, { timeout: 2500 })
    else setTimeout(markRead, 1200)
  } catch { /* 静默：标记已读失败不该影响导航 */ }
})

export default router