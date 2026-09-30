<!--
  桌面版固定操作键：返回 / 前进 / 刷新 ｜ 最小化 / 最大化 / 关闭。

  设计（2026-09-27 用户拍板）：
  - 不要独立标题栏 —— 那会让应用看着像弹窗、与内容有「切割感」
  - 六键全部对齐小基顶栏的 .nav-action（16px、var(--text-secondary)、FontAwesome 图标），
    位置也对齐到同一条线上；小基顶栏右侧用 padding 让出位置，
    视觉上就是「原来那 5 个键 + 这 6 个」连成一排
  - 返回/前进/刷新 是补回被我们屏蔽掉的浏览器能力（见 desktop/index.js 里对 F5 / 后退键的处理）：
    应用里没有地址栏和浏览器工具栏，这几个动作必须由应用自己提供
-->
<template>
  <div class="jz-wctl">
    <button class="jz-wbtn" title="返回" @click.stop="onBack">
      <i class="fas fa-arrow-left"></i>
    </button>
    <button class="jz-wbtn" title="前进" @click.stop="onForward">
      <i class="fas fa-arrow-right"></i>
    </button>
    <button class="jz-wbtn" title="刷新" @click.stop="onRefresh">
      <i class="fas fa-rotate-right"></i>
    </button>

    <span class="jz-wsep"></span>

    <button class="jz-wbtn" title="最小化" @click.stop="onMinimize">
      <i class="fas fa-window-minimize"></i>
    </button>
    <button class="jz-wbtn" :title="isMaximized ? '还原' : '最大化'" @click.stop="onToggleMaximize">
      <i :class="isMaximized ? 'fas fa-window-restore' : 'fas fa-window-maximize'"></i>
    </button>
    <button class="jz-wbtn jz-wbtn-close" title="关闭" @click.stop="onClose">
      <i class="fas fa-times"></i>
    </button>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { onWindowResized, winClose, winIsMaximized, winMinimize, winToggleMaximize } from './index.js'

const router = useRouter()
const isMaximized = ref(false)
let off = null

// ===== 导航三键 =====
// 用 vue-router 的 back/forward 而不是 webview 的 history —— 应用是 SPA，
// 路由历史就是同一份 history 栈，走 router 才不会和路由状态脱节。
function onBack() { router.back() }
function onForward() { router.forward() }
// 刷新 = 整页重载。这是最不容易出错的选择：组件级重挂载对"页面数据不重新拉取"的
// 页面会失效，而整页重载在 URL 不变的前提下总能拿到最新状态。
function onRefresh() { window.location.reload() }

// ===== 窗口三键 =====
async function syncMaximized() { isMaximized.value = await winIsMaximized() }
function onMinimize() { winMinimize() }
function onToggleMaximize() { winToggleMaximize().then(syncMaximized) }
function onClose() { winClose() }

onMounted(() => {
  syncMaximized()
  off = onWindowResized(syncMaximized)
})
onUnmounted(() => { try { off?.() } catch {} })
</script>

<style scoped>
/* 位置对齐小基顶栏：.call-nav 的 padding 是 10px 20px，按钮高 32px
   （el-button text 的默认高度），所以纵向中心落在 10+16=26px 处。 */
.jz-wctl {
  position: fixed;
  top: 10px;
  right: 20px;
  z-index: 100000;
  display: flex;
  align-items: center;
  /* 与 .nav-actions 的 gap 一致（同样做缩放反向补偿，保持物理间距恒定） */
  gap: calc(4px / var(--jz-scale, 1));
  height: calc(32px / var(--jz-scale, 1));
  pointer-events: none;     /* 容器不吃事件，只有按钮吃 */
  -webkit-user-select: none;
  user-select: none;
}

.jz-wbtn {
  pointer-events: auto;
  /* 除以 --jz-scale 反向补偿：页面被浏览器缩放后，按钮仍是恒定物理尺寸。
     不补偿的话窗口拖小时按钮会缩到很小，很难点中。 */
  width: calc(40px / var(--jz-scale, 1));
  height: calc(32px / var(--jz-scale, 1));
  padding: 0;
  border: none;
  background: transparent;
  /* 与小基顶栏 5 个键同色 */
  color: var(--text-secondary, #a8a8c0);
  font-size: calc(15px / var(--jz-scale, 1));
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: default;
  border-radius: 6px;
  transition: background-color .12s ease, color .12s ease;
}
.jz-wbtn:hover  { color: var(--text-primary, #e8e8f0); background: var(--border-color, rgba(128,128,128,.18)); }
.jz-wbtn:active { background: rgba(128, 128, 128, .28); }

/* 导航三键 与 窗口三键 之间的细分隔线：
   前者作用于应用内容，后者作用于窗口本身，分开更好认 */
.jz-wsep {
  width: 1px;
  height: calc(16px / var(--jz-scale, 1));
  background: var(--border-color, rgba(128,128,128,.25));
  margin: 0 calc(4px / var(--jz-scale, 1));
}

/* 关闭键用 Windows 惯例的红色 —— 这是用户对窗口按钮的肌肉记忆，值得破一次例 */
.jz-wbtn-close:hover  { background: #e81123 !important; color: #fff !important; }
.jz-wbtn-close:active { background: #c50f1f !important; color: #fff !important; }
</style>
