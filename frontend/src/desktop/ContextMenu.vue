<!--
  桌面版的右键菜单（2026-10-01）。

  为什么需要它：`desktop/index.js` 的 `suppressWebBehaviors()` 原来把右键**整个屏蔽**了 ——
  在应用里弹出「网页版 Chrome 菜单」（查看源代码 / 投射 / 打印…）非常出戏。
  但屏蔽之后**右键就彻底没反应了**，而用户对右键是有肌肉记忆的。
  所以这里补一个自己的：**按落点变内容**，和正经桌面应用一样。

  结构（自上而下分组，空组不渲染、不留分隔线）：
    ① 链接上    —— 用浏览器打开 / 复制链接地址 / 复制链接文字
    ② 图片上    —— 图片另存为… / 复制图片地址
    ③ 有选中文字 —— 复制 / 搜索「…」（走应用内全局搜索）/ 在浏览器中搜索
    ④ 导航      —— 返回 / 前进 / 刷新 / 回到主界面
    ⑤ 工具      —— 全局搜索 / 复制页面地址 / 全选

  ⚠️ **只在桌面壳里生效**：网页版不挂这个组件（App.vue 里 v-if="isDesktop"），
     浏览器该有自己的菜单就还给它 —— 那是用户预期内的。

  ⚠️ **输入框放行**：INPUT / TEXTAREA / contenteditable 上不拦，
     交给 WebView 原生菜单 —— 剪切/复制/粘贴/拼写检查那些是刚需，
     自己重做一遍只会更差。
-->
<template>
  <Teleport to="body">
    <Transition name="jz-ctx">
      <div
        v-if="open"
        ref="menuRef"
        class="jz-ctx"
        :style="{ left: pos.x + 'px', top: pos.y + 'px' }"
        @contextmenu.prevent
      >
        <template v-for="(it, i) in items" :key="i">
          <div v-if="it.sep" class="jz-ctx-sep"></div>
          <button v-else class="jz-ctx-item" @click="run(it)">
            <span class="jz-ctx-icon">{{ it.icon }}</span>
            <span class="jz-ctx-label">{{ it.label }}</span>
            <span v-if="it.hint" class="jz-ctx-hint">{{ it.hint }}</span>
          </button>
        </template>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { openExternal, saveBlobNative } from './index.js'
import { collectCtxItems, copyText } from './ctxMenu.js'
import { useNavStore } from '@/stores/nav'

const router = useRouter()
const navStore = useNavStore()

const open = ref(false)
const pos = ref({ x: 0, y: 0 })
const rawItems = ref([])
const menuRef = ref(null)

// 分隔线不能出现在开头/结尾，也不能连着两条 —— 空组本来就该整组消失
const items = computed(() => {
  const out = []
  for (const it of rawItems.value) {
    if (it.sep) {
      if (!out.length || out[out.length - 1].sep) continue
      out.push(it)
    } else out.push(it)
  }
  while (out.length && out[out.length - 1].sep) out.pop()
  return out
})

// ==================== 动作 ====================

// copyText 现在住在 ctxMenu.js —— 页面自己注册的项（复制题干、复制分享链接）
// 也要用它，兜底逻辑只该有一份。

/** 全选页面内容 */
function selectAll() {
  try {
    const range = document.createRange()
    range.selectNodeContents(document.body)
    const sel = window.getSelection()
    sel.removeAllRanges()
    sel.addRange(range)
  } catch { /* 忽略 */ }
}

/** 从 URL / MIME 推一个像样的文件名（另存为对话框的默认名） */
function guessFileName(src, mime) {
  const fromMime = String(mime || '').split('/')[1]
  const ext = (fromMime ? fromMime.replace('jpeg', 'jpg').split('+')[0] : 'png') || 'png'
  try {
    const base = new URL(src, location.href).pathname.split('/').pop() || ''
    if (/\.(png|jpe?g|gif|webp|svg|bmp|avif)$/i.test(base)) return base
  } catch { /* URL 解析失败就用兜底名 */ }
  return `image.${ext}`
}

