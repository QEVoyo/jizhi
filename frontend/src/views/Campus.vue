<template>
  <div class="campus-page">
    <div class="campus-map-shell">
      <div
        class="campus-map"
        :class="{ 'is-ready': mapLoaded }"
        :style="{ backgroundImage: `url(${MAP_SRC})` }"
      >
        <div class="campus-map-shade"></div>

        <button
          v-for="h in hotspots"
          :key="h.id"
          class="campus-label"
          :class="{
            recommended: h.id === recommendedId,
            'is-hover': hoverId === h.id,
          }"
          :style="{ left: h.x + '%', top: h.y + '%', '--hotspot': h.color }"
          @click="openHotspot(h.id)"
          @mouseenter="hoverId = h.id"
          @mouseleave="hoverId = null"
        >
          <span class="campus-label-dot"></span>
          <span class="campus-label-text">
            <b>{{ h.title }}</b>
            <em>{{ h.id === recommendedId ? '小基推荐' : h.subtitle }}</em>
          </span>
        </button>
      </div>
    </div>

    <header class="campus-top">
      <div class="campus-brand">
        <span class="campus-mark">✦</span>
        <div class="campus-brand-text">
          <b>基智学院 · 超大地图</b>
          <em>{{ guest ? '预览模式' : '按你的学习状态推荐' }}</em>
        </div>
      </div>
      <div class="campus-top-actions">
        <button @click="toggleFullscreen">{{ fullscreen ? '退出全屏' : '全屏' }}</button>
        <button class="primary" @click="backToDesk">回书桌</button>
      </div>
    </header>

    <aside class="campus-guide">
      <div class="campus-guide-avatar">
        <img :src="xiaojiSrc" alt="" draggable="false" @error="onXiaojiError" />
      </div>
      <div class="campus-guide-body">
        <span class="campus-guide-name">小基</span>
        <p>{{ guideLine }}</p>
      </div>
      <button class="campus-guide-go" @click="openHotspot(recommendedId)">带我去</button>
    </aside>

    <div class="campus-hint">点击地图上的传送点 · Esc 回书桌</div>

    <!-- 窄屏不塞小标签，改成区域卡片列表 -->
    <div class="campus-mobile-grid">
      <button
        v-for="h in hotspots"
        :key="'m-' + h.id"
        class="campus-mobile-card"
        :class="{ recommended: h.id === recommendedId }"
        :style="{ '--hotspot': h.color }"
        @click="openHotspot(h.id)"
      >
        <span class="campus-label-dot"></span>
        <span class="campus-mobile-card-text">
          <b>{{ h.title }}</b>
          <em>{{ h.id === recommendedId ? '小基推荐' : h.subtitle }}</em>
        </span>
      </button>
    </div>

    <Transition name="campus-fade">
      <div v-if="panel" class="campus-panel-wrap" @click.self="closePanel">
        <div class="campus-panel">
          <button class="campus-panel-close" @click="closePanel">×</button>
          <span class="campus-panel-kicker">{{ panelKicker }}</span>
          <h2>{{ panel.title }}</h2>
          <p>{{ panel.desc }}</p>
          <div class="campus-panel-actions">
            <button v-if="panel.path" class="primary" @click="enterPanel">去这里</button>
            <button v-else class="primary" @click="backToDesk">回书桌</button>
            <button class="ghost" @click="closePanel">再逛逛</button>
          </div>
          <span class="campus-panel-note">{{ panelNote }}</span>
        </div>
      </div>
    </Transition>

    <Transition name="campus-fade">
      <div v-if="loading" class="campus-loading">
        <div class="campus-loading-mark">✦</div>
        <b>正在铺开超大地图…</b>
        <span>地图取自《龙之城堡》当前超大地图</span>
      </div>
    </Transition>

    <div v-if="failed" class="campus-failed">
      <b>地图暂时加载不出来</b>
      <p>可以先回书桌，稍后再来。</p>
      <button class="primary" @click="backToDesk">回书桌</button>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { CAMPUS_HOTSPOTS, CAMPUS_LINES } from '@/campus/hotspots'
import { pickCampusHotspot } from '@/campus/recommendation'

const MAP_SRC = '/images/campus/campus_map_2d.webp'

const router = useRouter()
const auth = useAuthStore()

const hotspots = CAMPUS_HOTSPOTS
const loading = ref(true)
const mapLoaded = ref(false)
const failed = ref(false)
const fullscreen = ref(false)
const hoverId = ref(null)
const panel = ref(null)
const recommendedId = ref('today')
const guest = ref(!auth.user?.id)
const xiaojiFallback = ref(false)

const xiaojiSrc = computed(() => (xiaojiFallback.value
  ? '/images/xiaoji/xiaoji_idle-full.png'
  : '/xiaoji/xiaoji_idle_loop.webp'))

