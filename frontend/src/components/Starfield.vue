<template>
  <canvas ref="cv" class="starfield-canvas" aria-hidden="true"></canvas>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()
const cv = ref(null)
let ctx = null
let w = 0, h = 0, dpr = 1
let stars = []
let meteors = []
let rafId = null
let last = 0
let spawnTimer = null
// 指针视差（归一化 -1..1，目标/当前）
let tx = 0, ty = 0, cx = 0, cy = 0
const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
const finePointer = typeof window !== 'undefined' && window.matchMedia('(hover: hover) and (pointer: fine)').matches

function makeStars() {
  const count = Math.min(240, Math.max(80, Math.floor((w * h) / 8000)))
  stars = Array.from({ length: count }, () => ({
    x: Math.random(),
    y: Math.random(),
    z: Math.random(), // 0 近层（大/快）→ 1 远层（小/慢）
    r: 0.5 + Math.random() * 1.4,
    tw: Math.random() * Math.PI * 2,
    ts: 0.4 + Math.random() * 1.6,
  }))
}

function resize() {
  const parent = cv.value.parentElement
  if (!parent) return
  dpr = Math.min(2, window.devicePixelRatio || 1)
  w = parent.clientWidth
  h = parent.clientHeight
  cv.value.width = Math.max(1, w * dpr)
  cv.value.height = Math.max(1, h * dpr)
  cv.value.style.width = w + 'px'
  cv.value.style.height = h + 'px'
  ctx = cv.value.getContext('2d')
  makeStars()
}

function palette() {
  return themeStore.currentTheme === 'dark'
    ? { star: '255,255,255', tint: '125,211,252' }
    : { star: '60,90,160', tint: '64,158,255' }
}

function spawnMeteor() {
  meteors.push({
    x: Math.random() * w * 0.9 + w * 0.1,
    y: Math.random() * h * 0.35,
    vx: -(3 + Math.random() * 5),
    vy: 1.6 + Math.random() * 2.4,
    life: 1,
  })
}

function meteorShower() {
  for (let i = 0; i < 10; i++) setTimeout(spawnMeteor, i * 130)
}

function frame(now) {
  rafId = requestAnimationFrame(frame)
  const dt = last ? Math.min(0.05, (now - last) / 1000) : 0.016
  last = now
  const t = now / 1000
  const p = palette()
  ctx.clearRect(0, 0, w, h)

  // 指针视差平滑跟随
  cx += (tx - cx) * 0.045
  cy += (ty - cy) * 0.045

  for (const s of stars) {
    const depth = 1 - s.z
    const ox = cx * 30 * depth
    const oy = cy * 20 * depth
    const x = (s.x * w + ox + w) % w
    const y = (s.y * h + oy + h) % h
    const twinkle = 0.5 + 0.5 * Math.sin(t * s.ts + s.tw)
    const near = s.z < 0.3
    ctx.fillStyle = `rgba(${near ? p.tint : p.star}, ${(0.18 + 0.6 * twinkle * (1 - s.z)).toFixed(3)})`
    ctx.beginPath()
    ctx.arc(x, y, s.r * (0.7 + depth * 0.6), 0, Math.PI * 2)
    ctx.fill()
  }

  // 流星
  meteors = meteors.filter((m) => m.life > 0)
  for (const m of meteors) {
    m.x += m.vx * 60 * dt
    m.y += m.vy * 60 * dt
    m.life -= dt / 1.15
    const a = Math.max(0, m.life)
    const tailX = m.x - m.vx * 14
    const tailY = m.y - m.vy * 14
    const grad = ctx.createLinearGradient(m.x, m.y, tailX, tailY)
    grad.addColorStop(0, `rgba(${p.tint}, ${a})`)
    grad.addColorStop(1, `rgba(${p.tint}, 0)`)
    ctx.strokeStyle = grad
    ctx.lineWidth = 1.6
    ctx.beginPath()
    ctx.moveTo(m.x, m.y)
    ctx.lineTo(tailX, tailY)
    ctx.stroke()
  }
}

function onMove(e) {
  tx = (e.clientX / window.innerWidth) * 2 - 1
  ty = (e.clientY / window.innerHeight) * 2 - 1
}

function onResize() { resize() }

onMounted(() => {
  resize()
  if (reduced) {
    frame(performance.now()) // 静态渲染一帧
    if (rafId) cancelAnimationFrame(rafId)
    rafId = null
    return
  }
  rafId = requestAnimationFrame(frame)
  if (finePointer) window.addEventListener('mousemove', onMove, { passive: true })
  window.addEventListener('resize', onResize)
  spawnTimer = setInterval(() => { if (Math.random() < 0.6) spawnMeteor() }, 4200)
})

onBeforeUnmount(() => {
  if (rafId) cancelAnimationFrame(rafId)
  if (spawnTimer) clearInterval(spawnTimer)
  window.removeEventListener('mousemove', onMove)
  window.removeEventListener('resize', onResize)
})

defineExpose({ meteorShower })
</script>

<style scoped>
.starfield-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}
</style>
