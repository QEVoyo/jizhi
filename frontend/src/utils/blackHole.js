/**
 * 中央黑洞 —— 个人画像「维度宇宙」正中的天体，点它退出宇宙（被吸进去）。
 *
 * 三个部件：
 *  ① 事件视界：纯黑球，不反光，把背后的星空彻底挡住
 *  ② 光子环 + 透镜弧：一张朝向镜头的程序化贴图
 *  ③ 吸积盘：赤道面上的环，缓慢自转
 *
 * 关于②为什么用 billboard 而不是真做引力透镜：真透镜要单独一整套后处理，
 * 而这块招牌观感——视界边缘一圈细亮环、外加吸积盘远侧的光被弯折到视界上下各成一道弧——
 * 一张贴图就能拿到，而且镜头转到任何角度都成立。
 *
 * 配色跟随用户「外观色」（09-12 定下的：中央天体是这套外观的核心）。
 * 视界本身按物理就该是黑的，所以主题色落在吸积盘和环上。
 */
import * as THREE from 'three'
import { hexToRgb, fbm, clamp, mix3, smooth, rgb2hsl, hsl2rgb, makeLayer } from './procedural'

export const HORIZON_R = 0.68   // 事件视界半径（出场动画里行星「被吞掉」的尺度基准）
const PHOTON_R  = 0.76       // 光子环半径：紧贴视界外缘再往外一点
const DISK_IN   = 0.95       // 吸积盘内缘（再往里物质就绕不起来了）
const DISK_OUT  = 2.20       // 吸积盘外缘
const RING_SPAN = 4.6        // 光子环 billboard 的世界尺寸
// 粒子屏占的定标基准 = 本场景默认机位到中心的距离（camera 在 (0,12,18)）。
// 顶点着色器不做透视衰减，需要一个固定距离把世界单位换算成像素。
const REF_DIST = Math.hypot(12, 18)
const RING_U    = PHOTON_R / (RING_SPAN / 2)   // 环在贴图里占半画布的比例

/** 吸积盘贴图：内缘白热、向外幂律冷却，叠角向条纹做出湍流 */
function makeAccretionDiskTexture(brandColor) {
  const S = 512
  const L = makeLayer(S, S)
  const base = hexToRgb(brandColor) || { r: 64, g: 158, b: 255 }
  const [bh, bs] = rgb2hsl(base.r, base.g, base.b)
  const hot = hsl2rgb(bh, clamp(bs * 0.25, 0, 1), 0.94)    // 内缘：高温，近乎白
  const warm = hsl2rgb(bh, clamp(bs * 0.95, 0, 1), 0.60)   // 中段：主题色本色
  const cool = hsl2rgb(bh, clamp(bs * 0.85, 0, 1), 0.34)   // 外缘：冷却变暗
  const inner = DISK_IN / DISK_OUT
  const p = L.d
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      // RingGeometry 的 UV 是平面映射：画布中心=盘心、画布半径=盘外径
      const nx = (x + 0.5) / S * 2 - 1, ny = (y + 0.5) / S * 2 - 1
      const r = Math.sqrt(nx * nx + ny * ny)
      const o = (y * S + x) * 4
      let a = 0, c = cool
      if (r > inner && r < 1) {
        const t = (r - inner) / (1 - inner)                    // 0 内缘 → 1 外缘
        // 角向条纹：拿角度当噪声坐标，绕一圈自然连续、不会在接缝处断开。
        // 频率要够高、摆幅要够大，否则盘面渲染出来是一团均匀的雾，
        // 看不出是「绕转的物质」。
        const ang = Math.atan2(ny, nx)
        const streak = fbm(Math.cos(ang) * 4.0 + 5, Math.sin(ang) * 4.0 + 9, r * 14 + 2, 5)
        a = Math.pow(1 - t, 1.6) * (0.35 + 1.25 * streak)      // 内热外冷 + 湍流
        a *= smooth(0, 0.05, t) * (1 - smooth(0.78, 1, t))     // 内外缘柔化，别切出硬边
        c = t < 0.35 ? mix3(hot, warm, t / 0.35) : mix3(warm, cool, (t - 0.35) / 0.65)
      }
      p[o] = c[0]; p[o + 1] = c[1]; p[o + 2] = c[2]
      p[o + 3] = clamp(a, 0, 1) * 255
    }
  }
  L.ctx.putImageData(L.img, 0, 0)
  const tex = new THREE.CanvasTexture(L.canvas)
  tex.colorSpace = THREE.SRGBColorSpace
  return tex
}