const guideLine = computed(() => {
  if (guest.value) return CAMPUS_LINES.guest
  return CAMPUS_LINES[recommendedId.value] || CAMPUS_LINES.today
})

const panelKicker = computed(() => {
  if (!panel.value) return ''
  return panel.value.id === recommendedId.value ? '小基推荐' : '传送点'
})

const panelNote = computed(() => {
  if (guest.value) return '预览模式：登录后会按你的真实学习数据推荐'
  return '地图取自《龙之城堡》当前超大地图，学习入口回到基智'
})

function onXiaojiError() {
  xiaojiFallback.value = true
}

function openHotspot(id) {
  const h = hotspots.find(x => x.id === id)
  if (h) panel.value = h
}

function closePanel() {
  panel.value = null
}

function enterPanel() {
  const path = panel.value?.path
  if (path) router.push(path)
}

function backToDesk() {
  router.push('/home')
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen?.()
      .then(() => { fullscreen.value = true })
      .catch(() => { /* 浏览器不允许就算了 */ })
  } else {
    document.exitFullscreen?.()
      .then(() => { fullscreen.value = false })
      .catch(() => {})
  }
}

function onFsChange() {
  fullscreen.value = !!document.fullscreenElement
}

function onKey(e) {
  const el = e.target
  const tag = String(el?.tagName || '').toLowerCase()
  if (tag === 'input' || tag === 'textarea' || tag === 'select' || el?.isContentEditable) return
  if (e.key !== 'Escape') return
  if (panel.value) closePanel()
  else backToDesk()
}

