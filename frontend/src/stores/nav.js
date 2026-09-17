import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listSyllabi } from '@/api/subjectPlan'
import { getWordbook } from '@/api/vocab'
import { useAuthStore } from '@/stores/auth'

// ============================================================
// 全局导航 store — 搜索面板开关 + 搜索数据缓存 + 最近访问/搜索历史
// ============================================================

const RECENT_KEY = 'gs_recent_pages'
const HISTORY_KEY = 'gs_search_history'
const MAX_HISTORY = 10

function readLS(key) {
  try { return JSON.parse(localStorage.getItem(key)) || [] } catch { return [] }
}
function writeLS(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* 隐私模式等场景忽略 */ }
}

export const useNavStore = defineStore('nav', () => {
  // ===== 搜索面板状态 =====
  const searchOpen = ref(false)
  function openSearch() { searchOpen.value = true }
  function closeSearch() { searchOpen.value = false }
  function toggleSearch() { searchOpen.value = !searchOpen.value }

  // ===== 搜索数据缓存 =====
  const syllabi = ref([])        // 考纲 + 真题卷（一次接口全拿，会话内缓存）
  const syllabiLoaded = ref(false)
  const wordbook = ref([])       // 自己的词条本（每次打开面板刷新）

  async function loadSyllabi() {
    if (syllabiLoaded.value) return
    syllabiLoaded.value = true
    try {
      const res = await listSyllabi('')
      syllabi.value = res.syllabi || []
    } catch (e) {
      syllabiLoaded.value = false // 失败允许重试
      console.error('[search] 考纲加载失败:', e)
    }
  }

  async function loadWordbook() {
    const uid = useAuthStore().user?.id
    if (!uid) return
    try {
      wordbook.value = (await getWordbook(uid, 'all')) || []
    } catch (e) {
      console.error('[search] 词条本加载失败:', e)
    }
  }

  // ===== 最近访问（路由切换时记录）=====
  const recentPages = ref(readLS(RECENT_KEY))
  function recordRecent(path, title) {
    const list = recentPages.value.filter(p => p.path !== path)
    list.unshift({ path, title, t: Date.now() })
    recentPages.value = list.slice(0, MAX_HISTORY)
    writeLS(RECENT_KEY, recentPages.value)
  }
  function removeRecent(path) {
    recentPages.value = recentPages.value.filter(p => p.path !== path)
    writeLS(RECENT_KEY, recentPages.value)
  }
  function clearRecent() {
    recentPages.value = []
    writeLS(RECENT_KEY, [])
  }

  // ===== 搜索历史（跳转成功时记录）=====
  const searchHistory = ref(readLS(HISTORY_KEY))
  function recordSearch(q) {
    const list = searchHistory.value.filter(x => x !== q)
    list.unshift(q)
    searchHistory.value = list.slice(0, MAX_HISTORY)
    writeLS(HISTORY_KEY, searchHistory.value)
  }
  function removeSearch(q) {
    searchHistory.value = searchHistory.value.filter(x => x !== q)
    writeLS(HISTORY_KEY, searchHistory.value)
  }
  function clearSearch() {
    searchHistory.value = []
    writeLS(HISTORY_KEY, [])
  }

  // ===== 自定义搜索项（增删改查，localStorage 按用户隔离）=====
  function customKey() {
    const uid = useAuthStore().user?.id
    return uid ? `gs_custom_entries_${uid}` : 'gs_custom_entries'
  }
  const customEntries = ref(readLS(customKey()))
  function persistCustom() { writeLS(customKey(), customEntries.value) }
  function addCustomEntry({ title, path, aliases }) {
    customEntries.value.unshift({
      id: Date.now() + Math.random().toString(36).slice(2, 8),
      title: title.trim(),
      path: path.trim(),
      aliases: aliases,
    })
    persistCustom()
  }
  function updateCustomEntry(id, { title }) {
    const it = customEntries.value.find(e => e.id === id)
    if (!it) return
    const t = title.trim()
    if (!t || t === it.title) return
    // 旧名保留进别名，重命名后仍可被旧名搜到
    it.aliases = it.aliases || []
    if (!it.aliases.includes(it.title)) it.aliases.push(it.title)
    it.title = t
    persistCustom()
  }
  function removeCustomEntry(id) {
    customEntries.value = customEntries.value.filter(e => e.id !== id)
    persistCustom()
  }

  return {
    searchOpen, openSearch, closeSearch, toggleSearch,
    syllabi, loadSyllabi, wordbook, loadWordbook,
    recentPages, recordRecent, removeRecent, clearRecent,
    searchHistory, recordSearch, removeSearch, clearSearch,
    customEntries, addCustomEntry, updateCustomEntry, removeCustomEntry,
  }
})
