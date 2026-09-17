import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import './styles/global.css'
import './styles/theme.css'
import '@fortawesome/fontawesome-free/css/all.min.css'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

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