<template>
  <Teleport to="body">
    <Transition name="gs">
      <div v-if="navStore.searchOpen" class="gs-overlay" @mousedown.self="close">
        <div class="gs-panel" role="dialog" aria-label="全局搜索">
          <!-- 输入行 -->
          <div class="gs-input-row">
            <i class="fas fa-search gs-input-icon" />
            <input
              ref="inputEl"
              v-model="query"
              class="gs-input"
              placeholder="搜索页面、考纲、真题、智能体、词条…"
              @keydown="onKeydown"
              @input="onInput"
            />
            <button class="gs-esc" title="关闭 (Esc)" @click="close">Esc</button>
          </div>

          <div class="gs-body">
            <!-- 快捷入口选择器：列出全部可进入的页面，点选收录到自定义 -->
            <template v-if="pickerOpen">
              <div class="gs-picker-header">
                <span class="gs-picker-title">添加快捷入口</span>
                <button class="gs-chip" @click="pickerOpen = false">← 返回</button>
              </div>
              <p class="gs-picker-tip">全部可快捷进入的页面：点击「＋ 添加」收录到自定义，再点一次移除；上方输入框可筛选。</p>
              <template v-for="g in pickerGroups" :key="g.key">
                <div class="gs-group">
                  <div class="gs-label">
                    {{ g.label }}<span class="gs-count">{{ g.items.length }}</span>
                  </div>
                  <div v-for="it in g.items" :key="it.path" class="gs-item">
                    <span class="gs-type" :class="g.key">{{ g.tag }}</span>
                    <div class="gs-item-main">
                      <div class="gs-item-title">{{ it.title }}</div>
                      <div class="gs-item-sub">{{ it.path }}</div>
                    </div>
                    <button class="gs-pick-btn" :class="{ added: isAdded(it) }" @click.stop="toggleCustom(it)">
                      {{ isAdded(it) ? '✓ 已添加' : '＋ 添加' }}
                    </button>
                  </div>
                </div>
              </template>
              <div v-if="!pickerTotal" class="gs-empty">没有找到与「{{ query }}」相关的内容</div>
            </template>

            <!-- 空查询：最近访问 + 搜索历史 + 自定义项（均可增删改） -->
            <template v-else-if="!query.trim()">
              <div v-if="recent.length" class="gs-group">
                <div class="gs-label">
                  最近访问
                  <button class="gs-clear" @click="navStore.clearRecent()">清空</button>
                </div>
                <div v-for="r in recent" :key="r.path" class="gs-item" @click="jumpTo(r.path)">
                  <i class="fas fa-clock gs-clock" />
                  <span class="gs-item-title">{{ r.title }}</span>
                  <span class="gs-item-path">{{ r.path }}</span>
                  <button class="gs-x" title="删除" @click.stop="navStore.removeRecent(r.path)">✕</button>
                </div>
              </div>

              <div v-if="history.length" class="gs-group">
                <div class="gs-label">
                  搜索历史
                  <button class="gs-clear" @click="navStore.clearSearch()">清空</button>
                </div>
                <div class="gs-chips">
                  <button v-for="h in history" :key="h" class="gs-chip" @click="query = h">
                    {{ h }}<span class="gs-chip-x" title="删除" @click.stop="navStore.removeSearch(h)">✕</span>
                  </button>
                </div>
              </div>

              <div class="gs-group">
                <div class="gs-label">
                  自定义
                  <button class="gs-add" @click="pickerOpen = true">＋ 添加</button>
                </div>
                <p v-if="!customEntries.length" class="gs-custom-tip">
                  没有自定义项——点击「＋ 添加」从全部页面里挑选常用的收录进来。
                </p>
                <div v-for="c in customEntries" :key="c.id" class="gs-item" @click="jumpTo(c.path)">
                  <span class="gs-type custom">自</span>
                  <div class="gs-item-main">
                    <input
                      v-if="renamingId === c.id"
                      v-model="renameText"
                      class="gs-rename-input"
                      @click.stop
                      @keydown.enter="saveRename(c)"
                      @keydown.esc.stop="renamingId = null"
                    />
                    <template v-else>
                      <div class="gs-item-title">{{ c.title }}</div>
                      <div class="gs-item-sub">{{ c.path }}</div>
                    </template>
                  </div>
                  <button class="gs-mini-btn" title="重命名" @click.stop="startRename(c)"><i class="fas fa-pen" /></button>
                  <button class="gs-mini-btn danger" title="删除" @click.stop="navStore.removeCustomEntry(c.id)"><i class="fas fa-trash" /></button>
                </div>
              </div>

              <div v-if="!recent.length && !history.length && !customEntries.length" class="gs-tip">
                输入关键词，模糊搜索全站页面、17 个考纲、12 套真题、5 个智能体，以及你词条本里的词。
              </div>
            </template>

            <!-- 查询结果（分组） -->
            <template v-else>
              <template v-for="(group, gi) in resultGroups" :key="group.key">
                <div class="gs-group">
                  <div class="gs-label">
                    {{ group.label }}<span class="gs-count">{{ group.items.length }}</span>
                  </div>
                  <div
                    v-for="(it, idx) in group.items"
                    :key="group.key + ':' + it.path"
                    class="gs-item"
                    :class="{ active: activeGroup === gi && activeIdx === idx }"
                    @mousemove="setActive(gi, idx)"
                    @click="pick(it)"
                  >
                    <span class="gs-type" :class="group.key">{{ group.tag }}</span>
                    <div class="gs-item-main">
                      <div class="gs-item-title">{{ it.title }}</div>
                      <div v-if="it.subtitle" class="gs-item-sub">{{ it.subtitle }}</div>
                    </div>
                    <i class="fas fa-arrow-right gs-arrow" />
                  </div>
                </div>
              </template>
              <div v-if="!totalCount" class="gs-empty">没有找到与「{{ query }}」相关的内容</div>
            </template>
          </div>

          <!-- 快捷键提示 -->
          <div class="gs-footer">
            <span><kbd>↑</kbd><kbd>↓</kbd> 选择</span>
            <span><kbd>Enter</kbd> 跳转</span>
            <span><kbd>Esc</kbd> 关闭</span>
            <button v-if="!query.trim() && !pickerOpen" class="gs-add gs-add-footer" @click="pickerOpen = true">＋ 添加自定义项</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useNavStore } from '@/stores/nav'
