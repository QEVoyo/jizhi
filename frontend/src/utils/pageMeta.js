// ============================================================
// 全站页面命名册 — 全局搜索的唯一数据源
//   每个页面（含侧边栏没有的）都有：名称 + 路径 + 搜索别名 + 拼音首字母
//   aliases 支持中文关键词 / 英文缩写；initials 支持拼音首字母模糊
// ============================================================

export const STATIC_PAGES = [
  { title: '主界面',        path: '/home',                    aliases: ['主界面', '首页', '小基', '聊天', '对话', 'home', 'xiaoji'],  initials: 'xj' , group: '学习' , desc: '小基的主界面：聊天、今日任务、快捷入口都从这儿进' , wire: 'chat' },
  { title: '个人中心',      path: '/profile',                 aliases: ['我的', '个人资料', 'profile'],                              initials: 'grzx' , group: '我的' , desc: '个人资料、学习数据与账号信息' , wire: 'form' },
  { title: '设置',          path: '/settings',                aliases: ['设置中心', '偏好', 'settings'],                            initials: 'sz' , group: '我的' , desc: '全站唯一设置入口：偏好、外观、通知、快捷键、账号安全' , wire: 'form' },
  { title: '资源库',        path: '/resource-lib',            aliases: ['资源', '题集', '错题本', '生成历史', 'resource'],            initials: 'zyk' , group: '学习' , desc: '自己生成过的题集与历史，按知识点归类' , wire: 'board' },
  { title: '掌握度看板',    path: '/mastery-board',           aliases: ['掌握度', '薄弱点', 'mastery'],                             initials: 'zwdkb' , group: '学习' , desc: '按知识点看掌握度，找出该补的地方' , wire: 'board' },
  { title: '我的题集',      path: '/set-detail',              aliases: ['题集详情', '收藏题'],                                      initials: 'wdtj' , group: '学习' , desc: '某一个题集的题目列表与作答入口' , wire: 'list' },
  { title: '生成题目',      path: '/generate-from-mastery',   aliases: ['定向生成', '出题'],                                        initials: 'sctm' , group: '学习' , desc: '挑薄弱知识点，定向生成一组新题' , wire: 'form' },
  { title: '学程',          path: '/career',                  aliases: ['积分', '段位', '等级', 'career'],                          initials: 'xc' , group: '学程' , desc: '积分、段位与成长轨迹的总览' , wire: 'dashboard' },
  { title: '段位排行',      path: '/career/rank',             aliases: ['排行', '排名', 'rank'],                                    initials: 'dwph' , group: '学程' , desc: '段位排行榜，看自己在全站的位置' , wire: 'table' },
  { title: '成就任务',      path: '/career/tasks',            aliases: ['成就', '任务'],                                           initials: 'cjr' , group: '学程' , desc: '成就任务列表与领取入口' , wire: 'list' },
  { title: '成就墙',        path: '/career/achievements',     aliases: ['成就', '徽章'],                                           initials: 'cjq' , group: '学程' , desc: '已解锁的成就徽章墙' , wire: 'board' },
  { title: '个人画像',      path: '/profile-card',            aliases: ['画像', '能力', '学习画像'],                                initials: 'grhx' , group: '我的' , desc: 'AI 根据你的作答生成的学习画像' , wire: 'dashboard' },
  { title: '学科计划',      path: '/subject-plan',            aliases: ['考纲', '计划', 'syllabus'],                                initials: 'xkjh' , group: '学习' , desc: '选一门考纲，走摸底诊断 → 三阶段计划 → 每日任务' , wire: 'board' },
  { title: '社区',          path: '/community',               aliases: ['动态', '广场', 'community'],                               initials: 'sq' , group: '社区' , desc: '社区动态流：看别人的学习记录与分享' , wire: 'list' },
  { title: '社区好友',      path: '/community/friends',       aliases: ['好友', '关注'],                                           initials: 'sqhy' , group: '社区' , desc: '好友列表与好友请求' , wire: 'list' },
  { title: '社区排行',      path: '/community/rank',          aliases: ['社区排行榜'],                                             initials: 'sqph' , group: '社区' , desc: '社区活跃度排行榜' , wire: 'table' },
  { title: '我的帖子',      path: '/community/my-posts',      aliases: ['帖子'],                                                  initials: 'wdtz' , group: '社区' , desc: '自己发过的帖子与互动' , wire: 'list' },
  { title: '社区收藏',      path: '/community/collections',   aliases: ['收藏集'],                                                 initials: 'sqsc' , group: '社区' , desc: '收藏过的帖子集合' , wire: 'board' },
  { title: '帮助中心',      path: '/qa',                      aliases: ['Q&A', '帮助', 'FAQ', '常见问题', 'qa'],                    initials: 'bzzx' , group: '帮助' , desc: '常见问题与使用答疑' , wire: 'list' },
  { title: '消息中心',      path: '/message',                 aliases: ['消息', '公告', '通知'],                                    initials: 'xxzx' , group: '我的' , desc: '消息中心：所有通知按七种形态呈现' , wire: 'list' },
  { title: '评估中心',      path: '/evaluation-center',       aliases: ['评估'],                                                   initials: 'pgzx' , group: '评估' , desc: '学情评估的入口与概览' , wire: 'dashboard' },
  { title: '学情报告',      path: '/evaluation-report',       aliases: ['报告', '学情'],                                           initials: 'xqbg' , group: '评估' , desc: '这一阶段的学习报告' , wire: 'detail' },
  { title: '评估表',        path: '/evaluation-table',        aliases: ['自评', '测评'],                                           initials: 'pgb' , group: '评估' , desc: '逐题的评估表，看每题得分与建议' , wire: 'table' },
  { title: '语音通话',      path: '/xiaoji/voice-call',       aliases: ['通话', '打电话', '电话', 'voice call'],                    initials: 'yyth' , group: '小基' , desc: '和小基打电话，实时语音对话' , wire: 'call' },
  { title: '小基设置',      path: '/xiaoji/settings',         aliases: ['小基设置'],                                               initials: 'xjsz' , group: '小基' , desc: '小基的名字、语气、音色与主动关心频率' , wire: 'form' },
  { title: '聊天记录搜索',  path: '/xiaoji/search',           aliases: ['消息搜索', '聊天记录', '历史消息'],                        initials: 'ltss' , group: '小基' , desc: '在和小基的历史聊天记录里搜关键词' , wire: 'list' },
  { title: '词条本',        path: '/wordbook',                aliases: ['单词本', '生词', '单词', 'wordbook', '词条'],              initials: 'ctb' , group: '学习' , desc: '查过的词条与掌握情况' , wire: 'table' },
  { title: '智能体中心',    path: '/agent-center',            aliases: ['agent', '智能体', '磨合'],                                 initials: 'zntzx' , group: '智能体' , desc: '五个智能体的协作全景与磨合参数' , wire: 'dashboard' },
  { title: 'API 管理',      path: '/api-center',              aliases: ['api', 'key', '接口'],                                     initials: 'apigl' , group: '我的' , desc: '模型画廊与自己的 API Key 配置' , wire: 'board' },
  { title: '开源文档',      path: '/open-source',             aliases: ['开源', '文档'],                                           initials: 'kywd' , group: '帮助' , desc: '开源说明与依赖清单' , wire: 'detail' },
  { title: '学习计划', path: '/learning-plan', aliases: ['计划', '今日任务'], initials: 'xxjh', group: '学习', desc: '三阶段备考计划：阶段目标、每日任务与完成情况', wire: 'list' },
  { title: '视频广场', path: '/video-square', aliases: ['视频', '讲解视频'], initials: 'spsc', group: '学习', desc: '讲解视频广场：按知识点推荐与检索', wire: 'board' },
  { title: '主题分享', path: '/theme', aliases: ['主题', '配色', '外观'], initials: 'ztfx', group: '我的', desc: '换主题、导出配色，看别人分享的主题', wire: 'board' },
  { title: '语音通话', path: '/xiaoji/call', aliases: ['通话', '打电话'], initials: 'yyth', group: '小基', desc: '和小基实时语音通话的独立界面', wire: 'call' },
  { title: '功能树', path: '/xiaoji/tree', aliases: ['地图', '全部页面', '能去哪'], initials: 'gns', group: '小基', desc: '就是这一页：小基能带你去的地方，一眼看全', wire: 'tree' },
  { title: '动画演示', path: '/animation-demo', aliases: ['动画', '演示'], initials: 'dhm', group: '帮助', desc: '题目动画的渲染演示页', wire: 'detail' },
  { title: '视频渲染调试', path: '/vlp-debug', aliases: ['调试', '渲染'], initials: 'sprd', group: '帮助', desc: '视频渲染调试页（排产与帧检查）', wire: 'detail' },
  { title: '新手引导', path: '/onboarding', aliases: ['引导', '新手', '第一次'], initials: 'xsyd', group: '我的', desc: '第一次进来时的引导：填学习阶段与目标', wire: 'form' },
  { title: '计划预览', path: '/plan-preview', aliases: ['预览', '计划'], initials: 'jhtl', group: '学习', desc: '生成好的学习计划预览，确认后再落地', wire: 'timeline' },
  { title: '使用指引',      path: '/guide',                   aliases: ['说明书', '使用说明', '指南', 'guide', 'manual'],           initials: 'syzy' , group: '帮助' , desc: '使用说明书：从选考纲到每日任务怎么走' , wire: 'detail' },
  { title: '用户服务协议',  path: '/agreement',               aliases: ['用户协议', '服务协议', '协议', 'agreement', 'terms'],      initials: 'yhxy' , group: '帮助' , desc: '使用基智前需要阅读并同意的服务条款' , wire: 'detail' },
  { title: '隐私政策',      path: '/privacy',                 aliases: ['隐私', '个人信息', '个人信息保护', 'privacy'],              initials: 'yszc' , group: '帮助' , desc: '我们收集哪些信息、如何使用与保护' , wire: 'detail' },
]

