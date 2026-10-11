import { ref } from 'vue'
import { getBadges, listMessages, getMessageSettings } from '@/api/messages'
import { colorOf, labelOf } from '@/utils/messageTypes'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// ============================================================
// 未读角标 + 桌面通知 —— 全站**唯一**的轮询点（2026-10-08）
//
// 改造前 `Sidebar` / `EdgeNavDock` / `XiaojiCall` **各自** 30 秒轮询同一个
// `/messages/badges` —— 首页三个都挂着，就是同页面 **3 份重复请求**
//（`Sidebar.vue:419` / `EdgeNavDock.vue:497` / `XiaojiCall.vue:2691`）。
// 现在只有这里一个计时器、一份共享状态，三个组件都从这里读。
//
// ## 弹窗规则（用户 2026-10-08 定）
//
//   · **能进消息中心的都弹** —— 不按 `priority` 筛
//   · **人在线**（页面可见）→ 新消息逐条弹
//   · **人不在线**（页面刚打开 / 从后台切回）→ 只弹**一条**累计
//     「有 N 条未读通知」，不逐条补弹（人不在的时候攒的，回来一次说清）
//   · 同时**最多 3 个**，超出的合并成「还有 N 条新消息」
//   · **正在消息中心页面时不弹** —— 用户正看着呢
//
// ## 怎么知道「有新消息」
//
// 每 30 秒拉一次 `/messages/badges`（**很便宜**：一次计数查询），
// 比对返回的 `latest.id` 有没有变。变了才去拉一次列表
//（`GET /messages?unread_only=1`，**全行查询，贵得多**）拿具体是哪几条。
// 所以常态下每 30 秒只有一个轻查询。
// ============================================================

const POLL_MS = 30000
const MAX_TOASTS = 3          // 同时最多几个（超出的合并）
const DND_TTL_MS = 5 * 60000  // 设置缓存 5 分钟，免得每轮都多查一次

export const badges = ref({ total: 0, groups: {}, types: {}, todos: 0, latest: null })
export const ready = ref(false)

let timer = null
let started = false
let lastLatestId = null       // 上次见到的「最新一条未读」id
let bootstrapped = false      // 是否已完成首次拉取
let missedWhileHidden = false // 期间人不在，攒着不弹
let dnd = { start: '', end: '' }
let dndAt = 0

function auth() { return useAuthStore() }

// ===== 免打扰：设置页那句「此时段内不弹桌面通知」就靠这个兑现 =====
async function loadDnd(force = false) {
  if (!force && Date.now() - dndAt < DND_TTL_MS) return
  try {
    const s = await getMessageSettings(auth().user?.id)
    dnd = { start: s?.dnd_start || '', end: s?.dnd_end || '' }
    dndAt = Date.now()
  } catch { /* 读不到就当成不免打扰 —— 宁可多弹，不可因为读失败就静默不弹 */ }
}

/** 现在是否在免打扰时段。支持跨午夜（22:00 → 07:00）。留空 = 不免打扰。 */
function inDnd() {
  const { start, end } = dnd
  if (!start || !end || start.length < 4 || end.length < 4) return false
  const now = new Date()
  const hm = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
  const a = start.slice(0, 5)
  const b = end.slice(0, 5)
  return a <= b ? (hm >= a && hm < b) : (hm >= a || hm < b)   // 后者 = 跨午夜
}

/** 正在消息中心页面？那就不用弹了 —— 用户正看着 */
function onMessagePage() {
  return router.currentRoute.value?.path === '/message'
}

// ============================================================
// 两个通道（2026-10-08 用户定）
//
//   页面在**前台**   → 页内 toast，**上部分居中**，3 秒，可叉，点了进详情
//   页面在**后台/最小化** → **系统通知**（Windows 自己放右下角），
//                          点它把窗口唤到前面并进详情
//
// ⚠️ **「应用完全没打开」做不到** —— 没有进程在看门。要那样得走后端推送
//    （Web Push / 厂商通道），是另一个量级的工程。
// ⚠️ 系统通知要用户授权。**授权拿不到时不静默丢弃**，退回
//    「攒着，切回来累计弹一条」—— 用户选了「当场弹系统通知」，
//    但「收不到且没人知道」比「晚一点收到」糟得多。
// ============================================================

const APP_NAME = '基智 · 多智能体学习平台'

/** 系统通知可用吗（浏览器/WebView2 支持 + 用户已授权） */
function sysNotifyReady() {
  return typeof Notification !== 'undefined' && Notification.permission === 'granted'
}