import { useAuthStore } from '@/stores/auth'
import { STATIC_PAGES, ADMIN_PAGES, AGENT_PAGES, resolvePageTitle } from '@/utils/pageMeta'

const router = useRouter()
const navStore = useNavStore()
const authStore = useAuthStore()

const query = ref('')
const inputEl = ref(null)
const activeGroup = ref(0)
const activeIdx = ref(0)

function close() { navStore.closeSearch() }

// ===== 打开面板：清空、聚焦、拉数据 =====
watch(() => navStore.searchOpen, (open) => {
  if (!open) return
  query.value = ''
  activeGroup.value = 0
  activeIdx.value = 0
  pickerOpen.value = false
  renamingId.value = null
  nextTick(() => inputEl.value?.focus())
  navStore.loadSyllabi()   // 会话内缓存一次
  navStore.loadWordbook()  // 每次打开刷新（用户可能刚收了新词）
})

// ===== 数据源 =====
const isAdmin = computed(() => authStore.user?.role !== 'user')

const pageItems = computed(() => {
  const pages = [...STATIC_PAGES]
  if (isAdmin.value) pages.push(...ADMIN_PAGES)
  return pages
})

const syllabusItems = computed(() => navStore.syllabi.map(s => ({
  title: s.name,
  path: `/subject-plan/${s.id}`,
  subtitle: `学科计划 · ${s.question_count || 0} 题`,
  aliases: [s.id, s.abbr].filter(Boolean),
})))

