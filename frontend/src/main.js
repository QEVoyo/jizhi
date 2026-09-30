import { createApp, watch } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './styles/global.css'
import './styles/theme.css'
import '@fortawesome/fontawesome-free/css/all.min.css'
import { isDesktop, suppressWebBehaviors, initAutoScale, restorePet, pushPetToken, pushPetApiBase, savePetPrefs, petPrefsLocally } from './desktop'
import * as desktopApi from './desktop'
// ⚠️ 别删。文件里有两处用到它：桌宠的后端地址桥（pushPetApiBase）和
//    更新提示的点击回调（openExternal(`${BACKEND_URL}${r.url}`)）。
//    这两处都在 `if (isDesktop)` 里，而 dev 环境的 isDesktop 一直是 false
//    （dev 配置覆盖从没生效，主窗口加载的是线上站），所以缺 import 一直没暴露 ——
//    修好 dev 配置后立刻抛 ReferenceError 把整个模块求值打断。
import { BACKEND_URL } from '@/utils/constants'
import { installShortcuts } from './shortcuts/manager'
import { loadLocalBindings, syncFromAccount, resetToLocalOnly } from './shortcuts/store'
import { useNavStore } from './stores/nav'
import { useAuthStore } from './stores/auth'
import { useThemeStore } from './stores/theme'
import './desktop/desktop.css'

// 桌面版：屏蔽网页专属行为（右键菜单、Ctrl+滚轮缩放、F5 等）+ 窄窗口等比缩放。
// 网页版两者都直接 return，什么都不做。
suppressWebBehaviors()
initAutoScale()

// 桌面版：恢复桌宠（只在用户上次主动开过时）。
// 放在挂载之后 —— 窗口要等主窗口的 webview 就绪。
if (isDesktop) {
  setTimeout(() => restorePet().catch(() => {}), 1500)
}

// 桌面版：启动后静默检查更新。
// 延迟几秒是为了别和首屏抢资源；**探测失败一律安静放过** ——
// 断网、后端没起、安装包还没上传都不是错误，每次启动弹「检查更新失败」只会招人烦。
if (isDesktop) {
  setTimeout(async () => {
    try {
      const { checkUpdate, openExternal } = await import('./desktop')
      const r = await checkUpdate()
      if (!r?.hasUpdate) return
      ElNotification({
        title: '有新版本可用',
        dangerouslyUseHTMLString: true,
        message: `桌面版 v${r.latest} 已发布（当前 v${r.current}${r.sizeMb ? `，${r.sizeMb} MB` : ''}）`,
        duration: 0,
        onClick: () => openExternal(`${BACKEND_URL}${r.url}`),
        customClass: 'jz-update-notify',
      })
    } catch (e) {
      console.debug('[desktop] 更新检查异常（忽略）:', e)
    }
  }, 4000)
}

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

const pinia = createPinia()
app.use(pinia)

// 桌面版：把桌宠需要的两样东西推给壳。
//
// 桌宠的**所有操作都在它自己的窗口里完成**（说句话 / 语音通话 / 先躲起来），
// 不打开主窗口 —— 这是用户明确要求的，否则桌宠就退化成一个启动器。
//
// 但桌宠调接口需要两样东西，它自己拿不到（跨 origin 读不了这边的 localStorage）：
//   · 登录 token
//   · 后端地址（开发 localhost:8000 / 生产 api.jizhi-learn.com）
// 所以由主窗口推给壳，桌宠再问壳要。
//
// ⚠️ **这段必须待在 `app.use(pinia)` 之后**，别挪回文件顶部。
//    它要调 useAuthStore()，而 Pinia 的 store 在 `app.use(pinia)` 之前调用会抛
//    「getActivePinia() was called but there was no active Pinia」，
//    模块求值当场中断 → `app.mount('#app')` 根本执行不到 → 整个窗口一片空白。
//    它原来就在顶上，只因 isDesktop 一直是 false 才没暴露：
//    dev 环境的配置覆盖（tauri.dev.conf.json）从没生效过，主窗口加载的一直是线上站，
//    而线上站里没有桌面端代码。修好 dev 配置后这个分支第一次跑，立刻就炸了。
if (isDesktop) {
  const _authForPet = useAuthStore()
  watch(() => _authForPet.token, (t) => pushPetToken(t), { immediate: true })
  pushPetApiBase(BACKEND_URL)
  // 把设置页里存的桌宠偏好推给壳 —— 桌宠是独立 origin，读不到这边的 localStorage，
  // 不推的话它每次启动都会退回默认菜单（用户关掉的项又冒出来）。
  savePetPrefs(petPrefsLocally())
}

