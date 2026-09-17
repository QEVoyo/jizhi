// ============================================================
// 全站页面命名册 — 全局搜索的唯一数据源
//   每个页面（含侧边栏没有的）都有：名称 + 路径 + 搜索别名 + 拼音首字母
//   aliases 支持中文关键词 / 英文缩写；initials 支持拼音首字母模糊
// ============================================================

export const STATIC_PAGES = [
  { title: '小基',          path: '/home',                    aliases: ['主界面', '首页', '小基', '聊天', '对话', 'home', 'xiaoji'],  initials: 'xj' },
  { title: '个人中心',      path: '/profile',                 aliases: ['我的', '个人资料', 'profile'],                              initials: 'grzx' },
  { title: '设置',          path: '/settings',                aliases: ['设置中心', '偏好', 'settings'],                            initials: 'sz' },
  { title: '资源库',        path: '/resource-lib',            aliases: ['资源', '题集', '错题本', '生成历史', 'resource'],            initials: 'zyk' },
  { title: '掌握度看板',    path: '/mastery-board',           aliases: ['掌握度', '薄弱点', 'mastery'],                             initials: 'zwdkb' },
  { title: '我的题集',      path: '/set-detail',              aliases: ['题集详情', '收藏题'],                                      initials: 'wdtj' },
  { title: '生成题目',      path: '/generate-from-mastery',   aliases: ['定向生成', '出题'],                                        initials: 'sctm' },
  { title: '学程',          path: '/career',                  aliases: ['积分', '段位', '等级', 'career'],                          initials: 'xc' },
  { title: '段位排行',      path: '/career/rank',             aliases: ['排行', '排名', 'rank'],                                    initials: 'dwph' },
  { title: '成就任务',      path: '/career/tasks',            aliases: ['成就', '任务'],                                           initials: 'cjr' },
  { title: '成就墙',        path: '/career/achievements',     aliases: ['成就', '徽章'],                                           initials: 'cjq' },
  { title: '个人画像',      path: '/profile-card',            aliases: ['画像', '能力', '学习画像'],                                initials: 'grhx' },
  { title: '学科计划',      path: '/subject-plan',            aliases: ['考纲', '计划', 'syllabus'],                                initials: 'xkjh' },
  { title: '社区',          path: '/community',               aliases: ['动态', '广场', 'community'],                               initials: 'sq' },
  { title: '社区好友',      path: '/community/friends',       aliases: ['好友', '关注'],                                           initials: 'sqhy' },
  { title: '社区排行',      path: '/community/rank',          aliases: ['社区排行榜'],                                             initials: 'sqph' },
  { title: '我的帖子',      path: '/community/my-posts',      aliases: ['帖子'],                                                  initials: 'wdtz' },
  { title: '社区收藏',      path: '/community/collections',   aliases: ['收藏集'],                                                 initials: 'sqsc' },
  { title: '帮助中心',      path: '/qa',                      aliases: ['Q&A', '帮助', 'FAQ', '常见问题', 'qa'],                    initials: 'bzzx' },
  { title: '消息中心',      path: '/message',                 aliases: ['消息', '公告', '通知'],                                    initials: 'xxzx' },
  { title: '评估中心',      path: '/evaluation-center',       aliases: ['评估'],                                                   initials: 'pgzx' },
  { title: '学情报告',      path: '/evaluation-report',       aliases: ['报告', '学情'],                                           initials: 'xqbg' },
  { title: '评估表',        path: '/evaluation-table',        aliases: ['自评', '测评'],                                           initials: 'pgb' },
  { title: '语音通话',      path: '/xiaoji/voice-call',       aliases: ['通话', '打电话', '电话', 'voice call'],                    initials: 'yyth' },
  { title: '小基设置',      path: '/xiaoji/settings',         aliases: ['小基设置'],                                               initials: 'xjsz' },
  { title: '聊天记录搜索',  path: '/xiaoji/search',           aliases: ['消息搜索', '聊天记录', '历史消息'],                        initials: 'ltss' },
  { title: '词条本',        path: '/wordbook',                aliases: ['单词本', '生词', '单词', 'wordbook', '词条'],              initials: 'ctb' },
  { title: '智能体中心',    path: '/agent-center',            aliases: ['agent', '智能体', '磨合'],                                 initials: 'zntzx' },
  { title: 'API 管理',      path: '/api-center',              aliases: ['api', 'key', '接口'],                                     initials: 'apigl' },
  { title: '开源文档',      path: '/open-source',             aliases: ['开源', '文档'],                                           initials: 'kywd' },
  { title: '使用指引',      path: '/guide',                   aliases: ['说明书', '使用说明', '指南', 'guide', 'manual'],           initials: 'syzy' },
]

// 管理后台（仅管理员可见）
export const ADMIN_PAGES = [
  { title: '管理后台',      path: '/admin',                   aliases: ['admin', '后台', '管理', '仪表盘'],                        initials: 'glht' },
  { title: '用户管理',      path: '/admin/users',             aliases: ['封禁'],                                                  initials: 'yhgl' },
  { title: '内容审核',      path: '/admin/reports',           aliases: ['举报', '反馈'],                                          initials: 'nrsh' },
  { title: '题库管理',      path: '/admin/questions',         aliases: ['题目', '导入'],                                          initials: 'tkgl' },
  { title: '公告管理',      path: '/admin/announcements',     aliases: ['公告'],                                                  initials: 'gggl' },
  { title: '操作日志',      path: '/admin/logs',              aliases: ['审计'],                                                  initials: 'czrz' },
]

// 智能体详情页（key 固定，与 mockAgents.js / agent-center 一致）
export const AGENT_PAGES = [
  { title: '对话 Agent',    path: '/agent-center/chat',       aliases: ['对话', '答疑', '路由', 'chat'],                            initials: 'dh' },
  { title: '规划 Agent',    path: '/agent-center/plan',       aliases: ['规划', '备考计划', 'plan'],                                initials: 'gh' },
  { title: '生成 Agent',    path: '/agent-center/generate',   aliases: ['生成', '出题', 'generate'],                                initials: 'sc' },
  { title: '评估 Agent',    path: '/agent-center/evaluate',   aliases: ['评估', '批改', 'evaluate'],                                initials: 'pg' },
  { title: '小基 Agent',    path: '/agent-center/xiaoji',     aliases: ['小基', '陪伴', 'xiaoji'],                                  initials: 'xj' },
]

// ============================================================
// 最近访问标题解析（动态路由 → 模块名，供「最近访问」列表显示）
// ============================================================
const PREFIX_TITLES = [
  ['/subject-plan', '学科计划'],
  ['/agent-center', '智能体中心'],
  ['/community', '社区'],
  ['/career', '学程'],
  ['/xiaoji', '小基'],
  ['/do-question', '做题'],
  ['/admin', '管理后台'],
]

export function resolvePageTitle(path) {
  const hit = [...STATIC_PAGES, ...ADMIN_PAGES].find(p => p.path === path)
  if (hit) return hit.title
  if (path.includes('/exam/')) return '真题套卷'
  if (path.endsWith('/practice')) return '做题练习'
  for (const [prefix, title] of PREFIX_TITLES) {
    if (path.startsWith(prefix)) return title
  }
  return path
}
