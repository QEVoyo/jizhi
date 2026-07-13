import request from '@/utils/request'

// 打卡
export function getCheckin(userId) {
  return request.get(`/tools/checkin/${userId}`)
    .then(res => res.data)
}

export function saveCheckin(userId, projects) {
  return request.post(`/tools/checkin/${userId}`, { projects })
    .then(res => res.data)
}

// 倒计时
export function getCountdown(userId) {
  return request.get(`/tools/countdown/${userId}`)
    .then(res => res.data)
}

export function saveCountdown(userId, events) {
  return request.post(`/tools/countdown/${userId}`, { events })
    .then(res => res.data)
}

// 计时器
export function getTimer(userId) {
  return request.get(`/tools/timer/${userId}`)
    .then(res => res.data)
}

export function saveTimer(userId, timers) {
  return request.post(`/tools/timer/${userId}`, { timers })
    .then(res => res.data)
}

// 学习日志
export function getLearningLogs(userId) {
  return request.get(`/tools/learning-logs/${userId}`)
    .then(res => res.data)
}

export function addLearningLog(userId, keyword, date) {
  return request.post(`/tools/learning-logs/${userId}`, { keyword, date })
    .then(res => res.data)
}

export function clearLearningLogs(userId) {
  return request.delete(`/tools/learning-logs/${userId}`)
    .then(res => res.data)
}

// 学情报告
export function getReport(userId) {
  return request.get(`/tools/report/${userId}`)
    .then(res => res.data)
}
export function deleteLearningLog(userId, logId) {
  return request.delete('/tools/learning-log', {
    params: { user_id: userId, log_id: logId }
  }).then(res => res.data)
}