// ===== 自定义快捷键 =====
// 先把本地缓存装上（立刻能响应按键，不等账号资料回来），
// 再把分发器挂上。**全站只有这一个 keydown 分发点** ——
// 原来散在 desktop/index.js 与 GlobalSearch.vue 的两处监听已删除。
loadLocalBindings()
installShortcuts({
  router,
  nav: useNavStore(),
  desktop: desktopApi,
})

// 登录后拉账号上的绑定；退出登录回到本地那份（避免换人登录看到上一个人的配置）
const _auth = useAuthStore()
watch(
  () => _auth.user?.id,
  (uid, old) => {
    if (uid) syncFromAccount(uid)
    else if (old) resetToLocalOnly()
  },
  { immediate: true },
)
app.use(router)
app.use(ElementPlus)

// 桌面版：主动初始化主题 store。
// Pinia 的 store 是懒创建的，而 useThemeStore() 原本只在两处被调用 ——
// 落地页（enterLanding）和「已登录」的路由守卫分支。
// 桌面版跳过了落地页、又停在登录页，两条都不沾，于是 data-theme 没设、
// 主题变量没注入，页面回落到 CSS 的浅色默认值（那条白杠就是这么来的）。
if (isDesktop) {
  try {
    useThemeStore(pinia)
  } catch (e) {
    console.warn('[desktop] 主题初始化失败:', e)
  }
}

// ===== 全局错误保险（2026-09-05）：渲染/异步错误不再「整页静默空白」=====
// 任何未捕获错误都会在页面上画一条红色诊断条（原生 DOM，不依赖 Vue 存活），
// 报错信息直接可见，用户可以截图发来定位；生产环境同样保留（好过往死白页）。
let errBanner = null
function showErrorBanner(msg) {
  if (errBanner) {
    errBanner.querySelector('.jz-err-msg').textContent = msg
    return
  }
  errBanner = document.createElement('div')
  errBanner.style.cssText =
    'position:fixed;top:0;left:0;right:0;z-index:999999;background:#3d0a14;color:#ffd9df;' +
    'font:12px/1.5 Consolas,Menlo,monospace;padding:10px 44px 10px 14px;border-bottom:2px solid #ff4d6a;' +
    'white-space:pre-wrap;word-break:break-all;max-height:40vh;overflow:auto;'
  errBanner.innerHTML =
    '<div style="font-weight:700;color:#ff8fa3;margin-bottom:4px;">⚠️ 页面发生错误（把下面内容发给开发者）</div>' +
    '<div class="jz-err-msg"></div>' +
    '<button style="position:absolute;top:6px;right:10px;background:none;border:1px solid #ff8fa3;color:#ffb3bf;' +
    'border-radius:6px;cursor:pointer;font-size:12px;padding:1px 8px;">关闭</button>'
  errBanner.querySelector('button').onclick = () => errBanner.remove()
  document.body.appendChild(errBanner)
  errBanner.querySelector('.jz-err-msg').textContent = msg
}
function fmtError(e) {
  const stack = (e && e.stack) || (e && e.message) || String(e)
  return String(stack).split('\n').slice(0, 8).join('\n')
}
app.config.errorHandler = (err, instance, info) => {
  console.error('[JZ] Vue 错误:', err, info)
  const msg = `Vue 渲染错误 (${info})\n${fmtError(err)}`
  if (!document.body) return
  try { showErrorBanner(msg) } catch {}
}
window.addEventListener('error', (e) => {
  if (e && e.error && e.error.__jzHandled) return
  console.error('[JZ] 全局错误:', e.error || e.message)
  if (!document.body) return
  const target = e.target || {}
  const isRes = target.tagName === 'IMG' || target.tagName === 'SCRIPT' || target.tagName === 'LINK'
  // 资源加载失败不是渲染崩溃，不弹全局诊断条（组件内部各有兜底）
  if (isRes) return
  try { showErrorBanner('加载错误 ' + (e.filename || '') + '\n' + fmtError(e.error || e.message)) } catch {}
})
window.addEventListener('unhandledrejection', (e) => {
  const r = e.reason
  const msg = String(r && (r.message || r) || r)
  // 动态模块加载失败（chunk 失效）是整页空白的常见原因，必须暴露
  if (/Failed to fetch dynamically imported module|Importing a module script failed|CIRCULAR/.test(msg)) {
    console.error('[JZ] 模块加载失败:', r)
    try {
      const m = (r && r.message) || msg
      if (document.body && !/chunk|import/.test(errBanner && errBanner.querySelector('.jz-err-msg').textContent || '')) {
        showErrorBanner('模块加载失败（请强制刷新 Ctrl+Shift+R 重试）\n' + m)
      }
    } catch {}
  }
  console.error('[JZ] Promise 错误:', r)
})

app.mount('#app')