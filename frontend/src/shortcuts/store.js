/**
 * 快捷键绑定的状态与持久化。
 *
 * ## 存储策略（用户定的：**跟随账号**）
 *
 * 两层，各司其职：
 *   · **localStorage** —— 缓存。首屏立刻可用，不用等账号资料回来才开始响应按键；
 *     未登录时它就是唯一来源。
 *   · **账号（user_shortcuts 表）** —— 权威。登录后拉取、改动后回写，
 *     换电脑也在。表结构照 `user_theme_settings` 的先例（user_id 主键 + JSONB）。
 *
 * 合并规则：**账号里有的以账号为准**；账号里没有的保留本地那份。
 * 这样「没登录时改过、然后登录」不会把本地改动吞掉，
 * 而账号上已有的绑定也不会被本地的旧缓存覆盖。
 */
import { reactive } from 'vue'

import request from '@/utils/request'
import { availableActions, defaultBindings, actionById } from './registry'
import { parseCombo, formatCombo } from './combo'

const LS_KEY = 'jizhi-shortcuts'

export const shortcutState = reactive({
  /** { actionId: combo }，空串表示解绑 */
  bindings: {},
  /** 是否已经从任一来源装载过 */
  loaded: false,
  /** 正在同步账号 */
  syncing: false,
})

// ==================== 本地缓存 ====================

function readLocal() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    // 存坏了就当没有，绝不让它崩掉整个应用的启动
    return null
  }
}

function writeLocal(bindings) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(bindings))
  } catch {
    // 隐私模式/配额满 —— 忽略，账号那边仍然是权威
  }
}

// ==================== 装载 ====================

/** 首屏同步调用：先把本地那份装上，立刻能响应按键 */
export function loadLocalBindings() {
  const local = readLocal()
  shortcutState.bindings = { ...defaultBindings(), ...(local || {}) }
  shortcutState.loaded = true
}

/**
 * 登录后调用：拉账号上的绑定并合并进来。
 * 账号里没有的，保留本地 —— 并把本地推上去，让另一台设备也能拿到。
 */
export async function syncFromAccount(userId) {
  if (!userId) return
  shortcutState.syncing = true
  try {
    const res = await request.get(`/auth/shortcuts/${userId}`).then(r => r.data)
    const remote = (res && res.bindings) || {}
    const merged = { ...defaultBindings(), ...shortcutState.bindings, ...remote }
    shortcutState.bindings = merged
    writeLocal(merged)

    // 账号是空的（第一次用）→ 把当前这份推上去，省得用户在第二台设备上重配一遍
    if (Object.keys(remote).length === 0 && Object.keys(shortcutState.bindings).length) {
      await pushToAccount(userId).catch(() => {})
    }
  } catch (e) {
    // 拉不到就继续用本地那份 —— 快捷键不该因为网络问题失效
    console.warn('[shortcuts] 拉取账号绑定失败，沿用本地:', e?.message || e)
  } finally {
    shortcutState.syncing = false
  }
}

async function pushToAccount(userId) {
  await request.put('/auth/shortcuts', {
    user_id: userId,
    bindings: { ...shortcutState.bindings },
  })
}

/** 退出登录：把账号那份清掉、回到默认，避免下一个登录的人看到上一个人的绑定 */
export function resetToLocalOnly() {
  const local = readLocal()
  shortcutState.bindings = { ...defaultBindings(), ...(local || {}) }
}

// ==================== 改动 ====================

/**
 * 改一个绑定。
 *
 * @returns {{ok: true} | {ok: false, reason: string, conflictWith?: object}}
 *   **冲突不静默覆盖** —— 明确告诉调用方撞了哪个动作，由 UI 决定怎么提示。
 */
export function setBinding(actionId, combo, { userId = '' } = {}) {
  const conflict = findConflict(combo, actionId)
  if (conflict) {
    return {
      ok: false,
      reason: 'conflict',
      conflictWith: { id: conflict.id, label: conflict.label },
    }
  }
  shortcutState.bindings = { ...shortcutState.bindings, [actionId]: combo }
  writeLocal(shortcutState.bindings)
  if (userId) pushToAccount(userId).catch((e) => console.warn('[shortcuts] 同步失败:', e))
  return { ok: true }
}

export function resetOne(actionId, { userId = '' } = {}) {
  const def = actionById(actionId)?.def || ''
  return setBinding(actionId, def, { userId })
}

export function resetAll({ userId = '' } = {}) {
  shortcutState.bindings = defaultBindings()
  writeLocal(shortcutState.bindings)
  if (userId) pushToAccount(userId).catch((e) => console.warn('[shortcuts] 同步失败:', e))
}

// ==================== 查询 ====================

/**
 * 这个组合键是否已被**别的**动作占用。
 *
 * 比较用规范化后的形式，避免 `Ctrl+K` 与 `ctrl+k` 被当成两个键。
 * `#n` 后缀是同一动作的额外键（如「屏蔽刷新」同时占 F5 和 Ctrl+R），
 * 冲突提示里要能认出它属于哪个动作。
 */
export function findConflict(combo, exceptActionId = '') {
  if (!combo) return null
  const norm = (c) => {
    const { mods, key } = parseCombo(c)
    return [...mods].sort().join('+') + '|' + key.toUpperCase()
  }
  const target = norm(combo)
  for (const [id, c] of Object.entries(shortcutState.bindings)) {
    if (!c) continue
    if (id === exceptActionId || id.split('#')[0] === exceptActionId) continue
    if (norm(c) === target) {
      const base = id.split('#')[0]
      const a = actionById(base)
      return a ? { id: base, label: a.label, internal: !!a.internal } : null
    }
  }
  return null
}

/** 设置页展示用：动作 + 当前键 + 是否被改过 */
export function bindingsForDisplay() {
  return availableActions()
    .filter((a) => !a.internal)
    .map((a) => ({
      id: a.id,
      group: a.group,
      label: a.label,
      desc: a.desc,
      combo: shortcutState.bindings[a.id] ?? a.def ?? '',
      def: a.def || '',
      changed: (shortcutState.bindings[a.id] ?? a.def ?? '') !== (a.def || ''),
    }))
}

export { formatCombo }
