<template>
  <div class="nav-wheel" @wheel.prevent="onWheel">
    <!-- 左右旋转按钮 -->
    <button class="wheel-arrow left" @click="rotate(-1)" title="向左转">
      <i class="fas fa-chevron-left"></i>
    </button>
    <button class="wheel-arrow right" @click="rotate(1)" title="向右转">
      <i class="fas fa-chevron-right"></i>
    </button>

    <!-- 半椭圆轮盘：可见窗口 7 个槽位（中间最突出，两侧渐隐） -->
    <div class="wheel-stage">
      <div
        v-for="(slot, si) in SLOTS"
        :key="si"
        class="wheel-slot"
        :style="slotStyle(si, slot)"
      >
        <router-link
          v-if="itemAt(si)"
          :to="itemAt(si).to"
          class="wheel-item"
          :class="{ active: itemAt(si).active }"
          :style="itemStyle(si)"
          :title="itemAt(si).label"
          @click.stop
        >
          <img :src="iconPath(itemAt(si).icon)" :alt="itemAt(si).label" class="wheel-icon-img" />
          <span v-if="itemAt(si).badgeCount > 0" class="wheel-badge">{{ itemAt(si).badgeCount > 99 ? '99+' : itemAt(si).badgeCount }}</span>
          <span class="wheel-label" :class="{ show: si === 3 }">{{ itemAt(si).label }}</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
// ===== 半椭圆轮盘导航（2026-08-25）=====
// 图标沿半椭圆下弧排布：中间槽位（si=3）最大最亮，向两侧渐隐缩小；
// 旋转 = 整体平移槽位（CSS transition 平滑），支持按钮/滚轮。
// 点击任意可见图标直接跳转；中间图标下方显示名称标签。
import { ref, computed } from 'vue'

const props = defineProps({
  items: { type: Array, default: () => [] }   // {to, icon, label, active, badgeCount}
})

const SLOTS = [-75, -50, -25, 0, 25, 50, 75]   // 7 个槽位角度（度）
const CENTER = 3
const RX = 104   // 椭圆横半轴
const RY = 88    // 椭圆纵半轴

const offset = ref(0)   // 旋转步数（0..N-1）

const N = computed(() => Math.max(1, props.items.length))

function itemAt(si) {
  const n = N.value
  // 槽位 si 对应 items 里的下标：整体前移 offset 步
  const idx = (si - CENTER + offset.value + n * 10) % n
  return props.items[idx] || null
}

function slotStyle(si, angleDeg) {
  const a = (angleDeg * Math.PI) / 180
  const x = RX * Math.sin(a)
  const y = RY * (1 - Math.cos(a))
  return {
    left: `calc(50% + ${x}px)`,
    top: `${y}px`,
    zIndex: 10 - Math.abs(si - CENTER),
  }
}

function itemStyle(si) {
  const dist = Math.abs(si - CENTER)
  const scale = [0.55, 0.68, 0.84, 1, 0.84, 0.68, 0.55][si]
  const opacity = [0.25, 0.45, 0.75, 1, 0.75, 0.45, 0.25][si]
  return {
    transform: `translate(-50%, -50%) scale(${scale})`,
    opacity,
    cursor: 'pointer',
  }
}

function rotate(step) {
  offset.value = (offset.value + step + N.value) % N.value
}

function onWheel(e) {
  rotate(e.deltaY > 0 ? 1 : -1)
}

const iconBase = '/assets/icons/sidebar/'
function iconPath(name) { return iconBase + name }
</script>

<style scoped>
.nav-wheel {
  position: relative;
  height: 150px;
  margin: 4px 0 8px;
  user-select: none;
}
.wheel-stage {
  position: relative;
  width: 100%;
  height: 100%;
}
.wheel-slot {
  position: absolute;
  width: 0;
  height: 0;
  transition: left .45s cubic-bezier(.34,1.2,.64,1), top .45s cubic-bezier(.34,1.2,.64,1);
}
.wheel-item {
  position: absolute;
  width: 46px;
  height: 46px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: transform .45s cubic-bezier(.34,1.2,.64,1), opacity .45s ease;
}
.wheel-icon-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  filter: drop-shadow(0 2px 6px rgba(0,0,0,.25));
}
.wheel-item.active .wheel-icon-img {
  filter: brightness(1.2) drop-shadow(0 0 8px rgba(120,160,255,.7));
}
.wheel-badge {
  position: absolute;
  top: -4px;
  right: -6px;
  min-width: 16px;
  height: 16px;
  padding: 0 5px;
  border-radius: 8px;
  font-size: 9px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  background: #ef4444;
  color: #fff;
}
.wheel-label {
  position: absolute;
  top: 100%;
  margin-top: 4px;
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
  opacity: 0;
  transition: opacity .3s ease;
  pointer-events: none;
}
.wheel-label.show {
  opacity: 1;
}

/* 左右旋转按钮 */
.wheel-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  background: rgba(128,128,128,.12);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all .2s ease;
  z-index: 20;
}
.wheel-arrow:hover {
  background: rgba(128,128,128,.25);
  color: var(--text-primary);
}
.wheel-arrow.left { left: 0; }
.wheel-arrow.right { right: 0; }
</style>
