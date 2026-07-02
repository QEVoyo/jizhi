import request from '@/utils/request'

// 生成题目
export function generateQuestion(data) {
  return request.post('/questions/generate', data)
    .then(res => res.data)
}

// 评估答案
export function evaluateAnswer(data) {
  return request.post('/questions/evaluate', data)
    .then(res => res.data)
}

// 获取掌握度
export function getMastery(userId) {
  return request.get(`/questions/mastery/${userId}`)
    .then(res => res.data)
}

// 错题本
export function getMistakes(userId) {
  return request.get(`/questions/mistakes/${userId}`)
    .then(res => res.data)
}

export function conquerMistake(questionId) {
  return request.post(`/questions/mistakes/conquer/${questionId}`)
    .then(res => res.data)
}

// 题集
export function getQuestionSets(userId) {
  return request.get(`/questions/set/list/${userId}`)
    .then(res => res.data)
}

export function createQuestionSet(userId, data) {
  return request.post(`/questions/set/create?user_id=${userId}`, data)
    .then(res => res.data)
}

export function deleteQuestionSet(setId) {
  return request.delete(`/questions/set/${setId}`)
    .then(res => res.data)
}

export function getQuestionSetDetail(setId) {
  return request.get(`/questions/set/${setId}`)
    .then(res => res.data)
}

export function addQuestionToSet(setId, questionId) {
  return request.post(`/questions/set/${setId}/add/${questionId}`)
    .then(res => res.data)
}

export function removeQuestionFromSet(setId, questionId) {
  return request.post(`/questions/set/${setId}/remove/${questionId}`)
    .then(res => res.data)
}

// 生成历史
export function getGenerationHistory(userId) {
  return request.get(`/questions/history/${userId}`)
    .then(res => res.data)
}

export function saveGenerationHistory(data) {
  return request.post('/questions/history/save', data)
    .then(res => res.data)
}

// 获取题目详情
export function getQuestionDetail(questionId) {
  return request.get(`/questions/${questionId}`)
    .then(res => res.data)
}