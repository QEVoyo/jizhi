/**
 * 程序化星球地表 —— 个人画像「维度宇宙」的九颗行星。
 *
 * 球体贴等距圆柱投影图有两个老毛病：左右接缝对不上、两极挤成麻花。
 * 这里不按 (u,v) 平面采噪声，而是先把每个纹素换算成它在球面上的真实单位方向，
 * 再拿这个方向去采 3D 噪声——噪声本身就定义在球面上，接缝与极点问题自然都不存在。
 *
 * 全部图都是运行时现算的，不依赖任何图片资源。
 * 纯装饰：外观只呼应维度主题配色，不承载分数。
 */
import * as THREE from 'three'

import {
  hexToRgb as _hexToRgb, hash3 as _hash3,
  vnoise as _vnoise, fbm as _fbm, ridge as _ridge,
  clamp as _clamp, mix3 as _mix3, smooth as _smooth,
  rgb2hsl as _rgb2hsl, hsl2rgb as _hsl2rgb, makeLayer as _layer,
} from './procedural'

// ===== 程序化星球地表 =====
// 噪声与色彩基础件见 procedural.js（3D 值噪声 + fBm + 脊状噪声）：
// 用 3D 噪声而非平面噪声，是为了让球面贴图没有左右接缝、两极也不挤成麻花。
const PLANET_SPECS = {
  knowledge:   { type: 'terran', seed: 1, sea: 0.50, cloud: 0.42, shift: 0.09 },
  ability:     { type: 'gas',    seed: 2, bands: 11, turb: 0.55, storm: true,  cloud: 0.18, ring: 1.95, shift: 0.05 },
  rhythm:      { type: 'ice',    seed: 3, crack: 4.2, cloud: 0.14, shift: 0.05 },
  cognitive:   { type: 'rock',   seed: 4, craters: 16, cloud: 0.08, shift: 0.10 },
  mistake:     { type: 'lava',   seed: 5, vein: 4.5, cloud: 0.22, shift: 0.02 },
  growth:      { type: 'ocean',  seed: 6, sea: 0.66, cloud: 0.46, shift: 0.07 },
  personality: { type: 'terran', seed: 7, sea: 0.40, cloud: 0.62, shift: 0.12 },
  interest:    { type: 'gas',    seed: 8, bands: 22, turb: 0.34, storm: false, cloud: 0.12, ring: 2.10, shift: 0.04 },
  summary:     { type: 'ice',    seed: 9, crack: 2.6, cloud: 0.30, shift: 0.03 },
}

const PLANET_TEX_W = 512, PLANET_TEX_H = 256

/**
 * 生成一颗星球的地表贴图。
 * 返回两张纹理：color（颜色）与 data（R=高度→凹凸，G=粗糙度→海面反光、陆地哑光）。
 * 凹凸与粗糙度打包进同一张图，省一张纹理——three 的 bumpMap 取 .x、roughnessMap 取 .g。
 */
