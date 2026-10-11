import request from '@/utils/request'

// ============================================================
// 消息中心（2026-10-07 新接口）
//
// 替代掉改造前那四套互相打架的读法：
//   /community/messages/unread/summary、/community/messages/unread/count、
//   /community/sidebar-badges、/admin/announcements/active
// 现在只有 /messages 一套。设计见 project1/message_center_design.md
// ============================================================

/** 列表：已读未读都在里面，未读置顶 */
export function listMessages(params) {
  return request.get('/messages', { params }).then(res => res.data)
}

/** 角标 —— 侧边栏/顶栏/浏览器标题/桌宠**全部**用这一个，口径才一致 */
export function getBadges(userId) {
  return request.get('/messages/badges', { params: { user_id: userId } }).then(res => res.data)
}

/** 消息点注册表（Tab、图标、配色、跳转全从它推导；不需要登录） */
export function getRegistry() {
  return request.get('/messages/registry').then(res => res.data)
}

/** 单条详情（聚合行点开看"谁赞的"就靠它） */
export function getMessage(id, userId) {
  return request.get(`/messages/${id}`, { params: { user_id: userId } }).then(res => res.data)
}

/** 路径 A：点开这一条 */
export function readOne(id, userId) {
  return request.put(`/messages/${id}/read`, {}, { params: { user_id: userId } }).then(res => res.data)
}

/** 路径 C：直接标记（ids / group / type / all 四选一） */
export function readMany(userId, body) {
  return request.put('/messages/read', body, { params: { user_id: userId } }).then(res => res.data)
}

/** 路径 B：走到目标页面即已读（挂在路由守卫上，一处覆盖全部消息点） */
export function readByRoute(userId, url) {
  return request.put('/messages/read-by-route', { url }, { params: { user_id: userId } })
    .then(res => res.data)
}

/** 待办型专用：处理完了才算已读（接受/拒绝/回复） */
export function markHandled(id, userId) {
  return request.put(`/messages/${id}/handled`, {}, { params: { user_id: userId } }).then(res => res.data)
}

/** 单条删除（软删；system 组会被后端拒绝，返回 400） */
export function deleteMessage(id, userId) {
  return request.delete(`/messages/${id}`, { params: { user_id: userId } }).then(res => res.data)
}

/** 分类清空（软删；system 组永久保留） */
export function clearMessages(userId, { group, type }) {
  return request.delete('/messages', { params: { user_id: userId, group, type } }).then(res => res.data)
}

export function getMessageSettings(userId) {
  return request.get('/messages/settings', { params: { user_id: userId } }).then(res => res.data)
}

export function updateMessageSettings(userId, data) {
  return request.put('/messages/settings', data, { params: { user_id: userId } }).then(res => res.data)
}
