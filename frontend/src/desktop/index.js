/**
 * 桌面版（Tauri）运行时支持。
 *
 * 设计原则：同一份代码同时服务网页版和桌面版。
 * 网页版里 isDesktop 恒为 false，下面所有分支都不会执行 —— 网页行为零变化。
 *
 * 桌面壳通过 tauri.conf.json 里的 app.withGlobalTauri = true 注入 window.__TAURI__，
 * 我们靠它判断运行环境（比嗅探 userAgent 可靠）。
 */
import { BACKEND_URL } from '@/utils/constants'


export const isDesktop = (() => {
  if (typeof window === 'undefined') return false
  return !!(window.__TAURI__ || window.__TAURI_INTERNALS__)
})()

let _win = null

/** 拿当前窗口对象；拿不到就返回 null（所有调用点都要容忍 null） */
function currentWindow() {
  if (!isDesktop) return null
  if (_win) return _win
  try {
    _win = window.__TAURI__.window.getCurrentWindow()
  } catch (e) {
    console.warn('[desktop] 获取窗口失败:', e)
    return null
  }
  return _win
}

export async function winMinimize() {
  try { await currentWindow()?.minimize() } catch (e) { console.warn('[desktop] 最小化失败', e) }
}

export async function winToggleMaximize() {
  try { await currentWindow()?.toggleMaximize() } catch (e) { console.warn('[desktop] 最大化切换失败', e) }
}

export async function winClose() {
  try { await currentWindow()?.close() } catch (e) { console.warn('[desktop] 关闭失败', e) }
}

export async function winIsMaximized() {
  try { return !!(await currentWindow()?.isMaximized()) } catch { return false }
}

/**
 * 订阅窗口尺寸变化（用来同步「最大化/还原」按钮图标）。
 * 返回取消订阅函数。
 */
export function onWindowResized(cb) {
  if (!isDesktop) return () => {}
  const w = currentWindow()
  if (!w || typeof w.onResized !== 'function') {
    const h = () => cb()
    window.addEventListener('resize', h)
    return () => window.removeEventListener('resize', h)
  }
  let unlisten = null
  try {
    const p = w.onResized(() => cb())
    if (p && typeof p.then === 'function') p.then((fn) => { unlisten = fn })
  } catch (e) {
    console.warn('[desktop] 订阅窗口事件失败', e)
  }
  return () => { try { unlisten?.() } catch {} }
}

/**
 * 桌面版的设计宽度 —— 必须 **> 1500**。
 *
 * 项目里有一条 XIAOJI 的居中补偿规则：
 *   @media (max-width: 1500px) { .call-main { padding-left: 420px } }
 * padding-left 会把内容中心推到 `视口中心 + padding/2`，
 * 即 420px 的 padding 造成 **210px 的右偏**（实测：视口 1440 时中心在 930、而视口中心是 720）。
 * 视口 > 1500 时该规则不触发，小基和输入区才是真正居中的（实测 1707 时中心 854 = 视口中心 854）。
 *
 * 所以桌面版把布局宽度钉在 1600：无论窗口多窄，等比缩放都会把【视口】保持在 1600，
 * 那条媒体查询永不触发 → 永远居中。这不是绕过问题，是让桌面版落在正确的布局区间里。
 */
const DESIGN_WIDTH = 1600

let _scale = 1

/**
 * 等比缩放：窗口比设计宽度窄时整体缩小，而不是让布局重排变形。
 * 这和项目里既有的「窄屏缩放」是同一套思路（EdgeNavDock.vue 里
 * @media (max-width:1400px) 就是 .edge-dock { transform: scale(.8) }），只是推广到整页。
 *
 * ⚠️ 用 Tauri 的【浏览器缩放】而不是 CSS `zoom`（实测踩过，别改回去）：
 *   CSS zoom   → 布局视口不变，100vh 仍按真实视口算 → 内容画不满窗口，底部露底色；
 *                且媒体查询照样按真实宽度触发 → 布局仍然重排，等于没缩放。
 *   浏览器缩放 → 视口 / 100vh / 媒体查询一起换算 → 页面按 DESIGN_WIDTH 排版后整体缩放。
 *
 * --jz-scale 会写到 html 上，供悬浮窗口按钮做尺寸反向补偿（见 DesktopWindowControls.vue）。
 */
