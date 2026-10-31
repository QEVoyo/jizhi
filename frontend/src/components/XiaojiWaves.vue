<template>
  <canvas ref="canvas" class="xiaoji-waves-canvas" :class="{ active }" aria-hidden="true"></canvas>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  active: { type: Boolean, default: false },
})

const canvas = ref(null)
let ctx = null
let raf = null
let ro = null
let w = 0
let h = 0
let dpr = 1
let amp = 4
let phase = 0
let last = 0

const LINES = 6

function resize() {
  const el = canvas.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  dpr = Math.min(2, window.devicePixelRatio || 1)
  w = Math.max(1, rect.width)
  h = Math.max(1, rect.height)
  el.width = Math.round(w * dpr)
  el.height = Math.round(h * dpr)
  if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

function draw(now) {
  if (!ctx) return
  const dt = Math.min(50, now - (last || now))
  last = now
  const target = props.active ? 1 : 0.45
  amp += (target - amp) * Math.min(1, dt / 180)
  phase += (props.active ? 0.0046 : 0.0012) * dt

  const cx = w / 2
  const cy = h / 2 - 10
  const t = now / 1000

  ctx.clearRect(0, 0, w, h)
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'

  for (const side of [-1, 1]) {
    for (let i = 0; i < LINES; i++) {
      // 起点贴近小基，中段向外鼓出一条长弧；再叠一层会走的揉动。
      // 不是竖直直线，也不是闭合圆环。
      const baseX = cx + side * (132 + i * 10)
      const len = 232 + i * 6
      const drift = Math.sin(t * (props.active ? 1.0 : 0.3) + i * 1.1 + (side > 0 ? 0.7 : 0)) * 2
      const depth = (18 + 22 * amp + i * 2) * (0.88 + 0.12 * Math.sin(phase * 0.9 + i * 0.8))
      const wig = (2.5 + 6 * amp) * (0.7 + i * 0.05)
      const y0 = cy - len / 2 + drift
      const y1 = cy + len / 2 + drift

      ctx.beginPath()
      let first = true
      for (let k = 0; k <= 100; k++) {
        const u = k / 100
        const y = y0 + (y1 - y0) * u
        const env = Math.sin(Math.PI * u)
        const arc = depth * env
        const squirm = Math.sin(u * Math.PI * 2.2 + phase * (1 + i * 0.08) + i * 1.4) * wig * env
        const squirm2 = Math.sin(u * Math.PI * 4.8 - phase * 0.7 + i * 0.6) * wig * 0.35 * env
        const x = baseX + side * (arc + squirm + squirm2)
        if (first) {
          ctx.moveTo(x, y)
          first = false
        } else {
          ctx.lineTo(x, y)
        }
      }
      ctx.lineWidth = 0.95 + i * 0.08
      ctx.globalAlpha = 0.16 + i * 0.06
      ctx.strokeStyle = 'rgb(142, 180, 255)'
      ctx.shadowColor = 'rgba(100, 150, 255, .55)'
      ctx.shadowBlur = props.active ? 7 : 4
      ctx.stroke()
    }
  }
  ctx.globalAlpha = 1
  ctx.shadowBlur = 0
  raf = requestAnimationFrame(draw)
}

function onVis() {
  if (document.hidden) {
    if (raf) cancelAnimationFrame(raf)
    raf = null
  } else if (!raf) {
    last = 0
    raf = requestAnimationFrame(draw)
  }
}

onMounted(() => {
  ctx = canvas.value?.getContext('2d') || null
  resize()
  if (window.ResizeObserver) {
    ro = new ResizeObserver(resize)
    ro.observe(canvas.value)
  }
  document.addEventListener('visibilitychange', onVis)
  raf = requestAnimationFrame(draw)
})

watch(() => props.active, (v) => {
  if (v) last = 0
})

onBeforeUnmount(() => {
  if (raf) cancelAnimationFrame(raf)
  raf = null
  if (ro) ro.disconnect()
  ro = null
  document.removeEventListener('visibilitychange', onVis)
})
</script>

<style scoped>
.xiaoji-waves-canvas {
  position: absolute;
  left: 50%;
  top: calc(50% - 18px);
  width: min(640px, 92vw);
  height: 360px;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 0;
  /* 不说话时完全不显示，避免画面太乱 */
  opacity: 0;
  transition: opacity .22s ease;
}
.xiaoji-waves-canvas.active { opacity: 1; }
</style>