const paperItems = computed(() => {
  const out = []
  for (const s of navStore.syllabi) {
    for (const p of s.exam_papers || []) {
      // 过滤灰色占位卷（如 Cambridge 18 / TPO 75，无 paper_id）
      if (!p.paper_id || p.grey) continue
      out.push({
        title: p.name,
        path: `/subject-plan/${s.id}/exam/${p.paper_id}`,
        subtitle: `${s.name} · ${p.question_count || 0} 题`,
        aliases: [p.paper_id, s.name], // 考纲名也参与匹配：「四级」可命中四级真题卷
      })
    }
  }
  return out
})

const agentItems = computed(() => AGENT_PAGES.map(a => ({
  title: a.title,
  path: a.path,
  subtitle: '智能体中心 · 详情与参数调节',
  aliases: a.aliases,
})))

const wordItems = computed(() => navStore.wordbook.map(w => ({
  title: w.word,
  path: `/wordbook?q=${encodeURIComponent(w.word)}`,
  subtitle: w.entry?.meaning ? `词条本 · ${w.entry.meaning}` : '词条本',
  aliases: [],
})))

const customItems = computed(() => navStore.customEntries.map(c => ({
  title: c.title,
  path: c.path,
  subtitle: '自定义搜索项',
  aliases: c.aliases || [],
})))

// ===== 模糊匹配打分：0 最优，-1 不匹配 =====
function matchScore(entry, q) {
  if (!entry || entry.title == null) {
    console.error('[matchScore] 坏条目:', JSON.stringify(entry), '| q =', q)
    return -1
  }
  const title = entry.title.toLowerCase()
  if (title === q) return 0
  if (title.startsWith(q)) return 1
  if (title.includes(q)) return 2
  for (const a of entry.aliases || []) {
    if (a == null) continue
    const al = String(a).toLowerCase()
    if (al === q || al.startsWith(q)) return 3
    if (al.includes(q) || (al.length >= 2 && q.includes(al))) return 4
  }
  if (entry.initials) {
    if (entry.initials.startsWith(q)) return 5
    if (entry.initials.includes(q)) return 6
  }
  return -1
}

const GROUPS = [
  { key: 'page',     label: '页面',   tag: '页', items: pageItems },
  { key: 'custom',   label: '自定义', tag: '自', items: customItems },
  { key: 'syllabus', label: '考纲',   tag: '纲', items: syllabusItems },
  { key: 'paper',    label: '真题',   tag: '卷', items: paperItems },
  { key: 'agent',    label: '智能体', tag: '智', items: agentItems },
  { key: 'word',     label: '词条',   tag: '词', items: wordItems },
]

const resultGroups = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return []
  return GROUPS.map(g => ({
    ...g,
    items: g.items.value
      .map(it => ({ ...it, _s: matchScore(it, q) }))
      .filter(it => it._s >= 0)
      .sort((a, b) => a._s - b._s || a.title.length - b.title.length)
      .slice(0, 8),
  })).filter(g => g.items.length)
})

const totalCount = computed(() => resultGroups.value.reduce((n, g) => n + g.items.length, 0))

const recent = computed(() => navStore.recentPages)
const history = computed(() => navStore.searchHistory)
const customEntries = computed(() => navStore.customEntries)

// ===== 快捷入口选择器：列出全部可进入页面，点选收录到自定义 =====
const pickerOpen = ref(false)
const PICKER_GROUPS = [
  { key: 'page',     label: '页面',   tag: '页', items: pageItems },
  { key: 'syllabus', label: '考纲',   tag: '纲', items: syllabusItems },
  { key: 'paper',    label: '真题',   tag: '卷', items: paperItems },
  { key: 'agent',    label: '智能体', tag: '智', items: agentItems },
]
const pickerGroups = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return PICKER_GROUPS.map(g => ({ ...g, items: g.items.value })).filter(g => g.items.length)
  return PICKER_GROUPS.map(g => ({
    ...g,
    items: g.items.value
      .map(it => ({ ...it, _s: matchScore(it, q) }))
      .filter(it => it._s >= 0)
      .sort((a, b) => a._s - b._s || a.title.length - b.title.length)
      .slice(0, 12),
  })).filter(g => g.items.length)
})
const pickerTotal = computed(() => pickerGroups.value.reduce((n, g) => n + g.items.length, 0))

