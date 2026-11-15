// ============================================================
// 记忆流（2026-11-04）
//
// 页面驻扎小基的「路线记忆」，不是最近访问列表：
//   · 上次锚点：跨会话记住停在哪一页；
//   · 页面权重：有效停留 >= 5s 才算一次，按 14 天半衰期衰减；
//   · 方向边 A→B：有方向的转移，10 分钟内、有交互才算数；
//   · 建议必须有证据（次数 / 占比 / 与次优的差距），宁可不推；
//   · 用户点「不太准」→ 这条边降权并静默 3 天。
//
// 只存页面路径、时间和点击，不存页面内容；按用户隔离存在本机 localStorage。
// 后续如果要跨设备，再把结果批量同步到 agent_memory，不要把每次导航都发网络。
// ============================================================

const KEY_PREFIX = 'jz_route_memory_v1'
const VERSION = 1

const HALF_LIFE = 14 * 24 * 60 * 60 * 1000   // 权重半衰期：两周
const MIN_DWELL = 5000                        // 页面停留 >= 5s 才算一次访问
const MIN_EDGE_DWELL = 1000                   // 离开页面时至少待过 1s 才记转移
const TRANSITION_WINDOW = 10 * 60 * 1000      // 10 分钟内、且有交互，才算 A→B
const SESSION_GAP = 30 * 60 * 1000            // 30 分钟没动 → 下次打开算新会话
const RESUME_MAX_AGE = 14 * 24 * 60 * 60 * 1000
const PRUNE_AFTER = 60 * 24 * 60 * 60 * 1000  // 60 天没碰过的页面淡出
const MAX_PAGES = 50
const MAX_EDGES_PER_PAGE = 6
const MUTE_MS = 3 * 24 * 60 * 60 * 1000

const MIN_EDGE_N = 3          // 「下一步」至少走过 3 次
const MIN_EDGE_P = 0.4        // 至少占该页出边的 40%
const MIN_EDGE_EFF = 1.2      // 衰减后的有效次数
const MIN_MARGIN = 1.3        // 与次优差距不足 1.3 倍就不猜

const EXCLUDED = [
  /^\/$/, /^\/login(\/|$)/, /^\/onboarding(\/|$)/,
  /^\/agreement(\/|$)/, /^\/privacy(\/|$)/,
  /^\/admin(\/|$)/, /^\/animation-demo(\/|$)/, /^\/vlp-debug(\/|$)/,
]

const runtime = {
  installed: false,
  router: null,
  getUid: null,
  uid: '',
  state: null,
  current: null,
  sessionAnchor: null,
  sessionReady: false,
  saveTick: 0,
}

function nowMs() { return Date.now() }

function emptyState() {
  return {
    v: VERSION,
    updatedAt: 0,
    last: null,      // { key, path, fullPath, at }
    pages: {},       // key -> { w, n, dwell, last, path, fullPath }
    edges: {},       // fromKey -> toKey -> { w, n, last, accept, reject, mutedUntil, path, fullPath }
    stats: {},
    customRoute: null, // 用户自己设的固定路线：{ steps: [{key,path,title}], updatedAt }
  }
}

function storageKey(uid) { return `${KEY_PREFIX}:${uid}` }

function isExcluded(path) {
  const p = String(path || '')
  return EXCLUDED.some(re => re.test(p))
}

function decay(w, elapsedMs) {
  if (!Number.isFinite(w) || w <= 0) return 0
  const ms = Math.max(0, Number(elapsedMs) || 0)
  return w * Math.pow(0.5, ms / HALF_LIFE)
}

function pageEff(p, now) {
  if (!p) return 0
  return decay(Number(p.w) || 0, now - (Number(p.last) || now))
}

function edgeEff(e, now) {
  if (!e) return 0
  return decay(Number(e.w) || 0, now - (Number(e.last) || now))
}

