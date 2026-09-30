/**
 * 快捷键分发器 —— 全站**只挂一个** keydown 监听。
 *
 * ## 为什么要有这一层
 *
 * 原来键盘事件散在三处，各自的先后**取决于监听器注册顺序**：
 *   · `desktop/index.js` 里一段监听，preventDefault 掉 F5/Ctrl+R/Ctrl+P/Ctrl+U/F12
 *   · `GlobalSearch.vue` 里一段监听，处理 Ctrl+K
 *   · 各组件自己的 `@keyup.enter`
 * 注册顺序一变行为就变，而且没人能一眼看出「Ctrl+R 到底归谁」。
 *
 * 收进一个分发器之后，优先级是**写在代码里的常量**，不是运行时的偶然。
 *
 * ## 优先级（自上而下，命中即止）
 *
 *   ① 输入态保护 —— 焦点在输入框时放行一切无修饰键的按键（否则打字就被吃）
 *   ② 输入态 + Escape —— 允许，用于关闭面板
 *   ③ 内置屏蔽（internal）—— preventDefault 后什么都不做
 *   ④ 用户绑定
 *   ⑤ 默认绑定
 *
 * ⚠️ ②③ 的顺序是刻意的：**屏蔽浏览器行为要优先于输入态判断**。
 *    否则在输入框里按 F5 会走「输入态放行」那条路 → 页面被刷新。
 */
import { availableActions, actionById } from './registry'
import { matches } from './combo'
import { shortcutState } from './store'

let installed = false
let ctxRef = null

const EDITABLE = 'input, textarea, select, [contenteditable="true"]'

function isEditable(target) {
  if (!target) return false
  if (target.isContentEditable) return true
  try {
    return !!target.closest?.(EDITABLE)
  } catch {
    return false
  }
}

/** 在「用户绑定 + 默认绑定」里找命中的动作。用户绑定优先。 */
function findHit(e) {
  const acts = availableActions()

  // 用户改过的先看 —— 否则用户把 Ctrl+K 改掉之后，默认那条还会抢走
  for (const a of acts) {
    const cur = shortcutState.bindings[a.id]
    if (cur && matches(e, cur)) return a
    // 同一动作的额外键（#1/#2…）
    if (Array.isArray(a.also)) {
      for (let i = 0; i < a.also.length; i++) {
        const extra = shortcutState.bindings[`${a.id}#${i + 1}`]
        if (extra && matches(e, extra)) return a
      }
    }
  }

  // 再看内置屏蔽/默认键（这些通常不在 bindings 里，或已被用户清空）
  for (const a of acts) {
    if (a.def && matches(e, a.def) && !(a.id in shortcutState.bindings)) return a
    if (Array.isArray(a.also)) {
      for (let i = 0; i < a.also.length; i++) {
        const key = `${a.id}#${i + 1}`
        if (!(key in shortcutState.bindings) && matches(e, a.also[i])) return a
      }
    }
  }
  return null
}

function onKeydown(e) {
  const edit = isEditable(e.target)

  // ① 输入态 + 无修饰键 → 放行，交给输入框
  //    （带修饰键的组合仍然要处理：Ctrl+K 打开搜索时用户很可能正在打字）
  if (edit && e.key !== 'Escape' && !e.ctrlKey && !e.altKey && !e.metaKey) return

  const action = findHit(e)
  if (!action) return

  // ② 内置屏蔽：吃掉事件、什么都不做
  if (action.internal) {
    e.preventDefault()
    e.stopPropagation()
    return
  }

  // ③ 输入态下的 Escape 之外仍有动作命中时，也要拦掉默认行为
  e.preventDefault()

  try {
    action.run?.(ctxRef)
  } catch (err) {
    // 快捷键执行失败不能让整个键盘处理挂掉
    console.error(`[shortcuts] 动作 ${action.id} 执行失败:`, err)
  }
}

/**
 * 装载分发器。**整个应用只调一次**（main.js）。
 *
 * @param {object} ctx 动作执行体需要的上下文
 *   { router, nav, toggleTheme, desktop }
 */
export function installShortcuts(ctx) {
  if (installed) return
  installed = true
  ctxRef = ctx
  // 用捕获阶段：抢在组件自己的 @keyup 之前，
  // 但要晚于浏览器的默认行为处理不了的场景 —— 捕获阶段就足够早。
  window.addEventListener('keydown', onKeydown, true)
  console.log('[shortcuts] 已装载，当前绑定数:', Object.keys(shortcutState.bindings).length)
}

export function uninstallShortcuts() {
  if (!installed) return
  installed = false
  window.removeEventListener('keydown', onKeydown, true)
}
