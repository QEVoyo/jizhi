/**
 * 桌面版右键菜单的**扩展点**（2026-10-01）。
 *
 * ## 为什么要有这一层
 *
 * 通用菜单（返回 / 前进 / 刷新 / 复制 / 全选）哪个页面都一样 —— 那是「壳」的能力。
 * 但好的桌面应用右键是**贴着内容**的：视频卡片上给「播放 / 收藏 / 分享」，
 * 题目上给「复制题干」，评论上给「回复 / 举报」。**那才是用户右键的理由。**
 *
 * 这一层只做一件事：让页面能往菜单里**贡献自己的项**，而不用去碰菜单组件。
 *
 * ## 用法
 *
 * 在页面组件的 `<script setup>` 顶层调用一次（不是 onMounted 里）：
 *
 * ```js
 * registerCtxMenu('.vs-card', (card) => {
 *   const v = findVideo(card.dataset.videoId)
 *   if (!v) return []
 *   return [{ icon: '▶️', label: '播放', run: () => open(v) }]
 * })
 * ```
 *
 * - `card` 是**命中的那个元素**（不是右键的原始 target）—— 用 `closest` 找到的，
 *   所以卡片里点哪都算。
 * - 返回**空数组** = 这次不贡献（菜单照常显示通用项），不要为了「占位」返回空项。
 * - 贡献的项会出现在通用项**上面**，并自动补一条分隔线。
 *
 * ## 两个防呆
 *
 * - provider 抛错会被吞掉并打日志：一个页面的菜单坏了，不该让整个右键失效。
 * - 选择器写错（非法 CSS）也只会跳过那一条，不会炸。
 */
const providers = new Map()   // selector -> build

// 用 Map 而不是数组：HMR 重复注册同一个选择器时**覆盖**而不是叠加，
// 否则开发时改几次代码，菜单里就会出现几份重复项。
export function registerCtxMenu(selector, build) {
  if (!selector || typeof build !== 'function') return
  providers.set(selector, build)
}

/**
 * 收集落点上所有命中的 provider 贡献的项。
 * @param {Element} el   右键的原始 target
 * @param {string}  selection  当前选中的文字（provider 可能想用，比如「搜索选中的词」）
 * @returns {Array} 菜单项数组（每段末尾带一条 sep）
 */
export function collectCtxItems(el, selection = '') {
  const out = []
  if (!el || typeof el.closest !== 'function') return out
  for (const [selector, build] of providers) {
    let hit = null
    try {
      hit = el.closest(selector)
    } catch {
      continue   // 选择器非法，跳过这一条就好
    }
    if (!hit) continue
    try {
      const items = build(hit, selection) || []
      if (items.length) out.push(...items, { sep: true })
    } catch (e) {
      console.warn('[ctx] 菜单 provider 失败:', selector, e)
    }
  }
  return out
}

// ==================== 共用动作 ====================

/**
 * 复制到剪贴板。返回是否成功 —— 失败要能看见，不静默。
 *
 * 放在这里而不是菜单组件里：provider 也要复制（复制题干、复制分享链接），
 * 应该共用同一套「权限被拒 → 退回 execCommand」的兜底。
 */
export async function copyText(text, what = '内容') {
  if (!text) return false
  const { ElMessage } = await import('element-plus')   // 动态引入，别把整个组件库拖进首屏
  let ok = false
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
      ok = true
    }
  } catch { /* 落到下面的兜底 */ }
  if (!ok) {
    // 兜底：WebView2 在权限被拒 / 非安全上下文时上面那条会抛。
    // execCommand 虽然已废弃，但在 webview 里仍是最后一道能用的路。
    try {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.setAttribute('readonly', '')
      ta.style.cssText = 'position:fixed;top:-1000px;opacity:0'
      document.body.appendChild(ta)
      ta.select()
      ok = document.execCommand('copy')
      document.body.removeChild(ta)
    } catch { ok = false }
  }
  if (ok) ElMessage.success(`已复制${what}`)
  else ElMessage.warning('复制失败，可以试试 Ctrl+C')
  return ok
}