function activeMs(cur, now) {
  if (!cur) return 0
  const base = Number(cur.activeMs) || 0
  if (cur.hiddenAt) return base
  return base + Math.max(0, now - (Number(cur.activeSince) || now))
}

/**
 * 路由 → 页面 key。动态参数收敛成同一个页面：
 * /subject-plan/abc/practice → /subject-plan/:syllabusId/practice
 */
export function pageKeyOf(route) {
  const path = (route && route.path) || '/'
  let key = ''
  const matched = route && route.matched
  if (matched && matched.length) {
    const rec = matched[matched.length - 1]
    if (rec && rec.path) key = rec.path
  }
  if (!key) {
    key = path
    const params = (route && route.params) || {}
    for (const [name, value] of Object.entries(params)) {
      if (value === undefined || value === null || value === '') continue
      key = key.replace(`/${value}`, `/:${name}`)
    }
  }
  if (key.length > 1) key = key.replace(/\/+$/, '')
  return key || '/'
}

function normalizeState(raw) {
  if (!raw || raw.v !== VERSION) return emptyState()
  let customRoute = null
  if (raw.customRoute && Array.isArray(raw.customRoute.steps)) {
    const steps = raw.customRoute.steps
      .filter(s => s && s.path)
      .slice(0, 10)
      .map(s => ({
        key: s.key || s.path,
        path: s.path,
        title: s.title || '',
      }))
    if (steps.length >= 2) {
      customRoute = { steps, updatedAt: Number(raw.customRoute.updatedAt) || 0 }
    }
  }
  return {
    v: VERSION,
    updatedAt: Number(raw.updatedAt) || 0,
    last: raw.last && raw.last.key ? { ...raw.last } : null,
    pages: raw.pages && typeof raw.pages === 'object' ? raw.pages : {},
    edges: raw.edges && typeof raw.edges === 'object' ? raw.edges : {},
    stats: raw.stats && typeof raw.stats === 'object' ? raw.stats : {},
    customRoute,
  }
}

function loadState(uid) {
  try {
    const raw = localStorage.getItem(storageKey(uid))
    if (!raw) return emptyState()
    return normalizeState(JSON.parse(raw))
  } catch {
    return emptyState()
  }
}

function saveState(st, now, force = false) {
  if (!st || !runtime.uid) return
  const t = now || nowMs()
  st.updatedAt = t
  runtime.saveTick += 1
  if (force || runtime.saveTick % 20 === 0) prune(st, t)
  try {
    localStorage.setItem(storageKey(runtime.uid), JSON.stringify(st))
  } catch { /* 隐私模式 / 配额满：记忆流失效，不影响页面 */ }
}

function prune(st, now) {
  if (!st) return
  for (const [key, p] of Object.entries(st.pages || {})) {
    if (now - (Number(p.last) || 0) > PRUNE_AFTER) delete st.pages[key]
  }
  for (const [from, row] of Object.entries(st.edges || {})) {
    if (!st.pages[from]) { delete st.edges[from]; continue }
    for (const [to, e] of Object.entries(row || {})) {
      if (!st.pages[to] && now - (Number(e.last) || 0) > PRUNE_AFTER) delete row[to]
    }
  }
  // 页面太多时按最近使用裁剪；边跟着页面一起裁
  const pages = Object.entries(st.pages || {})
    .sort((a, b) => (Number(b[1].last) || 0) - (Number(a[1].last) || 0))
    .slice(0, MAX_PAGES)
  st.pages = Object.fromEntries(pages)
  for (const from of Object.keys(st.edges || {})) {
    if (!st.pages[from]) { delete st.edges[from]; continue }
    trimEdges(st.edges[from], now)
  }
}

function trimEdges(row, now) {
  if (!row) return
  const items = Object.entries(row)
    .sort((a, b) => edgeEff(b[1], now) - edgeEff(a[1], now))
    .slice(0, MAX_EDGES_PER_PAGE)
  for (const key of Object.keys(row)) {
    if (!items.some(([k]) => k === key)) delete row[key]
  }
}

