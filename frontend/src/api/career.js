import request from '@/utils/request'

// ============================================================
// 1. 用户统计
// ============================================================

export function getUserStats(userId) {
  return request.get(`/career/stats/${userId}`).then(res => res.data)
}

export function updateStats(data) {
  return request.post('/career/stats/update', data).then(res => res.data)
}


// ============================================================
// 2. 用户行为
// ============================================================

export function recordAction(userId, actionType, metadata = {}) {
  return request.post('/career/actions/record', {
    user_id: userId,
    action_type: actionType,
    metadata
  }).then(res => res.data)
}

// ============================================================
// 3. 任务进度
// ============================================================

export function getTaskProgress(userId) {
  if (!userId) {
    return Promise.resolve({ seed: [], daily: [], long: [], achievements: [] })
  }
  return request.get(`/career/task-progress/${userId}`).then(res => res.data)
}