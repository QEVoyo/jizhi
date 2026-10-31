<template>
  <Teleport to="body">
    <div v-if="open" class="shot-overlay" @keydown.esc.stop="cancel">
      <div class="shot-stage" ref="stageRef"
           @pointerdown="onDown" @pointermove="onMove"
           @pointerup="onUp" @pointercancel="onUp">
        <img ref="imgRef" class="shot-img" :src="imageUrl" alt="" @load="onImgLoad" />
        <div v-if="sel && selW > 2 && selH > 2" class="shot-sel" :style="selStyle">
          <span class="shot-dim">{{ selW }} × {{ selH }}</span>
        </div>
        <div v-if="!sel" class="shot-tip">拖拽框选要解析的区域</div>
      </div>
      <div class="shot-bar">
        <span class="shot-hint">拖拽选择区域 · Esc 取消</span>
        <button class="shot-btn ghost" @click="cancel">取消</button>
        <button class="shot-btn primary" :disabled="!sel || selW < 8 || selH < 8" @click="confirm">
          确认截图
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  imageUrl: { type: String, default: '' },
})
const emit = defineEmits(['confirm', 'cancel'])

const stageRef = ref(null)
const imgRef = ref(null)
const imgRect = ref(null)          // 图片内容在屏幕上的实际显示矩形
const sel = ref(null)              // { x, y, w, h } 相对 stage
let dragStart = null
let dragging = false

const selW = computed(() => sel.value ? Math.round(sel.value.w) : 0)
const selH = computed(() => sel.value ? Math.round(sel.value.h) : 0)

const selStyle = computed(() => sel.value ? {
  left: sel.value.x + 'px', top: sel.value.y + 'px',
  width: sel.value.w + 'px', height: sel.value.h + 'px',
} : {})

function measure() {
  const stage = stageRef.value
  const img = imgRef.value
  if (!stage || !img) return
  const sw = stage.clientWidth
  const sh = stage.clientHeight
  const nw = img.naturalWidth || sw
  const nh = img.naturalHeight || sh
  const scale = Math.min(sw / nw, sh / nh)
  const dw = nw * scale
  const dh = nh * scale
  imgRect.value = {
    left: (sw - dw) / 2,
    top: (sh - dh) / 2,
    width: dw,
    height: dh,
    naturalWidth: nw,
    naturalHeight: nh,
    scale,
  }
}

function onImgLoad() {
  nextTick(measure)
}

function clampPoint(x, y) {
  const r = imgRect.value
  if (!r) return { x: 0, y: 0 }
  return {
    x: Math.min(r.left + r.width, Math.max(r.left, x)),
    y: Math.min(r.top + r.height, Math.max(r.top, y)),
  }
}

function stagePoint(e) {
  const box = stageRef.value?.getBoundingClientRect()
  return { x: e.clientX - (box?.left || 0), y: e.clientY - (box?.top || 0) }
}

function onDown(e) {
  if (e.button !== 0 || !imgRect.value) return
  const sp = stagePoint(e)
  const p = clampPoint(sp.x, sp.y)
  dragStart = p
  dragging = true
  sel.value = { x: p.x, y: p.y, w: 0, h: 0 }
  try { e.currentTarget.setPointerCapture(e.pointerId) } catch { /* ignore */ }
  e.preventDefault()
}

function onMove(e) {
  if (!dragging || !dragStart) return
  const sp = stagePoint(e)
  const p = clampPoint(sp.x, sp.y)
  sel.value = {
    x: Math.min(dragStart.x, p.x),
    y: Math.min(dragStart.y, p.y),
    w: Math.abs(p.x - dragStart.x),
    h: Math.abs(p.y - dragStart.y),
  }
}

function onUp(e) {
  if (!dragging) return
  dragging = false
  try { e.currentTarget.releasePointerCapture(e.pointerId) } catch { /* ignore */ }
  if (sel.value && (sel.value.w < 4 || sel.value.h < 4)) sel.value = null
}