function ensureState(uid) {
  if (!uid) return null
  if (runtime.uid !== uid) {
    runtime.uid = uid
    runtime.state = loadState(uid)
    runtime.current = null
    runtime.sessionAnchor = null
    runtime.sessionReady = false
    runtime.saveTick = 0
    prune(runtime.state, nowMs())
  }
  if (!runtime.state) runtime.state = emptyState()
  return runtime.state
}

function ensureSessionAnchor(st, now) {
  if (!st || runtime.sessionReady) return
  runtime.sessionReady = true
  const last = st.last
  if (!last || !last.key || !last.path) return
  // 首页是默认落点，拿它当「上次」没有意义
  if (last.key === '/home') return
  const age = now - (Number(last.at) || 0)
  if (age >= SESSION_GAP && age <= RESUME_MAX_AGE) {
    runtime.sessionAnchor = { ...last }
  }
}

function snapshotRoute(route) {
  if (!route || !route.path || isExcluded(route.path)) return null
  return {
    key: pageKeyOf(route),
    path: route.path,
    fullPath: route.fullPath || route.path,
  }
}

function recordPage(st, snap, dwell, now) {
  const p = st.pages[snap.key] || {
    w: 0, n: 0, dwell: 0, last: 0, path: snap.path, fullPath: snap.fullPath,
  }
  p.w = decay(Number(p.w) || 0, now - (Number(p.last) || now)) + 1
  p.n = Math.min(9999, (Number(p.n) || 0) + 1)
  p.dwell = Math.min(30 * 24 * 3600, (Number(p.dwell) || 0) + Math.round(dwell / 1000))
  p.last = now
  p.path = snap.path
  p.fullPath = snap.fullPath
  st.pages[snap.key] = p
}

function recordEdge(st, fromKey, toSnap, now) {
  const row = st.edges[fromKey] || {}
  const e = row[toSnap.key] || {
    w: 0, n: 0, last: 0, accept: 0, reject: 0, mutedUntil: 0,
  }
  e.w = decay(Number(e.w) || 0, now - (Number(e.last) || now)) + 1
  e.n = Math.min(9999, (Number(e.n) || 0) + 1)
  e.last = now
  e.path = toSnap.path
  e.fullPath = toSnap.fullPath
  row[toSnap.key] = e
  st.edges[fromKey] = row
  trimEdges(row, now)
}

function flushVisit(cur, now) {
  if (!cur || cur.visitRecorded) return
  const st = runtime.state
  if (!st) return
  const dwell = activeMs(cur, now)
  if (dwell < MIN_DWELL) return
  recordPage(st, cur, dwell, now)
  cur.visitRecorded = true
  saveState(st, now)
}

/**
 * 当前页最有把握的下一步。
 * relaxed=true 用于路线第二跳，门槛略低一点。
 */
function bestNext(st, key, now, relaxed = false) {
  const row = st.edges[key]
  if (!row) return null
  const items = []
  let total = 0
  for (const [toKey, e] of Object.entries(row)) {
    if (e.mutedUntil && Number(e.mutedUntil) > now) continue
    const eff = edgeEff(e, now)
    if (eff <= 0) continue
    items.push({
      key: toKey,
      eff,
      n: Number(e.n) || 0,
      p: 0,
      path: e.path,
      fullPath: e.fullPath,
    })
    total += eff
  }
  if (!items.length || total <= 0) return null
  for (const it of items) it.p = it.eff / total
  items.sort((a, b) => b.eff - a.eff)

  const top = items[0]
  const second = items[1]
  const minN = relaxed ? 2 : MIN_EDGE_N
  const minP = relaxed ? 0.32 : MIN_EDGE_P
  const minEff = relaxed ? 0.9 : MIN_EDGE_EFF
  if (!top.path || String(top.path).includes('/:')) return null
  if (top.n < minN || top.p < minP || top.eff < minEff) return null
  if (!relaxed && second && second.n >= MIN_EDGE_N && top.eff < second.eff * MIN_MARGIN) {
    return null
  }
  return top
}

