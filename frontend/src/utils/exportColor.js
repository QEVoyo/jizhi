// ===== 导出/截图前的现代颜色降级 =====
//
// 背景（2026-09-27 修）：html2canvas@1.4.1 的颜色解析器只认 rgb/hsl 四种写法
// （dist/html2canvas.js 的 SUPPORTED_COLOR_FUNCTIONS = {hsl, hsla, rgb, rgba}），
// 遇到别的颜色函数直接抛：
//     Error: Attempting to parse an unsupported color function "color"
//
// 而 Chrome 在 computed value 阶段会把项目里大量使用的 color-mix() 解析成
//     color(srgb 0.25098 0.619608 1 / 0.5)
// 于是「个人中心导出 PDF/图片」「评估表导出」「学情报告导出」全部失败。
//
// 关键点：混色数学**不用重算**——浏览器已经算完了，这里只做格式转换
// color(srgb r g b / a) → rgba(R, G, B, A)。
// 这和项目里 withAlpha()/brandSoft() 对 ECharts 做的适配是同一件事
// （见 stores/theme.js:74 注释「ECharts canvas 不认 CSS var()/color-mix」）——
// 同一次主题改版里 ECharts 适配了，html2canvas 漏了。
//
// 用法：
//     const restore = normalizeModernColors(el)
//     try { await html2canvas(el, …) } finally { restore() }
// restore 必须放在 finally —— 否则截图抛异常会把 inline style 永久留在真实 DOM 上。

// 会被 html2canvas 解析、且可能拿到 color() 的「单色」属性
const COLOR_PROPS = [
  'color',
  'background-color',
  'border-top-color', 'border-right-color', 'border-bottom-color', 'border-left-color',
  'outline-color',
  'text-decoration-color',
  '-webkit-text-stroke-color',
  'fill',
  'stroke'
]

// 值里可能内嵌 color() 的「复合」属性（渐变、阴影）
const COMPOSITE_PROPS = ['background-image', 'box-shadow', 'text-shadow']

// Chrome 的序列化形式：color(srgb 0.1 0.2 0.3) 或 color(srgb 0.1 0.2 0.3 / 0.5)
// alpha 可能是 0-1 小数，也可能是百分比。
const SRGB_RE = /color\(\s*srgb\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s*(?:\/\s*([\d.]+%?)\s*)?\)/g

// 非 srgb 色彩空间的 color()（oklch/lab/display-p3…）——本项目当前 0 处，
// 但一旦有人加了，分量语义就不再是 0-1 RGB，不能按上面的方式换算。
const OTHER_COLOR_RE = /color\(\s*(?!srgb\b)[a-z0-9-]+\s/

let _probe = null
function canvasFallback(value) {
  // 用 canvas 把任意合法颜色解析成 rgba()：浏览器怎么算，html2canvas 就拿到什么。
  if (!_probe) {
    _probe = document.createElement('canvas')
    _probe.width = _probe.height = 1
  }
  const ctx = _probe.getContext('2d', { willReadFrequently: true })
  if (!ctx) return null
  ctx.clearRect(0, 0, 1, 1)
  ctx.fillStyle = '#000'
  ctx.fillStyle = value
  // 浏览器不认识的写法会保持上一次的值，用哨兵排除
  if (ctx.fillStyle === '#000' && !/^#000\b/.test(value)) {
    // 可能是真的解析不了，也可能本来就是黑色；再验一次
    ctx.fillStyle = '#fff'
    ctx.fillStyle = value
    if (ctx.fillStyle === '#fff') return null
  }
  ctx.fillRect(0, 0, 1, 1)
  const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data
  return `rgba(${r}, ${g}, ${b}, ${(a / 255).toFixed(3)})`
}

function srgbToRgba(_, r, g, b, a) {
  const R = Math.round(Math.max(0, Math.min(1, parseFloat(r))) * 255)
  const G = Math.round(Math.max(0, Math.min(1, parseFloat(g))) * 255)
  const B = Math.round(Math.max(0, Math.min(1, parseFloat(b))) * 255)
  let A = 1
  if (a != null) A = a.endsWith('%') ? parseFloat(a) / 100 : parseFloat(a)
  A = Math.max(0, Math.min(1, A))
  return `rgba(${R}, ${G}, ${B}, ${A})`
}

function convert(value) {
  if (!value || !value.includes('color(')) return null
  let out = value.replace(SRGB_RE, srgbToRgba)
  // 仍然残留非 srgb 的 color() → 交给 canvas 兜底（整值转换）
  if (OTHER_COLOR_RE.test(out)) {
    const fb = canvasFallback(value)
    if (fb) out = fb
  }
  return out === value ? null : out
}

/**
 * 把导出子树里 html2canvas 解析不了的现代颜色写成 inline style（等价色值）。
 * @param {HTMLElement} root 截图根节点
 * @returns {() => void} 还原函数，务必在 finally 里调用
 */
export function normalizeModernColors(root) {
  if (!root || typeof document === 'undefined') return () => {}

  // 必须分两趟：先全部读、再全部写。
  // 边读边写会「写一次样式 → 下一次 getComputedStyle 强制重排」，
  // 资料卡有几百个节点，交替式实现会明显卡顿。两趟各只触发一次布局。
  const touched = []   // [el, prop, 原 inline 值]
  const pending = []   // [el, prop, 新值]

  const collect = (el) => {
    if (el.nodeType !== 1) return
    const cs = getComputedStyle(el)          // 每元素只取一次
    for (const prop of COLOR_PROPS) {
      const converted = convert(cs.getPropertyValue(prop))
      if (converted) pending.push([el, prop, converted])
    }
    for (const prop of COMPOSITE_PROPS) {
      const converted = convert(cs.getPropertyValue(prop))
      if (converted) pending.push([el, prop, converted])
    }
    for (const child of el.children) collect(child)   // 伪元素不遍历：写不了 inline style
  }

  collect(root)

  for (const [el, prop, value] of pending) {
    touched.push([el, prop, el.style.getPropertyValue(prop)])
    el.style.setProperty(prop, value)
  }

  return function restore() {
    for (const [el, prop, prev] of touched) {
      if (prev) el.style.setProperty(prop, prev)
      else el.style.removeProperty(prop)
    }
    touched.length = 0
  }
}

/**
 * 包一层：在降级后的颜色环境下执行 fn，结束后必定还原。
 * 调用点用它可以把改动压到最小（不用给几十行 options 重新缩进）：
 *
 *     const canvas = await withNormalizedColors(el, () => html2canvas(el, { … }))
 *
 * @template T
 * @param {HTMLElement} root
 * @param {() => Promise<T>} fn
 * @returns {Promise<T>}
 */
export async function withNormalizedColors(root, fn) {
  const restore = normalizeModernColors(root)
  try {
    return await fn()
  } finally {
    restore()
  }
}

export default normalizeModernColors
