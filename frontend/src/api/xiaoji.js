import request from '@/utils/request'

// ===== 小基配置 =====
export function getXiaojiConfig(userId) {
  return request.get(`/community/xiaoji/config/${userId}`).then(res => res.data)
}

export function updateXiaojiConfig(userId, data) {
  return request.put(`/community/xiaoji/config/${userId}`, data).then(res => res.data)
}

export function getVoiceList() {
  return request.get('/community/xiaoji/voice/list').then(res => res.data)
}

// ===== 语音合成（TTS） =====
export function textToSpeech(data) {
  return request.post('/community/xiaoji/tts', data).then(res => res.data)
}

// ===== 语音识别（ASR） =====
export function speechToText(data) {
  return request.post('/community/xiaoji/asr', data).then(res => res.data)
}

// ===== 小基聊天 =====
export function sendXiaojiMessage(data) {
  return request.post('/community/xiaoji/chat', data, {
    params: { user_id: data.user_id }
  }).then(res => res.data)
}

export function xiaojiVision(data) {
  return request.post('/community/xiaoji/vision', data, {
    params: { user_id: data.user_id }
  }).then(res => res.data)
}

// ===== 聊天记录（含搜索） =====
export function getXiaojiMessages(userId, search = '', limit = 50, offset = 0) {
  return request.get(`/community/xiaoji/messages/${userId}`, {
    params: { search, limit, offset }
  }).then(res => res.data)
}

export function deleteXiaojiMessage(messageId, userId) {
  return request.delete(`/community/xiaoji/message/${messageId}`, {
    params: { user_id: userId }
  }).then(res => res.data)
}

export function clearXiaojiMessages(userId) {
  return request.delete(`/community/xiaoji/messages/${userId}`).then(res => res.data)
}
// ===== 评价题目 =====
export function evaluateQuestion(userId, question) {
  return request.post('/community/xiaoji/evaluate-question',
    { question },
    { params: { user_id: userId } }
  ).then(res => res.data)
}

// ===== 评价题集 =====
export function evaluateSet(userId, setData, questions) {
  return request.post('/community/xiaoji/evaluate-set',
    { set: setData, questions },
    { params: { user_id: userId } }
  ).then(res => res.data)
}
export function evaluateQuestionStream(userId, question) {
  // 流式接口用 fetch 直接调用，不需要封装
  return `${import.meta.env.VITE_BACKEND_URL || 'https://api.jizhi-learn.com'}/community/xiaoji/evaluate-question-stream?user_id=${userId}`
}