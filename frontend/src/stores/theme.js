import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getUserTheme } from '@/api/auth'

const CACHE_KEY = 'jizhi-custom-theme'   // 账号主题的本地缓存（离线秒开，登录后以服务端为准）

// 字体预设档（每档自带主/次/弱三连；default = 跟随深浅主题内置值，不注入覆盖）
export const FONT_SCHEMES = {
  default: null,
  paper: { primary: '#f7f6f2', secondary: '#c8c6bc', muted: '#939288' },   // 纯净白纸（适合深底）
  warmink: { primary: '#2b2520', secondary: '#5d544b', muted: '#8f857a' }, // 暖墨（适合浅底）
  cyanink: { primary: '#e9f4f6', secondary: '#a8c2c8', muted: '#779298' }, // 青灰（适合深底）
  ink: { primary: '#14161c', secondary: '#3c4150', muted: '#6e7483' },     // 曜黑（适合浅底）
}

// 主题色预设（设置页 + 恢复默认用）
export const BRAND_PRESETS = ['#409EFF', '#8b5cf6', '#35b7c9', '#ec4899', '#f59e0b', '#10b981', '#f43f5e']

// 背景色预设（浅系 / 深系两行）
export const BG_PRESETS = {
  light: ['#f5f5f7', '#eef4fb', '#f6f2e9', '#eef7f0', '#fdf0f4'],
  dark: ['#12121e', '#0d1117', '#151a2c', '#1d1526', '#101418'],
}

// 组件色预设（毛玻璃卡片/输入框等表面，浅系 / 深系两行）
export const SURFACE_PRESETS = {
  light: ['#ffffff', '#f2f6ff', '#fffaf1', '#eefaf4', '#fbf1f7'],
  dark: ['#161b2e', '#1c2a3a', '#241f33', '#1c2e2b', '#231d27'],
}

// 整套方案：背景 + 组件 + 主题 + 字体一次换好（对比度均为预校验过的搭配）
export const THEME_SETS = [
  { key: 'space', name: '深空蓝', bg: '#0d1220', surface: '#16233c', brand: '#409EFF', scheme: 'paper' },
  { key: 'pure', name: '纯净白', bg: '#f7f8fa', surface: '#ffffff', brand: '#2563eb', scheme: 'ink' },
  { key: 'nebula', name: '星云紫', bg: '#17122a', surface: '#241d3d', brand: '#8b5cf6', scheme: 'paper' },
  { key: 'glacier', name: '冰川青', bg: '#eef5f6', surface: '#ffffff', brand: '#0e7490', scheme: 'ink' },
  { key: 'cocoa', name: '暖沙棕', bg: '#f5eee1', surface: '#fffdf7', brand: '#c07a1d', scheme: 'warmink' },
  { key: 'noir', name: '曜黑金', bg: '#101112', surface: '#1f1e1a', brand: '#d4a94f', scheme: 'paper' },
]

// 默认方案（2026-09-03 用户拍板：新用户首次进入 +「恢复默认」= 深空蓝四轴；
// 浅/深不再由用户选择，明暗由背景色亮度自动派生；仅落地页跟随系统）
export const DEFAULT_SET = THEME_SETS[0]

// 字体色「默认」档跟随模式时的基准值（与 theme.css 的 --text-* 一致，适配度计算共用）
export const MODE_TEXT_COLORS = {
  dark: { primary: '#e8e8f0', secondary: '#a8a8c0', muted: '#8888aa' },
  light: { primary: '#1a1a2e', secondary: '#4a4a6a', muted: '#888888' },
}

// ===== 颜色工具 =====
export function hexToRgb(hex) {
  if (!hex || !hex.startsWith('#')) return null
  let h = hex.slice(1)
  if (h.length === 3) h = h.split('').map(c => c + c).join('')
  if (h.length !== 6 || !/^[0-9a-fA-F]{6}$/.test(h)) return null
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  }
}

// a 色与 b 色按 aWeight 混合（0-1）
export function mixColor(a, b, aWeight) {
  const ca = hexToRgb(a), cb = hexToRgb(b)
  if (!ca || !cb) return a
  const w = Math.max(0, Math.min(1, aWeight))
  const to = v => Math.round(ca[v] * w + cb[v] * (1 - w)).toString(16).padStart(2, '0')
  return `#${to('r')}${to('g')}${to('b')}`
}

