<template>
  <div class="app-container">
    <!-- 桌面版窗口控制（悬浮右上角，无横栏）：网页版 isDesktop=false，这一行不渲染 -->
    <DesktopWindowControls v-if="isDesktop" />

    <router-view v-slot="{ Component, route }">
      <!-- 显式 :duration：即使浏览器丢了 transitionend，也会到点强制结束过渡，
           绝不把新页面卡死在 enter-from(opacity:0)（2026-09-05 修「整页空白」） -->
      <Transition :name="route.meta.transition || 'page-fade'" mode="out-in" :duration="220">
        <component :is="Component" :key="route.path" ref="viewRef" />
      </Transition>
    </router-view>
    <!-- 全局搜索（登录后的主应用页面；落地页/登录/引导/管理后台不显示） -->
    <GlobalSearch v-if="showGlobalSearch" />

    <!-- 桌面版右键菜单（网页版不挂 —— 浏览器该有自己的菜单） -->
    <DesktopContextMenu v-if="isDesktop" />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { isDesktop } from '@/desktop'

// 这些组件首屏都不渲染：GlobalSearch 只在登录后的页面出现，
// 桌面窗口控件/右键菜单只在桌面壳里出现。异步加载，别让它们进首屏 entry。
const GlobalSearch = defineAsyncComponent(() => import('@/components/GlobalSearch.vue'))
const DesktopWindowControls = defineAsyncComponent(() => import('@/desktop/DesktopWindowControls.vue'))
const DesktopContextMenu = defineAsyncComponent(() => import('@/desktop/ContextMenu.vue'))

const route = useRoute()
const router = useRouter()

const showGlobalSearch = computed(() =>
  !!route.meta.requiresAuth &&
  !route.path.startsWith('/admin') &&
  route.path !== '/onboarding'
)

// ==================== 过渡兜底（2026-10-01）====================
//
// ⚠️ 为什么需要这个：路由切换的进场动画靠 `.page-fade-enter-from { opacity: 0 }`
//    这个类**被回收**才生效。Vue 回收它用的是 `requestAnimationFrame` ——
//    而 Chromium 对**被遮挡 / 最小化**的窗口会节流甚至停掉 rAF。
//    真发生时：类永远留在元素上 → **整页永久 opacity:0**，
//    表现为「切页面后一片空白、零报错、刷新一下就好」——
//    刷新不走进场过渡，所以看起来是好的。
//
// 这个现象在本项目**有前科**：2026-09-05 用无头 Edge + CDP 抓到过
//    `.vd-page` 在点击 6 秒后仍带 `page-fade-enter-from`、`opacity=0`。
//    当时的修法是给 VideoDetail 一个稳定根元素 + `:duration` 强制时长，
//    但**强制时长只保证计时器到点，不保证 rAF 回调发生过** —— 洞还在。
//
// 兜底原则：**正常路径一个字节都不改**，只在「已经卡住」时才动手。
//    ① 每次导航结束后 600ms 检查一次（220ms 强制时长 + 充足余量）
//    ② 窗口重新获得焦点 / 从隐藏变可见时再查一次 —— 卡住往往正是
//       在窗口不可见期间发生的，用户回到窗口的那一刻才是发现问题的时刻
const STUCK_SUFFIXES = ['enter-from', 'enter-active', 'enter-to',
                        'leave-from', 'leave-active', 'leave-to']
const TRANSITION_PREFIXES = ['page-fade', 'page-slide']

const viewRef = ref(null)

function unstickTransition() {
  const el = viewRef.value?.$el
  if (!el || el.nodeType !== 1) return
  let stuck = false
  for (const p of TRANSITION_PREFIXES) {
    for (const s of STUCK_SUFFIXES) {
      const cls = `${p}-${s}`
      if (el.classList.contains(cls)) { el.classList.remove(cls); stuck = true }
    }
  }
  if (stuck) {
    // 类摘掉后元素回到自然样式（opacity 1）；inline 里被写死的值也一并清掉
    el.style.opacity = ''
    el.style.transform = ''
    console.warn('[transition] 检测到卡住的过渡类（rAF 被节流？），已强制恢复显示')
  }
}

router.afterEach(() => { setTimeout(unstickTransition, 600) })

onMounted(() => {
  // 这两个监听器随 App 存活整个应用生命周期，不需要卸载
  window.addEventListener('focus', () => setTimeout(unstickTransition, 80))
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) setTimeout(unstickTransition, 80)
  })
  // 未读角标 + 桌面通知：**全站唯一**的轮询点（2026-10-08）。
  // 挂在这里而不是各页面里 —— 弹窗要跨路由存活，而且改造前
  // Sidebar / EdgeNavDock / XiaojiCall 各自起计时器，首页就是 3 份重复请求。
  //
  // 2026-10-17：改成空闲时再动态加载 —— 这个模块会带进 axios，
  // 而首屏（尤其落地页）并不需要它。等首屏画完再拉，别和主包抢带宽。
  const startNotificationsLater = () => {
    import('@/composables/useNotifications')
      .then(m => m.startNotifications())
      .catch(() => {})
  }
  if (window.requestIdleCallback) window.requestIdleCallback(startNotificationsLater, { timeout: 2000 })
  else setTimeout(startNotificationsLater, 800)
})
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  width: 100%;
  min-height: 100vh;
}

/* ===== 桌面壳：为右上角的窗口控制键让出一条高度 =====
   那 6 个键（返回/前进/刷新 ｜ 最小化/最大化/关闭）是 position:fixed 悬浮的
   （top:10px right:20px，高 32px）—— 直接压在页面内容上。
   这里由应用层统一让出 --jz-top：下面的 .app-container 加这段 padding，
   各页面的「满屏高度」也都写成 calc(100vh - var(--jz-top)) 一起扣掉，
   否则加了 padding 会让满屏页多出 44px、把滚动条又推回窗口。

   网页版没有 jz-desktop 这个类（由 desktop/index.js 在桌面壳里加到 <html>），
   --jz-top 保持 0px，渲染结果与改动前完全一致。 */
