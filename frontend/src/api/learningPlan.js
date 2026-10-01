import request from '@/utils/request'

export function createPlan(data) {
  return request.post('/learning-plan/create', data).then(res => res.data)
}

export function getPlans(userId) {
  return request.get(`/learning-plan/list?user_id=${userId}`).then(res => res.data)
}

export function getPlanDetail(planId) {
  return request.get(`/learning-plan/detail/${planId}`).then(res => res.data)
}

export function updateTaskStatus(data) {
  return request.put('/learning-plan/task/status', data).then(res => res.data)
}

/**
 * 回写一道题的作答结果（2026-10-01）。
 *
 * 自定义计划以前**做完什么也不记** —— 只改 status 字段，不记对错也不记次数，
 * 所以「当日正确率」根本无从算起。
 *
 * 语义（用户定调）：`attempts` / `last_correct` 每次更新，
 * `best_correct` **只从 false 变 true、永不回退** —— 重做做错了不该把成绩拉下来。
 */
export function recordTaskAnswer(data) {
  return request.put('/learning-plan/task/answer', data).then(res => res.data)
}

export function deletePlan(planId) {
  return request.delete(`/learning-plan/delete/${planId}`).then(res => res.data)
}