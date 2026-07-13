<template>
  <div class="demo-page">
    <!-- ===== 左下角礼炮喷射 ===== -->
    <div
      v-for="p in leftBurst"
      :key="'lp-' + p.id"
      class="burst-item"
      :style="{
        position: 'fixed',
        left: p.x + 'px',
        top: p.y + 'px',
        opacity: p.opacity,
        color: p.color,
        fontSize: p.size + 'px',
        zIndex: 8,
        pointerEvents: 'none',
        transform: `rotate(${p.rot}deg)`,
      }"
    >
      {{ p.icon }}
    </div>

    <!-- ===== 右下角礼炮喷射 ===== -->
    <div
      v-for="p in rightBurst"
      :key="'rp-' + p.id"
      class="burst-item"
      :style="{
        position: 'fixed',
        left: p.x + 'px',
        top: p.y + 'px',
        opacity: p.opacity,
        color: p.color,
        fontSize: p.size + 'px',
        zIndex: 8,
        pointerEvents: 'none',
        transform: `rotate(${p.rot}deg)`,
      }"
    >
      {{ p.icon }}
    </div>

    <!-- ===== 闪光 ===== -->
    <div v-if="flash" class="flash-overlay" :style="{ opacity: flashOpacity }" />

    <div class="header">
      <h1>🎊 双炮喷射</h1>
      <p>点击领取，1秒完成</p>
    </div>

    <button class="btn" ref="btnRef" @click="handleClaim">
      🎁 领取积分
    </button>

    <!-- ===== 积分栏 ===== -->
    <div class="score-bar" ref="scoreBarRef">
      <span>🏅</span>
      <span class="num" ref="scoreRef">{{ score }}</span>
      <span style="opacity:0.1">|</span>
      <span>⭐</span>
      <span class="num level" ref="levelScoreRef">{{ levelScore }}</span>
    </div>

    <!-- ===== 金币 ===== -->
    <div
      v-if="flying"
      class="coin"
      :style="{
        left: coinX + 'px',
        top: coinY + 'px',
        opacity: coinOpacity,
        transform: `scale(${coinScale}) rotate(${coinRotate}deg)`,
      }"
    >
      🪙
    </div>

    <!-- ===== 毛玻璃通知 ===== -->
    <div v-if="showGlass" class="glass" @click="showGlass = false">
      <div class="glass-box">
        <div class="g-icon">🎊</div>
        <div class="g-title">领取成功！</div>
        <div class="g-points">+{{ lastPoints }}</div>
        <div class="g-detail">
          段位 <span class="gold">+{{ lastRank }}</span>
          · 等级 <span class="green">+{{ lastLevel }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'

const score = ref(128)
const levelScore = ref(42)
const flying = ref(false)
const flash = ref(false)
const showGlass = ref(false)

const leftBurst = ref([])
const rightBurst = ref([])

const coinX = ref(0)
const coinY = ref(0)
const coinOpacity = ref(1)
const coinScale = ref(0.3)
const coinRotate = ref(0)

const flashOpacity = ref(0)

let lastPoints = ref(0)
let lastRank = ref(0)
let lastLevel = ref(0)

const btnRef = ref(null)
const scoreBarRef = ref(null)
const scoreRef = ref(null)
const levelScoreRef = ref(null)

let animId = null
let timer = null

function handleClaim() {
  const btn = btnRef.value
  const bar = scoreBarRef.value
  if (!btn || !bar) return

  const bx = btn.getBoundingClientRect()
  const br = bar.getBoundingClientRect()

  const startX = bx.left + bx.width / 2
  const startY = bx.top + bx.height / 2
  const endX = br.left + br.width - 30
  const endY = br.top + br.height / 2

  lastPoints.value = 10
  lastRank.value = 8
  lastLevel.value = 2

  // 喷射
  fireLeft()
  fireRight()

  // 1秒后金币飞出
  timer = setTimeout(() => {
    leftBurst.value = []
    rightBurst.value = []
    flyCoin(startX, startY, endX, endY)
  }, 1000)
}

function fireLeft() {
  const items = []
  const icons = ['✦', '✧', '✦', '✧', '✦', '✧', '✦', '✧']
  const colors = ['#FFD700', '#FF6B6B', '#FF1493', '#00BFFF', '#FFA500', '#FF4500', '#FFD700', '#7B68EE']

  const cx = 0
  const cy = window.innerHeight * 0.75

  for (let i = 0; i < 30; i++) {
    const angle = -0.3 + Math.random() * 1.2
    const dist = 80 + Math.random() * 500
    items.push({
      id: Math.random(),
      x: cx + Math.random() * 30,
      y: cy - 20 + Math.random() * 40,
      targetX: cx + Math.cos(angle) * dist,
      targetY: cy + Math.sin(angle) * dist * 0.7 - 200,
      opacity: 1,
      color: colors[Math.floor(Math.random() * colors.length)],
      size: 14 + Math.random() * 24,
      icon: icons[Math.floor(Math.random() * icons.length)],
      rot: Math.random() * 360,
    })
  }

  leftBurst.value = items
  animateBurst('left')
}

function fireRight() {
  const items = []
  const icons = ['✦', '✧', '✦', '✧', '✦', '✧', '✦', '✧']
  const colors = ['#FFD700', '#FF6B6B', '#FF1493', '#00BFFF', '#FFA500', '#FF4500', '#FFD700', '#7B68EE']

  const cx = window.innerWidth
  const cy = window.innerHeight * 0.75

  for (let i = 0; i < 30; i++) {
    const angle = Math.PI - 0.3 + Math.random() * 1.2
    const dist = 80 + Math.random() * 500
    items.push({
      id: Math.random(),
      x: cx - Math.random() * 30,
      y: cy - 20 + Math.random() * 40,
      targetX: cx + Math.cos(angle) * dist,
      targetY: cy + Math.sin(angle) * dist * 0.7 - 200,
      opacity: 1,
      color: colors[Math.floor(Math.random() * colors.length)],
      size: 14 + Math.random() * 24,
      icon: icons[Math.floor(Math.random() * icons.length)],
      rot: Math.random() * 360,
    })
  }

  rightBurst.value = items
  animateBurst('right')
}

function animateBurst(side) {
  const dur = 900
  const start = performance.now()

  function step(time) {
    const p = Math.min((time - start) / dur, 1)
    const ease = p

    if (side === 'left' || side === 'both') {
      leftBurst.value = leftBurst.value.map(item => ({
        ...item,
        x: item.x + (item.targetX - item.x) * 0.05,
        y: item.y + (item.targetY - item.y) * 0.05,
        opacity: 1 - ease * 0.7,
        rot: item.rot + 3,
      }))
    }

    if (side === 'right' || side === 'both') {
      rightBurst.value = rightBurst.value.map(item => ({
        ...item,
        x: item.x + (item.targetX - item.x) * 0.05,
        y: item.y + (item.targetY - item.y) * 0.05,
        opacity: 1 - ease * 0.7,
        rot: item.rot + 3,
      }))
    }

    if (p < 1) {
      animId = requestAnimationFrame(step)
    }
  }
  animId = requestAnimationFrame(step)
}

function flyCoin(sx, sy, ex, ey) {
  flying.value = true
  coinX.value = sx - 20
  coinY.value = sy - 20
  coinOpacity.value = 1
  coinScale.value = 0.3
  coinRotate.value = 0

  const dur = 600
  const start = performance.now()

  function step(time) {
    const p = Math.min((time - start) / dur, 1)
    const ease = p

    const arc = Math.sin(p * Math.PI) * 50
    coinX.value = sx + (ex - sx) * ease - 20
    coinY.value = sy + (ey - sy) * ease - arc - 20
    coinScale.value = 0.3 + ease * 0.8
    coinRotate.value = p * 720

    if (p < 1) {
      animId = requestAnimationFrame(step)
    } else {
      flying.value = false
      coinOpacity.value = 0

      // 闪光
      flash.value = true
      flashOpacity.value = 1
      let fp = 0
      const fstart = performance.now()
      function flashStep(t) {
        fp = (t - fstart) / 400
        if (fp >= 1) { flash.value = false; flashOpacity.value = 0; return }
        flashOpacity.value = 1 - fp
        requestAnimationFrame(flashStep)
      }
      requestAnimationFrame(flashStep)

      // 积分跳动
      if (scoreRef.value) {
        scoreRef.value.style.transform = 'scale(1.5)'
        scoreRef.value.style.color = '#FFD700'
        setTimeout(() => {
          if (scoreRef.value) {
            scoreRef.value.style.transform = 'scale(1)'
            scoreRef.value.style.color = ''
          }
        }, 300)
      }
      if (levelScoreRef.value) {
        levelScoreRef.value.style.transform = 'scale(1.5)'
        levelScoreRef.value.style.color = '#6BCB77'
        setTimeout(() => {
          if (levelScoreRef.value) {
            levelScoreRef.value.style.transform = 'scale(1)'
            levelScoreRef.value.style.color = ''
          }
        }, 300)
      }

      score.value += lastRank.value
      levelScore.value += lastLevel.value

      setTimeout(() => {
        showGlass.value = true
        setTimeout(() => { showGlass.value = false }, 2000)
      }, 300)
    }
  }
  animId = requestAnimationFrame(step)
}

onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId)
  if (timer) clearTimeout(timer)
})
</script>