// hex + 透明度 → rgba 字符串（毛玻璃组件色用）
export function withAlpha(hex, alpha) {
  const c = hexToRgb(hex)
  if (!c) return `rgba(255,255,255,${alpha})`
  return `rgba(${c.r}, ${c.g}, ${c.b}, ${Math.max(0, Math.min(1, alpha))})`
}

// WCAG 对比度（1-21），设置页适配度用
function _lum(c) {
  const f = v => {
    const s = v / 255
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4)
  }
  return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b)
}

// 相对亮度 0-1（深色背景判断、自动调整字体色用）
export function luminance(hex) {
  const c = hexToRgb(hex)
  return c ? _lum(c) : 0.5
}

export function contrastRatio(fg, bg) {
  const a = hexToRgb(fg), b = hexToRgb(bg)
  if (!a || !b) return 21
  const l1 = _lum(a), l2 = _lum(b)
  return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05)
}

// 四轴字体解析（设置页 / 外观码预览 / 分享页共用口径）：
// 自定义三档 > 预设档 > 按背景明暗派生的内置默认
export function resolveText(textScheme, textOverrides, bgColorHex) {
  if (textOverrides) {
    return { primary: textOverrides.primary, secondary: textOverrides.secondary, muted: textOverrides.muted }
  }
  if (FONT_SCHEMES[textScheme]) return FONT_SCHEMES[textScheme]
  const dark = luminance(bgColorHex) <= 0.5
  return MODE_TEXT_COLORS[dark ? 'dark' : 'light']
}

// 适配度：五组 WCAG 对比度按标杆折算加权成百分比（文字落在组件上，以组件色为基准）
export function computeFit(bg, surface, brand, text) {
  const items = [
    { key: 'text', label: '主文字 × 组件色', weight: 0.38, target: 4.5, ratio: contrastRatio(text.primary, surface),
      advice: luminance(surface) < 0.5
        ? '主文字与组件色太接近，卡片正文可能看不清。建议换更浅的字体色'
        : '主文字与组件色太接近，卡片正文可能看不清。建议换更深的字体色' },
    { key: 'brand', label: '主题色 × 组件色', weight: 0.2, target: 3, ratio: contrastRatio(brand, surface),
      advice: '主题色与组件色过于接近，按钮和选中态会不明显。建议换一个反差更大的主题色' },
    { key: 'surfbg', label: '组件色 × 背景色', weight: 0.17, target: 1.6, ratio: contrastRatio(surface, bg),
      advice: '组件色与背景色过于接近，毛玻璃卡片会融进背景。建议拉开两者的差距' },
    { key: 'text2', label: '次文字 × 组件色', weight: 0.15, target: 3, ratio: contrastRatio(text.secondary, surface),
      advice: '次文字与组件色对比偏弱，说明性文字可能费劲。建议提高次文字的反差' },
    { key: 'muted', label: '弱文字 × 组件色', weight: 0.1, target: 1.8, ratio: contrastRatio(text.muted, surface),
      advice: '弱文字与组件色过于接近，提示性文字难以辨认' },
  ]
  const checks = items.map(it => {
    const score = Math.max(0, Math.min(100, Math.round((it.ratio / it.target) * 100)))
    const cls = it.ratio >= it.target ? 'good' : it.ratio >= it.target * 0.72 ? 'warn' : 'bad'
    return { key: it.key, label: it.label, ratio: it.ratio.toFixed(1), score, weight: it.weight, cls, advice: cls === 'good' ? '' : it.advice }
  })
  const pct = Math.round(checks.reduce((s, c) => s + c.score * c.weight, 0))
  const cls = checks.some(c => c.cls === 'bad') ? 'bad' : checks.some(c => c.cls === 'warn') ? 'warn' : 'good'
  const summary = cls === 'bad' ? '存在看不清的风险，建议按上面提示调整后再用'
    : cls === 'warn' ? '个别搭配偏弱，建议微调' : '整体适配良好，可以放心使用'
  const canAutoFix = checks.filter(c => ['text', 'text2', 'muted'].includes(c.key)).some(c => c.cls !== 'good')
  return { pct, cls, checks, summary, canAutoFix }
}

