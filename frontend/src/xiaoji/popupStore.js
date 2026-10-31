import { reactive } from 'vue'

/**
 * 小基小窗的全局状态（2026-10-30）。
 *
 * 为什么用全局 reactive 而不是 Pinia：
 *   它只有一个面板、生命周期跟 App 一样长；Popover 需要从任意页面/拖拽/桌宠
 *   唤起，跨组件传 props 会把每个页面都污染一遍。一个模块级 reactive 最轻。
 */
export const popupState = reactive({
  open: false,
  mode: 'upload',      // upload | chat | practice
  file: null,
  jobId: '',
  autoStart: false,
})

export function openXiaojiPopup(payload = {}) {
  if (payload.file) popupState.file = payload.file
  if (payload.mode) popupState.mode = payload.mode
  if (payload.jobId) popupState.jobId = payload.jobId
  popupState.autoStart = !!payload.autoStart
  popupState.open = true
}

export function closeXiaojiPopup() {
  popupState.open = false
  popupState.file = null
  popupState.jobId = ''
  popupState.autoStart = false
}