onMounted(() => {
  recommendedId.value = pickCampusHotspot(auth.user?.id).id
  guest.value = !auth.user?.id

  const img = new Image()
  img.onload = () => {
    mapLoaded.value = true
    loading.value = false
  }
  img.onerror = () => {
    failed.value = true
    loading.value = false
  }
  img.src = MAP_SRC

  document.addEventListener('fullscreenchange', onFsChange)
  window.addEventListener('keydown', onKey)
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', onFsChange)
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.campus-page {
  position: relative;
  height: calc(100vh - var(--jz-top, 0px));
  min-height: 560px;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(3, 6, 14, .5), rgba(3, 6, 14, .72)),
    url('/images/campus/campus_home_bg.webp') center / cover no-repeat;
  color: #eef3ff;
  font-family: inherit;
  user-select: none;
}

/* ===== 2D 地图 ===== */
.campus-map-shell {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}
.campus-map {
  position: relative;
  width: 100%;
  max-width: calc((100vh - var(--jz-top, 0px)) * 16 / 9);
  max-height: 100%;
  aspect-ratio: 16 / 9;
  background-size: 100% 100%;
  background-repeat: no-repeat;
  opacity: 0;
  transform: scale(1.015);
  transition: opacity .45s ease, transform .45s ease;
}
.campus-map.is-ready { opacity: 1; transform: scale(1); }
.campus-map-shade {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  background:
    linear-gradient(180deg, rgba(3, 6, 14, .62), transparent 16%, transparent 78%, rgba(3, 6, 14, .72)),
    radial-gradient(circle at 50% 45%, transparent 38%, rgba(2, 4, 10, .48) 100%);
}

/* ===== 地图标签 ===== */
.campus-label {
  position: absolute;
  z-index: 4;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px 6px 8px;
  border-radius: 11px;
  border: 1px solid rgba(160, 200, 255, .18);
  background: rgba(6, 11, 24, .72);
  color: #e8f0ff;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  backdrop-filter: blur(16px) saturate(1.25);
  box-shadow: 0 8px 24px rgba(0, 0, 0, .3);
  transform: translate(-50%, -50%);
  transition: border-color .18s ease, background .18s ease, box-shadow .18s ease, opacity .25s ease;
  will-change: transform;
}
.campus-label.recommended {
  border-color: color-mix(in srgb, var(--hotspot) 60%, transparent);
  background: rgba(10, 16, 32, .82);
  box-shadow: 0 0 26px color-mix(in srgb, var(--hotspot) 22%, transparent), 0 8px 24px rgba(0, 0, 0, .32);
}
.campus-label.is-hover { border-color: color-mix(in srgb, var(--hotspot) 80%, transparent); }
.campus-label.is-locked { opacity: .82; }
.campus-label-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--hotspot);
  box-shadow: 0 0 10px var(--hotspot);
  flex: none;
}
.campus-label-text {
  display: flex;
  flex-direction: column;
  transition: transform .18s ease;
  transform-origin: left center;
}
.campus-label.is-hover .campus-label-text { transform: scale(1.045); }
.campus-label-text b { font-size: 11.5px; font-weight: 700; letter-spacing: .2px; }
.campus-label-text em {
  margin-top: 1px;
  font-style: normal;
  font-size: 9.5px;
  color: rgba(190, 208, 240, .62);
}
.campus-label.recommended .campus-label-text em {
  color: color-mix(in srgb, var(--hotspot) 80%, #fff);
}

/* ===== 顶栏 ===== */
.campus-top {
  position: absolute;
  top: 18px;
  left: 24px;
  right: 24px;
  z-index: 6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  pointer-events: none;
}
.campus-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 13px 8px 10px;
  border-radius: 13px;
  border: 1px solid rgba(140, 190, 255, .16);
  background: rgba(6, 11, 24, .6);
  backdrop-filter: blur(16px) saturate(1.3);
  box-shadow: 0 10px 30px rgba(0, 0, 0, .25);
}
.campus-mark {
  width: 30px;
  height: 30px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  color: #ffe1a1;
  font-size: 17px;
  background: linear-gradient(145deg, rgba(255, 205, 120, .24), rgba(110, 230, 255, .08));
  border: 1px solid rgba(255, 220, 150, .35);
  text-shadow: 0 0 14px rgba(255, 200, 100, .9);
}
.campus-brand-text { display: flex; flex-direction: column; }
.campus-brand-text b { font-size: 13.5px; letter-spacing: .4px; }
.campus-brand-text em {
  margin-top: 1px;
  font-style: normal;
  font-size: 10px;
  color: rgba(200, 215, 245, .55);
}
.campus-top-actions {
  display: flex;
  gap: 8px;
  pointer-events: auto;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.campus-top-actions button,
.campus-panel button,
.campus-failed button {
  padding: 7px 13px;
  border-radius: 9px;
  cursor: pointer;
  border: 1px solid rgba(140, 190, 255, .18);
  background: rgba(6, 11, 24, .62);
  color: rgba(230, 239, 255, .82);
  font-family: inherit;
  font-size: 11.5px;
  backdrop-filter: blur(14px);
  transition: all .18s ease;
}
.campus-top-actions button:hover {
  border-color: rgba(140, 190, 255, .4);
  color: #fff;
}
.campus-top-actions button.primary,
.campus-panel button.primary,
.campus-failed button.primary {
  border-color: rgba(255, 214, 140, .45);
  background: linear-gradient(145deg, rgba(255, 205, 120, .22), rgba(110, 230, 255, .1));
  color: #ffe6b6;
  box-shadow: 0 0 22px rgba(255, 190, 100, .12);
}

/* ===== 小基引导卡 ===== */
.campus-guide {
  position: absolute;
  left: 24px;
  bottom: 24px;
  z-index: 5;
  display: flex;
  align-items: center;
  gap: 10px;
  width: min(380px, calc(100vw - 48px));
  padding: 10px 12px;
  border-radius: 15px;
  border: 1px solid rgba(150, 200, 255, .18);
  background: rgba(6, 11, 24, .7);
  backdrop-filter: blur(20px) saturate(1.3);
  box-shadow: 0 12px 34px rgba(0, 0, 0, .32);
}
.campus-guide-avatar {
  flex: none;
  width: 46px;
  height: 58px;
  border-radius: 12px;
  overflow: hidden;
  background: radial-gradient(circle at 50% 40%, rgba(120, 220, 255, .2), rgba(6, 11, 24, .2));
}
.campus-guide-avatar img { width: 100%; height: 100%; object-fit: contain; }
.campus-guide-body { flex: 1; min-width: 0; }
.campus-guide-name {
  display: block;
  font-size: 10px;
  letter-spacing: .6px;
  color: rgba(160, 220, 255, .75);
}
.campus-guide-body p {
  margin-top: 2px;
  font-size: 12px;
  line-height: 1.55;
  color: rgba(235, 242, 255, .9);
}
.campus-guide-go {
  flex: none;
  padding: 7px 11px;
  border-radius: 9px;
  cursor: pointer;
  border: 1px solid rgba(255, 214, 140, .4);
  background: rgba(255, 205, 120, .12);
  color: #ffe3ad;
  font-family: inherit;
  font-size: 11px;
  transition: all .18s ease;
}
.campus-guide-go:hover {
  background: rgba(255, 205, 120, .22);
  border-color: rgba(255, 214, 140, .7);
}
.campus-hint {
  position: absolute;
  right: 24px;
  bottom: 28px;
  z-index: 5;
  font-size: 10.5px;
  color: rgba(190, 208, 240, .42);
  letter-spacing: .3px;
}

/* ===== 面板 ===== */
.campus-panel-wrap {
  position: absolute;
  inset: 0;
  z-index: 20;
  display: grid;
  place-items: center;
  background: rgba(3, 6, 14, .55);
  backdrop-filter: blur(7px);
  padding: 24px;
}
.campus-panel {
  position: relative;
  width: min(430px, calc(100vw - 48px));
  padding: 24px 24px 18px;
  border-radius: 18px;
  border: 1px solid rgba(160, 200, 255, .2);
  background: linear-gradient(160deg, rgba(14, 21, 40, .96), rgba(7, 11, 24, .96));
  box-shadow: 0 24px 70px rgba(0, 0, 0, .55), 0 0 0 1px rgba(255, 255, 255, .03) inset;
}
.campus-panel-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 26px;
  height: 26px;
  padding: 0;
  border-radius: 8px;
  border: 1px solid rgba(160, 200, 255, .16);
  background: rgba(255, 255, 255, .04);
  color: rgba(220, 232, 255, .65);
  cursor: pointer;
  font-size: 15px;
  line-height: 1;
}
.campus-panel-kicker {
  font-size: 10px;
  letter-spacing: .8px;
  text-transform: uppercase;
  color: rgba(150, 220, 255, .75);
}
.campus-panel h2 { margin: 6px 0 8px; font-size: 21px; letter-spacing: .3px; }
.campus-panel p {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.75;
  color: rgba(210, 222, 245, .75);
}
.campus-panel-actions { display: flex; gap: 8px; margin-top: 18px; }
.campus-panel-actions button { padding: 8px 16px; font-size: 12px; }
.campus-panel-note {
  display: block;
  margin-top: 14px;
  font-size: 10px;
  color: rgba(180, 200, 235, .4);
}