async function applyScale() {
  // innerWidth 已经反映了当前缩放，乘回去才是「zoom=1 时的宽度」
  const baseWidth = window.innerWidth * _scale
  const next = baseWidth < DESIGN_WIDTH ? Math.max(baseWidth / DESIGN_WIDTH, 0.62) : 1
  if (Math.abs(next - _scale) < 0.002) return
  _scale = next
  document.documentElement.style.setProperty('--jz-scale', String(next))
  try {
    const wv = window.__TAURI__?.webview?.getCurrentWebview?.()
      || window.__TAURI__?.webviewWindow?.getCurrentWebview?.()
    if (wv && typeof wv.setZoom === 'function') {
      await wv.setZoom(next)
    } else {
      console.warn('[desktop] 拿不到 webview.setZoom，缩放未生效')
    }
  } catch (e) {
    console.warn('[desktop] setZoom 失败:', e)
  }
}

export function initAutoScale() {
  if (!isDesktop) return
  applyScale()
  let t = null
  window.addEventListener('resize', () => {
    clearTimeout(t)
    t = setTimeout(applyScale, 120)
  })
}

export function currentScale() { return _scale }

/**
 * 原生「另存为」—— 桌面版导出用。
 *
 * 网页版靠 `pdf.save()` / `a.download` 触发浏览器下载栏；桌面壳里那套不会弹系统对话框，
 * 用户根本找不到文件。这里改调 Rust 侧的 save_file 命令，弹真正的原生保存框。
 *
 * @param {string} dataUrl  canvas.toDataURL(...) 或 pdf.output('dataurlstring') 的结果
 * @param {string} suggestedName  默认文件名
 * @returns {Promise<boolean>}  true = 已保存；false = 用户取消或失败
 */
export async function saveDataUrlNative(dataUrl, suggestedName) {
  if (!isDesktop) return false
  const s = String(dataUrl || '')
  const comma = s.indexOf(',')
  const b64 = comma >= 0 ? s.slice(comma + 1) : s
  if (!b64) return false
  try {
    const invoke = window.__TAURI__?.core?.invoke || window.__TAURI_INTERNALS__?.invoke
    if (typeof invoke !== 'function') {
      console.warn('[desktop] 拿不到 invoke，退回网页下载方式')
      return false
    }
    const saved = await invoke('save_file', { base64Data: b64, defaultName: suggestedName })
    return !!saved
  } catch (e) {
    console.warn('[desktop] 原生保存失败:', e)
    return false
  }
}

/**
 * 保存 Blob（如导出的 webm 视频）。转成 dataURL 后复用 saveDataUrlNative。
 * @returns {Promise<boolean>} true = 已保存；false = 取消或失败
 */
export async function saveBlobNative(blob, suggestedName) {
  if (!isDesktop || !blob) return false
  const dataUrl = await new Promise((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(r.result)
    r.onerror = () => reject(r.error || new Error('读取 Blob 失败'))
    r.readAsDataURL(blob)
  })
  return saveDataUrlNative(dataUrl, suggestedName)
}

/**
 * 用系统默认浏览器打开外链。
 *
 * 桌面壳里 `<a target="_blank">` 不会正常打开（要么没反应，要么弹出个没有地址栏的怪窗口）。
 * 项目里这类链接不少：开源依赖主页、ICP 备案号、题目出处。
 */
export async function openExternal(url) {
  if (!isDesktop) return
  try {
    const invoke = window.__TAURI__?.core?.invoke || window.__TAURI_INTERNALS__?.invoke
    if (typeof invoke === 'function') await invoke('open_external', { url })
  } catch (e) {
    console.warn('[desktop] 打开外链失败:', e)
  }
}

// ==================== 版本与更新 ====================

