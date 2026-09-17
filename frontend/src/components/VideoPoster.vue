<template>
  <!-- 视频海报 = 真实帧截图（2026-09-05 用户定调：预览界面用视频里的帧截图，不是模板色块）
       用原生渲染器 drawFrame 画视频 40% 处（跳过钩子，落在演示/例题镜头）的一帧 -->
  <div class="vp-frame">
    <canvas ref="cv" class="vp-canvas"></canvas>
    <div class="vp-overlay"><slot /></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { drawFrame } from '@/utils/videoRender'

const props = defineProps({
  video: { type: Object, default: null },
})

const cv = ref(null)
let ro = null

const hasScript = computed(() => {
  const s = props.video && props.video.script
  return !!(s && ((Array.isArray(s.scenes) && s.scenes.length) || (Array.isArray(s.sections) && s.sections.length)))
})

function paint() {
  const canvas = cv.value
  if (!canvas || !canvas.parentElement) return
  const rect = canvas.parentElement.getBoundingClientRect()
  if (rect.width < 4 || rect.height < 4) return
  const dpr = Math.min(2, window.devicePixelRatio || 1)
  const w = Math.round(rect.width * dpr)
  const h = Math.round(rect.height * dpr)
  if (canvas.width !== w) canvas.width = w
  if (canvas.height !== h) canvas.height = h
  if (!hasScript.value || !props.video) return
  const dur = Number(props.video.audio_duration || 0) || 90
  const t = Math.min(dur, Math.max(4, dur * 0.4))
  try {
    drawFrame(canvas.getContext('2d'), props.video, t, w, h)
  } catch (e) {
    console.error('VideoPoster paint:', e)
  }
}

onMounted(() => {
  nextTick(() => {
    paint()
    if (typeof ResizeObserver !== 'undefined' && cv.value && cv.value.parentElement) {
      ro = new ResizeObserver(() => paint())
      ro.observe(cv.value.parentElement)
    } else {
      window.addEventListener('resize', paint)
    }
  })
})

onUnmounted(() => {
  if (ro) ro.disconnect()
  window.removeEventListener('resize', paint)
})
</script>

<style scoped>
.vp-frame {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: linear-gradient(160deg, #0f1722 0%, #142030 60%, #101a28 100%);
}
.vp-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.vp-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
</style>