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

/** 领取单个学程任务（种子 / 每日 / 长期） */
export function claimCareerTask(userId, taskId, taskType) {
  return request.post('/career/task/claim', {
    user_id: userId,
    task_id: taskId,
    task_type: taskType,
  }).then(res => res.data)
}

/** 领取每日全部完成奖励 */
export function claimCareerBonus(userId) {
  return request.post('/career/bonus/claim', { user_id: userId }).then(res => res.data)
}