/**
 * 读当前页的「记忆流」建议。
 * 返回 { suggestions, resume, route }：
 *   suggestions 最多 2 条（接着上次 / 下一步常去），route 是 3 步常走路线。
 */
export function getMemoryFlow(uid, currentKey, opts = {}) {
  const st = ensureState(uid)
  if (!st) return { suggestions: [], resume: null, route: [] }
  const now = Number(opts.now) || nowMs()
  ensureSessionAnchor(st, now)

  if (runtime.sessionAnchor && runtime.sessionAnchor.key === currentKey) {
    runtime.sessionAnchor = null
  }

  const suggestions = []
  if (runtime.sessionAnchor) {
    suggestions.push({
      id: 'resume',
      type: 'resume',
      fromKey: currentKey,
      key: runtime.sessionAnchor.key,
      path: runtime.sessionAnchor.fullPath || runtime.sessionAnchor.path,
      titleKey: runtime.sessionAnchor.path,
      reason: '接着上次',
    })
  }

  const next = bestNext(st, currentKey, now)
  if (next) {
    const target = next.fullPath || next.path
    // 同一个页面被「接着上次」和「下一步」同时命中时只留一条
    const dup = suggestions.some(s => s.key === next.key)
    if (!dup) {
      suggestions.push({
        id: `next:${currentKey}>${next.key}`,
        type: 'next',
        fromKey: currentKey,
        key: next.key,
        path: target,
        titleKey: next.path,
        reason: '下一步常去',
        confidence: Math.round(next.p * 100) / 100,
        support: next.n,
      })
    }
  }

  const route = []
  if (next) {
    const cur = st.pages[currentKey]
    route.push({
      key: currentKey,
      path: opts.currentPath || cur?.path || currentKey,
      titleKey: opts.currentPath || cur?.path || currentKey,
    })
    route.push({ key: next.key, path: next.path, titleKey: next.path })
    const next2 = bestNext(st, next.key, now, true)
    if (next2 && next2.path) {
      route.push({ key: next2.key, path: next2.path, titleKey: next2.path })
    }
  }

  return {
    suggestions: suggestions.slice(0, 2),
    resume: suggestions.find(s => s.type === 'resume') || null,
    route: route.length >= 3 ? route : [],
  }
}

/** 用户点了建议：强化这条边；「接着上次」只清锚点。 */
export function acceptSuggestion(uid, s) {
  const st = ensureState(uid)
  if (!st || !s) return
  const now = nowMs()
  if (s.type === 'resume') {
    runtime.sessionAnchor = null
    st.stats.resume_accept = (Number(st.stats.resume_accept) || 0) + 1
    saveState(st, now)
    return
  }
  if (s.type === 'next' && s.fromKey) {
    const e = st.edges[s.fromKey] && st.edges[s.fromKey][s.key]
    if (e) {
      e.w = decay(Number(e.w) || 0, now - (Number(e.last) || now)) + 1.5
      e.accept = (Number(e.accept) || 0) + 1
      e.last = now
      saveState(st, now)
    }
  }
}

/** 用户点「不太准」：降权 + 静默 3 天。 */
export function rejectSuggestion(uid, s) {
  const st = ensureState(uid)
  if (!st || !s) return
  const now = nowMs()
  if (s.type === 'resume') {
    runtime.sessionAnchor = null
    st.stats.resume_reject = (Number(st.stats.resume_reject) || 0) + 1
    saveState(st, now)
    return
  }
  if (s.type === 'next' && s.fromKey) {
    const e = st.edges[s.fromKey] && st.edges[s.fromKey][s.key]
    if (e) {
      e.w = decay(Number(e.w) || 0, now - (Number(e.last) || now)) * 0.35
      e.reject = (Number(e.reject) || 0) + 1
      e.mutedUntil = now + MUTE_MS
      e.last = now
      saveState(st, now)
    }
  }
}

