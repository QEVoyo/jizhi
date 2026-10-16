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

// ===== 学习计划 =====
// 列表已经嵌好用户昵称/邮箱了（后端用外键嵌入查的），前端不用再逐个查用户。
export function getPlans(params = {}) {
  return request.get('/admin/plans', { params }).then(res => res.data)
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

// ===== 视频库管理（2026-09-04）=====
export function getAdminVideos(params = {}) {
  return request.get('/admin/video/list', { params }).then(res => res.data)
}

export function reviewAdminVideo(videoId, action) {
  return request.post(`/admin/video/${videoId}/review`, { action }).then(res => res.data)
}

export function removeAdminVideo(videoId) {
  return request.delete(`/admin/video/${videoId}`).then(res => res.data)
}

export function getAdminVideoReports(params = {}) {
  return request.get('/admin/video/reports', { params }).then(res => res.data)
}

export function handleAdminVideoReport(reportId, action) {
  return request.post(`/admin/video/reports/${reportId}/handle`, { action }).then(res => res.data)
}

export function adminVideoWarm(payload) {
  return request.post('/admin/video/warm', payload).then(res => res.data)
}

export function getAdminVideoStats() {
  return request.get('/admin/video/stats').then(res => res.data)
}

export function retryAdminVideo(videoId) {
  return request.post(`/admin/video/${videoId}/retry`).then(res => res.data)
}

// 系统信息（题库总量 / 考纲数 / 各 API 提供方是否已配置）。
// 后端这个端点在 admin.py 里一直存在，但前端此前**连封装都没有、全站零调用** ——
// 后台侧边栏也没有入口。2026-09-30 补上。
export function getSystemSettings() {
  return request.get('/admin/settings').then(res => res.data)
}

// ===== 安全中心（2026-10-15）=====
// 数据源是 security_events 表，由 utils/security_log.py 写入
// （中间件自动记限流/鉴权失败/越权，业务主动记冒充他人 user_id）。

/** 筛选器的可选项（事件类型 / 严重级）。类型来自后端登记表，不是查库 distinct */
export function getSecurityFilters() {
  return request.get('/admin/security/filters').then(res => res.data)
}

/** 安全事件分页列表 */
export function getSecurityEvents(params = {}) {
  return request.get('/admin/security/events', { params }).then(res => res.data)
}

/** 总览聚合（趋势 / 分布 / Top IP / Top 用户） */
export function getSecurityOverview(params = {}) {
  return request.get('/admin/security/overview', { params }).then(res => res.data)
}

// ===== 用户信誉（2026-10-15 第二期）=====
// 信誉分与「积分」是两个体系：积分只增不减（学习攒的），信誉可增可减（违规掉、清白回来）。
// 四张表：user_reputation / _logs / reputation_rules / reputation_tiers。

/** 单个用户：分数 + 档位 + 清白天数 + 完整变更历史 */
export function getUserReputation(userId, params = {}) {
  return request.get(`/admin/security/users/${userId}/reputation`, { params }).then(res => res.data)
}

/** 手动设分。**理由必填** —— 后端会拒空理由，前端也先拦一道 */
export function setUserReputation(userId, score, reason) {
  return request.put(`/admin/security/users/${userId}/reputation`, { score, reason }).then(res => res.data)
}

/** 信誉分列表（低分在前）。只列表里有行的用户 = 有过违规记录的人 */
export function listReputations(params = {}) {
  return request.get('/admin/security/reputation/list', { params }).then(res => res.data)
}

/** 规则与档位配置（只读；改值直接 UPDATE 表，代码零改动） */
export function getReputationRules() {
  return request.get('/admin/security/reputation/rules').then(res => res.data)
}

// ===== 生成审计（2026-10-15 第三期）=====
// 数据源是 ai_generation_audit 表，由 utils/safety_gateway.py 每次生成写一行
// （成功也写）。与「安全事件」是两回事：那边只记失败和拦截，问的是「谁在攻击」；
// 这边问的是「我们的 AI 生成跑成什么样」。
//
// ⚠️ 覆盖率取决于有多少调用点迁到了网关（现在 2/40），所以数字**不是全站**。
//    接口返回里的 coverage 字段就是给界面提示这件事用的。

/** 生成审计总览（成功率 / 按用途 / 按模型 / 耗时 / 趋势） */
export function getGenAuditOverview(params = {}) {
  return request.get('/admin/security/gen-audit/overview', { params }).then(res => res.data)
}

/** 生成审计明细 */
export function getGenAuditList(params = {}) {
  return request.get('/admin/security/gen-audit', { params }).then(res => res.data)
}