/** 图片另存为：抓 blob → 交给壳弹原生保存框 */
async function saveImage(img) {
  const src = img.currentSrc || img.src
  if (!src) return
  try {
    const res = await fetch(src, { mode: 'cors', credentials: 'omit' })
    if (!res.ok) throw new Error('HTTP ' + res.status)
    const blob = await res.blob()
    const saved = await saveBlobNative(blob, guessFileName(src, blob.type))
    if (saved) ElMessage.success('已保存')
    // saved=false 是「用户取消了保存框」，不是错误，不提示
  } catch (e) {
    // ⚠️ 跨域图片若没带 CORS 头，fetch 必然失败 —— 这是浏览器安全模型决定的，
    //    没有绕过的正当办法（canvas 也会被污染）。所以如实说清楚，
    //    并把「复制图片地址」作为能走通的替代方案留给用户。
    console.warn('[ctx] 图片另存为失败:', e)
    ElMessage.warning('这张图片不允许读取（跨域限制），可以先「复制图片地址」再用浏览器打开')
  }
}

function close() { open.value = false }

async function run(it) {
  close()
  try { await it.run() } catch (e) { console.warn('[ctx] 菜单动作失败:', e) }
}

// ==================== 按落点组菜单 ====================

function buildItems(e) {
  const list = []
  const el = e.target
  const linkEl = el && el.closest ? el.closest('a[href]') : null
  const imgEl = el && el.closest ? el.closest('img') : null
  const sel = String(window.getSelection?.()?.toString() || '').trim()

  // ⓪ 页面自己贡献的项，**排在最上面**。
  //    好应用的右键顺序是「先说这个位置能干什么，再说通用的那套」——
  //    在视频卡片上右键，用户要的是「播放 / 收藏」，不是「全选」。
  list.push(...collectCtxItems(el, sel))

  // ① 链接
  if (linkEl && linkEl.href) {
    list.push({ icon: '🌐', label: '用浏览器打开', run: () => openExternal(linkEl.href) })
    list.push({ icon: '🔗', label: '复制链接地址', run: () => copyText(linkEl.href, '链接') })
    const t = String(linkEl.textContent || '').trim()
    if (t) list.push({ icon: '📋', label: '复制链接文字', run: () => copyText(t, '文字') })
    list.push({ sep: true })
  }

  // ② 图片
  if (imgEl && (imgEl.currentSrc || imgEl.src)) {
    const src = imgEl.currentSrc || imgEl.src
    list.push({ icon: '💾', label: '图片另存为…', run: () => saveImage(imgEl) })
    list.push({ icon: '🔗', label: '复制图片地址', run: () => copyText(src, '图片地址') })
    list.push({ sep: true })
  }

  // ③ 选中文字
  if (sel) {
    const short = sel.length > 10 ? sel.slice(0, 10) + '…' : sel
    list.push({ icon: '📋', label: '复制', run: () => copyText(sel, '选中内容') })
    list.push({
      icon: '🔎',
      label: `搜索「${short}」`,
      hint: '应用内',
      run: () => navStore.openSearchWith(sel),
    })
    list.push({
      icon: '🌐',
      label: '在浏览器中搜索',
      run: () => openExternal('https://www.baidu.com/s?wd=' + encodeURIComponent(sel)),
    })
    list.push({ sep: true })
  }

  // ④ 导航
  list.push({ icon: '↩', label: '返回', run: () => router.back() })
  list.push({ icon: '↪', label: '前进', run: () => router.forward() })
  list.push({ icon: '⟳', label: '刷新', run: () => window.location.reload() })
  list.push({ icon: '🏠', label: '回到主界面', run: () => router.push('/home') })
  list.push({ sep: true })

  // ⑤ 工具
  list.push({
    icon: '🔍',
    label: '全局搜索',
    hint: 'Ctrl+K',
    run: () => navStore.openSearch(),
  })
  list.push({
    icon: '🔗',
    label: '复制页面地址',
    run: () => copyText(window.location.href, '页面地址'),
  })
  list.push({ icon: '▭', label: '全选', run: selectAll })

  return list
}