/** 这一轮先不提醒「接着上次」；下次打开还会重新判断。 */
export function dismissResume(uid) {
  if (uid && runtime.uid !== uid) ensureState(uid)
  runtime.sessionAnchor = null
}

/** 用户主动清空：忘掉学习出来的路线，但保留用户自己设的固定路线。 */
export function clearRouteMemory(uid) {
  const keep = runtime.uid === uid ? runtime.state?.customRoute || null : null
  if (uid) {
    try { localStorage.removeItem(storageKey(uid)) } catch { /* ignore */ }
  }
  if (runtime.uid === uid) {
    runtime.state = emptyState()
    runtime.sessionAnchor = null
    runtime.sessionReady = true
    // 当前这次访问不再补记，避免「刚清空又长回来」
    if (runtime.current) runtime.current.visitRecorded = true
    // 有「我的路线」才写回；否则让 storage key 保持不存在
    if (keep) {
      runtime.state.customRoute = keep
      saveState(runtime.state, nowMs(), true)
    }
  }
}

/** 上次锚点：2D 校园用它决定小基先带你去哪。 */
export function getLastAnchor(uid) {
  const st = ensureState(uid)
  return st?.last ? { ...st.last } : null
}

/** 用户自己设的固定路线（与学习出来的记忆分开）。 */
export function getCustomRoute(uid) {
  const st = ensureState(uid)
  const route = st && st.customRoute
  if (!route || !Array.isArray(route.steps) || route.steps.length < 2) return null
  return { steps: route.steps.map(s => ({ ...s })), updatedAt: route.updatedAt || 0 }
}

export function saveCustomRoute(uid, steps) {
  const st = ensureState(uid)
  if (!st || !Array.isArray(steps)) return false
  const clean = steps
    .filter(s => s && s.path)
    .slice(0, 10)
    .map(s => ({
      key: s.key || s.path,
      path: s.path,
      title: s.title || '',
    }))
  if (clean.length < 2) return false
  st.customRoute = { steps: clean, updatedAt: nowMs() }
  saveState(st, nowMs(), true)
  return true
}

export function clearCustomRoute(uid) {
  const st = ensureState(uid)
  if (!st) return false
  st.customRoute = null
  saveState(st, nowMs(), true)
  return true
}

/**
 * 「我的路线」按当前位置给下一步：
 *   - 当前页在路线中间 → 下一站
 *   - 当前页是终点 → 回起点（起点就是当前页时不重复推）
 *   - 当前页不在路线里 → 去起点
 */
export function nextCustomStep(steps, currentKey) {
  if (!Array.isArray(steps) || steps.length < 2) return null
  const idx = steps.findIndex(s => s && s.key === currentKey)
  if (idx < 0) {
    return { ...steps[0], type: 'custom', reason: '去你的路线起点' }
  }
  if (idx >= steps.length - 1) {
    const first = steps[0]
    if (first.key === currentKey) return null
    return { ...first, type: 'custom', reason: '路线走完了，回起点' }
  }
  return { ...steps[idx + 1], type: 'custom', reason: '按你的路线走' }
}

/**
 * 在应用入口调用一次。
 * @param {import('vue-router').Router} router
 * @param {() => string|undefined} getUid
 */
