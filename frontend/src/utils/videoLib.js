// 视频库键约定（2026-09-04，必须与 backend/services/video_gen.py 逐字节一致，
// 否则前端算的 knowledge_key 对不上后端存储，视频就查不中）

/** 同步 sha1（TextEncoder UTF-8 输入，与后端 hashlib.sha1(str.encode()) 一致） */
export function sha1Hex(input) {
  const data = new TextEncoder().encode(String(input))
  const bitLen = data.length * 8
  // 补齐到 64 字节块：消息 + 0x80 + 0 填充 + 8 字节长度
  const padded = new Uint8Array((Math.floor((data.length + 8) / 64) + 1) * 64)
  padded.set(data)
  padded[data.length] = 0x80
  const dv = new DataView(padded.buffer)
  dv.setUint32(padded.length - 8, Math.floor(bitLen / 0x100000000))
  dv.setUint32(padded.length - 4, bitLen >>> 0)

  let h0 = 0x67452301, h1 = 0xEFCDAB89, h2 = 0x98BADCFE, h3 = 0x10325476, h4 = 0xC3D2E1F0
  const w = new Array(80)
  for (let i = 0; i < padded.length; i += 64) {
    for (let t = 0; t < 16; t++) w[t] = dv.getUint32(i + t * 4)
    for (let t = 16; t < 80; t++) {
      const v = w[t - 3] ^ w[t - 8] ^ w[t - 14] ^ w[t - 16]
      w[t] = (v << 1) | (v >>> 31)
    }
    let a = h0, b = h1, c = h2, d = h3, e = h4
    for (let t = 0; t < 80; t++) {
      let f, k
      if (t < 20) { f = (b & c) | (~b & d); k = 0x5A827999 }
      else if (t < 40) { f = b ^ c ^ d; k = 0x6ED9EBA1 }
      else if (t < 60) { f = (b & c) | (b & d) | (c & d); k = 0x8F1BBCDC }
      else { f = b ^ c ^ d; k = 0xCA62C1D6 }
      const tmp = (((a << 5) | (a >>> 27)) + f + e + k + w[t]) | 0
      e = d; d = c; c = ((b << 30) | (b >>> 2)) | 0; b = a; a = tmp
    }
    h0 = (h0 + a) | 0; h1 = (h1 + b) | 0; h2 = (h2 + c) | 0; h3 = (h3 + d) | 0; h4 = (h4 + e) | 0
  }
  const hex = v => (v >>> 0).toString(16).padStart(8, '0')
  return hex(h0) + hex(h1) + hex(h2) + hex(h3) + hex(h4)
}

/** 知识点键：学科 + kp 短哈希（与后端 make_knowledge_key 一致） */
export function knowledgeKey(subject, kpId) {
  const h = sha1Hex(String(kpId || '').trim()).slice(0, 12)
  return `${subject || ''}:${h}`
}

/** 题干归一化指纹（与后端 question_fingerprint 一致：小写/全半角/去标点 → sha1 前 16 位） */
export function questionFingerprint(stem, options = null, answer = null) {
  let norm = String(stem || '')
  norm = norm.toLowerCase().replace(/（/g, '(').replace(/）/g, ')').replace(/，/g, ',').replace(/。/g, '.')
  norm = norm.replace(/[^\w一-鿿]+/gu, '')
  return sha1Hex(norm).slice(0, 16)
}

// 讲解角度 → 展示名（与后端 ANGLE_POOL 键对齐）
export const ANGLE_LABELS = {
  concept: '概念精讲', method: '方法论', pitfall: '易错排雷', shortcut: '秒杀技巧',
  contrast: '对比辨析', origin: '根源推导', mnemonic: '口诀记忆', exam: '考试视角',
  notes: '学霸笔记', story: '情境故事', visual: '图解演示', demo: '拆题示范',
}