/**
 * 当前桌面壳的版本号。
 *
 * 壳加载的是线上站点 —— 同一份网页既可能跑在浏览器里、也可能跑在任意版本的壳里，
 * 网页端无从知道壳的版本，只能问壳（Rust 侧的 `app_version` 命令）。
 * 浏览器里返回 null，调用方据此不显示「桌面版 vX」那一行。
 */
export async function getAppVersion() {
  if (!isDesktop) return null
  try {
    const invoke = window.__TAURI__?.core?.invoke || window.__TAURI_INTERNALS__?.invoke
    if (typeof invoke !== 'function') return null
    return await invoke('app_version')
  } catch (e) {
    console.warn('[desktop] 读版本号失败:', e)
    return null
  }
}

/** 语义化版本比较：a 比 b 新返回正数，相同返回 0，旧返回负数。 */
function compareVersion(a, b) {
  const pa = String(a).split('.').map((x) => parseInt(x, 10) || 0)
  const pb = String(b).split('.').map((x) => parseInt(x, 10) || 0)
  const n = Math.max(pa.length, pb.length)
  for (let i = 0; i < n; i++) {
    const d = (pa[i] || 0) - (pb[i] || 0)
    if (d !== 0) return d
  }
  return 0
}

/**
 * 检查有没有新版本。比对的是**后端安装包目录里那个 exe 的版本**
 * （`GET /download/latest`，版本号从文件名 `JIZHI_0.1.0_x64-setup.exe` 里解析）。
 *
 * 返回值：
 *   null                      → 不在桌面壳里 / 探测失败（**静默**，不打扰用户）
 *   { hasUpdate: false, ... } → 已是最新
 *   { hasUpdate: true,  ... } → 有新版本，含 latest / sizeMb / url
 *
 * ⚠️ 设计上**只在成功且确实有新版本时才打扰用户**：
 * 启动时的探测失败（断网、后端没起来、还没上传安装包）一律安静放过 ——
 * 桌面端每次启动都弹「检查更新失败」会非常烦人，而它并不是错误。
 */
export async function checkUpdate() {
  if (!isDesktop) return null
  const current = await getAppVersion()
  if (!current) return null
  try {
    const res = await fetch(`${BACKEND_URL}/download/latest`, { cache: 'no-store' })
    if (!res.ok) return null
    const info = await res.json()
    if (!info?.available || !info?.version) return null
    const cmp = compareVersion(info.version, current)
    return {
      hasUpdate: cmp > 0,
      current,
      latest: info.version,
      sizeMb: info.size_mb,
      url: info.url,
      filename: info.filename,
    }
  } catch (e) {
    // 断网/后端没起 都走这里 —— 安静放过，不是错误
    console.debug('[desktop] 检查更新失败（忽略）:', e?.message || e)
    return null
  }
}

// ==================== 桌宠 ====================

/**
 * 显示 / 隐藏桌宠（桌面级：独立透明置顶窗口，不在这个页面里）。
 *
 * 状态存在 localStorage，**由网页端负责持久化** ——
 * Rust 侧只管开窗关窗，不碰存储。这样「开关的真相」只有一处，
 * 不会出现「设置里显示开着、实际窗口不见了」这种对不上的情况。
 */
export async function setPetVisible(visible) {
  if (!isDesktop) return { ok: false, error: '不在桌面壳里' }
  try {
    const invoke = window.__TAURI__?.core?.invoke || window.__TAURI_INTERNALS__?.invoke
    if (typeof invoke !== 'function') {
      return { ok: false, error: '拿不到 Tauri invoke（withGlobalTauri 没开？）' }
    }
    await invoke('set_pet_visible', { visible: !!visible })
    try { localStorage.setItem('jizhi-pet-visible', visible ? '1' : '0') } catch {}
    return { ok: true }
  } catch (e) {
    // ⚠️ 把原始错误**原样带出去**，不再吞进 console ——
    //    webview 的 console 在开发终端里看不到，吞掉就等于没有信息。
    console.warn('[desktop] 切换桌宠失败:', e)
    return { ok: false, error: String((e && (e.message || e)) || e) }
  }
}

