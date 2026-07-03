<template>
  <div class="particle-container" ref="containerRef">
    <canvas ref="canvasRef" />
    <slot />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'

const canvasRef = ref(null)
const containerRef = ref(null)
let ctx = null
let width = 0
let height = 0
let animationId = null

const particles = []
const PARTICLE_COUNT = 150
const MOUSE_RADIUS = 130

let mouseX = -9999
let mouseY = -9999
let targetX = -9999
let targetY = -9999
let mouseSpeed = 0
let prevMouseX = -9999
let prevMouseY = -9999

function getColors(isDark) {
  if (isDark) {
    return {
      main: '180, 200, 255',
      glow: '200, 180, 255',
      bright: '220, 220, 255',
      connection: '180, 200, 255'
    }
  } else {
    return {
      main: '100, 150, 255',
      glow: '120, 180, 255',
      bright: '150, 200, 255',
      connection: '100, 150, 255'
    }
  }
}

class Particle {
  constructor() {
    this.x = Math.random() * width
    this.y = Math.random() * height
    this.homeX = this.x
    this.homeY = this.y
    this.size = Math.random() * 4 + 2
    this.offsetX = 0
    this.offsetY = 0
    this.vx = 0
    this.vy = 0
    this.colorShift = Math.random() * 40 - 20
  }

  update() {
    const dx = mouseX - this.x
    const dy = mouseY - this.y
    const dist = Math.sqrt(dx * dx + dy * dy)

    if (dist < MOUSE_RADIUS && mouseX > -100 && mouseY > -100) {
      const force = (1 - dist / MOUSE_RADIUS) * 8
      const angle = Math.atan2(dy, dx)
      const speedInfluence = Math.min(1, mouseSpeed / 20)
      const pushForce = force * (1 + speedInfluence * 2)

      this.vx += Math.cos(angle) * pushForce * 0.25
      this.vy += Math.sin(angle) * pushForce * 0.25

      if (dist < 30) {
        this.vx *= 0.85
        this.vy *= 0.85
      }
    }

    this.vx += (0 - this.vx) * 0.025
    this.vy += (0 - this.vy) * 0.025

    this.x += this.vx
    this.y += this.vy

    if (this.x < -50) { this.x = -50; this.vx *= -0.5 }
    if (this.x > width + 50) { this.x = width + 50; this.vx *= -0.5 }
    if (this.y < -50) { this.y = -50; this.vy *= -0.5 }
    if (this.y > height + 50) { this.y = height + 50; this.vy *= -0.5 }
  }

  draw(ctx, colors, isDark) {
    const distToMouse = Math.sqrt(
      (mouseX - this.x) ** 2 + (mouseY - this.y) ** 2
    )
    const influence = Math.max(0, 1 - distToMouse / MOUSE_RADIUS)

    const baseR = parseInt(colors.main.split(',')[0]) + this.colorShift * 0.3
    const baseG = parseInt(colors.main.split(',')[1]) + this.colorShift * 0.2
    const baseB = parseInt(colors.main.split(',')[2]) + this.colorShift * 0.3
    const colorStr = `${Math.max(0, Math.min(255, baseR))}, ${Math.max(0, Math.min(255, baseG))}, ${Math.max(0, Math.min(255, baseB))}`

    // 深色主题透明度更低
    const alpha = isDark
      ? 0.08 + influence * 0.3
      : 0.2 + influence * 0.5

    // 光晕
    const glowSize = this.size * (1 + influence * 1.8)
    const gradient = ctx.createRadialGradient(
      this.x, this.y, 0,
      this.x, this.y, glowSize * 2
    )
    gradient.addColorStop(0, `rgba(${colorStr}, ${alpha * 0.2})`)
    gradient.addColorStop(1, `rgba(${colorStr}, 0)`)
    ctx.fillStyle = gradient
    ctx.beginPath()
    ctx.arc(this.x, this.y, glowSize * 2, 0, Math.PI * 2)
    ctx.fill()

    // 粒子
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(${colorStr}, ${alpha})`
    ctx.fill()

    // 高亮
    if (influence > 0.2 && distToMouse < 50) {
      ctx.beginPath()
      ctx.arc(this.x, this.y, this.size * 0.6, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(255, 255, 255, ${influence * 0.2})`
      ctx.fill()
    }
  }
}

