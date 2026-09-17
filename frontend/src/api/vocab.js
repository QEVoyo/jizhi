import request from '@/utils/request'

// ============================================================
// 词条系统 — 词条查询（AI 生成缓存）、抓取记录、熟练度、词条本、定向出题
// ============================================================

// 获取词条（不存在则 AI 生成并全局缓存）
export function getVocabEntry(word) {
  return request.get(`/vocab/entries/${encodeURIComponent(word)}`).then(res => res.data)
}

// 记录词条抓取/讲解触点（chat_ask / xiaoji_vision）
export function postVocabLookups(userId, words, touchpoint) {
  return request.post('/vocab/lookups', { user_id: userId, words, touchpoint }).then(res => res.data)
}

// 词条卡「认识/不认识」打分（EWMA 熟练度）
export function postVocabMastery(userId, word, known) {
  return request.post('/vocab/mastery', { user_id: userId, word, known }).then(res => res.data)
}

// 词条本统计
export function getVocabStats(userId) {
  return request.get('/vocab/stats', { params: { user_id: userId } }).then(res => res.data)
}

// 词条本列表（filter: all / weak / mastered）
export function getWordbook(userId, filter = 'all') {
  return request.get('/vocab/wordbook', { params: { user_id: userId, filter } }).then(res => res.data)
}

// 薄弱词定向出题
export function postVocabPracticeSet(userId, words) {
  return request.post('/vocab/practice-set', { user_id: userId, words }).then(res => res.data)
}
