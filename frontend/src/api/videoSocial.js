import request from '@/utils/request'

// ===== 视频库·广场与互动（2026-09-04）=====

/** 广场信息流：学科/角度筛选 + 关键词 + 排序（hot/new/like） */
export function getVideoSquare(params) {
  return request.get('/video/square', { params }).then(res => res.data)
}

/** 广场学科 chips */
export function getVideoSubjects() {
  return request.get('/video/subjects').then(res => res.data)
}

/** 视频详情 + 当前用户互动状态 + 相关推荐 */
export function getVideoDetail(videoId, userId = '') {
  return request.get(`/video/${videoId}/detail`, { params: { user_id: userId } }).then(res => res.data)
}

/** 播放上报：浏览量（人日去重）+ 热点词库 */
export function reportVideoPlay(videoId, payload = {}) {
  return request.post(`/video/lib/${videoId}/play`, payload).then(res => res.data).catch(() => null)
}

/** 做题按钮：视频知识点的学科计划推荐题目（无则前端走 AI 生成） */
export function getVideoQuestions(videoId, limit = 12) {
  return request.get(`/video/lib/${videoId}/questions`, { params: { limit } }).then(res => res.data)
}

/** 点赞 toggle */
export function toggleVideoLike(videoId, userId) {
  return request.post(`/video/${videoId}/like`, { user_id: userId }).then(res => res.data)
}

/** 收藏 toggle */
export function toggleVideoFavorite(videoId, userId) {
  return request.post(`/video/${videoId}/favorite`, { user_id: userId }).then(res => res.data)
}

/** 评论列表 */
export function getVideoComments(videoId, page = 1) {
  return request.get(`/video/${videoId}/comments`, { params: { page } }).then(res => res.data)
}

/** 发表评论 */
export function postVideoComment(videoId, payload) {
  return request.post(`/video/${videoId}/comments`, payload).then(res => res.data)
}

/** 删除自己的评论 */
export function deleteVideoComment(commentId, userId) {
  return request.delete(`/video/comment/${commentId}`, { params: { user_id: userId } }).then(res => res.data)
}

/** 举报 */
export function reportVideo(videoId, payload) {
  return request.post(`/video/${videoId}/report`, payload).then(res => res.data)
}

/** 我的生成列表 */
export function getMyVideos(userId) {
  return request.get(`/video/me/${userId}`).then(res => res.data)
}

/** 我的收藏 */
export function getMyFavoriteVideos(userId) {
  return request.get(`/video/me/${userId}/favorites`).then(res => res.data)
}

/** 自己生成（模板排队） */
export function generateMyVideo(payload) {
  return request.post('/video/generate-mine', payload).then(res => res.data)
}

/** 发布到广场（待审核） */
export function publishMyVideo(videoId, userId) {
  return request.post(`/video/${videoId}/publish`, { user_id: userId }).then(res => res.data)
}

/** 重试失败视频 */
export function retryMyVideo(videoId, userId) {
  return request.post(`/video/${videoId}/retry`, { user_id: userId }).then(res => res.data)
}

/** 删除自己的视频 */
export function deleteMyVideo(videoId, userId) {
  return request.delete(`/video/${videoId}`, { params: { user_id: userId } }).then(res => res.data)
}