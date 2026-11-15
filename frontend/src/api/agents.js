import request from '@/utils/request'

// ============================================================
// 多智能体编排（2026-10-30）
// 后端：backend/routers/agents.py
// ============================================================

export function getWorkflows() {
  return request.get('/agents/workflows').then(res => res.data)
}

export function getAgentDefs() {
  return request.get('/agents/defs').then(res => res.data)
}

// 知识库定义 + 各知识源条目数（2026-11-12）
export function getKnowledge(userId) {
  return request.get('/agents/knowledge', { params: { user_id: userId } }).then(res => res.data)
}

// 跨知识源检索（题库 / 上传资料 / 学情 / 长期记忆）
export function searchKnowledge(userId, q, sources = '', limit = 4) {
  return request.get('/agents/knowledge/search', {
    params: { user_id: userId, q, sources, limit },
  }).then(res => res.data)
}

// 策略台账：quick / team 两个臂的历史结果与当前分数（2026-11-13）
export function getPolicy(userId) {
  return request.get('/agents/policy', { params: { user_id: userId } }).then(res => res.data)
}

export function createRun(payload, userId) {
  return request.post('/agents/runs', payload, { params: { user_id: userId } }).then(res => res.data)
}

export function getRun(runId, userId) {
  return request.get(`/agents/runs/${runId}`, { params: { user_id: userId } }).then(res => res.data)
}

export function listRuns(userId, limit = 30, opts = {}) {
  const params = { user_id: userId, limit }
  if (opts.active) params.active = true
  if (opts.workflowKey) params.workflow_key = opts.workflowKey
  return request.get('/agents/runs', { params }).then(res => res.data)
}

export function cancelRun(runId, userId) {
  return request.post(`/agents/runs/${runId}/cancel`, null, { params: { user_id: userId } }).then(res => res.data)
}

export function pauseRun(runId, userId) {
  return request.post(`/agents/runs/${runId}/pause`, null, { params: { user_id: userId } }).then(res => res.data)
}

export function resumeRun(runId, userId) {
  return request.post(`/agents/runs/${runId}/resume`, null, { params: { user_id: userId } }).then(res => res.data)
}

export function retryRun(runId, userId) {
  return request.post(`/agents/runs/${runId}/retry`, null, { params: { user_id: userId } }).then(res => res.data)
}

export function deleteRun(runId, userId) {
  return request.delete(`/agents/runs/${runId}`, { params: { user_id: userId } }).then(res => res.data)
}

export function reorderRuns(ids, userId) {
  return request.post('/agents/runs/reorder', { ids }, { params: { user_id: userId } }).then(res => res.data)
}

export function getRunMetrics(userId, days = 30) {
  return request.get('/agents/metrics', { params: { user_id: userId, days } }).then(res => res.data)
}

// 调参圆桌（2026-11-11）：后端复用 tuning_debate 工作流
export function startDebate(userId, payload = {}) {
  return request.post('/agent-center/debate/run', payload,
    { params: { user_id: userId } }).then(res => res.data)
}

// ============================================================
// 分层记忆 M3/M4（2026-10-30）
// ============================================================

export function getMemory(userId, kind = '') {
  return request.get('/agents/memory', { params: { user_id: userId, kind } }).then(res => res.data)
}

export function postPreference(userId, dimension, value, source = 'explicit') {
  return request.post('/agents/memory/preference', { dimension, value, source },
    { params: { user_id: userId } }).then(res => res.data)
}

export function deleteMemory(userId, memoryId) {
  return request.delete(`/agents/memory/${memoryId}`,
    { params: { user_id: userId } }).then(res => res.data)
}

// 页面驻扎小基：总结当前页（2026-10-30）
export function summarizePage(userId, payload) {
  return request.post('/agents/page-summary', payload,
    { params: { user_id: userId } }).then(res => res.data)
}

// 页面驻扎小基：截图解析（系统截屏 / 粘贴图片）
// ⚠️ 与上传出题不同：不落库、不写聊天记录，只做一次视觉模型调用。
export function analyzeImage(userId, file, prompt = '') {
  const form = new FormData()
  form.append('file', file)
  if (prompt) form.append('prompt', prompt)
  return request.post('/agents/image-analyze', form, {
    params: { user_id: userId },
    timeout: 120000,
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(res => res.data)
}