/* ===== 加载 / 失败 ===== */
.campus-loading,
.campus-failed {
  position: absolute;
  inset: 0;
  z-index: 30;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-align: center;
  background:
    linear-gradient(180deg, rgba(3, 6, 14, .55), rgba(3, 6, 14, .82)),
    url('/images/campus/campus_home_bg.webp') center / cover no-repeat;
  color: rgba(230, 240, 255, .85);
}
.campus-loading-mark {
  font-size: 30px;
  color: #ffe1a1;
  text-shadow: 0 0 24px rgba(255, 200, 100, .9);
  animation: campus-spin 2.4s ease-in-out infinite;
}
.campus-loading b { font-size: 14px; letter-spacing: .5px; }
.campus-loading span { font-size: 10.5px; color: rgba(190, 208, 240, .45); }
@keyframes campus-spin {
  0%, 100% { transform: rotate(0deg) scale(.9); opacity: .6; }
  50% { transform: rotate(180deg) scale(1.1); opacity: 1; }
}
.campus-failed { z-index: 31; }
.campus-failed b { font-size: 16px; }
.campus-failed p {
  margin: 0 0 8px;
  font-size: 12px;
  color: rgba(200, 215, 245, .6);
}

.campus-fade-enter-active,
.campus-fade-leave-active { transition: opacity .22s ease; }
.campus-fade-enter-from,
.campus-fade-leave-to { opacity: 0; }

/* ===== 窄屏：地图标签改成卡片列表 ===== */
.campus-mobile-grid { display: none; }

@media (max-width: 760px) {
  .campus-page {
    height: auto;
    min-height: calc(100vh - var(--jz-top, 0px));
    overflow-y: auto;
    padding: 92px 16px 24px;
  }
  .campus-map-shell {
    position: relative;
    inset: auto;
    display: block;
    padding: 0;
  }
  .campus-map {
    width: 100%;
    max-width: none;
    max-height: none;
    border-radius: 16px;
    border: 1px solid rgba(160, 200, 255, .14);
    overflow: hidden;
  }
  .campus-label { display: none; }
  .campus-mobile-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 12px;
  }
  .campus-mobile-card {
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 9px 10px;
    border-radius: 11px;
    border: 1px solid rgba(160, 200, 255, .16);
    background: rgba(6, 11, 24, .62);
    color: #e8f0ff;
    font-family: inherit;
    text-align: left;
    cursor: pointer;
  }
  .campus-mobile-card.recommended {
    border-color: color-mix(in srgb, var(--hotspot) 60%, transparent);
    box-shadow: 0 0 18px color-mix(in srgb, var(--hotspot) 16%, transparent);
  }
  .campus-mobile-card.is-locked { opacity: .78; }
  .campus-mobile-card-text { display: flex; flex-direction: column; }
  .campus-mobile-card-text b { font-size: 11.5px; }
  .campus-mobile-card-text em {
    margin-top: 1px;
    font-style: normal;
    font-size: 9.5px;
    color: rgba(190, 208, 240, .62);
  }
  .campus-top { top: 12px; left: 12px; right: 12px; }
  .campus-brand-text b { font-size: 12px; }
  .campus-guide {
    position: static;
    width: auto;
    margin-top: 12px;
  }
  .campus-hint { display: none; }
}
</style>