function makePlanetSurface(baseColor, spec) {
  const W = PLANET_TEX_W, H = PLANET_TEX_H
  const col = _layer(W, H)
  const dat = _layer(W, H)
  const emi = spec.type === 'lava' ? _layer(W, H) : null

  const base = _hexToRgb(baseColor) || { r: 64, g: 158, b: 255 }
  const [bh, bs] = _rgb2hsl(base.r, base.g, base.b)
  // 调色板全部从维度主题色沿色相/明度派生：九颗各有身份，又是同一套语言
  const P = {
    deep:    _hsl2rgb(bh - 0.04, _clamp(bs * 0.95, 0, 1), 0.10),
    shallow: _hsl2rgb(bh, _clamp(bs * 0.90, 0, 1), 0.30),
    low:     _hsl2rgb(bh + spec.shift, _clamp(bs * 0.62, 0, 1), 0.40),
    high:    _hsl2rgb(bh + spec.shift * 0.6, _clamp(bs * 0.30, 0, 1), 0.58),
    peak:    _hsl2rgb(bh, 0.06, 0.93),
    ice:     _hsl2rgb(bh, 0.10, 0.95),
    rock:    _hsl2rgb(bh - 0.02, _clamp(bs * 0.35, 0, 1), 0.13),
    hot:     _hsl2rgb(bh + 0.03, 1.0, 0.60),
  }
  const S = spec.seed * 37.13

  // 陨坑：先把位置与半径摇好，免得在逐纹素循环里再算随机
  const craters = []
  if (spec.type === 'rock') {
    for (let i = 0; i < (spec.craters || 14); i++) {
      const u = _hash3(i * 7 + spec.seed, 13, 29), v = _hash3(i * 3 + spec.seed, 71, 5)
      const th = Math.acos(2 * u - 1), ph = v * Math.PI * 2
      craters.push({
        x: Math.sin(th) * Math.cos(ph), y: Math.cos(th), z: Math.sin(th) * Math.sin(ph),
        r: 0.10 + _hash3(i, 91, spec.seed) * 0.26,
      })
    }
  }

  const cp = col.d, dp = dat.d, ep = emi ? emi.d : null
  for (let j = 0; j < H; j++) {
    const theta = (j + 0.5) / H * Math.PI
    const dy = Math.cos(theta), sr = Math.sin(theta)
    for (let i = 0; i < W; i++) {
      const phi = (i + 0.5) / W * Math.PI * 2
      const dx = Math.cos(phi) * sr, dz = Math.sin(phi) * sr
      let c, height, rough, glow = 0

      switch (spec.type) {
        case 'terran': {
          const cont = _fbm(dx * 1.9 + S, dy * 1.9 + S * 0.7 + 3, dz * 1.9 + S * 0.3 + 7, 6)
          const det = _fbm(dx * 6.5 + 31, dy * 6.5 + 13, dz * 6.5 + 53, 4)
          const h = cont * 0.76 + det * 0.24
          const sea = spec.sea
          if (h < sea) {
            const t = Math.pow(h / sea, 0.7)
            c = _mix3(P.deep, P.shallow, t)          // 远海→近海
            height = 0.10 + t * 0.05
            rough = 0.10                              // 水面反光
          } else {
            const t = _clamp((h - sea) / (1 - sea), 0, 1)
            c = t < 0.45 ? _mix3(P.shallow, P.low, t / 0.45) : _mix3(P.low, P.high, (t - 0.45) / 0.55)
            if (t > 0.82) c = _mix3(c, P.peak, (t - 0.82) / 0.18)
            height = 0.35 + t * 0.65
            rough = 0.92                              // 陆地哑光
          }
          const snow = _smooth(0.70, 0.94, Math.abs(dy) + (h - sea) * 0.35)
          if (snow > 0) { c = _mix3(c, P.ice, snow); height += (0.75 - height) * snow }
          break
        }
        case 'ocean': {
          // 域扭曲：先算一个低频偏移量，再用它去扰动采样坐标，出洋流/涡旋那种卷曲纹理。
          // 没有这一层的话，全球皆水 = 一整个纯色球，和没贴图看不出区别。
          const wx = _fbm(dx * 1.4 + S, dy * 1.4 + 2, dz * 1.4 + 6, 3) - 0.5
          const wz = _fbm(dx * 1.4 + 19, dy * 1.4 + 8, dz * 1.4 + 4, 3) - 0.5
          const swirl = _fbm(dx * 3.6 + wx * 4.5 + 11, dy * 3.6 + wz * 4.5 + 3, dz * 3.6 + wx * 3 + 7, 4)
          const cont = _fbm(dx * 2.3 + S, dy * 2.3 + S * 0.5 + 5, dz * 2.3 + S * 0.9 + 2, 6)
          const det = _fbm(dx * 7.5 + 11, dy * 7.5 + 43, dz * 7.5 + 23, 4)
          const h = cont * 0.8 + det * 0.2
          const sea = spec.sea
          if (h < sea) {
            const t = Math.pow(h / sea, 0.6)
            c = _mix3(P.deep, P.shallow, t)
            c = _mix3(c, P.high, _smooth(0.34, 0.72, swirl) * 0.60)   // 洋流花纹
            height = 0.08 + t * 0.06
            rough = 0.08
          } else {
            const t = _clamp((h - sea) / (1 - sea), 0, 1)   // 零星岛屿
            c = _mix3(P.low, P.high, t)
            height = 0.40 + t * 0.60
            rough = 0.90
          }
          const snow = _smooth(0.62, 0.90, Math.abs(dy))    // 极冠比类地行星大
          if (snow > 0) { c = _mix3(c, P.ice, snow); height += (0.72 - height) * snow }
          break
        }
        case 'gas': {
          const turb = _fbm(dx * 2.2 + S, dy * 2.2 + 1 + S * 0.4, dz * 2.2 + 9, 5)
          const lat = dy + turb * 0.22                       // 纬度被湍流扰动，条纹不是死板直线
          const band = Math.sin(lat * spec.bands * Math.PI) * 0.5 + 0.5
          const fine = _fbm(dx * 11 + 3, dy * 17 + 7, dz * 11 + 5, 4)  // y 频率更高 → 细节拉成纬向条
          const t = band * 0.68 + fine * 0.32
          c = _mix3(P.deep, P.high, _smooth(0.12, 0.88, t))
          height = 0.5
          rough = 0.85
          if (spec.storm) {
            // 大红斑：固定在一处，经向拉长（y 权重更大 → 扁）
            const sx = dx - 0.62, sy = dy - 0.30, sz = dz + 0.72
            const d = Math.sqrt(sx * sx * 0.55 + sy * sy * 2.4 + sz * sz * 0.55)
            const sp = _smooth(0.52, 0.20, d)
            if (sp > 0) { c = _mix3(c, P.hot, sp); height = 0.5 + sp * 0.1 }
          }
          break
        }
        case 'ice': {
          const plates = _fbm(dx * 2.4 + S, dy * 2.4 + 2, dz * 2.4 + 5, 5)
          const fine = _fbm(dx * 9 + 4, dy * 9 + 6, dz * 9 + 1, 4)
          const crack = _ridge(dx * spec.crack + 7, dy * spec.crack + 11, dz * spec.crack + 3, 5)
          // _ridge 的取值挤在 0.5 附近（fBm 平均掉了尖峰），直接 pow 之后整条曲线被压平，
          // 渲染出来就是一颗纯色球。先按实测区间拉伸再平方，才收得出「缝」。
          const cv = Math.pow(_clamp((crack - 0.60) / 0.20, 0, 1), 1.6)
          const t = plates * 0.55 + fine * 0.45
          c = _mix3(P.deep, P.ice, _smooth(0.22, 0.85, t + cv * 0.25))
          c = _mix3(c, P.deep, cv * 0.85)                     // 裂缝压暗，像冰层断开
          height = t * 0.7 + (1 - cv) * 0.3
          rough = 0.25                                        // 冰面偏亮
          break
        }
        case 'rock': {
          const b1 = _fbm(dx * 2.1 + S, dy * 2.1 + 6, dz * 2.1 + 2, 6)
          const b2 = _fbm(dx * 9 + 5, dy * 9 + 3, dz * 9 + 9, 4)
          const t = b1 * 0.7 + b2 * 0.3
          c = _mix3(P.deep, P.high, _smooth(0.18, 0.85, t))
          height = t
          rough = 0.95
          for (let k = 0; k < craters.length; k++) {
            const cr = craters[k]
            const ax = dx - cr.x, ay = dy - cr.y, az = dz - cr.z
            const d = Math.sqrt(ax * ax + ay * ay + az * az)
            if (d < cr.r * 1.5) {
              const e = d / cr.r
              if (e < 1) {                       // 坑底：压暗压平
                const k2 = 1 - e
                c = _mix3(c, P.deep, k2 * 0.55)
                height *= 1 - k2 * 0.5
              } else {                           // 坑缘：隆起提亮
                const k2 = 1 - (e - 1) / 0.5
                c = _mix3(c, P.high, k2 * 0.3)
                height = Math.min(1, height + k2 * 0.22)
              }
            }
          }
          break
        }
        case 'lava': {
          const crust = _fbm(dx * 3.0 + S, dy * 3.0 + 4, dz * 3.0 + 8, 6)
          const vein = _ridge(dx * spec.vein + 13, dy * spec.vein + 5, dz * spec.vein + 17, 5)
          const v = _clamp(Math.pow(vein, 4.5) * 1.6, 0, 1)
          c = _mix3(P.rock, P.hot, v)
          height = crust
          rough = 0.9 - v * 0.5
          glow = v                                    // 只有裂缝发光，冷壳不发光
          break
        }
      }

      const o = (j * W + i) * 4
      cp[o] = c[0]; cp[o + 1] = c[1]; cp[o + 2] = c[2]; cp[o + 3] = 255
      dp[o] = height * 255; dp[o + 1] = rough * 255; dp[o + 2] = 0; dp[o + 3] = 255
      if (ep) { ep[o] = P.hot[0] * glow; ep[o + 1] = P.hot[1] * glow; ep[o + 2] = P.hot[2] * glow; ep[o + 3] = 255 }
    }
  }

  col.ctx.putImageData(col.img, 0, 0)
  dat.ctx.putImageData(dat.img, 0, 0)
  if (emi) emi.ctx.putImageData(emi.img, 0, 0)

  const colorTex = new THREE.CanvasTexture(col.canvas)
  colorTex.colorSpace = THREE.SRGBColorSpace
  colorTex.anisotropy = 4
  return {
    color: colorTex,
    data: new THREE.CanvasTexture(dat.canvas),      // 线性空间，不能标 sRGB
    emissive: emi ? (() => { const t = new THREE.CanvasTexture(emi.canvas); t.colorSpace = THREE.SRGBColorSpace; return t })() : null,
  }
}