function drawConnections(ctx, colors, isDark) {
  const colorStr = colors.connection
  const maxDist = 80

  const nearby = particles.filter(p => {
    const dx = mouseX - p.x
    const dy = mouseY - p.y
    return Math.sqrt(dx * dx + dy * dy) < MOUSE_RADIUS * 1.5
  })

  for (let i = 0; i < nearby.length; i++) {
    for (let j = i + 1; j < nearby.length; j++) {
      const dx = nearby[i].x - nearby[j].x
      const dy = nearby[i].y - nearby[j].y
      const dist = Math.sqrt(dx * dx + dy * dy)

      if (dist < maxDist) {
        const alpha = (1 - dist / maxDist) * 0.08
        ctx.beginPath()
        ctx.moveTo(nearby[i].x, nearby[i].y)
        ctx.lineTo(nearby[j].x, nearby[j].y)
        ctx.strokeStyle = `rgba(${colorStr}, ${alpha})`
        ctx.lineWidth = 0.5
        ctx.stroke()
      }
    }
  }
}

function initParticles() {
  particles.length = 0
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const p = new Particle()
    p.x = Math.random() * width
    p.y = Math.random() * height
    p.homeX = p.x
    p.homeY = p.y
    particles.push(p)
  }
}

function onMouseMove(e) {
  const rect = containerRef.value.getBoundingClientRect()
  targetX = e.clientX - rect.left
  targetY = e.clientY - rect.top

  if (prevMouseX > -100) {
    const dx = targetX - prevMouseX
    const dy = targetY - prevMouseY
    mouseSpeed = Math.sqrt(dx * dx + dy * dy)
  }
  prevMouseX = targetX
  prevMouseY = targetY
}

function onMouseLeave() {
  targetX = -9999
  targetY = -9999
  prevMouseX = -9999
  prevMouseY = -9999
  mouseSpeed = 0
}

function onResize() {
  const container = containerRef.value
  if (!container) return
  width = container.clientWidth
  height = container.clientHeight
  const canvas = canvasRef.value
  if (!canvas) return
  const dpr = window.devicePixelRatio || 1
  canvas.width = width * dpr
  canvas.height = height * dpr
  canvas.style.width = width + 'px'
  canvas.style.height = height + 'px'
  ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)
  initParticles()
}

function animate() {
  if (!ctx) return

  mouseX += (targetX - mouseX) * 0.12
  mouseY += (targetY - mouseY) * 0.12

  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
  const colors = getColors(isDark)

  ctx.clearRect(0, 0, width, height)

  for (const p of particles) {
    p.update()
  }

  drawConnections(ctx, colors, isDark)

  for (const p of particles) {
    p.draw(ctx, colors, isDark)
  }

  animationId = requestAnimationFrame(animate)
}

function initCanvas() {
  const container = containerRef.value
  const canvas = canvasRef.value
  if (!container || !canvas) return

  width = container.clientWidth
  height = container.clientHeight

  const dpr = window.devicePixelRatio || 1
  canvas.width = width * dpr
  canvas.height = height * dpr
  canvas.style.width = width + 'px'
  canvas.style.height = height + 'px'

  ctx = canvas.getContext('2d')
  ctx.scale(dpr, dpr)

  initParticles()
}

onMounted(() => {
  nextTick(() => {
    initCanvas()
    animate()

    const container = containerRef.value
    container.addEventListener('mousemove', onMouseMove)
    container.addEventListener('mouseleave', onMouseLeave)
    window.addEventListener('resize', onResize)
  })
})

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  const container = containerRef.value
  if (container) {
    container.removeEventListener('mousemove', onMouseMove)
    container.removeEventListener('mouseleave', onMouseLeave)
  }
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
.particle-container {
  position: relative;
  width: 100%;
  min-height: 100vh;
  overflow: hidden;
}

.particle-container canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
}

.particle-container > :not(canvas) {
  position: relative;
  z-index: 2;
}
</style>