/** 光子环 + 透镜弧：一道细亮圆环，外加视界上下两道更亮的弧 */
function makePhotonRingTexture(brandColor) {
  const S = 256
  const L = makeLayer(S, S)
  const base = hexToRgb(brandColor) || { r: 64, g: 158, b: 255 }
  // 环本身接近白（高温），只蘸一点主题色，免得整圈发脏
  const ring = mix3([255, 255, 255], [base.r, base.g, base.b], 0.22)
  const arc = mix3([255, 255, 255], [base.r, base.g, base.b], 0.38)
  const W0 = 0.017                                          // 环的厚度：细才像光子环，粗了就是个发光甜甜圈
  const p = L.d
  for (let y = 0; y < S; y++) {
    for (let x = 0; x < S; x++) {
      const nx = (x + 0.5) / S * 2 - 1, ny = (y + 0.5) / S * 2 - 1
      const r = Math.sqrt(nx * nx + ny * ny)
      const ang = Math.atan2(ny, nx)
      // 主环：紧贴视界的一圈细光
      const gRing = Math.exp(-Math.pow((r - RING_U) / W0, 2))
      // 上下两道弧：吸积盘远侧的光被引力弯折过来（sin^4 让它只集中在正上/正下）
      const arcMask = Math.pow(Math.abs(Math.sin(ang)), 4)
      const gArc = Math.exp(-Math.pow((r - RING_U * 1.16) / (W0 * 2.4), 2)) * arcMask * 0.85
      // 外侧柔光：让细环在缩放较小时也还看得见。范围收窄，不然整圈会糊成一团云
      const gGlow = Math.exp(-Math.max(0, r - RING_U) / 0.085) * 0.10
      const v = clamp(gRing + gArc + gGlow, 0, 1)
      const c = mix3(ring, arc, clamp(gArc * 1.6, 0, 1))
      const o = (y * S + x) * 4
      p[o] = c[0]; p[o + 1] = c[1]; p[o + 2] = c[2]; p[o + 3] = v * 255
    }
  }
  L.ctx.putImageData(L.img, 0, 0)
  const tex = new THREE.CanvasTexture(L.canvas)
  tex.colorSpace = THREE.SRGBColorSpace
  return tex
}

/**
 * 星尘：被黑洞吸进去的粒子流。
 *
 * 「粒子不断变多」是这个效果的要点，所以用**固定粒子池 + 逐渐放行**的做法：
 * 池子里有 count 颗，某时刻只有前 floor(count * activeFrac) 颗可见，activeFrac 从 0 涨到 1，
 * 观感上就是星尘越聚越多。每颗落到中心就重新丢回外圈，于是外圈始终有新的补进来、形成持续的内流。
 *
 * 每颗粒子的轨迹与行星同一套：半径按幂次收缩，角速度随半径缩小而暴涨。
 */
