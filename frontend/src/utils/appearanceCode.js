// ===== 外观码（2026-09-04）=====
// 把四轴外观（背景/组件/主题/字体）打包成可分享的「外观码」。
// 设计：码本身就是四轴色值（可读、可手改），不是黑盒 base64；带校验段防抄错。
//
//   套装别名形（四轴恰为官方方案 → 超短码，像游戏种子）：  JZ1-space
//   全量形（hex 直排，能一眼读出配色）：                    JZ1-0d1220-16233c-409eff-paper-CK2F8
//   自定义字色形（custom 后跟三档字色 hex）：               JZ1-0d1220-16233c-409eff-custom-e8e8f0-a8a8c0-8888aa-7H33M
//
// 段结构：JZ1 <bg> <surface> <brand> <scheme> [<p> <s> <m>] <校验5位>
//   scheme 与 FONT_SCHEMES 键一致（default/paper/warmink/cyanink/ink/custom）

import { FONT_SCHEMES, THEME_SETS } from '@/stores/theme'

const PREFIX = 'jz1'
const HEX = /^[0-9a-f]{6}$/

// 校验字表（32 字符，剔掉 0/O/1/I/L 易混淆字符）
const CK_ALPHA = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

// djb2 哈希 → 5 位 32 进制（约 2.8 亿空间，抄错一段基本必现校验失败）
function checksum(payload) {
  let h = 5381
  for (let i = 0; i < payload.length; i++) {
    h = ((h << 5) + h + payload.charCodeAt(i)) >>> 0
  }
  let s = ''
  for (let i = 0; i < 5; i++) {
    s = CK_ALPHA[h % 32] + s
    h = Math.floor(h / 32)
  }
  return s
}

// 输入四轴 → 外观码字符串；恰为官方套装时给出超短别名（setKey/setName）
export function encodeAppearance(app) {
  const scheme = (app.textScheme === 'custom' && !app.textOverrides) ? 'default' : (app.textScheme || 'default')
  const overrides = scheme === 'custom' ? (app.textOverrides || null) : null
  const clean = c => String(c || '').replace(/^#/, '').toLowerCase()
  const flat = {
    bg: clean(app.bg),
    surface: clean(app.surface),
    brand: clean(app.brand),
    scheme,
    overrides: overrides ? {
      primary: clean(overrides.primary), secondary: clean(overrides.secondary), muted: clean(overrides.muted),
    } : null,
  }

  const hit = THEME_SETS.find(t =>
    clean(t.bg) === flat.bg
    && clean(t.surface) === flat.surface
    && clean(t.brand) === flat.brand
    && t.scheme === flat.scheme
    && !overrides
  )
  if (hit) return { code: `${PREFIX}-${hit.key}`, setKey: hit.key, setName: hit.name }

  const parts = [flat.bg, flat.surface, flat.brand, flat.scheme]
  // 四轴恒有合法 hex（themeStore 维护），越界值（历史脏数据）落到默认纸墨三档再编码，保证出码必可解
  if (flat.overrides) {
    const o = flat.overrides
    parts.push(
      HEX.test(o.primary) ? o.primary : 'f7f6f2',
      HEX.test(o.secondary) ? o.secondary : 'c8c6bc',
      HEX.test(o.muted) ? o.muted : '939288',
    )
  }
  const payload = parts.join('-')

  return { code: `${PREFIX}-${payload}-${checksum(payload)}`, setKey: null, setName: null }
}

// 分享直达链接：默认用当前站点域名（上线后自动是正式域名，无需改码）；
// 想在开发机/内网提前测「发给手机打开」，在 .env 配 VITE_SHARE_BASE_URL 覆盖
export function appearanceLink(code) {
  const raw = import.meta.env.VITE_SHARE_BASE_URL || location.origin
  const base = String(raw || '').replace(/\/+$/, '')
  return `${base}/theme?code=${encodeURIComponent(code)}`
}

// 解析外观码 → { ok, payload? | error? }；宽容输入：大小写/·._- 分隔符、随手带的 # 号均可
export function decodeAppearance(raw) {
  const code = String(raw || '').trim().replace(/#/g, '').replace(/[·._\s]+/g, '-').toLowerCase()
  if (!code) return { ok: false, error: '外观码不能为空' }
  const seg = code.split('-').filter(Boolean)
  if (seg[0] !== PREFIX) return { ok: false, error: '这不是基智外观码（应以 jz1 开头）' }
  seg.shift()

  // 套装别名形：JZ1-space
  if (seg.length === 1) {
    const t = THEME_SETS.find(x => x.key === seg[0])
    if (!t) return { ok: false, error: `未知套装「${seg[0]}」，可用：${THEME_SETS.map(x => x.key).join(' / ')}` }
    return {
      ok: true,
      isSet: true,
      setName: t.name,
      payload: { bg: t.bg, surface: t.surface, brand: t.brand, textScheme: t.scheme, textOverrides: null },
    }
  }

  // 全量形 → 末段是校验码：4 段正文 + 1 校验；custom 7 段正文 + 1 校验
  if (seg.length !== 5 && seg.length !== 8) {
    return { ok: false, error: '外观码段落不完整（应为 6 段或 9 段），请核对是否漏字符' }
  }
  const ck = seg[seg.length - 1].toUpperCase()
  const parts = seg.slice(0, -1)
  const [bg, surface, brand, scheme, ...rest] = parts

  if (!HEX.test(bg) || !HEX.test(surface) || !HEX.test(brand)) {
    return { ok: false, error: '色值段不合法（应为 6 位十六进制）' }
  }
  // 白名单：FONT_SCHEMES 预设档 + custom（store 里「自定义三档字色」的约定键，不在预设表里）
  const known = [...Object.keys(FONT_SCHEMES), 'custom']
  if (!known.includes(scheme)) {
    return { ok: false, error: `未知字体档「${scheme}」，可用：${known.join(' / ')}` }
  }
  let textOverrides = null
  if (scheme === 'custom') {
    if (rest.length !== 3 || !rest.every(x => HEX.test(x))) {
      return { ok: false, error: 'custom 字体档需要跟三档字色（主/次/弱 hex）' }
    }
    textOverrides = { primary: rest[0], secondary: rest[1], muted: rest[2] }
  } else if (rest.length !== 0) {
    return { ok: false, error: '外观码段落数量与字体档不符' }
  }

  if (checksum(parts.join('-')) !== ck) {
    return { ok: false, error: '校验失败：码里有错别字或缺字符，请对照原文核对' }
  }

  return { ok: true, isSet: false, setName: null, payload: { bg, surface, brand, textScheme: scheme, textOverrides } }
}