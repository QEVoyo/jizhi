/**
 * 消息点注册表的**前端消费者**（2026-10-07）
 *
 * ⚠️ 这里**不重写配色公式** —— 颜色、组内序号、跳转都在后端算好，
 * 前端只从 `GET /messages/registry` 取。理由：配色只有一份实现，
 * 预览页（_devtools/message-center-preview.html）和线上才会长得一模一样。
 *
 * 加一个消息点 = 后端注册表加一行，**前端零改动**：Tab、图标、配色、角标归属、
 * 跳转全部由注册表推导。
 */
import { getRegistry } from '@/api/messages'

const CACHE_KEY = 'jz-message-registry'

let registry = null          // { groups: {...}, types: {...}, no_route_read, no_delete }
let loading = null

/** 兜底色：注册表还没到时的中性色，别让界面白块 */
export const FALLBACK_COLOR = { c1: 'hsl(215, 12%, 58%)', c2: 'hsl(220, 14%, 46%)' }

/** 启动时读本地缓存，界面立刻能渲染，随后再拉最新的 */
export function hydrateFromCache() {
  if (registry) return registry
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (raw) registry = JSON.parse(raw)
  } catch { /* 坏缓存就当没有 */ }
  return registry
}

export async function loadRegistry(force = false) {
  if (registry && !force) return registry
  if (loading) return loading
  loading = getRegistry()
    .then((data) => {
      if (data && data.types) {
        registry = data
        try { localStorage.setItem(CACHE_KEY, JSON.stringify(data)) } catch { /* 存不下就算了 */ }
      }
      return registry
    })
    .catch(() => registry || hydrateFromCache())
    .finally(() => { loading = null })
  return loading
}

export function getGroups() {
  const r = registry || hydrateFromCache()
  if (!r) return []
  return Object.entries(r.groups)
    .map(([key, meta]) => ({ key, ...meta }))
    .sort((a, b) => a.order - b.order)
}

export function typeMeta(type) {
  const r = registry || hydrateFromCache()
  return (r && r.types && r.types[type]) || null
}

/** 某条消息的渐变色两端。注册表没有就返回兜底色。 */
export function colorOf(type) {
  const meta = typeMeta(type)
  return meta ? { c1: meta.c1, c2: meta.c2 } : FALLBACK_COLOR
}

/** 某条消息属于哪个大类（角标按大类归集） */
export function groupOf(type) {
  const meta = typeMeta(type)
  return meta ? meta.group : 'system'
}

export function groupMeta(group) {
  const r = registry || hydrateFromCache()
  const g = r && r.groups && r.groups[group]
  return g || { label: group, color: FALLBACK_COLOR.c1, order: 99, switch: '' }
}

export function labelOf(type) {
  const meta = typeMeta(type)
  return meta ? meta.label : type
}

export function isTodo(type) {
  const meta = typeMeta(type)
  return !!(meta && meta.todo)
}

/**
 * 这条消息的详情用哪种**形态**渲染（2026-10-08）。
 *
 * ⚠️ **形态是由后端注册表算好的**（`notification_registry._shape_of`），
 * 前端只认名字、不做推导 —— 推导规则只有一份实现，加消息点仍然前端零改动。
 * 这里取不到就退回 `plain`（分段正文），绝不会白屏。
 *
 *   rec       学习推荐三合一（三块预览 + 去学习）
 *   summary   昨日总结（数字卡片 + 知识点标签 + 三段文字）
 *   actors    聚合型「N 人做了某事」（人物标签 + 聚合明细）
 *   todo      待办（要动手处理）
 *   notice    系统/账号类正式通知
 *   celebrate 学程成就 / 晋升
 *   plain     其余：分段正文
 */
export function shapeOf(type) {
  const meta = typeMeta(type)
  return (meta && meta.shape) || 'plain'
}

/** 大类 → FontAwesome 图标。用在详情与列表的方形图标上（比取标签首字好看）。 */
const GROUP_ICON = {
  chat: 'fa-comment',
  social: 'fa-heart',
  learning: 'fa-book-open',
  plan: 'fa-calendar-check',
  evaluation: 'fa-chart-line',
  career: 'fa-trophy',
  todo: 'fa-list-check',
  system: 'fa-shield-halved',
  admin: 'fa-user-shield',
}
export function iconOf(type) {
  return GROUP_ICON[groupOf(type)] || 'fa-bell'
}

/** 生成 CSS 变量，直接挂到卡片上：style="--c1:…;--c2:…" */
export function cssVars(type) {
  const { c1, c2 } = colorOf(type)
  return { '--c1': c1, '--c2': c2 }
}

/**
 * 从消息的 link 判断点击去哪（消息自带 link 优先，其次注册表缺省）。
 * 待办型用自己的处理页，不进详情。
 */
export function linkOf(message) {
  if (message && message.link) return message.link
  const meta = typeMeta(message && message.type)
  return (meta && meta.link) || ''
}

export default {
  loadRegistry, hydrateFromCache, getGroups, typeMeta, colorOf, groupOf,
  groupMeta, labelOf, isTodo, shapeOf, iconOf, cssVars, linkOf, FALLBACK_COLOR,
}