:root { --jz-top: 0px; }
/* ⚠️ 必须除以 --jz-scale 做反向补偿，理由和窗口按钮本身一样（见 DesktopWindowControls.vue）：
   按钮写的是 calc(32px / var(--jz-scale))，为的是缩放后**物理尺寸恒定**。
   留白如果写死 44px，窗口一缩小（zoom < 1）留白的物理高度跟着缩、
   而按钮物理高度不变 —— 又会压回内容上。这里同步补偿。 */
html.jz-desktop { --jz-top: calc(48px / var(--jz-scale, 1)); }

.app-container {
  min-height: 100vh;
  position: relative;
}
html.jz-desktop .app-container {
  padding-top: var(--jz-top);
}

/* ===== 页面路由过渡 ===== */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* 横向滑动变体（用于同层级子页） */
.page-slide-enter-active,
.page-slide-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}
.page-slide-enter-from {
  opacity: 0;
  transform: translateX(16px);
}
.page-slide-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(128, 128, 128, 0.3);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(128, 128, 128, 0.5);
}

/* ===== 桌面通知：页内长条（2026-10-08）=====
   由 `composables/useNotifications.js` 用 `document.createElement` 挂到 body 上，
   **在组件作用域之外** —— 所以样式必须写在这里（全局），写进任何 .vue 的
   scoped 里都命中不了。

   三条设计要求（用户提的）：
     ① **长条，不是方卡** —— 宽而扁，照消息中心的列表行做
        （左侧 3px 竖色条 + 方形图标 + 标题/时间一行 + 摘要一行）
     ② **毛玻璃** —— 低不透明度 + 强模糊 + 高饱和 + 一道亮边；
        以前写成 88% 不透明，那看着就是块实心板
     ③ **覆盖，不是堆积** —— 同一时刻**只有一条**，新的顶掉旧的，
        总高度恒定（所以不用 ElNotification：它只会往下堆）

   位置：**上部居中**（2026-10-08 用户定）。
   注意不是四角 —— 右上角被桌面壳的窗口控制键占着（top:10px right:20px）。 */
.jz-toast {
  position: fixed;
  top: 18px;
  left: 50%;
  z-index: 9999;
  width: min(620px, calc(100vw - 40px));
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px 11px 16px;
  border-radius: 14px;
  cursor: pointer;
  overflow: hidden;

  /* ② 毛玻璃 */
  background: color-mix(in srgb, var(--surface, #ffffff) 62%, transparent);
  backdrop-filter: blur(30px) saturate(1.7);
  -webkit-backdrop-filter: blur(30px) saturate(1.7);
  border: 1px solid color-mix(in srgb, var(--surface, #ffffff) 45%, transparent);
  box-shadow: 0 12px 40px rgba(0, 0, 0, .16),
              inset 0 1px 0 rgba(255, 255, 255, .35);

  /* 进场/出场。⚠️ translateX(-50%) 必须一直带着 —— 它是横向居中的实现，
     任何一处 transform 漏了它，长条就会跳回左侧。 */
  transform: translateX(-50%) translateY(-14px) scale(.985);
  opacity: 0;
  transition: transform .22s cubic-bezier(.2, .9, .3, 1.15), opacity .22s ease;
}
.jz-toast.in  { transform: translateX(-50%) translateY(0) scale(1); opacity: 1; }
.jz-toast.out { transform: translateX(-50%) translateY(-10px) scale(.985); opacity: 0; }
.jz-toast:hover {
  transform: translateX(-50%) translateY(0) scale(1.006);
  box-shadow: 0 16px 48px rgba(0, 0, 0, .2),
              inset 0 1px 0 rgba(255, 255, 255, .45);
}

/* ① 左侧 3px 竖色条 —— 与消息中心 `.mc-card .bar` 同一个视觉语言 */
.jz-toast .jz-bar {
  position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: linear-gradient(180deg, var(--c1), var(--c2));
}
/* 方形图标，取消息点标签的首字 —— 同 `.mc-icon` */
.jz-toast .jz-ic {
  flex: none; width: 30px; height: 30px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 600; color: #fff;
  background: linear-gradient(135deg, var(--c1), var(--c2));
}
.jz-toast .jz-body { flex: 1; min-width: 0; }
.jz-toast .jz-top { display: flex; align-items: center; gap: 8px; }
.jz-toast .jz-name {
  font-size: 13.5px; font-weight: 600; color: var(--text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
/* 聚合行的「N 条」标记 */
.jz-toast .jz-count {
  flex: none; font-size: 11px; padding: 1px 7px; border-radius: 8px;
  background: color-mix(in srgb, var(--c1) 18%, transparent); color: var(--c1);
}
.jz-toast .jz-time { flex: none; margin-left: auto; font-size: 11px; color: var(--text-muted); }
/* 摘要**只占一行** + 省略号 —— 这是「长条」的关键，多行就变回方块了 */
.jz-toast .jz-preview {
  margin-top: 2px; font-size: 12.5px; line-height: 1.6; color: var(--text-secondary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.jz-toast .jz-x {
  flex: none; width: 22px; height: 22px; border: none; border-radius: 7px;
  background: transparent; cursor: pointer; color: var(--text-muted); font-size: 13px;
}
.jz-toast .jz-x:hover {
  background: color-mix(in srgb, var(--text-muted) 20%, transparent);
  color: var(--text-primary);
}
</style>