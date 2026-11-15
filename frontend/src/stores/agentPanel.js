import { reactive } from 'vue'

/**
 * 全局「小队协作」面板状态（2026-11-11）
 *
 * 任何一个真实 run（团队出题 / 上传出题 / 调参圆桌）都能打开同一个协作视图。
 * 这里只存「看哪条 run、开没开」，数据由组件按 run_id 拉取。
 */
export const agentPanelState = reactive({
  open: false,
  runId: '',
  at: 0,
})

export function openAgentPanel(runId = '') {
  agentPanelState.runId = runId || ''
  agentPanelState.open = true
  agentPanelState.at = Date.now()
}

export function closeAgentPanel() {
  agentPanelState.open = false
}