export function createStardust(brandColor, count = 3200) {
  const pos = new Float32Array(count * 3)
  const aSize = new Float32Array(count)
  const aAlpha = new Float32Array(count)
  const r0 = new Float32Array(count)       // 起始半径
  const ang0 = new Float32Array(count)     // 起始相位
  const yAmp = new Float32Array(count)     // 离面高度（略呈盘状，不是正球壳）
  const prog = new Float32Array(count)     // 下落进度 0..1
  const rate = new Float32Array(count)     // 进度推进速度（每颗快慢不同）

  for (let i = 0; i < count; i++) {
    // 世界单位下的半径量级。默认机位下约合 1~3.5 像素——
    // 星尘就该是细碎亮点；给到 0.5 以上会变成比行星还大的糊团
    aSize[i] = 0.055 + Math.random() * 0.110
    respawn(i, true)
  }

  function respawn(i, initial) {
    // 从远处来：起点要远到默认机位（距中心约 21.6）的取景框之外，
    // 这样粒子是从画面外缘飞进来、旋转着汇向中心，而不是在画面中央凭空出现。
    r0[i] = 9 + Math.pow(Math.random(), 1.3) * 21        // 9 ~ 30
    ang0[i] = Math.random() * Math.PI * 2
    yAmp[i] = (Math.random() - 0.5) * 1.6 * (r0[i] / 20)  // 略呈盘状，越靠外越松散
    rate[i] = 0.22 + Math.random() * 0.30
    // 初始让各颗粒散布在不同进度上，否则一开场会是一圈整齐的环同时往里掉
    prog[i] = initial ? Math.random() : 0
  }

  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
  geo.setAttribute('aSize', new THREE.BufferAttribute(aSize, 1))
  geo.setAttribute('aAlpha', new THREE.BufferAttribute(aAlpha, 1))

  const mat = new THREE.ShaderMaterial({
    uniforms: {
      // 用 new THREE.Color(字符串) 而不是 new Color(r/255, g/255, b/255)：
      // 后者是把 sRGB 数值直接当线性色用，渲染出来会淡一大截。
      // 传字符串时 three 会按 sRGB 解释并转到线性工作空间，正好和片元着色器末尾的
      // colorspace_fragment 对上，出来的才是外观色本身。
      uColor: { value: new THREE.Color(hexToRgb(brandColor) ? brandColor : '#409eff') },
      uScale: { value: 620 },
      uOpacity: { value: 0.75 },
    },
    vertexShader: `
      attribute float aSize; attribute float aAlpha;
      uniform float uScale;
      varying float vA;
      void main() {
        vA = aAlpha;
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        // 屏占恒定，不做透视衰减（除 -mv.z）。粒子是从远处一路旋转到镜头附近的，
        // 带透视的话近处那几颗会涨到几百像素、糊掉整个画面。
        gl_PointSize = clamp(aSize * uScale, 0.5, 60.0);
        gl_Position = projectionMatrix * mv;
      }`,
    // 圆形软边。末尾两个 include 不能省：ShaderMaterial 不会自动做色调映射与色彩空间转换，
    // 少了它们星尘的颜色会和场景里其它东西对不上（本场景开着 ACES）。
    fragmentShader: `
      uniform vec3 uColor; uniform float uOpacity; varying float vA;
      void main() {
        vec2 d = gl_PointCoord - vec2(0.5);
        float f = 1.0 - smoothstep(0.0, 0.5, length(d));
        gl_FragColor = vec4(uColor, f * f * vA * uOpacity);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
    // 用普通 alpha 混合而不是加法混合。
    // 加法下密度不均必然出问题：中心重叠十几倍、边缘才一两倍，中心一定会累加过头、
    // 经 ACES 去饱和后烧成白色，外观色就丢了。alpha 混合的重叠是渐近的——
    // 再密也只会逼近 uColor 本身，数学上不可能超过它，正好是「填满即外观色」要的性质。
    transparent: true, blending: THREE.NormalBlending, depthWrite: false,
  })

  const points = new THREE.Points(geo, mat)
  points.frustumCulled = false          // 粒子会跑出初始包围盒，交给视锥剔除会被整批剔掉

  return {
    points,
    /**
     * 视口变化时重算点尺寸系数，否则缩放窗口后粒子会跟着变大变小。
     * 除以 REF_DIST 是把「世界单位」换算成默认机位下的屏占——
     * 因为顶点着色器里不做透视衰减，得有个固定基准距离来定标。
     */
    setViewport(h, fov) {
      mat.uniforms.uScale.value = h / (2 * Math.tan(fov * Math.PI / 360)) / REF_DIST
    },
    /** active 0→1：可见粒子从 0 涨到全部 */
    update(dt, activeFrac = 1) {
      const active = Math.floor(count * clamp(activeFrac, 0, 1))
      for (let i = 0; i < active; i++) {
        prog[i] += dt * rate[i]
        if (prog[i] >= 1) { respawn(i, false); continue }
        const p = prog[i]
        const fall = Math.pow(p, 1.4)
        const r = r0[i] * (1 - fall)
        const th = ang0[i] + (1 / Math.pow(Math.max(0.05, 1 - fall), 1.2) - 1) * 1.1
        const o = i * 3
        pos[o] = Math.cos(th) * r
        pos[o + 1] = yAmp[i] * (1 - fall)     // 越靠近越贴向赤道面
        pos[o + 2] = Math.sin(th) * r
        // 出生淡入；贴近视界时淡出，像是被吃掉而不是糊在洞口。
        // 淡出区间要窄：留太宽会在视界外面箍出一圈明显的暗环，把「填满」破掉。
        aAlpha[i] = smooth(0, 0.06, p) * smooth(HORIZON_R * 0.75, HORIZON_R * 1.35, r)
      }
      for (let i = active; i < count; i++) aAlpha[i] = 0
      geo.attributes.position.needsUpdate = true
      geo.attributes.aAlpha.needsUpdate = true
    },
  }
}

/**
 * 造一个黑洞。返回 group（挂到场景即可）与需要 dispose 的纹理。
 * horizon 就是要拿去做出场动画和点击射线的那颗球。
 */
export function createBlackHole(brandColor) {
  const group = new THREE.Group()

  // ① 事件视界。
  // MeshBasicMaterial 不受光照影响，贴上去就是纯黑，正好把背后的星空彻底吃掉。
  // 必须 DoubleSide：出场动画里它会放大到把相机吞进去，那时若只渲染正面，
  // 从球内部看会被背面剔除掉，画面反而透出后面的星空，白忙一场。
  const horizon = new THREE.Mesh(
    new THREE.SphereGeometry(HORIZON_R, 48, 32),
    new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.DoubleSide })
  )
  group.add(horizon)

  // ② 光子环 + 透镜弧。
  // billboard 落在原点，中心那圈正好被视界球挡住（球面比它近），只露出外面那圈光。
  const ringTex = makePhotonRingTexture(brandColor)
  const ring = new THREE.Sprite(new THREE.SpriteMaterial({
    map: ringTex, transparent: true, blending: THREE.AdditiveBlending,
    depthWrite: false, depthTest: true,
  }))
  ring.scale.set(RING_SPAN, RING_SPAN, 1)
  group.add(ring)

  // ③ 吸积盘：赤道面上的环，加法混合（自己发光的天体不参与受光）
  const diskGeo = new THREE.RingGeometry(DISK_IN, DISK_OUT, 160, 1)
  diskGeo.rotateX(-Math.PI / 2)
  const diskTex = makeAccretionDiskTexture(brandColor)
  const disk = new THREE.Mesh(diskGeo, new THREE.MeshBasicMaterial({
    map: diskTex, transparent: true, side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending, depthWrite: false,
  }))
  group.add(disk)

  return { group, horizon, disk, ring, textures: [ringTex, diskTex] }
}
