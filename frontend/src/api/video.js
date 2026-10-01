import request from '@/utils/request'
import { recordAction } from '@/api/career'

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
  return request.post('/video/lib/ensure', data).then(res => {
    const d = res.data
    // 学程埋点（2026-10-01）：真的**触发了生成**才记 ——
    // ensure 是幂等的，命中已有视频时 triggered 为假，那不算「生成视频」。
    // 埋在这一处而不是各个调用点：ensure 有 4 个调用方，散着写必然漏。
    if (d && d.triggered && data && data.user_id) {
      recordAction(data.user_id, 'generate_video')
    }
    return d
  })
}

/**
 * 检索排行（零 LLM）：100 本知识点 / 70 同学科 / 55 全局热门，用户自选
 * @param {{knowledge_key, subject?, question_fingerprint?, limit?}} params
 */
export function getVideoRelated(params) {
  return request.get('/video/lib/related', { params }).then(res => res.data)
}

/**
 * 「推送」分类：题目/计划那边触发懒生成时，推送到我视频库里的视频（2026-10-01）。
 *
 * ⚠️ 和「我的视频」是两回事：
 *   我的视频 = 我主动点「生成我的视频」建的
 *   推送     = 我生成题目/计划时，顺带带出来的讲解
 * 视频本身是全站共享的（一个知识点只有一条），所以「谁被推送过什么」
 * 单独记在 `user_video_pushes` 里。
 */
export function getMyPushes(userId) {
  return request.get(`/video/me/${userId}/pushes`).then(res => res.data)
}

/**
 * 按知识点查视频的**生成状态**（含失败原因）。
 *
 * ⚠️ 为什么不能只看 `getVideoRelated`：它**只返回 ready 的视频**，
 * 所以「正在生成」和「已经失败」在前端看起来一模一样 ——
 * 用户会一直等一个永远不会出现的视频（2026-10-01 实测等了一分多钟，
 * 而那条视频其实早就 failed 了）。
 *
 * @returns {Promise<{ready:number, generating:number, failed:number, total:number, error:string|null}>}
 */
export function getVideoStatus(params) {
  return request.get('/video/lib/status', { params }).then(res => res.data)
}

/** 播放计数（热度/扩产依据） */
export function recordVideoPlay(videoId) {
  return request.post(`/video/lib/${videoId}/play`).then(res => res.data).catch(() => null)
}