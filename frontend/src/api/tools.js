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

