/**
 * 小基事件总线（2026-11-11）
 *
 * 页面只负责说「这里发生了什么」，驻扎小基自己决定怎么反应。
 * 不依赖 Vue、不引 Element Plus，谁都可以 import，进首屏也只有几百字节。
 *
 * 用法：
 *   import { emitXiaoji } from '@/xiaoji/bus'
 *   emitXiaoji('answer:correct', { data: { question_type: 'choice' } })
 *
 * 订阅：
 *   const off = onXiaoji('answer:correct', detail => { ... })
 *   const offAll = onXiaoji('*', detail => { ... })   // 通配，调试/统一反应层用
 *   off(); offAll()
 *
 * 直控（任何页面都能让小基说一句/做个表情）：
 *   emitXiaoji('xiaoji:say', { text: '先歇会儿。', look: 'happy' })
 *   emitXiaoji('xiaoji:react', { look: 'thinking', ms: 1800 })
 */

/** 标准事件名。只是常量，不限制 emit 任意字符串。 */
export const XIAOJI_EVENT = {
  // 做题
  ANSWER_SUBMIT: 'answer:submit',
  ANSWER_CORRECT: 'answer:correct',
  ANSWER_WRONG: 'answer:wrong',
  // 生成 / 评估
  GENERATION_START: 'generation:start',
  GENERATION_DONE: 'generation:done',
  GENERATION_ERROR: 'generation:error',
  PLAN_GENERATE_START: 'plan:generate:start',
  PLAN_GENERATE_DONE: 'plan:generate:done',
  PLAN_GENERATE_ERROR: 'plan:generate:error',
  // 任务
  TASK_COMPLETE: 'task:complete',
  TASK_FAIL: 'task:fail',
  // 通用
  SAVE_SUCCESS: 'save:success',
  NETWORK_ERROR: 'network:error',
  ACHIEVEMENT_UNLOCK: 'achievement:unlock',
  // 直接控制
  SAY: 'xiaoji:say',
  REACT: 'xiaoji:react',
  // 订阅全部
  ANY: '*',
}

const listeners = new Map()

function setOf(type) {
  let set = listeners.get(type)
  if (!set) {
    set = new Set()
    listeners.set(type, set)
  }
  return set
}

/**
 * 订阅某类事件，返回取消订阅函数。
 * type 传 '*' 可收全部事件（用于统一反应层/调试）。
 */
export function onXiaoji(type, handler) {
  if (!type || typeof handler !== 'function') return () => {}
  setOf(type).add(handler)
  return () => offXiaoji(type, handler)
}

export function offXiaoji(type, handler) {
  const set = listeners.get(type)
  if (!set) return
  set.delete(handler)
  if (!set.size) listeners.delete(type)
}

/**
 * 发一个事件。payload 支持：
 *   { data, importance, once, text, look, ms }
 * 顶层 text/look/ms 是给 xiaoji:say / xiaoji:react 直控用的。
 */
export function emitXiaoji(type, payload = {}) {
  if (!type) return
  const detail = {
    type,
    page: typeof window !== 'undefined' ? window.location.pathname : '',
    at: Date.now(),
    importance: payload.importance || 'normal',
    once: !!payload.once,
    data: payload.data || {},
  }
  if (payload.text) detail.text = String(payload.text).slice(0, 80)
  if (payload.look) detail.look = payload.look
  if (payload.ms) detail.ms = payload.ms

  const direct = listeners.get(type)
  const all = listeners.get(XIAOJI_EVENT.ANY)
  for (const fn of [...(direct || []), ...(all || [])]) {
    try {
      fn(detail)
    } catch (e) {
      // 一个订阅者出错不能影响页面主流程
      console.error('[xiaoji bus]', type, e)
    }
  }
}

// 开发期方便在控制台手动触发：__xiaojiEmit('answer:correct')
if (typeof window !== 'undefined' && import.meta.env?.DEV) {
  window.__xiaojiEmit = emitXiaoji
}
