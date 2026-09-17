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

/** 视频分析（2026-09-05）：前端本地抽帧 → 后端逐帧识图 + 汇总 */
export function xiaojiVideoAnalyze(data) {
  return request.post('/community/xiaoji/video-analyze', data, {
    params: { user_id: data.user_id },
    timeout: 180000
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

// ===== 语音识别（讯飞 ASR，audio_base64 为 16k 16bit 单声道 PCM） =====
export function xiaojiAsr(audioBase64, format = 'raw') {
  return request.post('/community/xiaoji/asr', {
    audio_base64: audioBase64,
    format
  }).then(res => res.data)
}