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

export function createRun(payload, userId) {
  return request.post('/agents/runs', payload, { params: { user_id: userId } }).then(res => res.data)
}

export function getRun(runId, userId) {
  return request.get(`/agents/runs/${runId}`, { params: { user_id: userId } }).then(res => res.data)
}

export function listRuns(userId, limit = 30) {
  return request.get('/agents/runs', { params: { user_id: userId, limit } }).then(res => res.data)
}

export function cancelRun(runId, userId) {
  return request.post(`/agents/runs/${runId}/cancel`, null, { params: { user_id: userId } }).then(res => res.data)
}

export function getRunMetrics(userId, days = 30) {
  return request.get('/agents/metrics', { params: { user_id: userId, days } }).then(res => res.data)
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
