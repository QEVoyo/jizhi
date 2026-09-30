/**
 * 组合键的规范化 / 格式化 / 匹配。
 *
 * 单独成文件是因为**边界情况比看上去多**，散在业务里必然写歪：
 *   · `e.key` 在按住 Shift 时会变成大写（`K`），不统一就永远匹配不上
 *   · 空格键的 `e.key` 是 `' '`，不是 `'Space'`
 *   · Mac 的 Cmd 与 Windows 的 Ctrl 要归一到同一个修饰键，否则配置没法跨平台跟随账号
 *   · `+` 本身是分隔符，绑到 `+` 键时必须转义，否则字符串会被拆错
 */

/** 允许的修饰键（顺序固定，保证同一组合只有一种写法） */
const MODS = ['Ctrl', 'Alt', 'Shift', 'Meta']

/** 把 `e.key` 归一成稳定的名字 */
export function normalizeKey(key) {
  if (!key) return ''
  if (key === ' ') return 'Space'
  if (key === '+') return 'Plus'
  if (key === '-') return 'Minus'
  if (key === ',') return 'Comma'
  if (key === '.') return 'Period'
  if (key === '/') return 'Slash'
  if (key === '\\') return 'Backslash'
  if (key === ';') return 'Semicolon'
  if (key === "'") return 'Quote'
  if (key === '[') return 'BracketLeft'
  if (key === ']') return 'BracketRight'
  if (key === '`') return 'Backquote'
  if (key === 'Escape') return 'Esc'
  if (key === 'ArrowUp') return 'Up'
  if (key === 'ArrowDown') return 'Down'
  if (key === 'ArrowLeft') return 'Left'
  if (key === 'ArrowRight') return 'Right'
  // 字母统一成大写：按住 Shift 时 e.key 是大写，不统一就会「绑了 K 却按 Shift+K 不触发」
  if (key.length === 1) return key.toUpperCase()
  return key
}

/**
 * 从键盘事件生成组合键字符串，如 `Ctrl+Shift+K`。
 *
 * ⚠️ `Meta`（Mac 的 Cmd / Windows 的 Win 键）在桌面端会和系统快捷键冲突，
 * 这里**不做映射**——用户按什么就记什么，但界面上会提示 Win 键被系统占用。
 */
export function comboFromEvent(e) {
  const parts = []
  if (e.ctrlKey) parts.push('Ctrl')
  if (e.altKey) parts.push('Alt')
  if (e.shiftKey) parts.push('Shift')
  if (e.metaKey) parts.push('Meta')

  const key = normalizeKey(e.key)
  // 只按了修饰键本身，不构成组合
  if (MODS.includes(key)) return ''

  // Shift 与「本身就是 Shift 出来的符号」会重复：
  // 按 Shift+K 得到 key='K'（已含 Shift 的语义），再加一个 Shift 就是多余的。
  // 但 Shift+1 得到 '!'，那是真的需要 Shift —— 所以只对字母/数字去重。
  if (parts.includes('Shift') && key.length === 1 && /[A-Z0-9]/.test(key)) {
    // 保留 Shift：这样 Ctrl+Shift+K 与 Ctrl+K 能区分开
  }

  parts.push(key)
  return parts.join('+')
}

/** 解析成结构化对象，便于比较与展示 */
export function parseCombo(combo) {
  if (!combo) return { mods: new Set(), key: '' }
  const parts = String(combo).split('+')
  const key = parts.pop() || ''
  const mods = new Set(parts.filter((p) => MODS.includes(p)))
  return { mods, key: key === 'Plus' ? '+' : key }
}

/** 判断一次按键是否命中某个绑定 */
export function matches(e, combo) {
  if (!combo) return false
  const { mods, key } = parseCombo(combo)
  const pressed = normalizeKey(e.key)
  const pressedKey = pressed === 'Plus' ? '+' : pressed

  // 修饰键必须**完全一致**：多按一个 Shift 就不该命中（否则 Ctrl+K 与 Ctrl+Shift+K 会互相误触）
  if (mods.has('Ctrl') !== !!e.ctrlKey) return false
  if (mods.has('Alt') !== !!e.altKey) return false
  if (mods.has('Shift') !== !!e.shiftKey) return false
  if (mods.has('Meta') !== !!e.metaKey) return false

  return key.toUpperCase() === pressedKey.toUpperCase()
}

/** 给人看的样子（Mac 上把 Ctrl 显示成 ⌘ 更符合直觉） */
export function formatCombo(combo) {
  if (!combo) return '未设置'
  const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform || '')
  return String(combo)
    .split('+')
    .map((p) => {
      if (isMac && p === 'Ctrl') return '⌘'
      if (isMac && p === 'Alt') return '⌥'
      if (isMac && p === 'Shift') return '⇧'
      if (p === 'Esc') return 'Esc'
      return p
    })
    .join(isMac ? '' : ' + ')
}

/** 这个组合是否只是「一个裸键」（没有修饰键）—— 裸键做全局快捷键太危险，要提醒 */
export function isBareKey(combo) {
  const { mods, key } = parseCombo(combo)
  return mods.size === 0 && !!key && key !== 'Esc'
}