const addedPaths = computed(() => new Set(navStore.customEntries.map(c => c.path)))
function isAdded(it) { return addedPaths.value.has(it.path) }
function toggleCustom(it) {
  if (isAdded(it)) {
    const e = navStore.customEntries.find(c => c.path === it.path)
    if (e) navStore.removeCustomEntry(e.id)
  } else {
    // 收录：名称/路径/别名均取自索引，不手填
    navStore.addCustomEntry({ title: it.title, path: it.path, aliases: [...(it.aliases || [])] })
  }
}

// ===== 自定义项重命名（改）=====
const renamingId = ref(null)
const renameText = ref('')
function startRename(c) {
  renamingId.value = c.id
  renameText.value = c.title
  nextTick(() => document.querySelector('.gs-rename-input')?.focus())
}
function saveRename(c) {
  const t = renameText.value.trim()
  renamingId.value = null
  if (t && t !== c.title) navStore.updateCustomEntry(c.id, { title: t })
}

// ===== 键盘导航 =====
function activeItem() {
  const group = resultGroups.value[activeGroup.value]
  if (!group) return null
  return group.items[activeIdx.value] || null
}

function setActive(gi, idx) {
  activeGroup.value = gi
  activeIdx.value = idx
}

function move(delta) {
  const groups = resultGroups.value
  if (!groups.length) return
  const total = groups.reduce((n, g) => n + g.items.length, 0)
  // 扁平位置 = 之前所有组的条目数 + 当前 idx
  let flat = 0
  for (let i = 0; i < activeGroup.value; i++) flat += groups[i].items.length
  flat += activeIdx.value
  flat = (flat + delta + total) % total
  // 还原为 (组, idx)
  let g = 0
  while (g < groups.length && flat >= groups[g].items.length) {
    flat -= groups[g].items.length
    g++
  }
  setActive(Math.min(g, groups.length - 1), flat)
}

function onKeydown(e) {
  if (e.key === 'Escape') {
    e.preventDefault()
    if (pickerOpen.value) {
      pickerOpen.value = false
      e.stopPropagation() // 阻止全局 Esc 直接关面板
      return
    }
    close()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (pickerOpen.value) return // 选择器模式下回车不跳转
    const it = activeItem()
    if (it) pick(it)
  } else if (e.key === 'ArrowDown') {
    e.preventDefault()
    if (pickerOpen.value) return
    move(1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    if (pickerOpen.value) return
    move(-1)
  }
}

// 输入变化：回到第一项
function onInput() {
  activeGroup.value = 0
  activeIdx.value = 0
}

// ===== 跳转 =====
function pick(it) {
  const q = query.value.trim()
  if (q) navStore.recordSearch(q)
  close()
  router.push(it.path)
}

function jumpTo(path) {
  close()
  router.push(path)
}

// ===== Ctrl+K 全局唤起 + 最近访问记录 =====
let recentHooked = false

function onGlobalKey(e) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    navStore.toggleSearch()
  } else if (e.key === 'Escape' && navStore.searchOpen) {
    if (pickerOpen.value) { pickerOpen.value = false; return } // 先退出选择器，再 Esc 才关面板
    close()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onGlobalKey)
  if (!recentHooked) {
    recentHooked = true
    router.afterEach((to) => {
      navStore.recordRecent(to.path, resolvePageTitle(to.path))
    })
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onGlobalKey)
})
</script>

<style scoped>
/* ===== 遮罩 + 面板 ===== */
.gs-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(2, 6, 16, 0.55);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  display: flex; align-items: flex-start; justify-content: center;
  padding-top: 14vh;
}
.gs-panel {
  width: 620px; max-width: 92vw;
  border-radius: 16px;
  background: var(--well);
  border: 1px solid var(--line-soft);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.55);
  overflow: hidden;
  display: flex; flex-direction: column;
}

