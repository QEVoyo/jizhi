import request from '@/utils/request'

// ===== 主面板 =====
export function getDashboard() {
  return request.get('/admin/dashboard').then(res => res.data)
}

// ===== 用户管理 =====
export function getUsers(params = {}) {
  return request.get('/admin/users', { params }).then(res => res.data)
}

export function getUserDetail(userId) {
  return request.get(`/admin/users/${userId}`).then(res => res.data)
}

export function updateUserStatus(userId, isActive) {
  return request.put(`/admin/users/${userId}/status`, { is_active: isActive }).then(res => res.data)
}

export function updateUserAdmin(userId, isAdmin) {
  return request.put(`/admin/users/${userId}/admin`, { is_admin: isAdmin }).then(res => res.data)
}

// ===== 内容举报 =====
export function getReports(params = {}) {
  return request.get('/admin/reports', { params }).then(res => res.data)
}

export function resolveReport(reportId, data) {
  return request.put(`/admin/reports/${reportId}/resolve`, data).then(res => res.data)
}

// ===== 用户反馈 =====
export function getFeedbacks(params = {}) {
  return request.get('/admin/feedback', { params }).then(res => res.data)
}

export function resolveFeedback(feedbackId, data) {
  return request.put(`/admin/feedback/${feedbackId}`, data).then(res => res.data)
}

// ===== Q&A =====
export function getQAList(params = {}) {
  return request.get('/admin/qa', { params }).then(res => res.data)
}

export function resolveQA(qaId, data) {
  return request.put(`/admin/qa/${qaId}`, data).then(res => res.data)
}

// ===== 题库管理 =====
export function getQuestions(params = {}) {
  return request.get('/admin/questions', { params }).then(res => res.data)
}

export function getQuestionDetail(questionId) {
  return request.get(`/admin/questions/${questionId}`).then(res => res.data)
}

export function createQuestion(data, syllabusId = 'cet4') {
  return request.post('/admin/questions', data, { params: { syllabus_id: syllabusId } }).then(res => res.data)
}

export function updateQuestion(questionId, data) {
  return request.put(`/admin/questions/${questionId}`, data).then(res => res.data)
}

export function deleteQuestion(questionId) {
  return request.delete(`/admin/questions/${questionId}`).then(res => res.data)
}

export function importQuestions(questions, syllabusId = 'cet4') {
  return request.post('/admin/questions/import', { questions }, { params: { syllabus_id: syllabusId } }).then(res => res.data)
}

// ===== 公告 =====
export function getAnnouncements() {
  return request.get('/admin/announcements').then(res => res.data)
}

export function getActiveAnnouncements() {
  return request.get('/admin/announcements/active').then(res => res.data)
}

export function createAnnouncement(data) {
  return request.post('/admin/announcements', data).then(res => res.data)
}

export function updateAnnouncement(id, data) {
  return request.put(`/admin/announcements/${id}`, data).then(res => res.data)
}

export function deleteAnnouncement(id) {
  return request.delete(`/admin/announcements/${id}`).then(res => res.data)
}

// ===== 审计日志 =====
export function getAuditLogs(params = {}) {
  return request.get('/admin/logs', { params }).then(res => res.data)
}

// ===== 系统信息 =====
export function getSystemInfo() {
  return request.get('/admin/settings').then(res => res.data)
}
