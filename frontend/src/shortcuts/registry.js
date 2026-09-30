/**
 * 快捷键动作清单 —— **唯一数据源**。
 *
 * 分发器、设置页的列表、冲突检测、恢复默认，全部从这里读。
 * 新增一个可绑定的动作 = 在这里加一条，别处不用动。
 *
 * 字段：
 *   id       稳定标识，**存进账号的就是它**（改 label 不影响用户已有绑定）
 *   group    设置页里的分组
 *   label    给人看的名字
 *   desc     一句话说明（设置页显示）
 *   def      默认组合键，空串 = 默认不绑
 *   scope    'all' 全端可用 / 'desktop' 仅桌面壳（网页里不注册、不显示）
 *   run      执行体，收到 ctx（见 manager.js）
 */
import { isDesktop } from '@/desktop'

/** 导航类：跳页面。路径与 EdgeNavDock 的导航项保持一致 */
const NAV = [
  { key: 'home', label: '回到小基', path: '/home', def: 'Ctrl+Shift+H' },
  { key: 'profile', label: '个人中心', path: '/profile', def: '' },
  { key: 'settings', label: '打开设置', path: '/settings', def: 'Ctrl+Comma' },
  { key: 'resource-lib', label: '资源库', path: '/resource-lib', def: '' },
  { key: 'evaluation-center', label: '评估中心', path: '/evaluation-center', def: '' },
  { key: 'career', label: '学程', path: '/career', def: '' },
  { key: 'subject-plan', label: '学科计划', path: '/subject-plan', def: '' },
  { key: 'profile-card', label: '个人画像', path: '/profile-card', def: '' },
  { key: 'community', label: '社区', path: '/community', def: '' },
  { key: 'qa', label: 'Q&A', path: '/qa', def: '' },
  { key: 'message', label: '消息中心', path: '/message', def: '' },
  { key: 'wordbook', label: '词条本', path: '/wordbook', def: '' },
  { key: 'video-square', label: '视频库', path: '/video-square', def: '' },
  { key: 'agent-center', label: '智能体中心', path: '/agent-center', def: '' },
  { key: 'api-center', label: 'API 管理', path: '/api-center', def: '' },
]