function cancel() {
  sel.value = null
  emit('cancel')
}

async function confirm() {
  const r = imgRect.value
  const s = sel.value
  const img = imgRef.value
  if (!r || !s || !img) return
  // stage 坐标 → 原图像素
  const sx = (s.x - r.left) / r.scale
  const sy = (s.y - r.top) / r.scale
  const sw = s.w / r.scale
  const sh = s.h / r.scale
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(sw))
  canvas.height = Math.max(1, Math.round(sh))
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.drawImage(img, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height)
  const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.9))
  if (!blob) return
  sel.value = null
  emit('confirm', blob)
}

function onResize() {
  measure()
  sel.value = null
}

function onKey(e) {
  if (e.key === 'Escape') cancel()
}

watch(() => props.open, (open) => {
  if (open) {
    sel.value = null
    nextTick(measure)
    window.addEventListener('resize', onResize)
    window.addEventListener('keydown', onKey)
  } else {
    window.removeEventListener('resize', onResize)
    window.removeEventListener('keydown', onKey)
  }
})

onMounted(() => {
  if (props.open) {
    nextTick(measure)
    window.addEventListener('resize', onResize)
    window.addEventListener('keydown', onKey)
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.shot-overlay {
  position: fixed; inset: 0; z-index: 20000;
  background: #0a0f18;
  display: flex; flex-direction: column;
}
.shot-stage {
  position: relative; flex: 1; min-height: 0;
  overflow: hidden; cursor: crosshair; touch-action: none;
}
.shot-img {
  position: absolute; inset: 0; width: 100%; height: 100%;
  object-fit: contain; pointer-events: none; user-select: none;
}
.shot-sel {
  position: absolute;
  border: 1.5px dashed rgba(255, 255, 255, .95);
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, .58);
  background: rgba(255, 255, 255, .02);
  pointer-events: none;
}
.shot-sel::before, .shot-sel::after {
  content: ''; position: absolute; width: 8px; height: 8px;
  border: 1.5px solid #fff; background: #4f7cff;
}
.shot-sel::before { left: -5px; top: -5px; }
.shot-sel::after { right: -5px; bottom: -5px; }
.shot-dim {
  position: absolute; left: 50%; top: -26px; transform: translateX(-50%);
  padding: 2px 8px; border-radius: 7px; white-space: nowrap;
  font-size: 11px; color: #fff; background: rgba(15, 23, 42, .92);
  border: 1px solid rgba(255, 255, 255, .16);
}
.shot-tip {
  position: absolute; left: 50%; top: 22px; transform: translateX(-50%);
  padding: 7px 14px; border-radius: 10px;
  font-size: 13px; color: #e8ecf1; background: rgba(15, 23, 42, .9);
  border: 1px solid rgba(255, 255, 255, .14);
  pointer-events: none;
}
.shot-bar {
  flex: none; display: flex; align-items: center; gap: 10px;
  padding: 12px 20px; background: rgba(12, 18, 30, .96);
  border-top: 1px solid rgba(255, 255, 255, .10);
}
.shot-hint { margin-right: auto; font-size: 12px; color: #8b98ab; }
.shot-btn {
  padding: 8px 18px; border-radius: 9px; font-size: 13px;
  font-family: inherit; cursor: pointer;
  border: 1px solid rgba(255, 255, 255, .18); background: transparent;
  color: #dbe3ee;
}
.shot-btn.ghost:hover { background: rgba(255, 255, 255, .08); }
.shot-btn.primary {
  border-color: rgba(99, 132, 255, .55);
  background: rgba(79, 124, 255, .22); color: #dfe7ff; font-weight: 600;
}
.shot-btn.primary:hover:not(:disabled) { background: rgba(79, 124, 255, .32); }
.shot-btn:disabled { opacity: .4; cursor: not-allowed; }
</style>
