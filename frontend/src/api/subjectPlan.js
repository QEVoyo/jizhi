import request from '@/utils/request'

// ===== 考纲 =====
export function listSyllabi(userId) {
  return request.get('/subject-plan/syllabi', { params: { user_id: userId } }).then(r => r.data)
}
export function getSyllabusDetail(syllabusId, userId) {
  return request.get(`/subject-plan/syllabi/${syllabusId}`, { params: { user_id: userId } }).then(r => r.data)
}

// ===== 诊断 =====
export function startDiagnosis(syllabusId) {
  return request.get(`/subject-plan/syllabi/${syllabusId}/diagnosis/start`).then(r => r.data)
}
export function submitDiagnosis(syllabusId, data) {
  return request.post(`/subject-plan/syllabi/${syllabusId}/diagnosis/submit`, data).then(r => r.data)
}

// ===== 题库（考纲下） =====
export function getQuestions(syllabusId, params) {
  return request.get(`/subject-plan/syllabi/${syllabusId}/questions`, { params }).then(r => r.data)
}

// ===== 计划 =====
export function getPlanDetail(planId, userId) {
  return request.get(`/subject-plan/plans/${planId}`, { params: { user_id: userId } }).then(r => r.data)
}
export function updatePlan(planId, userId, data) {
  return request.put(`/subject-plan/plans/${planId}`, data, { params: { user_id: userId } }).then(r => r.data)
}
export function deletePlan(planId, userId) {
  return request.delete(`/subject-plan/plans/${planId}`, { params: { user_id: userId } }).then(r => r.data)
}

// ===== 每日任务 =====
export function getAllTasks(planId, userId) {
  return request.get(`/subject-plan/plans/${planId}/tasks`, { params: { user_id: userId } }).then(r => r.data)
}
export function getTodayTasks(planId, userId) {
  return request.get(`/subject-plan/plans/${planId}/tasks/today`, { params: { user_id: userId } }).then(r => r.data)
}
export function getQuestionStats(planId, userId) {
  return request.get(`/subject-plan/plans/${planId}/questions-count`, { params: { user_id: userId } }).then(r => r.data)
}

// ===== 做题 =====
export function submitAnswer(planId, data) {
  return request.post(`/subject-plan/plans/${planId}/submit`, data).then(r => r.data)
}

// ===== 题目作答状态 =====
export function getQuestionStates(planId, userId) {
  return request.get(`/subject-plan/plans/${planId}/question-states`, { params: { user_id: userId } }).then(r => r.data)
}

// ===== 掌握度 =====
export function getMastery(planId, userId) {
  return request.get(`/subject-plan/plans/${planId}/mastery`, { params: { user_id: userId } }).then(r => r.data)
}

// ===== 错题 =====
export function getMistakes(planId, userId, params = {}) {
  return request.get(`/subject-plan/plans/${planId}/mistakes`, { params: { user_id: userId, ...params } }).then(r => r.data)
}
export function getMistakesOverview(userId) {
  return request.get('/subject-plan/mistakes/overview', { params: { user_id: userId } }).then(r => r.data)
}
export function randomMistakePractice(params) {
  return request.get('/subject-plan/mistakes/practice', { params }).then(r => r.data)
}

// ===== 代码判题 =====
export function submitCode(data) {
  return request.post('/subject-plan/code/submit', data).then(r => r.data)
}

// ===== 真题套卷 =====
export function listExamPapers(syllabusId, userId) {
  return request.get(`/subject-plan/syllabi/${syllabusId}/exam-papers`, { params: { user_id: userId || '' } }).then(r => r.data)
}
export function getExamPaper(paperId, mode, userId) {
  return request.get(`/subject-plan/exam-papers/${paperId}`, { params: { mode, user_id: userId || '' } }).then(r => r.data)
}
export function submitExamPaper(paperId, data) {
  return request.post(`/subject-plan/exam-papers/${paperId}/submit`, data).then(r => r.data)
}
export function submitExamPlan(paperId, data) {
  return request.post(`/subject-plan/exam-papers/${paperId}/generate-plan`, data).then(r => r.data)
}