/** 把菜单夹在视口内 —— 贴着右/下边缘右键时不能有一半跑到屏幕外 */
async function placeAt(x, y) {
  pos.value = { x, y }
  await nextTick()
  const m = menuRef.value
  if (!m) return
  const r = m.getBoundingClientRect()
  const pad = 6
  const nx = Math.min(x, window.innerWidth - r.width - pad)
  const ny = Math.min(y, window.innerHeight - r.height - pad)
  pos.value = { x: Math.max(pad, nx), y: Math.max(pad, ny) }
}

function onContextMenu(e) {
  const t = e.target
  // 输入框放行原生菜单（剪切/复制/粘贴/拼写检查是刚需）
  if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return
  e.preventDefault()
  rawItems.value = buildItems(e)
  open.value = true
  placeAt(e.clientX, e.clientY)
}

// 失焦即关：滚动、缩放、按 Esc、点到别处，菜单都不该赖着不走
function onScrollOrResize() { if (open.value) close() }
function onKey(e) { if (e.key === 'Escape' && open.value) close() }
function onMouseDown(e) {
  if (!open.value) return
  if (menuRef.value && menuRef.value.contains(e.target)) return   // 点菜单自身交给 @click
  close()
}

onMounted(() => {
  window.addEventListener('contextmenu', onContextMenu)
  window.addEventListener('mousedown', onMouseDown, true)
  window.addEventListener('blur', close)
  window.addEventListener('resize', onScrollOrResize)
  window.addEventListener('scroll', onScrollOrResize, true)   // 捕获：页面内部滚动容器也要能关掉它
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => {
  window.removeEventListener('contextmenu', onContextMenu)
  window.removeEventListener('mousedown', onMouseDown, true)
  window.removeEventListener('blur', close)
  window.removeEventListener('resize', onScrollOrResize)
  window.removeEventListener('scroll', onScrollOrResize, true)
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.jz-ctx {
  position: fixed;
  z-index: 2147483000;   /* 高于页面里的一切；窗口按钮是 100000 */
  min-width: 208px;
  padding: 5px;
  border-radius: 10px;
  background: var(--card-bg, rgba(28, 28, 40, .96));
  border: 1px solid var(--line-soft, rgba(255, 255, 255, .12));
  box-shadow: 0 10px 30px rgba(0, 0, 0, .38);
  backdrop-filter: blur(18px) saturate(1.2);
  -webkit-backdrop-filter: blur(18px) saturate(1.2);
}
.jz-ctx-item {
  display: flex; align-items: center; gap: 9px;
  width: 100%; padding: 7px 10px;
  border: none; border-radius: 7px; background: transparent;
  font-family: inherit; font-size: 13px; text-align: left;
  color: var(--text-primary, #e8e8f0);
  cursor: default;
}
.jz-ctx-item:hover { background: color-mix(in srgb, var(--brand, #409EFF) 20%, transparent); }
.jz-ctx-icon { width: 16px; text-align: center; font-size: 12px; opacity: .85; }
.jz-ctx-label { flex: 1; white-space: nowrap; }
.jz-ctx-hint { font-size: 11px; color: var(--text-muted, #8888aa); padding-left: 14px; }
.jz-ctx-sep { height: 1px; margin: 4px 8px; background: var(--line-soft, rgba(255, 255, 255, .1)); }

.jz-ctx-enter-active, .jz-ctx-leave-active { transition: opacity .12s ease, transform .12s ease; }
.jz-ctx-enter-from, .jz-ctx-leave-to { opacity: 0; transform: scale(.96); }
</style>
