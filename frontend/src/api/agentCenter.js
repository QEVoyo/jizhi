import request from '@/utils/request'

// ============================================================
// 智能体中心 — 聚合分析 + 参数/磨合（真实数据，替代 mock）
// 数据来源见 agent_center_design.md；后端 routers/agent_center.py
// ============================================================

// 总览：KPI + 协作闭环 + 协同增益 + 路由转化 + 智能体卡片数据
export function getOverview(userId, days = 30) {
  return request.get('/agent-center/overview', { params: { user_id: userId, days } }).then(res => res.data)
}

// 单智能体详情：主指标趋势 + 特点面板 + 触点计数 + 统计格
export function getAgentDetail(agentKey, userId, days = 30) {
  return request.get(`/agent-center/agents/${agentKey}`, { params: { user_id: userId, days } }).then(res => res.data)
}

// 参数读写（agent_prefs）
export function getAgentPrefs(agentKey, userId) {
  return request.get(`/agent-center/agents/${agentKey}/prefs`, { params: { user_id: userId } }).then(res => res.data)
}

export function saveAgentPrefs(agentKey, userId, prefs) {
  return request.put(`/agent-center/agents/${agentKey}/prefs`, prefs, { params: { user_id: userId } }).then(res => res.data)
}

// 磨合记录（agent_tuning_log）
export function getAgentTuning(agentKey, userId) {
  return request.get(`/agent-center/agents/${agentKey}/tuning`, { params: { user_id: userId } }).then(res => res.data)
}

export function postAgentTuning(agentKey, userId, item) {
  return request.post(`/agent-center/agents/${agentKey}/tuning`, item, { params: { user_id: userId } }).then(res => res.data)
}

// 立即执行磨合规则评估（返回实际调整列表）
export function postRunTuning(userId) {
  return request.post('/agent-center/tuning/run', null, { params: { user_id: userId } }).then(res => res.data)
}