export const SHORTCUT_ACTIONS = [
  // ── 导航 ──
  ...NAV.map((n) => ({
    id: `nav.${n.key}`,
    group: '导航',
    label: n.label,
    desc: `跳转到「${n.label}」`,
    def: n.def,
    scope: 'all',
    run: (ctx) => ctx.router.push(n.path),
  })),

  // ── 动作 ──
  {
    id: 'action.search',
    group: '动作',
    label: '全局搜索',
    desc: '打开全局搜索面板',
    // Ctrl+K 是这里原本就硬绑着的键（GlobalSearch.vue），收进注册表后
    // 用户可以在设置页改掉它 —— 原来那处监听已删除。
    def: 'Ctrl+K',
    scope: 'all',
    run: (ctx) => ctx.nav.toggleSearch(),
  },
  // ⚠️ 这里**没有**「切换深浅色」。
  //    项目在 09-03 就去掉了浅/深/跟随系统开关，外观改成四轴定制
  //    （背景色 + 组件色 + 主题色 + 字体色），theme store 里根本没有这个方法。
  //    我第一版按惯例想当然加了 `action.theme`，那是个**不存在的功能** ——
  //    按了没反应，正是这个项目最忌讳的「看起来有、其实是空的」。
  //    要做的话得先有「一键切到另一套四轴」的产品定义，不是快捷键层面能补的。
  {
    id: 'action.xiaojiNewChat',
    group: '动作',
    label: '回到对话',
    desc: '回到小基并聚焦输入框',
    def: 'Ctrl+Shift+C',
    scope: 'all',
    run: (ctx) => {
      ctx.router.push('/home')
      // 等路由切完再聚焦，否则元素还不存在
      setTimeout(() => {
        const el = document.querySelector('.chat-input, .jz-chat-input, textarea')
        if (el && typeof el.focus === 'function') el.focus()
      }, 260)
    },
  },

  // ── 窗口（仅桌面壳）──
  // 这几个原来散在 desktop/index.js 的悬浮按钮里，收进注册表后也能绑键。
  {
    id: 'win.minimize', group: '窗口', label: '最小化', desc: '最小化窗口',
    def: '', scope: 'desktop',
    run: (ctx) => ctx.desktop.winMinimize(),
  },
  {
    id: 'win.maximize', group: '窗口', label: '最大化 / 还原', desc: '切换窗口最大化',
    def: '', scope: 'desktop',
    run: (ctx) => ctx.desktop.winToggleMaximize(),
  },
  {
    id: 'win.close', group: '窗口', label: '关闭窗口', desc: '关闭桌面端窗口',
    def: '', scope: 'desktop',
    run: (ctx) => ctx.desktop.winClose(),
  },
  {
    id: 'win.refresh', group: '窗口', label: '刷新页面', desc: '重新加载当前页面',
    def: '', scope: 'desktop',
    run: () => window.location.reload(),
  },
  {
    id: 'win.back', group: '窗口', label: '后退', desc: '返回上一页',
    def: '', scope: 'desktop',
    run: (ctx) => window.history.back(),
  },
  {
    id: 'win.forward', group: '窗口', label: '前进', desc: '前进到下一页',
    def: '', scope: 'desktop',
    run: (ctx) => window.history.forward(),
  },

  // ── 内置：屏蔽浏览器默认行为（不可解绑、不出现在设置页）──
  // ⚠️ 这几个原来是 desktop/index.js 里一段独立的 keydown 监听，
  //    它 preventDefault 掉 F5/Ctrl+R/Ctrl+P/Ctrl+U/F12。
  //    那份实现的问题：**和快捷键系统的先后完全取决于监听器注册顺序**，
  //    是个隐式依赖 —— 用户把 Ctrl+R 绑成别的动作时，行为会变得不可预测。
  //    收进注册表后优先级是**显式写在表里**的（见 manager.js 的 PHASES），
  //    而且用户在设置页能看见「这个键被占用了」。
  {
    id: 'sys.blockReload',
    group: '内置', label: '屏蔽刷新', desc: '应用里屏蔽 F5 / Ctrl+R',
    def: 'F5', scope: 'desktop', internal: true,
    // 同一动作绑两个键，用数组
    also: ['Ctrl+R'],
    run: () => {},
  },
  {
    id: 'sys.blockPrint',
    group: '内置', label: '屏蔽打印', desc: '屏蔽 Ctrl+P',
    def: 'Ctrl+P', scope: 'desktop', internal: true,
    run: () => {},
  },
  {
    id: 'sys.blockSource',
    group: '内置', label: '屏蔽查看源码', desc: '屏蔽 Ctrl+U',
    def: 'Ctrl+U', scope: 'desktop', internal: true,
    run: () => {},
  },
  {
    id: 'sys.blockDevtools',
    group: '内置', label: '屏蔽开发者工具', desc: '屏蔽 F12 / Ctrl+Shift+I',
    def: 'F12', scope: 'desktop', internal: true,
    also: ['Ctrl+Shift+I'],
    run: () => {},
  },
]

/** 当前平台可用的动作（网页端过滤掉窗口类与内置屏蔽类） */
export function availableActions() {
  const desktop = isDesktop
  return SHORTCUT_ACTIONS.filter((a) => a.scope === 'all' || desktop)
}

/** 设置页要展示的（排掉 internal） */
export function userFacingActions() {
  return availableActions().filter((a) => !a.internal)
}

export function actionById(id) {
  return SHORTCUT_ACTIONS.find((a) => a.id === id) || null
}

/** 默认绑定表 { actionId: combo }，含 also 里的额外键（用同 id + '#n' 后缀区分） */
export function defaultBindings() {
  const out = {}
  for (const a of availableActions()) {
    if (a.def) out[a.id] = a.def
    if (Array.isArray(a.also)) {
      a.also.forEach((c, i) => { out[`${a.id}#${i + 1}`] = c })
    }
  }
  return out
}
