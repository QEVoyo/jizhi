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

// 立即执行磨合规则评估（返回实际调整列表 + 调参日记）
export function postRunTuning(userId) {
  return request.post('/agent-center/tuning/run', null, { params: { user_id: userId } }).then(res => res.data)
}

// ============================================================
// 调参日记（agent_decisions，2026-10-30）
// ============================================================

// 日记列表：诊断 / 证据 / 改了什么 / 否决了什么 / 7 天复盘
export function getDecisions(userId, days = 30) {
  return request.get('/agent-center/decisions', { params: { user_id: userId, days } }).then(res => res.data)
}

export function getDecision(decisionId, userId) {
  return request.get(`/agent-center/decisions/${decisionId}`, { params: { user_id: userId } }).then(res => res.data)
}

// action: agree / disagree / lock（lock = 别再自动改这次涉及的参数）
export function postDecisionFeedback(decisionId, userId, action, note = '') {
  return request.post(`/agent-center/decisions/${decisionId}/feedback`, { action, note },
    { params: { user_id: userId } }).then(res => res.data)
}

// 回滚本次调整（恢复 old_value，并暂停这些参数的自动托管）
export function postDecisionRevert(decisionId, userId) {
  return request.post(`/agent-center/decisions/${decisionId}/revert`, null,
    { params: { user_id: userId } }).then(res => res.data)
}

// 立即复盘：对比决策时与近 7 天指标，变差会自动回滚（2026-11-12）
export function postDecisionReview(decisionId, userId) {
  return request.post(`/agent-center/decisions/${decisionId}/review`, null,
    { params: { user_id: userId } }).then(res => res.data)
}
