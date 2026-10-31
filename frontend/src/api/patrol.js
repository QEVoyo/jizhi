import request from '@/utils/request'

// ============================================================
// 主动巡检 Self-Loop（2026-10-30）
// 后端：backend/routers/patrol.py
// ============================================================

export function getPatrolInbox(userId) {
  return request.get('/patrol/inbox', { params: { user_id: userId } }).then(res => res.data)
}

export function actPatrolEvent(eventId, userId) {
  return request.post(`/patrol/events/${eventId}/act`, null,
    { params: { user_id: userId } }).then(res => res.data)
}

export function dismissPatrolEvent(eventId, userId) {
  return request.post(`/patrol/events/${eventId}/dismiss`, null,
    { params: { user_id: userId } }).then(res => res.data)
}

export function snoozePatrolEvent(eventId, userId, hours = 4) {
  return request.post(`/patrol/events/${eventId}/snooze`, { hours },
    { params: { user_id: userId } }).then(res => res.data)
}

export function getPatrolRules(userId) {
  return request.get('/patrol/rules', { params: { user_id: userId } }).then(res => res.data)
}

export function getPatrolMetrics(userId, days = 30) {
  return request.get('/patrol/metrics', { params: { user_id: userId, days } }).then(res => res.data)
}