/** 申请一次授权。浏览器要求**用户手势**，所以挂在第一次点击上，只挂一次。 */
function ensurePermission() {
  if (typeof Notification === 'undefined' || Notification.permission !== 'default') return
  const ask = () => {
    try { Notification.requestPermission() } catch { /* 老浏览器没有 Promise 版，忽略 */ }
  }
  window.addEventListener('click', ask, { once: true })
}

/** 系统通知（右下角由操作系统决定，不归我们摆） */
function systemNotify({ title, message, id }) {
  try {
    const n = new Notification(title || APP_NAME, {
      body: message || '',
      icon: '/logo.png',
      // 同一条消息用同一个 tag —— 轮询重复命中时会替换而不是叠加
      tag: id || 'jizhi-msg',
    })
    n.onclick = () => {
      window.focus()                      // 把窗口唤到前面
      router.push(id ? `/message?open=${id}` : '/message')
      n.close()
    }
    return true
  } catch {
    return false                          // 平台不支持/被拦 —— 交给调用方退回页内
  }
}

// ============================================================
// 页内 toast —— **自己渲染一条，不用 ElNotification**（2026-10-08 改）
//
// 为什么弃用 ElNotification（它本来能用）：
//   ① 它只有四个角，**没有 top-center**，居中要跟它的 class 打架
//   ② 它会**往下堆叠** —— 一次来三条就往下长三格。用户要的是
//      「**覆盖**而不是堆积下去」：同一时刻**只显示一条**，新的顶掉旧的，
//      总高度恒定
//
// 长相照消息中心的列表行做（`.mc-card`）：左侧 3px 竖色条 + 方形图标 +
// 标题/时间一行 + 内容摘要一行 —— **长条、宽而扁**，不是方卡片。
// ============================================================

const TOP_MS = 3200          // 每条停留（用户定的 3 秒，留 200ms 给进出动画）
const MAX_QUEUE = 5          // 排队的上限，超出的合并成一条「还有 N 条」

const queue = []
let showing = false
let liveEl = null
let liveTimer = null

/** 把一条消息渲染成 DOM 并挂上去（同一时刻只有一条） */
function renderOne(item) {
  const el = document.createElement('div')
  el.className = 'jz-toast'
  el.style.setProperty('--c1', item.c1 || 'var(--brand)')
  el.style.setProperty('--c2', item.c2 || 'var(--brand)')
  const initial = (item.label || '·').slice(0, 1)
  const multi = item.count > 1 ? `<span class="jz-count">${item.count} 条</span>` : ''
  el.innerHTML = `
    <div class="jz-bar"></div>
    <div class="jz-ic">${initial}</div>
    <div class="jz-body">
      <div class="jz-top">
        <span class="jz-name">${item.title || '新消息'}</span>
        ${multi}
        <span class="jz-time">刚刚</span>
      </div>
      <div class="jz-preview">${item.message || ''}</div>
    </div>
    <button class="jz-x" title="关闭">✕</button>`

  const dismiss = () => {
    if (!el.isConnected) return
    clearTimeout(liveTimer)
    el.classList.add('out')
    setTimeout(() => { el.remove(); liveEl = null; drain() }, 200)
  }
  el.querySelector('.jz-x').addEventListener('click', (e) => {
    e.stopPropagation()                 // 叉掉 ≠ 点击进详情
    dismiss()
  })
  el.addEventListener('click', () => {
    router.push(item.id ? `/message?open=${item.id}` : '/message')
    dismiss()
  })

  document.body.appendChild(el)
  liveEl = el
  // 下一帧加 in —— 让 CSS 过渡能跑（同一个 tick 里加会没动画）
  requestAnimationFrame(() => el.classList.add('in'))
  liveTimer = setTimeout(dismiss, item.duration || TOP_MS)
}

/** 队列泵：同一时刻只显示一条，前一条走了才上后一条 */
function drain() {
  if (showing && liveEl) return
  const item = queue.shift()
  if (!item) { showing = false; return }
  showing = true
  renderOne(item)
}

function enqueue(items) {
  if (!items.length) return
  if (queue.length + items.length > MAX_QUEUE) {
    // 压太多就不逐条排了 —— 留前几条 + 一条合并
    const keep = Math.max(0, MAX_QUEUE - 1 - queue.length)
    const rest = items.length - keep
    items.slice(0, keep).forEach(i => queue.push(i))
    queue.push({
      title: `还有 ${rest} 条新消息`, message: '点这里进消息中心查看',
      duration: 4200,               // 合并那条给久一点
    })
  } else {
    items.forEach(i => queue.push(i))
  }
  drain()
}