/** 云层贴图：白色带 alpha，单独一层球，转得比地表快一点就有视差 */
function makeCloudTexture(baseColor, spec) {
  const W = 256, H = 128
  const L = _layer(W, H)
  const base = _hexToRgb(baseColor) || { r: 64, g: 158, b: 255 }
  const tint = _mix3([255, 255, 255], [base.r, base.g, base.b], 0.16)
  const S = spec.seed * 91.7
  const thr = 1 - spec.cloud, p = L.d
  for (let j = 0; j < H; j++) {
    const theta = (j + 0.5) / H * Math.PI
    const dy = Math.cos(theta), sr = Math.sin(theta)
    for (let i = 0; i < W; i++) {
      const phi = (i + 0.5) / W * Math.PI * 2
      const dx = Math.cos(phi) * sr, dz = Math.sin(phi) * sr
      const n = _fbm(dx * 3.2 + S, dy * 3.2 + 7, dz * 3.2 + 11, 5)
      const w = _fbm(dx * 9 + 4, dy * 9 + 21, dz * 9 + 2, 3)
      let a = n * 0.7 + w * 0.3
      a *= 0.75 + 0.25 * Math.cos(dy * Math.PI * 2.2)     // 赤道与中纬云多，极地稀
      a = _smooth(thr, thr + 0.34, a)
      const o = (j * W + i) * 4
      p[o] = tint[0]; p[o + 1] = tint[1]; p[o + 2] = tint[2]; p[o + 3] = a * 235
    }
  }
  L.ctx.putImageData(L.img, 0, 0)
  const t = new THREE.CanvasTexture(L.canvas)
  t.colorSpace = THREE.SRGBColorSpace
  return t
}

