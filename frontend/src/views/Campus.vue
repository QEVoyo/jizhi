<template>
  <div class="campus-page">
    <header class="campus-top">
      <div class="campus-brand">
        <span class="campus-mark">✦</span>
        <div class="campus-brand-text">
          <b>基智 · 校园</b>
          <em>第三条学习路线</em>
        </div>
      </div>
      <div class="campus-top-actions">
        <button @click="toggleFullscreen">{{ fullscreen ? '退出全屏' : '全屏' }}</button>
        <button class="primary" @click="backToDesk">回书桌</button>
      </div>
    </header>

    <main class="campus-launcher">
      <section class="campus-card">
        <span class="campus-kicker">龙之城堡 · 2D 魔法世界</span>
        <h1>龙之城堡</h1>
        <p class="campus-sub">登录后进入超大地图，人物可以移动</p>
        <p class="campus-desc">
          这是独立的桌面游戏，不在网页里运行。桌面版客户端会直接拉起本机的游戏本体；
          网页端只负责说明和下载桌面版。
        </p>

        <div v-if="desktop" class="campus-actions">
          <button class="campus-main-btn" :disabled="launching" @click="launchGame">
            {{ launching ? '正在启动…' : '启动游戏' }}
          </button>
          <button class="campus-ghost-btn" @click="backToDesk">回书桌</button>
        </div>
        <div v-else class="campus-actions">
          <a class="campus-main-btn" href="https://api.jizhi-learn.com/download/JIZHI-setup.exe">
            下载桌面版
          </a>
          <button class="campus-ghost-btn" @click="backToDesk">回书桌</button>
        </div>

        <p class="campus-status" :class="{ 'is-error': statusError }">{{ status }}</p>
        <p class="campus-note">
          游戏默认从 <code>D:\jizhi-game</code> 启动；也可以设置环境变量
          <code>JIZHI_GAME_DIR</code> 指向游戏目录。
        </p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { isDesktop } from '@/desktop'

const router = useRouter()

const desktop = isDesktop
const launching = ref(false)
const fullscreen = ref(false)
const statusError = ref(false)
const status = ref(desktop
  ? '桌面版会直接启动本机的《龙之城堡》。'
  : '网页端不能直接运行桌面游戏，请下载桌面版客户端。')

function invokeTauri(command, args) {
  const invoke = window.__TAURI__?.core?.invoke || window.__TAURI_INTERNALS__?.invoke
  if (!invoke) return Promise.reject(new Error('当前不在桌面版里'))
  return invoke(command, args)
}

async function launchGame() {
  if (launching.value) return
  launching.value = true
  statusError.value = false
  status.value = '正在启动《龙之城堡》…'
  try {
    const dir = await invokeTauri('launch_game')
    status.value = `已启动：${dir}`
  } catch (e) {
    statusError.value = true
    status.value = String(e?.message || e || '启动失败')
  } finally {
    launching.value = false
  }
}

function backToDesk() {
  router.push('/home')
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen?.()
      .then(() => { fullscreen.value = true })
      .catch(() => {})
  } else {
    document.exitFullscreen?.()
      .then(() => { fullscreen.value = false })
      .catch(() => {})
  }
}

function onFsChange() {
  fullscreen.value = !!document.fullscreenElement
}

onMounted(() => {
  document.addEventListener('fullscreenchange', onFsChange)
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', onFsChange)
})
</script>

<style scoped>
.campus-page {
  position: relative;
  min-height: calc(100vh - var(--jz-top, 0px));
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px 24px 40px;
  background:
    linear-gradient(180deg, rgba(3, 6, 14, .55), rgba(3, 6, 14, .78)),
    url('/images/campus/campus_home_bg.webp') center / cover no-repeat;
  color: #eef3ff;
  font-family: inherit;
  user-select: none;
}

.campus-top {
  position: absolute;
  top: 18px;
  left: 24px;
  right: 24px;
  z-index: 6;
  display: flex;
  align-items: center;
  justify-content: space-between;
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
  flex-wrap: wrap;
  justify-content: flex-end;
}
.campus-top-actions button {
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
.campus-top-actions button.primary {
  border-color: rgba(255, 214, 140, .45);
  background: linear-gradient(145deg, rgba(255, 205, 120, .22), rgba(110, 230, 255, .1));
  color: #ffe6b6;
}

.campus-launcher {
  position: relative;
  z-index: 3;
  width: min(680px, 100%);
}
.campus-card {
  padding: 34px 36px 28px;
  border-radius: 20px;
  border: 1px solid rgba(160, 200, 255, .18);
  background: linear-gradient(160deg, rgba(12, 18, 34, .88), rgba(6, 10, 22, .9));
  backdrop-filter: blur(18px) saturate(1.2);
  box-shadow: 0 28px 80px rgba(0, 0, 0, .5);
}
.campus-kicker {
  font-size: 10.5px;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: rgba(255, 214, 140, .8);
}
.campus-card h1 {
  margin: 8px 0 2px;
  font-size: clamp(34px, 5vw, 52px);
  letter-spacing: 2px;
  color: #ffe6b6;
  text-shadow: 0 0 32px rgba(255, 190, 100, .25);
}
.campus-sub {
  margin: 0 0 16px;
  font-size: 14px;
  color: rgba(230, 240, 255, .78);
}
.campus-desc {
  margin: 0 0 22px;
  font-size: 12.5px;
  line-height: 1.8;
  color: rgba(210, 222, 245, .68);
}
.campus-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
.campus-main-btn,
.campus-ghost-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 132px;
  padding: 11px 20px;
  border-radius: 10px;
  font-family: inherit;
  font-size: 13px;
  cursor: pointer;
  text-decoration: none;
  transition: all .18s ease;
}
.campus-main-btn {
  border: 1px solid rgba(255, 214, 140, .55);
  background: linear-gradient(145deg, rgba(255, 205, 120, .3), rgba(110, 230, 255, .12));
  color: #ffe6b6;
  box-shadow: 0 0 24px rgba(255, 190, 100, .16);
}
.campus-main-btn:hover { background: linear-gradient(145deg, rgba(255, 205, 120, .42), rgba(110, 230, 255, .18)); }
.campus-main-btn:disabled { opacity: .6; cursor: default; }
.campus-ghost-btn {
  border: 1px solid rgba(140, 190, 255, .2);
  background: rgba(6, 11, 24, .55);
  color: rgba(230, 239, 255, .82);
}
.campus-ghost-btn:hover { border-color: rgba(140, 190, 255, .42); color: #fff; }

.campus-status {
  min-height: 18px;
  margin: 16px 0 0;
  font-size: 11.5px;
  color: rgba(150, 220, 255, .72);
}
.campus-status.is-error { color: #ff9d9d; }
.campus-note {
  margin: 10px 0 0;
  font-size: 10px;
  line-height: 1.7;
  color: rgba(180, 200, 235, .4);
}
.campus-note code {
  padding: 1px 4px;
  border-radius: 4px;
  background: rgba(255, 255, 255, .06);
  font-family: Consolas, monospace;
}

@media (max-width: 640px) {
  .campus-page { padding: 86px 16px 24px; }
  .campus-card { padding: 24px 20px 20px; }
  .campus-top { top: 12px; left: 12px; right: 12px; }
  .campus-top-actions button { padding: 6px 10px; }
}
</style>