/** 上次的开关状态。默认关 —— 未经用户同意就常驻一个浮窗是很打扰的。 */
export function petEnabledLocally() {
  try { return localStorage.getItem('jizhi-pet-visible') === '1' } catch { return false }
}

/**
 * 启动时恢复桌宠。**只有上次主动开过才恢复**（默认不打扰）。
 * 注意要在主窗口起来之后再调 —— 太早的话 pet 窗口可能还没建好。
 */
export async function restorePet() {
  if (!isDesktop || !petEnabledLocally()) return
  await setPetVisible(true)
}

/**
 * 把登录 token 推给桌面壳，供桌宠窗口使用。
 *
 * 桌宠和主窗口是**两个不同 origin**，同源策略下它读不到这边的 localStorage。
 * 所以由这边主动推给壳（存内存不落盘），桌宠需要时再问壳要。
 * 退出登录时传空串清掉。
 */
export async function pushPetToken(token) {
  if (!isDesktop) return
  try {
    const invoke = window.__TAURI__?.core?.invoke || window.__TAURI_INTERNALS__?.invoke
    if (typeof invoke !== 'function') return
    await invoke('set_pet_token', { token: token || '' })
  } catch (e) {
    console.warn('[desktop] 推送 token 给桌宠失败:', e)
  }
}

/**
 * 把后端地址推给桌面壳，供桌宠调接口用。
 * 与 token 同理：桌宠读不到这边的 .env，只能由这边告诉它。
 */
export async function pushPetApiBase(apiBase) {
  if (!isDesktop) return
  try {
    const invoke = window.__TAURI__?.core?.invoke || window.__TAURI_INTERNALS__?.invoke
    if (typeof invoke !== 'function') return
    await invoke('set_pet_api_base', { apiBase: apiBase || '' })
  } catch (e) {
    console.warn('[desktop] 推送后端地址给桌宠失败:', e)
  }
}

// ==================== 桌宠偏好（设置页可定制） ====================

const PET_PREFS_KEY = 'jizhi-pet-prefs'

/**
 * 轮盘里可出现的项 —— **设置页的开关列表与桌宠的菜单共用这份 id**。
 *
 * ⚠️ 桌宠那边的 `ui/pet.html` 里另有一份同 id 的菜单（label/图标/行为都在那），
 *    这边只重复 id 与给人看的名字。id 对不上时桌宠会忽略该项（不会崩），
 *    所以两边漂移是「少个开关」而不是「坏掉」。加一项要同时改两处。
 */
export const PET_WHEEL_ITEMS = [
  { id: 'voice', icon: '🎙', label: '语音', desc: '按住说话，小基用语音回你（文字也留一份）' },
  { id: 'look', icon: '🎨', label: '换个样子', desc: '滚到哪个当场变脸，确认才固定' },
  { id: 'focus', icon: '⏱', label: '专注计时', desc: '滚动选时长，到点小基提醒你' },
  // ⚠️ pinned：**不提供开关**。
  //    「先躲起来」是收起桌宠的唯一入口，一旦关掉，桌宠就再也没法收起来 ——
  //    只能回设置页去动总开关，等于把自己锁在"桌宠常驻、关不掉"的状态里。
  //    这是第一版埋的坑（用户报过「先躲起来怎么没了」）。
  { id: 'hide', icon: '👋', label: '先躲起来', desc: '把桌宠收起来', pinned: true },
]

/**
 * 桌宠尺寸：**连续可调**（设置页是滑杆，不是三档按钮）。
 *
 * 倍率相对基准 —— 1 = 窗口 220 / 轮盘 340 / 形象 180px，其它尺寸全部乘它。
 * 上限 1.6 是实测出来的：再大，轮盘展开时窗口会顶到 340×1.6=544，
 * 在常见的 1080p 屏上夹取（防出屏）会频繁触发，环就被挤扁了。
 */