/**
 * 光环贴图。RingGeometry 的 UV 是平面映射（(x/外径+1)/2），
 * 所以画布中心=环心、画布半径=环外径，径向画分带即可。
 */
function makeRingTexture(baseColor, seed) {
  const S = 256
  const L = _layer(S, S)
  const base = _hexToRgb(baseColor) || { r: 64, g: 158, b: 255 }
  const [bh, bs] = _rgb2hsl(base.r, base.g, base.b)
  const light = _hsl2rgb(bh, _clamp(bs * 0.35, 0, 1), 0.72)
  const dark = _hsl2rgb(bh, _clamp(bs * 0.55, 0, 1), 0.30)
  const sd = seed * 53.9, inner = 0.66, p = L.d
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      const nx = (x + 0.5) / S * 2 - 1, ny = (y + 0.5) / S * 2 - 1
      const r = Math.sqrt(nx * nx + ny * ny)
      let a = 0
      if (r > inner && r < 1) {
        const bands = _vnoise(r * 46 + sd, 0.5, 0.5)      // 高频 = 细密环缝
        const gap = _vnoise(r * 13 + sd * 2, 3.7, 1.3)    // 低频 = 卡西尼缝那种大空档
        a = _smooth(0.18, 0.78, bands * 0.55 + gap * 0.45)
        a *= _smooth(inner, inner + 0.05, r) * (1 - _smooth(0.90, 1.0, r))
      }
      const c = _mix3(dark, light, 0.5 + 0.5 * _vnoise(r * 24 + sd, 2.1, 7.3))
      const o = (y * S + x) * 4
      p[o] = c[0]; p[o + 1] = c[1]; p[o + 2] = c[2]; p[o + 3] = a * 210
    }
  }
  L.ctx.putImageData(L.img, 0, 0)
  const t = new THREE.CanvasTexture(L.canvas)
  t.colorSpace = THREE.SRGBColorSpace
  return t
}

// 占位贴图：1×1 白。先挂上去让着色器按「有贴图」编译好，
// 之后换真图不会触发重新编译（否则九颗星球会在进场动画里各卡一下）。
let _placeholderTex = null
function getPlaceholderTexture() {
  if (_placeholderTex) return _placeholderTex
  const c = document.createElement('canvas'); c.width = 1; c.height = 1
  const ctx = c.getContext('2d'); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, 1, 1)
  _placeholderTex = new THREE.CanvasTexture(c)
  return _placeholderTex
}

export {
  PLANET_SPECS, PLANET_TEX_W, PLANET_TEX_H,
  makePlanetSurface, makeCloudTexture, makeRingTexture,
  getPlaceholderTexture,
}