function loadCache() {
  try {
    return JSON.parse(localStorage.getItem(CACHE_KEY) || 'null')
  } catch {
    return null
  }
}

const cache = loadCache()

export const useThemeStore = defineStore('theme', () => {
  // 明暗不再由用户选择（2026-09-03 用户拍板：删浅/深/跟随系统）：
  // resolved 深浅由背景色亮度自动派生；落地页期间由 enterLanding 改为跟随系统
  const currentTheme = ref('dark')
  let landingActive = false   // 落地页期间为 true：明暗跟系统、定制变量摘下

  // ===== 四轴定制（2026-09-02 品牌/字体 → 09-03 四轴：背景/组件/主题/字体）=====
  // 四轴恒有具体值：默认 = 深空蓝方案（新用户首次进入 + 恢复默认），null（老账号数据）映射回默认
  const brandColor = ref(cache?.brand_color || DEFAULT_SET.brand)
  const textScheme = ref(cache?.text_scheme || DEFAULT_SET.scheme)
  const textOverrides = ref(cache?.text_overrides || null)   // {primary, secondary, muted}
  const bgColor = ref(cache?.bg_color || DEFAULT_SET.bg)
  const surfaceColor = ref(cache?.surface_color || DEFAULT_SET.surface)

  function deriveTheme() {
    if (landingActive) return currentTheme.value   // 落地页跟随系统，不走派生
    return luminance(bgColor.value) > 0.5 ? 'light' : 'dark'
  }

  // 注入运行时 CSS 变量：--brand 系列 + 三档字色 + 背景色 + 组件色（四轴全覆盖）
  function injectCustomVars() {
    const root = document.documentElement
    const brand = brandColor.value || DEFAULT_SET.brand
    root.style.setProperty('--brand', brand)
    // 深底上的亮字版 / 浅底上的深字版：由品牌色向白/黑混合，保证可读
    root.style.setProperty('--brand-bright', mixColor(brand, '#ffffff', 0.82))
    root.style.setProperty('--brand-ink', mixColor(brand, '#000000', 0.62))
    root.style.setProperty('--brand-glow', mixColor(brand, '#ffffff', 0.45))
    // 品牌色块上的可读字色（2026-09-03 审计第 3 批）：亮品牌用深墨、暗品牌用白
    root.style.setProperty('--brand-on', luminance(brand) > 0.5 ? '#1a1a2e' : '#ffffff')

    const effective = textOverrides.value || FONT_SCHEMES[textScheme.value]
    if (effective) {
      root.style.setProperty('--text-primary', effective.primary)
      root.style.setProperty('--text-secondary', effective.secondary)
      root.style.setProperty('--text-muted', effective.muted)
    } else {
      root.style.removeProperty('--text-primary')
      root.style.removeProperty('--text-secondary')
      root.style.removeProperty('--text-muted')
    }

    // 背景色 + 组件色恒注入；卡片/输入框底色按派生明暗的透明度重算
    const dark = currentTheme.value === 'dark'
    root.style.setProperty('--bg-color', bgColor.value)
    root.style.setProperty('--surface', surfaceColor.value)
    root.style.setProperty('--card-bg', withAlpha(surfaceColor.value, dark ? 0.8 : 0.85))
    root.style.setProperty('--input-bg', withAlpha(surfaceColor.value, dark ? 0.4 : 0.7))
  }

  // 摘下全部内联定制变量（落地页跟随系统时用：系统明暗的纯净观感，四轴定制色不渗入）
  function removeCustomVars() {
    const root = document.documentElement
    for (const k of ['--brand', '--brand-bright', '--brand-ink', '--brand-glow', '--brand-on',
      '--text-primary', '--text-secondary', '--text-muted',
      '--bg-color', '--surface', '--card-bg', '--input-bg']) {
      root.style.removeProperty(k)
    }
  }

  function setBrand(color) {
    brandColor.value = color
    applyTheme()
  }

  function setTextScheme(scheme) {
    textScheme.value = scheme
    textOverrides.value = null
    applyTheme()
  }

  function setTextOverrides(obj) {
    textScheme.value = 'custom'
    textOverrides.value = obj || null
    applyTheme()
  }

  function setBg(color) {
    bgColor.value = color || DEFAULT_SET.bg
    applyTheme()
  }

  function setSurface(color) {
    surfaceColor.value = color || DEFAULT_SET.surface
    applyTheme()
  }

  // 四轴当前状态快照（外观码导出用）
  function currentAppearance() {
    return {
      bg: bgColor.value,
      surface: surfaceColor.value,
      brand: brandColor.value,
      textScheme: textScheme.value,
      textOverrides: textOverrides.value,
    }
  }

  // 外观码导入：四轴一步到位（单次 applyTheme，避免四连闪烁）
  function applyAppearance({ bg, surface, brand, textScheme, textOverrides }) {
    if (bg) bgColor.value = bg
    if (surface) surfaceColor.value = surface
    if (brand) brandColor.value = brand
    if (textScheme) {
      textScheme.value = textScheme
      textOverrides.value = textOverrides || null
    }
    cachePersist()
    applyTheme()
  }

  // 恢复默认 = 回到默认方案四轴（背景 + 组件 + 主题 + 字体全覆盖）
  function resetCustom() {
    brandColor.value = DEFAULT_SET.brand
    textScheme.value = DEFAULT_SET.scheme
    textOverrides.value = null
    bgColor.value = DEFAULT_SET.bg
    surfaceColor.value = DEFAULT_SET.surface
    applyTheme()
  }

  function applyTheme() {
    currentTheme.value = deriveTheme()
    document.documentElement.setAttribute('data-theme', currentTheme.value)
    injectCustomVars()
  }

  // 登录后从账号拉主题（本地缓存先顶着，服务端返回后覆盖）；登出调 resetCustom
  async function loadFromAccount(userId) {
    if (!userId) { resetCustom(); return }
    try {
      const t = await getUserTheme(userId)
      if (!t) return   // 接口还没上线/表未建：保持本地值与默认
      // 老账号存的 null（曾表示「跟随模式」）统一映射回默认方案四轴
      brandColor.value = t.brand_color || DEFAULT_SET.brand
      textScheme.value = t.text_scheme || DEFAULT_SET.scheme
      textOverrides.value = t.text_overrides || null
      bgColor.value = t.bg_color || DEFAULT_SET.bg
      surfaceColor.value = t.surface_color || DEFAULT_SET.surface
      cachePersist()
      applyTheme()
    } catch {
      // 静默：网络失败继续用本地
    }
  }

  function cachePersist() {
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      brand_color: brandColor.value, text_scheme: textScheme.value,
      text_overrides: textOverrides.value, bg_color: bgColor.value, surface_color: surfaceColor.value,
    }))
  }

  // ===== 落地页专属：跟随系统明暗（2026-09-03 用户拍板：仅落地页跟系统，无任何可改入口）=====
  const landingQuery = window.matchMedia('(prefers-color-scheme: dark)')
  function onLandingThemeChange() {
    if (!landingActive) return
    currentTheme.value = landingQuery.matches ? 'dark' : 'light'
    document.documentElement.setAttribute('data-theme', currentTheme.value)
  }
  // 进入落地页：摘下四轴定制变量 + 明暗改跟系统；离开：applyTheme 恢复派生 + 重注入
  function enterLanding() {
    landingActive = true
    removeCustomVars()
    onLandingThemeChange()
    landingQuery.addEventListener('change', onLandingThemeChange)
  }
  function exitLanding() {
    landingActive = false
    landingQuery.removeEventListener('change', onLandingThemeChange)
    applyTheme()
  }

  // 初始化
  applyTheme()

  return {
    currentTheme,
    brandColor,
    textScheme,
    textOverrides,
    bgColor,
    surfaceColor,
    setBrand,
    setTextScheme,
    setTextOverrides,
    setBg,
    setSurface,
    resetCustom,
    currentAppearance,
    applyAppearance,
    applyTheme,
    loadFromAccount,
    cachePersist,
    enterLanding,
    exitLanding,
  }
})