function toastAggregate(n, viaSystem = false) {
  if (n <= 0) return
  const payload = { title: `有 ${n} 条未读通知`, message: '点这里进消息中心查看' }
  if (viaSystem && systemNotify(payload)) return
  enqueue([{ ...payload, duration: 5000 }])   // 累计的给久一点，信息更多
}

/** 投递。前台 → 页内长条（一条一条覆盖）；后台 → 系统通知 */
function toastMany(rows) {
  if (!rows.length) return
  if (sysNotifyReady() && document.visibilityState !== 'visible') {
    rows.forEach(r => systemNotify({
      title: r.title || '新消息', message: r.content || '', id: r.id,
    }))
    return
  }
  enqueue(rows.map(r => {
    const c = colorOf(r.type)
    return {
      id: r.id,
      title: r.title || labelOf(r.type) || '新消息',
      message: r.content || '',
      label: labelOf(r.type),        // 图标取它的首字
      count: r.msg_count,            // 聚合行显示「N 条」
      c1: c?.c1, c2: c?.c2,
    }
  }))
}

// ===== 轮询 =====
async function poll() {
  const uid = auth().user?.id
  if (!uid) return
  let data
  try {
    data = await getBadges(uid)
  } catch {
    return                    // 角标/弹窗失败绝不打断页面（与改造前的口径一致）
  }
  badges.value = data || badges.value
  ready.value = true

  const latestId = data?.latest?.id || null
  const visible = document.visibilityState === 'visible'

  if (!bootstrapped) {
    // 页面刚打开：已经有未读的话累计说一句（不逐条补弹历史消息）
    bootstrapped = true
    lastLatestId = latestId
    if ((data?.total || 0) > 0 && !onMessagePage()) {
      await loadDnd()
      if (!inDnd()) toastAggregate(data.total)
    }
    return
  }

  const changed = latestId && latestId !== lastLatestId
  lastLatestId = latestId

  // 正在消息中心页面：用户正看着列表，别在他眼皮底下弹。
  // 但要记一笔 —— 免得他离开这一页时补弹一堆。
  if (onMessagePage()) {
    if (changed) missedWhileHidden = true
    return
  }

  await loadDnd()
  if (inDnd()) { if (changed) missedWhileHidden = true; return }

  if (!changed) return

  // 在后台**且系统通知不可用**（没授权 / 平台不支持）→ 攒着，切回来累计说一句。
  // ⚠️ 不静默丢弃：用户选了「当场弹系统通知」，但「收不到且没人知道」
  //    比「晚一点收到」糟得多。授权到手后这条分支自然就失效了。
  if (!visible && !sysNotifyReady()) {
    missedWhileHidden = true
    return
  }

  // 拉具体是哪几条。
  // ⚠️ 这一步是全行查询，所以只在 `latest.id` 变了的时候做（见文件头）
  let rows = []
  try {
    const res = await listMessages({ user_id: uid, unread_only: true, page_size: 10 })
    rows = res?.items || []
  } catch {
    // 拉不到明细也要让用户知道「有新东西」—— 退回累计口径，别静默
    toastAggregate(data?.total || 0, !visible)
    return
  }

  // 前台 + 之前攒过（刚从消息中心出来、或授权后就补上）：先累计说一句，不逐条刷屏
  if (visible && missedWhileHidden) {
    missedWhileHidden = false
    toastAggregate(data?.total || 0)
    return
  }

  // 通道由 toastMany 内部按 `document.visibilityState` 选：
  // 前台 → 页内 toast（上部分居中）；后台 → 系统通知（右下角）
  toastMany(rows)
}

// ===== 生命周期：全站只起一次 =====
export function startNotifications() {
  if (started) return
  started = true
  ensurePermission()          // 挂在第一次点击上（浏览器要求用户手势）
  // 从后台切回时立刻补一次，别等下一个 30 秒
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') poll()
  })
  poll()
  timer = setInterval(poll, POLL_MS)
}

export function stopNotifications() {
  if (timer) { clearInterval(timer); timer = null }
  started = false
}

/** 组件用：读角标（**不再各自起计时器**，计时器只有 startNotifications 那一个）。
 *
 * `refresh()` 给「刚做完一件事、本地状态自己改了、想让角标立刻跟上」的场合用 ——
 * 比如标记已读 / 删除 / 全部已读。不调也能在下一轮（≤30 秒）自己更正，
 * 但那种「点了已读、角标还挂着红点」的延迟看着像没生效。
 */
export function useNotifications() {
  return { badges, ready, refresh: poll }
}