<style scoped>
.demo-page {
  min-height: 100vh;
  background: #0a0a18;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-family: system-ui, sans-serif;
  overflow: hidden;
  position: relative;
}

.header {
  text-align: center;
  z-index: 10;
  margin-bottom: 30px;
}
.header h1 {
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, #FFD700, #FF6B00);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.header p {
  color: rgba(255,255,255,0.3);
  font-size: 13px;
}

.btn {
  z-index: 10;
  padding: 16px 48px;
  font-size: 18px;
  font-weight: 700;
  border: none;
  border-radius: 20px;
  background: linear-gradient(135deg, #FFD700, #FF8C00);
  color: #1a1a2e;
  cursor: pointer;
  box-shadow: 0 4px 30px rgba(255,215,0,0.25);
  transition: all 0.2s;
}
.btn:hover {
  transform: scale(1.03);
  box-shadow: 0 6px 40px rgba(255,215,0,0.35);
}

/* ===== 积分栏 ===== */
.score-bar {
  position: fixed;
  top: 20px;
  right: 24px;
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 6px;
  z-index: 100;
  color: rgba(255,255,255,0.5);
  font-size: 14px;
}
.score-bar .num {
  color: #FFD700;
  font-size: 20px;
  font-weight: 800;
  transition: all 0.2s;
  min-width: 24px;
}
.score-bar .num.level {
  color: #6BCB77;
}

/* ===== 闪光 ===== */
.flash-overlay {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: radial-gradient(circle, rgba(255,255,255,0.5), rgba(255,215,0,0.1));
  pointer-events: none;
}

/* ===== 金币 ===== */
.coin {
  position: fixed;
  z-index: 20;
  pointer-events: none;
  font-size: 48px;
  filter: drop-shadow(0 0 30px rgba(255,215,0,0.5));
}

/* ===== 毛玻璃通知 ===== */
.glass {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.3);
  backdrop-filter: blur(6px);
}
.glass-box {
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(32px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 28px;
  padding: 32px 48px;
  text-align: center;
  animation: pop 0.4s ease;
}
@keyframes pop {
  0% { transform: scale(0.8); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
.g-icon { font-size: 40px; }
.g-title { font-size: 18px; font-weight: 600; color: rgba(255,255,255,0.8); }
.g-points {
  font-size: 44px;
  font-weight: 900;
  background: linear-gradient(135deg, #FFD700, #FF6B00);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.g-detail {
  font-size: 14px;
  color: rgba(255,255,255,0.4);
}
.gold { color: #FFD700; font-weight: 600; }
.green { color: #6BCB77; font-weight: 600; }
</style>