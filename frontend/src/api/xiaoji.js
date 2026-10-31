import request from '@/utils/request'

// ===== 小基页侧栏（每日推荐 + 学习关心统计） =====
export function getXiaojiDaily(userId) {
  return request.get(`/xiaoji/daily/${userId}`).then(res => res.data)
}

// ===== 小基配置 =====
export function getXiaojiConfig(userId) {
  return request.get('/community/xiaoji/config', { params: { user_id: userId } }).then(res => res.data)
}

export function updateXiaojiConfig(userId, data) {
  return request.put('/community/xiaoji/config', data, { params: { user_id: userId } }).then(res => res.data)
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

/** 视频分析（2026-10-17 限额版）：前端每 3 秒抽 1 帧 → 后端逐帧识图 + 汇总 */
export function xiaojiVideoAnalyze(data) {
  return request.post('/community/xiaoji/video-analyze', data, {
    params: { user_id: data.user_id },
    timeout: 180000
  }).then(res => res.data)
}

/** 今日视频分析额度（北京时间零点重置，每天 5 分钟） */
export function getVideoQuota(userId) {
  return request.get('/community/xiaoji/video-quota', {
    params: { user_id: userId }
  }).then(res => res.data)
}

// ===== 聊天记录（含搜索） =====
export function getXiaojiMessages(userId, search = '', limit = 50, offset = 0) {
  return request.get('/community/xiaoji/messages', {
    params: { user_id: userId, search, limit, offset }
  }).then(res => res.data)
}

export function clearXiaojiMessages(userId) {
  // community 路由没有清空端点，用顶层 /xiaoji 的清空接口
  return request.delete(`/xiaoji/messages/${userId}`).then(res => res.data)
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

// ===== 生成 Agent 队友：指定知识点出题 / 留空自动选题（薄弱优先）→ 真实生成落库 → 题目卡回聊（2026-09-02） =====
export function agentGenerate(userId, topic = '') {
  return request.post('/community/xiaoji/agent-generate', { topic }, {
    params: { user_id: userId }
  }).then(res => res.data)
}

/**
 * 意图判别（2026-09-10 自动分流）
 * deep=false（默认）只跑规则层与关键词门——零成本零延迟，供输入框实时预判；
 * deep=true 允许在「像派活但规则没抓住」时调一次 qwen-flash，发送时用（现已由
 * chat-stream 内部完成，此接口主要供前端预判/调试）。
 */
export function routeIntent(text, deep = false) {
  return request.post('/community/xiaoji/route', { text, deep }, { timeout: 15000 }).then(res => res.data)
}

// ===== 上传文件生成题目（2026-10-30） =====
// 流程：upload → 轮询 job（解析/画像/可出题点）→ confirm（唯一生成入口）→ generate → result
export function uploadQuestionFile(userId, file) {
  const form = new FormData()
  form.append('file', file)
  // ⚠️ axios 实例在 utils/request.js 里默认写了 `Content-Type: application/json`。
  //    不覆盖它，FormData 会被当成 JSON 发出去，后端 FastAPI 收不到 file 字段
  //    → 422 {"loc":["body","file"],"msg":"Field required"}（2026-10-30 实测）。
  //    显式写 multipart，浏览器/axios 会自己补 boundary。
  return request.post('/xiaoji/upload', form, {
    params: { user_id: userId },
    timeout: 120000,
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(res => res.data)
}

export function getUploadJob(jobId, userId) {
  return request.get(`/xiaoji/upload/${jobId}`, { params: { user_id: userId } }).then(res => res.data)
}

export function confirmUpload(jobId, userId, data) {
  return request.post(`/xiaoji/upload/${jobId}/confirm`, data, {
    params: { user_id: userId },
  }).then(res => res.data)
}

export function generateUpload(jobId, userId) {
  return request.post(`/xiaoji/upload/${jobId}/generate`, null, {
    params: { user_id: userId },
    timeout: 120000,
  }).then(res => res.data)
}

export function getUploadResult(jobId, userId) {
  return request.get(`/xiaoji/upload/${jobId}/result`, { params: { user_id: userId } }).then(res => res.data)
}

export function deleteUpload(jobId, userId) {
  return request.delete(`/xiaoji/upload/${jobId}`, { params: { user_id: userId } }).then(res => res.data)
}

// ===== 语音合成（千问 TTS，返回 audio_base64 + format） =====
export function xiaojiTts(text, opts = {}) {
  return request.post('/xiaoji/tts', {
    text,
    speed: opts.speed ?? 5,
    volume: opts.volume ?? 5,
    pitch: opts.pitch ?? 5,
    voice_name: opts.voice_name ?? 'longanqian'
  }).then(res => res.data)
}