export const PET_SCALE_MIN = 0.6
export const PET_SCALE_MAX = 1.6
export const PET_SCALE_STEP = 0.05

/** 补齐/校正形状：缺字段按默认来，认不出的值丢掉 */
export function normalizePetPrefs(p) {
  const wheel = {}
  for (const it of PET_WHEEL_ITEMS) {
    // pinned 的项**强制开启** —— 连存坏的旧值也一并纠正回来
    // 默认全部开启；只有明确写了 false 才关
    wheel[it.id] = it.pinned ? true : (p && p.wheel && p.wheel[it.id] === false ? false : true)
  }
  // 尺寸兜底：非数字、NaN、越界一律夹回范围内。
  // 旧版本存的是 'small'/'medium'/'large' 字符串，Number() 会得到 NaN → 落到 1，正好是"中"。
  let s = Number(p?.petScale)
  if (!Number.isFinite(s)) s = 1
  s = Math.min(PET_SCALE_MAX, Math.max(PET_SCALE_MIN, Math.round(s * 100) / 100))
  return { wheel, petScale: s }
}

/** 读本地那份偏好。网页版也读得到（但没人用它）—— 保持纯函数，不碰 isDesktop。 */
export function petPrefsLocally() {
  try {
    const raw = localStorage.getItem(PET_PREFS_KEY)
    return normalizePetPrefs(raw ? JSON.parse(raw) : null)
  } catch {
    // 存坏了就当没有 —— 绝不让它影响设置页渲染
    return normalizePetPrefs(null)
  }
}

/**
 * 存本地 + 推给壳。两件事一起做，免得调用方漏掉一半。
 *
 * 推给壳的那一步，Rust 侧会**广播 `pet-prefs` 事件**，桌宠监听后立刻重渲染 ——
 * 所以设置页一改，桌宠马上跟着变，不用等轮询、也不用重启。
 */
export async function savePetPrefs(prefs) {
  const clean = normalizePetPrefs(prefs)
  try { localStorage.setItem(PET_PREFS_KEY, JSON.stringify(clean)) } catch {}
  if (!isDesktop) return clean
  try {
    const invoke = window.__TAURI__?.core?.invoke || window.__TAURI_INTERNALS__?.invoke
    if (typeof invoke === 'function') await invoke('set_pet_prefs', { prefs: clean })
  } catch (e) {
    console.warn('[desktop] 推送桌宠偏好失败:', e)
  }
  return clean
}

// ==================== 开机自启 ====================
//
// 走 tauri-plugin-autostart。它的命令是插件级的，不需要再写一层 Rust 包装 ——
// 直接按 `plugin:autostart|<cmd>` 调，ACL 里已放行 autostart:default。

/**
 * @returns {Promise<boolean|null>} true/false = 壳给的答案；**null = 问不到**
 *   （不在桌面壳里、或插件不可用）。别把 null 当 false —— 那会让开关
 *   在查不出来时假装"已关闭"，用户以为自启关了其实没关。
 */
export async function isAutostartEnabled() {
  if (!isDesktop) return null
  try {
    const invoke = window.__TAURI__?.core?.invoke || window.__TAURI_INTERNALS__?.invoke
    if (typeof invoke !== 'function') return null
    return !!(await invoke('plugin:autostart|is_enabled'))
  } catch (e) {
    console.warn('[desktop] 读开机自启状态失败:', e)
    return null
  }
}

/**
 * @returns {Promise<{ok: boolean, error?: string}>} 失败时把原因原样带出去
 *   （写注册表 Run 项在受管控的机器上会被拒，用户需要知道为什么）
 */
export async function setAutostart(on) {
  if (!isDesktop) return { ok: false, error: '不在桌面壳里' }
  try {
    const invoke = window.__TAURI__?.core?.invoke || window.__TAURI_INTERNALS__?.invoke
    if (typeof invoke !== 'function') return { ok: false, error: '拿不到 Tauri invoke' }
    await invoke(on ? 'plugin:autostart|enable' : 'plugin:autostart|disable')
    return { ok: true }
  } catch (e) {
    console.warn('[desktop] 设置开机自启失败:', e)
    return { ok: false, error: String((e && (e.message || e)) || e) }
  }
}