export function installRouteMemory(router, getUid) {
  if (runtime.installed) return
  runtime.installed = true
  runtime.router = router
  runtime.getUid = getUid

  const uidOf = () => {
    try { return getUid && getUid() } catch { return '' }
  }

  router.afterEach((to) => {
    try { handleNavigation(to, uidOf()) } catch (e) {
      console.warn('[route-memory] 记录失败（忽略）:', e)
    }
  })

  // 初始导航通常在 afterEach 之前完成；这里兜一次，避免首屏那次没记上
  router.isReady().then(() => {
    if (!runtime.current) {
      try { handleNavigation(router.currentRoute.value, uidOf()) } catch { /* ignore */ }
    }
  }).catch(() => {})

  // 有交互才算「还在这一页」；滚动也算，读长文不是离开
  const onActivity = () => {
    const cur = runtime.current
    if (!cur) return
    const now = nowMs()
    if (now - (Number(cur.lastActiveAt) || 0) >= 500) cur.lastActiveAt = now
  }
  for (const ev of ['pointerdown', 'keydown', 'wheel', 'touchstart', 'scroll']) {
    window.addEventListener(ev, onActivity, { passive: true, capture: true })
  }

  document.addEventListener('visibilitychange', () => {
    const cur = runtime.current
    if (!cur) return
    const now = nowMs()
    if (document.hidden) {
      cur.activeMs = activeMs(cur, now)   // 结算到最后一次可见为止
      cur.hiddenAt = now
    } else {
      cur.activeSince = now
      cur.lastActiveAt = now
      cur.hiddenAt = 0
    }
  })

  window.addEventListener('pagehide', () => {
    try {
      const now = nowMs()
      const cur = runtime.current
      if (!cur) return
      flushVisit(cur, now)
      // 离开时间按最后一次活动算；下次打开据此判断是不是新会话
      if (runtime.state?.last && runtime.state.last.key === cur.key) {
        runtime.state.last.at = now
        saveState(runtime.state, now)
      }
    } catch { /* ignore */ }
  })

  window.addEventListener('pageshow', (e) => {
    if (!e.persisted) return
    const cur = runtime.current
    if (!cur) return
    cur.activeSince = nowMs()
    cur.lastActiveAt = nowMs()
    cur.hiddenAt = 0
  })
}

function handleNavigation(to, uid) {
  const now = nowMs()

  if (!uid) {
    if (runtime.current) flushVisit(runtime.current, now)
    runtime.current = null
    return
  }

  // 换账号：先把上一个人的最后一页结算掉，再加载新用户的记忆
  if (runtime.current && runtime.uid && runtime.uid !== uid) {
    flushVisit(runtime.current, now)
  }
  const st = ensureState(uid)
  if (!st) { runtime.current = null; return }
  ensureSessionAnchor(st, now)

  const trackable = !!(to && to.meta && to.meta.requiresAuth) && !isExcluded(to.path)
  const next = trackable ? snapshotRoute(to) : null
  const prev = runtime.current

  // 同一页只改 query / hash：不重算停留，也不记转移
  if (prev && next && prev.key === next.key) {
    prev.path = next.path
    prev.fullPath = next.fullPath
    st.last = { key: prev.key, path: prev.path, fullPath: prev.fullPath, at: now }
    saveState(st, now)
    return
  }

  if (prev) {
    flushVisit(prev, now)
    if (next && prev.key !== next.key) {
      const dwell = activeMs(prev, now)
      const activeRecently = now - (Number(prev.lastActiveAt) || 0) <= TRANSITION_WINDOW
      if (dwell >= MIN_EDGE_DWELL && activeRecently) {
        recordEdge(st, prev.key, next, now)
      }
    }
  }

  if (!next) {
    runtime.current = null
    saveState(st, now)
    return
  }

  if (runtime.sessionAnchor && runtime.sessionAnchor.key === next.key) {
    runtime.sessionAnchor = null
  }

  st.last = { key: next.key, path: next.path, fullPath: next.fullPath, at: now }
  runtime.current = {
    ...next,
    enteredAt: now,
    activeSince: now,
    activeMs: 0,
    lastActiveAt: now,
    hiddenAt: 0,
    visitRecorded: false,
  }
  saveState(st, now)
}
