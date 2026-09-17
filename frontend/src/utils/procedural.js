/**
 * 程序化生成的基础件：噪声、色彩、画布。
 * 星球地表（planetTexture.js）和黑洞（blackHole.js）共用这一份。
 */

/** #rrggbb → {r,g,b}（0-255）。不引主题 store，保持本模块自足 */
export function hexToRgb(hex) {
  if (!hex) return null
  const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(String(hex).trim())
  return m ? { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) } : null
}

// ===== 3D 值噪声 =====
// 用 3D 而不是 2D 是关键：球面贴图只要按 (u,v) 平面采噪声，左右接缝就对不上、
// 两极会被挤成麻花。把纹素换算成球面上的真实方向再采 3D 噪声，噪声本身就定义在球面上。

export function hash3(ix, iy, iz) {
  let h = Math.imul(ix, 374761393) ^ Math.imul(iy, 668265263) ^ Math.imul(iz, 1274126177)
  h = Math.imul(h ^ (h >>> 13), 1274126177)
  h ^= h >>> 16
  return (h >>> 0) / 4294967295
}

export function vnoise(x, y, z) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z)
  const xf = x - xi, yf = y - yi, zf = z - zi
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf), w = zf * zf * (3 - 2 * zf)
  const c000 = hash3(xi, yi, zi), c100 = hash3(xi + 1, yi, zi)
  const c010 = hash3(xi, yi + 1, zi), c110 = hash3(xi + 1, yi + 1, zi)
  const c001 = hash3(xi, yi, zi + 1), c101 = hash3(xi + 1, yi, zi + 1)
  const c011 = hash3(xi, yi + 1, zi + 1), c111 = hash3(xi + 1, yi + 1, zi + 1)
  const x00 = c000 + (c100 - c000) * u, x10 = c010 + (c110 - c010) * u
  const x01 = c001 + (c101 - c001) * u, x11 = c011 + (c111 - c011) * u
  const y0 = x00 + (x10 - x00) * v, y1 = x01 + (x11 - x01) * v
  return y0 + (y1 - y0) * w
}

/** 分形叠加：多倍频噪声相加，得到自然界的粗细层次 */
export function fbm(x, y, z, oct) {
  let a = 0.5, f = 1, s = 0, n = 0
  for (let i = 0; i < oct; i++) { s += a * vnoise(x * f, y * f, z * f); n += a; a *= 0.5; f *= 2.03 }
  return s / n
}

/**
 * 脊状噪声：把噪声折起来取尖峰，专门用来出裂纹/山脊/熔岩缝。
 * 注意取值会挤在 0.5 附近（fBm 把尖峰平均掉了），用之前得先按区间拉伸，
 * 直接 pow 的话整条曲线是平的，渲染出来就是一颗纯色球。
 */
export function ridge(x, y, z, oct) {
  let a = 0.5, f = 1, s = 0, n = 0
  for (let i = 0; i < oct; i++) {
    s += a * (1 - Math.abs(vnoise(x * f, y * f, z * f) * 2 - 1)); n += a; a *= 0.5; f *= 2.03
  }
  return s / n
}

// ===== 小工具 =====
export const clamp = (v, lo, hi) => v < lo ? lo : v > hi ? hi : v
export const mix3 = (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t]
export const smooth = (e0, e1, x) => { const t = clamp((x - e0) / ((e1 - e0) || 1e-6), 0, 1); return t * t * (3 - 2 * t) }

export function rgb2hsl(r, g, b) {
  r /= 255; g /= 255; b /= 255
  const mx = Math.max(r, g, b), mn = Math.min(r, g, b), l = (mx + mn) / 2
  let h = 0, s = 0
  if (mx !== mn) {
    const d = mx - mn
    s = l > 0.5 ? d / (2 - mx - mn) : d / (mx + mn)
    if (mx === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6
    else if (mx === g) h = ((b - r) / d + 2) / 6
    else h = ((r - g) / d + 4) / 6
  }
  return [h, s, l]
}

export function hsl2rgb(h, s, l) {
  h = ((h % 1) + 1) % 1
  if (s <= 0) { const v = Math.round(l * 255); return [v, v, v] }
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s
  const p = 2 * l - q
  const f = t => {
    t = ((t % 1) + 1) % 1
    if (t < 1 / 6) return p + (q - p) * 6 * t
    if (t < 1 / 2) return q
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6
    return p
  }
  return [Math.round(f(h + 1 / 3) * 255), Math.round(f(h) * 255), Math.round(f(h - 1 / 3) * 255)]
}

/** 一张待填充的 ImageData 画布 */
export function makeLayer(w, h) {
  const canvas = document.createElement('canvas'); canvas.width = w; canvas.height = h
  const ctx = canvas.getContext('2d')
  const img = ctx.createImageData(w, h)
  return { canvas, ctx, img, d: img.data }
}