/**
 * 屏蔽网页专属行为，让操作手感变成「应用」而不是「网页」。
 * 只在桌面版调用。
 */
export function suppressWebBehaviors() {
  if (!isDesktop) return

  // ===== 拖动窗口 =====
  // 没有标题栏了，靠顶部一条窄带拖。但页面顶部往往有自己的按钮/输入框，
  // 所以落点如果压着可交互元素就【让位】—— 否则会把页面顶栏的点击全吃掉。
  // elementFromPoint 会跳过 pointer-events:none 的元素，所以悬浮的窗口按钮不会误判。
  const DRAG_STRIP_H = 30
  const INTERACTIVE = 'button, a, input, select, textarea, label, summary,' +
    '[role="button"], [contenteditable="true"], .el-button, .el-input, .el-select, .jz-wctl'

  function topStripTarget(e) {
    if (e.clientY > DRAG_STRIP_H) return null
    const el = document.elementFromPoint(e.clientX, e.clientY)
    if (el && el.closest && el.closest(INTERACTIVE)) return null
    return el || undefined   // undefined 表示"这块是空白/背景，可以拖"
  }

  document.addEventListener('mousedown', async (e) => {
    if (e.button !== 0) return
    if (topStripTarget(e) === null) return
    e.preventDefault()
    try { await currentWindow()?.startDragging() } catch (err) { /* 忽略 */ }
  })

  document.addEventListener('dblclick', (e) => {
    if (topStripTarget(e) === null) return
    winToggleMaximize()
  })

  // 右键菜单：先直接屏蔽。将来要做自定义菜单，在这里换成自己的实现。
  window.addEventListener('contextmenu', (e) => {
    const t = e.target
    // 输入框里保留右键（复制/粘贴是刚需）
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return
    e.preventDefault()
  })

  // Ctrl + 滚轮缩放：网页里会整体缩放，应用里非常出戏
  window.addEventListener('wheel', (e) => {
    if (e.ctrlKey) e.preventDefault()
  }, { passive: false })

  // 浏览器专属快捷键（F5 / Ctrl+R / Ctrl+P / Ctrl+U / F12 / Ctrl+Shift+I）
  // 原来在这里拦，现已收进 shortcuts/registry.js 的 `sys.block*` 内置动作。
  //
  // 为什么必须搬：这段监听和 GlobalSearch 的 Ctrl+K、以及用户自定义快捷键
  // 三者的先后**取决于监听器注册顺序** —— 那是个隐式依赖，
  // 一旦用户把 Ctrl+R 绑成别的动作，谁吃掉事件就变得不可预测。
  // 搬进注册表后优先级是显式的（见 shortcuts/manager.js 顶部的优先级表）。

  // 外链一律交给系统浏览器。
  // 用【捕获阶段】抢在浏览器默认行为之前 —— 否则 target="_blank" 要么没反应，
  // 要么弹出个没有地址栏、关不掉的怪窗口。
  document.addEventListener('click', (e) => {
    const a = e.target && e.target.closest ? e.target.closest('a[href]') : null
    if (!a) return
    const href = a.getAttribute('href') || ''
    if (!/^https?:\/\//i.test(href)) return   // 站内相对路径，交给 vue-router
    try {
      if (new URL(href, location.href).origin === location.origin) return  // 同源不算外链
    } catch { return }
    e.preventDefault()
    e.stopPropagation()
    openExternal(href)
  }, true)

  // 拖拽图片/链接会拖出一个幽灵图，网页味很重
  window.addEventListener('dragstart', (e) => {
    const t = e.target
    if (t && (t.tagName === 'IMG' || t.tagName === 'A')) e.preventDefault()
  })

  // 双击空白处选中文字 → 应用里不该发生（输入框除外，交给 CSS 处理）
  document.documentElement.classList.add('jz-desktop')
}
