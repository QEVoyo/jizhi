<template>
  <div class="bubble-container">
    <div
      v-for="(bubble, index) in bubbles"
      :key="index"
      class="bubble"
      :style="{
        width: bubble.size + 'px',
        height: bubble.size + 'px',
        left: bubble.x + '%',
        top: bubble.y + '%',
        animationDuration: bubble.duration + 's',
        animationDelay: bubble.delay + 's',
        opacity: bubble.opacity
      }"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const bubbles = ref([])

function generateBubbles() {
  const count = 40
  const newBubbles = []
  for (let i = 0; i < count; i++) {
    newBubbles.push({
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 30 + 10,
      duration: Math.random() * 15 + 10,
      delay: Math.random() * 10,
      opacity: Math.random() * 0.15 + 0.05
    })
  }
  bubbles.value = newBubbles
}

let mouseX = 0
let mouseY = 0

function onMouseMove(e) {
  mouseX = (e.clientX / window.innerWidth) * 100
  mouseY = (e.clientY / window.innerHeight) * 100

  document.querySelectorAll('.bubble').forEach((el, i) => {
    if (i < bubbles.value.length) {
      const baseX = bubbles.value[i].x
      const baseY = bubbles.value[i].y
      const dx = (mouseX - baseX) * 0.02
      const dy = (mouseY - baseY) * 0.02
      el.style.transform = `translate(${dx}px, ${dy}px)`
    }
  })
}

onMounted(() => {
  generateBubbles()
  window.addEventListener('mousemove', onMouseMove)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
})
</script>

<style scoped>
.bubble-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.bubble {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(
    circle at 30% 30%,
    rgba(255, 255, 255, 0.3),
    rgba(255, 255, 255, 0.05)
  );
  border: 1px solid rgba(255, 255, 255, 0.08);
  animation: floatUp linear infinite;
  transition: transform 0.1s ease-out;
  will-change: transform;
  pointer-events: none;
}

[data-theme="dark"] .bubble {
  background: radial-gradient(
    circle at 30% 30%,
    rgba(255, 255, 255, 0.08),
    rgba(255, 255, 255, 0.02)
  );
  border-color: rgba(255, 255, 255, 0.04);
}

@keyframes floatUp {
  0% {
    transform: translateY(100vh) scale(0.8);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    transform: translateY(-20vh) scale(1.2);
    opacity: 0;
  }
}
</style>