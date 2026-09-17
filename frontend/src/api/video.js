import request from '@/utils/request'

/**
 * 搜索B站视频
 * @param {string} keyword - 搜索关键词
 * @param {number} page - 页码
 * @param {number} pageSize - 每页数量
 */
export function searchBilibili(keyword, page = 1, pageSize = 4) {
  return request.get('/video/search', {
    params: { keyword, page, page_size: pageSize }
  }).then(res => res.data)
}

// ===== 自营视频库（2026-09-04：知识点级模板生成视频）=====

/**
 * 懒生成主入口：确保知识点有视频（命中即复用；缺口后台排产，返回现有列表）
 * @param {{knowledge_key, knowledge_name, subject?, stage?, goal?}} data
 */
export function ensureVideoLib(data) {
  return request.post('/video/lib/ensure', data).then(res => res.data)
}

/**
 * 检索排行（零 LLM）：100 本知识点 / 70 同学科 / 55 全局热门，用户自选
 * @param {{knowledge_key, subject?, question_fingerprint?, limit?}} params
 */
export function getVideoRelated(params) {
  return request.get('/video/lib/related', { params }).then(res => res.data)
}

/** 播放计数（热度/扩产依据） */
export function recordVideoPlay(videoId) {
  return request.post(`/video/lib/${videoId}/play`).then(res => res.data).catch(() => null)
}