import request from '@/utils/request'

export function getTaskProgress(userId) {
  return request.get(`/career/task-progress/${userId}`)
    .then(res => res.data)
}

export function getUserStats(userId) {
  return request.get(`/career/stats/${userId}`)
    .then(res => res.data)
}

export function updateStats(data) {
  return request.post('/career/stats/update', data)
    .then(res => res.data)
}

export function recordAction(userId, actionType, metadata = {}) {
  return request.post('/career/actions/record', {
    user_id: userId,
    action_type: actionType,
    metadata
  }).then(res => res.data)
}

export function getActionStats(userId) {
  return request.get(`/career/actions/stats/${userId}`)
    .then(res => res.data)
}