// 管理后台（仅管理员可见）
export const ADMIN_PAGES = [
  { title: '管理后台',      path: '/admin',                   aliases: ['admin', '后台', '管理', '仪表盘'],                        initials: 'glht' , group: '管理后台' , desc: '后台主面板：10 项统计，每张卡都能点进去' , wire: 'dashboard' },
  { title: '用户管理',      path: '/admin/users',             aliases: ['封禁'],                                                  initials: 'yhgl' , group: '管理后台' , desc: '全站用户列表、封禁与角色管理' , wire: 'table' },
  { title: '内容审核',      path: '/admin/reports',           aliases: ['举报', '反馈'],                                          initials: 'nrsh' , group: '管理后台' , desc: '举报、反馈、Q&A 三合一的审核台' , wire: 'list' },
  { title: '题库管理',      path: '/admin/questions',         aliases: ['题目', '导入'],                                          initials: 'tkgl' , group: '管理后台' , desc: '题库的增删改查与批量导入' , wire: 'table' },
  { title: '公告管理',      path: '/admin/announcements',     aliases: ['公告'],                                                  initials: 'gggl' , group: '管理后台' , desc: '发布与下架全站公告' , wire: 'list' },
  { title: '学习计划', path: '/admin/plans', aliases: ['计划'], initials: 'glxx', group: '管理后台', desc: '跨用户的学习计划列表', wire: 'table' },
  { title: '反馈', path: '/admin/feedback', aliases: ['反馈', '意见'], initials: 'fk', group: '管理后台', desc: '用户反馈的处理队列', wire: 'list' },
  { title: 'Q&A', path: '/admin/qa', aliases: ['问答', '答疑'], initials: 'qa', group: '管理后台', desc: '用户提问与答疑记录', wire: 'list' },
  { title: '视频库', path: '/admin/videos', aliases: ['视频', '审核'], initials: 'spk', group: '管理后台', desc: '用户投稿视频的审核与批量暖库', wire: 'board' },
  { title: '安全中心', path: '/admin/security', aliases: ['安全', '信誉', '审计'], initials: 'aqzx', group: '管理后台', desc: '安全事件 / 用户信誉 / 生成审计三个 Tab', wire: 'dashboard' },
  { title: '系统信息', path: '/admin/settings', aliases: ['设置', 'api'], initials: 'xtxx', group: '管理后台', desc: '系统信息与 API 提供方状态', wire: 'form' },
  { title: '操作日志',      path: '/admin/logs',              aliases: ['审计'],                                                  initials: 'czrz' , group: '管理后台' , desc: '管理员操作审计日志' , wire: 'table' },
]

// 智能体详情页（key 固定，与 mockAgents.js / agent-center 一致）
export const AGENT_PAGES = [
  { title: '对话 Agent',    path: '/agent-center/chat',       aliases: ['对话', '答疑', '路由', 'chat'],                            initials: 'dh' , desc: '对话智能体：答疑与意图分流' , wire: 'chat' },
  { title: '规划 Agent',    path: '/agent-center/plan',       aliases: ['规划', '备考计划', 'plan'],                                initials: 'gh' , desc: '规划智能体：把目标拆成可执行的计划' , wire: 'timeline' },
  { title: '生成 Agent',    path: '/agent-center/generate',   aliases: ['生成', '出题', 'generate'],                                initials: 'sc' , desc: '生成智能体：出题与内容生成' , wire: 'dashboard' },
  { title: '评估 Agent',    path: '/agent-center/evaluate',   aliases: ['评估', '批改', 'evaluate'],                                initials: 'pg' , desc: '评估智能体：批改与学情判断' , wire: 'dashboard' },
  { title: '小基 Agent',    path: '/agent-center/xiaoji',     aliases: ['小基', '陪伴', 'xiaoji'],                                  initials: 'xj' , desc: '小基本体：陪伴与督促这条线' , wire: 'chat' },
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
