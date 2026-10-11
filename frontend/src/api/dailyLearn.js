import request from '@/utils/request'

// ============================================================
// 每日学习推荐（三合一：学习内容 + 题目 + 视频）· 2026-10-08
//
// 首页「小基推荐」卡片和消息中心那条**进的是同一个页面**（/daily-learn），
// 所以取数与进度都走这一套 —— 两边各写一份的话，进度判定迟早分叉
//（10-07 那轮踩过：消息中心和侧边栏两套角标算法，数字永远对不上）。
//
// 设计规格见 project1/message_center_design.md §六。
// ============================================================

/**
 * 我最新的一条推荐 —— 首页卡片跳的是**不带 id** 的 /daily-learn，走这条。
 *
 * ⚠️ 没有推荐时后端返回 `null`（不是 404）：卡片要把「今天还没有」显示成
 * 空态，而不是弹一个错误框。
 */
export function getLatestRec(userId) {
  return request.get('/daily-learn/latest', { params: { user_id: userId } }).then(r => r.data)
}

/** 指定某一条（从消息中心点某条旧推荐进来时用） */
export function getRec(id, userId) {
  return request.get(`/daily-learn/${id}`, { params: { user_id: userId } }).then(r => r.data)
}

/**
 * 完整题面。
 *
 * ⚠️ payload 里只存了 120 字 `stem` 摘要（列表要显示），做题得拿全的。
 * 后端按**每道题自己的 syllabus_id** 取 —— 题库 497 个 id 横跨多库，
 * 统一用一个 syllabus_id 会取错题。
 */
export function getRecQuestions(id, userId) {
  return request.get(`/daily-learn/${id}/questions`, { params: { user_id: userId } }).then(r => r.data)
}

/** 取（或首次生成）学习正文。**幂等**：生成过就直接回缓存，不重烧 LLM */
export function getRecContent(id, userId) {
  return request.post(`/daily-learn/${id}/content`, {}, { params: { user_id: userId } })
    .then(r => r.data)
}

/** 标记某一块做完（content / questions / video）。三块齐 → 整条完成 */
export function setRecProgress(id, userId, block) {
  return request.put(`/daily-learn/${id}/progress`, { block }, { params: { user_id: userId } })
    .then(r => r.data)
}

/**
 * 手动生成今天的推荐 —— 首页卡片空态里那个「生成今日推荐」按钮。
 *
 * `force` 只忽略**发送时间**（想现在看就现在生成），**去重照旧生效**：
 * 今天已经有了就直接把它返回（`detail.skipped_done`），不会多出一条。
 * 所以这个按钮点几次都安全。
 *
 * 返回 `{ success, generated, detail, recommendation }`。
 * `generated === 0` 且 `detail.no_content` 说明**凑不出内容**（宁缺毋滥的设计），
 * 前端要给出「做几道题再试」的提示，而不是干巴巴的「失败」。
 */
export function generateTodayRec(userId) {
  return request.post('/daily-learn/generate', {}, { params: { user_id: userId } })
    .then(r => r.data)
}
