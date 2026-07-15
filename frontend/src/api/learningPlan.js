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

export function updateTaskStatus(taskId, status) {
  return request.put('/learning-plan/task/status', { task_id: taskId, status }).then(res => res.data)
}

export function deletePlan(planId) {
  return request.delete(`/learning-plan/delete/${planId}`).then(res => res.data)
}