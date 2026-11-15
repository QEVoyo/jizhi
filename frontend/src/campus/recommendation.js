// 2D 校园的「小基先带你去哪」。
// 不新造推荐算法：优先用用户自己设的「我的路线」，其次用记忆流的上次锚点/下一步，
// 最后才回落到今日任务。
import { getLastAnchor, getMemoryFlow, getCustomRoute, nextCustomStep } from '@/utils/routeMemory'

function mapPath(path) {
  const p = String(path || '')
  if (!p) return null
  if (/resource-lib|set-detail|generate-from-mastery|video-square/.test(p)) return 'resource'
  if (/mastery-board|do-question|subject-plan|evaluation|wordbook/.test(p)) return 'weakness'
  if (/learning-plan|plan-|daily-learn|\/home/.test(p)) return 'today'
  return null
}

export function pickCampusHotspot(uid) {
  if (!uid) return { id: 'today', guest: true }

  const last = getLastAnchor(uid)
  const custom = getCustomRoute(uid)

  // 1) 用户自己设的固定路线优先
  if (custom && last) {
    const next = nextCustomStep(custom.steps, last.key)
    const mapped = next && mapPath(next.path)
    if (mapped) return { id: mapped, from: 'custom' }
  }

  // 2) 学习出来的记忆流：下一步 > 接着上次 > 上次页面
  if (last) {
    const flow = getMemoryFlow(uid, last.key, { currentPath: last.path })
    const next = flow.suggestions.find(s => s.type === 'next')
      || flow.suggestions.find(s => s.type === 'resume')
    const mapped = mapPath(next?.path) || mapPath(last.path)
    if (mapped) return { id: mapped, from: 'memory' }
  }

  return { id: 'today', guest: false }
}