/* ===== 输入行 ===== */
.gs-input-row {
  display: flex; align-items: center; gap: 10px;
  padding: 15px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.gs-input-icon { color: var(--text-muted); font-size: 14px; }
.gs-input {
  flex: 1; background: transparent; border: none; outline: none;
  color: var(--text-primary); font-size: 15px; font-family: inherit;
}
.gs-input::placeholder { color: var(--text-muted); }
.gs-esc {
  border: 1px solid var(--line-soft); background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  color: var(--text-secondary); font-size: 11px; padding: 3px 8px; border-radius: 6px;
  cursor: pointer; font-family: inherit;
}
.gs-esc:hover { background: color-mix(in srgb, var(--surface, #ffffff) 10%, transparent); color: var(--text-primary); }

/* ===== 结果区 ===== */
.gs-body { max-height: 50vh; overflow-y: auto; padding: 8px; }
.gs-body::-webkit-scrollbar { width: 4px; }
.gs-body::-webkit-scrollbar-thumb { background: rgba(128, 128, 128, 0.25); border-radius: 2px; }

.gs-label {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; color: var(--text-muted); letter-spacing: 0.5px;
  padding: 10px 10px 5px;
}
.gs-count { font-size: 10px; color: var(--text-muted); }

.gs-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 10px; border-radius: 8px; cursor: pointer;
}
.gs-item:hover, .gs-item.active { background: rgba(108, 140, 255, 0.14); }
.gs-arrow { margin-left: auto; color: var(--text-muted); font-size: 11px; opacity: 0; transition: opacity .15s; }
.gs-item:hover .gs-arrow, .gs-item.active .gs-arrow { opacity: 1; }

.gs-type {
  width: 24px; height: 24px; border-radius: 7px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 600;
}
.gs-type.page     { background: rgba(108, 140, 255, 0.18); color: color-mix(in srgb, #8ea4ff 60%, var(--text-primary)); }
.gs-type.syllabus { background: rgba(16, 185, 129, 0.16); color: color-mix(in srgb, #34d399 65%, var(--text-primary)); }
.gs-type.paper    { background: rgba(245, 158, 11, 0.16); color: color-mix(in srgb, #fbbf24 70%, var(--text-primary)); }
.gs-type.agent    { background: rgba(168, 85, 247, 0.18); color: color-mix(in srgb, #c084fc 60%, var(--text-primary)); }
.gs-type.word     { background: rgba(38, 208, 206, 0.16); color: color-mix(in srgb, #2dd4bf 65%, var(--text-primary)); }

.gs-item-main { min-width: 0; }
.gs-item-title { font-size: 13.5px; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.gs-item-sub { font-size: 11.5px; color: var(--text-muted); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.gs-item-path { margin-left: auto; font-size: 11px; color: var(--text-muted); flex-shrink: 0; }
.gs-clock { color: var(--text-muted); font-size: 12px; }

/* ===== 空态 / 历史 ===== */
.gs-tip { padding: 26px 20px; text-align: center; color: var(--text-muted); font-size: 13px; line-height: 1.7; }
.gs-empty { padding: 30px 0; text-align: center; color: var(--text-muted); font-size: 13px; }
.gs-chips { display: flex; flex-wrap: wrap; gap: 6px; padding: 4px 10px 12px; }
.gs-chip {
  display: inline-flex; align-items: center; gap: 6px;
  background: color-mix(in srgb, var(--surface, #ffffff) 6%, transparent); border: 1px solid var(--line-soft);
  color: var(--text-secondary); font-size: 12px; padding: 4px 12px; border-radius: 14px;
  cursor: pointer; font-family: inherit; transition: all .2s;
}
.gs-chip:hover { background: rgba(108, 140, 255, 0.15); color: color-mix(in srgb, #c7d2fe 60%, var(--text-primary)); }

/* ===== 历史 / 自定义项管理 ===== */
.gs-clear {
  margin-left: auto; background: transparent; border: none; color: var(--text-muted);
  font-size: 11px; cursor: pointer; font-family: inherit; padding: 0 2px;
}
.gs-clear:hover { color: #f87171; }
.gs-x {
  margin-left: auto; background: transparent; border: none; color: var(--text-muted);
  font-size: 12px; cursor: pointer; padding: 2px 5px; border-radius: 4px; flex-shrink: 0;
}
.gs-x:hover { color: #f87171; background: rgba(248, 113, 113, 0.1); }
.gs-chip-x { color: var(--text-muted); font-size: 10px; }
.gs-chip-x:hover { color: #f87171; }
.gs-add {
  margin-left: auto; background: rgba(108, 140, 255, 0.12); border: 1px solid rgba(108, 140, 255, 0.25);
  color: color-mix(in srgb, #8ea4ff 60%, var(--text-primary)); font-size: 11px; cursor: pointer; font-family: inherit;
  padding: 2px 10px; border-radius: 10px; transition: all .2s;
}
.gs-add:hover { background: rgba(108, 140, 255, 0.2); }
.gs-add-footer { margin-left: auto; }
.gs-mini-btn {
  background: transparent; border: none; color: var(--text-muted); font-size: 12px;
  cursor: pointer; padding: 4px 6px; border-radius: 6px; flex-shrink: 0;
}
.gs-mini-btn:hover { color: color-mix(in srgb, #8ea4ff 60%, var(--text-primary)); background: rgba(108, 140, 255, 0.12); }
.gs-mini-btn.danger:hover { color: #f87171; background: rgba(248, 113, 113, 0.1); }
.gs-type.custom { background: rgba(236, 72, 153, 0.16); color: color-mix(in srgb, #f472b6 60%, var(--text-primary)); }
.gs-custom-tip { padding: 4px 10px 10px; font-size: 12px; color: var(--text-muted); }

/* ===== 快捷入口选择器 ===== */
.gs-picker-header {
  display: flex; align-items: center; justify-content: space-between; gap: 10px;
  padding: 10px 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.gs-picker-title { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.gs-picker-tip { padding: 10px 12px 2px; font-size: 11.5px; color: var(--text-muted); line-height: 1.6; }
.gs-pick-btn {
  margin-left: auto; flex-shrink: 0;
  background: rgba(108, 140, 255, 0.14); border: 1px solid rgba(108, 140, 255, 0.3);
  color: color-mix(in srgb, #8ea4ff 60%, var(--text-primary)); font-size: 11px; cursor: pointer; font-family: inherit;
  padding: 3px 10px; border-radius: 12px; transition: all .2s;
}
.gs-pick-btn:hover { background: rgba(108, 140, 255, 0.25); }
.gs-pick-btn.added {
  background: rgba(16, 185, 129, 0.14); border-color: rgba(16, 185, 129, 0.3); color: color-mix(in srgb, #34d399 65%, var(--text-primary));
}
.gs-pick-btn.added:hover { background: rgba(248, 113, 113, 0.12); border-color: rgba(248, 113, 113, 0.3); color: #f87171; }

/* ===== 自定义项重命名 ===== */
.gs-rename-input {
  width: 100%; background: color-mix(in srgb, var(--surface, #ffffff) 7%, transparent); border: 1px solid rgba(108, 140, 255, 0.5);
  outline: none; border-radius: 6px; padding: 4px 10px; color: var(--text-primary); font-size: 13px; font-family: inherit;
}

/* ===== 底部快捷键提示 ===== */
.gs-footer {
  display: flex; gap: 16px; align-items: center;
  padding: 9px 16px; border-top: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--text-muted); font-size: 11px;
}
.gs-footer kbd {
  border: 1px solid var(--line-soft); background: color-mix(in srgb, var(--surface, #ffffff) 4%, transparent);
  border-radius: 4px; padding: 1px 5px; font-size: 10px; font-family: inherit;
}

/* ===== 过渡 ===== */
.gs-enter-active, .gs-leave-active { transition: opacity 0.18s ease; }
.gs-enter-active .gs-panel, .gs-leave-active .gs-panel { transition: transform 0.18s ease; }
.gs-enter-from, .gs-leave-to { opacity: 0; }
.gs-enter-from .gs-panel { transform: translateY(-8px) scale(0.98); }
.gs-leave-to .gs-panel { transform: translateY(-8px) scale(0.98); }
</style>
